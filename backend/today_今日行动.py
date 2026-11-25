from datetime import datetime, timedelta

from .models_数据模型 import parse_temporal
from .rules_规则 import application_state, match_notice


def calendar_day(value):
    parsed = parse_temporal(value)
    return parsed.date() if isinstance(parsed, datetime) else parsed


def student_actions(store, student_id, school_id, now):
    upcoming, changes, missing = [], [], []
    horizon = now.date() + timedelta(days=7)

    with store.connection() as db:
        # Read approved notice versions and their corresponding task changes together.
        db.execute("BEGIN")
        profile = store.profile(student_id, db)
        for notice in store.list_notices(school_id, db=db):
            match = match_notice(notice, profile)
            tasks = store.tasks(student_id, notice.id, db)
            related = match["status"] != "conditions_not_met"
            entry = {"notice_id": notice.id, "title": notice.title.model_dump()}

            if notice.version > 1 and (related or tasks):
                changes.append({
                    **entry,
                    "version": notice.version,
                    "summary": notice.change_summary.model_dump(),
                    "tasks": [{"id": task["id"], "title": task["title"]} for task in tasks
                              if task["status"] == "requires_reconfirmation"],
                })

            window = application_state(notice, now)
            if not related or window["status"] == "closed":
                continue
            submission = store.submission(student_id, notice.id, db)
            if submission["status"] == "self_reported_submitted" and submission.get("notice_version") == notice.version:
                continue

            if match["missing_fields"]:
                missing.append({**entry, "fields": match["missing_fields"]})

            deadline = window["closes_at"]
            near_deadline = deadline is not None and calendar_day(deadline) <= horizon
            pending = []
            for task in tasks:
                if task["status"] == "done":
                    continue
                start = task["suggested_start_at"]
                if near_deadline or (start and calendar_day(start) <= horizon):
                    pending.append({"id": task["id"], "title": task["title"], "suggested_start_at": start})

            if near_deadline or pending:
                upcoming.append({**entry, "deadline": deadline, "match_status": match["status"], "tasks": pending})

    # Values share the campus timezone. A date-only value stays date-only.
    upcoming.sort(key=lambda entry: entry["deadline"] or "9999-12-31")
    return {"upcoming": upcoming, "changes": changes, "missing": missing}
