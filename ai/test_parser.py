# Chalao (ai-job-portal folder se): python ai/test_parser.py
import os
from parser import extract_text

folder = os.path.join(os.path.dirname(__file__), 'sample_resumes')

for name in sorted(os.listdir(folder)):
    text = extract_text(os.path.join(folder, name))
    print('=' * 60)
    print(name, '->', len(text), 'characters')
    if not text:
        print('EMPTY: Could not read resume, upload a text PDF (scanned?)')
    else:
        print(text[:500])
