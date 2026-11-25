"""Student notice previews and handoff to the existing staff draft workflow."""

import re
from codecs import BOM_UTF8
from email import policy
from email.errors import MessageError
from email.parser import BytesParser
from hashlib import sha256
from html.parser import HTMLParser
from time import monotonic
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from .fixtures_演示案例 import bi
from .models_数据模型 import Notice


NOTICE_HOSTS = {
    "www.hanyang.ac.kr", "site.hanyang.ac.kr", "global.hanyang.ac.kr",
    "oia.hanyang.ac.kr", "ehaksa.hanyang.ac.kr", "esc.hanyang.ac.kr",
    "studyerica.hanyang.ac.kr", "ericaexchange.hanyang.ac.kr",
    "ericaiie.hanyang.ac.kr", "hydorm.hanyang.ac.kr",
}
MAX_PAGE_BYTES = 1_000_000
MAX_SOURCE_LENGTH = 100_000
MAX_EMAIL_BYTES = 2 * 1024 * 1024
NO_SOURCE_LINK = "https://demo.invalid/student-source"
DATE = re.compile(
    r"(?<!\d)(?:20\d{2}\s*[./\-년年]\s*\d{1,2}\s*[./\-월月]\s*\d{1,2}(?!\d)"
    r"|\d{1,2}\s*[월月]\s*\d{1,2}\s*[일日]|\d{1,2}/\d{1,2}(?![\d/]))"
)
DATE_CONTEXT = re.compile(r"마감|기간|일정|접수|신청일|기한|截止|期间|日程|日期|deadline|dates?|period", re.I)
DIGIT_SPACING = re.compile(r"(?<=\d)[ \t]+(?=\d)")
MATERIALS = re.compile(
    r"(?:제출|필요|구비|필수|준비)\s*(?:서류|자료|물)|제출할\s*서류"
    r"|(?:申请|提交|所需|必备|必需|准备|报名)\s*(?:材料|文件|资料)"
    r"|required\s+(?:documents|materials)|(?:documents|materials)\s+to\s+submit", re.I,
)
LIST_ITEM = re.compile(r"^(?:[-*•·▪●▶]|[①-⑳]|\d+[.)]|\(\d+\))\s*")


class StudentNoticeError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def notice_source_url(value):
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
        valid = (
            parsed.scheme == "https"
            and parsed.hostname in NOTICE_HOSTS
            and parsed.port in (None, 443)
            and parsed.username is None
            and "\\" not in value
            and not any(char.isspace() or ord(char) < 32 for char in value)
        )
        if valid:
            return urlunsplit(("https", parsed.hostname, parsed.path or "/", parsed.query, ""))
    except ValueError:
        pass
    raise StudentNoticeError("student_notice_invalid_url", "请输入受支持的汉阳大学 HTTPS 公告链接，或直接粘贴通知原文。")


class NoticeHTML(HTMLParser):
    """Prefer article text over page chrome and preserve block boundaries."""

    ignored = {"head", "script", "style", "noscript", "nav", "header", "footer", "aside", "form", "template"}
    void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    blocks = {"article", "main", "section", "div", "p", "br", "li", "tr", "h1", "h2", "h3", "h4", "table"}

    def __init__(self, *, whole_body=False):
        super().__init__(convert_charrefs=True)
        self.whole_body = whole_body
        self.path = []
        self.regions = [[], [], [], []]
        self.title = []

    def handle_starttag(self, tag, attrs):
        parent = self.path[-1][1] if self.path else 0
        attrs = dict(attrs)
        region = parent
        if parent < 0 or tag in self.ignored or "hidden" in attrs:
            region = -1
        elif not self.whole_body:
            if attrs.get("id") == "bo_v_con" or "entry-content" in (attrs.get("class") or "").split():
                region = 3
            elif tag == "article":
                region = max(parent, 2)
            elif tag == "main":
                region = max(parent, 1)
        if tag not in self.void:
            self.path.append((tag, region))
        if region >= 0 and tag in self.blocks:
            self.regions[region].append("\n")
            if self.whole_body and tag == "li":
                self.regions[region].append("- ")

    def handle_endtag(self, tag):
        for index in range(len(self.path) - 1, -1, -1):
            if self.path[index][0] == tag:
                region = self.path[index][1]
                if region >= 0 and tag in self.blocks:
                    self.regions[region].append("\n")
                del self.path[index:]
                break

    def handle_data(self, data):
        tag, region = self.path[-1] if self.path else ("", 0)
        if tag == "title":
            self.title.append(data)
        if region >= 0:
            self.regions[region].append(data)

    def source_text(self):
        for parts in reversed(self.regions):
            body = "\n".join(" ".join(line.split()) for line in "".join(parts).splitlines() if line.strip())
            if body:
                title = " ".join("".join(self.title).split())
                return f"{title}\n{body}" if not self.whole_body and title and title not in body else body
        return ""


def read_public_notice(url, client):
    """Read a bounded, unauthenticated text response from a supported campus host."""
    cutoff = monotonic() + 12
    try:
        for _ in range(3):
            with client.stream("GET", notice_source_url(url), headers={"Accept-Encoding": "identity"}) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers["location"])
                    continue
                response.raise_for_status()
                mime = response.headers.get("content-type", "").split(";", 1)[0].lower()
                if mime not in {"text/html", "application/xhtml+xml", "text/plain"}:
                    break
                data = bytearray()
                for chunk in response.iter_bytes(chunk_size=8192):
                    data.extend(chunk)
                    if len(data) > MAX_PAGE_BYTES or monotonic() >= cutoff:
                        raise ValueError("notice too large or slow")
                try:
                    text = data.decode(response.encoding or "utf-8")
                except UnicodeDecodeError:
                    text = data.decode("cp949")
                if mime != "text/plain":
                    parser = NoticeHTML()
                    parser.feed(text)
                    parser.close()
                    text = parser.source_text()
                if text.strip() and len(text) <= MAX_SOURCE_LENGTH:
                    return text, notice_source_url(url)
                break
    except (httpx.HTTPError, ValueError, KeyError, StudentNoticeError):
        pass
    raise StudentNoticeError("student_notice_read_failed", "未能读取该网页的公告正文。请展开公告后复制原文。")


def preview_notice(source_text, source_url):
    source_url = notice_source_url(source_url)
    if not source_text.strip():
        if not source_url:
            raise StudentNoticeError("student_notice_source_required", "请粘贴公告原文或输入汉阳大学公告链接。")
        with httpx.Client(timeout=4.0, follow_redirects=False, trust_env=False) as client:
            source_text, source_url = read_public_notice(source_url, client)
    lines = [line.strip() for line in source_text.splitlines()]
    title = next(line for line in lines if line)[:160]
    dated_lines = [
        line for line in lines
        if DATE.search(line) or DATE.search(DIGIT_SPACING.sub("", line))
    ]
    dated_lines.sort(key=lambda line: not DATE_CONTEXT.search(line))
    material_lines = []
    in_materials = False
    for line in lines:
        if MATERIALS.search(line):
            in_materials = True
        elif not (in_materials and LIST_ITEM.match(line)):
            in_materials = False
        if in_materials:
            material_lines.append(line)
    return {
        "source_text": source_text,
        "source_url": source_url,
        "title": title,
        "dates": list(dict.fromkeys(line[:500] for line in dated_lines))[:8],
        "materials": list(dict.fromkeys(line[:500] for line in material_lines))[:10],
    }


def preview_email_notice(raw):
    invalid = "无法读取该邮件文件。请重新导出 .eml，或复制邮件正文后粘贴。"
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw.removeprefix(BOM_UTF8))
        if not message.keys() or message.defects:
            raise StudentNoticeError("student_email_invalid", invalid)
        subject = " ".join(str(message.get("Subject", "")).split())
        body = ""
        bad_charset = False
        for kind in ("plain", "html"):
            part = message.get_body((kind,))
            if part is None or part.get_filename():
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            try:
                body = payload.decode(part.get_content_charset() or "utf-8").strip()
            except (LookupError, UnicodeError):
                bad_charset = True
                continue
            if kind == "html" and body:
                parser = NoticeHTML(whole_body=True)
                parser.feed(body)
                parser.close()
                body = parser.source_text()
            if body:
                break
    except (MessageError, RecursionError, ValueError) as exc:
        raise StudentNoticeError("student_email_invalid", invalid) from exc

    if not body:
        if bad_charset:
            raise StudentNoticeError("student_email_invalid", invalid)
        raise StudentNoticeError("student_email_no_body", "邮件没有可读取的正文。请复制公告内容后粘贴。")
    source_text = f"{subject}\n\n{body}" if subject else body
    if len(source_text) > MAX_SOURCE_LENGTH:
        raise StudentNoticeError("student_email_text_too_long", "邮件正文过长。请复制与公告相关的内容后粘贴。")
    return preview_notice(source_text, "")


def student_notice_draft(source_text, source_url, school_id):
    if not source_text.strip():
        raise StudentNoticeError("student_notice_source_required", "请预览或粘贴公告原文后送审。")
    preview = preview_notice(source_text, source_url)
    source_hash = sha256(source_text.encode("utf-8")).hexdigest()
    fingerprint = sha256(f"{source_hash}\n{preview['source_url']}".encode("utf-8")).hexdigest()
    return Notice(
        id=f"STU-{fingerprint[:28]}",
        school_id=school_id,
        title=bi(preview["title"], preview["title"]),
        category="activity",
        source_url=preview["source_url"] or NO_SOURCE_LINK,
        source_text=source_text,
        source_hash=source_hash,
        version=1,
        publication_status="draft",
        eligibility_rules={"op": "needs_staff_review", "evidence": preview["title"]},
        required_documents=[],
        official_deadline=None,
        application_window={},
        application_url=None,
        application_link_type="unknown",
        office_contact=None,
        task_templates=[],
        evidence={},
        ambiguities=[bi("학생이 보낸 원문입니다. 조건, 제출 자료와 날짜를 확인하세요.", "请核对学生提交原文中的条件、材料和日期。")],
        change_summary=bi("학생이 검토를 요청한 공지", "学生送审的公告"),
    )
