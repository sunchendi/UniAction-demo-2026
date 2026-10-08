"""Local-only competition prototype; preset demo identities are not school SSO."""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .extractors_提取器 import ExtractionError, extractor_for
from .fixtures_演示案例 import ACCOUNTS, DEMO_TIME, SCHOOL, SCHOOL_NAME, all_sources, bi
from .models_数据模型 import CaseCreate, CaseUpdate, ImportRequest, LoginRequest, Notice, Profile, RegisterRequest, SharingUpdate, TaskUpdate
from .rules_规则 import application_state, match_notice
from .store_存储 import Store
from .auth_本地认证 import AUTH_WINDOW_SECONDS, DUMMY_PASSWORD_HASH, SESSION_COOKIE, SESSION_PATTERN, SESSION_SECONDS, hash_password, new_session_token, token_hash, verify_password

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)


LOCAL_ORIGINS = {"http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000"}
LOOPBACK_CLIENTS = {"127.0.0.1", "::1", "localhost", "testclient"}


def create_app(db_path=None, clock=None, auth_clock=None):
    store = Store(db_path or os.environ.get("DATABASE_PATH", str(PROJECT_ROOT / "backend" / "data" / "demo.sqlite3")))
    app = FastAPI(title="UniAction / 校园行动演示", version="0.1.0")
    app.state.store = store
    app.state.clock = clock or (lambda: datetime.fromisoformat(os.environ.get("DEMO_TIME", DEMO_TIME)))
    app.state.auth_clock = auth_clock or (lambda: datetime.now(timezone.utc))
    app.add_middleware(CORSMiddleware, allow_origins=sorted(LOCAL_ORIGINS), allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH"], allow_headers=["Content-Type", "X-Demo-Account"])

    @app.middleware("http")
    async def local_api_guard(request: Request, call_next):
        is_test = request.client and request.client.host == "testclient"
        local_target = request.url.hostname in {"127.0.0.1", "localhost", "::1"} or (is_test and request.url.hostname == "testserver")
        if request.url.path.startswith("/api/") and not local_target:
            return JSONResponse(status_code=403, content={"detail": {"code": "local_host_required", "message": "本地原型接口仅接受 localhost 或 loopback 主机地址。"}})
        if request.url.path.startswith("/api/") and request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            allowed = set(LOCAL_ORIGINS)
            if is_test:
                allowed.add("http://testserver")
            if local_target and request.client and request.client.host in LOOPBACK_CLIENTS:
                # Standalone previews/tests may use another loopback port. Never
                # trust an arbitrary Host as its own origin (DNS rebinding).
                allowed.add(f"{request.url.scheme}://{request.url.netloc}")
            if origin is not None:
                source = origin
            elif referer:
                parsed = urlsplit(referer)
                source = f"{parsed.scheme}://{parsed.netloc}"
            else:
                source = None
            # Browser writes (and every cookie-bearing write) require an exact
            # trusted source. Legacy no-cookie loopback scripts remain usable.
            browser_request = request.headers.get("sec-fetch-site") is not None
            local_cli = request.client and request.client.host in LOOPBACK_CLIENTS and request.url.hostname in {"127.0.0.1", "localhost", "::1", "testserver"}
            rejected = not local_target or (source is not None and source not in allowed) or (source is None and (SESSION_COOKIE in request.cookies or browser_request or not local_cli))
            if rejected:
                return JSONResponse(status_code=403, content={"detail": {"code": "csrf_origin_rejected", "message": "拒绝跨站状态修改。请从本地原型页面操作；带会话的请求必须提供匹配的 Origin 或 Referer。"}})
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def safe_validation_errors(request: Request, exc: RequestValidationError):
        if request.url.path.startswith("/api/auth/"):
            return JSONResponse(status_code=422, content={"detail": {"code": "invalid_auth_fields", "message": "账号字段无效。用户名须为 3–32 位英文、数字或 _.-；注册密码 15–128 字符，显示名 1–50 字符；请选择合法课程、在读状态与院系。", "fields": [str(error["loc"][-1]) for error in exc.errors()]}})
        return JSONResponse(status_code=422, content={"detail": [{"type": error["type"], "loc": error["loc"], "msg": error["msg"]} for error in exc.errors()]})

    def now():
        value = app.state.clock()
        if value.tzinfo is None or value.utcoffset().total_seconds() != 9 * 3600:
            raise HTTPException(500, "演示时钟必须配置韩国 +09:00 时区")
        return value

    def real_time():
        value = app.state.auth_clock()
        if value.tzinfo is None:
            raise HTTPException(500, "认证时钟必须是有时区的真实 UTC 时间")
        return value.timestamp()

    def session_identity(request: Request):
        raw = request.cookies.get(SESSION_COOKIE)
        if raw is None:
            return None
        if not SESSION_PATTERN.fullmatch(raw):
            raise HTTPException(401, {"code": "session_invalid", "message": "会话已失效，请重新登录。"})
        found = store.session_account(token_hash(raw), real_time())
        if not found:
            raise HTTPException(401, {"code": "session_invalid", "message": "会话已失效，请重新登录。"})
        return found

    def account(request: Request, x_demo_account: str | None = Header(default=None)):
        authenticated = session_identity(request)
        if authenticated:
            return authenticated
        if not request.client or request.client.host not in LOOPBACK_CLIENTS:
            raise HTTPException(403, {"code": "demo_local_only", "message": "预设演示身份仅允许本地使用。"})
        found = next((a for a in ACCOUNTS if a["id"] == x_demo_account), None)
        if not found:
            raise HTTPException(401, {"code": "login_required", "message": "请登录本地学生账号或选择预设演示账号；不是学校 SSO。"})
        return {**found, "is_demo": True}

    def rate_buckets(request, username):
        address = request.client.host if request.client else "unknown"
        return "login_ip:" + token_hash(address), "login_user:" + token_hash(username)

    def check_limits(buckets):
        stamp = real_time()
        if any(store.auth_attempts(bucket, stamp, AUTH_WINDOW_SECONDS) >= limit for bucket, limit in buckets):
            raise HTTPException(429, {"code": "rate_limited", "message": "登录或注册失败次数过多，请 15 分钟后重试。"}, headers={"Retry-After": str(AUTH_WINDOW_SECONDS)})

    def issue_session(user, request, response):
        old = request.cookies.get(SESSION_COOKIE)
        if old:
            store.revoke_session(token_hash(old))
        raw, stamp = new_session_token(), real_time()
        store.save_session(token_hash(raw), user["id"], stamp + SESSION_SECONDS, stamp)
        response.set_cookie(SESSION_COOKIE, raw, max_age=SESSION_SECONDS, httponly=True, samesite="lax", secure=request.url.scheme == "https", path="/")
        response.headers["Cache-Control"] = "no-store"

    @app.post("/api/auth/register")
    def register(data: RegisterRequest, request: Request, response: Response):
        bucket = "register_ip:" + token_hash(request.client.host if request.client else "unknown")
        check_limits([(bucket, 10)])
        store.record_auth_attempt(bucket, real_time(), AUTH_WINDOW_SECONDS)
        if store.registered_credentials(data.username):
            raise HTTPException(409, {"code": "username_taken", "message": "该用户名已存在，请换一个用户名或登录。"})
        try:
            user = store.register_user(data, hash_password(data.password), real_time())
        except sqlite3.IntegrityError as exc:
            raise HTTPException(409, {"code": "username_taken", "message": "该用户名已存在，请换一个用户名或登录。"}) from exc
        issue_session(user, request, response)
        return {"account": user}

    @app.post("/api/auth/login")
    def login(data: LoginRequest, request: Request, response: Response):
        ip_bucket, username_bucket = rate_buckets(request, data.username)
        check_limits([(ip_bucket, 20), (username_bucket, 5)])
        user = store.registered_credentials(data.username)
        valid = verify_password(data.password, user["password_hash"] if user else DUMMY_PASSWORD_HASH)
        if not user or not valid:
            for bucket in [ip_bucket, username_bucket]:
                store.record_auth_attempt(bucket, real_time(), AUTH_WINDOW_SECONDS)
            raise HTTPException(401, {"code": "login_error", "message": "用户名或密码不正确。"})
        store.clear_auth_attempts(username_bucket)
        user = store.account_from_user(user)
        issue_session(user, request, response)
        return {"account": user}

    @app.get("/api/auth/me")
    def me(request: Request):
        return {"account": session_identity(request)}

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response):
        raw = request.cookies.get(SESSION_COOKIE)
        if raw:
            store.revoke_session(token_hash(raw))
        response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=request.url.scheme == "https")
        return {"account": None}

    def student(user=Depends(account)):
        if user["role"] != "student":
            raise HTTPException(403, "学生功能仅限本人演示账号")
        return user

    def staff(user=Depends(account)):
        if user["role"] != "staff":
            raise HTTPException(403, "需要工作人员角色")
        return user

    def get_notice(id, user, version=None, approved=None):
        notice = store.notice(id, user["school_id"], version, approved=user["role"] == "student" if approved is None else approved)
        if not notice:
            raise HTTPException(404, "通知不存在、未经审核或不属于当前学校")
        return notice

    def version_summaries(id, user):
        return [{"version": n["version"], "publication_status": n["publication_status"], "change_summary": n["change_summary"], "source_hash": n["source_hash"], "reviewed_by": n["reviewed_by"], "reviewed_at": n["reviewed_at"]} for n in store.versions(id, user["school_id"], user["role"] == "student")]

    @app.get("/api/health")
    def health():
        ready = bool(os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_MODEL"))
        configured = os.environ.get("EXTRACTOR_MODE", "demo")
        return {"status": "ok", "mode": "real_ai" if configured == "real" and ready else "fixed_demo", "demo_time": now().isoformat(), "timezone": "Asia/Seoul", "fixed_clock": True, "real_ai_configured": ready, "auth_mode": "local_student_sessions_and_local_demo_accounts", "school": SCHOOL_NAME, "fictional_data": True, "registered_accounts_supported": True}

    @app.get("/api/accounts")
    def accounts():
        return [{**a, "is_demo": True} for a in ACCOUNTS]

    @app.get("/api/profile")
    def profile(user=Depends(student)):
        return store.profile(user["id"]).model_dump()

    @app.put("/api/profile")
    def update_profile(data: Profile, user=Depends(student)):
        if data.school_id != user["school_id"]:
            raise HTTPException(403, "school_id 由服务端账号确定，不允许跨学校修改")
        store.save_profile(user["id"], data)
        return data.model_dump()

    @app.get("/api/notices")
    def notices(user=Depends(account)):
        profile = store.profile(user["id"]) if user["role"] == "student" else None
        result = []
        for notice in store.list_notices(user["school_id"], user["role"] == "staff"):
            result.append({"id": notice.id, "title": notice.title.model_dump(), "category": notice.category, "version": notice.version, "publication_status": notice.publication_status, "official_deadline": notice.official_deadline, "extraction_mode": notice.extraction_mode, "match": match_notice(notice, profile) if profile else None, "application_state": application_state(notice, now()), "change_summary": notice.change_summary.model_dump()})
        return result

    @app.get("/api/notices/{id}")
    def notice_detail(id: str, user=Depends(account)):
        notice = get_notice(id, user)
        is_student = user["role"] == "student"
        return {"notice": notice.model_dump(), "match": match_notice(notice, store.profile(user["id"])) if is_student else None, "tasks": store.tasks(user["id"], id) if is_student else [], "versions": version_summaries(id, user), "application_state": application_state(notice, now()), "submission_status": store.submission(user["id"], id) if is_student else None, "sharing_scope": store.sharing(user["id"], id) if is_student else "none"}

    @app.get("/api/notices/{id}/versions")
    def versions(id: str, user=Depends(account)):
        get_notice(id, user)
        return version_summaries(id, user)

    @app.get("/api/notices/{id}/versions/{version}")
    def version(id: str, version: int, user=Depends(account)):
        return get_notice(id, user, version).model_dump()

    @app.post("/api/notices/{id}/tasks")
    def generate_tasks(id: str, user=Depends(student)):
        notice = get_notice(id, user)
        match = match_notice(notice, store.profile(user["id"]))
        if match["status"] == "conditions_not_met":
            raise HTTPException(409, "当前资料明确不满足条件；请先修改相关资料再生成行动清单")
        return store.make_tasks(user["id"], notice, now())

    @app.patch("/api/tasks/{id}")
    def update_task(id: str, data: TaskUpdate, user=Depends(student)):
        task = store.task(id)
        if not task or task["student_id"] != user["id"]:
            raise HTTPException(404, "任务不存在或无本人访问权限")
        get_notice(task["notice_id"], user)
        if task.get("removed_in_version"):
            raise HTTPException(409, "任务已在新版本中移除")
        if data.status == "done":
            dependencies = [store.task(dep) for dep in task["depends_on"]]
            if any(dep is None or dep["status"] != "done" for dep in dependencies):
                raise HTTPException(409, "请先完成依赖的材料任务；任务依赖不等于学校已确认申请")
        return store.update_task(id, data.status)

    @app.post("/api/notices/{id}/submit")
    def submit(id: str, user=Depends(student)):
        notice = get_notice(id, user)
        return store.submit(user["id"], id, notice.version, now())

    @app.put("/api/notices/{id}/sharing")
    def sharing(id: str, data: SharingUpdate, user=Depends(student)):
        get_notice(id, user)
        store.set_sharing(user["id"], id, data.sharing_scope)
        return {"sharing_scope": data.sharing_scope, "notice_id": id, "revoked": data.sharing_scope == "none"}

    @app.post("/api/cases")
    def create_case(data: CaseCreate, user=Depends(student)):
        get_notice(data.notice_id, user)
        return store.create_case(user, data, now())

    @app.get("/api/cases")
    def cases(user=Depends(account)):
        return store.cases(user)

    @app.patch("/api/cases/{id}")
    def update_case(id: str, data: CaseUpdate, user=Depends(staff)):
        if not any(case["id"] == id for case in store.cases(user)):
            raise HTTPException(403, "案例未授权、授权已撤销或不属于当前学校")
        return store.update_case(id, data, now())

    @app.get("/api/staff/students/{student_id}/notices/{notice_id}/tasks")
    def staff_tasks(student_id: str, notice_id: str, user=Depends(staff)):
        get_notice(notice_id, user, approved=True)
        target = store.registered_account(student_id) or next((a for a in ACCOUNTS if a["id"] == student_id and a["role"] == "student"), None)
        if not target or target["school_id"] != user["school_id"]:
            raise HTTPException(403, "拒绝跨学校访问")
        if store.sharing(student_id, notice_id) != "tasks_and_cases":
            raise HTTPException(403, "未获得相关任务进度共享授权，或授权已撤销")
        return store.tasks(student_id, notice_id)  # deliberately no profile or GPA

    @app.get("/api/demo/sources")
    def demo_sources(user=Depends(staff)):
        if user["school_id"] != SCHOOL:
            raise HTTPException(403, "此学校无演示通知资源")
        return all_sources()

    @app.post("/api/staff/import")
    def import_notice(data: ImportRequest, user=Depends(staff)):
        try:
            extracted = extractor_for(data.mode).extract(data.source_text, data.source_url)
        except ExtractionError as exc:
            raise HTTPException(exc.status, {"code": exc.code, "message": exc.message, "can_create_manual_draft": True}) from exc
        id = data.notice_id or (extracted["id"] if extracted["id"] != "pending" else "notice_" + uuid4().hex[:12])
        latest = store.notice(id, user["school_id"])
        # Account's school is authoritative; a foreign-school staff cannot import
        # fixture source into the Hanyang school's record.
        extracted.update(id=id, school_id=user["school_id"], version=latest.version + 1 if latest else 1, publication_status="draft", reviewed_by=None, reviewed_at=None)
        notice = Notice.model_validate(extracted)
        store.save_notice(notice)
        return notice.model_dump()

    @app.post("/api/staff/manual")
    def manual_notice(data: Notice, user=Depends(staff)):
        if data.school_id != user["school_id"]:
            raise HTTPException(403, "不允许跨学校创建草稿")
        latest = store.notice(data.id, user["school_id"])
        data.version = latest.version + 1 if latest else 1
        data.publication_status = "draft"
        data.reviewed_by = data.reviewed_at = None
        data.extraction_mode = "manual"
        store.save_notice(data)
        return data.model_dump()

    @app.put("/api/staff/notices/{id}/versions/{version}")
    def edit_notice(id: str, version: int, data: Notice, user=Depends(staff)):
        current = get_notice(id, user, version)
        if current.publication_status not in {"draft", "under_review"}:
            raise HTTPException(409, "已审核版本不可覆盖；请导入新版本保留旧原文")
        if data.id != id or data.version != version or data.school_id != user["school_id"]:
            raise HTTPException(403, "版本、通知与学校标识不可修改")
        if data.source_text != current.source_text or data.source_hash != current.source_hash:
            raise HTTPException(409, "保存的原文不可覆盖；请导入新版本")
        data.publication_status = "draft"
        data.reviewed_by = data.reviewed_at = None
        store.save_notice(data)
        return data.model_dump()

    @app.post("/api/staff/notices/{id}/versions/{version}/review")
    def review_notice(id: str, version: int, user=Depends(staff)):
        notice = get_notice(id, user, version)
        if notice.publication_status not in {"draft", "under_review"}:
            raise HTTPException(409, "此版本已经审核，不能重写审核状态")
        notice.publication_status = "under_review"
        store.save_notice(notice)
        return notice.model_dump()

    @app.post("/api/staff/notices/{id}/versions/{version}/approve")
    def approve_notice(id: str, version: int, user=Depends(staff)):
        notice = get_notice(id, user, version)
        if notice.publication_status == "approved":
            return notice.model_dump()  # repeat approval is idempotent
        if notice.publication_status != "under_review":
            raise HTTPException(409, "请先开始人工审核，确认重要条件、材料、日期及依据后再批准")
        latest_approved = store.notice(id, user["school_id"], approved=True)
        if latest_approved and version <= latest_approved.version:
            raise HTTPException(409, "不可批准早于当前正式版本的草稿")
        notice = Notice.model_validate(notice.model_dump())
        return store.approve_and_sync(notice, user["id"], now()).model_dump()

    @app.post("/api/demo/reset")
    def reset(user=Depends(staff)):
        if user["school_id"] != SCHOOL:
            raise HTTPException(403, "只有 Hanyang 演示工作人员可重置此本地演示环境")
        try:
            store.reset()
        except ValueError as exc:
            raise HTTPException(409, {"code": "registered_accounts_protected", "message": "此数据库已有独立学生账号，已拒绝重置以保护个人资料和进度。比赛演示请通过 DATABASE_PATH 使用独立演示数据库。"}) from exc
        return {"status": "reset", "demo_time": now().isoformat(), "notices": 5, "students": 3, "message": "虚构演示数据已重置，N1 恢复第一版"}

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "API 不存在")
        dist = (PROJECT_ROOT / "frontend" / "dist").resolve()
        candidate = (dist / path).resolve()
        if candidate.is_relative_to(dist) and candidate.is_file():
            return FileResponse(candidate)
        if (dist / "index.html").is_file():
            return FileResponse(dist / "index.html")
        return {"message": "前端尚未构建。请在 frontend 运行 npm run build，或使用 Vite 开发入口 http://127.0.0.1:5173", "api_docs": "/docs"}

    return app


app = create_app()
