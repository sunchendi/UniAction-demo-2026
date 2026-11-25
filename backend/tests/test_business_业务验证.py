from copy import deepcopy
from datetime import datetime
from email.message import EmailMessage
from email.policy import SMTP
from hashlib import sha256

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.extractors_提取器 import ExtractionError, FixedDemoExtractor, OpenAIExtractor
from backend.fixtures_演示案例 import BASE_NOTICES, DEMO_TIME, EXPECTED_RESULTS, N1_V2, PROFILES, SCHOOL, bi, leaf
from backend.main_主程序 import create_app
from backend.models_数据模型 import Notice, Profile, Rule
from backend.rules_规则 import application_state, evaluate, match_notice
from backend.student_notices_学生导入 import MAX_EMAIL_BYTES, StudentNoticeError, read_public_notice


def headers(user):
    return {"X-Demo-Account": user}


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "test.sqlite3", clock=lambda: datetime.fromisoformat(DEMO_TIME)))


@pytest.mark.parametrize("student,index", [(student, i) for student in "ABC" for i in range(5)])
def test_all_fifteen_matching_results(client, student, index):
    detail = client.get(f"/api/notices/N{index + 1}", headers=headers(student))
    assert detail.status_code == 200
    assert detail.json()["match"]["status"] == EXPECTED_RESULTS[student][index]
    assert all(reason["evidence"] in detail.json()["notice"]["source_text"] for reason in detail.json()["match"]["reasons"])


def test_decisive_non_undergraduate_does_not_request_gpa(client):
    result = client.get("/api/notices/N1", headers=headers("B")).json()["match"]
    assert result["status"] == "conditions_not_met"
    assert result["missing_fields"] == []
    assert any(reason["field"] == "program_type" and reason["result"] is False for reason in result["reasons"])
    incomplete = client.get("/api/notices/N1", headers=headers("C")).json()["match"]
    assert incomplete["status"] == "missing_information"
    assert "gpa_value" in incomplete["missing_fields"]


def test_student_notice_preview_and_submission_use_existing_staff_review(client):
    source = "校园活动公告\n报名截止 2026年11月30日 17:00\n申请材料\n- 在学证明\n- 报名表\n"
    payload = {"source_text": source}
    response = client.post("/api/student-notices/preview", json=payload, headers=headers("A"))
    assert response.status_code == 200
    preview = response.json()
    assert preview["source_text"] == source
    assert preview["dates"] == ["报名截止 2026年11月30日 17:00"]
    assert preview["materials"] == ["申请材料", "- 在学证明", "- 报名表"]
    assert not any(n["id"].startswith("STU-") for n in client.get("/api/notices", headers=headers("staff")).json())

    response = client.post("/api/student-notices", json=payload, headers=headers("A"))
    assert response.status_code == 200
    receipt = response.json()
    assert receipt["publication_status"] == "draft"
    notice_route = f"/api/notices/{receipt['notice_id']}"
    for account in ("A", "B", "other_staff"):
        assert client.get(notice_route, headers=headers(account)).status_code == 404
    staff_detail = client.get(notice_route, headers=headers("staff")).json()["notice"]
    assert staff_detail["source_text"] == source
    assert staff_detail["official_deadline"] is None and staff_detail["required_documents"] == []
    assert staff_detail["eligibility_rules"]["op"] == "needs_staff_review"
    assert client.post("/api/student-notices", json=payload, headers=headers("B")).json() == receipt
    versions_route = f"/api/staff/notices/{receipt['notice_id']}/versions/1"
    assert client.post(versions_route + "/approve", headers=headers("A")).status_code == 403
    assert client.post(versions_route + "/approve", headers=headers("staff")).status_code == 409
    assert client.post(versions_route + "/review", headers=headers("staff")).status_code == 200
    assert client.post(versions_route + "/approve", headers=headers("staff")).status_code == 200
    assert client.get(notice_route, headers=headers("A")).status_code == 200


def test_staff_review_queue_flags_gaps_and_only_compares_other_notices_in_school(client):
    source = "校内交流会\n活动范围请向工作人员确认。"
    url = "https://global.hanyang.ac.kr/example-notice"
    submitted = client.post("/api/student-notices", json={"source_text": source, "source_url": url}, headers=headers("A"))
    notice_id = submitted.json()["notice_id"]
    original = client.get(f"/api/notices/{notice_id}", headers=headers("staff")).json()["notice"]
    duplicate = {**original, "id": "DUP-1", "source_url": url + "#schedule"}
    assert client.post("/api/staff/manual", json=duplicate, headers=headers("staff")).status_code == 200
    assert client.post("/api/staff/manual", json=original, headers=headers("staff")).json()["version"] == 2

    queue = {row["id"]: row for row in client.get("/api/notices", headers=headers("staff")).json()}
    assert "review_checks" not in queue["N1"]
    checks = queue[notice_id]["review_checks"]
    assert checks["missing_deadline"] and checks["missing_evidence"]
    assert checks["duplicates"] == [{"id": "DUP-1", "title": original["title"], "reasons": ["same_link", "same_source", "same_title"]}]
    assert all("review_checks" not in notice for notice in client.get("/api/notices", headers=headers("A")).json())
    assert all(notice["id"] != notice_id for notice in client.get("/api/notices", headers=headers("other_staff")).json())


def test_email_preview_decodes_subject_and_body_without_creating_a_draft(client):
    email = EmailMessage()
    email["Subject"] = "교내 활동 안내"
    email["From"] = "Campus Office <office@example.invalid>"
    email["To"] = "recipient@example.invalid"
    email["Date"] = "Wed, 7 Oct 2026 10:00:00 +0900"
    email.set_content("신청 마감: 2026-11-30 17:00\n제출 서류\n- 재학증명서", charset="euc-kr", cte="base64")
    email.add_alternative("<p>Alternate body</p>", subtype="html")
    email.add_attachment("Attachment-only document", filename="attachment.txt")
    route = "/api/student-notices/preview-email"
    raw = email.as_bytes(policy=SMTP)
    response = client.post(route, content=raw, headers=headers("A"))
    assert response.status_code == 200
    preview = response.json()
    assert preview == {
        "title": "교내 활동 안내", "source_url": "",
        "source_text": "교내 활동 안내\n\n신청 마감: 2026-11-30 17:00\n제출 서류\n- 재학증명서",
        "dates": ["신청 마감: 2026-11-30 17:00"],
        "materials": ["제출 서류", "- 재학증명서"],
    }
    assert client.post(route, content=raw, headers=headers("staff")).status_code == 403
    assert not any(n["id"].startswith("STU-") for n in client.get("/api/notices", headers=headers("staff")).json())


def test_email_preview_reads_html_as_text_and_rejects_unreadable_files(client):
    email = EmailMessage()
    email["Subject"] = "校园活动公告"
    email.set_content("""<html><body><p>截止 2026-11-30 17:00</p>
        <p>申请材料</p><ul><li>在学证明</li></ul>
        <img src="https://example.invalid/pixel"><script>Script text</script>
        </body></html>""", subtype="html", cte="quoted-printable")
    route = "/api/student-notices/preview-email"
    response = client.post(route, content=email.as_bytes(), headers=headers("A"))
    assert response.status_code == 200
    preview = response.json()
    assert preview["title"] == "校园活动公告"
    assert preview["materials"] == ["申请材料", "- 在学证明"]
    assert preview["dates"] == ["截止 2026-11-30 17:00"]
    assert "example.invalid" not in preview["source_text"] and "Script text" not in preview["source_text"]

    attachment_only = EmailMessage()
    attachment_only["Subject"] = "Attachment-only email"
    attachment_only.add_attachment("Text attachment", filename="document.txt")
    for raw, status, code in (
        (attachment_only.as_bytes(), 422, "student_email_no_body"),
        (b"not an email", 422, "student_email_invalid"),
        (b"x" * (MAX_EMAIL_BYTES + 1), 413, "student_email_too_large"),
    ):
        failure = client.post(route, content=raw, headers=headers("A"))
        assert failure.status_code == status
        assert failure.json()["detail"]["code"] == code


def test_public_notice_reader_extracts_article_and_respects_school_host_scope(client):
    url = "https://global.hanyang.ac.kr/bbs/board.php?bo_table=s4_1&wr_id=10"
    html = """<head><title>Campus notice</title></head><body>
        <nav>Menu</nav><main><div id="bo_v_con">
        <p>Deadline 2026-11-30</p><p>Required documents</p><p>1. Enrollment certificate</p>
        <script>Ignored script</script></div></main><footer>Footer</footer></body>"""
    requested = []

    def public_school(request):
        requested.append(request.url)
        return httpx.Response(200, text=html, headers={"Content-Type": "text/html; charset=utf-8"})

    with httpx.Client(transport=httpx.MockTransport(public_school)) as reader:
        source, final_url = read_public_notice(url, reader)
        assert final_url == url
        assert source == "Campus notice\nDeadline 2026-11-30\nRequired documents\n1. Enrollment certificate"
        assert requested == [httpx.URL(url)]

    requested.clear()

    def school_redirect(request):
        requested.append(request.url)
        return httpx.Response(302, headers={"Location": "https://example.org/"})

    with httpx.Client(transport=httpx.MockTransport(school_redirect)) as reader:
        with pytest.raises(StudentNoticeError, match="未能读取"):
            read_public_notice(url, reader)
    assert requested == [httpx.URL(url)]

    invalid = client.post("/api/student-notices/preview", json={"source_url": "https://example.org/"}, headers=headers("A"))
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "student_notice_invalid_url"


def test_onboarding_filters_programs_and_saves_only_the_current_students_progress(client):
    def items(student):
        result = client.get("/api/onboarding", headers=headers(student))
        assert result.status_code == 200
        return {item["id"]: item for item in result.json()["items"]}

    path = "/api/onboarding/student-id"
    assert client.get("/api/onboarding", headers=headers("staff")).status_code == 403
    assert client.put(path, headers=headers("staff"), json={"completed": True}).status_code == 403
    assert len(items("A")) == len(items("B")) == 7
    assert len(items("A")["housing"]["steps"]) == 2
    assert items("A")["housing"]["place"]["building_number"] == "501"
    assert items("A")["orientation"]["place"]["floor"] == 3
    assert client.put(path, headers=headers("A"), json={"completed": "true"}).status_code == 422
    for _ in range(2):
        assert client.put(path, headers=headers("A"), json={"completed": True}).json() == {"id": "student-id", "completed": True}
    assert items("A")["student-id"]["completed"] is True
    assert items("C")["student-id"]["completed"] is False

    profile = client.get("/api/profile", headers=headers("A")).json()
    response = client.put("/api/profile", headers=headers("A"), json={**profile, "program_type": "language"})
    assert response.status_code == 200
    language_items = items("A")
    assert len(language_items) == 6
    assert "student-id" not in language_items and "scholarships" not in language_items
    assert "courses" not in language_items and "language-courses" in language_items
    assert language_items["language-placement"]["source_url"].startswith("https://ericaiie.hanyang.ac.kr/")
    assert language_items["orientation"]["place"] is None
    assert client.put(path, headers=headers("A"), json={"completed": False}).status_code == 404
    assert client.put("/api/profile", headers=headers("A"), json=profile).status_code == 200
    assert items("A")["student-id"]["completed"] is True

    assert client.post("/api/demo/reset", headers=headers("staff")).status_code == 200
    assert items("A")["student-id"]["completed"] is False


@pytest.mark.parametrize("op,children,expected", [
    ("all", [True, None], None), ("all", [False, None], False), ("all", [True, True], True),
    ("any", [True, None], True), ("any", [False, None], None), ("any", [False, False], False),
])
def test_three_valued_and_or(op, children, expected):
    fields = ["international_student", "current_dorm_resident"]
    rule = Rule.model_validate({"op": op, "children": [leaf("is_true", field, None, "quote") for field in fields], "evidence": "quote"})
    result = evaluate(rule, dict(zip(fields, children)))
    assert result.value is expected
    if expected is not None:
        assert result.missing == set()


@pytest.mark.parametrize("field,value", [("gpa_scale", 4.3), ("gpa_period", "cumulative")])
def test_gpa_scale_and_period_require_confirmation(field, value):
    profile = deepcopy(PROFILES["A"])
    profile[field] = value
    result = match_notice(Notice.model_validate(BASE_NOTICES[0]), Profile.model_validate(profile))
    assert result["status"] == "needs_staff_review"
    assert any(reason.get("note") == "gpa_basis_mismatch_no_conversion" for reason in result["reasons"])


def test_or_gpa_alternatives_keep_branch_specific_scale():
    def branch(scale, minimum):
        return {"op": "all", "evidence": "quote", "children": [leaf("eq", "gpa_scale", scale, "quote"), leaf("eq", "gpa_period", "previous_semester", "quote"), leaf("gte", "gpa_value", minimum, "quote")]}
    rule = Rule.model_validate({"op": "any", "evidence": "quote", "children": [branch(4.5, 3.5), branch(4.3, 3.3)]})
    profile = {"gpa_scale": 4.5, "gpa_period": "previous_semester", "gpa_value": 3.6}
    assert evaluate(rule, profile).value is True
    profile.update(gpa_scale=4.3, gpa_value=3.4)
    assert evaluate(rule, profile).value is True


def test_vague_language_always_requires_staff_no_topik_invention():
    profile = deepcopy(PROFILES["A"])
    profile["language_qualification"] = "TOPIK 6"
    result = match_notice(Notice.model_validate(BASE_NOTICES[4]), Profile.model_validate(profile))
    assert result["status"] == "needs_staff_review"
    rule = BASE_NOTICES[4]["eligibility_rules"]["children"][-1]
    assert rule["op"] == "needs_staff_review" and rule["value"] is None


def test_unreviewed_notice_cannot_generate_personal_conclusion(client):
    imported = client.post("/api/staff/import", json={"source_text": N1_V2["source_text"], "source_url": N1_V2["source_url"], "mode": "demo"}, headers=headers("staff"))
    assert imported.status_code == 200
    assert imported.json()["publication_status"] == "draft"
    assert client.get("/api/notices/N1", headers=headers("A")).json()["notice"]["version"] == 1
    assert client.get("/api/notices/N1/versions/2", headers=headers("A")).status_code == 404
    with pytest.raises(ValueError, match="unreviewed"):
        match_notice(Notice.model_validate(imported.json()), Profile.model_validate(PROFILES["A"]))
    assert client.post("/api/staff/notices/N1/versions/2/approve", headers=headers("staff")).status_code == 409


def test_tasks_idempotent_dependency_and_progress_persist(client):
    first = client.post("/api/notices/N1/tasks", headers=headers("A")).json()
    second = client.post("/api/notices/N1/tasks", headers=headers("A")).json()
    assert [t["id"] for t in first] == [t["id"] for t in second]
    assert len(first) == len({task["id"] for task in first}) == 4
    assert client.patch("/api/tasks/A_N1_apply", json={"status": "done"}, headers=headers("A")).status_code == 409
    for task in first:
        if task["task_type"] == "document":
            assert client.patch("/api/tasks/" + task["id"], json={"status": "done"}, headers=headers("A")).status_code == 200
    assert client.patch("/api/tasks/A_N1_apply", json={"status": "done"}, headers=headers("A")).status_code == 200
    refreshed = client.get("/api/notices/N1", headers=headers("A")).json()["tasks"]
    assert next(t for t in refreshed if t["id"] == "A_N1_apply")["status"] == "done"


def test_dependency_cycle_and_invalid_fields_rejected():
    invalid = deepcopy(BASE_NOTICES[0])
    invalid["task_templates"][0]["depends_on"] = ["apply"]
    with pytest.raises(ValidationError, match="cyclic"):
        Notice.model_validate(invalid)
    with pytest.raises(ValidationError):
        Rule.model_validate(leaf("eval", "gpa_value", "__import__('os')", "quote"))
    with pytest.raises(ValidationError, match="unsupported rule field"):
        Rule.model_validate(leaf("eq", "passport_number", "x", "quote"))
    with pytest.raises(ValidationError):
        Profile.model_validate({**PROFILES["A"], "passport_number": "forbidden"})
    with pytest.raises(ValidationError):
        Rule.model_validate(leaf("eq", "international_student", "true", "quote"))


def test_korea_clock_and_date_only_precision(client):
    health = client.get("/api/health").json()
    assert health["demo_time"] == DEMO_TIME
    assert health["timezone"] == "Asia/Seoul" and health["fixed_clock"] is True
    detail = client.get("/api/notices/N1", headers=headers("A")).json()
    assert detail["application_state"]["status"] == "open"
    notice = deepcopy(BASE_NOTICES[0])
    notice["official_deadline"] = "2026-10-16"
    notice["application_window"]["closes_at"] = "2026-10-16"
    model = Notice.model_validate(notice)
    assert model.official_deadline == "2026-10-16"
    state = application_state(model, datetime.fromisoformat("2026-10-16T19:00:00+09:00"))
    assert state["deadline_time_unknown"] is True and state["needs_confirmation"] is True
    assert application_state(model, datetime.fromisoformat("2026-10-17T01:00:00+09:00"))["status"] == "closed"
    client.app.state.store.save_notice(model)
    client.app.state.clock = lambda: datetime.fromisoformat("2026-10-16T19:00:00+09:00")
    assert client.get("/api/today", headers=headers("staff")).status_code == 403
    upcoming = client.get("/api/today", headers=headers("A")).json()["upcoming"]
    assert next(item for item in upcoming if item["notice_id"] == "N1")["deadline"] == "2026-10-16"
    result = client.get("/api/calendar", headers=headers("A"))
    assert result.status_code == 200
    calendar = result.json()
    assert (calendar["month"], calendar["today"]) == ("2026-10", "2026-10-16")
    deadline = next(event for event in calendar["events"] if event["id"] == "deadline:N1")
    assert deadline["starts_at"] == "2026-10-16"
    assert client.get("/api/calendar?month=2026-13", headers=headers("A")).status_code == 422
    assert client.get("/api/calendar", headers=headers("staff")).status_code == 403
    client.app.state.clock = lambda: datetime.fromisoformat("2026-10-17T01:00:00+09:00")
    upcoming = client.get("/api/today", headers=headers("A")).json()["upcoming"]
    assert all(item["notice_id"] != "N1" for item in upcoming)
    bad = deepcopy(BASE_NOTICES[0]); bad["official_deadline"] = "2026-10-16T18:00:00"
    with pytest.raises(ValidationError):
        Notice.model_validate(bad)


def import_and_approve_v2(client):
    result = client.post("/api/staff/import", json={"source_text": N1_V2["source_text"], "source_url": N1_V2["source_url"], "mode": "demo"}, headers=headers("staff"))
    assert result.status_code == 200
    assert result.json()["version"] == 2
    assert client.post("/api/staff/notices/N1/versions/2/review", headers=headers("staff")).status_code == 200
    assert client.post("/api/staff/notices/N1/versions/2/approve", headers=headers("staff")).status_code == 200


def test_version_update_preserves_unrelated_done_adds_material_reconfirms_affected(client):
    first_detail = client.get("/api/notices/N1", headers=headers("A")).json()
    assert first_detail["tasks"] == []
    assert set(first_detail["task_places"]) == {"transcript"}
    assert client.get("/api/notices/N1", headers=headers("staff")).json()["task_places"] == {}
    tasks = client.post("/api/notices/N1/tasks", headers=headers("A")).json()
    for task in tasks:
        if task["task_type"] in {"document", "prepare"}:
            client.patch("/api/tasks/" + task["id"], json={"status": "done"}, headers=headers("A"))
    client.patch("/api/tasks/A_N1_apply", json={"status": "done"}, headers=headers("A"))
    before = {event["id"]: event for event in client.get("/api/calendar", headers=headers("A")).json()["events"]}
    assert before["deadline:N1"]["starts_at"] == "2026-10-16T18:00:00+09:00"
    import_and_approve_v2(client)
    after = {event["id"]: event for event in client.get("/api/calendar", headers=headers("A")).json()["events"]}
    assert after["deadline:N1"]["starts_at"] == "2026-10-14T18:00:00+09:00"
    assert after["deadline:N1"]["version"] == 2
    certificate = after["preparation:N1:enrollment_certificate"]
    assert (certificate["starts_at"], certificate["task_id"]) == ("2026-10-11", "A_N1_enrollment_certificate")
    assert "preparation:N1:transcript" not in after
    detail = client.get("/api/notices/N1", headers=headers("A")).json()
    by_key = {task["template_id"]: task for task in detail["tasks"]}
    assert by_key["transcript"]["status"] == "done"
    assert by_key["application_form"]["status"] == "done"
    assert by_key["prepare"]["status"] == "done"
    assert by_key["enrollment_certificate"]["status"] == "todo"
    kiosk = by_key["enrollment_certificate"]["place"]
    assert kiosk["id"] == by_key["transcript"]["place"]["id"] == "certificate-kiosk"
    assert detail["task_places"]["enrollment_certificate"] == kiosk
    assert (kiosk["building_number"], kiosk["floor"]) == ("102", 2)
    assert "place" not in by_key["application_form"] and "place" not in by_key["apply"]
    assert by_key["apply"]["status"] == "requires_reconfirmation"
    assert by_key["apply"]["official_due_at"] == "2026-10-14T18:00:00+09:00"
    assert "A_N1_enrollment_certificate" in by_key["apply"]["depends_on"]
    assert len(detail["versions"]) == 2
    assert client.get("/api/notices/N1/versions/1", headers=headers("A")).json()["source_text"] == BASE_NOTICES[0]["source_text"]
    assert detail["notice"]["source_text"] == N1_V2["source_text"]
    assert client.post("/api/staff/notices/N1/versions/2/approve", headers=headers("staff")).status_code == 200
    assert len(client.post("/api/notices/N1/tasks", headers=headers("A")).json()) == 5


def test_self_report_never_becomes_official_confirmation(client):
    result = client.post("/api/notices/N1/submit", headers=headers("A")).json()
    assert result["status"] == "self_reported_submitted"
    assert result["school_received"] is False and result["school_approved"] is False
    assert client.get("/api/notices/N1", headers=headers("A")).json()["submission_status"] == result


def test_application_followup_is_private_and_survives_notice_updates(client):
    endpoint = "/api/applications"
    edit = endpoint + "/N1/follow-up"
    update = {"status": "needs_documents", "next_check_on": "2026-10-08", "note": "Check with the office"}
    assert client.get(endpoint, headers=headers("A")).json()["items"] == []
    assert client.put(edit, json=update, headers=headers("A")).status_code == 409

    client.post("/api/notices/N1/submit", headers=headers("A"))
    item, = client.get(endpoint, headers=headers("A")).json()["items"]
    assert item["followup"] == {"status": "waiting_result", "next_check_on": None, "note": ""}
    assert client.put(edit, json={**update, "next_check_on": "2026-02-30"}, headers=headers("A")).status_code == 422
    assert client.put(edit, json=update, headers=headers("A")).json() == update

    import_and_approve_v2(client)
    item, = client.get(endpoint, headers=headers("A")).json()["items"]
    assert (item["submitted_version"], item["latest_version"], item["followup"]) == (1, 2, update)
    client.post("/api/notices/N1/submit", headers=headers("A"))
    item, = client.get(endpoint, headers=headers("A")).json()["items"]
    assert (item["submitted_version"], item["followup"]) == (2, update)

    client.post("/api/notices/N1/submit", headers=headers("B"))
    other, = client.get(endpoint, headers=headers("B")).json()["items"]
    assert other["followup"]["note"] == ""
    assert client.get(endpoint, headers=headers("staff")).status_code == 403
    assert client.put(edit, json=update, headers=headers("staff")).status_code == 403
    assert client.get("/api/notices/N1", headers=headers("staff")).json()["submission_status"] is None
    assert client.get("/api/notices/N1", headers=headers("A")).json()["submission_status"]["school_approved"] is False


def test_scope_role_school_and_revocation_enforced_server_side(client):
    client.post("/api/notices/N1/tasks", headers=headers("A"))
    endpoint = "/api/staff/students/A/notices/N1/tasks"
    assert client.get(endpoint, headers=headers("staff")).status_code == 403
    assert client.get("/api/profile", headers=headers("staff")).status_code == 403
    assert client.get(endpoint, headers=headers("A")).status_code == 403
    assert client.get("/api/notices/N1", headers=headers("other_staff")).status_code == 404
    created = client.post("/api/cases", json={"notice_id": "N1", "message": "자료 준비 도움이 필요합니다", "sharing_scope": "case_only"}, headers=headers("A")).json()
    assert client.get(endpoint, headers=headers("staff")).status_code == 403
    staff_cases = client.get("/api/cases", headers=headers("staff")).json()
    assert [case["id"] for case in staff_cases] == [created["id"]]
    assert all("gpa" not in str(case) for case in staff_cases)
    assert client.get("/api/cases", headers=headers("other_staff")).json() == []
    client.put("/api/notices/N1/sharing", json={"sharing_scope": "tasks_and_cases"}, headers=headers("A"))
    assert client.get(endpoint, headers=headers("staff")).status_code == 200
    assert "gpa" not in str(client.get(endpoint, headers=headers("staff")).json())
    client.put("/api/notices/N1/sharing", json={"sharing_scope": "none"}, headers=headers("A"))
    assert client.get(endpoint, headers=headers("staff")).status_code == 403
    assert client.get("/api/cases", headers=headers("staff")).json() == []
    assert client.patch("/api/cases/" + created["id"], json={"status": "resolved", "response": "확인"}, headers=headers("staff")).status_code == 403
    assert len(client.get("/api/cases", headers=headers("A")).json()) == 1


def test_private_case_stays_private_when_different_case_shared(client):
    first = client.post("/api/cases", json={"notice_id": "N5", "message": "private", "sharing_scope": "none"}, headers=headers("A")).json()
    second = client.post("/api/cases", json={"notice_id": "N5", "message": "shared", "sharing_scope": "case_only"}, headers=headers("A")).json()
    visible = client.get("/api/cases", headers=headers("staff")).json()
    assert [c["id"] for c in visible] == [second["id"]]
    assert first["id"] != second["id"]


def test_revoked_shared_case_never_reopens_when_new_case_sent(client):
    old = client.post("/api/cases", json={"notice_id": "N5", "message": "old explicit case", "sharing_scope": "case_only"}, headers=headers("A")).json()
    client.put("/api/notices/N5/sharing", json={"sharing_scope": "none"}, headers=headers("A"))
    new = client.post("/api/cases", json={"notice_id": "N5", "message": "new explicit case", "sharing_scope": "case_only"}, headers=headers("A")).json()
    assert [case["id"] for case in client.get("/api/cases", headers=headers("staff")).json()] == [new["id"]]


def test_scope_none_through_new_case_revokes_previous_case_access(client):
    old = client.post("/api/cases", json={"notice_id": "N5", "message": "old shared case", "sharing_scope": "case_only"}, headers=headers("A")).json()
    client.post("/api/cases", json={"notice_id": "N5", "message": "private case changes scope to none", "sharing_scope": "none"}, headers=headers("A"))
    new = client.post("/api/cases", json={"notice_id": "N5", "message": "new shared case", "sharing_scope": "case_only"}, headers=headers("A")).json()
    assert [case["id"] for case in client.get("/api/cases", headers=headers("staff")).json()] == [new["id"]]
    own_cases = client.get("/api/cases", headers=headers("A")).json()
    revoked = next(case for case in own_cases if case["id"] == old["id"])
    assert revoked["access_revoked"] is True and revoked["current_sharing_scope"] == "none"
    client.put("/api/notices/N5/sharing", json={"sharing_scope": "tasks_and_cases"}, headers=headers("A"))
    assert [case["id"] for case in client.get("/api/cases", headers=headers("staff")).json()] == [new["id"]]


def test_cross_school_import_cannot_overwrite_hanyang(client):
    result = client.post("/api/staff/import", json={"source_text": BASE_NOTICES[0]["source_text"], "source_url": "https://demo.invalid/other", "mode": "demo"}, headers=headers("other_staff"))
    assert result.status_code == 200
    assert result.json()["school_id"] == "other_demo"
    original = client.get("/api/notices/N1", headers=headers("A")).json()["notice"]
    assert original["school_id"] == SCHOOL and original["publication_status"] == "approved"


def test_demo_extractor_only_accepts_exact_complete_source(client):
    assert FixedDemoExtractor().extract(BASE_NOTICES[0]["source_text"], "demo")["extraction_mode"] == "fixed_demo"
    count = len(client.get("/api/notices/N1/versions", headers=headers("staff")).json())
    for text in ["any notice", BASE_NOTICES[0]["source_text"] + "\n", BASE_NOTICES[0]["source_text"][:100]]:
        result = client.post("/api/staff/import", json={"source_text": text, "mode": "demo"}, headers=headers("staff"))
        assert result.status_code == 422
        assert result.json()["detail"]["code"] == "demo_source_unknown"
        assert result.json()["detail"]["can_create_manual_draft"] is True
    assert len(client.get("/api/notices/N1/versions", headers=headers("staff")).json()) == count


def test_missing_real_ai_key_is_actionable_failure_never_published(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    health = client.get("/api/health").json()
    assert health["mode"] == "fixed_demo" and health["real_ai_configured"] is False
    result = client.post("/api/staff/import", json={"source_text": "new original", "mode": "real"}, headers=headers("staff"))
    assert result.status_code == 503
    assert result.json()["detail"]["code"] == "ai_not_configured"
    assert len(client.get("/api/notices", headers=headers("staff")).json()) == 5


def test_real_ai_invalid_schema_and_service_failures_are_not_success(monkeypatch):
    import openai
    import httpx
    from types import SimpleNamespace

    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder-not-a-real-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-configured-model")
    outcomes = [
        (SimpleNamespace(output_parsed=None), "ai_invalid_return"),
        (openai.APITimeoutError(request=httpx.Request("POST", "https://example.invalid")), "ai_timeout"),
        (ValueError("bad schema"), "ai_semantic_invalid"),
        (openai.RateLimitError("quota", response=httpx.Response(429, request=httpx.Request("POST", "https://example.invalid")), body={}), "ai_quota_unavailable"),
    ]
    for outcome, code in outcomes:
        def parse(**kwargs):
            if isinstance(outcome, Exception):
                raise outcome
            return outcome
        monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse)))
        with pytest.raises(ExtractionError) as error:
            OpenAIExtractor().extract("source", "demo")
        assert error.value.code == code


def test_real_ai_schema_converts_to_strict_sdk_format_without_arbitrary_objects():
    from openai.lib._pydantic import to_strict_json_schema
    from backend.extractors_提取器 import ExtractedNotice
    schema = to_strict_json_schema(ExtractedNotice)
    object_count = 0

    def walk(node):
        nonlocal object_count
        if isinstance(node, dict):
            if node.get("type") == "object":
                object_count += 1
                assert node.get("additionalProperties") is False
                assert set(node.get("required", [])) == set(node.get("properties", {}))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    assert object_count >= 8


def test_exact_evidence_missing_fields_and_unsupported_rules_rejected(client):
    bad = deepcopy(BASE_NOTICES[0]); bad["evidence"]["official_deadline"] = "not in source"
    assert client.post("/api/staff/manual", json=bad, headers=headers("staff")).status_code == 422
    bad = deepcopy(BASE_NOTICES[0]); bad["eligibility_rules"]["children"][0]["field"] = "bank_number"
    assert client.post("/api/staff/manual", json=bad, headers=headers("staff")).status_code == 422
    bad = deepcopy(BASE_NOTICES[0]); del bad["official_deadline"]
    assert client.post("/api/staff/manual", json=bad, headers=headers("staff")).status_code == 422
    bad = deepcopy(BASE_NOTICES[0]); bad["official_deadline"] = "2026-10-17T18:00:00+09:00"
    assert client.post("/api/staff/manual", json=bad, headers=headers("staff")).status_code == 422


def test_manual_draft_edit_review_approve_and_role_guards(client):
    manual = deepcopy(BASE_NOTICES[3]); manual["id"] = "manual_demo"
    created = client.post("/api/staff/manual", json=manual, headers=headers("staff"))
    assert created.status_code == 200
    draft = created.json()
    assert draft["extraction_mode"] == "manual" and draft["publication_status"] == "draft"
    assert client.get("/api/notices/manual_demo", headers=headers("A")).status_code == 404
    draft["title"] = bi("수동 검토 활동", "人工审核活动")
    edited = client.put("/api/staff/notices/manual_demo/versions/1", json=draft, headers=headers("staff"))
    assert edited.status_code == 200
    assert client.post("/api/staff/notices/manual_demo/versions/1/review", headers=headers("A")).status_code == 403
    client.post("/api/staff/notices/manual_demo/versions/1/review", headers=headers("staff"))
    assert client.post("/api/staff/notices/manual_demo/versions/1/approve", headers=headers("staff")).status_code == 200
    assert client.get("/api/notices/manual_demo", headers=headers("B")).json()["match"]["status"] == "conditions_met"
    assert client.put("/api/staff/notices/manual_demo/versions/1", json=draft, headers=headers("staff")).status_code == 409


def test_profile_persists_across_server_restart_and_rematches(tmp_path):
    path = tmp_path / "persist.sqlite3"
    first = TestClient(create_app(path))
    profile = first.get("/api/profile", headers=headers("C")).json()
    profile.update(gpa_value=3.8, gpa_scale=4.5, gpa_period="previous_semester", current_dorm_resident=True)
    assert first.put("/api/profile", json=profile, headers=headers("C")).status_code == 200
    first.post("/api/notices/N1/tasks", headers=headers("C"))
    first.patch("/api/tasks/C_N1_transcript", json={"status": "in_progress"}, headers=headers("C"))
    second = TestClient(create_app(path))
    detail = second.get("/api/notices/N1", headers=headers("C")).json()
    assert detail["match"]["status"] == "conditions_met"
    assert next(t for t in detail["tasks"] if t["template_id"] == "transcript")["status"] == "in_progress"
    profile["school_id"] = "other_demo"
    assert second.put("/api/profile", json=profile, headers=headers("C")).status_code == 403


def test_reset_reproducibly_restores_accounts_versions_and_progress(client):
    client.post("/api/notices/N1/tasks", headers=headers("A"))
    import_and_approve_v2(client)
    assert client.post("/api/demo/reset", headers=headers("A")).status_code == 403
    assert client.post("/api/demo/reset", headers=headers("other_staff")).status_code == 403
    assert client.post("/api/demo/reset", headers=headers("staff")).status_code == 200
    detail = client.get("/api/notices/N1", headers=headers("A")).json()
    assert detail["notice"]["version"] == 1 and detail["tasks"] == [] and len(detail["versions"]) == 1


def test_no_auth_and_other_student_task_access_denied(client):
    assert client.get("/api/profile").status_code == 401
    client.post("/api/notices/N1/tasks", headers=headers("A"))
    assert client.patch("/api/tasks/A_N1_transcript", json={"status": "done"}, headers=headers("C")).status_code == 404
    assert client.post("/api/notices/N1/tasks", headers=headers("B")).status_code == 409
