import re
from typing import Dict, Any
from .base import BaseExtractor

class RegexExtractor(BaseExtractor):
    def __init__(self):
        # Basic patterns
        self.email_pattern = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
        self.phone_pattern = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
        self.url_pattern = re.compile(r"(https?://[^\s]+|www\.[^\s]+|linkedin\.com/in/[^\s]+|github\.com/[^\s]+)")

    def extract(self, text: str) -> Dict[str, Any]:
        """Extracts email, phone, and links from the provided text.
        This will be run on BOTH the whole document and the Contact segment.
        """
        result = {
            "email": None,
            "phone": None,
            "links": []
        }
        
        email_match = self.email_pattern.search(text)
        if email_match:
            result["email"] = email_match.group(0)
            
        phone_match = self.phone_pattern.search(text)
        if phone_match:
            result["phone"] = phone_match.group(0)
            
        urls = self.url_pattern.findall(text)
        if urls:
            result["links"] = list(set(urls)) # unique links
            
        return result
