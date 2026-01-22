"""
Standalone Resume-JD Match Scorer

This module scores how well your resumes match a job description.
Run independently without affecting the main tailoring pipeline.

Usage:
    python -m src.match_scorer "https://job-posting-url.com"
    python -m src.match_scorer path/to/job_description.txt
"""

import sys
import logging
from pathlib import Path
from typing import Tuple, Dict, List

# Reuse pipeline modules (read-only, doesn't modify anything)
from src.utils.web_scraper import scrape_job_description
from src.utils.resume_selector import load_candidates, keyword_score, ResumeCandidate
from src.utils.io_pdf import pdf_to_text
from src.utils.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def get_jd_text(source: str) -> str:
    """
    Get job description text from URL or file path.
    
    Args:
        source: URL or file path to job description
        
    Returns:
        Job description text
    """
    # Check if it's a URL
    if source.startswith(('http://', 'https://')):
        logger.info(f"🌐 Scraping job description from URL...")
        jd_text = scrape_job_description(source)
    else:
        # Treat as file path
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source}")
        logger.info(f"📄 Reading job description from file...")
        jd_text = path.read_text(encoding='utf-8')
    
    if not jd_text or len(jd_text.strip()) < 100:
        raise ValueError(f"Job description too short or empty ({len(jd_text)} chars)")
    
    return jd_text


def score_all_resumes(jd_text: str) -> List[Tuple[ResumeCandidate, float]]:
    """
    Score all resumes against a job description.
    
    Args:
        jd_text: Job description text
        
    Returns:
        List of (candidate, score) tuples sorted by score descending
    """
    index_path = str(Config.RESUME_INDEX_PATH)
    candidates = load_candidates(index_path)
    
    if not candidates:
        raise ValueError("No resume candidates found in index")
    
    results = []
    for candidate in candidates:
        score = keyword_score(jd_text, candidate.keywords)
        results.append((candidate, score))
    
    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def normalize_score(raw_score: float, max_possible: float = 30.0) -> float:
    """
    Normalize raw keyword score to 0-10 scale.
    
    Raw scores typically range from 0-30+ depending on keyword matches.
    - 0-5: Poor match (1-3/10)
    - 5-10: Fair match (3-5/10)
    - 10-20: Good match (5-7/10)
    - 20-30: Excellent match (7-9/10)
    - 30+: Perfect match (9-10/10)
    """
    if raw_score <= 0:
        return 0.0
    
    # Use logarithmic-ish scaling for better distribution
    if raw_score >= max_possible:
        return 10.0
    
    # Linear scaling with floor
    normalized = (raw_score / max_possible) * 10.0
    return round(min(10.0, max(0.0, normalized)), 1)


def get_match_rating(score: float) -> str:
    """Get a text rating for the score."""
    if score >= 8.0:
        return "🟢 Excellent Match"
    elif score >= 6.0:
        return "🟡 Good Match"
    elif score >= 4.0:
        return "🟠 Fair Match"
    elif score >= 2.0:
        return "🔴 Weak Match"
    else:
        return "⚫ Poor Match"


def run_match_scorer(source: str) -> Dict:
    """
    Main function to score resumes against a job description.
    
    Args:
        source: URL or file path to job description
        
    Returns:
        Dictionary with match results
    """
    print("\n" + "="*60)
    print("📊 RESUME-JD MATCH SCORER")
    print("="*60 + "\n")
    
    # Get JD text
    jd_text = get_jd_text(source)
    logger.info(f"   ✓ Extracted {len(jd_text)} characters\n")
    
    # Score all resumes
    logger.info("📋 Scoring resumes against job description...\n")
    results = score_all_resumes(jd_text)
    
    # Find max raw score for normalization
    max_raw = max(r[1] for r in results) if results else 1.0
    max_possible = max(30.0, max_raw * 1.2)  # Dynamic ceiling
    
    # Display results
    print("-"*60)
    print(f"{'Resume':<30} {'Raw Score':>12} {'Match (0-10)':>12}")
    print("-"*60)
    
    for candidate, raw_score in results:
        normalized = normalize_score(raw_score, max_possible)
        print(f"{candidate.label:<30} {raw_score:>12.1f} {normalized:>12.1f}")
    
    print("-"*60 + "\n")
    
    # Best match details
    best_candidate, best_raw = results[0]
    best_score = normalize_score(best_raw, max_possible)
    rating = get_match_rating(best_score)
    
    print("🏆 BEST MATCH:")
    print(f"   Resume: {best_candidate.label}")
    print(f"   Score:  {best_score}/10")
    print(f"   Rating: {rating}")
    print(f"   Path:   {best_candidate.path}\n")
    
    # Show matched keywords
    jd_lower = jd_text.lower()
    matched_keywords = [kw for kw in best_candidate.keywords if kw.lower() in jd_lower]
    if matched_keywords:
        print(f"   Matched Keywords ({len(matched_keywords)}):")
        for kw in matched_keywords[:15]:
            print(f"     • {kw}")
        if len(matched_keywords) > 15:
            print(f"     ... and {len(matched_keywords) - 15} more")
    
    print("\n" + "="*60 + "\n")
    
    return {
        "best_match": {
            "resume": best_candidate.label,
            "path": best_candidate.path,
            "score": best_score,
            "raw_score": best_raw,
            "rating": rating,
            "matched_keywords": matched_keywords
        },
        "all_results": [
            {
                "resume": c.label,
                "score": normalize_score(s, max_possible),
                "raw_score": s
            }
            for c, s in results
        ]
    }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.match_scorer <job_url_or_file>")
        print("\nExamples:")
        print("  python -m src.match_scorer 'https://jobs.example.com/posting/123'")
        print("  python -m src.match_scorer job_description.txt")
        sys.exit(1)
    
    source = sys.argv[1]
    
    try:
        run_match_scorer(source)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
