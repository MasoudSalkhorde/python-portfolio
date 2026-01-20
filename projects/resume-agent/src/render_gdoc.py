"""
Render tailored resume to Google Docs using template.

Template placeholders:
- {{NAME}}
- {{HEADLINE}}
- {{SUMMARY_BULLETS}}
- {{SKILLS_CATEGORY1}}: {{SKILLS1}} (up to 4 categories)
- {{JOB_TITLE1}}, {{DURATION1}}, {{COMPANY1}}, {{RESPONSIBILITIES1}} (up to 4 jobs)
- {{CERTIFICATIONS}}
- {{AWARDS & SCHOLARSHIPS}}
"""
import json
import os
from pathlib import Path
from typing import Dict

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger()

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


# =============================================================================
# AUTHENTICATION
# =============================================================================

def get_services():
    """Get Google Docs and Drive services."""
    creds = None
    token_path = Config.GOOGLE_TOKEN_PATH
    creds_path = Config.GOOGLE_CREDENTIALS_PATH

    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Google credentials file not found: {creds_path}\n"
            "Please download credentials.json from Google Cloud Console."
        )

    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load existing token: {e}")

    if not creds or not creds.valid:
        logger.info("Authenticating with Google...")
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        logger.info("Authentication successful")

    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return docs, drive


# =============================================================================
# TEMPLATE RENDERING
# =============================================================================

def copy_template(drive, template_doc_id: str, new_title: str) -> str:
    """Copy Google Doc template."""
    logger.info(f"Copying template: {template_doc_id}")
    copied = drive.files().copy(
        fileId=template_doc_id,
        body={"name": new_title}
    ).execute()
    return copied["id"]


def build_replacements(data: dict) -> Dict[str, str]:
    """
    Build placeholder replacements from tailored resume data.
    
    Uses numbered placeholders for skills and experience:
    - {{SKILLS_CATEGORY1}}, {{SKILLS1}}, etc.
    - {{JOB_TITLE1}}, {{COMPANY1}}, {{DURATION1}}, {{RESPONSIBILITIES1}}, etc.
    """
    replacements = {}
    
    # {{NAME}}
    replacements["{{NAME}}"] = data.get("name", "Your Name")
    
    # {{HEADLINE}}
    replacements["{{HEADLINE}}"] = data.get("tailored_headline", "")
    
    # {{SUMMARY_BULLETS}} - bullet points with •
    summary = data.get("tailored_summary", [])
    summary_lines = []
    for bullet in summary:
        summary_lines.append(f"• {bullet}")
    replacements["{{SUMMARY_BULLETS}}"] = "\n".join(summary_lines)
    
    # ========================================
    # SKILLS - numbered placeholders (1-4)
    # ========================================
    skills = data.get("tailored_skills", [])
    
    for i in range(1, 5):  # Support up to 4 skill categories
        if i <= len(skills):
            skill_cat = skills[i - 1]
            if isinstance(skill_cat, dict):
                category_name = skill_cat.get("category", "")
                category_skills = skill_cat.get("skills", [])
                replacements[f"{{{{SKILLS_CATEGORY{i}}}}}"] = category_name
                replacements[f"{{{{SKILLS{i}}}}}"] = ", ".join(category_skills)
            else:
                # Flat skill
                replacements[f"{{{{SKILLS_CATEGORY{i}}}}}"] = "Skills"
                replacements[f"{{{{SKILLS{i}}}}}"] = str(skill_cat)
        else:
            # No skill at this position - clear placeholder
            replacements[f"{{{{SKILLS_CATEGORY{i}}}}}"] = ""
            replacements[f"{{{{SKILLS{i}}}}}"] = ""
    
    # ========================================
    # EXPERIENCE - numbered placeholders (1-4)
    # ========================================
    roles = data.get("tailored_roles", [])
    
    for i in range(1, 5):  # Support up to 4 jobs
        if i <= len(roles):
            role = roles[i - 1]
            company = role.get("company", "")
            title = role.get("title", "")
            dates = role.get("dates", "")
            
            replacements[f"{{{{JOB_TITLE{i}}}}}"] = title
            replacements[f"{{{{COMPANY{i}}}}}"] = company
            replacements[f"{{{{DURATION{i}}}}}"] = dates
            
            # Build responsibilities (bullets)
            bullets = role.get("bullets", [])
            resp_lines = []
            for b in bullets:
                bullet_text = b.get("text", b) if isinstance(b, dict) else str(b)
                needs_revision = b.get("needs_revision", False) if isinstance(b, dict) else False
                
                if needs_revision:
                    bullet_text = f"{bullet_text} [NEEDS REVIEW]"
                
                resp_lines.append(f"• {bullet_text}")
            
            replacements[f"{{{{RESPONSIBILITIES{i}}}}}"] = "\n".join(resp_lines)
        else:
            # No role at this position - clear placeholders
            replacements[f"{{{{JOB_TITLE{i}}}}}"] = ""
            replacements[f"{{{{COMPANY{i}}}}}"] = ""
            replacements[f"{{{{DURATION{i}}}}}"] = ""
            replacements[f"{{{{RESPONSIBILITIES{i}}}}}"] = ""
    
    # {{CERTIFICATIONS}}
    certs = data.get("certifications", [])
    replacements["{{CERTIFICATIONS}}"] = "\n".join(certs)
    
    # {{AWARDS & SCHOLARSHIPS}}
    awards = data.get("awards", [])
    replacements["{{AWARDS & SCHOLARSHIPS}}"] = "\n".join(awards)
    
    return replacements


def replace_placeholders(docs, doc_id: str, replacements: Dict[str, str]):
    """Replace all placeholders in the document."""
    requests = []
    
    for placeholder, value in replacements.items():
        requests.append({
            "replaceAllText": {
                "containsText": {"text": placeholder, "matchCase": True},
                "replaceText": value
            }
        })
    
    logger.info(f"Replacing {len(requests)} placeholders...")
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def load_json(path: str) -> dict:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_to_gdoc(data: dict, title: str = "Tailored Resume") -> str:
    """
    Render tailored resume to Google Docs using template.
    
    Args:
        data: Tailored resume data (dict or TailoredResumeJSON)
        title: Document title
    
    Returns:
        Document URL
    """
    docs, drive = get_services()
    
    # Convert Pydantic model to dict if needed
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    
    # Copy template
    template_id = Config.GOOGLE_TEMPLATE_DOC_ID
    if not template_id:
        raise ValueError("GOOGLE_TEMPLATE_DOC_ID not configured. Set it in .env file.")
    
    doc_id = copy_template(drive, template_id, title)
    
    # Build and apply replacements
    replacements = build_replacements(data)
    replace_placeholders(docs, doc_id, replacements)
    
    doc_url = f"https://docs.google.com/document/d/{doc_id}"
    logger.info(f"✅ Created: {doc_url}")
    
    return doc_url


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = str(Config.OUTPUT_DIR / "tailored_resume.json")
    
    if len(sys.argv) > 2:
        doc_title = sys.argv[2]
    else:
        doc_title = "Tailored Resume"
    
    logger.info(f"Loading: {json_path}")
    data = load_json(json_path)
    
    doc_url = render_to_gdoc(data, doc_title)
    
    print(f"\n✅ Created Google Doc: {doc_url}")
    
    # Check for revisions
    revision_count = sum(
        1 for r in data.get("tailored_roles", [])
        for b in r.get("bullets", [])
        if isinstance(b, dict) and b.get("needs_revision", False)
    )
    if revision_count > 0:
        print(f"\n⚠️  {revision_count} bullet(s) flagged for revision")


if __name__ == "__main__":
    main()
