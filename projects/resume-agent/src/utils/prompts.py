"""
Modular prompts for resume tailoring.

Architecture:
- Extract JD → Extract Resume → Tailor Header → Tailor Each Role
- Each LLM call is focused and simple
"""
import json


def _json_only() -> str:
    return "Return ONLY valid JSON. No markdown, no commentary."


# =============================================================================
# EXTRACTION PROMPTS
# =============================================================================

def prompt_extract_jd(jd_text: str) -> str:
    """Extract structured data from job description."""
    return f"""
{_json_only()}

Extract the job description into JSON. List responsibilities in ORDER OF IMPORTANCE (most important first).

JD TEXT:
{jd_text}

OUTPUT:
{{
  "company": "",
  "role_title": "",
  "level": "",
  "location": "",
  "responsibilities": ["#1 most important", "#2 second most important", "..."],
  "requirements": [{{"requirement":"", "type":"must|nice"}}],
  "tools_platforms": ["..."],
  "metrics_kpis": ["..."],
  "keywords": ["important terms for ATS"]
}}
""".strip()


def prompt_extract_resume(resume_text: str) -> str:
    """Extract structured data from resume."""
    return f"""
{_json_only()}

Extract resume into JSON. Preserve ALL metrics exactly. Keep company names exactly as written.

RESUME TEXT:
{resume_text}

OUTPUT:
{{
  "name": "",
  "email": "",
  "location": "",
  "headline": "",
  "summary": ["..."],
  "skills": ["..."],
  "roles": [
    {{
      "company": "",
      "title": "",
      "dates": "",
      "bullets": [{{"id": "company_1", "text": "", "has_metric": true}}]
    }}
  ],
  "education": ["Master of Business Administration, University Name, 2020", "..."],
  "certifications": ["..."]
}}

IMPORTANT: education must be an array of STRINGS, not objects. Format each as "Degree, Institution, Year".
""".strip()


# =============================================================================
# TAILORING PROMPTS (MODULAR)
# =============================================================================

def prompt_tailor_header(jd_json: dict, resume_json: dict) -> str:
    """Tailor headline, summary, and skills to match JD."""
    return f"""
{_json_only()}

Create a tailored headline, summary, and CATEGORIZED skills section for this resume to match the job.

JOB:
- Company: {jd_json.get('company', '')}
- Role: {jd_json.get('role_title', '')}
- Key responsibilities: {json.dumps(jd_json.get('responsibilities', [])[:5])}
- Required tools: {json.dumps(jd_json.get('tools_platforms', []))}
- Keywords: {json.dumps(jd_json.get('keywords', [])[:15])}

ORIGINAL RESUME:
- Current headline: {resume_json.get('headline', '')}
- Current summary: {json.dumps(resume_json.get('summary', resume_json.get('summary_bullets', [])))}
- Current skills: {json.dumps(resume_json.get('skills', []))}

INSTRUCTIONS:
1. Headline: Brief, impactful, relevant to the job role
2. Summary: 3-4 bullets highlighting relevant experience (use JD keywords naturally)
3. Skills: Organize into 3-5 CATEGORIES. Put JD-relevant skills first in each category.
   Common categories: "Strategy & Marketing", "Data & Analytics", "Tools & Platforms", "Technical Skills", "Leadership & Soft Skills"

OUTPUT:
{{
  "headline": "",
  "summary": ["...", "...", "..."],
  "skills": [
    {{"category": "Strategy & Marketing", "skills": ["Digital Marketing", "Campaign Management", "..."]}},
    {{"category": "Data & Analytics", "skills": ["Google Analytics", "SQL", "..."]}},
    {{"category": "Tools & Platforms", "skills": ["Salesforce", "HubSpot", "..."]}},
    {{"category": "Technical Skills", "skills": ["Python", "SQL", "..."]}},
    {{"category": "Leadership", "skills": ["Team Management", "Cross-functional Collaboration", "..."]}}
  ]
}}
""".strip()


def prompt_tailor_role(
    jd_json: dict,
    role: dict,
    role_index: int,
    total_roles: int,
    responsibilities_to_cover: list,
    used_responsibilities: list
) -> str:
    """
    Tailor a single role's bullets to match JD responsibilities.
    
    Args:
        jd_json: Job description data
        role: Single role from resume
        role_index: 0 = most recent role, 1 = second, etc.
        total_roles: Total number of roles
        responsibilities_to_cover: JD responsibilities this role should address
        used_responsibilities: Responsibilities already covered by previous roles
    """
    
    # Determine bullet count based on role position
    if role_index == 0:
        bullet_count = "5-7"
        priority = "TOP PRIORITY"
        focus = "Cover the MOST important JD responsibilities. First bullet MUST address the #1 responsibility."
    elif role_index == 1:
        bullet_count = "5-6"
        priority = "HIGH PRIORITY"
        focus = "Cover the next most important JD responsibilities not yet addressed."
    else:
        bullet_count = "4-5"
        priority = "SUPPORTING"
        focus = "Cover remaining JD responsibilities and demonstrate depth of experience."
    
    return f"""
{_json_only()}

Rewrite the bullets for this role to match the job description.

=== FIXED (DO NOT CHANGE) ===
Company: {role.get('company', '')}
Title: {role.get('title', '')}
Dates: {role.get('dates', '')}

=== JOB REQUIREMENTS ===
Role applying for: {jd_json.get('role_title', '')} at {jd_json.get('company', '')}
Responsibilities to cover in this role: {json.dumps(responsibilities_to_cover)}
Keywords to include: {json.dumps(jd_json.get('keywords', [])[:10])}

=== ORIGINAL BULLETS ===
{json.dumps([b.get('text', b) if isinstance(b, dict) else b for b in role.get('bullets', [])], indent=2)}

=== INSTRUCTIONS ({priority}) ===
- Write {bullet_count} bullets
- {focus}
- Use original bullet metrics/outcomes when possible
- If you invent content not in original bullets, flag it for revision
- Write naturally - don't copy JD sentences verbatim
- Include JD keywords where they fit naturally

=== OUTCOME RULES ===
- 2-4 bullets should have outcomes (metrics, %, $, numbers)
- At least 1 bullet should have NO outcome (describes responsibility)
- Prefer using metrics from original bullets
- If inventing a metric, mark needs_revision=true

OUTPUT:
{{
  "company": "{role.get('company', '')}",
  "title": "[can adjust slightly to match JD role]",
  "dates": "{role.get('dates', '')}",
  "bullets": [
    {{
      "text": "Bullet text here",
      "source_bullet_ids": [],
      "needs_revision": false,
      "revision_note": null
    }}
  ],
  "responsibilities_covered": ["which JD responsibilities this role addresses"]
}}

NOTE: source_bullet_ids should be empty array [] for new bullets, or contain the original bullet ID if adapting an existing bullet.
""".strip()


def prompt_final_review(tailored_resume: dict, jd_json: dict) -> str:
    """Final review to identify gaps and generate questions."""
    return f"""
{_json_only()}

Review this tailored resume against the job description.

JOB RESPONSIBILITIES:
{json.dumps(jd_json.get('responsibilities', []))}

TAILORED RESUME:
{json.dumps(tailored_resume, indent=2)}

Identify:
1. gaps_to_confirm: JD requirements not adequately covered
2. questions_for_user: Clarifications needed about candidate's experience
3. change_log: Summary of major changes made

OUTPUT:
{{
  "gaps_to_confirm": ["..."],
  "questions_for_user": ["..."],
  "change_log": ["..."]
}}
""".strip()


# =============================================================================
# LEGACY PROMPTS (for backward compatibility)
# =============================================================================

def prompt_match(jd, resume) -> str:
    """Match JD requirements to resume bullets."""
    return f"""
{_json_only()}

Match JD requirements to resume bullets.

JOB: {jd.model_dump_json()}
RESUME: {resume.model_dump_json()}

OUTPUT:
{{
  "match_map":[{{"jd_requirement":"","matched_bullet_ids":["..."],"strength":"strong|medium|weak|missing"}}],
  "priority_keywords":["..."],
  "gaps":["..."]
}}
""".strip()


def prompt_tailor(jd, resume, match) -> str:
    """Legacy single-call tailor prompt (deprecated - use modular approach)."""
    return f"""
{_json_only()}

Tailor the resume for this job. Keep company names and dates EXACTLY as in original.

JOB: {jd.model_dump_json()}
RESUME: {resume.model_dump_json()}

OUTPUT:
{{
  "tailored_headline": "",
  "tailored_summary": ["..."],
  "tailored_skills": ["..."],
  "tailored_roles": [
    {{
      "company": "[EXACT from resume]",
      "title": "",
      "dates": "[EXACT from resume]",
      "bullets": [{{"text":"", "source_bullet_ids":[], "needs_revision": false, "revision_note": null}}]
    }}
  ],
  "change_log": [],
  "questions_for_user": [],
  "gaps_to_confirm": []
}}
""".strip()
