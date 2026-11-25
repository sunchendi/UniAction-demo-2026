# API Contract 接口契约

Base `/api`. JSON. Preset competition identities use the demo authorization header `X-Demo-Account`: A, B, C, staff, other_staff (other school). These are demo identities, not SSO. GET `/api/health` returns mode, demo_time. GET `/api/accounts` lists preset accounts.

## Personal student authentication extension / 个人学生认证扩展


| Method and path | Request | Response / behavior |
|---|---|---|
| GET `/api/schools` | No body | Public school, college, and major options, with Korean, Chinese, and English names |
| POST `/api/auth/register` | `{username,password,display_name,program_type,enrollment_status,school_id,college_id,major_id}` | `{account}` and an HttpOnly session cookie |
| POST `/api/auth/login` | `{username,password}` | `{account}` and an HttpOnly session cookie |
| GET `/api/auth/me` | No body | `{account}` for an active session; `{account:null}` without a cookie; HTTP 401 for invalid or expired cookies |
| POST `/api/auth/logout` | No body | HTTP 200 `{account:null}`, revoke the personal session and clear its cookie, also when missing or expired |

Registration requires a valid combination from the school catalog. The server persists the chosen Seoul (`hanyang_demo`) or ERICA (`hanyang_erica`) campus in the account and profile and assigns the student role. A registered account contains `{id,role,school_id,label:{ko,zh},username,is_demo:false}`. The profile also stores `college_id` and `major_id`, and the server derives `department_id` for existing matching rules. Profile updates may change college and major within the account's campus. Older profiles can retain their existing classification until the student chooses a college and major. Usernames allow 3–32 ASCII letters, digits, underscore, dot or hyphen and are normalized to lowercase. New passwords require 10–32 Unicode code points. Login continues to accept existing passwords up to 128 code points. Display names are trimmed and require 1–50 characters. Other optional profile fields start at null.

Passwords are hashed; only a hash of the session credential is persisted server-side. Sessions expire after 8 hours, using a real UTC clock independent of the fixed notice/demo clock. A valid personal cookie takes priority over `X-Demo-Account`; a demo header cannot impersonate a different student while a personal session is active. Invalid/expired cookies return 401 instead of falling back to a demo header. The frontend must end the personal session before selecting a preset identity. Preset headers are accepted only from local loopback clients. This is local authentication, not school SSO or production security approval. Stored personal data remains in the local runtime database, excluded from GitHub synchronization.

Implemented choices for developers: PBKDF2-SHA256 with 600,000 iterations and a random 16-byte salt; random 32-byte session tokens with only their hash stored; Origin validation for browser cross-site protection. Backend checks cover local authentication behavior; these choices are not a production security certification.

Auth error examples: HTTP 409 `username_taken`; HTTP 401 `login_error` or `session_invalid`; HTTP 422 `invalid_auth_fields` with field names, without echoing password values; HTTP 429 `rate_limited` with Retry-After. Actionable errors do not create a successful session. Limits persist in SQLite and use the real authentication clock.

The existing profile, notice, task and assistance routes below apply to the authenticated student. Staff profile visibility is not expanded. School, role and sharing-scope checks remain server-side.

## Existing notice, profile and assistance contract / 既有业务接口

GET `/api/today` gives the signed-in student a read-only summary of `{upcoming,changes,missing}` from the latest approved notices for their school and their own progress. Entries share `notice_id` and `title`. Upcoming entries include `deadline`, `match_status` and unfinished `tasks` with `id`, `title` and `suggested_start_at`. The horizon is seven campus calendar days after the server date, inclusive. Change entries include the approved `version`, `summary` and tasks that require reconfirmation. Missing entries include the matching rule’s `fields`. Dates retain their source precision.

GET `/api/calendar?month=YYYY-MM` returns `{month,today,events}` to signed-in students and defaults to the current campus month. Events have `id`, `kind`, `starts_at`, `title`, `notice_id`, `notice_title`, `version`, and nullable `task_id`. `deadline` events use the latest approved notice’s deadline. `preparation` events use suggested starts from the student's unfinished tasks on that version. Dates retain their source precision.

GET `/api/applications` returns `{today,items}` for the signed-in student's self-reported submissions at their school. Each item has `notice_id`, `title`, `reported_at`, `submitted_version`, `latest_version`, and a private `followup`. PUT `/api/applications/{id}/follow-up` saves `{status,next_check_on,note}` for an existing submission. `status` is `waiting_result`, `needs_documents`, or `result_checked`, and `next_check_on` is a campus date (`YYYY-MM-DD`) or `null`. Follow-up edits leave the school's receipt and approval flags unchanged.

GET `/api/onboarding` returns `{program_type,items}` for the signed-in student. Each applicable item includes `id`, `stage`, `title`, `steps`, `source_url` and `completed`. Stages are `before_arrival`, `first_week` and `term_start`. PUT `/api/onboarding/{item_id}` accepts `{completed: boolean}` and returns `{id,completed}`. Repeating a save is safe. An unavailable item returns 404. Progress is tied to the authenticated student, and role checks exclude staff.

GET `/api/profile`, PUT `/api/profile` student fields (body profile). GET `/api/notices` latest approved summaries (staff includes drafts). GET `/api/notices/{id}` detail with `notice`, `match` (student), `tasks`, `versions`, `application_state`, `submission_status`, `sharing_scope`. GET `/api/notices/{id}/versions` array. GET `/api/notices/{id}/versions/{version}` notice.

In the staff response to `GET /api/notices`, pending notices include advisory `review_checks` with `missing_deadline`, `missing_evidence` for rules requiring staff confirmation, and up to five `duplicates`. Each duplicate includes the same-school notice ID, title, and matching reasons (`same_source`, `same_link`, or `same_title`). Other versions of the same notice are excluded. Review and approval still use the existing validation.

Selected items in `GET /api/onboarding` and student tasks in `GET /api/notices/{id}` include optional `place` guidance. It contains the location name, building and floor, hours in KST, a visiting note, the public campus map and official sources. This guidance is calculated on read and requires no change to saved task progress.

The notice detail also provides `task_places`, keyed by document template ID, for locations supported by the current approved notice. Student Q&A reads this mapping before or after the student creates tasks and uses the existing `match`, `required_documents`, and student task statuses.

Students can call `POST /api/student-notices/preview` with `{source_text,source_url}`. Either field can supply the source. The response includes the source snapshot, title, and candidate date and material excerpts. Link-only previews read supported public Hanyang University HTTPS pages. `POST /api/student-notices` accepts the resulting text and optional link and returns `{notice_id,publication_status}`. Identical text and source links are idempotent within a school. Staff find those drafts through existing notice management, and the existing review and approval endpoints control publication.

`POST /api/student-notices/preview-email` accepts raw `.eml` bytes up to 2 MiB and returns the same preview shape with an empty `source_url`. The source snapshot contains the subject and readable message body. HTML bodies are converted to text. Previewing an email creates no draft, and students use the existing submission endpoint to send the reviewed text.

Notice title and task title/description are bilingual objects `{ko,zh}`. Required documents objects `{id,title,evidence}`. Evidence is exact source quote string. Rule shape `{op,field?,value?,children?,evidence}`. Match `{status,reasons:[{field,op,result,actual,expected,evidence}],missing_fields,needs_staff_review}`. Reasons `result`: true,false,null. GPA scale/period mismatch yields staff review. Profile department uses `department_id`.

POST `/api/notices/{id}/tasks` idempotent task generation. PATCH `/api/tasks/{id}` `{status}`. POST `/api/notices/{id}/submit` records self_reported_submitted. PUT `/api/notices/{id}/sharing` `{sharing_scope}`. POST `/api/cases` `{notice_id,message,sharing_scope}`. GET `/api/cases` student own/staff authorized. PATCH `/api/cases/{id}` staff `{status,response}`. GET `/api/staff/students/{student_id}/notices/{notice_id}/tasks` authorized task scope only, no profile.

GET `/api/demo/sources` array `{id,title,source_text}` incl N1-v2. POST `/api/staff/import` `{source_text,source_url,mode:'demo'|'real',notice_id?:string}` returns draft notice; errors produce actionable detail and do not publish. POST `/api/staff/manual` body notice creates manual draft. PUT `/api/staff/notices/{id}/versions/{version}` full notice edited. POST `/api/staff/notices/{id}/versions/{version}/review` moves under_review. POST `/api/staff/notices/{id}/versions/{version}/approve` validates then approves, syncing existing tasks. POST `/api/demo/reset` staff restores the fictional baseline only when no registered account exists; the new personal-data protection contract returns 409 and preserves all data otherwise. Use a separate `DATABASE_PATH` for a resettable competition database. Student results use approved version only.

All dates ISO with +09:00 or date-only without invented time. Task includes id,student_id,notice_id,notice_version,title,description,task_type,required_or_suggested,source_evidence,official_due_at,suggested_start_at,depends_on,status. `depends_on` task IDs. Version summary includes version,publication_status,change_summary. Categories scholarship,dormitory,activity.
