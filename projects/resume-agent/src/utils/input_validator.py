"""Input validation utilities."""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def validate_job_description(text: str, min_length: int = 100) -> None:
    """
    Validate job description text.
    
    Args:
        text: Job description text to validate
        min_length: Minimum required length
        
    Raises:
        ValueError: If validation fails
    """
    if not text:
        raise ValueError("Job description cannot be empty")
    
    if not isinstance(text, str):
        raise ValueError(f"Job description must be a string, got {type(text)}")
    
    text = text.strip()
    
    if len(text) < min_length:
        raise ValueError(
            f"Job description too short ({len(text)} chars). "
            f"Minimum {min_length} characters required."
        )
    
    # Check for suspiciously repetitive content (might indicate scraping failure)
    words = text.split()
    if len(words) > 0:
        unique_words = len(set(words))
        repetition_ratio = unique_words / len(words)
        if repetition_ratio < 0.1:  # Less than 10% unique words
            logger.warning(
                f"Job description has low word diversity ({repetition_ratio:.2%}). "
                "This might indicate a scraping issue."
            )


def validate_file_path(path: str, must_exist: bool = True, extensions: Optional[list] = None) -> Path:
    """
    Validate and normalize file path.
    
    Args:
        path: File path to validate
        must_exist: Whether file must exist
        extensions: Allowed file extensions (e.g., ['.txt', '.pdf'])
        
    Returns:
        Normalized Path object
        
    Raises:
        ValueError: If validation fails
        FileNotFoundError: If file doesn't exist and must_exist=True
    """
    file_path = Path(path)
    
    if must_exist and not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if extensions:
        if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
            raise ValueError(
                f"File must have one of these extensions: {', '.join(extensions)}, "
                f"got: {file_path.suffix}"
            )
    
    return file_path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be filesystem-safe.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized
