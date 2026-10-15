# Chalao (ai-job-portal folder se): python -m pytest tests/
from ai.matcher import match_score, score_many, skill_overlap, final_score


def test_same_text_is_100():
    assert match_score('python flask mongodb', 'python flask mongodb') == 100.0


def test_no_overlap_is_0():
    assert match_score('python flask', 'java spring') == 0.0


def test_ranking():
    scores = score_many('python flask mongodb developer',
                        ['python developer flask', 'java spring developer'])
    assert scores[0] > scores[1]


def test_overlap():
    assert skill_overlap(['python', 'sql'], ['python', 'sql', 'aws']) == 2 / 3


def test_empty_text_does_not_crash():
    assert match_score('', 'python') == 0.0
    assert score_many('python', ['', '']) == [0.0, 0.0]


def test_final_score_all_skills_present():
    s = final_score('python flask mongodb', 'python flask mongodb', ['python', 'flask'], ['python', 'flask'])
    assert s == 100.0
