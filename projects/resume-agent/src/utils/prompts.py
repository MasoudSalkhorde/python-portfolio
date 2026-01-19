import json

def _json_only_rule() -> str:
    return (
        "Return ONLY valid JSON. No markdown. No commentary. "
        "If information is missing, use empty strings/lists, never invent."
    )

def prompt_extract_jd(jd_text: str) -> str:
    return f"""
{_json_only_rule()}

You are extracting a job description into structured JSON.
Extract: responsibilities (in order of importance), requirements (must/nice), tools/platforms, and key metrics.

JD TEXT:
{jd_text}

Output JSON schema:
{{
  "company": "",
  "role_title": "",
  "level": "",
  "location": "",
  "responsibilities": ["..."],
  "requirements": [{{"requirement":"", "type":"must|nice", "category":"", "keywords":["..."]}}],
  "networks_tools": ["..."],
  "metrics": ["..."],
  "priority_keywords": ["..."]
}}
""".strip()

def prompt_extract_resume(resume_text: str) -> str:
    return f"""
{_json_only_rule()}

Extract this resume into structured JSON.
- Create bullet IDs in format "<companykey>_<n>" e.g. "aylo_1".
- Preserve ALL metrics exactly (e.g., "$10M+/y", "CPI -30%", "LTV +45%").
- Keep company names EXACTLY as they appear.

RESUME TEXT:
{resume_text}

Output JSON schema:
{{
  "name": "",
  "location": "",
  "email": "",
  "headline": "",
  "summary_bullets": ["..."],
  "skills": ["..."],
  "roles": [
    {{
      "company": "",
      "title": "",
      "dates": "",
      "location": "",
      "bullets": [{{"id":"", "text":"", "evidence_tags":["..."]}}]
    }}
  ],
  "education": ["..."],
  "certifications": ["..."],
  "awards": ["..."]
}}
""".strip()

def prompt_match(jd, resume) -> str:
    return f"""
{_json_only_rule()}

Match JD requirements to resume bullets. For each JD requirement, find matching resume bullets.

JOB JSON:
{jd.model_dump_json()}

RESUME JSON:
{resume.model_dump_json()}

Output JSON schema:
{{
  "match_map":[{{"jd_requirement":"","matched_bullet_ids":["..."],"strength":"strong|medium|weak|missing","notes":""}}],
  "priority_keywords":["..."],
  "gaps":["..."]
}}
""".strip()

def prompt_tailor(jd, resume, match) -> str:
    return f"""
{_json_only_rule()}

You are tailoring the resume to match the job description. 

=== ABSOLUTE RULES (NEVER VIOLATE) ===
1. Company names: Use EXACT names from RESUME JSON. NEVER change, add to, or modify company names.
2. Dates: Keep EXACT dates from RESUME JSON.
3. Metrics: Keep EXACT numbers from RESUME JSON (never invent metrics).
4. Number of roles: Keep the SAME number of roles as in RESUME JSON.

=== GOAL ===
Rewrite the resume bullets to align with the job description responsibilities, while keeping company names and dates unchanged.

=== STRUCTURE ===
FIRST ROLE (most recent): 5-7 bullets covering the top 4-5 JD responsibilities
- First bullet: Must address the #1 JD responsibility with an outcome
- Second bullet: Must address another top JD responsibility with an outcome
- Mix/match JD responsibilities into bullets for coverage

SECOND ROLE: 5-6 bullets covering the next important JD responsibilities

OTHER ROLES: 5 bullets each, covering remaining JD responsibilities

=== OUTCOME RULES ===
- 2-4 bullets per role should have outcomes (metrics, percentages, numbers)
- At least 1 bullet per role should have NO outcome (describes responsibility only)
- Use outcomes from the original RESUME JSON when possible
- If you invent an outcome, set needs_revision=true with a note explaining what was invented

=== WRITING STYLE ===
- Write naturally, like a real person describing their work
- Use JD keywords naturally (for ATS matching)
- Paraphrase JD language - don't copy exact sentences
- Vary action verbs and sentence structures

=== INPUTS ===
JOB JSON:
{jd.model_dump_json()}

RESUME JSON:
{resume.model_dump_json()}

MATCH JSON:
{match.model_dump_json()}

=== OUTPUT (Must match exactly) ===
{{
  "tailored_headline": "[Role-aligned headline]",
  "tailored_summary": ["...", "..."],
  "tailored_skills": ["...", "..."],
  "tailored_roles": [
    {{
      "company": "[EXACT company name from RESUME JSON - DO NOT MODIFY]",
      "title": "[Can adjust slightly to match JD role]",
      "dates": "[EXACT dates from RESUME JSON]",
      "bullets": [
        {{
          "text": "[Tailored bullet text]",
          "source_bullet_ids": ["original_bullet_id"],
          "needs_revision": false,
          "revision_note": null
        }}
      ]
    }}
  ],
  "change_log": ["..."],
  "questions_for_user": ["..."],
  "gaps_to_confirm": ["..."]
}}

CRITICAL: The company field must be the EXACT string from RESUME JSON. Copy it exactly - no additions, no modifications, no parenthetical notes.
""".strip()
