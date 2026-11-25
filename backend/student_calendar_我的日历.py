"""Read-only view of the student's campus deadlines and preparation dates."""

from .models_数据模型 import parse_temporal
from .rules_规则 import match_notice


def student_calendar(store, student_id, school_id, today, month):
    events = []
    with store.connection() as db:
        # The approved notice and its synchronized tasks share a read snapshot.
        db.execute("BEGIN")
        profile = store.profile(student_id, db)
        for notice in store.list_notices(school_id, db=db):
            if match_notice(notice, profile)["status"] == "conditions_not_met":
                continue
            context = {"notice_id": notice.id, "notice_title": notice.title.model_dump(), "version": notice.version}
            deadline = notice.official_deadline or notice.application_window.closes_at
            if deadline:
                when = parse_temporal(deadline).isoformat()
                if when.startswith(month + "-"):
                    events.append({
                        **context, "id": f"deadline:{notice.id}", "kind": "deadline",
                        "title": context["notice_title"], "starts_at": when, "task_id": None,
                    })

            for task in store.tasks(student_id, notice.id, db):
                start = task.get("suggested_start_at")
                if not start or task["status"] == "done" or task["notice_version"] != notice.version:
                    continue
                if start.startswith(month + "-"):
                    events.append({
                        **context, "id": f"preparation:{notice.id}:{task['template_id']}", "kind": "preparation",
                        "title": task["title"], "starts_at": start, "task_id": task["id"],
                    })

    events.sort(key=lambda event: (event["starts_at"][:10], event["kind"], event["starts_at"], event["id"]))
    return {"month": month, "today": today.isoformat(), "events": events}
