# Day 10 test report

Date: 21 October 2026. Result: **27 / 27 passed**, no code changes were needed.

How it was run: rows 1 to 25 were executed in order with the Flask test client against a **fresh, separate
database** (`job_portal_test`, dropped first, admin created with the same code as `create_admin.py`, dropped
again at the end) so that the demo data in `job_portal` stayed untouched. Row 26 is `python -m pytest tests/`.
Row 27 was a real `git clone` of the repository into an empty folder, a new `venv`, `pip install -r
requirements.txt`, the NLTK downloads, pytest, `create_admin.py` and a request to `/`, exactly as the README
says. The three README screenshots in this folder were taken from the same test database.

Test data: seeker **Riya Sharma** (riya@gmail.com), recruiter **Amit Verma** (amit@gmail.com, Skyline
Softwares), three jobs posted by Amit (Python Developer, Java Developer, Data Analyst), resume
`ai/sample_resumes/rahul_python.pdf` uploaded by Riya.

| # | Test | Expected | Observed | Pass |
|---|---|---|---|---|
| 1 | Open `/` logged out | Landing page, Login/Register in navbar | 200, landing page, both links present | ✅ |
| 2 | Register seeker Riya, recruiter Amit | Both in `users` with hashes | both rows present, `password_hash` starts with `scrypt:`, no plain password | ✅ |
| 3 | Register with same email again | "Email already registered" | flash shown, still one user with that email | ✅ |
| 4 | Login wrong password | "Wrong email or password" | flash shown | ✅ |
| 5 | Login Amit, fill company, post 3 jobs | 3 jobs in My Jobs, `clean_text` filled | 3 jobs, company name copied, `clean_text` e.g. "python developer need python developer b…" | ✅ |
| 6 | Login Riya, open `/recruiter/jobs` | Redirected to login with warning | 302 → `/login`, "Please login as recruiter" | ✅ |
| 7 | Riya fills profile | Saved, skills lowercase list | `"Python, SQL , Flask"` → `['python', 'sql', 'flask']` | ✅ |
| 8 | Riya browses jobs, searches "java" | Only Java job shown | only Java Developer in results | ✅ |
| 9 | Riya opens a job without a resume | "Upload a resume to see your match" | badge shown, no score | ✅ |
| 10 | Riya applies without resume | Redirected to Upload Resume | 302 → `/seeker/resume`, "Upload your resume before applying", 0 applications | ✅ |
| 11 | Upload `.txt` | Rejected | "Only PDF or DOCX allowed", nothing stored | ✅ |
| 12 | Upload scanned PDF | "Could not read text" | message shown, file removed from disk, nothing stored | ✅ |
| 13 | Upload Python resume PDF | Text preview + skills badges | preview shown, 11 skills: python, flask, django, mysql, git, mongodb, html, css, rest api, javascript, pytest | ✅ |
| 14 | Open Python job | Score 60+, green/yellow badge; have/missing correct | **61.8 %**, yellow badge, You have 5/5, Missing 0 | ✅ |
| 15 | Open Java job | Lower score than Python job | 11.7 % < 61.8 % | ✅ |
| 16 | Recommended Jobs | Python job on top | order: Python Developer, Java Developer, Data Analyst | ✅ |
| 17 | Apply to Python job, then again | Success, then "already applied" | "Applied successfully", then "You already applied to this job"; 1 application | ✅ |
| 18 | My Applications | Row with score and status "applied" | Python Developer, 61.8 %, applied | ✅ |
| 19 | Amit: Received Applications | Riya with score; Shortlist works | Riya 61.8 %; "Candidate marked as shortlisted", status updated | ✅ |
| 20 | Amit: Recommended Candidates for Java job | Riya listed, Applied = No | Riya 11.7 %, Applied = No | ✅ |
| 21 | Amit: View profile, Download resume | File downloads | profile 200; download 200, `attachment; filename=rahul_python.pdf`, PDF bytes | ✅ |
| 22 | Amit: edit job, close job | Changes visible; closed job hidden from Riya | title "Python Developer (Flask)" visible; Data Analyst closed and absent from Riya's job list | ✅ |
| 23 | Admin dashboard | Counts correct | cards 3 / 1 / 1 / 3 / 1 (users / seekers / recruiters / jobs / applications) = MongoDB counts | ✅ |
| 24 | Admin deletes Riya | Resume, profile, applications gone | user, profile, resume record **and file on disk**, application all gone | ✅ |
| 25 | Admin tries to delete admin | Blocked | "Admin account cannot be deleted", admin still present | ✅ |
| 26 | `python -m pytest tests/` | All pass | 11 passed in 1.85 s | ✅ |
| 27 | Fresh clone following README | Runs | clone → venv → pip install (exit 0) → NLTK data → 11 tests pass → `GET /` 200 → `create_admin.py` creates admin | ✅ |

Notes

- Scores depend on the job description text. With the demo data in `job_portal` (TechNova Solutions jobs)
  the same resume scores 50.9 % on Python Developer; with the shorter, more focused test description it
  scores 61.8 %. The ordering (Python > Java) is the same in both.
- The score on the job page became 62.2 % after row 22, because editing the title to "Python Developer
  (Flask)" adds the word *flask* to the job's `clean_text`. Scores saved on applications do not change.
