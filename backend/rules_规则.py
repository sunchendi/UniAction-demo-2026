"""Deterministic three-valued logic, never executes notice text."""
from dataclasses import dataclass
from datetime import datetime

from .models_数据模型 import Notice, Profile, Rule, parse_temporal


@dataclass
class Evaluation:
    value: bool | None
    reasons: list[dict]
    missing: set[str]
    staff: bool = False


def evaluate(rule: Rule, profile: dict, expected_gpa: dict | None = None) -> Evaluation:
    expected_gpa = dict(expected_gpa or {})
    if rule.op in {"all", "any"}:
        # GPA bases belong to an AND group. Do not flatten OR alternatives:
        # 3.5/4.5 OR 3.3/4.3 must retain each branch's scale.
        if rule.op == "all":
            for child in rule.children:
                if child.op == "eq" and child.field in {"gpa_scale", "gpa_period"}:
                    expected_gpa[child.field] = child.value
        children = [evaluate(child, profile, expected_gpa) for child in rule.children]
        decisive = False if rule.op == "all" else True
        if any(child.value is decisive for child in children):
            value, missing, staff = decisive, set(), False
        else:
            unknown = [child for child in children if child.value is None]
            value = None if unknown else not decisive
            missing = set().union(*(c.missing for c in unknown)) if unknown else set()
            staff = any(c.staff for c in unknown)
        return Evaluation(value, [reason for c in children for reason in c.reasons], missing, staff)
    actual = profile.get(rule.field) if rule.field else None
    reason = {"field": rule.field, "op": rule.op, "actual": actual, "expected": rule.value, "evidence": rule.evidence, "result": None}
    if rule.op == "needs_staff_review":
        reason["note"] = "ambiguous_condition"
        return Evaluation(None, [reason], set(), True)
    if actual is None:
        return Evaluation(None, [reason], {rule.field})
    if rule.field in {"gpa_scale", "gpa_period"} and rule.op == "eq" and actual != rule.value:
        reason["note"] = "gpa_basis_mismatch_no_conversion"
        return Evaluation(None, [reason], set(), True)
    if rule.field == "gpa_value":
        if not {"gpa_scale", "gpa_period"}.issubset(expected_gpa):
            reason["note"] = "notice_gpa_basis_missing"
            return Evaluation(None, [reason], set(), True)
        mismatched = [field for field, expected in expected_gpa.items() if profile.get(field) is not None and profile.get(field) != expected]
        missing_basis = {field for field in expected_gpa if profile.get(field) is None}
        if mismatched or missing_basis:
            reason["note"] = "gpa_basis_requires_confirmation"
            return Evaluation(None, [reason], missing_basis, bool(mismatched))
    if rule.op == "eq":
        result = actual == rule.value
    elif rule.op == "in":
        result = actual in rule.value
    elif rule.op == "gte":
        result = actual >= rule.value
    elif rule.op == "lte":
        result = actual <= rule.value
    elif rule.op == "is_true":
        result = actual is True
    else:
        result = actual is False
    reason["result"] = result
    return Evaluation(result, [reason], set())


def match_notice(notice: Notice, profile: Profile) -> dict:
    if notice.publication_status != "approved":
        raise ValueError("unreviewed notice cannot generate a formal personal conclusion")
    evaluated = evaluate(notice.eligibility_rules, profile.model_dump())
    status = "conditions_met" if evaluated.value is True else "conditions_not_met" if evaluated.value is False else "needs_staff_review" if evaluated.staff else "missing_information"
    return {"status": status, "reasons": evaluated.reasons, "missing_fields": sorted(evaluated.missing), "needs_staff_review": evaluated.staff, "notice_version": notice.version, "disclaimer": {"ko": "현재 제공한 정보로 공지의 명시 조건을 충족합니다. 최종 접수·자격 확인·선발은 학교가 결정합니다.", "zh": "按当前提供的信息满足通知明确条件；最终受理、资格核验及选拔结果由学校确认。"}}


def application_state(notice: Notice, now: datetime) -> dict:
    start = notice.application_window.opens_at
    end = notice.official_deadline or notice.application_window.closes_at
    def compare(value, is_start):
        parsed = parse_temporal(value)
        if isinstance(parsed, datetime):
            return now < parsed if is_start else now > parsed
        # Date-only precision: during the day the exact closing hour is unknown.
        return now.date() < parsed if is_start else now.date() > parsed
    if start and compare(start, True):
        state = "not_open"
    elif end and compare(end, False):
        state = "closed"
    else:
        state = "open" if start or end else "unknown"
    return {"status": state, "opens_at": start, "closes_at": end, "date_precision": "date_only" if end and len(end) == 10 else "timestamp" if end else "unknown", "deadline_time_unknown": bool(end and len(end) == 10), "needs_confirmation": bool(end and len(end) == 10 and now.date().isoformat() == end), "timezone": "Asia/Seoul", "now": now.isoformat()}
