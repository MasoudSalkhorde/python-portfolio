"""Validation utilities for resume tailoring."""
import logging
from src.utils.schemas import ResumeJSON, TailoredResumeJSON

logger = logging.getLogger(__name__)


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
    
    # Check bullet provenance
    for role in tailored.tailored_roles:
        if role.company not in valid_companies:
            errors.append(f"New company not allowed: {role.company}")
            logger.error(f"Validation error: New company '{role.company}' not in original resume")
        
        for bullet in role.bullets:
            for sid in bullet.source_bullet_ids:
                if sid not in valid_ids:
                    errors.append(f"Invalid source bullet id: {sid}")
                    logger.error(f"Validation error: Invalid source bullet ID '{sid}'")
    
    # Check if skills are reasonable (allow some new skills but warn)
    new_skills = set(tailored.tailored_skills) - valid_skills
    if new_skills:
        logger.warning(f"New skills added that weren't in original resume: {new_skills}")
        # Don't error, just warn - skills can be added
    
    if errors:
        error_msg = "; ".join(errors)
        raise ValueError(f"Validation failed: {error_msg}")
    
    logger.debug("Validation passed")
