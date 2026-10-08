"""Local auth business risks, using temporary databases and no external accounts."""
import base64
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.auth_本地认证 import PASSWORD_ITERATIONS, SESSION_COOKIE, SESSION_SECONDS, token_hash, verify_password
from backend.fixtures_演示案例 import BASE_NOTICES, DEMO_TIME, N1_V2, PROFILES, SCHOOL
from backend.main_主程序 import create_app

ORIGIN = {"Origin": "http://testserver"}
PASSWORD = "Fictional local password 42!"


def registration(username="student_one", **updates):
    body = {"username": username, "password": PASSWORD, "display_name": "自建测试学生", "program_type": "undergraduate", "enrollment_status": "enrolled", "department_id": "engineering"}
    return {**body, **updates}


@pytest.fixture
def environment(tmp_path):
    clock = {"now": datetime(2026, 10, 3, 9, 0, tzinfo=timezone.utc)}
    path = tmp_path / "accounts.sqlite3"
    app = create_app(path, auth_clock=lambda: clock["now"])
    return app, path, clock


@pytest.fixture
def client(environment):
    return TestClient(environment[0], headers=ORIGIN)


def register(client, **updates):
    result = client.post("/api/auth/register", json=registration(**updates))
    assert result.status_code == 200, result.text
    return result.json()["account"]


def test_register_creates_independent_student_cookie_and_null_optional_profile(client):
    assert client.get("/api/auth/me").json() == {"account": None}
    result = client.post("/api/auth/register", json=registration())
    assert result.status_code == 200
    account = result.json()["account"]
    assert account["id"].startswith("user_") and account["id"] not in {"A", "B", "C", "staff"}
    assert account["role"] == "student" and account["school_id"] == SCHOOL
    assert account["is_demo"] is False and account["username"] == "student_one"
    assert account["label"] == {"ko": "自建测试学生", "zh": "自建测试学生"}
    cookie = result.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "path=/" in cookie
    assert f"max-age={SESSION_SECONDS}" in cookie
    profile = client.get("/api/profile").json()
    assert profile["school_id"] == SCHOOL
    assert profile["program_type"] == "undergraduate" and profile["enrollment_status"] == "enrolled" and profile["department_id"] == "engineering"
    assert all(value is None for key, value in profile.items() if key not in {"school_id", "program_type", "enrollment_status", "department_id"})
    assert client.get("/api/auth/me").json()["account"] == account
    assert PASSWORD not in result.text and "password_hash" not in result.text
    assert len(client.get("/api/accounts").json()) == 5  # no public listing of personal usernames


@pytest.mark.parametrize("updates", [
    {"role": "staff"}, {"school_id": "other_demo"}, {"gpa_value": 3.8},
    {"program_type": "administrator"}, {"enrollment_status": "unknown"}, {"department_id": "invented_department"},
    {"department_id": None}, {"display_name": " "}, {"display_name": "x" * 51},
])
def test_registration_rejects_privileges_and_invalid_required_fields(client, updates):
    result = client.post("/api/auth/register", json=registration(**updates))
    assert result.status_code == 422
    assert client.get("/api/auth/me").json() == {"account": None}
    assert client.app.state.store.registered_credentials("student_one") is None
    assert PASSWORD not in result.text


def test_registration_required_selects_have_no_silent_defaults(client):
    for field in ["program_type", "enrollment_status", "department_id"]:
        body = registration(); del body[field]
        assert client.post("/api/auth/register", json=body).status_code == 422


def test_username_uniqueness_is_case_insensitive_and_password_policy_not_echoed(client):
    register(client)
    duplicate = client.post("/api/auth/register", json=registration("STUDENT_ONE"))
    assert duplicate.status_code == 409 and duplicate.json()["detail"]["code"] == "username_taken"
    short = "TooShort9!"
    invalid = client.post("/api/auth/register", json=registration("another_name", password=short))
    assert invalid.status_code == 422 and short not in invalid.text


def test_custom_profile_and_session_survive_new_app_instance(environment, client):
    account = register(client)
    profile = client.get("/api/profile").json()
    profile.update(year=3, semester=5, international_student=True, gpa_value=3.9, gpa_scale=4.5, gpa_period="previous_semester", current_dorm_resident=False)
    assert client.put("/api/profile", json=profile).status_code == 200
    assert client.get("/api/notices/N1").json()["match"]["status"] == "conditions_met"
    client.post("/api/notices/N1/tasks")
    task = account["id"] + "_N1_transcript"
    assert client.patch("/api/tasks/" + task, json={"status": "in_progress"}).status_code == 200
    restarted = TestClient(create_app(environment[1], auth_clock=lambda: environment[2]["now"]), headers=ORIGIN)
    restarted.cookies.update(client.cookies)
    assert restarted.get("/api/profile").json() == profile
    assert restarted.get("/api/auth/me").json()["account"]["id"] == account["id"]
    assert next(item for item in restarted.get("/api/notices/N1").json()["tasks"] if item["id"] == task)["status"] == "in_progress"


def test_login_logout_and_rotated_session_are_real_cookie_behaviors(client):
    account = register(client)
    first_token = client.cookies.get(SESSION_COOKIE)
    assert client.post("/api/auth/logout").json() == {"account": None}
    assert client.get("/api/auth/me").json() == {"account": None}
    assert client.get("/api/profile").status_code == 401
    result = client.post("/api/auth/login", json={"username": "STUDENT_ONE", "password": PASSWORD})
    assert result.status_code == 200 and result.json()["account"] == account
    second_token = client.cookies.get(SESSION_COOKIE)
    assert second_token != first_token
    assert client.app.state.store.session_account(token_hash(first_token), client.app.state.auth_clock().timestamp()) is None
    assert client.post("/api/auth/logout").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200


def test_wrong_password_and_unknown_username_get_identical_generic_failure(client):
    register(client)
    client.post("/api/auth/logout")
    wrong = client.post("/api/auth/login", json={"username": "student_one", "password": "Wrong fictional password"})
    absent = client.post("/api/auth/login", json={"username": "not_registered", "password": "Wrong fictional password"})
    assert wrong.status_code == absent.status_code == 401
    assert wrong.json() == absent.json() == {"detail": {"code": "login_error", "message": "用户名或密码不正确。"}}


def test_session_expiry_uses_auth_utc_clock_not_fixed_demo_clock(environment, client):
    register(client)
    environment[2]["now"] += timedelta(seconds=SESSION_SECONDS - 1)
    assert client.get("/api/auth/me").status_code == 200
    assert client.get("/api/health").json()["demo_time"] == DEMO_TIME
    environment[2]["now"] += timedelta(seconds=2)
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/profile", headers={"X-Demo-Account": "A"}).status_code == 401
    assert client.post("/api/auth/logout").status_code == 200  # recover an expired cookie
    assert client.get("/api/auth/me").json() == {"account": None}


@pytest.mark.parametrize("token", ["forged-cookie", "x" * 43])
def test_forged_cookie_rejected_and_cannot_fall_back_to_demo_staff(client, token):
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/cases", headers={"X-Demo-Account": "staff"}).status_code == 401
    assert client.post("/api/auth/logout").status_code == 200


def test_valid_cookie_cannot_be_overridden_by_other_demo_or_staff_header(client):
    own = register(client)
    profile = client.get("/api/profile", headers={"X-Demo-Account": "A"}).json()
    assert profile["gpa_value"] is None
    assert client.get("/api/auth/me", headers={"X-Demo-Account": "staff"}).json()["account"]["id"] == own["id"]
    assert client.get("/api/demo/sources", headers={"X-Demo-Account": "staff"}).status_code == 403
    assert client.post("/api/demo/reset", headers={"X-Demo-Account": "staff"}).status_code == 403
    assert client.get("/api/staff/students/A/notices/N1/tasks", headers={"X-Demo-Account": "other_staff"}).status_code == 403
    profile["school_id"] = "other_demo"
    assert client.put("/api/profile", json=profile).status_code == 403


def test_two_registered_students_have_separate_profiles_tasks_and_cases(environment, client):
    first = register(client)
    second_client = TestClient(environment[0], headers=ORIGIN)
    second = register(second_client, username="student_two", display_name="另一学生", program_type="master", department_id="business")
    assert first["id"] != second["id"]
    assert client.get("/api/profile").json()["program_type"] == "undergraduate"
    assert second_client.get("/api/profile").json()["program_type"] == "master"
    client.post("/api/notices/N1/tasks")
    own_task = first["id"] + "_N1_transcript"
    assert second_client.patch("/api/tasks/" + own_task, json={"status": "done"}).status_code == 404
    assert second_client.get("/api/notices/N1").json()["tasks"] == []
    sent = client.post("/api/cases", json={"notice_id": "N5", "message": "本人的测试协助", "sharing_scope": "none"}).json()
    assert sent["student_id"] == first["id"]
    assert second_client.get("/api/cases").json() == []
    assert client.get("/api/profile", headers={"X-Demo-Account": second["id"]}).json()["program_type"] == "undergraduate"


def test_registered_student_staff_progress_still_requires_explicit_scope_and_school(environment, client):
    account = register(client)
    client.post("/api/notices/N1/tasks")
    endpoint = f"/api/staff/students/{account['id']}/notices/N1/tasks"
    staff = TestClient(environment[0], headers={**ORIGIN, "X-Demo-Account": "staff"})
    assert staff.get(endpoint).status_code == 403
    client.post("/api/cases", json={"notice_id": "N1", "message": "准备材料的演示问题", "sharing_scope": "case_only"})
    assert staff.get(endpoint).status_code == 403
    client.put("/api/notices/N1/sharing", json={"sharing_scope": "tasks_and_cases"})
    result = staff.get(endpoint)
    assert result.status_code == 200 and len(result.json()) == 4 and "gpa_value" not in result.text
    assert staff.get(endpoint, headers={"X-Demo-Account": "other_staff"}).status_code in {403, 404}
    assert staff.get("/api/profile").status_code == 403
    client.put("/api/notices/N1/sharing", json={"sharing_scope": "none"})
    assert staff.get(endpoint).status_code == 403 and staff.get("/api/cases").json() == []


def test_password_salts_and_session_tokens_are_never_stored_in_plaintext(environment, client, caplog, capsys):
    first = register(client)
    token = client.cookies.get(SESSION_COOKIE)
    second_client = TestClient(environment[0], headers=ORIGIN)
    register(second_client, username="same_password_other_user")
    store = environment[0].state.store
    one = store.registered_credentials("student_one")["password_hash"]
    two = store.registered_credentials("same_password_other_user")["password_hash"]
    assert one != two and verify_password(PASSWORD, one) and verify_password(PASSWORD, two)
    algorithm, rounds, salt, digest = one.split("$")
    assert algorithm == "pbkdf2_sha256" and int(rounds) >= 600_000 == PASSWORD_ITERATIONS
    assert len(base64.b64decode(salt)) >= 16 and len(base64.b64decode(digest)) == 32
    assert len(base64.urlsafe_b64decode(token + "=")) >= 32
    with store.connection() as db:
        row = db.execute("SELECT token_hash FROM auth_sessions WHERE student_id=?", (first["id"],)).fetchone()
        assert row[0] == token_hash(token) and row[0] != token
    data = environment[1].read_bytes()
    assert PASSWORD.encode() not in data and token.encode() not in data
    output = capsys.readouterr()
    assert PASSWORD not in caplog.text + output.out + output.err and token not in caplog.text + output.out + output.err


def test_demo_reset_protects_registered_data_and_existing_demo_progress(environment, client):
    demo = TestClient(environment[0], headers={**ORIGIN, "X-Demo-Account": "A"})
    demo.post("/api/notices/N1/tasks")
    demo.patch("/api/tasks/A_N1_transcript", json={"status": "done"})
    account = register(client)
    client.post("/api/notices/N1/tasks")
    client.post("/api/cases", json={"notice_id": "N5", "message": "保留此测试案例", "sharing_scope": "none"})
    staff = TestClient(environment[0], headers={**ORIGIN, "X-Demo-Account": "staff"})
    denied = staff.post("/api/demo/reset")
    assert denied.status_code == 409 and denied.json()["detail"]["code"] == "registered_accounts_protected"
    assert "DATABASE_PATH" in denied.json()["detail"]["message"]
    assert client.get("/api/auth/me").json()["account"]["id"] == account["id"]
    assert len(client.get("/api/notices/N1").json()["tasks"]) == 4
    assert len(client.get("/api/cases").json()) == 1
    assert next(t for t in demo.get("/api/notices/N1").json()["tasks"] if t["template_id"] == "transcript")["status"] == "done"
    assert demo.get("/api/profile").json() == PROFILES["A"]


@pytest.mark.parametrize("origin", ["https://evil.invalid", "http://localhost:8000.evil.invalid", "null"])
def test_cross_site_registration_login_logout_and_profile_writes_are_rejected(client, origin):
    assert client.post("/api/auth/register", json=registration(), headers={"Origin": origin}).status_code == 403
    register(client)
    assert client.post("/api/auth/login", json={"username": "student_one", "password": PASSWORD}, headers={"Origin": origin}).status_code == 403
    assert client.post("/api/auth/logout", headers={"Origin": origin}).status_code == 403
    profile = client.get("/api/profile").json()
    profile["year"] = 9
    assert client.put("/api/profile", json=profile, headers={"Origin": origin}).status_code == 403
    assert client.get("/api/profile").json()["year"] is None


def test_cookie_writes_without_source_are_blocked_but_exact_referer_allowed(environment, client):
    register(client)
    no_origin = TestClient(environment[0])
    no_origin.cookies.update(client.cookies)
    assert no_origin.post("/api/auth/logout").status_code == 403
    assert no_origin.post("/api/auth/logout", headers={"Referer": "http://testserver/student/tasks"}).status_code == 200


def test_loopback_random_port_same_origin_allowed_but_rebinding_host_read_denied(environment):
    local = TestClient(environment[0], base_url="http://127.0.0.1:43819", headers={"Origin": "http://127.0.0.1:43819"})
    assert local.post("/api/auth/register", json=registration()).status_code == 200
    assert local.get("/api/auth/me").json()["account"]["is_demo"] is False
    for endpoint in ["/api/profile", "/api/cases", "/api/auth/me"]:
        assert local.get(endpoint, headers={"Host": "evil.invalid", "X-Demo-Account": "staff"}).status_code == 403
    assert local.post("/api/auth/logout", headers={"Host": "evil.invalid", "Origin": "http://evil.invalid"}).status_code == 403


def test_demo_header_is_local_only_and_browser_without_origin_cannot_write(environment):
    remote = TestClient(environment[0], base_url="http://127.0.0.1:8000", client=("203.0.113.10", 9000))
    assert remote.get("/api/profile", headers={"X-Demo-Account": "A"}).status_code == 403
    local = TestClient(environment[0])
    assert local.post("/api/auth/register", json=registration(), headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert local.get("/api/profile", headers={"X-Demo-Account": "A"}).status_code == 200


def test_failed_login_limit_persists_and_recovers_after_utc_window(environment, client):
    register(client)
    client.post("/api/auth/logout")
    for _ in range(5):
        assert client.post("/api/auth/login", json={"username": "student_one", "password": "Wrong test password"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "student_one", "password": PASSWORD}).status_code == 429
    restarted = TestClient(create_app(environment[1], auth_clock=lambda: environment[2]["now"]), headers=ORIGIN)
    assert restarted.post("/api/auth/login", json={"username": "student_one", "password": PASSWORD}).status_code == 429
    environment[2]["now"] += timedelta(minutes=16)
    assert restarted.post("/api/auth/login", json={"username": "student_one", "password": PASSWORD}).status_code == 200


def test_successful_login_does_not_clear_ip_failures_across_usernames(environment, client):
    register(client)
    client.post("/api/auth/logout")
    for username in ["unknown_name_1", "unknown_name_2"]:
        assert client.post("/api/auth/login", json={"username": username, "password": "Wrong test password"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "student_one", "password": PASSWORD}).status_code == 200
    bucket = "login_ip:" + token_hash("testclient")
    assert environment[0].state.store.auth_attempts(bucket, environment[2]["now"].timestamp(), 900) == 2


def test_school_rename_keeps_accounts_sessions_versions_progress_consent_and_originals(environment, client):
    import json
    from copy import deepcopy
    from hashlib import sha256
    from backend.models_数据模型 import Notice
    from backend.school_migration_学校更名迁移 import LEGACY_SCHOOL, legacy_demo_text

    account = register(client)
    student = account["id"]
    profile = {**PROFILES["A"], "year": 4}
    assert client.put("/api/profile", json=profile).status_code == 200
    assert client.post("/api/notices/N1/tasks").status_code == 200
    assert client.patch(f"/api/tasks/{student}_N1_transcript", json={"status": "done"}).status_code == 200
    assert client.patch(f"/api/tasks/{student}_N1_application_form", json={"status": "done"}).status_code == 200
    assert client.patch(f"/api/tasks/{student}_N1_apply", json={"status": "done"}).status_code == 200
    store = environment[0].state.store
    store.approve_and_sync(Notice.model_validate(deepcopy(N1_V2)), "staff", datetime.fromisoformat(DEMO_TIME))
    assert client.post("/api/cases", json={"notice_id": "N1", "message": "保留我的授权和进度", "sharing_scope": "tasks_and_cases"}).status_code == 200
    assert client.post("/api/notices/N1/submit").status_code == 200
    expected_detail = client.get("/api/notices/N1").json()
    expected_cases = client.get("/api/cases").json()
    saved_cookie = client.cookies.get(SESSION_COOKIE)
    password_hash = store.registered_credentials("student_one")["password_hash"]
    manual = deepcopy(BASE_NOTICES[3])
    manual.update(id="MANUAL", source_text=manual["source_text"] + "\n人工补充的原文应完整保留。")
    manual["source_hash"] = sha256(manual["source_text"].encode("utf-8")).hexdigest()
    store.save_notice(Notice.model_validate(manual))
    other = {**deepcopy(BASE_NOTICES[3]), "school_id": "other_demo", "id": "OTHER"}
    store.save_notice(Notice.model_validate(other))

    def old_value(value):
        if isinstance(value, str):
            return LEGACY_SCHOOL if value == SCHOOL else legacy_demo_text(value)
        if isinstance(value, list):
            return [old_value(item) for item in value]
        if isinstance(value, dict):
            return {key: old_value(item) for key, item in value.items()}
        return value

    # Build an old installation with meaningful saved data, without touching
    # any real user's database or password. The new startup must migrate it.
    with store.connection() as db:
        for table in ("profiles", "notices", "cases"):
            for row in db.execute(f"SELECT rowid,data FROM {table} WHERE school_id=?", (SCHOOL,)).fetchall():
                data = old_value(json.loads(row["data"]))
                if table == "notices":
                    data["source_hash"] = sha256(data["source_text"].encode("utf-8")).hexdigest()
                db.execute(f"UPDATE {table} SET school_id=?,data=? WHERE rowid=?", (LEGACY_SCHOOL, json.dumps(data, ensure_ascii=False), row["rowid"]))
        for row in db.execute("SELECT id,data FROM tasks WHERE student_id=?", (student,)).fetchall():
            db.execute("UPDATE tasks SET data=? WHERE id=?", (json.dumps(old_value(json.loads(row["data"])), ensure_ascii=False), row["id"]))
        db.execute("UPDATE auth_users SET school_id=? WHERE id=?", (LEGACY_SCHOOL, student))
    original_manual_text = legacy_demo_text(manual["source_text"])
    restarted_app = create_app(environment[1], auth_clock=lambda: environment[2]["now"])
    restarted = TestClient(restarted_app, headers=ORIGIN)
    restarted.cookies.set(SESSION_COOKIE, saved_cookie)
    assert restarted.get("/api/auth/me").json()["account"] == account
    assert restarted.get("/api/profile").json() == profile
    assert restarted.get("/api/notices/N1").json() == expected_detail
    assert restarted.get("/api/cases").json() == expected_cases
    assert restarted_app.state.store.registered_credentials("student_one")["password_hash"] == password_hash
    assert restarted_app.state.store.notice("MANUAL", SCHOOL).source_text == original_manual_text
    assert restarted_app.state.store.notice("OTHER", "other_demo").model_dump() == other
    assert restarted.post("/api/demo/reset", headers={"X-Demo-Account": "staff"}).status_code == 403
    staff = TestClient(restarted_app, headers={**ORIGIN, "X-Demo-Account": "staff"})
    assert staff.get(f"/api/staff/students/{student}/notices/N1/tasks").status_code == 200
    backups = list(environment[1].parent.joinpath("backups").glob("*.sqlite3"))
    assert len(backups) == 1
    import sqlite3
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute("SELECT school_id FROM auth_users WHERE id=?", (student,)).fetchone()[0] == LEGACY_SCHOOL
    create_app(environment[1])
    assert list(environment[1].parent.joinpath("backups").glob("*.sqlite3")) == backups
