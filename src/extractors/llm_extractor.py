from abc import ABC, abstractmethod
from typing import Dict, Any, Type
import logging
from pydantic import BaseModel
import google.generativeai as genai

from .base import BaseExtractor
from ..config import settings

logger = logging.getLogger(__name__)

class LLMExtractor(BaseExtractor, ABC):
    @abstractmethod
    def extract_structured(self, text: str, schema: Type[BaseModel]) -> BaseModel:
        """Extracts data adhering to a specific pydantic schema"""
        pass
        
    def extract(self, text: str) -> Dict[str, Any]:
        """BaseExtractor compatibility. Usually we call extract_structured directly."""
        pass

class GeminiExtractor(LLMExtractor):
    def __init__(self):
        self.api_key = settings.gemini_api_key
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. GeminiExtractor will fail if called.")
        else:
            genai.configure(api_key=self.api_key)
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception:
                self.model = genai.GenerativeModel('gemini-pro')
            
    def extract_structured(self, text: str, schema: Type[BaseModel]) -> BaseModel:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing. Cannot perform LLM extraction.")
            
        try:
            # 1. Try native structured output via response_schema
            response = self.model.generate_content(
                f"Extract the requested fields from the following resume text. Output purely as JSON matching the schema.\n\nText:\n{text}",
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1
                )
            )
            return schema.model_validate_json(response.text)
        except Exception as e:
            # 2. Resilient fallback for Pydantic v2 schemas or model schema errors
            logger.warning(f"Native response_schema failed ({e}). Retrying with prompt-based JSON specification.")
            import json
            import re
            schema_json = json.dumps(schema.model_json_schema())
            prompt = (
                f"Extract data from this text into valid JSON adhering strictly to this JSON Schema:\n"
                f"{schema_json}\n\n"
                f"Text:\n{text}\n\n"
                f"Return ONLY valid JSON with no markdown formatting."
            )
            try:
                response = self.model.generate_content(prompt)
                resp_text = response.text.strip()
                # Strip markdown code blocks if present
                if resp_text.startswith("```"):
                    resp_text = re.sub(r"^```[a-zA-Z]*\n", "", resp_text)
                    resp_text = re.sub(r"\n```$", "", resp_text).strip()
                return schema.model_validate_json(resp_text)
            except Exception as final_e:
                logger.error(f"Gemini LLM extraction failed: {final_e}")
                raise final_e

    def redact_pii(self, text: str) -> str:
        """Uses LLM to redact Personally Identifiable Information before parsing."""
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is missing. Skipping PII redaction.")
            return text
            
        prompt = (
            "You are a strict PII redaction bot for a blind-hiring ATS. "
            "Rewrite the following resume text exactly as provided, but replace all instances of "
            "the candidate's Name, Email, Phone Number, Physical Address, Links to Personal Sites/LinkedIn, "
            "University Names, Age, Date of Birth, Gender, and Nationality with the literal string '[REDACTED]'.\n\n"
            f"Text:\n{text}"
        )
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"PII Redaction failed: {e}")
            return text
