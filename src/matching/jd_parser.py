import re
from typing import Optional
from ..schema import JobDescriptionSchema
from ..extractors.skill_matcher import SkillMatcher

class JDParser:
    def __init__(self, skill_matcher: Optional[SkillMatcher] = None):
        self.skill_matcher = skill_matcher or SkillMatcher()
        
        # Heuristic regex for experience
        # e.g. "3+ years of experience", "Minimum 5 years", "2-4 years"
        self.exp_pattern = re.compile(r'(?:minimum|at least)?\s*(\d+)(?:\s*[-+to]+\s*\d+)?\s*(?:\+)?\s*years?', re.IGNORECASE)
        
        # Heuristic regex for degree
        self.degree_patterns = {
            "PhD": re.compile(r'\b(phd|doctorate)\b', re.IGNORECASE),
            "Master's": re.compile(r'\b(master\'?s|msc|ms|mba)\b', re.IGNORECASE),
            "Bachelor's": re.compile(r'\b(bachelor\'?s|bsc|bs|ba)\b', re.IGNORECASE)
        }

    def parse(self, text: str) -> JobDescriptionSchema:
        """Parses a raw Job Description string into a structured schema."""
        if not text:
            return JobDescriptionSchema()
            
        skills = self.skill_matcher.extract_skills(text)
        
        # Extract years of experience
        min_years = 0
        exp_matches = self.exp_pattern.findall(text)
        if exp_matches:
            # If multiple mentions, take the maximum as the requirement 
            # (or we could take the first. taking max is safer for "minimum 3 years... 5 years preferred")
            try:
                min_years = max(int(m) for m in exp_matches)
            except ValueError:
                min_years = 0
                
        # Extract degree
        required_degree = None
        for degree_tier, pattern in self.degree_patterns.items():
            if pattern.search(text):
                required_degree = degree_tier
                break # We take the highest tier mentioned (since dictionary order PhD > MS > BS)
                
        return JobDescriptionSchema(
            raw_text=text,
            skills=skills,
            min_years_experience=min_years,
            required_degree=required_degree
        )
