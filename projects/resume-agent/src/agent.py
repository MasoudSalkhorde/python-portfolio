"""
Modular resume tailoring agent.

Architecture:
1. Extract JD structure
2. Extract Resume structure  
3. Tailor header (headline, summary, skills)
4. Tailor each role separately
5. Assemble final resume
6. Final review for gaps

This modular approach gives the LLM focused, simple tasks.
"""
import json
import time
from typing import Type, TypeVar, Optional, List
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from openai.types.chat import ChatCompletion

from src.utils.schemas import (
    JobDescriptionJSON, 
    ResumeJSON, 
    TailoredResumeJSON,
    TailoredRole,
    TailoredBullet,
    HeaderOutput,
    RoleOutput,
    ReviewOutput,
    SkillCategory,
    SkillsOutput,
    ResumeScoreOutput,
    GapCoverageOutput,
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


# =============================================================================
# LLM UTILITIES
# =============================================================================

def call_llm(prompt: str, retry_count: int = 0) -> str:
    """Call OpenAI LLM with retry logic."""
    try:
        logger.debug(f"Calling LLM (attempt {retry_count + 1})")
        response: ChatCompletion = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise JSON-only generator. Return only valid JSON."},
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
            wait_time = (2 ** retry_count) * 5
            logger.warning(f"Rate limit hit. Waiting {wait_time}s...")
            time.sleep(wait_time)
            return call_llm(prompt, retry_count + 1)
        raise APIError(f"Rate limit exceeded after retries") from e
        
    except APITimeoutError as e:
        if retry_count < Config.OPENAI_MAX_RETRIES:
            logger.warning(f"Timeout. Retrying...")
            time.sleep(2)
            return call_llm(prompt, retry_count + 1)
        raise APIError(f"Request timeout after retries") from e
        
    except APIError as e:
        if retry_count < Config.OPENAI_MAX_RETRIES and e.status_code and e.status_code >= 500:
            wait_time = (2 ** retry_count) * 2
            logger.warning(f"Server error. Waiting {wait_time}s...")
            time.sleep(wait_time)
            return call_llm(prompt, retry_count + 1)
        raise


def parse_json_response(raw: str) -> dict:
    """Parse JSON from LLM response, handling markdown wrapping."""
    # Remove markdown code blocks if present
    if "```json" in raw:
        start = raw.find("```json") + 7
        end = raw.find("```", start)
        raw = raw[start:end].strip()
    elif "```" in raw:
        start = raw.find("```") + 3
        end = raw.find("```", start)
        raw = raw[start:end].strip()
    
    return json.loads(raw)


def llm_to_schema(prompt: str, schema: Type[T]) -> T:
    """Call LLM and parse response into Pydantic schema."""
    try:
        raw = call_llm(prompt)
        data = parse_json_response(raw)
        return schema.model_validate(data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise ValueError(f"Invalid JSON response: {e}") from e
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise ValueError(f"Schema validation failed: {e}") from e


def llm_to_dict(prompt: str) -> dict:
    """Call LLM and parse response as dict."""
    raw = call_llm(prompt)
    return parse_json_response(raw)


# =============================================================================
# JOB DESCRIPTION INPUT
# =============================================================================

def get_job_description(input_source: str, use_selenium: bool = True) -> str:
    """Get job description from URL or file path."""
    if is_url(input_source):
        logger.info("Detected URL, scraping job description...")
        return scrape_job_description(input_source, use_selenium=use_selenium)
    else:
        jd_path = Path(input_source)
        if not jd_path.exists():
            raise FileNotFoundError(f"Job description file not found: {jd_path}")
        
        logger.info(f"Reading job description from: {jd_path}")
        with open(jd_path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip():
            raise ValueError(f"Job description file is empty: {jd_path}")
        return content


# =============================================================================
# MODULAR PIPELINE
# =============================================================================

def run_pipeline(jd_text: str, resume_index_path: Optional[str] = None) -> tuple:
    """
    Run the modular resume tailoring pipeline.
    
    Steps:
    1. Select best resume
    2. Extract JD and Resume structures
    3. Tailor header (1 LLM call)
    4. Tailor each role (1 LLM call per role)
    5. Final review (1 LLM call)
    6. Assemble and validate
    7. Score resume (Talent Acquisition Manager evaluation)
    
    Returns:
        Tuple of (TailoredResumeJSON, ResumeScoreOutput)
    """
    from src.utils.prompts import (
        prompt_extract_jd,
        prompt_extract_resume,
        prompt_tailor_header,
        prompt_tailor_skills,
        prompt_tailor_role,
        prompt_tailor_role_low_match,
        prompt_final_review,
        prompt_score_resume,
        prompt_cover_gaps,
        prompt_final_score_resume,
    )
    
    logger.info("=" * 50)
    logger.info("Starting MODULAR resume tailoring pipeline")
    logger.info("=" * 50)
    
    # Step 1: Select best resume(s)
    logger.info("\n[Step 1] Selecting best resume...")
    index_path = resume_index_path or str(Config.RESUME_INDEX_PATH)
    selection = choose_resume_pdf(jd_text, index_path)
    
    best_resume = selection.primary
    is_low_match = selection.is_low_match
    
    logger.info(f"  → Primary: {best_resume.label}")
    if selection.use_secondary and selection.secondary:
        logger.info(f"  → Secondary: {selection.secondary.label} (will use for additional skills/metrics)")
    if is_low_match:
        logger.warning(f"  → ⚠️ LOW MATCH MODE: Will write responsibilities based on JD")
    
    # Step 2: Extract resume text
    logger.info("\n[Step 2] Extracting resume text from PDF...")
    resume_text = pdf_to_text(best_resume.path)
    if not resume_text or len(resume_text.strip()) < 50:
        raise ValueError(f"Resume PDF appears empty: {best_resume.path}")
    
    # Extract secondary resume text if available
    secondary_resume_text = None
    if selection.use_secondary and selection.secondary:
        logger.info(f"  → Also extracting secondary resume: {selection.secondary.label}")
        secondary_resume_text = pdf_to_text(selection.secondary.path)
    
    # Step 3: Extract structures (2 LLM calls)
    logger.info("\n[Step 3] Extracting JD structure...")
    jd = llm_to_schema(prompt_extract_jd(jd_text), JobDescriptionJSON)
    logger.info(f"  → {jd.company} - {jd.role_title}")
    logger.info(f"  → {len(jd.responsibilities)} responsibilities found")
    
    logger.info("\n[Step 4] Extracting resume structure...")
    resume = llm_to_schema(prompt_extract_resume(resume_text), ResumeJSON)
    logger.info(f"  → {resume.name} with {len(resume.roles)} roles")
    
    # Extract secondary resume structure if available
    secondary_resume = None
    secondary_skills = []
    secondary_metrics = []
    
    if secondary_resume_text:
        logger.info(f"  → Extracting secondary resume structure...")
        secondary_resume = llm_to_schema(prompt_extract_resume(secondary_resume_text), ResumeJSON)
        
        # Extract additional skills from secondary resume
        secondary_skills = [s for s in secondary_resume.skills if s not in resume.skills]
        logger.info(f"  → Found {len(secondary_skills)} additional skills from secondary resume")
        
        # Extract metrics/outcomes from secondary resume bullets
        for role in secondary_resume.roles:
            for bullet in role.bullets:
                bullet_text = bullet.text if hasattr(bullet, 'text') else str(bullet)
                # Check if bullet contains metrics (%, $, numbers)
                if any(char in bullet_text for char in ['%', '$']) or any(c.isdigit() for c in bullet_text):
                    secondary_metrics.append({
                        "company": role.company,
                        "text": bullet_text
                    })
        logger.info(f"  → Found {len(secondary_metrics)} metrics from secondary resume")
    
    # Store original companies for validation
    original_companies = [role.company for role in resume.roles]
    
    # Step 5: Tailor header (1 LLM call)
    logger.info("\n[Step 5] Tailoring header (headline + summary)...")
    
    header = llm_to_schema(
        prompt_tailor_header(jd.model_dump(), resume.model_dump()),
        HeaderOutput
    )
    logger.info(f"  → Headline: {header.headline[:50]}...")
    
    # Step 5b: Tailor skills separately (based ONLY on JD)
    logger.info("\n[Step 5b] Tailoring skills (from JD only)...")
    
    skills_output = llm_to_schema(
        prompt_tailor_skills(jd_json=jd.model_dump()),
        SkillsOutput
    )
    
    # Replace header skills with the JD-based skills output
    header.skills = skills_output.skills
    
    logger.info(f"  → {len(skills_output.skills)} skill categories generated")
    logger.info(f"  → {len(skills_output.ats_keywords_used)} ATS keywords included")
    if skills_output.coverage_notes:
        logger.info(f"  → Coverage: {skills_output.coverage_notes[:80]}...")
    
    # Step 6: Tailor each role (1 LLM call per role)
    logger.info(f"\n[Step 6] Tailoring {len(resume.roles)} roles...")
    
    tailored_roles: List[TailoredRole] = []
    used_responsibilities: List[str] = []
    all_responsibilities = jd.responsibilities.copy()
    
    for i, role in enumerate(resume.roles):
        logger.info(f"\n  [Role {i+1}/{len(resume.roles)}] {role.company} - {role.title}")
        
        # Determine which responsibilities this role should cover
        if i == 0:
            # First role: top 4-5 responsibilities
            responsibilities_to_cover = all_responsibilities[:5]
        elif i == 1:
            # Second role: next 3-4 responsibilities
            remaining = [r for r in all_responsibilities if r not in used_responsibilities]
            responsibilities_to_cover = remaining[:4]
        else:
            # Other roles: remaining responsibilities
            remaining = [r for r in all_responsibilities if r not in used_responsibilities]
            responsibilities_to_cover = remaining[:3]
        
        # Call LLM for this role - use low_match prompt if JD is significantly different
        if is_low_match:
            role_prompt = prompt_tailor_role_low_match(
                jd_json=jd.model_dump(),
                role=role.model_dump(),
                role_index=i,
                total_roles=len(resume.roles),
                responsibilities_to_cover=responsibilities_to_cover,
                used_responsibilities=used_responsibilities,
                secondary_metrics=secondary_metrics if secondary_metrics else None
            )
        else:
            role_prompt = prompt_tailor_role(
                jd_json=jd.model_dump(),
                role=role.model_dump(),
                role_index=i,
                total_roles=len(resume.roles),
                responsibilities_to_cover=responsibilities_to_cover,
                used_responsibilities=used_responsibilities,
                secondary_metrics=secondary_metrics if secondary_metrics else None
            )
        
        role_output = llm_to_schema(role_prompt, RoleOutput)
        
        # CRITICAL: Enforce original company name
        if role_output.company != original_companies[i]:
            logger.warning(f"  ⚠️  Company name changed, reverting: {role_output.company} → {original_companies[i]}")
            role_output.company = original_companies[i]
        
        # Track covered responsibilities
        used_responsibilities.extend(role_output.responsibilities_covered)
        
        # Convert to TailoredRole
        tailored_role = TailoredRole(
            company=role_output.company,
            title=role_output.title,
            dates=role_output.dates,
            bullets=role_output.bullets
        )
        tailored_roles.append(tailored_role)
        
        # Log bullet stats
        revision_count = sum(1 for b in role_output.bullets if b.needs_revision)
        logger.info(f"    → {len(role_output.bullets)} bullets ({revision_count} need revision)")
        logger.info(f"    → Covers: {role_output.responsibilities_covered[:2]}...")
    
    # Step 7: Final review (1 LLM call)
    logger.info("\n[Step 7] Final review...")
    
    # Assemble preliminary resume for review
    # Convert skills to dicts if they are SkillCategory objects
    skills_for_review = []
    for skill in header.skills:
        if hasattr(skill, "model_dump"):
            skills_for_review.append(skill.model_dump())
        elif isinstance(skill, dict):
            skills_for_review.append(skill)
        else:
            skills_for_review.append({"category": "Skills", "skills": [str(skill)]})
    
    preliminary = {
        "headline": header.headline,
        "summary": header.summary,
        "skills": skills_for_review,
        "roles": [r.model_dump() for r in tailored_roles]
    }
    
    review = llm_to_schema(
        prompt_final_review(preliminary, jd.model_dump()),
        ReviewOutput
    )
    
    if review.gaps_to_confirm:
        logger.warning(f"  ⚠️  {len(review.gaps_to_confirm)} gaps identified")
    
    # Step 8: Assemble final resume
    logger.info("\n[Step 8] Assembling final resume...")
    
    # Extract education as strings if they're dicts
    education_list = []
    for edu in resume.education:
        if isinstance(edu, dict):
            parts = []
            if edu.get("degree"):
                parts.append(edu["degree"])
            if edu.get("institution"):
                parts.append(edu["institution"])
            education_list.append("\n".join(parts) if parts else str(edu))
        else:
            education_list.append(str(edu))
    
    tailored = TailoredResumeJSON(
        # Personal info from original resume
        name=resume.name,
        email=resume.email,
        location=resume.location,
        linkedin=None,  # TODO: extract from resume if available
        
        # Target job info
        target_company=jd.company,
        target_role=jd.role_title,
        
        # Tailored content
        tailored_headline=header.headline,
        tailored_summary=header.summary,
        tailored_skills=header.skills,
        tailored_roles=tailored_roles,
        
        # Preserved from original resume
        education=education_list,
        certifications=resume.certifications,
        awards=resume.awards,
        
        # Metadata
        change_log=review.change_log,
        questions_for_user=review.questions_for_user,
        gaps_to_confirm=review.gaps_to_confirm
    )
    
    # Step 9: Validate
    logger.info("\n[Step 9] Validating...")
    from src.utils.validators import validate_tailored_resume
    validate_tailored_resume(resume, tailored)
    
    # Count total revisions needed
    total_revisions = sum(
        1 for role in tailored.tailored_roles
        for bullet in role.bullets
        if bullet.needs_revision
    )
    
    # Step 10: Score resume (Talent Acquisition Manager evaluation)
    logger.info("\n[Step 10] Scoring resume (Talent Acquisition Manager evaluation)...")
    score_result = llm_to_schema(
        prompt_score_resume(tailored.model_dump(), jd.model_dump()),
        ResumeScoreOutput
    )
    logger.info(f"  → Interview Selection Score: {score_result.score}/100")
    if score_result.gaps:
        logger.info(f"  → Gaps identified: {len(score_result.gaps)}")
    
    # Step 11: Cover gaps by adding new bullet points
    if score_result.gaps:
        logger.info("\n[Step 11] Adding bullet points to cover gaps...")
        gap_coverage = llm_to_schema(
            prompt_cover_gaps(tailored.model_dump(), score_result.model_dump(), jd.model_dump()),
            GapCoverageOutput
        )
        
        # Apply the gap coverage additions to the tailored resume
        new_bullets_added = 0
        for role_update in gap_coverage.roles_with_additions:
            # Find the corresponding role in tailored resume
            if role_update.role_index < len(tailored.tailored_roles):
                original_role = tailored.tailored_roles[role_update.role_index]
                
                # Add only the NEW bullets (is_new=True)
                for bullet in role_update.bullets:
                    if bullet.is_new:
                        new_bullet = TailoredBullet(
                            text=bullet.text,
                            source_bullet_ids=[],
                            needs_revision=bullet.needs_revision,
                            revision_note=bullet.revision_note
                        )
                        original_role.bullets.append(new_bullet)
                        new_bullets_added += 1
        
        logger.info(f"  → Added {new_bullets_added} new bullet(s) to cover gaps")
        logger.info(f"  → Gaps addressed: {gap_coverage.gaps_addressed}")
        if gap_coverage.gaps_not_addressable:
            logger.warning(f"  → Gaps not addressable: {gap_coverage.gaps_not_addressable}")
    else:
        logger.info("\n[Step 11] No gaps to cover - skipping gap coverage step")
        gap_coverage = None
    
    # Recount revisions after gap coverage
    total_revisions = sum(
        1 for role in tailored.tailored_roles
        for bullet in role.bullets
        if bullet.needs_revision
    )
    
    # Step 12: Re-score the final resume after gap coverage
    logger.info("\n[Step 12] Re-scoring final resume after gap coverage...")
    
    # Get the gaps that were addressed (if gap_coverage exists)
    initial_gaps = score_result.gaps if score_result else []
    gaps_addressed = gap_coverage.gaps_addressed if gap_coverage else []
    
    final_score_result = llm_to_schema(
        prompt_final_score_resume(
            tailored.model_dump(), 
            jd.model_dump(),
            initial_gaps,
            gaps_addressed
        ),
        ResumeScoreOutput
    )
    logger.info(f"  → Final Interview Selection Score: {final_score_result.score}/100")
    logger.info(f"  → Score improvement: {final_score_result.score - score_result.score} points")
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ Pipeline completed successfully!")
    logger.info(f"   Roles: {len(tailored.tailored_roles)}")
    logger.info(f"   Bullets needing revision: {total_revisions}")
    logger.info(f"   Gaps to confirm: {len(tailored.gaps_to_confirm)}")
    logger.info(f"   Initial Score: {score_result.score}/100")
    logger.info(f"   Final Score: {final_score_result.score}/100")
    logger.info("=" * 50)
    
    return tailored, score_result, gap_coverage, final_score_result


# =============================================================================
# OUTPUT
# =============================================================================

def save_tailored_resume(
    tailored: TailoredResumeJSON, 
    score: Optional[ResumeScoreOutput] = None,
    gap_coverage: Optional[GapCoverageOutput] = None,
    final_score: Optional[ResumeScoreOutput] = None,
    output_path: Optional[str] = None
) -> Path:
    """Save tailored resume, score, gap coverage, and final score to JSON file."""
    if output_path:
        output_file = Path(output_path)
    else:
        output_file = Config.OUTPUT_DIR / "tailored_resume.json"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Combine tailored resume with score, gap coverage, and final score data
    output_data = tailored.model_dump()
    if score:
        output_data["score"] = score.model_dump()
    if gap_coverage:
        output_data["gap_coverage"] = gap_coverage.model_dump()
    if final_score:
        output_data["final_score"] = final_score.model_dump()
    
    logger.info(f"Saving to: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    return output_file


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.agent <job_description_url_or_file>")
        sys.exit(1)
    
    input_source = sys.argv[1]
    
    try:
        jd_text = get_job_description(input_source)
        tailored, score, gap_coverage, final_score = run_pipeline(jd_text)
        output_file = save_tailored_resume(tailored, score, gap_coverage, final_score)
        
        print(f"\n✅ Tailored resume saved to: {output_file}")
        
        # Print score
        print(f"\n📊 INTERVIEW SELECTION SCORE: {score.score}/100")
        print(f"   {score.score_rationale}")
        
        if score.gaps:
            print(f"\n🔍 GAPS TO REACH 100/100:")
            for i, gap in enumerate(score.gaps, 1):
                print(f"   {i}. {gap}")
        
        if score.recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(score.recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Print revision summary
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
            print(f"\n⚠️  {len(revision_bullets)} BULLETS NEED REVISION:")
            for i, item in enumerate(revision_bullets, 1):
                print(f"\n{i}. {item['role']}")
                print(f"   {item['bullet'][:80]}...")
                if item['note']:
                    print(f"   Note: {item['note']}")
        
        if tailored.gaps_to_confirm:
            print(f"\n⚠️  GAPS TO CONFIRM:")
            for gap in tailored.gaps_to_confirm:
                print(f"   - {gap}")
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        sys.exit(1)
