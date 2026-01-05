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
Include responsibilities, requirements (must/nice), all of the networks/tools/technical skills sorted by importance, and all of the key metrics sorted by importance.

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
  "networks_tools": ["Meta", "Google App Campaigns", "TikTok", "AppLovin", "..."],
  "metrics": ["ROAS", "LTV", "CPI", "Retention", "..."]
}}
""".strip()

def prompt_extract_resume(resume_text: str) -> str:
    return f"""
{_json_only_rule()}

Extract this resume into structured JSON.
IMPORTANT:
- Create bullet IDs in format "<companykey>_<n>" e.g. "aylo_1".
- Preserve metrics exactly (e.g., "$10M+/y", "CPI -30%", "LTV +45%").

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
      "bullets": [{{"id":"", "text":"", "evidence_tags":["budget","testing","roas","dashboards","partners","leadership"]}}]
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

You are matching a Job Description to a Resume.
For each JD requirement:
- list best matching resume bullet IDs (can be empty)
- set strength: strong/medium/weak/missing
- add notes if needed
Also output: priority_keywords and gaps.

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

You are tailoring the resume for this job by REWRITING WORK EXPERIENCE BULLETS.
Your goal is to maximize alignment with the job description:

HARD RULES:titles
1) NEVER invent budgets, employers, dates, education, certifications.
2) You MAY rephrase, merge, split, and reorder bullets.
3) You MAY create a NEW bullet. In that case try to anchor it to the metrics/outcomes already present in the resume bullets if it makes sense.
4) Preserve metrics exactly as they appear in RESUME JSON (do not change numbers, currency, %).
5) You can modify the role titles a little bit to align with the JD

PRIMARY OBJECTIVE:
- Ensure the tailored bullets collectively cover ALL key responsibilities + qualifications in the job description as much as possible.

PRIORITY EMPHASIS (CRITICAL):
A) For the FIRST TWO ROLES in RESUME JSON (most recent two roles):
   - Rewrite 5–6 bullets per role.
   - These bullets must be explicitly designed to cover the FIRST 4–5 responsibilities in the JD responsibilities list
   - METHOD:
     - First try to "mix and match" each of those JD responsibilities with the closest existing resume bullets.
     - If not possible, still write a bullet aligned to the JD responsibility, and try to anchor it with the KPIs/metrics/outcomes/tools from the most relevant resume bullets.
     - If not supportable, claim it; but this piece of text at the end of it to let the user know that you added a new bullet and make it bold : <<new bullet>>
     - In all of the scnarios above, parahrase the JD and try not to use the exact language in the JD except for the profossional words or jargons related to the role 

B) For ALL REMAINING ROLES (3rd role and earlier):
   - Rewrite 5 bullets per role.
   - Use ALL JD responsibilities + qualifications and pick the best matches.
   - Rewrite bullets to include JD language + resume outcomes/metrics/tools. 
   - In all of the scnarios above, parahrase the JD and try not to use the exact language in the JD except for the profossional words or jargons related to the role 


STYLE:
- Director/Head of UA language: strategy, governance, experimentation, forecasting, performance measurement, partner management, executive reporting.
- 1–2 lines max per bullet; impact-first; metric-forward.
- Use UA vocabulary: ROAS, LTV, CPI, cohorts, creative testing, channel exploration, dashboards, attribution.
- Avoid vague filler like "responsible for" or "helped".

INPUTS:
JOB JSON:
{jd.model_dump_json()}

RESUME JSON:
{resume.model_dump_json()}

MATCH JSON:
{match.model_dump_json()}

OUTPUT JSON schema (MUST MATCH EXACTLY):
{{
  "tailored_headline":"",
  "tailored_summary":["..."],
  "tailored_skills":["..."],
  "tailored_roles":[
    {{
      "company":"",
      "title":"",
      "dates":"",
      "bullets":[{{"text":"", "source_bullet_ids":["..."]}}]
    }}
  ],
  "change_log":["..."],
  "questions_for_user":["..."],
  "gaps_to_confirm":["..."]
}}
""".strip()
