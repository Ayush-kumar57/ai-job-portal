# Demo script and viva preparation

## Before the demo

- Start MongoDB, then `venv\Scripts\activate`, `cd backend`, `flask --app app run --debug`.
- The database is already pre-filled (do **not** drop it):
  - recruiter **ayush@gmail.com** (TechNova Solutions, Greater Noida) with 4 jobs: Python Developer,
    Data Analyst Intern, Frontend Developer, Java Developer
  - seekers **rahul@gmail.com / rahul123** (Python resume, top match Python Developer 50.9 %),
    **priya@gmail.com / priya123** (Java resume, top match Java Developer 41.6 %, has applied),
    **anita@gmail.com / anita123** (Data Analyst resume, top match Data Analyst Intern 62.4 %),
    **noresume@gmail.com / nores123** (no resume, shows the empty state)
  - admin **admin@portal.com / admin123**
- Register one throw-away seeker (e.g. `demo1@gmail.com`) before the demo so the admin delete step has
  something safe to delete.
- Keep MongoDB Compass open on a second window (database `job_portal`) to show the data if asked.
- Never type a long description live. Jobs are already posted; resumes are in `ai/sample_resumes/`.

## 5 minutes

| Minute | Shows | Say |
|---|---|---|
| 0 to 1 | Landing page. Register a seeker (or login as rahul@gmail.com). | "Too many jobs, no idea which ones fit. This portal reads the resume and scores every job from 0 to 100." |
| 1 to 2 | Resume → upload `rahul_python.pdf`. Show the extracted text and the skill badges. | "The computer just read my resume. PyMuPDF pulled the text out, and these 11 skills were found from our skills list." |
| 2 to 3 | Jobs → Python Developer: score badge, You have / Missing. Then Java Developer: lower score. | "Both texts are cleaned (lowercase, stopwords out, lemmatised), turned into TF-IDF vectors, and compared with cosine similarity. With 5 words: resume [1,1,1,1,1], job [1,1,1,0,0], cosine = 3 / (2.236 × 1.732) = 0.775, so 77.5 %. The final score is 70 % of that plus 30 % skill overlap." |
| 3 to 4 | Logout, login as the recruiter. My Jobs → Python Developer → Applications (sorted by score). Then Recommended → shows Rahul, Priya, Anita ranked, including people who did not apply. | "The recruiter sees applicants best-first, and also candidates who never applied, because every resume in the system is scored against the job." |
| 4 to 5 | Logout, login as admin. Dashboard counts → Users → delete the throw-away seeker. | "Admin sees live counts and can remove a user with everything they own. Limitation: this is word matching, so 'ML' and 'machine learning' are different unless both are in skills.txt. Next step: Sentence-BERT embeddings for meaning." |

Rehearse twice with a timer; the hard part is minute 2 to 3, keep the maths to the 5-word example.

## Viva questions

| Question | Short answer |
|---|---|
| Why Flask and not Django? | Lighter, no ORM; Django's ORM is built for SQL and we use MongoDB. |
| Why MongoDB? | Resume and job documents have flexible fields (skills lists, extracted text); our reads need no joins. |
| How is the password stored? | As a scrypt hash via Werkzeug `generate_password_hash`; at login we compare hashes, never the password. |
| What does `clean_text` do? | Lowercase, protect `c++`/`node.js`, remove non-letters, split into words, drop stopwords, lemmatise (`projects` → `project`). Skill words are not lemmatised (`css` would become `cs`). |
| What is a stopword? Give 3. | A word with no matching value: the, and, of. NLTK's English list has 198. |
| What is TF-IDF? | A number per word per document: high when the word is frequent in this document but rare across documents. TF = count here, IDF = log(N / documents containing it). |
| What is cosine similarity? | The cosine of the angle between two vectors: 1 = same direction, 0 = nothing in common. Length does not matter, so a 1-page and a 3-page resume with the same skills score the same. |
| Why the 70/30 final score? | TF-IDF alone under-weights the recruiter's required skills because a description has many other words (Rahul's resume got only 29.9 % text score with all 5 skills present); 30 % skill overlap fixes that (50.9 %). |
| What happens for a scanned PDF? | It has no text layer, `page.get_text()` returns an empty string, we delete the file and show "Could not read text". OCR is future scope. |
| How does the recruiter find people who did not apply? | `recommend_candidates` scores every seeker with a resume against the job, not only applicants; the Applied column shows who applied. |
| Why is the same score shown on every page? | TF-IDF is fitted per resume-job pair; a shared fit would change the IDF with the batch and give different numbers on different pages. |
| Why is the score saved on the application? | It is frozen at apply time in `applications.match_score`; a later resume upload does not rewrite history. |
| Biggest limitation? | Word matching, not meaning: "ML" and "machine learning" differ unless both are in `skills.txt`. |
| What would you add with more time? | Sentence-BERT embeddings, OCR for scanned resumes, email notifications, password reset, interview scheduling, MongoDB Atlas deployment. |
| Why no spaCy? | It does not install on Python 3.14; the NLTK lemmatizer does the same job for us. |
| Which part did you build? | All of it (solo project): frontend templates, Flask backend, and the AI modules. Days 1 to 10 are listed in the README and the commit history. |

## Final submission checklist

- [x] All 27 tests ticked (`docs/test_report.md`)
- [x] README complete with 3 screenshots (`docs/landing.png`, `docs/job_score.png`, `docs/recommended_candidates.png`)
- [x] `docs/db_schema.md` and `docs/routes.md` in repo
- [x] `requirements.txt` regenerated with `pip freeze`
- [x] `.gitignore` has `venv/`, `uploads/`, `__pycache__/`
- [x] Final commit "Day 10: final" pushed
- [ ] Demo rehearsed twice, under 5 minutes
- [ ] Technical Document printed or exported to PDF for submission
