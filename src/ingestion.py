import logging
from io import BytesIO
from pdfminer.high_level import extract_text
import docx

logger = logging.getLogger(__name__)

class IngestionError(Exception):
    pass

class RequiresOCRError(Exception):
    pass

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
    cleaned_text = text.strip()
    if len(cleaned_text) < 50:
        logger.warning(f"File {file_path} yielded very little text. Likely a scanned/image-only PDF.")
        raise RequiresOCRError("PDF appears to be image-only and requires OCR.")
        
    return cleaned_text

def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        logger.error(f"Failed to read DOCX {file_path}: {e}")
        raise IngestionError(f"DOCX extraction failed: {e}")

def ingest_document(file_path: str) -> str:
    """Routes to the correct extraction method based on file extension."""
    ext = file_path.lower().split('.')[-1]
    if ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['doc', 'docx']:
        return extract_text_from_docx(file_path)
    else:
        raise IngestionError(f"Unsupported file extension: {ext}")
