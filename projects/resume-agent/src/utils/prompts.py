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
    """Tailor headline and summary to match JD. Skills are handled separately."""
    
    # Extract tools/platforms for bullet 4
    tools = jd_json.get('tools_platforms', [])
    tools_str = ", ".join(tools[:10]) if tools else "relevant tools and platforms"
    
    return f"""
{_json_only()}

Create a tailored headline and summary for this resume to match the job.
NOTE: Skills will be handled in a separate step - include empty skills array.

JOB:
- Company: {jd_json.get('company', '')}
- Role: {jd_json.get('role_title', '')}
- Key responsibilities: {json.dumps(jd_json.get('responsibilities', []))}
- Tools/Platforms: {json.dumps(tools)}
- Keywords: {json.dumps(jd_json.get('keywords', [])[:15])}

ORIGINAL RESUME:
- Current headline: {resume_json.get('headline', '')}

INSTRUCTIONS:

1. HEADLINE: Brief, impactful, relevant to the job role title

2. SUMMARY: Create 4-5 bullet points following this EXACT structure:

   BULLET 1 (Introduction):
   "Experienced professional in [job-title-related-to-posting] with over 9 years of experience in B2B, B2C, Ecommerce, SaaS, and gaming industries."
   - Use a job title that matches the job posting (e.g., "Marketing Technology", "User Acquisition", "Growth Marketing")
   
   BULLET 2 (Key Responsibilities - Part 1):
   - Mix and match the 2-3 MOST IMPORTANT responsibilities from the job description
   - Paraphrase, do NOT copy verbatim
   - Make it sound like your experience, not a job requirement
   
   BULLET 3 (Key Responsibilities - Part 2):
   - Cover another 2-3 important responsibilities from the job description
   - Again, paraphrase and present as your experience
   
   BULLET 4 (Tools & Technologies):
   - Cover the most important tools, technologies, and platforms from the JD
   - Example: "Proficient in [Tool1], [Tool2], [Tool3], and [Tool4] for [purpose]."
   - Use tools from JD: {tools_str}
   
   BULLET 5 (Optional - Additional Coverage):
   - If there are more important JD responsibilities not covered, add a 5th bullet
   - Skip if bullets 2-3 already covered the main responsibilities

CRITICAL RULES:
- NEVER copy job description language verbatim
- Sound like a professional describing their experience, NOT a job posting
- Each bullet should be 1-2 sentences max
- Bullet 1 MUST follow the exact format given

OUTPUT:
{{
  "headline": "",
  "summary": [
    "Experienced professional in ... with over 9 years of experience in B2B, B2C, Ecommerce, SaaS, and gaming industries.",
    "...",
    "...",
    "Proficient in ... for ...",
    "..."
  ],
  "skills": []
}}
""".strip()


def prompt_tailor_skills(jd_json: dict, primary_skills: list = None, secondary_skills: list = None) -> str:
    """
    Dedicated prompt for comprehensive skills section tailoring.
    Creates skills based ONLY on the job description.
    
    Args:
        jd_json: Job description data
        primary_skills: Ignored (kept for backward compatibility)
        secondary_skills: Ignored (kept for backward compatibility)
    """
    # Extract all JD requirements for comprehensive matching
    jd_tools = jd_json.get('tools_platforms', [])
    jd_keywords = jd_json.get('keywords', [])
    jd_responsibilities = jd_json.get('responsibilities', [])
    jd_requirements = jd_json.get('requirements', [])
    
    # Build requirements list for display
    req_list = []
    for req in jd_requirements:
        if isinstance(req, dict):
            req_list.append(f"- {req.get('requirement', '')} ({req.get('type', 'must')})")
        else:
            req_list.append(f"- {req}")
    
    return f"""
{_json_only()}

You are an ATS optimization expert. Create a COMPREHENSIVE skills section based ENTIRELY on the job description.

=== JOB DESCRIPTION ===

COMPANY: {jd_json.get('company', '')}
ROLE: {jd_json.get('role_title', '')}

TOOLS & PLATFORMS MENTIONED:
{json.dumps(jd_tools, indent=2)}

KEYWORDS FROM JD:
{json.dumps(jd_keywords, indent=2)}

JOB REQUIREMENTS:
{chr(10).join(req_list) if req_list else "Not specified"}

KEY RESPONSIBILITIES:
{json.dumps(jd_responsibilities, indent=2)}

=== YOUR TASK ===

Extract ALL skills from the job description and organize them into categories.

RULES:
1. INCLUDE ALL REQUIRED SKILLS: Every tool, platform, and skill mentioned in the JD MUST be included
2. INCLUDE ALL IMPORTANT SKILLS: Skills implied by responsibilities should be included
3. USE EXACT JD TERMINOLOGY: If JD says "Google Analytics 4", use exactly that (not "GA4" or "Analytics")
4. PRIORITIZE ORDER: Within each category, put REQUIRED skills first, then NICE-TO-HAVE skills
5. COMPREHENSIVE COVERAGE: 4-6 categories, 5-10 skills per category

CATEGORIES TO USE (pick 4-6 that fit the JD):
- "Marketing & Strategy" (campaigns, growth, brand, positioning, etc.)
- "Data & Analytics" (GA4, SQL, BI tools, reporting, A/B testing, etc.)
- "Advertising Platforms" (Google Ads, Meta Ads, programmatic, DSPs, etc.)
- "MarTech & Tools" (CRM, CDPs, automation, tracking, tag management, etc.)
- "Technical Skills" (Python, SQL, APIs, scripting, etc.)
- "Leadership & Collaboration" (team management, stakeholder communication, etc.)

=== OUTPUT FORMAT ===
{{
  "skills": [
    {{"category": "Category Name", "skills": ["Required Skill 1", "Required Skill 2", "Important Skill 3", "..."]}},
    ...
  ],
  "ats_keywords_used": ["keyword1", "keyword2", "..."],
  "coverage_notes": "Brief note: X required skills covered, Y important skills covered"
}}

CRITICAL: Do NOT invent skills not in the JD. Extract ONLY what is mentioned or clearly implied.
Include ALL required skills and MOST important skills from the job description.
""".strip()


def prompt_tailor_role(
    jd_json: dict,
    role: dict,
    role_index: int,
    total_roles: int,
    responsibilities_to_cover: list,
    used_responsibilities: list,
    secondary_metrics: list = None
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
        secondary_metrics: Additional metrics from secondary resume to borrow from
    """
    
    # Determine bullet count and outcome requirements based on role position
    if role_index == 0:
        bullet_count = "6-7"
        exact_outcomes = 4
        priority = "TOP PRIORITY"
        focus = "Cover the MOST important JD responsibilities. First bullet MUST address the #1 responsibility."
        outcome_requirement = f"⚠️ MANDATORY: EXACTLY {exact_outcomes} bullets must have numerical outcomes. The remaining 2-3 bullets must be QUALITATIVE (no numbers)."
    elif role_index == 1:
        bullet_count = "5-6"
        exact_outcomes = 3
        priority = "HIGH PRIORITY"
        focus = "Cover the next most important JD responsibilities not yet addressed."
        outcome_requirement = f"⚠️ MANDATORY: EXACTLY {exact_outcomes} bullets must have numerical outcomes. The remaining 2-3 bullets must be QUALITATIVE (no numbers)."
    else:
        bullet_count = "4-5"
        exact_outcomes = 3
        priority = "SUPPORTING"
        focus = "Cover remaining JD responsibilities and demonstrate depth of experience."
        outcome_requirement = f"EXACTLY {exact_outcomes} bullets should have numerical outcomes. The remaining 1-2 bullets must be QUALITATIVE (no numbers)."
    
    return f"""
{_json_only()}

Rewrite the bullets for this role to match the job description.

╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  CRITICAL: EXACTLY {exact_outcomes} BULLETS WITH NUMERICAL OUTCOMES  ⚠️             ║
║  ⚠️  AND 2-3 BULLETS WITHOUT OUTCOMES (QUALITATIVE)  ⚠️                      ║
║                                                                              ║
║  NUMERICAL OUTCOME = contains %, $, or specific numbers                      ║
║  QUALITATIVE = describes skills/actions WITHOUT numbers                      ║
║                                                                              ║
║  ✅ NUMERICAL: "Improved ROAS by 35%", "Managed $2.5M budget"                ║
║  ✅ QUALITATIVE: "Partnered with product teams to align strategy"            ║
║                                                                              ║
║  DO NOT add numbers to every bullet. Mix is required.                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

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
- Write {bullet_count} bullets total
- {focus}
- {outcome_requirement}
- DO NOT put numerical outcomes in every bullet - you need a mix
- Use original bullet metrics/outcomes when possible
- If you invent content not in original bullets, flag it for revision

=== PARAPHRASING RULES ===
NEVER copy JD language verbatim. Paraphrase and rewrite.

=== HOW TO ADD NUMERICAL OUTCOMES ===
Priority order:
1. FIRST: Use outcomes from ORIGINAL BULLETS (preserve exact numbers)
2. SECOND: Adapt an outcome from a different original bullet if relevant
3. THIRD: Use metrics from SECONDARY RESUME below (if available)
4. FOURTH: INVENT a reasonable outcome if needed (set needs_revision=true)

{f"=== ADDITIONAL METRICS FROM SECONDARY RESUME ===" + chr(10) + "You can borrow/adapt these metrics for your bullets:" + chr(10) + json.dumps(secondary_metrics[:10], indent=2) if secondary_metrics else ""}

IMPORTANT: Only {exact_outcomes} bullets should have numerical outcomes. The rest must be qualitative.

=== OUTPUT FORMAT ===
Return {bullet_count} bullets. EXACTLY {exact_outcomes} with numerical outcomes, and 2-3 QUALITATIVE (no numbers).

EXAMPLE OUTPUT (showing exactly 4 numerical + 2 qualitative):
{{
  "company": "{role.get('company', '')}",
  "title": "User Acquisition Manager",
  "dates": "{role.get('dates', '')}",
  "bullets": [
    {{"text": "Scaled paid acquisition to $3.2M annual spend across Meta, Google, and TikTok, achieving 145% ROAS", "source_bullet_ids": [], "needs_revision": false, "revision_note": null}},
    {{"text": "Reduced CPI by 28% through creative testing and audience optimization strategies", "source_bullet_ids": [], "needs_revision": false, "revision_note": null}},
    {{"text": "Built analytics dashboards tracking 15+ KPIs, enabling data-driven budget reallocation", "source_bullet_ids": [], "needs_revision": false, "revision_note": null}},
    {{"text": "Led cross-functional team of 4 to launch campaigns across multiple channels", "source_bullet_ids": [], "needs_revision": false, "revision_note": null}},
    {{"text": "Developed incrementality testing framework to measure true channel contribution", "source_bullet_ids": [], "needs_revision": false, "revision_note": null}},
    {{"text": "Partnered with product and creative teams to align UA strategy with retention goals", "source_bullet_ids": [], "needs_revision": false, "revision_note": null}}
  ],
  "responsibilities_covered": ["UA strategy", "Budget management", "Analytics", "Team leadership"]
}}

VERIFY YOUR OUTPUT: Count bullets with numbers (%, $, digits). Should be EXACTLY {exact_outcomes}. Bullets 5-6 are qualitative (no numbers).
""".strip()


def prompt_tailor_role_low_match(
    jd_json: dict,
    role: dict,
    role_index: int,
    total_roles: int,
    responsibilities_to_cover: list,
    used_responsibilities: list,
    secondary_metrics: list = None
) -> str:
    """
    Tailor a role when the JD is significantly different from available resumes.
    
    In this mode:
    - Keep company name, title (can adjust slightly), and dates from the resume
    - Write ALL responsibilities based on the JD (not the original resume bullets)
    - Flag ALL bullets as needing revision since they're essentially invented
    """
    
    # Determine bullet count based on role position
    if role_index == 0:
        bullet_count = "6-7"
        exact_outcomes = 4
        priority = "TOP PRIORITY"
        focus = "Cover the MOST important JD responsibilities comprehensively."
    elif role_index == 1:
        bullet_count = "5-6"
        exact_outcomes = 3
        priority = "HIGH PRIORITY"
        focus = "Cover the next most important JD responsibilities."
    else:
        bullet_count = "4-5"
        exact_outcomes = 3
        priority = "SUPPORTING"
        focus = "Cover remaining JD responsibilities."
    
    return f"""
{_json_only()}

⚠️ LOW MATCH MODE: The job description is significantly different from the candidate's actual resume.
Write responsibilities based ENTIRELY on the JD, using the candidate's work history as a template.

=== FIXED (DO NOT CHANGE) ===
Company: {role.get('company', '')}
Dates: {role.get('dates', '')}

=== CAN ADJUST ===
Original Title: {role.get('title', '')}
→ You MAY adjust the title to better fit the JD role (but keep it realistic for the company)

=== JOB DESCRIPTION (PRIMARY SOURCE) ===
Target Role: {jd_json.get('role_title', '')} at {jd_json.get('company', '')}

Responsibilities to cover:
{json.dumps(responsibilities_to_cover, indent=2)}

Key Tools/Platforms mentioned in JD: {json.dumps(jd_json.get('tools_platforms', jd_json.get('networks_tools', [])))}
Key Metrics/KPIs mentioned in JD: {json.dumps(jd_json.get('metrics_kpis', jd_json.get('metrics', [])))}
Important Keywords: {json.dumps(jd_json.get('keywords', [])[:15])}

=== ORIGINAL BULLETS (FOR REFERENCE ONLY - may not be relevant) ===
{json.dumps([b.get('text', b) if isinstance(b, dict) else b for b in role.get('bullets', [])], indent=2)}

=== INSTRUCTIONS ({priority}) ===
1. Write {bullet_count} bullets based on the JD responsibilities
2. {focus}
3. EXACTLY {exact_outcomes} bullets must have numerical outcomes (realistic estimates)
4. The remaining bullets should be qualitative
5. Use the JD's terminology, tools, and context
6. Make bullets sound authentic for someone working at {role.get('company', 'this company')}
7. ALL bullets must have needs_revision=true since content is invented

=== OUTCOME GUIDELINES ===
Since you're inventing content, use realistic ranges for outcomes:
- Percentages: 15-40% improvements
- Budgets: $100K-$5M depending on company size
- Team sizes: 2-10 people
- Project counts: 5-50 depending on scope

{f"=== ADDITIONAL METRICS FROM SECONDARY RESUME ===" + chr(10) + "You can borrow/adapt these metrics for your bullets:" + chr(10) + json.dumps(secondary_metrics[:10], indent=2) if secondary_metrics else ""}

=== OUTPUT FORMAT ===
{{
  "company": "{role.get('company', '')}",
  "title": "[adjusted title that fits JD better]",
  "dates": "{role.get('dates', '')}",
  "bullets": [
    {{
      "text": "Bullet based on JD responsibility...",
      "source_bullet_ids": [],
      "needs_revision": true,
      "revision_note": "Content created based on JD - please verify/adjust"
    }}
  ],
  "responsibilities_covered": ["which JD responsibilities this role addresses"]
}}

IMPORTANT: Every bullet MUST have needs_revision=true in this mode.
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


def prompt_score_resume(tailored_resume: dict, jd_json: dict) -> str:
    """
    Generate prompt for scoring the tailored resume against the job description.
    Simulates a Talent Acquisition Manager evaluation.
    """
    # Build a text representation of the tailored resume
    resume_text_parts = []
    resume_text_parts.append(f"HEADLINE: {tailored_resume.get('tailored_headline', '')}")
    resume_text_parts.append(f"SUMMARY: {' | '.join(tailored_resume.get('tailored_summary', []))}")
    
    # Handle skills (could be list of strings or list of dicts)
    skills = tailored_resume.get('tailored_skills', [])
    if skills and isinstance(skills[0], dict):
        skills_text = []
        for s in skills:
            cat = s.get('category', '')
            skill_list = s.get('skills', [])
            skills_text.append(f"{cat}: {', '.join(skill_list)}")
        resume_text_parts.append(f"SKILLS: {' | '.join(skills_text)}")
    else:
        resume_text_parts.append(f"SKILLS: {', '.join(skills)}")
    
    for role in tailored_resume.get('tailored_roles', []):
        resume_text_parts.append(f"\n{role.get('title', '')} at {role.get('company', '')} ({role.get('dates', '')})")
        for bullet in role.get('bullets', []):
            text = bullet.get('text', '') if isinstance(bullet, dict) else bullet
            resume_text_parts.append(f"  • {text}")
    
    resume_text = "\n".join(resume_text_parts)
    
    # Handle responsibilities (could be list of strings or list of dicts)
    responsibilities = jd_json.get('responsibilities', [])
    if responsibilities and isinstance(responsibilities[0], dict):
        resp_list = [r.get('text', str(r)) for r in responsibilities]
    else:
        resp_list = responsibilities
    
    return f"""
{_json_only()}

You are a TALENT ACQUISITION MANAGER reviewing a resume for a job opening.

=== JOB DESCRIPTION ===
Company: {jd_json.get('company', '')}
Role: {jd_json.get('role_title', '')}
Level: {jd_json.get('level', '')}

Key Responsibilities:
{json.dumps(resp_list, indent=2)}

Required Tools/Platforms: {json.dumps(jd_json.get('tools_platforms', jd_json.get('networks_tools', [])))}
Key Metrics Expected: {json.dumps(jd_json.get('metrics_kpis', jd_json.get('metrics', [])))}

=== CANDIDATE'S RESUME ===
{resume_text}

=== YOUR TASK ===
As a Talent Acquisition Manager, evaluate this candidate's chances of being selected for an interview.

1. Give a SCORE out of 100 representing the likelihood of getting selected for an interview
2. Explain your scoring rationale briefly
3. List the specific GAPS - what's missing or weak that prevents this from being a 100/100
4. Provide actionable RECOMMENDATIONS to improve the score

Be realistic and critical. Consider:
- How well do their skills match the requirements?
- Do they have relevant experience with the required tools/platforms?
- Are their achievements/metrics impressive for this level?
- Are there any red flags or missing must-have requirements?

OUTPUT:
{{
  "score": 85,
  "score_rationale": "Brief explanation of why this score...",
  "gaps": [
    "Gap 1: Missing X experience...",
    "Gap 2: No mention of Y tool...",
    "Gap 3: Weak Z qualification..."
  ],
  "recommendations": [
    "Add more detail about...",
    "Highlight experience with...",
    "Consider mentioning..."
  ]
}}
""".strip()


def prompt_final_score_resume(
    tailored_resume: dict,
    jd_json: dict,
    initial_gaps: list,
    gaps_addressed: list
) -> str:
    """
    Generate prompt for RE-scoring the resume AFTER gap coverage bullets were added.
    This is a fresh evaluation that should recognize the improvements.
    """
    # Build a text representation of the tailored resume
    resume_text_parts = []
    resume_text_parts.append(f"HEADLINE: {tailored_resume.get('tailored_headline', '')}")
    resume_text_parts.append(f"SUMMARY: {' | '.join(tailored_resume.get('tailored_summary', []))}")
    
    # Handle skills
    skills = tailored_resume.get('tailored_skills', [])
    if skills and isinstance(skills[0], dict):
        skills_text = []
        for s in skills:
            cat = s.get('category', '')
            skill_list = s.get('skills', [])
            skills_text.append(f"{cat}: {', '.join(skill_list)}")
        resume_text_parts.append(f"SKILLS: {' | '.join(skills_text)}")
    else:
        resume_text_parts.append(f"SKILLS: {', '.join(skills)}")
    
    for role in tailored_resume.get('tailored_roles', []):
        resume_text_parts.append(f"\n{role.get('title', '')} at {role.get('company', '')} ({role.get('dates', '')})")
        for bullet in role.get('bullets', []):
            text = bullet.get('text', '') if isinstance(bullet, dict) else bullet
            # Highlight the newly added bullets
            if "(added to cover gaps)" in text:
                resume_text_parts.append(f"  • [NEW] {text}")
            else:
                resume_text_parts.append(f"  • {text}")
    
    resume_text = "\n".join(resume_text_parts)
    
    # Handle responsibilities
    responsibilities = jd_json.get('responsibilities', [])
    if responsibilities and isinstance(responsibilities[0], dict):
        resp_list = [r.get('text', str(r)) for r in responsibilities]
    else:
        resp_list = responsibilities
    
    return f"""
{_json_only()}

You are a TALENT ACQUISITION MANAGER RE-EVALUATING a resume AFTER improvements were made.

=== IMPORTANT CONTEXT ===
This resume was previously scored and had gaps identified.
NEW bullet points marked with [NEW] and "(added to cover gaps)" were added to address those gaps.
You MUST evaluate whether these additions have improved the candidate's fit.

=== INITIAL GAPS THAT WERE IDENTIFIED ===
{json.dumps(initial_gaps, indent=2)}

=== GAPS THAT WERE ADDRESSED (new bullets added) ===
{json.dumps(gaps_addressed, indent=2)}

=== JOB DESCRIPTION ===
Company: {jd_json.get('company', '')}
Role: {jd_json.get('role_title', '')}
Level: {jd_json.get('level', '')}

Key Responsibilities:
{json.dumps(resp_list, indent=2)}

Required Tools/Platforms: {json.dumps(jd_json.get('tools_platforms', jd_json.get('networks_tools', [])))}
Key Metrics Expected: {json.dumps(jd_json.get('metrics_kpis', jd_json.get('metrics', [])))}

=== UPDATED CANDIDATE'S RESUME (with [NEW] bullets marked) ===
{resume_text}

=== YOUR TASK ===
RE-EVALUATE this candidate after the improvements. The score SHOULD be higher if the gaps were properly addressed.

1. Give a NEW SCORE out of 100 - this should reflect the improvements made
2. Explain how the new bullets addressed (or failed to address) the initial gaps
3. List any REMAINING gaps that still exist
4. Provide final recommendations

If the gaps were addressed with relevant bullet points, the score MUST improve.

OUTPUT:
{{
  "score": 92,
  "score_rationale": "Improved from initial score because...",
  "gaps": [
    "Remaining gap 1 (if any)...",
    "Remaining gap 2 (if any)..."
  ],
  "recommendations": [
    "Final recommendation 1...",
    "Final recommendation 2..."
  ]
}}
""".strip()


def prompt_cover_gaps(
    tailored_resume: dict,
    score_result: dict,
    jd_json: dict
) -> str:
    """
    Generate prompt to add bullet points that cover identified gaps.
    
    The LLM should:
    - Keep ALL existing content unchanged
    - Add new bullet points marked with "(added to cover gaps)" in bold
    - Can use/modify existing bullets as inspiration but must add as NEW bullets
    """
    
    # Build current resume state for context
    roles_summary = []
    for i, role in enumerate(tailored_resume.get('tailored_roles', [])):
        bullets = role.get('bullets', [])
        bullet_texts = [b.get('text', b) if isinstance(b, dict) else b for b in bullets]
        roles_summary.append({
            "index": i,
            "company": role.get('company', ''),
            "title": role.get('title', ''),
            "dates": role.get('dates', ''),
            "current_bullet_count": len(bullets),
            "current_bullets": bullet_texts
        })
    
    gaps = score_result.get('gaps', [])
    recommendations = score_result.get('recommendations', [])
    score = score_result.get('score', 0)
    
    return f"""
{_json_only()}

You are improving a tailored resume by adding bullet points to cover identified gaps.

=== CURRENT SCORE ===
Interview Selection Score: {score}/100

=== GAPS TO COVER ===
{json.dumps(gaps, indent=2)}

=== RECOMMENDATIONS ===
{json.dumps(recommendations, indent=2)}

=== JOB DESCRIPTION CONTEXT ===
Company: {jd_json.get('company', '')}
Role: {jd_json.get('role_title', '')}
Key Requirements: {json.dumps(jd_json.get('responsibilities', [])[:5])}
Tools/Platforms: {json.dumps(jd_json.get('tools_platforms', jd_json.get('networks_tools', [])))}

=== CURRENT ROLES IN RESUME ===
{json.dumps(roles_summary, indent=2)}

=== YOUR TASK ===
Add NEW bullet points to cover the gaps. For each gap, create a bullet point that addresses it.

CRITICAL RULES:
1. DO NOT remove or modify any existing bullets
2. ONLY ADD new bullet points
3. Each new bullet MUST end with: **(added to cover gaps)**
4. You can use existing bullets as INSPIRATION, but add as a NEW bullet with the marker
5. Add bullets to the most relevant role (usually first or second role)
6. New bullets should have numerical outcomes where possible (%, $, numbers)
7. Mark needs_revision=true for invented content

For each role, return:
- All EXISTING bullets unchanged
- Plus any NEW bullets with "(added to cover gaps)" marker

OUTPUT FORMAT:
{{
  "roles_with_additions": [
    {{
      "role_index": 0,
      "company": "Company Name",
      "title": "Job Title",
      "dates": "Date Range",
      "bullets": [
        {{"text": "EXISTING bullet 1 (keep unchanged)", "is_new": false, "needs_revision": false, "revision_note": null}},
        {{"text": "EXISTING bullet 2 (keep unchanged)", "is_new": false, "needs_revision": false, "revision_note": null}},
        {{"text": "NEW bullet addressing gap X **(added to cover gaps)**", "is_new": true, "needs_revision": true, "revision_note": "Added to cover gap about X"}}
      ]
    }}
  ],
  "gaps_addressed": ["Gap 1", "Gap 2"],
  "gaps_not_addressable": ["Gap that cannot be reasonably added"]
}}

IMPORTANT:
- Keep existing bullets EXACTLY as they are (copy them verbatim)
- Only add new bullets where they make sense for the role
- The "(added to cover gaps)" marker must be in bold: **(added to cover gaps)**
- If a gap cannot be reasonably addressed without fabricating too much, list it in gaps_not_addressable
""".strip()
