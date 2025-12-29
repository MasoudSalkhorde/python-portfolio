import json

def _json_only_rule() -> str:
    return (
        "Return ONLY valid JSON. No markdown. No commentary. "
        "If information is missing, use empty strings/lists, never invent."
    )

def prompt_extract_jd(jd_text: str) -> str:
    return f"""
{_json_only_rule()}

You are extracting a mobile app UA leadership job description into structured JSON.
Include responsibilities, requirements (must/nice), networks/tools, and key metrics.

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
- Do not infer people management if not stated.

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

Tailor the resume for this job.
Rules:
1) NEVER invent facts, titles, tools, budgets, employers, dates, education, certifications, or people-management scope.
2) Every tailored bullet MUST include source_bullet_ids that exist in RESUME JSON.
3) Optimize for ATS + Director/Head of UA language: strategy, governance, experimentation, P&L, forecasting, exec reporting, partner management.
4) Emphasize: multi-million budgets, ROAS/LTV modeling, channel expansion, dashboards/analytics, cross-functional work.
5) If a JD need is missing, do NOT add it; put it into questions_for_user.

JOB JSON:
{jd.model_dump_json()}

RESUME JSON:
{resume.model_dump_json()}

MATCH JSON:
{match.model_dump_json()}

Output JSON schema:
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
  "questions_for_user":["..."]
}}
""".strip()
