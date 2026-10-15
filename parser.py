"""
Standalone Parser Engine
Deliverable 1: ResumeParser class with parse_file(file_path) -> dict/JSON
"""
import sys
import os
import json
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.parser import ResumeParser
from src.schema import ResumeSchema, ParsedResumeOutput

__all__ = ["ResumeParser"]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python parser.py <path_to_resume_file> [--json]")
        print("Example: python parser.py tests/test_data/resumes/standard_resume.pdf")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)

    print(f"Parsing resume: {file_path} ...")
    parser = ResumeParser()
    result = parser.parse_file(file_path)
    print("\n--- Parsed JSON Result ---")
    print(json.dumps(result, indent=2, default=str))
