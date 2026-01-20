"""Validation utilities for resume tailoring."""
import logging
import re
from src.utils.schemas import ResumeJSON, TailoredResumeJSON

logger = logging.getLogger(__name__)


def has_outcome(text: str) -> bool:
    """
    Check if a bullet point contains an outcome (metric, percentage, dollar amount, KPI).
    
    Args:
        text: Bullet point text
        
    Returns:
        True if the text contains an outcome
    """
    # Patterns for outcomes:
    # - Percentages: "25%", "+30%", "-15%"
    # - Dollar amounts: "$5M", "$1.2B", "$500K"
    # - Numbers with context: "10 channels", "3.5x ROAS", "50% increase"
    # - KPIs: "ROAS", "LTV", "CPI" with numbers
    # - Results: "increased", "reduced", "achieved", "managed" with numbers
    
    outcome_patterns = [
        r'\$[\d.,]+[KMB]?',  # Dollar amounts
        r'\d+\.?\d*\s*%',  # Percentages
        r'\d+\.?\d*\s*x\s*[A-Z]+',  # Multipliers like "3.5x ROAS"
        r'\d+\.?\d*\s*(channels|partners|campaigns|markets)',  # Counts
        r'(increased|reduced|improved|achieved|managed|grew|decreased|lowered|raised|boosted).*?\d+',  # Action verbs with numbers
        r'(ROAS|LTV|CPI|CTR|CVR|CPA|CPC|CPM).*?\d+',  # KPIs with numbers
        r'\d+\.?\d*\s*(million|billion|thousand)',  # Written numbers
    ]
    
    text_lower = text.lower()
    for pattern in outcome_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False


def validate_outcome_distribution(tailored: TailoredResumeJSON) -> None:
    """
    Validate that each role has the required outcome distribution.
    
    Args:
        tailored: Tailored resume JSON
        
    Raises:
        ValueError: If outcome distribution requirements are not met
    """
    logger.debug("Validating outcome distribution...")
    
    warnings = []
    
    for role_idx, role in enumerate(tailored.tailored_roles, 1):
        bullets_with_outcomes = []
        bullets_without_outcomes = []
        
        for bullet in role.bullets:
            if has_outcome(bullet.text):
                bullets_with_outcomes.append(bullet)
            else:
                bullets_without_outcomes.append(bullet)
        
        outcome_count = len(bullets_with_outcomes)
        no_outcome_count = len(bullets_without_outcomes)
        total_bullets = len(role.bullets)
        
        # First role can have up to 7 bullets, others typically 5-6
        is_first_role = role_idx == 1
        is_second_role = role_idx == 2
        max_expected = 7 if is_first_role else 6
        
        # Check that first two bullets have outcomes (for first two roles)
        if (is_first_role or is_second_role) and total_bullets >= 2:
            first_two_bullets = role.bullets[:2]
            first_two_with_outcomes = sum(1 for b in first_two_bullets if has_outcome(b.text))
            
            if first_two_with_outcomes < 2:
                warnings.append(
                    f"Role {role_idx} ({role.company}): First two bullets must have outcomes. "
                    f"Only {first_two_with_outcomes} of the first 2 bullets have outcomes."
                )
            else:
                logger.debug(
                    f"Role {role_idx} ({role.company}): ✅ First two bullets have outcomes"
                )
        
        # Check requirements
        if outcome_count < 2:
            warnings.append(
                f"Role {role_idx} ({role.company}): Only {outcome_count} bullet(s) with outcomes. "
                f"Requires at least 2-4 bullets with outcomes."
            )
        elif outcome_count > 4:
            # For first role with 7 bullets, having 5 outcomes is acceptable
            if is_first_role and total_bullets == 7 and outcome_count == 5:
                logger.debug(
                    f"Role {role_idx} ({role.company}): {outcome_count} bullets with outcomes "
                    f"(acceptable for first role with 7 bullets)"
                )
            else:
                logger.debug(
                    f"Role {role_idx} ({role.company}): {outcome_count} bullets with outcomes "
                    f"(recommended: 2-4)"
                )
        
        if no_outcome_count < 1:
            warnings.append(
                f"Role {role_idx} ({role.company}): No bullets without outcomes. "
                f"Requires at least 1 bullet without outcome."
            )
        
        # Check total bullet count
        if total_bullets > max_expected:
            logger.debug(
                f"Role {role_idx} ({role.company}): Has {total_bullets} bullets "
                f"(expected: up to {max_expected})"
            )
        
        logger.debug(
            f"Role {role_idx} ({role.company}): {total_bullets} total bullets, "
            f"{outcome_count} with outcomes, {no_outcome_count} without outcomes"
        )
    
    if warnings:
        warning_msg = "\n".join(warnings)
        logger.warning(f"Outcome distribution warnings:\n{warning_msg}")
        # Don't raise error, just warn - the LLM should handle this, but we log it


def validate_tailored_resume(resume: ResumeJSON, tailored: TailoredResumeJSON) -> None:
    """
    Validate that tailored resume is consistent with original resume.
    
    Args:
        resume: Original resume JSON
        tailored: Tailored resume JSON
        
    Raises:
        ValueError: If validation fails
    """
    logger.debug("Validating tailored resume...")
    
    # Collect valid IDs and companies
    valid_ids = {b.id for r in resume.roles for b in r.bullets}
    valid_companies = {r.company for r in resume.roles}
    valid_skills = set(resume.skills)
    
    errors = []
    
    # Check company names (critical validation)
    for role in tailored.tailored_roles:
        if role.company not in valid_companies:
            error_msg = (
                f"New company not allowed: '{role.company}'. "
                f"Valid companies from resume: {', '.join(sorted(valid_companies))}. "
                f"The LLM must use exact company names from the original resume, not invent new ones."
            )
            errors.append(error_msg)
            logger.error(f"Validation error: {error_msg}")
        
        # Check bullet provenance (warning only, not error)
        for bullet in role.bullets:
            for sid in bullet.source_bullet_ids:
                if sid and sid not in valid_ids:
                    # Just log warning, don't fail - new bullets may not have valid source IDs
                    logger.debug(f"Note: Bullet references unknown source ID '{sid}' (may be a new bullet)")
    
    # Check if skills are reasonable (allow some new skills but warn)
    # Handle both flat and categorized skills
    tailored_skills_flat = []
    for skill in tailored.tailored_skills:
        if isinstance(skill, dict) and "skills" in skill:
            tailored_skills_flat.extend(skill.get("skills", []))
        elif hasattr(skill, "skills"):
            tailored_skills_flat.extend(skill.skills)
        elif isinstance(skill, str):
            tailored_skills_flat.append(skill)
    
    new_skills = set(tailored_skills_flat) - valid_skills
    if new_skills:
        logger.warning(f"New skills added that weren't in original resume: {new_skills}")
        # Don't error, just warn - skills can be added
    
    if errors:
        error_msg = "; ".join(errors)
        raise ValueError(f"Validation failed: {error_msg}")
    
    # Validate outcome distribution (warns but doesn't error)
    validate_outcome_distribution(tailored)
    
    logger.debug("Validation passed")
