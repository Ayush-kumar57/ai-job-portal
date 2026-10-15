# nlp.py - raw resume / job text ko saaf karta hai, taaki AI (TF-IDF) sahi compare kar sake
# Day 4: clean_text()      Day 6: extract_skills()
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
# Lambi skills pehle check hoti hain: 'spring boot' pehle, phir 'spring'; 'c++' pehle, phir 'c'
SKILLS = sorted(SKILL_WORDS, key=len, reverse=True)


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


def extract_skills(text):
    """
    skills.txt ki jo skills text mein milti hain, unki list (jis order mein text mein aayi).
    - poore word ka match: 'c' 'communication' ke andar nahi milega
    - jo skill mil gayi, uska text mita dete hain, taaki 'c++' milne ke baad 'c' dobara na mile
    - 1-2 letter wali skills (c, r, go) sirf list jaise context mein: "C, Java" ya "R | Python"
    """
    # lowercase; hyphen ko space ('go-getter' -> 'go getter'); letters, digits, + # . space rakho;
    # baaki (comma, slash, pipe, colon...) ko '|' separator bana do
    text = text.lower().replace('-', ' ')
    text = '|' + re.sub(r'[^a-z0-9+#.\s]', '|', text) + '|'
    found = {}                                     # skill -> text mein pehli position
    for skill in SKILLS:
        name = skill.replace('-', ' ')             # 'scikit-learn' bhi text jaisa 'scikit learn' ban jaaye
        if len(skill) <= 2:
            # chhoti skill: dono taraf separator (| ya line break) hona chahiye, beech mein sirf space
            pattern = r'(?<=[|\n])[ \t]*' + re.escape(skill) + r'[ \t]*(?=[|\n])'
        else:
            pattern = r'(?<![a-z0-9])' + re.escape(name) + r'(?![a-z0-9])'
        m = re.search(pattern, text)
        if m:
            found[skill] = m.start()
            text = re.sub(pattern, '|', text)     # mil gayi -> text se hata do
    return sorted(found, key=found.get)           # text ke order mein


if __name__ == '__main__':
    print(clean_text('Developed REST APIs in Python & Flask, 3 projects. Knows C++ and Node.js!'))
    print(extract_skills('Languages: C, Java, C++. Good communication, go-getter. Spring Boot, node.js, React Native'))
