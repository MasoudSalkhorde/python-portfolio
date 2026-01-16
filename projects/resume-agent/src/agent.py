"""Main agent module for resume tailoring pipeline."""
import json
import time
from typing import Type, TypeVar, Optional
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from openai.types.chat import ChatCompletion

from src.utils.schemas import (
    JobDescriptionJSON, ResumeJSON, MatchJSON, TailoredResumeJSON
)
from src.utils.io_pdf import pdf_to_text
from src.utils.resume_selector import choose_resume_pdf
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.web_scraper import scrape_job_description, is_url

# Initialize logger
logger = setup_logger()

# Initialize OpenAI client
Config.validate()
client = OpenAI(
    api_key=Config.OPENAI_API_KEY,
    timeout=Config.OPENAI_TIMEOUT,
    max_retries=Config.OPENAI_MAX_RETRIES
)

T = TypeVar("T")


def call_llm(prompt: str, retry_count: int = 0) -> str:
    """
    Call OpenAI LLM with retry logic and error handling.
    
    Args:
        prompt: The prompt to send to the LLM
        retry_count: Current retry attempt (for recursive retries)
        
    Returns:
        Response text from the LLM
        
    Raises:
        APIError: If API call fails after all retries
        ValueError: If response is invalid
    """
    try:
        logger.debug(f"Calling LLM (attempt {retry_count + 1})")
        response: ChatCompletion = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise JSON-only generator."},
                {"role": "user", "content": prompt},
            ],
            temperature=Config.OPENAI_TEMPERATURE,
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        
        return content.strip()
        
    except RateLimitError as e:
        if retry_count < Config.OPENAI_MAX_RETRIES:
            wait_time = (2 ** retry_count) * 5  # Exponential backoff
            logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
            return call_llm(prompt, retry_count + 1)
        else:
            logger.error(f"Rate limit error after {Config.OPENAI_MAX_RETRIES} retries")
            raise APIError(f"Rate limit exceeded after {Config.OPENAI_MAX_RETRIES} retries") from e
            
    except APITimeoutError as e:
        if retry_count < Config.OPENAI_MAX_RETRIES:
            logger.warning(f"Timeout. Retrying (attempt {retry_count + 1})...")
            time.sleep(2)
            return call_llm(prompt, retry_count + 1)
        else:
            logger.error(f"Timeout after {Config.OPENAI_MAX_RETRIES} retries")
            raise APIError(f"Request timeout after {Config.OPENAI_MAX_RETRIES} retries") from e
            
    except APIError as e:
        if retry_count < Config.OPENAI_MAX_RETRIES and e.status_code and e.status_code >= 500:
            # Retry on server errors
            wait_time = (2 ** retry_count) * 2
            logger.warning(f"Server error {e.status_code}. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
            return call_llm(prompt, retry_count + 1)
        else:
            logger.error(f"API error: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Unexpected error in LLM call: {e}")
        raise


def llm_to_schema(prompt: str, schema: Type[T]) -> T:
    """
    Convert LLM response to Pydantic schema with error handling.
    
    Args:
        prompt: The prompt to send to the LLM
        schema: The Pydantic model class to validate against
        
    Returns:
        Validated instance of the schema
        
    Raises:
        ValueError: If JSON parsing or validation fails
    """
    try:
        raw = call_llm(prompt)
        
        # Try to extract JSON if wrapped in markdown code blocks
        if "```json" in raw:
            start = raw.find("```json") + 7
            end = raw.find("```", start)
            raw = raw[start:end].strip()
        elif "```" in raw:
            start = raw.find("```") + 3
            end = raw.find("```", start)
            raw = raw[start:end].strip()
        
        data = json.loads(raw)
        return schema.model_validate(data)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.debug(f"Raw response: {raw[:500]}...")
        raise ValueError(f"Invalid JSON response from LLM: {e}") from e
        
    except Exception as e:
        logger.error(f"Failed to validate schema: {e}")
        raise ValueError(f"Schema validation failed: {e}") from e


def get_job_description(input_source: str, use_selenium: bool = True) -> str:
    """
    Get job description from URL or file path.
    
    Args:
        input_source: URL or file path to job description
        use_selenium: Whether to use Selenium for JavaScript-rendered pages
        
    Returns:
        Job description text
        
    Raises:
        ValueError: If input is invalid or file doesn't exist
        FileNotFoundError: If file path doesn't exist
    """
    if is_url(input_source):
        logger.info("Detected URL input, scraping job description...")
        return scrape_job_description(input_source, use_selenium=use_selenium)
    else:
        # Assume it's a file path
        jd_path = Path(input_source)
        if not jd_path.exists():
            raise FileNotFoundError(f"Job description file not found: {jd_path}")
        
        logger.info(f"Reading job description from file: {jd_path}")
        try:
            with open(jd_path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                raise ValueError(f"Job description file is empty: {jd_path}")
            return content
        except Exception as e:
            logger.error(f"Failed to read job description file: {e}")
            raise


def run_pipeline(jd_text: str, resume_index_path: Optional[str] = None) -> TailoredResumeJSON:
    """
    Run the complete resume tailoring pipeline.
    
    Args:
        jd_text: Job description text
        resume_index_path: Optional path to resume index JSON file
        
    Returns:
        Tailored resume JSON
        
    Raises:
        ValueError: If pipeline step fails
        FileNotFoundError: If required files are missing
    """
    logger.info("Starting resume tailoring pipeline...")
    
    try:
        # Step 1: Select best resume
        logger.info("Step 1/5: Selecting best resume...")
        index_path = resume_index_path or str(Config.RESUME_INDEX_PATH)
        best_resume, scores = choose_resume_pdf(jd_text, index_path)
        
        logger.info(f"Selected base resume: {best_resume.label}")
        logger.debug(f"Resume scores: {scores}")
        logger.debug(f"Using PDF: {best_resume.path}")
        
        # Step 2: Extract resume text
        logger.info("Step 2/5: Extracting resume text from PDF...")
        resume_text = pdf_to_text(best_resume.path)
        if not resume_text or len(resume_text.strip()) < 50:
            raise ValueError(f"Resume PDF appears to be empty or invalid: {best_resume.path}")
        
        # Step 3: Extract structured data
        from src.utils.prompts import (
            prompt_extract_jd,
            prompt_extract_resume,
            prompt_match,
            prompt_tailor,
        )
        
        logger.info("Step 3/5: Extracting job description structure...")
        jd = llm_to_schema(prompt_extract_jd(jd_text), JobDescriptionJSON)
        logger.debug(f"Extracted JD: {jd.company} - {jd.role_title}")
        
        logger.info("Step 4/5: Extracting resume structure...")
        resume = llm_to_schema(prompt_extract_resume(resume_text), ResumeJSON)
        logger.debug(f"Extracted resume: {resume.name} with {len(resume.roles)} roles")
        
        logger.info("Step 5/5: Matching and tailoring resume...")
        match = llm_to_schema(prompt_match(jd, resume), MatchJSON)
        logger.debug(f"Match analysis: {len(match.match_map)} requirements matched")
        
        tailored = llm_to_schema(prompt_tailor(jd, resume, match), TailoredResumeJSON)
        
        # Count bullets needing revision
        revision_count = sum(
            1 for role in tailored.tailored_roles
            for bullet in role.bullets
            if bullet.needs_revision
        )
        if revision_count > 0:
            logger.warning(f"⚠️  {revision_count} bullet(s) flagged for revision - please review")
        
        # Step 6: Validate
        logger.info("Validating tailored resume...")
        from src.utils.validators import validate_tailored_resume
        validate_tailored_resume(resume, tailored)
        
        logger.info("✅ Pipeline completed successfully!")
        return tailored
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


def save_tailored_resume(tailored: TailoredResumeJSON, output_path: Optional[str] = None) -> Path:
    """
    Save tailored resume to JSON file.
    
    Args:
        tailored: Tailored resume JSON
        output_path: Optional output file path
        
    Returns:
        Path to saved file
    """
    if output_path:
        output_file = Path(output_path)
    else:
        output_file = Config.OUTPUT_DIR / "tailored_resume.json"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving tailored resume to: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(tailored.model_dump_json(indent=2))
    
    return output_file


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.agent <job_description_url_or_file>")
        sys.exit(1)
    
    input_source = sys.argv[1]
    
    try:
        jd_text = get_job_description(input_source)
        tailored = run_pipeline(jd_text)
        output_file = save_tailored_resume(tailored)
        print(f"\n✅ Tailored resume saved to: {output_file}")
        
        # Print revision warnings if any
        revision_bullets = []
        for role in tailored.tailored_roles:
            for bullet in role.bullets:
                if bullet.needs_revision:
                    revision_bullets.append({
                        "role": f"{role.company} - {role.title}",
                        "bullet": bullet.text,
                        "note": bullet.revision_note
                    })
        
        if revision_bullets:
            print("\n⚠️  BULLETS REQUIRING REVISION:")
            for i, item in enumerate(revision_bullets, 1):
                print(f"\n{i}. {item['role']}")
                print(f"   Bullet: {item['bullet']}")
                if item['note']:
                    print(f"   Note: {item['note']}")
        
    except Exception as e:
        logger.error(f"Failed to process: {e}")
        sys.exit(1)
