import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_services():
    creds = None
    token_path = "token.json"
    creds_path = "credentials.json"  # downloaded from Google Cloud

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return docs, drive

def copy_template(drive, template_doc_id: str, new_title: str) -> str:
    copied = drive.files().copy(
        fileId=template_doc_id,
        body={"name": new_title}
    ).execute()
    return copied["id"]

def replace_placeholders(docs, doc_id: str, replacements: dict):
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
    # Summary bullets as lines (we’ll convert to actual bullets in the next step)
    summary_lines = "\n".join([f"- {s}" for s in data.get("tailored_summary", [])])

    skills_line = ", ".join(data.get("tailored_skills", []))

    # Experience block
    exp_parts = []
    for r in data.get("tailored_roles", []):
        header = f'{r.get("title","")} — {r.get("company","")} ({r.get("dates","")})'
        exp_parts.append(header)
        for b in r.get("bullets", []):
            exp_parts.append(f"- {b.get('text','')}")
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
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


def main():
    TEMPLATE_DOC_ID = "1eIP5OWCnFlK-BGu9lq6-5MGiUvrLelc7pFSxSoq0Xio"

    data = load_json("outputs/tailored_resume.json")
    docs, drive = get_services()

    new_doc_id = copy_template(
        drive,
        template_doc_id=TEMPLATE_DOC_ID,
        new_title="Tailored Resume — Mistplay (UA Director)"
    )

    replacements = build_resume_blocks(data)
    replace_placeholders(docs, new_doc_id, replacements)

    # Turn "- " lines into real bullets
    convert_hyphen_lines_to_bullets(docs, new_doc_id)

    print("Created Google Doc with ID:", f'https://docs.google.com/document/d/{new_doc_id}')
    print("Open it in Google Drive and export to PDF if needed.")

if __name__ == "__main__":
    main()
