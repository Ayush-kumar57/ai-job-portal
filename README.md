# AI Job Portal

A job portal that reads a candidate's resume and scores how well it matches each job (0 to 100 %), so job seekers see the jobs that fit them and recruiters see candidates ranked by fit.

MCA Major Project, Galgotias University, Greater Noida. Built with Python Flask, MongoDB, NLTK and scikit-learn.

> Screenshots (landing, job details with score, recommended candidates) will be added in `docs/` on Day 10.

## Features

**Job seeker**
- Register, login, fill a profile (skills, education, experience)
- Upload a resume (PDF or DOCX); the text and skills are extracted automatically
- Browse and search open jobs; every job shows **Your match %** and the skills you have / are missing
- Apply with one click (the score is saved with the application)
- *Recommended Jobs*: top 5 open jobs ranked by match score
- Track application status (applied / shortlisted / rejected)

**Recruiter**
- Company profile; post, edit and close jobs
- Received applications sorted by match score; shortlist or reject
- *Recommended Candidates*: every seeker with a resume, ranked for a job (even those who did not apply)
- Candidate page with resume text and resume download

**Admin**
- Dashboard with live counts (users, seekers, recruiters, jobs, applications)
- Manage users (search, role filter, delete with cascade), recruiters, jobs and applications

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML, Bootstrap 5, Bootstrap Icons, Jinja2 templates |
| Backend | Python 3, Flask (blueprints, sessions) |
| Database | MongoDB (PyMongo), 6 collections |
| Resume parsing | PyMuPDF (PDF), python-docx (DOCX) |
| NLP | NLTK (stopwords, WordNet lemmatizer), regex skill extraction with `ai/skills.txt` |
| Matching | scikit-learn `TfidfVectorizer` + cosine similarity |
| Tests | pytest |

## How the AI works

1. **Parse.** When a seeker uploads a resume, `ai/parser.py` pulls the raw text out of the file: PyMuPDF reads the text layer of a PDF page by page, python-docx reads the paragraphs and tables of a DOCX. A scanned PDF has no text layer, so it is rejected.
2. **Clean.** `clean_text()` in `ai/nlp.py` lowercases the text, protects symbols that matter (`c++` becomes `cplusplus`, `node.js` becomes `nodejs`), removes everything that is not a letter, drops English stopwords (the, and, of, ...) and lemmatises the remaining words (`projects` becomes `project`). The job's title, description and skills go through the same function, so both sides use the same word forms.
3. **Extract skills.** `extract_skills()` looks for each of the 200 names in `ai/skills.txt` as a whole word in the text, longest names first ("spring boot" before "spring"). The matched skills are stored with the resume.
4. **Vectorise (TF-IDF).** `ai/matcher.py` turns the cleaned resume and the cleaned job into two number vectors with scikit-learn's `TfidfVectorizer`: one column per word, where TF counts how often the word appears in that document and IDF gives rare words (mongodb) more weight than common ones (work, experience).
5. **Compare (cosine similarity).** The similarity is the cosine of the angle between the two vectors: identical text gives 1.0, text with nothing in common gives 0. Multiplied by 100 this is the *text score*. Cosine ignores document length, so a one-page and a three-page resume with the same skills score the same.
6. **Final score = 70 % text + 30 % skill overlap.** Skill overlap is the fraction of the job's required skills that were found in the resume. Pure TF-IDF alone under-scores a good match because a job description contains many words that are not skills: for the demo Python resume against the *Python Developer* job the text score is only 29.9 even though all 5 required skills are present; with 100 % overlap the final score becomes `0.7 × 29.9 + 0.3 × 100 = 50.9`.
7. **Recommendations** are this score in a loop: a seeker's resume is scored against every open job and the top 5 are shown; a job is scored against every resume and the candidates are listed best first. Nothing is pre-computed; every page is calculated on request, and the same resume-job pair gives the same number on every page.

Score quality check (Day 9, three DOCX resumes against three jobs, the diagonal is the best match in every row):

| Resume \ Job | Python Developer | Java Developer | Data Analyst Intern |
|---|---|---|---|
| Python resume (Rahul) | **54.9** | 22.9 | 14.4 |
| Java resume (Priya) | 7.5 | **41.6** | 7.9 |
| Data Analyst resume (Anita) | 14.5 | 9.0 | **62.4** |

## Setup

```
git clone https://github.com/Ayush-kumar57/ai-job-portal.git
cd ai-job-portal
python -m venv venv
venv\Scripts\activate              # Windows
pip install -r requirements.txt
python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"
```

Start MongoDB locally (default `mongodb://localhost:27017`, database `job_portal`), then:

```
cd backend
python create_admin.py             # once: creates the admin account
flask --app app run --debug
```

Open http://127.0.0.1:5000. Run the tests from the project folder with `python -m pytest tests/`.

## Folder structure

```
ai-job-portal/
├── backend/            Flask app: app.py, config.py, db.py, utils.py, auth/ seeker/ recruiter/ admin/ blueprints, recommend.py
├── frontend/           templates/ (Jinja2) and static/ (css, js, img)
├── ai/                 parser.py, nlp.py, matcher.py, recommend.py, skills.txt, sample_resumes/
├── tests/              pytest tests for the matcher and the recommender
├── uploads/resumes/    uploaded resume files (not committed)
└── requirements.txt
```

## Default admin login

`admin@portal.com` / `admin123` (change it in `backend/create_admin.py` before deploying).

## Team

| Name | Role | Built |
|---|---|---|
| _to fill on Day 10_ | Frontend / Backend / AI | |

## Known limitations and future scope

- Matching is keyword based (TF-IDF); it does not understand synonyms or meaning. Word embeddings or a sentence-transformer model would improve this.
- Skills are recognised only if they appear in `ai/skills.txt`.
- Scanned (image) resumes are rejected; OCR could be added.
- No email notifications or password reset yet.
- Single-server deployment with local MongoDB; MongoDB Atlas and a cloud host are the next step.
