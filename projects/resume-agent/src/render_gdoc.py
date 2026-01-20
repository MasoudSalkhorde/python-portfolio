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
    
    # {{GAPS}} - Score and gap analysis from Talent Acquisition Manager evaluation
    gaps_block = ""
    score_data = data.get("score", {})
    if score_data:
        score_value = score_data.get("score", "N/A")
        score_rationale = score_data.get("score_rationale", "")
        gaps = score_data.get("gaps", [])
        recommendations = score_data.get("recommendations", [])
        
        gaps_parts = []
        gaps_parts.append(f"Interview Selection Score: {score_value}/100")
        gaps_parts.append(f"{score_rationale}")
        gaps_parts.append("")
        
        if gaps:
            gaps_parts.append("Gaps to reach 100/100:")
            for gap in gaps:
                gaps_parts.append(f"• {gap}")
            gaps_parts.append("")
        
        if recommendations:
            gaps_parts.append("Recommendations:")
            for rec in recommendations:
                gaps_parts.append(f"• {rec}")
        
        gaps_block = "\n".join(gaps_parts)
    
    # Also include gap coverage results if available
    gap_coverage = data.get("gap_coverage", {})
    if gap_coverage:
        gaps_addressed = gap_coverage.get("gaps_addressed", [])
        gaps_not_addressable = gap_coverage.get("gaps_not_addressable", [])
        
        coverage_parts = []
        if gaps_addressed:
            coverage_parts.append("")
            coverage_parts.append("Gaps Addressed (bullet points added):")
            for gap in gaps_addressed:
                coverage_parts.append(f"✅ {gap}")
        
        if gaps_not_addressable:
            coverage_parts.append("")
            coverage_parts.append("Gaps Not Addressable:")
            for gap in gaps_not_addressable:
                coverage_parts.append(f"⚠️ {gap}")
        
        if coverage_parts:
            gaps_block += "\n" + "\n".join(coverage_parts)
    
    replacements["{{GAPS}}"] = gaps_block
    
    # {{GAPS1}} - Final score after gap coverage (re-evaluation of the final resume)
    gaps1_block = ""
    final_score_data = data.get("final_score", {})
    if final_score_data:
        final_score_value = final_score_data.get("score", "N/A")
        final_score_rationale = final_score_data.get("score_rationale", "")
        final_gaps = final_score_data.get("gaps", [])
        final_recommendations = final_score_data.get("recommendations", [])
        
        # Calculate improvement if initial score exists
        initial_score = score_data.get("score", 0) if score_data else 0
        improvement = final_score_value - initial_score if isinstance(final_score_value, int) else 0
        
        gaps1_parts = []
        gaps1_parts.append(f"Final Interview Selection Score: {final_score_value}/100")
        if improvement > 0:
            gaps1_parts.append(f"(+{improvement} points improvement)")
        gaps1_parts.append(f"{final_score_rationale}")
        gaps1_parts.append("")
        
        if final_gaps:
            gaps1_parts.append("Remaining Gaps:")
            for gap in final_gaps:
                gaps1_parts.append(f"• {gap}")
            gaps1_parts.append("")
        
        if final_recommendations:
            gaps1_parts.append("Final Recommendations:")
            for rec in final_recommendations:
                gaps1_parts.append(f"• {rec}")
        
        gaps1_block = "\n".join(gaps1_parts)
    
    replacements["{{GAPS1}}"] = gaps1_block
    
    return replacements


def replace_placeholders(docs, doc_id: str, replacements: Dict[str, str]):
    """Replace all placeholders in the document (except certifications which need special handling)."""
    requests = []
    
    for placeholder, value in replacements.items():
        # Skip certifications - handled separately with hyperlinks
        if placeholder == "{{CERTIFICATIONS}}":
            continue
            
        requests.append({
            "replaceAllText": {
                "containsText": {"text": placeholder, "matchCase": True},
                "replaceText": value
            }
        })
    
    logger.info(f"Replacing {len(requests)} placeholders...")
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


def parse_certifications(certifications: list) -> list:
    """
    Parse certifications into (name, url) pairs.
    
    Supports formats:
    - "Name, https://url.com"
    - "Name\\nhttps://url.com"
    - ["Name", "https://url.com"]
    """
    cert_pairs = []
    i = 0
    while i < len(certifications):
        cert = certifications[i]
        
        # Check if format is "Name, https://url"
        if ", http" in cert:
            parts = cert.split(", http", 1)
            name = parts[0].strip()
            url = "http" + parts[1].strip() if len(parts) > 1 else None
            cert_pairs.append((name, url))
            i += 1
        # Check if this cert contains a newline (name + url in one string)
        elif "\n" in cert:
            parts = cert.split("\n")
            name = parts[0].strip()
            url = parts[1].strip() if len(parts) > 1 and parts[1].startswith("http") else None
            cert_pairs.append((name, url))
            i += 1
        # Check if next item is a URL
        elif i + 1 < len(certifications) and certifications[i + 1].startswith("http"):
            cert_pairs.append((cert, certifications[i + 1]))
            i += 2
        else:
            # Just a name, no URL
            cert_pairs.append((cert, None))
            i += 1
    
    return cert_pairs


def insert_certifications_with_links(docs, doc_id: str, certifications: list):
    """
    Replace {{CERTIFICATIONS}} placeholder with certification names (preserving formatting),
    then add hyperlinks to each certification.
    """
    if not certifications:
        # Just remove the placeholder
        requests = [{
            "replaceAllText": {
                "containsText": {"text": "{{CERTIFICATIONS}}", "matchCase": True},
                "replaceText": ""
            }
        }]
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
        return
    
    # Parse certifications
    cert_pairs = parse_certifications(certifications)
    
    # Build certification text (just names, newline separated)
    cert_text = "\n".join(name for name, url in cert_pairs)
    
    # Step 1: Replace placeholder with certification names (this preserves formatting!)
    requests = [{
        "replaceAllText": {
            "containsText": {"text": "{{CERTIFICATIONS}}", "matchCase": True},
            "replaceText": cert_text
        }
    }]
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    
    # Step 2: Find the inserted text and add hyperlinks
    # Re-fetch document to get updated indices
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])
    
    # Find each certification name and add hyperlink
    link_requests = []
    
    for name, url in cert_pairs:
        if not url:
            continue
        
        # Search for this certification name in the document
        for elem in content:
            para = elem.get("paragraph")
            if not para:
                continue
            
            for text_elem in para.get("elements", []):
                text_run = text_elem.get("textRun")
                if not text_run:
                    continue
                
                text_content = text_run.get("content", "")
                if name in text_content:
                    # Found it! Calculate the exact position
                    elem_start = text_elem.get("startIndex", 0)
                    name_offset = text_content.find(name)
                    
                    link_start = elem_start + name_offset
                    link_end = link_start + len(name)
                    
                    # Add hyperlink
                    link_requests.append({
                        "updateTextStyle": {
                            "range": {
                                "startIndex": link_start,
                                "endIndex": link_end
                            },
                            "textStyle": {
                                "link": {"url": url}
                            },
                            "fields": "link"
                        }
                    })
                    # Set color to black (separate request to override link color)
                    link_requests.append({
                        "updateTextStyle": {
                            "range": {
                                "startIndex": link_start,
                                "endIndex": link_end
                            },
                            "textStyle": {
                                "foregroundColor": {
                                    "color": {
                                        "rgbColor": {
                                            "red": 0.0,
                                            "green": 0.0,
                                            "blue": 0.0
                                        }
                                    }
                                }
                            },
                            "fields": "foregroundColor"
                        }
                    })
                    break
    
    # Apply hyperlinks
    if link_requests:
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": link_requests}).execute()
        logger.info(f"Added {len(link_requests)} certification hyperlinks")


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def load_json(path: str) -> dict:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_markers_bold(docs, doc_id: str):
    """
    Find all [NEEDS REVIEW] and (added to cover gaps) markers and make them bold.
    """
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])
    
    # Markers to make bold
    markers = ["[NEEDS REVIEW]", "(added to cover gaps)"]
    bold_requests = []
    
    for elem in content:
        para = elem.get("paragraph")
        if not para:
            continue
        
        for text_elem in para.get("elements", []):
            text_run = text_elem.get("textRun")
            if not text_run:
                continue
            
            text_content = text_run.get("content", "")
            
            for marker in markers:
                if marker in text_content:
                    elem_start = text_elem.get("startIndex", 0)
                    marker_offset = text_content.find(marker)
                    
                    marker_start = elem_start + marker_offset
                    marker_end = marker_start + len(marker)
                    
                    bold_requests.append({
                        "updateTextStyle": {
                            "range": {
                                "startIndex": marker_start,
                                "endIndex": marker_end
                            },
                            "textStyle": {
                                "bold": True
                            },
                            "fields": "bold"
                        }
                    })
    
    if bold_requests:
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": bold_requests}).execute()
        logger.info(f"Made {len(bold_requests)} markers bold")


def generate_doc_title(data: dict, company_name: str = None) -> str:
    """
    Generate document title in format: company_mason_sal
    
    Args:
        data: Resume data (to get candidate name)
        company_name: Company name from job description
    
    Returns:
        Formatted title
    """
    # Get candidate name and format it
    name = data.get("name", "candidate")
    # Convert "Mason Sal" -> "mason_sal"
    name_formatted = name.lower().replace(" ", "_").replace(".", "")
    
    # Get company name and format it
    if company_name:
        company_formatted = company_name.lower().replace(" ", "_").replace(".", "")
    else:
        company_formatted = "company"
    
    return f"{company_formatted}_{name_formatted}"


def render_to_gdoc(data: dict, title: str = None, company_name: str = None) -> str:
    """
    Render tailored resume to Google Docs using template.
    
    Args:
        data: Tailored resume data (dict or TailoredResumeJSON)
        title: Document title (if None, auto-generates as company_name)
        company_name: Company name for auto-generated title
    
    Returns:
        Document URL
    """
    docs, drive = get_services()
    
    # Convert Pydantic model to dict if needed
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    
    # Generate title if not provided
    if title is None:
        title = generate_doc_title(data, company_name)
    
    # Copy template
    template_id = Config.GOOGLE_TEMPLATE_DOC_ID
    if not template_id:
        raise ValueError("GOOGLE_TEMPLATE_DOC_ID not configured. Set it in .env file.")
    
    doc_id = copy_template(drive, template_id, title)
    
    # Build and apply replacements (excluding certifications)
    replacements = build_replacements(data)
    replace_placeholders(docs, doc_id, replacements)
    
    # Handle certifications separately (with hyperlinks)
    certifications = data.get("certifications", [])
    insert_certifications_with_links(docs, doc_id, certifications)
    
    # Make [NEEDS REVIEW] markers bold
    format_markers_bold(docs, doc_id)
    
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
    
    # Optional: company name for title (arg 2) or explicit title (arg 2)
    company_name = None
    doc_title = None
    
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
        # If it looks like a company name (no spaces or underscores pattern), use as company
        # Otherwise use as explicit title
        if "_" in arg2 or " " not in arg2:
            company_name = arg2.replace("_", " ")
        else:
            doc_title = arg2
    
    logger.info(f"Loading: {json_path}")
    data = load_json(json_path)
    
    # Try to get company name from the JSON if not provided
    if company_name is None and doc_title is None:
        # Check if there's job info in the data
        company_name = data.get("target_company", None)
    
    doc_url = render_to_gdoc(data, title=doc_title, company_name=company_name)
    
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
