# Routes

All routes live in `backend/`. Role checks are done by the `@role_required(role)` decorator in `utils.py`:
a user with the wrong role (or no login) is redirected to `/login` with the warning "Please login as …".
Every action that changes data is a `POST` form, never a link.

## Public (`app.py`, `auth/routes.py`)

| Method | URL | Function | What it does | Day |
|---|---|---|---|---|
| GET | `/` | `index` | Landing page with live counts (open jobs, seekers, recruiters) | 1, 3 |
| GET, POST | `/register` | `auth.register` | Create a seeker or recruiter account; rejects a duplicate email and `role=admin` | 2 |
| GET, POST | `/login` | `auth.login` | Check the password hash, store `user_id`, `name`, `role` in the session, redirect to the role's dashboard | 2 |
| GET | `/logout` | `auth.logout` | Clear the session | 2 |
| GET | `/forgot-password` | `auth.forgot` | Static page (no email sending; future scope) | 2 |
| POST | `/api/score` | `api_score` | JSON `{"resume": "...", "job": "..."}` → `{"score", "resume_skills", "job_skills"}` (demo / Postman) | 7 |
| GET | `/db-test` | `db_test` | Day 1 connection check | 1 |

## Job seeker (`seeker/routes.py`, blueprints `seeker` and `jobs`, role `seeker`)

| Method | URL | Function | What it does | Day |
|---|---|---|---|---|
| GET | `/seeker/dashboard` | `seeker.dashboard` | Counts (applied, shortlisted), profile status, top 3 recommended jobs | 2, 8 |
| GET, POST | `/seeker/profile` | `seeker.profile` | Phone, location, skills (comma list → lowercase list), experience, education; `upsert` | 4 |
| GET, POST | `/seeker/resume` | `seeker.resume` | Upload PDF/DOCX (max 2 MB): extract text, clean it, extract skills, save; shows the text preview and skill badges | 5, 6 |
| GET | `/seeker/resume/download` | `seeker.resume_download` | Download own resume file | 5 |
| GET | `/jobs?q=` | `jobs.browse` | Open jobs, newest first; `q` searches the title (regex, case-insensitive) or the skills list | 4 |
| GET | `/jobs/<id>` | `jobs.detail` | Job page with **Your match %**, "You have / Missing" skill badges, Apply button | 4, 6, 7 |
| POST | `/jobs/<id>/apply` | `jobs.apply` | Needs a resume; saves the application with the score; duplicate apply is blocked by the unique index | 4, 5, 7 |
| GET | `/seeker/recommended` | `seeker.recommended` | Top 5 open jobs for the latest resume (`None` = no resume yet) | 8 |
| GET | `/seeker/applications` | `seeker.my_applications` | Own applications with job title, score and status | 4, 7 |

## Recruiter (`recruiter/routes.py`, prefix `/recruiter`, role `recruiter`)

Every query includes `recruiter_id = session user`, so a recruiter can only see and change their own jobs
and the applications on them.

| Method | URL | Function | What it does | Day |
|---|---|---|---|---|
| GET | `/recruiter/dashboard` | `recruiter.dashboard` | Job counts, company status, top 3 candidates for the newest job | 2, 8 |
| GET, POST | `/recruiter/company` | `recruiter.company` | Company profile (`upsert`) | 3 |
| GET, POST | `/recruiter/jobs/new` | `recruiter.new_job` | Post a job; stores `clean_text` of title + description + skills | 3, 6 |
| GET | `/recruiter/jobs` | `recruiter.my_jobs` | Own jobs with Edit / Applications / Recommended / Close | 3 |
| GET, POST | `/recruiter/jobs/<id>/edit` | `recruiter.edit_job` | Edit a job (recomputes `clean_text`) | 3 |
| POST | `/recruiter/jobs/<id>/close` | `recruiter.close_job` | `status = closed`; hidden from seekers, apply refused | 3 |
| GET | `/recruiter/jobs/<id>/applications` | `recruiter.job_applications` | Received applications sorted by score, with Shortlist / Reject buttons | 4, 7 |
| POST | `/recruiter/applications/<id>/status` | `recruiter.set_status` | Set `applied` / `shortlisted` / `rejected` (only on own jobs) | 4 |
| GET | `/recruiter/jobs/<id>/recommended?applicants=0|1` | `recruiter.recommended` | Every seeker with a resume ranked for this job; `applicants=1` shows only applicants | 8 |
| GET | `/recruiter/candidates/<seeker_id>` | `recruiter.candidate` | Profile + extracted resume text of a seeker who applied to one of my jobs or has a resume | 5, 8 |
| GET | `/recruiter/candidates/<seeker_id>/download` | `recruiter.candidate_download` | Download that candidate's resume file (same visibility rule) | 9 |

## Admin (`admin/routes.py`, prefix `/admin`, role `admin`)

Read and delete over all collections, no owner filter.

| Method | URL | Function | What it does | Day |
|---|---|---|---|---|
| GET | `/admin/dashboard` | `admin.dashboard` | 5 counts (users, seekers, recruiters, jobs, applications), newest users, latest applications | 9 |
| GET | `/admin/users?q=&role=` | `admin.manage_users` | All users; search name/email, filter by role | 9 |
| POST | `/admin/users/<id>/delete` | `admin.delete_user` | Cascade delete (profile, resumes + files, applications, jobs); refuses to delete an admin | 9 |
| GET | `/admin/recruiters` | `admin.manage_recruiters` | Company profiles with job counts; recruiter accounts without a profile listed below | 9 |
| GET | `/admin/jobs?status=` | `admin.manage_jobs` | All jobs with application counts; filter open/closed | 9 |
| POST | `/admin/jobs/<id>/delete` | `admin.delete_job` | Delete a job and its applications | 9 |
| GET | `/admin/applications?status=` | `admin.manage_applications` | All applications with job and seeker; filter by status | 9 |
| POST | `/admin/applications/<id>/delete` | `admin.delete_application` | Delete one application | 9 |

## Helper modules (no routes)

| File | Functions | Used by |
|---|---|---|
| `backend/utils.py` | `role_required(role)`, `to_oid(id)` | all blueprints |
| `backend/recommend.py` | `recommend_jobs(seeker_id, limit)`, `recommend_candidates(job_id, only_applicants, limit)` (DB reads) | seeker + recruiter routes |
| `ai/parser.py` | `extract_text(path)` | resume upload |
| `ai/nlp.py` | `clean_text(text)`, `extract_skills(text)` | upload, post/edit job, `/api/score` |
| `ai/matcher.py` | `match_score`, `score_many`, `skill_overlap`, `final_score` | job page, apply, `/api/score`, recommendations |
| `ai/recommend.py` | `rank_jobs(resume, jobs, limit)`, `rank_candidates(job, candidates, limit)` (pure, no DB) | `backend/recommend.py`, tests |
