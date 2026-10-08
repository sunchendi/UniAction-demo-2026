# API Contract 接口契约

Base `/api`. JSON. Preset competition identities use the demo authorization header `X-Demo-Account`: A, B, C, staff, other_staff (other school). These are demo identities, not SSO. GET `/api/health` returns mode, demo_time. GET `/api/accounts` lists preset accounts.

## Personal student authentication extension / 个人学生认证扩展


| Method and path | Request | Response / behavior |
|---|---|---|
| POST `/api/auth/register` | `{username,password,display_name,program_type,enrollment_status,department_id}` | `{account}` and an HttpOnly session cookie |
| POST `/api/auth/login` | `{username,password}` | `{account}` and an HttpOnly session cookie |
| GET `/api/auth/me` | No body | `{account}` for an active session; `{account:null}` without a cookie; HTTP 401 for invalid or expired cookies |
| POST `/api/auth/logout` | No body | HTTP 200 `{account:null}`, revoke the personal session and clear its cookie, also when missing or expired |

The server sets registered accounts to `school_id: hanyang_demo` and `role: student`; clients cannot select another school or a staff role. A registered account contains `{id,role,school_id,label:{ko,zh},username,is_demo:false}`; it does not return password or session hashes. Registration must explicitly supply the supported program, enrollment and department categories. Usernames allow 3–32 ASCII letters, digits, underscore, dot or hyphen and are normalized to lowercase. Passwords require 15–128 characters; display names are trimmed and require 1–50 characters. The registration department whitelist is `engineering`, `business`, `humanities`. Remaining optional profile fields start at null, including GPA, international-student and dormitory status; personal matching still uses the existing unknown-value rules.

Passwords are hashed; only a hash of the session credential is persisted server-side. Sessions expire after 8 hours, using a real UTC clock independent of the fixed notice/demo clock. A valid personal cookie takes priority over `X-Demo-Account`; a demo header cannot impersonate a different student while a personal session is active. Invalid/expired cookies return 401 instead of falling back to a demo header. The frontend must end the personal session before selecting a preset identity. Preset headers are accepted only from local loopback clients. This is local authentication, not school SSO or production security approval. Stored personal data remains in the local runtime database, excluded from GitHub synchronization.

Implemented choices for developers: PBKDF2-SHA256 with 600,000 iterations and a random 16-byte salt; random 32-byte session tokens with only their hash stored; Origin validation for browser cross-site protection. Backend checks cover local authentication behavior; these choices are not a production security certification.

Auth error examples: HTTP 409 `username_taken`; HTTP 401 `login_error` or `session_invalid`; HTTP 422 `invalid_auth_fields` with field names, without echoing password values; HTTP 429 `rate_limited` with Retry-After. Actionable errors do not create a successful session. Limits persist in SQLite and use the real authentication clock.

The existing profile, notice, task and assistance routes below apply to the authenticated student. Staff profile visibility is not expanded. School, role and sharing-scope checks remain server-side.

## Existing notice, profile and assistance contract / 既有业务接口

GET `/api/profile`, PUT `/api/profile` student fields (body profile). GET `/api/notices` latest approved summaries (staff includes drafts). GET `/api/notices/{id}` detail with `notice`, `match` (student), `tasks`, `versions`, `application_state`, `submission_status`, `sharing_scope`. GET `/api/notices/{id}/versions` array. GET `/api/notices/{id}/versions/{version}` notice.

Notice title and task title/description are bilingual objects `{ko,zh}`. Required documents objects `{id,title,evidence}`. Evidence is exact source quote string. Rule shape `{op,field?,value?,children?,evidence}`. Match `{status,reasons:[{field,op,result,actual,expected,evidence}],missing_fields,needs_staff_review}`. Reasons `result`: true,false,null. GPA scale/period mismatch yields staff review. Profile department uses `department_id`.

POST `/api/notices/{id}/tasks` idempotent task generation. PATCH `/api/tasks/{id}` `{status}`. POST `/api/notices/{id}/submit` records self_reported_submitted. PUT `/api/notices/{id}/sharing` `{sharing_scope}`. POST `/api/cases` `{notice_id,message,sharing_scope}`. GET `/api/cases` student own/staff authorized. PATCH `/api/cases/{id}` staff `{status,response}`. GET `/api/staff/students/{student_id}/notices/{notice_id}/tasks` authorized task scope only, no profile.

GET `/api/demo/sources` array `{id,title,source_text}` incl N1-v2. POST `/api/staff/import` `{source_text,source_url,mode:'demo'|'real',notice_id?:string}` returns draft notice; errors produce actionable detail and do not publish. POST `/api/staff/manual` body notice creates manual draft. PUT `/api/staff/notices/{id}/versions/{version}` full notice edited. POST `/api/staff/notices/{id}/versions/{version}/review` moves under_review. POST `/api/staff/notices/{id}/versions/{version}/approve` validates then approves, syncing existing tasks. POST `/api/demo/reset` staff restores the fictional baseline only when no registered account exists; the new personal-data protection contract returns 409 and preserves all data otherwise. Use a separate `DATABASE_PATH` for a resettable competition database. Student results use approved version only.

All dates ISO with +09:00 or date-only without invented time. Task includes id,student_id,notice_id,notice_version,title,description,task_type,required_or_suggested,source_evidence,official_due_at,suggested_start_at,depends_on,status. `depends_on` task IDs. Version summary includes version,publication_status,change_summary. Categories scholarship,dormitory,activity.
