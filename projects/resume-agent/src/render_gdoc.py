"""
Render tailored resume to Google Docs.

Two modes:
1. Template mode (default): Copy a template and replace placeholders
2. Build mode: Create document structure from scratch

Set GOOGLE_TEMPLATE_DOC_ID in .env for template mode.
Leave it empty or set to "BUILD" to build from scratch.
"""
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

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
# DOCUMENT BUILDING (FROM SCRATCH)
# =============================================================================

def create_blank_document(docs, title: str) -> str:
    """Create a new blank Google Doc."""
    doc = docs.documents().create(body={"title": title}).execute()
    return doc.get("documentId")


def build_document_requests(data: dict) -> List[Dict[str, Any]]:
    """
    Build Google Docs API requests to create resume structure.
    
    Structure:
    - Name (large, bold, centered)
    - Contact info (centered)
    - Headline (centered)
    - SUMMARY section
    - SKILLS section  
    - EXPERIENCE section (with roles and bullets)
    - EDUCATION section
    """
    requests = []
    
    # We build content from bottom to top (inserting at index 1)
    # because Google Docs insertText shifts indices
    
    # Collect all content first, then reverse
    content_parts = []
    
    # === HEADER ===
    name = data.get("name", "Your Name")
    email = data.get("email", "")
    location = data.get("location", "")
    headline = data.get("tailored_headline", "")
    
    # Name
    content_parts.append({
        "text": f"{name}\n",
        "style": "HEADING_1",
        "center": True,
        "bold": True
    })
    
    # Contact line
    contact_parts = []
    if location:
        contact_parts.append(location)
    if email:
        contact_parts.append(email)
    if contact_parts:
        content_parts.append({
            "text": " | ".join(contact_parts) + "\n",
            "style": "NORMAL_TEXT",
            "center": True,
            "fontSize": 10
        })
    
    # Headline
    if headline:
        content_parts.append({
            "text": f"{headline}\n\n",
            "style": "NORMAL_TEXT",
            "center": True,
            "bold": True,
            "fontSize": 11
        })
    
    # === SUMMARY ===
    summary_bullets = data.get("tailored_summary", [])
    if summary_bullets:
        content_parts.append({
            "text": "SUMMARY\n",
            "style": "HEADING_2",
            "bold": True,
            "underline": True
        })
        for bullet in summary_bullets:
            content_parts.append({
                "text": f"• {bullet}\n",
                "style": "NORMAL_TEXT",
                "indent": True
            })
        content_parts.append({"text": "\n", "style": "NORMAL_TEXT"})
    
    # === SKILLS ===
    skills = data.get("tailored_skills", [])
    if skills:
        content_parts.append({
            "text": "SKILLS\n",
            "style": "HEADING_2",
            "bold": True,
            "underline": True
        })
        
        # Check if skills are categorized (list of dicts with category/skills)
        if skills and isinstance(skills[0], dict) and "category" in skills[0]:
            # Categorized skills
            for cat in skills:
                category_name = cat.get("category", "")
                category_skills = cat.get("skills", [])
                if category_name and category_skills:
                    skills_line = ", ".join(category_skills)
                    content_parts.append({
                        "text": f"{category_name}: ",
                        "style": "NORMAL_TEXT",
                        "bold": True
                    })
                    content_parts.append({
                        "text": f"{skills_line}\n",
                        "style": "NORMAL_TEXT"
                    })
        else:
            # Flat list of skills (backward compatibility)
            skills_text = ", ".join(skills) if isinstance(skills[0], str) else str(skills)
            content_parts.append({
                "text": f"{skills_text}\n",
                "style": "NORMAL_TEXT"
            })
        
        content_parts.append({"text": "\n", "style": "NORMAL_TEXT"})
    
    # === EXPERIENCE ===
    roles = data.get("tailored_roles", [])
    if roles:
        content_parts.append({
            "text": "EXPERIENCE\n",
            "style": "HEADING_2",
            "bold": True,
            "underline": True
        })
        
        for role in roles:
            company = role.get("company", "")
            title = role.get("title", "")
            dates = role.get("dates", "")
            
            # Role header: Title — Company (Dates)
            role_header = f"{title}"
            if company:
                role_header += f" — {company}"
            if dates:
                role_header += f" ({dates})"
            
            content_parts.append({
                "text": f"{role_header}\n",
                "style": "NORMAL_TEXT",
                "bold": True
            })
            
            # Bullets
            bullets = role.get("bullets", [])
            for b in bullets:
                bullet_text = b.get("text", b) if isinstance(b, dict) else b
                needs_revision = b.get("needs_revision", False) if isinstance(b, dict) else False
                
                if needs_revision:
                    revision_note = b.get("revision_note", "") if isinstance(b, dict) else ""
                    bullet_text = f"{bullet_text} [NEEDS REVIEW: {revision_note}]"
                
                content_parts.append({
                    "text": f"• {bullet_text}\n",
                    "style": "NORMAL_TEXT",
                    "indent": True
                })
            
            content_parts.append({"text": "\n", "style": "NORMAL_TEXT"})
    
    # === EDUCATION ===
    education = data.get("education", [])
    if education:
        content_parts.append({
            "text": "EDUCATION\n",
            "style": "HEADING_2",
            "bold": True,
            "underline": True
        })
        for edu in education:
            if isinstance(edu, dict):
                edu_text = edu.get("degree", "")
                if edu.get("institution"):
                    edu_text += f", {edu['institution']}"
                if edu.get("year"):
                    edu_text += f" ({edu['year']})"
            else:
                edu_text = str(edu)
            content_parts.append({
                "text": f"• {edu_text}\n",
                "style": "NORMAL_TEXT",
                "indent": True
            })
    
    # === CERTIFICATIONS ===
    certs = data.get("certifications", [])
    if certs:
        content_parts.append({
            "text": "\nCERTIFICATIONS\n",
            "style": "HEADING_2",
            "bold": True,
            "underline": True
        })
        for cert in certs:
            content_parts.append({
                "text": f"• {cert}\n",
                "style": "NORMAL_TEXT",
                "indent": True
            })
    
    # Now build the actual requests
    # Insert all text first at index 1
    full_text = ""
    text_ranges = []  # Track where each part starts/ends for formatting
    
    for part in content_parts:
        start_idx = len(full_text) + 1  # +1 because doc starts at index 1
        full_text += part["text"]
        end_idx = len(full_text) + 1
        text_ranges.append({
            "start": start_idx,
            "end": end_idx,
            **part
        })
    
    # Insert all text at once
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": full_text
        }
    })
    
    # Apply formatting
    for tr in text_ranges:
        start = tr["start"]
        end = tr["end"]
        
        # Paragraph style
        if tr.get("style") == "HEADING_1":
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_1",
                        "alignment": "CENTER" if tr.get("center") else "START"
                    },
                    "fields": "namedStyleType,alignment"
                }
            })
        elif tr.get("style") == "HEADING_2":
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_2"
                    },
                    "fields": "namedStyleType"
                }
            })
        
        # Text formatting
        text_style = {}
        fields = []
        
        if tr.get("bold"):
            text_style["bold"] = True
            fields.append("bold")
        
        if tr.get("underline"):
            text_style["underline"] = True
            fields.append("underline")
        
        if tr.get("fontSize"):
            text_style["fontSize"] = {"magnitude": tr["fontSize"], "unit": "PT"}
            fields.append("fontSize")
        
        if fields:
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": start, "endIndex": end - 1},  # -1 to exclude newline
                    "textStyle": text_style,
                    "fields": ",".join(fields)
                }
            })
        
        # Center alignment
        if tr.get("center") and tr.get("style") != "HEADING_1":
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": {"alignment": "CENTER"},
                    "fields": "alignment"
                }
            })
        
        # Indent for bullets
        if tr.get("indent"):
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": start, "endIndex": end},
                    "paragraphStyle": {
                        "indentFirstLine": {"magnitude": 18, "unit": "PT"},
                        "indentStart": {"magnitude": 18, "unit": "PT"}
                    },
                    "fields": "indentFirstLine,indentStart"
                }
            })
    
    return requests


def build_resume_from_scratch(docs, data: dict, title: str) -> str:
    """Build a resume document from scratch."""
    logger.info("Creating new document...")
    doc_id = create_blank_document(docs, title)
    
    logger.info("Building document structure...")
    requests = build_document_requests(data)
    
    if requests:
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    
    logger.info("Document built successfully")
    return doc_id


# =============================================================================
# TEMPLATE MODE (LEGACY)
# =============================================================================

def load_json(path: str) -> dict:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def copy_template(drive, template_doc_id: str, new_title: str) -> str:
    """Copy Google Doc template."""
    copied = drive.files().copy(
        fileId=template_doc_id,
        body={"name": new_title}
    ).execute()
    return copied["id"]


def replace_placeholders(docs, doc_id: str, replacements: dict):
    """Replace placeholders in document."""
    requests = []
    for key, value in replacements.items():
        requests.append({
            "replaceAllText": {
                "containsText": {"text": key, "matchCase": True},
                "replaceText": value
            }
        })
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


def build_resume_blocks(data: dict) -> dict:
    """Build replacement blocks for template mode."""
    summary_lines = "\n".join([f"- {s}" for s in data.get("tailored_summary", [])])
    
    # Handle categorized skills
    skills = data.get("tailored_skills", [])
    if skills and isinstance(skills[0], dict) and "category" in skills[0]:
        # Categorized skills
        skill_lines = []
        for cat in skills:
            category_name = cat.get("category", "")
            category_skills = cat.get("skills", [])
            if category_name and category_skills:
                skill_lines.append(f"{category_name}: {', '.join(category_skills)}")
        skills_line = "\n".join(skill_lines)
    else:
        # Flat list
        skills_line = ", ".join(skills) if skills else ""

    exp_parts = []
    for r in data.get("tailored_roles", []):
        header = f'{r.get("title","")} — {r.get("company","")} ({r.get("dates","")})'
        exp_parts.append(header)
        for b in r.get("bullets", []):
            text = b.get('text', '') if isinstance(b, dict) else b
            needs_revision = b.get('needs_revision', False) if isinstance(b, dict) else False
            if needs_revision:
                revision_note = b.get('revision_note', '') if isinstance(b, dict) else ''
                text = f"{text} [REVISION NEEDED: {revision_note}]"
            exp_parts.append(f"- {text}")
        exp_parts.append("")
    experience_block = "\n".join(exp_parts).strip()

    return {
        "{{NAME}}": data.get("name", "Your Name"),
        "{{HEADLINE}}": data.get("tailored_headline", ""),
        "{{SUMMARY_BULLETS}}": summary_lines,
        "{{SKILLS}}": skills_line,
        "{{EXPERIENCE}}": experience_block,
    }


def convert_hyphen_lines_to_bullets(docs, doc_id: str):
    """Convert '- ' lines to real bullets."""
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])

    targets = []
    for elem in content:
        para = elem.get("paragraph")
        if not para:
            continue
        start = elem.get("startIndex")
        end = elem.get("endIndex")
        if start is None or end is None:
            continue
        text_runs = para.get("elements", [])
        text = "".join(tr.get("textRun", {}).get("content", "") for tr in text_runs).strip()
        if text.startswith("- "):
            targets.append((start, end))

    targets.sort(key=lambda x: x[0], reverse=True)

    requests = []
    for start, end in targets:
        requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start, "endIndex": end},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })
        requests.append({
            "deleteContentRange": {
                "range": {"startIndex": start, "endIndex": start + 2}
            }
        })

    if requests:
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


def build_with_template(docs, drive, data: dict, template_id: str, title: str) -> str:
    """Build resume using template mode."""
    logger.info(f"Copying template: {template_id}")
    doc_id = copy_template(drive, template_id, title)
    
    logger.info("Replacing placeholders...")
    replacements = build_resume_blocks(data)
    replace_placeholders(docs, doc_id, replacements)
    
    logger.info("Converting to bullets...")
    convert_hyphen_lines_to_bullets(docs, doc_id)
    
    return doc_id


# =============================================================================
# MAIN
# =============================================================================

def render_to_gdoc(data: dict, title: str = "Tailored Resume", use_template: bool = None) -> str:
    """
    Render tailored resume to Google Docs.
    
    Args:
        data: Tailored resume data (dict or TailoredResumeJSON)
        title: Document title
        use_template: Force template mode (True) or build mode (False). 
                      If None, auto-detect based on config.
    
    Returns:
        Document URL
    """
    docs, drive = get_services()
    
    # Convert Pydantic model to dict if needed
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    
    # Determine mode
    template_id = Config.GOOGLE_TEMPLATE_DOC_ID
    
    if use_template is None:
        use_template = bool(template_id and template_id != "BUILD")
    
    if use_template and template_id and template_id != "BUILD":
        logger.info("Using template mode")
        doc_id = build_with_template(docs, drive, data, template_id, title)
    else:
        logger.info("Building document from scratch")
        doc_id = build_resume_from_scratch(docs, data, title)
    
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
