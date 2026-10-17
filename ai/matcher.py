# matcher.py - resume aur job ka match score (0 se 100)
# Idea: text -> numbers (TF-IDF vector) -> do vectors ka angle (cosine similarity)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def match_score(resume_clean, job_clean):
    """Ek resume vs ek job. 0 se 100 ke beech number.
    Same text -> 100, koi common word nahi -> 0."""
    if not resume_clean or not job_clean:
        return 0.0
    vec = TfidfVectorizer()
    try:
        m = vec.fit_transform([resume_clean, job_clean])   # 2 rows (documents) x N columns (words)
    except ValueError:            # "empty vocabulary": dono text mein sirf stopwords/garbage
        return 0.0
    score = cosine_similarity(m[0:1], m[1:2])[0][0]       # row 0 vs row 1
    return round(float(score) * 100, 1)


def score_many(base_clean, other_cleans):
    """Ek text vs bahut saare (Day 8: ek resume vs saari jobs). Scores usi order mein.
    Har pair ke liye alag fit (match_score hi loop mein) - jaan-bujh ke.
    Pehle sab texts ek saath fit kiye the (ek hi vectorizer, tez), par tab IDF is baat pe depend
    karta hai ki batch mein kaun se texts hain: same resume-job pair ko seeker page pe 46.7,
    recruiter page pe 46.0 aur 'only applicants' filter pe 41.6 mila. Ab har page pe wahi number
    aata hai jo job page (Day 7) dikhata hai. 50-100 jobs ke liye bhi ye milliseconds ka kaam hai."""
    return [match_score(base_clean, o) for o in other_cleans]


def skill_overlap(resume_skills, required_skills):
    """Job ki kitni required skills resume mein hain, 0 se 1. ['python','sql'] vs ['python','sql','aws'] -> 2/3"""
    required = set(required_skills)
    if not required:
        return 0.0
    return len(set(resume_skills) & required) / len(required)


def final_score(resume_clean, job_clean, resume_skills, required_skills):
    """70% text similarity + 30% skill overlap. App mein har jagah YAHI use hota hai.
    Kyon? Sirf TF-IDF kam number deta hai jab job description mein aur bahut words hon,
    chahe saari skills resume mein hon. Skill overlap jod ke score insaan ko sahi lagta hai."""
    text = match_score(resume_clean, job_clean)
    skills = skill_overlap(resume_skills, required_skills) * 100
    return round(0.7 * text + 0.3 * skills, 1)


if __name__ == '__main__':
    print(match_score('python flask mongodb', 'python flask mongodb'))   # 100.0
    print(match_score('python flask', 'java spring'))                    # 0.0
    print(final_score('python flask mongodb developer', 'python developer flask',
                      ['python', 'flask', 'mongodb'], ['python', 'flask']))
