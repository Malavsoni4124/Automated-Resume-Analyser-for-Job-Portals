import os
from src.parser import ResumeParser
from src.matching.engine import MatchingEngine
from src.matching.jd_parser import JDParser
from src.matching.explainer import MatchExplainer

_parser = None
_engine = None
_jd_parser = None

def get_resume_parser() -> ResumeParser:
    global _parser
    if _parser is None:
        _parser = ResumeParser()
    return _parser

def get_matching_engine() -> MatchingEngine:
    global _engine
    if _engine is None:
        _engine = MatchingEngine()
    return _engine

def get_jd_parser() -> JDParser:
    global _jd_parser
    if _jd_parser is None:
        _jd_parser = JDParser()
    return _jd_parser
