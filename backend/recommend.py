# recommend.py (backend) - DB se data uthao, ai/recommend.py se rank karao.
# Saare DB reads yahan hain taaki routes chhote rahein.
# Kuch bhi store nahi hota: recommendation har request pe fresh compute hoti hai (table change: none).
from db import jobs, resumes, job_seekers, users, applications
from utils import to_oid
from ai.recommend import rank_jobs, rank_candidates


def recommend_jobs(seeker_id, limit=5):
    """Seeker ke latest resume ke liye top open jobs. Resume nahi -> None (template empty state dikhayega)."""
    p = job_seekers.find_one({'user_id': seeker_id}) or {}
    r = resumes.find_one({'_id': to_oid(p['resume_id'])}) if p.get('resume_id') else None
    if not r:
        return None
    # sirf open jobs jinka clean_text bana hua hai (Day 6 se pehle wali purani jobs skip)
    open_jobs = list(jobs.find({'status': 'open', 'clean_text': {'$nin': ['', None]}}))
    return rank_jobs(r, open_jobs, limit)


def recommend_candidates(job_id, only_applicants=False, limit=None):
    """Is job ke liye saare seekers jinke paas resume hai, score ke hisaab se ranked.
    Apply na kiya ho tab bhi list mein aate hain (candidate discovery) - 'applied' flag batata hai."""
    job = jobs.find_one({'_id': to_oid(job_id)})
    if not job:
        return []
    # Ek hi query mein is job ke saare applicants (loop ke andar nahi)
    applied = {a['seeker_id'] for a in applications.find({'job_id': job_id}, {'seeker_id': 1})}

    profiles = list(job_seekers.find({'resume_id': {'$exists': True, '$nin': ['', None]}}))
    if only_applicants:
        profiles = [p for p in profiles if p['user_id'] in applied]
    if not profiles:
        return []

    # Batch lookup: N find_one ki jagah ek-ek find with $in (50 candidates = 2 queries, 100 nahi)
    resume_map = {str(r['_id']): r for r in resumes.find(
        {'_id': {'$in': [to_oid(p['resume_id']) for p in profiles]}})}
    user_map = {str(u['_id']): u for u in users.find(
        {'_id': {'$in': [to_oid(p['user_id']) for p in profiles]}}, {'name': 1, 'email': 1})}

    candidates = []
    for p in profiles:
        r, u = resume_map.get(p['resume_id']), user_map.get(p['user_id'])
        if not r or not u:                    # resume/user delete ho gaya ho toh skip
            continue
        candidates.append({'seeker_id': p['user_id'], 'name': u['name'], 'email': u['email'],
                           'applied': p['user_id'] in applied, 'resume': r})
    return rank_candidates(job, candidates, limit)
