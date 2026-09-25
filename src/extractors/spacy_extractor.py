import spacy
from typing import Dict, Any, List
import logging
from .base import BaseExtractor

logger = logging.getLogger(__name__)

class SpacyExtractor(BaseExtractor):
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_md")
        except OSError:
            logger.error("Failed to load spaCy model. Ensure it was downloaded.")
            raise

    def extract(self, text: str) -> Dict[str, Any]:
        """Extracts names, organizations, and potential degrees (based on patterns)
        Returns a dictionary and the confidence/counts so orchestrator can decide on LLM fallback.
        """
        doc = self.nlp(text)
        
        persons = []
        orgs = []
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                persons.append(ent.text)
            elif ent.label_ == "ORG":
                orgs.append(ent.text)
                
        # Simple heuristic: most common PERSON is likely the candidate name (especially if early in text)
        # We can just return the first one found for now.
        name = persons[0] if persons else None
        
        return {
            "name": name,
            "organizations": list(set(orgs)),
            "raw_persons": persons,
            "raw_orgs": orgs
        }

    def evaluate_confidence(self, extracted: Dict[str, Any]) -> float:
        """
        Mock confidence metric. 
        If it found a name and some orgs, confidence is high (1.0).
        If missing name, confidence is low (0.0).
        """
        if extracted.get("name"):
            return 1.0
        return 0.0
