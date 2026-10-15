import logging
from io import BytesIO
from pdfminer.high_level import extract_text
import docx

import re
import unicodedata

logger = logging.getLogger(__name__)

class IngestionError(Exception):
    pass

class RequiresOCRError(Exception):
    pass

def clean_text(text: str) -> str:
    """Robust text cleaning pipeline:
    - Normalizes unicode characters and removes non-printable noise
    - Standardizes bullet points to clean format
    - Normalizes smart quotes, hyphens, and whitespace
    """
    if not text:
        return ""
    
    # Standardize unicode characters (NFKD)
    normalized = unicodedata.normalize("NFKD", text)
    
    # Replace common smart quotes, dashes, and unicode symbols with standard ASCII equivalents
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": "...",
        "\u00a0": " ",  # non-breaking space
    }
    for orig, repl in replacements.items():
        normalized = normalized.replace(orig, repl)
        
    # Standardize bullet characters to clean bullet markers
    bullet_pattern = re.compile(r"[\u2022\u2023\u25e6\u2043\u2219\u25aa\u25cf\u25cb•●▪◆◦]")
    normalized = bullet_pattern.sub("- ", normalized)
    
    # Filter out non-printable control characters except standard whitespace
    cleaned_chars = [
        c for c in normalized 
        if c in ("\n", "\r", "\t") or (32 <= ord(c) <= 126) or ord(c) > 127
    ]
    cleaned = "".join(cleaned_chars)
    
    # Normalize excessive horizontal whitespace per line
    lines = []
    for line in cleaned.splitlines():
        line_clean = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(line_clean)
        
    # Remove excessive blank lines (more than 2 consecutive newlines)
    compacted = "\n".join(lines)
    compacted = re.sub(r"\n{3,}", "\n\n", compacted)
    
    return compacted.strip()

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file using pdfminer.six.
    Detects if the PDF is likely image-only/scanned.
    """
    try:
        text = extract_text(file_path)
    except Exception as e:
        logger.error(f"Failed to read PDF {file_path}: {e}")
        raise IngestionError(f"PDF extraction failed: {e}")
    
    # Check if the extracted text is too short or just whitespace/noise
    raw_cleaned = text.strip()
    if len(raw_cleaned) < 50:
        logger.warning(f"File {file_path} yielded very little text. Likely a scanned/image-only PDF.")
        raise RequiresOCRError("PDF appears to be image-only and requires OCR.")
        
    return clean_text(raw_cleaned)

def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from a DOCX file using python-docx."""
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        return clean_text("\n".join(full_text))
    except Exception as e:
        logger.error(f"Failed to read DOCX {file_path}: {e}")
        raise IngestionError(f"DOCX extraction failed: {e}")

def extract_text_from_txt(file_path: str) -> str:
    """Extracts and cleans text from a plain TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return clean_text(content)
    except Exception as e:
        logger.error(f"Failed to read TXT {file_path}: {e}")
        raise IngestionError(f"TXT extraction failed: {e}")

def ingest_document(file_path: str) -> str:
    """Routes to the correct extraction method based on file extension."""
    ext = file_path.lower().split('.')[-1]
    if ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['doc', 'docx']:
        return extract_text_from_docx(file_path)
    elif ext in ['txt']:
        return extract_text_from_txt(file_path)
    else:
        raise IngestionError(f"Unsupported file extension: {ext}")
