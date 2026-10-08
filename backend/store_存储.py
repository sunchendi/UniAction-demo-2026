import json
import sqlite3
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from .fixtures_演示案例 import BASE_NOTICES, DEMO_TIME, PROFILES, SCHOOL, bi
from .models_数据模型 import Notice, Profile
from .school_migration_学校更名迁移 import migrate_school


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, school_id TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS notices (id TEXT NOT NULL, version INTEGER NOT NULL, school_id TEXT NOT NULL, publication_status TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(school_id,id,version));
                CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, student_id TEXT NOT NULL, notice_id TEXT NOT NULL, template_id TEXT NOT NULL, data TEXT NOT NULL, UNIQUE(student_id,notice_id,template_id));
                CREATE TABLE IF NOT EXISTS sharing (student_id TEXT NOT NULL, notice_id TEXT NOT NULL, scope TEXT NOT NULL, PRIMARY KEY(student_id,notice_id));
                CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, student_id TEXT NOT NULL, school_id TEXT NOT NULL, notice_id TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS submissions (student_id TEXT NOT NULL, notice_id TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(student_id,notice_id));
                CREATE TABLE IF NOT EXISTS auth_users (id TEXT PRIMARY KEY, username TEXT COLLATE NOCASE NOT NULL UNIQUE, password_hash TEXT NOT NULL, display_name TEXT NOT NULL, school_id TEXT NOT NULL, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS auth_sessions (token_hash TEXT PRIMARY KEY, student_id TEXT NOT NULL REFERENCES auth_users(id), expires_at REAL NOT NULL, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS auth_limits (bucket TEXT PRIMARY KEY, window_started REAL NOT NULL, attempts INTEGER NOT NULL);
            """)
            migrate_school(db, self.path)
            if not db.execute("SELECT 1 FROM profiles LIMIT 1").fetchone():
                self.seed(db)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def seed(self, db):
        for id, profile in PROFILES.items():
            db.execute("INSERT INTO profiles VALUES (?,?,?)", (id, profile["school_id"], encode(profile)))
        for notice in BASE_NOTICES:
            self.save_notice(Notice.model_validate(deepcopy(notice)), db)

    def reset(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM auth_users LIMIT 1").fetchone():
                raise ValueError("registered_accounts_exist")
            for table in ["tasks", "sharing", "cases", "submissions", "notices", "profiles"]:
                db.execute(f"DELETE FROM {table}")  # trusted constant table list only
            self.seed(db)

    @staticmethod
    def account_from_user(row):
        return {"id": row["id"], "role": "student", "school_id": row["school_id"], "label": bi(row["display_name"], row["display_name"]), "username": row["username"], "is_demo": False}

    def registered_account(self, student_id):
        with self.connection() as db:
            row = db.execute("SELECT * FROM auth_users WHERE id=?", (student_id,)).fetchone()
            return self.account_from_user(row) if row else None

    def registered_credentials(self, username):
        with self.connection() as db:
            row = db.execute("SELECT * FROM auth_users WHERE username=?", (username,)).fetchone()
            return dict(row) if row else None

    def register_user(self, data, password_hash, real_time):
        id = "user_" + uuid4().hex
        profile = Profile(school_id=SCHOOL, program_type=data.program_type, enrollment_status=data.enrollment_status, department_id=data.department_id)
        with self.connection() as db:
            db.execute("INSERT INTO auth_users VALUES (?,?,?,?,?,?)", (id, data.username, password_hash, data.display_name, SCHOOL, real_time))
            db.execute("INSERT INTO profiles VALUES (?,?,?)", (id, SCHOOL, encode(profile.model_dump())))
            row = db.execute("SELECT * FROM auth_users WHERE id=?", (id,)).fetchone()
            return self.account_from_user(row)

    def save_session(self, token_hash, student_id, expires_at, real_time):
        with self.connection() as db:
            db.execute("DELETE FROM auth_sessions WHERE expires_at<=?", (real_time,))
            db.execute("INSERT INTO auth_sessions VALUES (?,?,?,?)", (token_hash, student_id, expires_at, real_time))

    def session_account(self, token_hash, real_time):
        with self.connection() as db:
            row = db.execute("SELECT u.* FROM auth_users u JOIN auth_sessions s ON s.student_id=u.id WHERE s.token_hash=? AND s.expires_at>?", (token_hash, real_time)).fetchone()
            return self.account_from_user(row) if row else None

    def revoke_session(self, token_hash):
        with self.connection() as db:
            db.execute("DELETE FROM auth_sessions WHERE token_hash=?", (token_hash,))

    def auth_attempts(self, bucket, real_time, window_seconds):
        with self.connection() as db:
            row = db.execute("SELECT attempts,window_started FROM auth_limits WHERE bucket=?", (bucket,)).fetchone()
            return row["attempts"] if row and real_time - row["window_started"] < window_seconds else 0

    def record_auth_attempt(self, bucket, real_time, window_seconds):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT attempts,window_started FROM auth_limits WHERE bucket=?", (bucket,)).fetchone()
            if row and real_time - row["window_started"] < window_seconds:
                db.execute("UPDATE auth_limits SET attempts=attempts+1 WHERE bucket=?", (bucket,))
            else:
                db.execute("INSERT OR REPLACE INTO auth_limits VALUES (?,?,1)", (bucket, real_time))

    def clear_auth_attempts(self, bucket):
        with self.connection() as db:
            db.execute("DELETE FROM auth_limits WHERE bucket=?", (bucket,))

    def save_notice(self, notice, db=None):
        if db is None:
            with self.connection() as conn:
                return self.save_notice(notice, conn)
        db.execute("INSERT OR REPLACE INTO notices VALUES (?,?,?,?,?)", (notice.id, notice.version, notice.school_id, notice.publication_status, encode(notice.model_dump())))

    def notice(self, id, school_id, version=None, approved=False, db=None):
        if db is None:
            with self.connection() as conn:
                return self.notice(id, school_id, version, approved, conn)
        query, params = "SELECT data FROM notices WHERE id=? AND school_id=?", [id, school_id]
        if version is not None:
            query += " AND version=?"
            params.append(version)
        if approved:
            query += " AND publication_status='approved'"
        row = db.execute(query + " ORDER BY version DESC LIMIT 1", params).fetchone()
        return Notice.model_validate(json.loads(row[0])) if row else None

    def versions(self, id, school_id, approved_only=False):
        with self.connection() as db:
            query = "SELECT data FROM notices WHERE id=? AND school_id=?"
            if approved_only:
                query += " AND publication_status='approved'"
            return [json.loads(row[0]) for row in db.execute(query + " ORDER BY version", (id, school_id))]

    def list_notices(self, school_id, staff=False):
        with self.connection() as db:
            query = "SELECT DISTINCT id FROM notices WHERE school_id=?"
            if not staff:
                query += " AND publication_status='approved'"
            ids = [row[0] for row in db.execute(query + " ORDER BY id", (school_id,))]
            return [self.notice(id, school_id, approved=not staff, db=db) for id in ids]

    def profile(self, student_id):
        with self.connection() as db:
            row = db.execute("SELECT data FROM profiles WHERE id=?", (student_id,)).fetchone()
            return Profile.model_validate(json.loads(row[0])) if row else None

    def save_profile(self, id, profile):
        with self.connection() as db:
            db.execute("UPDATE profiles SET data=? WHERE id=? AND school_id=?", (encode(profile.model_dump()), id, profile.school_id))

    def tasks(self, student_id, notice_id, db=None):
        if db is None:
            with self.connection() as conn:
                return self.tasks(student_id, notice_id, conn)
        items = [json.loads(row[0]) for row in db.execute("SELECT data FROM tasks WHERE student_id=? AND notice_id=? ORDER BY rowid", (student_id, notice_id))]
        return [item for item in items if not item.get("removed_in_version")]

    def make_tasks(self, student_id, notice, now, db=None):
        if db is None:
            with self.connection() as conn:
                return self.make_tasks(student_id, notice, now, conn)
        for template in notice.task_templates:
            existing = db.execute("SELECT 1 FROM tasks WHERE student_id=? AND notice_id=? AND template_id=?", (student_id, notice.id, template.id)).fetchone()
            if existing:
                continue
            task = self.task_from_template(student_id, notice, template)
            self.save_task(task, db)
        return self.tasks(student_id, notice.id, db)

    @staticmethod
    def task_from_template(student_id, notice, template):
        id = f"{student_id}_{notice.id}_{template.id}"
        start = None
        if template.suggested_lead_days is not None and notice.official_deadline:
            raw = notice.official_deadline
            due = datetime.fromisoformat(raw) if len(raw) > 10 else datetime.fromisoformat(raw + "T00:00:00+09:00")
            # Suggested scheduling is explicitly date-only; do not imply an official hour.
            start = (due - timedelta(days=template.suggested_lead_days)).date().isoformat()
        return {"id": id, "student_id": student_id, "notice_id": notice.id, "notice_version": notice.version, "template_id": template.id, "title": template.title.model_dump(), "description": template.description.model_dump(), "task_type": template.task_type, "required_or_suggested": template.required_or_suggested, "source_evidence": template.source_evidence, "official_due_at": notice.official_deadline if template.uses_deadline else None, "suggested_start_at": start, "suggested_date_adjustable": True, "depends_on": [f"{student_id}_{notice.id}_{dep}" for dep in template.depends_on], "status": "todo", "changed_in_version": None, "previous_status": None}

    def save_task(self, task, db):
        db.execute("INSERT OR REPLACE INTO tasks VALUES (?,?,?,?,?)", (task["id"], task["student_id"], task["notice_id"], task["template_id"], encode(task)))

    def task(self, id):
        with self.connection() as db:
            row = db.execute("SELECT data FROM tasks WHERE id=?", (id,)).fetchone()
            return json.loads(row[0]) if row else None

    def update_task(self, id, status):
        with self.connection() as db:
            row = db.execute("SELECT data FROM tasks WHERE id=?", (id,)).fetchone()
            task = json.loads(row[0])
            task["status"] = status
            self.save_task(task, db)
            return task

    def approve_and_sync(self, notice, staff_id, now):
        with self.connection() as db:
            old = self.notice(notice.id, notice.school_id, approved=True, db=db)
            notice.publication_status = "approved"
            notice.reviewed_by, notice.reviewed_at = staff_id, now.isoformat()
            self.save_notice(notice, db)
            if old:
                students = [row[0] for row in db.execute("SELECT DISTINCT student_id FROM tasks WHERE notice_id=?", (notice.id,))]
                old_templates = {t.id: t for t in old.task_templates}
                new_templates = {t.id: t for t in notice.task_templates}
                for student_id in students:
                    for previous in self.tasks(student_id, notice.id, db):
                        key = previous["template_id"]
                        if key not in new_templates:
                            previous["removed_in_version"] = notice.version
                            self.save_task(previous, db)
                            continue
                        template = new_templates[key]
                        fresh = self.task_from_template(student_id, notice, template)
                        # Evidence context can change when the material list grows. Compare actual
                        # task semantics so unrelated completed material work remains complete.
                        fields = ["title", "description", "task_type", "required_or_suggested", "depends_on", "official_due_at"]
                        changed = any(previous.get(field) != fresh.get(field) for field in fields)
                        if template.task_type == "apply":
                            changed = changed or old.application_url != notice.application_url or old.eligibility_rules != notice.eligibility_rules
                        fresh["status"] = "requires_reconfirmation" if changed and previous["status"] == "done" else previous["status"]
                        fresh["previous_status"] = previous["status"] if changed else previous.get("previous_status")
                        fresh["changed_in_version"] = notice.version if changed else previous.get("changed_in_version")
                        self.save_task(fresh, db)
                    self.make_tasks(student_id, notice, now, db)
            return notice

    def sharing(self, student_id, notice_id, db=None):
        if db is None:
            with self.connection() as conn:
                return self.sharing(student_id, notice_id, conn)
        row = db.execute("SELECT scope FROM sharing WHERE student_id=? AND notice_id=?", (student_id, notice_id)).fetchone()
        return row[0] if row else "none"

    def set_sharing(self, student_id, notice_id, scope):
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO sharing VALUES (?,?,?)", (student_id, notice_id, scope))
            if scope == "none":
                rows = db.execute("SELECT id,data FROM cases WHERE student_id=? AND notice_id=?", (student_id, notice_id)).fetchall()
                for row in rows:
                    case = json.loads(row["data"])
                    case["access_revoked"] = True
                    db.execute("UPDATE cases SET data=? WHERE id=?", (encode(case), row["id"]))

    def create_case(self, account, data, now):
        id = uuid4().hex
        case = {"id": id, "student_id": account["id"], "school_id": account["school_id"], "notice_id": data.notice_id, "message": data.message, "sharing_scope": data.sharing_scope, "access_revoked": data.sharing_scope == "none", "status": "open", "response": "", "created_at": now.isoformat(), "updated_at": now.isoformat(), "school_application_result": "not_confirmed"}
        with self.connection() as db:
            db.execute("INSERT INTO cases VALUES (?,?,?,?,?)", (id, account["id"], account["school_id"], data.notice_id, encode(case)))
            db.execute("INSERT OR REPLACE INTO sharing VALUES (?,?,?)", (account["id"], data.notice_id, data.sharing_scope))
            if data.sharing_scope == "none":
                # The same scope change must revoke prior cases whether it comes
                # from the dedicated revoke endpoint or a newly saved private case.
                rows = db.execute("SELECT id,data FROM cases WHERE student_id=? AND notice_id=?", (account["id"], data.notice_id)).fetchall()
                for row in rows:
                    previous = json.loads(row["data"])
                    previous["access_revoked"] = True
                    db.execute("UPDATE cases SET data=? WHERE id=?", (encode(previous), row["id"]))
        return case

    def cases(self, account):
        with self.connection() as db:
            rows = db.execute("SELECT data FROM cases WHERE school_id=? ORDER BY rowid DESC", (account["school_id"],))
            result = []
            for row in rows:
                case = json.loads(row[0])
                current = self.sharing(case["student_id"], case["notice_id"], db)
                if case.get("access_revoked"):
                    current = "none"
                if account["role"] == "student" and case["student_id"] != account["id"]:
                    continue
                # Cases that were never explicitly shared stay private even if a later
                # case grants case_only access to its own necessary contents.
                if account["role"] == "staff" and (current == "none" or case["sharing_scope"] == "none"):
                    continue
                case["current_sharing_scope"] = current
                result.append(case)
            return result

    def update_case(self, id, data, now):
        with self.connection() as db:
            row = db.execute("SELECT data FROM cases WHERE id=?", (id,)).fetchone()
            case = json.loads(row[0])
            case.update(status=data.status, response=data.response, updated_at=now.isoformat())
            db.execute("UPDATE cases SET data=? WHERE id=?", (encode(case), id))
            return case

    def submission(self, student_id, notice_id):
        with self.connection() as db:
            row = db.execute("SELECT data FROM submissions WHERE student_id=? AND notice_id=?", (student_id, notice_id)).fetchone()
            return json.loads(row[0]) if row else {"status": "not_reported", "school_received": False, "school_approved": False}

    def submit(self, student_id, notice_id, version, now):
        data = {"status": "self_reported_submitted", "notice_version": version, "reported_at": now.isoformat(), "school_received": False, "school_approved": False}
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO submissions VALUES (?,?,?)", (student_id, notice_id, encode(data)))
        return data
