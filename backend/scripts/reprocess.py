# Ek baar chalao (backend folder se): python scripts/reprocess.py
# Purane resumes aur jobs (jo Day 6 se pehle bane) mein clean_text aur extracted_skills bharta hai.
import os
import sys
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)                       # db, config import ke liye
sys.path.insert(0, os.path.dirname(BACKEND))      # ai package ke liye

from db import resumes, jobs
from ai.nlp import clean_text, extract_skills

n = 0
for r in resumes.find():
    resumes.update_one({'_id': r['_id']}, {'$set': {
        'clean_text': clean_text(r['raw_text']),
        'extracted_skills': extract_skills(r['raw_text'])}})
    n += 1
print(f'resumes updated: {n}')

n = 0
for j in jobs.find():
    full = f"{j['title']} {j['description']} {' '.join(j.get('required_skills', []))}"
    jobs.update_one({'_id': j['_id']}, {'$set': {'clean_text': clean_text(full)}})
    n += 1
print(f'jobs updated: {n}')
