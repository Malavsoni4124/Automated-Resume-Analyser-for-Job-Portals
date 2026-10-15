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

    def _heuristic_experience_fallback(self, exp_text: str) -> list:
        """Heuristic fallback to extract experiences using regex and spaCy when LLM is unavailable."""
        import re
        from ..schema import Experience

        experiences = []
        date_pattern = re.compile(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})\s*(?:-|–|to)\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|Present|Current)",
            re.IGNORECASE
        )
        single_year_pattern = re.compile(r"\b(19\d\d|20\d\d)\b")

        blocks = [b.strip() for b in re.split(r"\n\s*\n", exp_text) if b.strip()]
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            company = None
            role = None
            start_date = None
            end_date = None
            bullet_points = []
            desc_lines = []

            # Check for dates in lines
            for line in lines:
                date_match = date_pattern.search(line)
                if date_match and not start_date:
                    start_date = date_match.group(1)
                    end_date = date_match.group(2)
                elif line.startswith(("-", "*", "•")):
                    bullet_points.append(line.lstrip("-*• ").strip())
                else:
                    desc_lines.append(line)

            # Heuristic for role and company from header lines
            header_lines = desc_lines[:2] if len(desc_lines) >= 2 else desc_lines
            for hline in header_lines:
                if any(sep in hline for sep in ["|", " - ", " at ", "@", ","]):
                    parts = re.split(r"\s*(?:\|| - | at |@|,)\s*", hline)
                    if len(parts) >= 2:
                        role = parts[0].strip()
                        company = parts[1].strip()
                        break
                elif any(kw in hline.lower() for kw in ["engineer", "developer", "manager", "lead", "analyst", "intern", "consultant", "architect"]):
                    role = hline.strip()
                elif self.spacy:
                    doc = self.spacy.nlp(hline)
                    for ent in doc.ents:
                        if ent.label_ == "ORG" and not company:
                            company = ent.text

            if not role and header_lines:
                role = header_lines[0]
            if not company and len(header_lines) > 1:
                company = header_lines[1]

            if role or company or bullet_points:
                experiences.append(Experience(
                    company=company,
                    role=role,
                    start_date=start_date,
                    end_date=end_date,
                    description="\n".join(bullet_points) if bullet_points else ("\n".join(desc_lines) if desc_lines else None),
                    bullet_points=bullet_points
                ))

        return experiences

    def _heuristic_education_fallback(self, edu_text: str) -> list:
        """Heuristic fallback to extract education using regex and spaCy when LLM is unavailable."""
        import re
        from ..schema import Education

        educations = []
        degree_pattern = re.compile(
            r"\b(B\.?S\.?|B\.?Tech|B\.?E\.?|M\.?S\.?|M\.?Tech|Master|Bachelor|Ph\.?D\.?|Associate|Diploma|High School|B\.?Sc|BCA|MCA)\b",
            re.IGNORECASE
        )
        institution_pattern = re.compile(
            r"\b([A-Z][a-zA-Z\s&]+(?:University|College|Institute|School|Academy))\b",
            re.IGNORECASE
        )
        gpa_pattern = re.compile(r"(?:GPA|CGPA|Grade)[\s:]*([0-9]+(?:\.[0-9]+)?(?:\s*/\s*[0-9]+(?:\.[0-9]+)?)?)", re.IGNORECASE)
        date_pattern = re.compile(r"\b(19\d\d|20\d\d)\s*(?:-|–|to)?\s*(19\d\d|20\d\d|Present)?\b", re.IGNORECASE)

        blocks = [b.strip() for b in re.split(r"\n\s*\n", edu_text) if b.strip()]
        for block in blocks:
            degree = None
            institution = None
            start_date = None
            end_date = None
            gpa = None
            major = None

            d_match = degree_pattern.search(block)
            if d_match:
                degree = d_match.group(0)

            inst_match = institution_pattern.search(block)
            if inst_match:
                institution = inst_match.group(0).strip()
            elif self.spacy:
                doc = self.spacy.nlp(block)
                for ent in doc.ents:
                    if ent.label_ == "ORG":
                        institution = ent.text
                        break

            gpa_match = gpa_pattern.search(block)
            if gpa_match:
                gpa = gpa_match.group(1)

            date_match = date_pattern.search(block)
            if date_match:
                start_date = date_match.group(1)
                end_date = date_match.group(2)

            for line in block.split("\n"):
                if "in " in line.lower() and degree:
                    parts = line.lower().split("in ", 1)
                    if len(parts) > 1:
                        major = parts[1].split(",")[0].split("-")[0].strip().title()

            if institution or degree:
                educations.append(Education(
                    institution=institution,
                    degree=degree,
                    major=major,
                    start_date=start_date,
                    end_date=end_date,
                    gpa=gpa
                ))

        return educations

    def process_experience(self, exp_text: str) -> list:
        # LLM is preferred for nested structured data like Experience
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
                if result and result.experiences:
                    return result.experiences
        except Exception as e:
            logger.info(f"LLM extraction for Experience failed or unavailable ({e}). Using heuristic extractor.")

        return self._heuristic_experience_fallback(exp_text)

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
                if result and result.educations:
                    return result.educations
        except Exception as e:
            logger.info(f"LLM extraction for Education failed or unavailable ({e}). Using heuristic extractor.")

        return self._heuristic_education_fallback(edu_text)

