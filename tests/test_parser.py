import os
import json
import pytest
from pydantic import BaseModel
from src.parser import ResumeParser
from src.extractors.llm_extractor import LLMExtractor

RESUME_DIR = "tests/test_data/resumes"
TRUTH_DIR = "tests/test_data/ground_truth"

class MockLLMExtractor(LLMExtractor):
    """Mocks the LLM calls so tests run fully offline."""
    def extract_structured(self, text: str, schema: type[BaseModel]) -> BaseModel:
        # For tests, we just return empty models to simulate a fallback that doesn't 
        # add new info, ensuring we mostly test the heuristics/regex/spacy.
        # Alternatively, we could parse the JSON ground truth and mock it exactly.
        return schema()

@pytest.fixture
def parser():
    return ResumeParser(llm_extractor_override=MockLLMExtractor())

def test_standard_pdf(parser):
    result = parser.parse(os.path.join(RESUME_DIR, "standard_resume.pdf"))
    assert result.status == "success"
    assert result.data is not None
    
    with open(os.path.join(TRUTH_DIR, "standard_resume.json")) as f:
        truth = json.load(f)
        
    assert result.data.contact.email == truth["contact"]["email"]
    assert result.data.contact.phone == truth["contact"]["phone"]
    # Check that skill matching found Python and AWS (case-insensitive checks usually in skill extractor)
    assert "Python" in result.data.skills
    assert "AWS" in result.data.skills

def test_scanned_image_pdf(parser):
    result = parser.parse(os.path.join(RESUME_DIR, "scanned_image.pdf"))
    assert result.status == "requires_ocr"
    
def test_skills_only_docx(parser):
    result = parser.parse(os.path.join(RESUME_DIR, "skills_only.docx"))
    assert result.status == "success"
    assert result.data.contact.email == "jane.smith@email.com"
    assert "React" in result.data.skills

def test_dense_no_headers_pdf(parser):
    result = parser.parse(os.path.join(RESUME_DIR, "dense_no_headers.pdf"))
    assert result.status == "success"
    assert result.data.contact.email == "alice@walker.net"
    # Spacy should ideally catch Alice Walker as the name
    # We might not get full extraction without LLM on dense blocks, but contact should work due to whole-doc pass
    assert "Python" in result.data.skills

# Test runner hook
if __name__ == "__main__":
    pytest.main(["-v", __file__])
