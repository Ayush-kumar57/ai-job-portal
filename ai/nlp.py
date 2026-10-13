# nlp.py - raw resume / job text ko saaf karta hai, taaki AI (TF-IDF) sahi compare kar sake
# Day 4: clean_text()      Day 6: extract_skills() yahan add hoga
import os
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

STOPWORDS = set(stopwords.words('english'))   # the, and, of, is, in ... (198 words)
lemmatizer = WordNetLemmatizer()

# Kuch tech words mein symbol hota hai, unko alag se bacha ke rakhte hain
KEEP = {'c++': 'cplusplus', 'c#': 'csharp', '.net': 'dotnet', 'node.js': 'nodejs'}

# skills.txt ke words ko lemmatize NAHI karte: warna 'css' -> 'cs', 'aws' -> 'aw' ho jaata hai
SKILLS_FILE = os.path.join(os.path.dirname(__file__), 'skills.txt')
with open(SKILLS_FILE, encoding='utf-8') as f:
    SKILL_WORDS = {line.strip().lower() for line in f if line.strip()}


def lemma(w):
    return w if w in SKILL_WORDS else lemmatizer.lemmatize(w)


def clean_text(text):
    """
    'Developed REST APIs in Python & Flask, 3 projects.'
      -> 'developed rest apis python flask project'
    Steps: lowercase -> special tech words -> remove punctuation/numbers
           -> remove stopwords -> lemmatize (projects -> project, databases -> database)
    """
    text = text.lower()
    for word, safe in KEEP.items():
        text = text.replace(word, ' ' + safe + ' ')
    text = re.sub(r'[^a-z\s]', ' ', text)          # sirf a-z aur space rakho
    words = text.split()                           # extra spaces/newlines khud chale jaate hain
    words = [lemma(w) for w in words
             if w not in STOPWORDS and len(w) > 1]  # 'the', 'and' aur single letters hatao
    return ' '.join(words)


if __name__ == '__main__':
    print(clean_text('Developed REST APIs in Python & Flask, 3 projects. Knows C++ and Node.js!'))
