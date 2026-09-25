import yaml
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
from dateutil import parser as date_parser
import numpy as np

from ..schema import ResumeSchema, JobDescriptionSchema
from ..vector_store.faiss_adapter import FaissAdapter
from ..extractors.skill_matcher import SkillMatcher

logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self, weights_path: str = None, vector_store=None, skill_matcher=None):
        if not weights_path:
            weights_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'matching_weights.yaml')
            
        with open(weights_path, 'r') as f:
            self.weights = yaml.safe_load(f)
            
        self.vector_store = vector_store or FaissAdapter(dimension=384)
        self.skill_matcher = skill_matcher or SkillMatcher()
        
        # We assume the SentenceTransformer model is available via the skill matcher to encode text
        self.embedding_model = self.skill_matcher.model

    def parse_date(self, date_str: str) -> datetime:
        """Parses a date string into a datetime object. Handles 'Present'."""
        if not date_str:
            return datetime.now()
            
        if date_str.lower() in ["present", "current", "now", "ongoing"]:
            return datetime.now()
            
        try:
            # We use a simple parser or python-dateutil if available (we can assume dateutil since it's a common dependency, or write simple fallback)
            # Actually, let's just use a simple heuristic to avoid adding new deps if possible, but python-dateutil is standard
            # We will use a safe try-except
            from dateutil.parser import parse
            # default to first of the month if day is missing
            return parse(date_str, default=datetime(datetime.now().year, 1, 1))
        except Exception:
            logger.warning(f"Failed to parse date: {date_str}. Defaulting to today.")
            return datetime.now()

    def calculate_total_experience_years(self, experiences: List[Any]) -> float:
        """Uses interval union math to prevent double counting overlapping roles."""
        intervals = []
        for exp in experiences:
            if not exp.start_date:
                continue
            start = self.parse_date(exp.start_date)
            end = self.parse_date(exp.end_date) if exp.end_date else datetime.now()
            if start > end:
                start, end = end, start # Swap if somehow inverted
            intervals.append([start, end])
            
        if not intervals:
            return 0.0
            
        # Sort by start date
        intervals.sort(key=lambda x: x[0])
        
        # Merge overlapping intervals
        merged = [intervals[0]]
        for current in intervals[1:]:
            last = merged[-1]
            if current[0] <= last[1]:
                # Overlap, merge them
                last[1] = max(last[1], current[1])
            else:
                merged.append(current)
                
        # Sum durations
        total_days = sum((interval[1] - interval[0]).days for interval in merged)
        return total_days / 365.25

    def _get_experience(self, resume: Any) -> list:
        if isinstance(resume, dict):
            return resume.get("experience") or resume.get("work_experience") or []
        return getattr(resume, "experience", None) or getattr(resume, "work_experience", []) or []

    def score_experience(self, jd: JobDescriptionSchema, resume: ResumeSchema) -> float:
        required = jd.min_years_experience
        if required == 0:
            return 1.0 # No requirement means perfect fit
            
        actual_years = self.calculate_total_experience_years(self._get_experience(resume))
        if actual_years >= required:
            return 1.0
        return max(0.0, actual_years / required)

    def score_education(self, jd: JobDescriptionSchema, resume: ResumeSchema) -> float:
        required_degree = jd.required_degree
        if not required_degree:
            return 1.0
            
        # Hierarchy: PhD > Master's > Bachelor's
        hierarchy = {"Bachelor's": 1, "Master's": 2, "PhD": 3}
        req_level = hierarchy.get(required_degree, 0)
        
        actual_level = 0
        education_list = getattr(resume, 'education', []) or (resume.get('education', []) if isinstance(resume, dict) else [])
        for edu in education_list:
            degree_str = (getattr(edu, 'degree', None) or (edu.get('degree') if isinstance(edu, dict) else "") or "").lower()
            if "phd" in degree_str or "doctorate" in degree_str:
                level = 3
            elif "master" in degree_str or "msc" in degree_str or "ms" in degree_str or "mba" in degree_str:
                level = 2
            elif "bachelor" in degree_str or "bsc" in degree_str or "bs" in degree_str or "ba" in degree_str:
                level = 1
            else:
                level = 0
            actual_level = max(actual_level, level)
            
        if actual_level >= req_level:
            return 1.0
            
        # Partial credit for being 1 tier below? Let's say 0.5
        if req_level - actual_level == 1:
            return 0.5
            
        return 0.0

    def score_skills(self, jd: JobDescriptionSchema, resume: ResumeSchema) -> float:
        if not jd.skills:
            return 1.0  # No skills required

        def normalize_to_canonical(skills_list: list) -> set:
            """Normalize a list of skill strings to their canonical names using the ontology."""
            canonical = set()
            for skill in skills_list:
                s_lower = skill.lower().strip()
                # Direct ontology variant lookup
                if s_lower in self.skill_matcher.variant_to_canonical:
                    canonical.add(self.skill_matcher.variant_to_canonical[s_lower])
                else:
                    # Fallback: check if any variant is a substring of the skill (handles 'React Native' → 'React')
                    matched = False
                    for variant, canon in self.skill_matcher.variant_to_canonical.items():
                        if variant in s_lower or s_lower in variant:
                            canonical.add(canon)
                            matched = True
                            break
                    if not matched:
                        # Use the skill as-is (normalized to title case)
                        canonical.add(skill.strip().title())
            return canonical

        jd_canonical = normalize_to_canonical(jd.skills)
        res_skills_raw = getattr(resume, 'skills', []) or (resume.get('skills', []) if isinstance(resume, dict) else [])
        res_canonical = normalize_to_canonical(res_skills_raw)

        if not jd_canonical:
            return 1.0

        overlap = jd_canonical.intersection(res_canonical)

        # Recall-based: what % of JD required skills does the candidate possess
        return len(overlap) / len(jd_canonical)

    def generate_resume_embedding(self, resume: Any) -> np.ndarray:
        # Build a text representation of the resume's core substance
        text_parts = []
        summary = getattr(resume, 'summary', None) or (resume.get('summary') if isinstance(resume, dict) else None)
        if summary:
            text_parts.append(summary)
            
        experiences = self._get_experience(resume)
        for exp in experiences:
            role = getattr(exp, 'role', None) or (exp.get('role') if isinstance(exp, dict) else None) or getattr(exp, 'job_title', None)
            company = getattr(exp, 'company', None) or (exp.get('company') if isinstance(exp, dict) else None) or getattr(exp, 'organization', None)
            desc = getattr(exp, 'description', None) or (exp.get('description') if isinstance(exp, dict) else None)
            if role and company:
                text_parts.append(f"{role} at {company}")
            if desc:
                text_parts.append(desc)
        
        full_text = " ".join(text_parts)
        if not full_text.strip():
            skills = getattr(resume, 'skills', []) or (resume.get('skills', []) if isinstance(resume, dict) else [])
            full_text = " ".join(skills)
            
        if not full_text.strip():
            raw_text = getattr(resume, 'raw_text', '') or (resume.get('raw_text', '') if isinstance(resume, dict) else '')
            full_text = raw_text[:500]
            
        if not full_text.strip():
            return np.zeros(384)
            
        return self.embedding_model.encode([full_text])[0]

    def score_semantic_similarity(self, jd: JobDescriptionSchema, resume: ResumeSchema) -> float:
        if not self.embedding_model:
            return 0.0
            
        # We index the resume and search with the JD.
        # But we only need a 1-to-1 comparison here.
        resume_emb = self.generate_resume_embedding(resume)
        jd_emb = self.embedding_model.encode([jd.raw_text])[0]
        
        # Calculate cosine similarity directly for 1-to-1
        norm_r = np.linalg.norm(resume_emb)
        norm_j = np.linalg.norm(jd_emb)
        
        if norm_r == 0 or norm_j == 0:
            return 0.0
            
        similarity = np.dot(resume_emb, jd_emb) / (norm_r * norm_j)
        # Clip to [0, 1] (negative similarity means totally orthogonal/opposite, we floor to 0)
        return float(max(0.0, min(1.0, similarity)))

    def calculate_match(self, jd: JobDescriptionSchema, resume: ResumeSchema) -> Dict[str, Any]:
        """Calculates the composite match score and returns a breakdown."""
        semantic = self.score_semantic_similarity(jd, resume)
        skills = self.score_skills(jd, resume)
        experience = self.score_experience(jd, resume)
        education = self.score_education(jd, resume)
        
        w = self.weights
        composite = (
            semantic * w.get("semantic_similarity", 0.4) +
            skills * w.get("skill_overlap", 0.3) +
            experience * w.get("experience_fit", 0.2) +
            education * w.get("education_fit", 0.1)
        )
        
        return {
            "overall_score": composite,
            "breakdown": {
                "semantic_similarity": semantic,
                "skill_overlap": skills,
                "experience_fit": experience,
                "education_fit": education
            },
            "years_of_experience": self.calculate_total_experience_years(self._get_experience(resume))
        }
