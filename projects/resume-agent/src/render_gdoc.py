import json
import os
import logging
from pathlib import Path

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

def load_json(path: str) -> dict:
    """Load JSON file with error handling."""
    json_path = Path(path)
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    
    logger.debug(f"Loading JSON from: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file: {e}")
        raise ValueError(f"Invalid JSON file: {path}") from e

def get_services():
    """Get Google Docs and Drive services with error handling."""
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
        try:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
            logger.info("Authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    try:
        docs = build("docs", "v1", credentials=creds)
        drive = build("drive", "v3", credentials=creds)
        return docs, drive
    except Exception as e:
        logger.error(f"Failed to build Google services: {e}")
        raise

def copy_template(drive, template_doc_id: str, new_title: str) -> str:
    """Copy Google Doc template with error handling."""
    try:
        logger.debug(f"Copying template document: {template_doc_id}")
        copied = drive.files().copy(
            fileId=template_doc_id,
            body={"name": new_title}
        ).execute()
        new_doc_id = copied["id"]
        logger.info(f"Created new document: {new_doc_id}")
        return new_doc_id
    except HttpError as e:
        logger.error(f"Failed to copy template: {e}")
        raise ValueError(f"Failed to copy Google Doc template: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error copying template: {e}")
        raise

def replace_placeholders(docs, doc_id: str, replacements: dict):
    """Replace placeholders in Google Doc with error handling."""
    try:
        requests = []
        for key, value in replacements.items():
            requests.append({
                "replaceAllText": {
                    "containsText": {"text": key, "matchCase": True},
                    "replaceText": value
                }
            })
        logger.debug(f"Replacing {len(requests)} placeholders")
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
        logger.info("Placeholders replaced successfully")
    except HttpError as e:
        logger.error(f"Failed to replace placeholders: {e}")
        raise ValueError(f"Failed to update Google Doc: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error replacing placeholders: {e}")
        raise

def build_resume_blocks(data: dict) -> dict:
    # Summary bullets as lines (we’ll convert to actual bullets in the next step)
    summary_lines = "\n".join([f"- {s}" for s in data.get("tailored_summary", [])])

    skills_line = ", ".join(data.get("tailored_skills", []))

    # Experience block
    exp_parts = []
    for r in data.get("tailored_roles", []):
        header = f'{r.get("title","")} — {r.get("company","")} ({r.get("dates","")})'
        exp_parts.append(header)
        for b in r.get("bullets", []):
            text = b.get('text', '')
            needs_revision = b.get('needs_revision', False)
            revision_note = b.get('revision_note', '')
            
            if needs_revision:
                # Add revision indicator
                text = f"{text} [REVISION NEEDED: {revision_note}]"
            exp_parts.append(f"- {text}")
        exp_parts.append("")  # blank line between roles
    experience_block = "\n".join(exp_parts).strip()

    # If you stored name/contact in the JSON, use those. Otherwise, set manually.
    return {
        "{{NAME}}": "Masoud Salkhorde",  # TODO: fill from resume JSON ideally
        "{{HEADLINE}}": data.get("tailored_headline", ""),
        "{{SUMMARY_BULLETS}}": summary_lines,
        "{{SKILLS}}": skills_line,
        "{{EXPERIENCE}}": experience_block,
    }

def convert_hyphen_lines_to_bullets(docs, doc_id: str):
    """
    Converts paragraphs that start with '- ' into real bulleted list items.
    IMPORTANT: We process from bottom-to-top so index shifts from deletions
    do not break subsequent requests.
    """
    try:
        logger.debug("Converting hyphen lines to bullets")
        doc = docs.documents().get(documentId=doc_id).execute()
        content = doc.get("body", {}).get("content", [])

        targets = []

        # Collect target paragraphs with their indices
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

        # Process from end -> start to avoid index shift issues
        targets.sort(key=lambda x: x[0], reverse=True)

        requests = []
        for start, end in targets:
            # 1) Turn paragraph into bullets first (using original range)
            requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": start, "endIndex": end},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
                }
            })
            # 2) Remove "- " prefix (first 2 chars of the paragraph)
            requests.append({
                "deleteContentRange": {
                    "range": {"startIndex": start, "endIndex": start + 2}
                }
            })

        if requests:
            logger.debug(f"Converting {len(requests) // 2} lines to bullets")
            docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
            logger.info("Bullet conversion completed")
    except HttpError as e:
        logger.error(f"Failed to convert bullets: {e}")
        raise ValueError(f"Failed to format Google Doc: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error converting bullets: {e}")
        raise


def main():
    """Main function to render tailored resume to Google Doc."""
    import sys
    
    # Get template ID from config or command line
    template_doc_id = Config.GOOGLE_TEMPLATE_DOC_ID
    
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    else:
        json_path = str(Config.OUTPUT_DIR / "tailored_resume.json")
    
    if len(sys.argv) > 2:
        doc_title = sys.argv[2]
    else:
        doc_title = "Tailored Resume"
    
    try:
        logger.info(f"Loading tailored resume from: {json_path}")
        data = load_json(json_path)
        
        logger.info("Connecting to Google Docs...")
        docs, drive = get_services()

        logger.info(f"Copying template document: {template_doc_id}")
        new_doc_id = copy_template(
            drive,
            template_doc_id=template_doc_id,
            new_title=doc_title
        )

        logger.info("Building resume content...")
        replacements = build_resume_blocks(data)
        replace_placeholders(docs, new_doc_id, replacements)

        logger.info("Converting to bullet points...")
        convert_hyphen_lines_to_bullets(docs, new_doc_id)

        doc_url = f'https://docs.google.com/document/d/{new_doc_id}'
        logger.info(f"✅ Created Google Doc: {doc_url}")
        print(f"\n✅ Created Google Doc: {doc_url}")
        print("Open it in Google Drive and export to PDF if needed.")
        
        # Check for revision notes
        revision_count = sum(
            1 for r in data.get("tailored_roles", [])
            for b in r.get("bullets", [])
            if b.get("needs_revision", False)
        )
        if revision_count > 0:
            print(f"\n⚠️  {revision_count} bullet(s) flagged for revision - see notes in document")
        
    except Exception as e:
        logger.error(f"Failed to render Google Doc: {e}")
        raise

if __name__ == "__main__":
    main()
