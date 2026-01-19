"""Keyword optimization utilities for ATS matching."""
import logging
import re
from typing import List, Dict, Set, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

# Common skill synonyms and variations
SKILL_SYNONYMS = {
    # Machine Learning / AI
    "machine learning": ["ML", "machine-learning", "ML/AI", "artificial intelligence"],
    "AI": ["artificial intelligence", "machine learning", "ML"],
    "deep learning": ["neural networks", "NN", "CNN", "RNN"],
    
    # Data Science
    "data science": ["data analytics", "data analysis", "analytics"],
    "data analysis": ["data science", "analytics", "data analytics"],
    
    # Programming
    "python": ["Python", "PYTHON"],
    "javascript": ["JS", "JavaScript", "ECMAScript"],
    "sql": ["SQL", "Structured Query Language"],
    
    # UA/Marketing
    "user acquisition": ["UA", "acquisition", "user growth"],
    "ROAS": ["return on ad spend", "return on advertising spend"],
    "LTV": ["lifetime value", "customer lifetime value", "CLV"],
    "CPI": ["cost per install", "cost-per-install"],
    "CPC": ["cost per click", "cost-per-click"],
    "CPM": ["cost per mille", "cost per thousand"],
    
    # Platforms
    "google ads": ["Google AdWords", "AdWords", "Google Advertising"],
    "facebook ads": ["Meta Ads", "Facebook Advertising", "Meta Advertising"],
    "tiktok ads": ["TikTok Advertising", "TikTok for Business"],
    
    # Tools
    "excel": ["Microsoft Excel", "MS Excel"],
    "powerpoint": ["Microsoft PowerPoint", "MS PowerPoint", "PowerPoint"],
}

# Common abbreviations
ABBREVIATIONS = {
    "ML": "machine learning",
    "AI": "artificial intelligence",
    "UA": "user acquisition",
    "ROAS": "return on ad spend",
    "LTV": "lifetime value",
    "CPI": "cost per install",
    "CPC": "cost per click",
    "CPM": "cost per mille",
    "CTR": "click-through rate",
    "CVR": "conversion rate",
    "CPA": "cost per acquisition",
    "SQL": "structured query language",
    "API": "application programming interface",
}


def normalize_keyword(keyword: str) -> str:
    """Normalize a keyword for matching."""
    return keyword.lower().strip()


def expand_keyword_synonyms(keyword: str) -> Set[str]:
    """
    Expand a keyword to include synonyms and variations.
    
    Args:
        keyword: Original keyword
        
    Returns:
        Set of keyword variations including synonyms
    """
    normalized = normalize_keyword(keyword)
    variations = {normalized, keyword}  # Include original
    
    # Check direct synonyms
    if normalized in SKILL_SYNONYMS:
        variations.update(SKILL_SYNONYMS[normalized])
        variations.update(normalize_keyword(v) for v in SKILL_SYNONYMS[normalized])
    
    # Check if it's a synonym of something else
    for main_term, synonyms in SKILL_SYNONYMS.items():
        if normalized in [normalize_keyword(s) for s in synonyms]:
            variations.add(main_term)
            variations.update(synonyms)
    
    # Check abbreviations
    if normalized.upper() in ABBREVIATIONS:
        variations.add(ABBREVIATIONS[normalized.upper()])
        variations.add(normalized.upper())
    
    # Add common variations
    variations.add(keyword.title())
    variations.add(keyword.upper())
    
    return variations


def extract_keywords_from_text(text: str, min_length: int = 2) -> List[str]:
    """
    Extract potential keywords from text.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length
        
    Returns:
        List of potential keywords
    """
    # Remove common stop words and extract meaningful terms
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Extract words (alphanumeric + hyphens, at least 2 chars)
    words = re.findall(r'\b[a-zA-Z0-9-]{2,}\b', text.lower())
    
    # Filter stop words and short words
    keywords = [w for w in words if w not in stop_words and len(w) >= min_length]
    
    # Count frequency
    keyword_counts = Counter(keywords)
    
    # Return most common keywords (top 50)
    return [kw for kw, count in keyword_counts.most_common(50)]


def extract_ats_keywords(jd_text: str, jd_json: Dict) -> Dict[str, List[str]]:
    """
    Extract ATS-relevant keywords from job description.
    
    Args:
        jd_text: Raw job description text
        jd_json: Extracted job description JSON
        
    Returns:
        Dictionary with categorized keywords
    """
    keywords = {
        "skills": [],
        "tools": [],
        "technologies": [],
        "certifications": [],
        "metrics": [],
        "soft_skills": [],
        "industry_terms": [],
    }
    
    # Extract from structured data
    if isinstance(jd_json, dict):
        keywords["tools"] = jd_json.get("networks_tools", [])
        keywords["metrics"] = jd_json.get("metrics", [])
        
        # Extract from requirements
        requirements = jd_json.get("requirements", [])
        for req in requirements:
            if isinstance(req, dict):
                req_keywords = req.get("keywords", [])
                keywords["skills"].extend(req_keywords)
    
    # Extract additional keywords from text
    text_keywords = extract_keywords_from_text(jd_text)
    
    # Categorize keywords (simple heuristic)
    skill_indicators = ["management", "leadership", "strategy", "analysis", "optimization"]
    tool_indicators = ["platform", "tool", "software", "system"]
    
    for kw in text_keywords[:30]:  # Top 30
        kw_lower = kw.lower()
        if any(indicator in kw_lower for indicator in skill_indicators):
            if kw not in keywords["skills"]:
                keywords["skills"].append(kw)
        elif any(indicator in kw_lower for indicator in tool_indicators):
            if kw not in keywords["tools"]:
                keywords["tools"].append(kw)
        elif kw_lower in ["certified", "certification", "certificate"]:
            if kw not in keywords["certifications"]:
                keywords["certifications"].append(kw)
    
    # Remove duplicates while preserving order
    for key in keywords:
        seen = set()
        keywords[key] = [x for x in keywords[key] if x not in seen and not seen.add(x)]
    
    return keywords


def calculate_keyword_coverage(
    jd_keywords: Dict[str, List[str]],
    resume_text: str
) -> Dict[str, Dict]:
    """
    Calculate how well resume covers JD keywords.
    
    Args:
        jd_keywords: Extracted JD keywords
        resume_text: Resume text to check
        
    Returns:
        Coverage report with matched/missing keywords
    """
    resume_lower = resume_text.lower()
    coverage = {}
    
    for category, keywords in jd_keywords.items():
        matched = []
        missing = []
        
        for keyword in keywords:
            keyword_variations = expand_keyword_synonyms(keyword)
            found = False
            
            for variation in keyword_variations:
                if normalize_keyword(variation) in resume_lower:
                    matched.append(keyword)
                    found = True
                    break
            
            if not found:
                missing.append(keyword)
        
        coverage[category] = {
            "matched": matched,
            "missing": missing,
            "coverage_rate": len(matched) / len(keywords) if keywords else 0.0
        }
    
    return coverage


def get_priority_keywords(jd_keywords: Dict[str, List[str]]) -> List[str]:
    """
    Get priority keywords that should definitely appear in resume.
    
    Args:
        jd_keywords: Extracted JD keywords
        
    Returns:
        List of priority keywords
    """
    priority = []
    
    # Skills and tools are high priority
    priority.extend(jd_keywords.get("skills", [])[:10])
    priority.extend(jd_keywords.get("tools", [])[:10])
    priority.extend(jd_keywords.get("technologies", [])[:5])
    
    # Metrics are also important
    priority.extend(jd_keywords.get("metrics", []))
    
    return priority[:20]  # Top 20 priority keywords
