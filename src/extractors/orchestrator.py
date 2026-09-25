import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ExtractorOrchestrator:
    def __init__(self, regex_extractor, spacy_extractor, llm_extractor, skill_matcher):
        self.regex = regex_extractor
        self.spacy = spacy_extractor
        self.llm = llm_extractor
        self.skill_matcher = skill_matcher

    def log_disagreement(self, field_name: str, spacy_val: Any, llm_val: Any):
        """Logs a disagreement between spaCy and LLM extraction."""
        if spacy_val != llm_val and spacy_val and llm_val:
            logger.warning(
                f"Extraction disagreement for '{field_name}'. "
                f"spaCy: '{spacy_val}' | LLM: '{llm_val}'"
            )

    def process_contact_section(self, whole_text: str, contact_text: str) -> Dict[str, Any]:
        """
        Regex runs on whole text first (as requested).
        Then spaCy runs on contact text.
        LLM runs only if confidence is low.
        """
        # 1. Regex (Whole document pass + contact text pass, regex extractor handles it internally if we pass whole text)
        regex_results = self.regex.extract(whole_text)
        
        # 2. SpaCy (on contact text, mainly for Names)
        spacy_results = self.spacy.extract(contact_text)
        confidence = self.spacy.evaluate_confidence(spacy_results)
        
        # 3. LLM Fallback for low confidence
        llm_results = {}
        if confidence < 0.5:
            logger.info("Low confidence in spaCy extraction for Contact. Invoking LLM fallback.")
            from ..schema import ContactInfo # inline import to avoid circular dependency if any
            try:
                if self.llm:
                    llm_schema = self.llm.extract_structured(contact_text, ContactInfo)
                    llm_results = llm_schema.model_dump()
            except Exception as e:
                logger.error(f"LLM fallback failed for contact: {e}")
                
        # 4. Disagreement logging & merging
        # Prefer regex for deterministic fields, then spacy for names, fallback to LLM
        name = spacy_results.get("name")
        if llm_results.get("name"):
            self.log_disagreement("name", name, llm_results.get("name"))
            if not name:
                name = llm_results.get("name")
                
        return {
            "name": name,
            "email": regex_results.get("email") or llm_results.get("email"),
            "phone": regex_results.get("phone") or llm_results.get("phone"),
            "links": regex_results.get("links") or llm_results.get("links", []),
            "location": llm_results.get("location") # Spacy didn't extract location in our simple heuristic
        }

    def process_experience(self, exp_text: str) -> list:
        # LLM is best for nested structured data like Experience
        from ..schema import Experience
        from pydantic import BaseModel, Field
        from typing import List
        
        class ExpList(BaseModel):
            experiences: List[Experience] = Field(default_factory=list)
            
        if not exp_text.strip():
            return []
            
        try:
            if self.llm:
                result = self.llm.extract_structured(exp_text, ExpList)
                return result.experiences
        except Exception as e:
            logger.error(f"LLM extraction failed for Experience: {e}")
        return []

    def process_education(self, edu_text: str) -> list:
        from ..schema import Education
        from pydantic import BaseModel, Field
        from typing import List
        
        class EduList(BaseModel):
            educations: List[Education] = Field(default_factory=list)
            
        if not edu_text.strip():
            return []
            
        try:
            if self.llm:
                result = self.llm.extract_structured(edu_text, EduList)
                return result.educations
        except Exception as e:
            logger.error(f"LLM extraction failed for Education: {e}")
        return []
