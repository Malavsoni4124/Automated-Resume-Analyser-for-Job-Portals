import re
import logging
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class Section(str, Enum):
    CONTACT = "Contact"
    SUMMARY = "Summary"
    EXPERIENCE = "Experience"
    EDUCATION = "Education"
    SKILLS = "Skills"
    PROJECTS = "Projects"
    CERTIFICATIONS = "Certifications"
    UNKNOWN = "Unknown"

# Standard heuristic patterns
SECTION_PATTERNS = {
    Section.CONTACT: re.compile(r"^(contact|personal info|about me)\b", re.IGNORECASE),
    Section.SUMMARY: re.compile(r"^(summary|profile|objective|professional summary)\b", re.IGNORECASE),
    Section.EXPERIENCE: re.compile(r"^(experience|employment|work history|professional experience)\b", re.IGNORECASE),
    Section.EDUCATION: re.compile(r"^(education|academic background|qualifications)\b", re.IGNORECASE),
    Section.SKILLS: re.compile(r"^(skills|technical skills|technologies|core competencies)\b", re.IGNORECASE),
    Section.PROJECTS: re.compile(r"^(projects|personal projects|academic projects)\b", re.IGNORECASE),
    Section.CERTIFICATIONS: re.compile(r"^(certifications|licenses|courses)\b", re.IGNORECASE),
}

class Segmenter:
    def __init__(self, fallback_classifier=None):
        """
        fallback_classifier: A callable or object with a `classify(text)` method. 
        Will be invoked for blocks that don't match known patterns.
        """
        self.fallback_classifier = fallback_classifier

    def segment(self, text: str) -> Dict[Section, str]:
        """
        Segments the full resume text into predefined sections.
        """
        lines = text.split('\n')
        sections_content = {sec: [] for sec in Section}
        
        current_section = Section.CONTACT # Default first section
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Check if this line is a header
            matched_section = None
            if len(line_clean) < 60: # Heuristic: headers are usually short
                for sec, pattern in SECTION_PATTERNS.items():
                    if pattern.search(line_clean):
                        matched_section = sec
                        break
                
            if matched_section:
                current_section = matched_section
            else:
                # If we encounter an unknown header-like line (uppercase, short, not matching),
                # we could trigger the fallback here.
                # For simplicity, we just append to the current section.
                # A more advanced heuristic might look for ANY short uppercase line as a new boundary.
                if len(line_clean) < 40 and line_clean.isupper() and len(line_clean.split()) < 5:
                    logger.warning(f"Found unknown header-like block: '{line_clean}'. Using fallback classifier.")
                    if self.fallback_classifier:
                        try:
                            inferred_section = self.fallback_classifier(line_clean)
                            if inferred_section in sections_content:
                                current_section = inferred_section
                        except Exception as e:
                            logger.error(f"Fallback classifier failed: {e}")
                    else:
                        logger.info("No fallback classifier provided, assigning to Unknown.")
                        current_section = Section.UNKNOWN
                
            sections_content[current_section].append(line_clean)
            
        return {sec: "\n".join(lines) for sec, lines in sections_content.items() if lines}
