from copy import deepcopy
from datetime import datetime
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.extractors_提取器 import ExtractionError, FixedDemoExtractor, OpenAIExtractor
from backend.fixtures_演示案例 import BASE_NOTICES, DEMO_TIME, EXPECTED_RESULTS, N1_V2, PROFILES, SCHOOL, bi, leaf
from backend.main_主程序 import create_app
from backend.models_数据模型 import Notice, Profile, Rule
from backend.rules_规则 import application_state, evaluate, match_notice


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
    tasks = client.post("/api/notices/N1/tasks", headers=headers("A")).json()
    for task in tasks:
        if task["task_type"] in {"document", "prepare"}:
            client.patch("/api/tasks/" + task["id"], json={"status": "done"}, headers=headers("A"))
    client.patch("/api/tasks/A_N1_apply", json={"status": "done"}, headers=headers("A"))
    import_and_approve_v2(client)
    detail = client.get("/api/notices/N1", headers=headers("A")).json()
    by_key = {task["template_id"]: task for task in detail["tasks"]}
    assert by_key["transcript"]["status"] == "done"
    assert by_key["application_form"]["status"] == "done"
    assert by_key["prepare"]["status"] == "done"
    assert by_key["enrollment_certificate"]["status"] == "todo"
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
