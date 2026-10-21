# Database schema

MongoDB, database `job_portal`, six collections. Every id that points to another collection is stored as a
**string** (`str(ObjectId)`), because the same id also travels in URLs and in the session; `utils.to_oid()`
converts it back when a lookup is needed. There are no joins: pages that need the job title or the candidate
name do a second lookup (one `$in` query for a whole page, not one query per row).

Created in `backend/db.py`. Indexes:

| Collection | Index | Why |
|---|---|---|
| users | `email` unique | one email = one account |
| applications | `(job_id, seeker_id)` unique | a seeker can apply to a job only once; the database raises `DuplicateKeyError` on a second apply |

## 1. users (Day 2)

One row per account, all three roles.

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | |
| `name` | string | |
| `email` | string | lowercase, unique |
| `password_hash` | string | Werkzeug `generate_password_hash` (scrypt); the password itself is never stored |
| `role` | string | `seeker`, `recruiter` or `admin` (admin only via `create_admin.py`, the register form refuses it) |
| `created_at` | datetime | |

## 2. job_seekers (Day 4, Day 5)

Profile of a seeker; created with `upsert=True` the first time the profile or a resume is saved.

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | |
| `user_id` | string | `users._id` |
| `phone` | string | |
| `skills` | list of string | lowercase, e.g. `['python', 'sql']` (typed by the seeker) |
| `experience_years` | float | |
| `education` | string | |
| `location` | string | |
| `resume_id` | string | `resumes._id` of the **latest** uploaded resume; missing until the first upload |

## 3. recruiters (Day 3)

Company profile of a recruiter (`upsert=True`).

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | |
| `user_id` | string | `users._id` |
| `company_name` | string | copied onto every job the recruiter posts |
| `company_website` | string | |
| `about` | string | |
| `location` | string | |

## 4. jobs (Day 3, Day 6)

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | |
| `recruiter_id` | string | `users._id` of the recruiter; every recruiter query filters on it |
| `company_name` | string | from the recruiter profile at posting time |
| `title` | string | |
| `description` | string | |
| `required_skills` | list of string | lowercase, from the comma separated form field |
| `location` | string | |
| `job_type` | string | Full-time / Internship / Part-time |
| `salary_range` | string | |
| `clean_text` | string | `clean_text(title + description + skills)`; the text TF-IDF compares with a resume |
| `status` | string | `open` or `closed`; seekers only see open jobs |
| `created_at` | datetime | |

## 5. resumes (Day 5, Day 6)

One row per upload. A seeker can upload many times; `job_seekers.resume_id` points to the newest.

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | |
| `user_id` | string | `users._id` of the seeker |
| `file_name` | string | original name, passed through `secure_filename` (used for downloads) |
| `file_path` | string | where the file is on disk: `uploads/resumes/<user_id>_<timestamp>.<ext>` |
| `file_type` | string | `pdf` or `docx` |
| `raw_text` | string | text extracted by `ai/parser.py`; an upload with fewer than 50 characters is rejected |
| `clean_text` | string | `clean_text(raw_text)` for TF-IDF |
| `extracted_skills` | list of string | `extract_skills(raw_text)`, the names from `ai/skills.txt` found in the text |
| `uploaded_at` | datetime | |

## 6. applications (Day 4, Day 7)

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | |
| `job_id` | string | `jobs._id` |
| `seeker_id` | string | `users._id` of the seeker |
| `resume_id` | string | the resume that was current when the seeker applied |
| `status` | string | `applied`, `shortlisted` or `rejected` (changed by the recruiter) |
| `match_score` | float | `final_score()` at apply time, 0 to 100; frozen, a later resume upload does not change it |
| `applied_at` | datetime | |

## Relationships

```
users ──1:1── job_seekers ──1:n── resumes
  │                │
  │                └──1:n── applications ──n:1── jobs ──n:1── recruiters ──1:1── users
  └──1:1── recruiters
```

Admin cascade delete (`admin.delete_user_everything`): resumes (records and files on disk), job_seekers,
applications made by the user, recruiters, the user's jobs and the applications on those jobs, then the
user. Recommendations are **not** stored anywhere; they are computed on every request.
