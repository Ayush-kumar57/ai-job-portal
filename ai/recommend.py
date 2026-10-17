# recommend.py - recommendation = scoring in a loop + sorting. Koi magic nahi.
# Seeker ke liye: har open job ko score do, sort karo, top N dikhao.
# Recruiter ke liye: har resume ko is job ke against score do, sort karo.
# Yahan DB nahi hai (sirf lists in, lists out) taaki pytest se bina MongoDB ke test ho sake.
# DB se data uthane ka kaam backend/recommend.py karta hai.
from ai.matcher import score_many, skill_overlap


def combine(text_scores, resume_skills_list, required_skills_list):
    """Day 7 ka 70/30 rule, par ek saath poori list pe (final_score ka list-version)."""
    out = []
    for t, rs, req in zip(text_scores, resume_skills_list, required_skills_list):
        out.append(round(0.7 * t + 0.3 * skill_overlap(rs, req) * 100, 1))
    return out


def rank_jobs(resume, jobs, limit=5):
    """Ek resume vs bahut si jobs. Har job dict mein 'score' aur 'matched' jodta hai,
    score ke hisaab se (high -> low) sort karke top `limit` lautata hai."""
    jobs = list(jobs)
    if not jobs:
        return []
    # score_many: ek hi TfidfVectorizer fit sab texts pe -> loop mein match_score se tez
    text_scores = score_many(resume.get('clean_text', ''), [j.get('clean_text', '') for j in jobs])
    scores = combine(text_scores,
                     [resume.get('extracted_skills', [])] * len(jobs),
                     [j.get('required_skills', []) for j in jobs])
    mine = set(resume.get('extracted_skills', []))
    for s, j in zip(scores, jobs):                 # zip: har score ko uski job ke saath pair karo
        j['score'] = s
        j['matched'] = [k for k in j.get('required_skills', []) if k in mine]
    jobs.sort(key=lambda j: j['score'], reverse=True)   # key = kis field se sort, reverse = bada pehle
    return jobs[:limit] if limit else jobs


def rank_candidates(job, candidates, limit=None):
    """Ek job vs bahut se candidates. candidates = list of dicts, har ek mein 'resume' key (resume doc).
    Har candidate mein 'score' aur 'matched' jodta hai, sorted (high -> low)."""
    candidates = list(candidates)
    if not candidates:
        return []
    res = [c['resume'] for c in candidates]
    text_scores = score_many(job.get('clean_text', ''), [r.get('clean_text', '') for r in res])
    scores = combine(text_scores,
                     [r.get('extracted_skills', []) for r in res],
                     [job.get('required_skills', [])] * len(res))
    required = job.get('required_skills', [])
    for s, c, r in zip(scores, candidates, res):
        c['score'] = s
        c['matched'] = [k for k in required if k in r.get('extracted_skills', [])]
    candidates.sort(key=lambda c: c['score'], reverse=True)
    return candidates[:limit] if limit else candidates
