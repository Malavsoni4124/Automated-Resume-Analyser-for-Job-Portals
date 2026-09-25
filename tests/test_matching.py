import pytest
from src.matching.engine import MatchingEngine
from src.matching.jd_parser import JDParser
from src.schema import ResumeSchema, Experience

@pytest.fixture
def engine():
    return MatchingEngine()

@pytest.fixture
def parser():
    return JDParser()

def test_interval_union_experience(engine):
    exp1 = Experience(start_date="2020-01-01", end_date="2022-01-01") # 2 years
    exp2 = Experience(start_date="2021-01-01", end_date="2023-01-01") # overlapping, total span 2020-2023 = 3 years
    
    total = engine.calculate_total_experience_years([exp1, exp2])
    assert 2.9 < total < 3.1 # ~3 years
    
def test_zero_overlap_skills(engine):
    from src.schema import JobDescriptionSchema
    jd = JobDescriptionSchema(skills=["Python", "AWS"])
    resume = ResumeSchema(skills=["Java", "C++"])
    
    score = engine.score_skills(jd, resume)
    assert score == 0.0

def test_high_skill_low_exp(engine, parser):
    jd = parser.parse("Requires Python and AWS. 5 years experience required.")
    
    # Candidate has skills but only 1 year exp
    exp = Experience(start_date="2022-01-01", end_date="2023-01-01")
    resume = ResumeSchema(skills=["Python", "AWS"], experience=[exp])
    
    skill_score = engine.score_skills(jd, resume)
    exp_score = engine.score_experience(jd, resume)
    
    assert skill_score == 1.0
    assert 0.1 < exp_score < 0.3 # 1 / 5 = 0.2

def test_malformed_jd(engine, parser):
    # Missing all fields
    jd = parser.parse("")
    assert jd.min_years_experience == 0
    assert not jd.skills
    assert jd.required_degree is None
    
    resume = ResumeSchema(skills=["Python"])
    
    # Should not crash and should return 1.0 for missing requirements
    assert engine.score_skills(jd, resume) == 1.0
    assert engine.score_experience(jd, resume) == 1.0
    assert engine.score_education(jd, resume) == 1.0
