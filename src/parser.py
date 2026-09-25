import logging
from typing import Optional

from .schema import ParsedResumeOutput, ResumeSchema, ContactInfo, Experience, Education
from .ingestion import ingest_document, IngestionError, RequiresOCRError
from .segmentation import Segmenter, Section
from .extractors.regex_extractor import RegexExtractor
from .extractors.spacy_extractor import SpacyExtractor
from .extractors.llm_extractor import GeminiExtractor
from .extractors.skill_matcher import SkillMatcher
from .extractors.orchestrator import ExtractorOrchestrator

logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self, llm_extractor_override=None):
        """
        llm_extractor_override allows tests to inject a mock LLM.
        """
        self.regex = RegexExtractor()
        self.spacy = SpacyExtractor()
        
        # Dependency injection for LLM
        self.llm = llm_extractor_override if llm_extractor_override is not None else GeminiExtractor()
        
        self.skill_matcher = SkillMatcher()
        self.orchestrator = ExtractorOrchestrator(self.regex, self.spacy, self.llm, self.skill_matcher)
        
        # Segmenter uses the LLM as a fallback classifier
        # We wrap it in a lambda that returns a Section enum
        def llm_fallback(text: str) -> Section:
            from pydantic import BaseModel
            class SectionClassification(BaseModel):
                section: str
            if self.llm:
                res = self.llm.extract_structured(
                    f"Classify this header into one of: Contact, Summary, Experience, Education, Skills, Projects, Certifications. Header: {text}",
                    SectionClassification
                )
                try:
                    return Section(res.section.title())
                except ValueError:
                    return Section.UNKNOWN
            return Section.UNKNOWN
            
        self.segmenter = Segmenter(fallback_classifier=llm_fallback)

    def parse(self, file_path: str) -> ParsedResumeOutput:
        try:
            # 1. Ingestion
            raw_text = ingest_document(file_path)
            
            # 1.5 Blind Hiring / PII Redaction
            if hasattr(self.llm, "redact_pii"):
                raw_text = self.llm.redact_pii(raw_text)
            
            # 2. Segmentation
            segments = self.segmenter.segment(raw_text)
            
            # 3. Extraction via Orchestrator
            contact_data = self.orchestrator.process_contact_section(
                whole_text=raw_text, 
                contact_text=segments.get(Section.CONTACT, "")
            )
            
            experience_data = self.orchestrator.process_experience(segments.get(Section.EXPERIENCE, ""))
            education_data = self.orchestrator.process_education(segments.get(Section.EDUCATION, ""))
            
            # Skills extraction (run on the whole text to catch all variants, not just the Skills section)
            skills = self.skill_matcher.extract_skills(raw_text)
            
            resume_data = ResumeSchema(
                contact=ContactInfo(**contact_data) if contact_data else ContactInfo(),
                summary=segments.get(Section.SUMMARY),
                experience=experience_data,
                education=education_data,
                skills=skills,
                projects=[],
                certifications=[]
            )
            
            return ParsedResumeOutput(
                status="success",
                message="Successfully parsed",
                data=resume_data
            )
            
        except RequiresOCRError as e:
            return ParsedResumeOutput(status="requires_ocr", message=str(e), data=None)
        except IngestionError as e:
            return ParsedResumeOutput(status="error", message=str(e), data=None)
        except Exception as e:
            logger.error(f"Unexpected error during parsing: {e}")
            return ParsedResumeOutput(status="error", message=str(e), data=None)
