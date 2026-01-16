"""PDF input/output utilities."""
import logging
from pathlib import Path
from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)


def pdf_to_text(path: str) -> str:
    """
    Extract text from PDF file.
    
    Args:
        path: Path to PDF file
        
    Returns:
        Extracted text from all pages
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF is invalid or empty
    """
    pdf_path = Path(path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    
    if not pdf_path.suffix.lower() == '.pdf':
        raise ValueError(f"File is not a PDF: {path}")
    
    logger.debug(f"Extracting text from PDF: {path}")
    
    try:
        reader = PdfReader(path)
        
        if len(reader.pages) == 0:
            raise ValueError(f"PDF has no pages: {path}")
        
        pages = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                pages.append(text)
                logger.debug(f"Extracted {len(text)} characters from page {i + 1}")
            except Exception as e:
                logger.warning(f"Failed to extract text from page {i + 1}: {e}")
                pages.append("")
        
        full_text = "\n".join(pages)
        
        if not full_text.strip():
            raise ValueError(f"PDF appears to be empty or contains no extractable text: {path}")
        
        logger.info(f"Successfully extracted {len(full_text)} characters from {len(reader.pages)} pages")
        return full_text
        
    except PdfReadError as e:
        logger.error(f"Failed to read PDF: {e}")
        raise ValueError(f"Invalid or corrupted PDF file: {path}") from e
    except Exception as e:
        logger.error(f"Unexpected error reading PDF: {e}")
        raise ValueError(f"Failed to extract text from PDF: {path}") from e
