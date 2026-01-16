"""Configuration management for resume agent."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for resume agent."""
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    OPENAI_MAX_RETRIES: int = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
    OPENAI_TIMEOUT: int = int(os.getenv("OPENAI_TIMEOUT", "60"))
    
    # File paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "src" / "data"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    RESUME_INDEX_PATH: Path = DATA_DIR / "resumes" / "resume_index.json"
    
    # Google Docs settings
    GOOGLE_TEMPLATE_DOC_ID: str = os.getenv("GOOGLE_TEMPLATE_DOC_ID", "1eIP5OWCnFlK-BGu9lq6-5MGiUvrLelc7pFSxSoq0Xio")
    GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    GOOGLE_TOKEN_PATH: str = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
    
    # Web scraping settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    USER_AGENT: str = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Create output directory if it doesn't exist
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create data directory if it doesn't exist
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
