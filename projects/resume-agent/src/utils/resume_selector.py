"""Resume selection utilities."""
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from src.utils.io_pdf import pdf_to_text
from src.utils.config import Config

logger = logging.getLogger(__name__)


@dataclass
class ResumeCandidate:
    """Represents a resume candidate for selection."""
    id: str
    path: str
    label: str
    keywords: List[str]


def load_candidates(index_path: str) -> List[ResumeCandidate]:
    """
    Load resume candidates from index file.
    
    Args:
        index_path: Path to resume index JSON file
        
    Returns:
        List of resume candidates
        
    Raises:
        FileNotFoundError: If index file doesn't exist
        ValueError: If index file is invalid
    """
    index_file = Path(index_path)
    
    if not index_file.exists():
        raise FileNotFoundError(f"Resume index file not found: {index_path}")
    
    logger.debug(f"Loading resume candidates from: {index_path}")
    
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        
        if not isinstance(items, list):
            raise ValueError(f"Resume index must be a list, got {type(items)}")
        
        candidates = []
        for item in items:
            if not isinstance(item, dict):
                logger.warning(f"Skipping invalid item in index: {item}")
                continue
            
            try:
                candidate = ResumeCandidate(**item)
                # Validate that PDF exists
                if not Path(candidate.path).exists():
                    logger.warning(f"Resume PDF not found: {candidate.path}, skipping candidate {candidate.id}")
                    continue
                candidates.append(candidate)
            except Exception as e:
                logger.warning(f"Failed to create candidate from item {item}: {e}")
                continue
        
        if not candidates:
            raise ValueError(f"No valid candidates found in index: {index_path}")
        
        logger.info(f"Loaded {len(candidates)} resume candidates")
        return candidates
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in resume index: {e}")
        raise ValueError(f"Resume index file is not valid JSON: {index_path}") from e
    except Exception as e:
        logger.error(f"Failed to load resume candidates: {e}")
        raise


def keyword_score(jd_text: str, keywords: List[str]) -> float:
    """
    Calculate keyword match score between job description and resume keywords.
    
    Args:
        jd_text: Job description text
        keywords: List of keywords associated with resume
        
    Returns:
        Match score (higher is better)
    """
    if not keywords:
        return 0.0
    
    jd = jd_text.lower()
    jd_tokens = set(jd.split())
    score = 0.0

    for kw in keywords:
        if not kw:
            continue
            
        kw_l = kw.lower()
        kw_tokens = set(kw_l.split())

        if kw_l in jd:
            score += 2.0  # Strong signal (exact match)
        elif kw_tokens & jd_tokens:
            score += 1.0  # Weaker signal (partial match)

    return score


@dataclass
class ResumeSelection:
    """Result of resume selection process."""
    primary: ResumeCandidate
    secondary: Optional[ResumeCandidate]  # Close second-best, if any
    scores: Dict[str, float]
    is_low_match: bool
    use_secondary: bool  # True if secondary resume should be used for additional context


def choose_resume_pdf(
    jd_text: str,
    index_path: str = None
) -> ResumeSelection:
    """
    Choose the best matching resume PDF based on job description.
    
    If a second resume scores within 20% of the best, it will be included
    as a secondary source for additional skills and metrics.
    
    Args:
        jd_text: Job description text
        index_path: Path to resume index JSON file (defaults to config)
        
    Returns:
        ResumeSelection with primary resume, optional secondary, scores, and flags
        
    Raises:
        ValueError: If no candidates available or selection fails
    """
    if not jd_text or not jd_text.strip():
        raise ValueError("Job description text cannot be empty")
    
    index_file = index_path or str(Config.RESUME_INDEX_PATH)
    candidates = load_candidates(index_file)
    
    if not candidates:
        raise ValueError("No resume candidates available")
    
    logger.info(f"Evaluating {len(candidates)} resume candidates...")
    
    scores = {}
    for candidate in candidates:
        try:
            score = keyword_score(jd_text, candidate.keywords)
            scores[candidate.id] = score
            # Always log scores for visibility
            logger.info(f"  📊 {candidate.label}: score={score:.1f}")
        except Exception as e:
            logger.warning(f"Failed to score candidate {candidate.id}: {e}")
            scores[candidate.id] = 0.0
    
    if not scores:
        raise ValueError("Failed to score any candidates")
    
    # Sort candidates by score (descending)
    sorted_candidates = sorted(candidates, key=lambda c: scores.get(c.id, 0.0), reverse=True)
    
    best = sorted_candidates[0]
    best_score = scores[best.id]
    
    # Check for close second-best
    secondary = None
    use_secondary = False
    SECONDARY_THRESHOLD = 0.80  # Use secondary if within 20% of best score
    
    if len(sorted_candidates) > 1:
        second_best = sorted_candidates[1]
        second_score = scores[second_best.id]
        
        if best_score > 0 and second_score >= best_score * SECONDARY_THRESHOLD:
            secondary = second_best
            use_secondary = True
            logger.info(f"  🔀 Secondary resume: {secondary.label} (score={second_score:.1f}, within {SECONDARY_THRESHOLD*100:.0f}% of best)")
    
    # Calculate match quality
    LOW_MATCH_THRESHOLD = 6.0
    is_low_match = best_score < LOW_MATCH_THRESHOLD
    
    if is_low_match:
        logger.warning(f"⚠️  LOW MATCH DETECTED: Best score is {best_score:.2f} (threshold: {LOW_MATCH_THRESHOLD})")
        logger.warning(f"   Job description appears significantly different from available resumes.")
        logger.warning(f"   Will use work history from '{best.label}' but write responsibilities based on JD.")
    else:
        logger.info(f"  ✅ Selected primary: {best.label} (score: {best_score:.1f})")
    
    return ResumeSelection(
        primary=best,
        secondary=secondary,
        scores=scores,
        is_low_match=is_low_match,
        use_secondary=use_secondary
    )
