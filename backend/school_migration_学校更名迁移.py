"""Rename this prototype's school identity without deleting user-owned data.

The old name is retained only as a migration lookup. The untouched SQLite
backup is private runtime data; manually imported original texts are preserved.
"""
import json
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from .fixtures_演示案例 import BASE_NOTICES, N1_V2, SCHOOL, SCHOOL_NAME

LEGACY_SCHOOL = "hanbit_demo"
RENAMES = (
    ("Hanbit Demo University / 한빛 데모대학교", SCHOOL_NAME),
    ("[가상 데모 공지 · 실제 학교 공지가 아닙니다]", "[가상 데모 공지 · 한양대학교 공식 공지가 아닙니다]"),
    ("https://demo.invalid/hanbit/", "https://demo.invalid/hanyang/"),
    ("demo-office@hanbit.invalid", "demo-office@hanyang.invalid"),
)


def rename_demo_text(text):
    for old, new in RENAMES:
        text = text.replace(old, new)
    return text


def legacy_demo_text(text):
    for old, new in reversed(RENAMES):
        text = text.replace(new, old)
    return text


def rename_fixture_value(value):
    if isinstance(value, str):
        return SCHOOL if value == LEGACY_SCHOOL else rename_demo_text(value)
    if isinstance(value, list):
        return [rename_fixture_value(item) for item in value]
    if isinstance(value, dict):
        return {key: rename_fixture_value(item) for key, item in value.items()}
    return value


def migrate_school(db, path):
    db.execute("BEGIN IMMEDIATE")
    legacy_profiles = db.execute("SELECT id,data FROM profiles WHERE school_id=?", (LEGACY_SCHOOL,)).fetchall()
    legacy_notices = db.execute("SELECT id,version,data FROM notices WHERE school_id=?", (LEGACY_SCHOOL,)).fetchall()
    legacy_cases = db.execute("SELECT id,data FROM cases WHERE school_id=?", (LEGACY_SCHOOL,)).fetchall()
    has_users = db.execute("SELECT 1 FROM auth_users WHERE school_id=? LIMIT 1", (LEGACY_SCHOOL,)).fetchone()
    if not (legacy_profiles or legacy_notices or legacy_cases or has_users):
        return False

    # A consistent backup is made before the first mutation. No account, password,
    # session, consent, progress or original source is removed by this migration.
    backups = Path(path).parent / "backups"
    backups.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = backups / f"SchoolRename_学校更名_{stamp}_{uuid4().hex[:8]}.sqlite3"
    with sqlite3.connect(str(path)) as source, sqlite3.connect(target) as backup:
        source.backup(backup)

    fixed_sources = {legacy_demo_text(notice["source_text"]) for notice in [*BASE_NOTICES, N1_V2]}
    fixed_evidence = {legacy_demo_text(task["source_evidence"]) for notice in [*BASE_NOTICES, N1_V2] for task in notice["task_templates"]}
    for row in legacy_profiles:
        profile = json.loads(row["data"])
        profile["school_id"] = SCHOOL
        db.execute("UPDATE profiles SET school_id=?,data=? WHERE id=?", (SCHOOL, json.dumps(profile, ensure_ascii=False), row["id"]))
    db.execute("UPDATE auth_users SET school_id=? WHERE school_id=?", (SCHOOL, LEGACY_SCHOOL))
    for row in legacy_notices:
        notice = json.loads(row["data"])
        raw = notice["source_text"]
        if raw in fixed_sources and notice["source_hash"] == sha256(raw.encode("utf-8")).hexdigest():
            notice = rename_fixture_value(notice)
            notice["source_hash"] = sha256(notice["source_text"].encode("utf-8")).hexdigest()
        notice["school_id"] = SCHOOL
        db.execute("UPDATE notices SET school_id=?,data=? WHERE school_id=? AND id=? AND version=?", (SCHOOL, json.dumps(notice, ensure_ascii=False), LEGACY_SCHOOL, row["id"], row["version"]))
    for row in legacy_profiles:
        for task_row in db.execute("SELECT id,data FROM tasks WHERE student_id=?", (row["id"],)).fetchall():
            task = json.loads(task_row["data"])
            if task.get("source_evidence") in fixed_evidence:
                task["source_evidence"] = rename_demo_text(task["source_evidence"])
                db.execute("UPDATE tasks SET data=? WHERE id=?", (json.dumps(task, ensure_ascii=False), task_row["id"]))
    for row in legacy_cases:
        case = json.loads(row["data"])
        case["school_id"] = SCHOOL
        db.execute("UPDATE cases SET school_id=?,data=? WHERE id=?", (SCHOOL, json.dumps(case, ensure_ascii=False), row["id"]))
    return True
