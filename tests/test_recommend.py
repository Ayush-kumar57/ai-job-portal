# Chalao (ai-job-portal folder se): python -m pytest tests/
# Bina MongoDB ke test: ai/recommend.py sirf lists leta hai, DB nahi chhoota.
from ai.recommend import rank_jobs, rank_candidates, combine

python_resume = {'clean_text': 'python flask mongodb developer rest api project',
                 'extracted_skills': ['python', 'flask', 'mongodb', 'rest api']}
java_resume = {'clean_text': 'java spring boot developer hibernate project',
               'extracted_skills': ['java', 'spring boot', 'hibernate']}
python_job = {'title': 'Python Developer', 'clean_text': 'python developer flask mongodb rest api',
              'required_skills': ['python', 'flask', 'mongodb']}
java_job = {'title': 'Java Developer', 'clean_text': 'java developer spring boot hibernate',
            'required_skills': ['java', 'spring boot']}


def test_python_resume_gets_python_job_first():
    top = rank_jobs(python_resume, [dict(java_job), dict(python_job)])
    assert top[0]['title'] == 'Python Developer'
    assert top[0]['score'] > top[1]['score']
    assert top[0]['matched'] == ['python', 'flask', 'mongodb']


def test_limit():
    assert len(rank_jobs(python_resume, [dict(python_job), dict(java_job)], limit=1)) == 1


def test_empty_jobs():
    assert rank_jobs(python_resume, []) == []


def test_java_candidate_ranks_first_for_java_job():
    cands = [{'name': 'Rahul', 'resume': python_resume}, {'name': 'Priya', 'resume': java_resume}]
    ranked = rank_candidates(java_job, cands)
    assert [c['name'] for c in ranked] == ['Priya', 'Rahul']
    assert ranked[0]['matched'] == ['java', 'spring boot']


def test_combine_is_70_30():
    # text 50, overlap 1/2 -> 0.7*50 + 0.3*50 = 50
    assert combine([50.0], [['python']], [['python', 'sql']]) == [50.0]
