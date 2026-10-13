# Chalao (ai folder se): python test_nlp.py
# Day 3 ke sample resumes ka text nikaal kar before / after dikhata hai
import os
from parser import extract_text
from nlp import clean_text, STOPWORDS

folder = os.path.join(os.path.dirname(__file__), 'sample_resumes')

for name in sorted(os.listdir(folder)):
    raw = extract_text(os.path.join(folder, name))
    if not raw:
        print('=' * 60); print(name, '-> EMPTY (scanned?)'); continue
    clean = clean_text(raw)
    print('=' * 60)
    print(name)
    print('--- BEFORE (%d chars) ---' % len(raw)); print(raw[:300])
    print('--- AFTER  (%d chars) ---' % len(clean)); print(clean[:300])
    # End-of-day check: no capitals, no punctuation, no stopwords
    words = clean.split()
    print('CHECK: capitals=%s punctuation=%s stopwords=%s' % (
        any(c.isupper() for c in clean),
        any(not (c.isalpha() or c == ' ') for c in clean),
        [w for w in words if w in STOPWORDS]))
