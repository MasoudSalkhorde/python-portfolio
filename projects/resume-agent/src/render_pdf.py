"""PDF rendering utilities for tailored resumes."""
import json
import logging
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.colors import red, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from src.utils.config import Config

logger = logging.getLogger(__name__)


def load_tailored_json(path: str) -> dict:
    """
    Load tailored resume JSON.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Dictionary with tailored resume data
    """
    json_path = Path(path)
    if not json_path.exists():
        raise FileNotFoundError(f"Tailored resume JSON not found: {path}")
    
    logger.debug(f"Loading tailored resume from: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def bullets(items, style):
    """Create a bulleted list from items."""
    return ListFlowable(
        [ListItem(Paragraph(i, style), leftIndent=14) for i in items],
        bulletType="bullet",
        leftIndent=18,
    )


def role_bullets(role: dict, bullet_style: ParagraphStyle, revision_style: ParagraphStyle):
    """
    Create bullet list for a role, highlighting bullets that need revision.
    
    Args:
        role: Role dictionary with bullets
        bullet_style: Style for normal bullets
        revision_style: Style for bullets needing revision
    """
    items = []
    for b in role.get("bullets", []):
        text = b.get("text", "")
        needs_revision = b.get("needs_revision", False)
        revision_note = b.get("revision_note", "")
        
        if needs_revision:
            # Add revision indicator
            text_with_note = f"{text} <b><i>[REVISION NEEDED: {revision_note}]</i></b>"
            items.append(Paragraph(text_with_note, revision_style))
        else:
            items.append(Paragraph(text, bullet_style))
    
    return ListFlowable(
        items,
        bulletType="bullet",
        leftIndent=18,
    )


def render_pdf(tailored_json_path: str, output_pdf_path: str, include_notes: bool = True):
    """
    Render tailored resume to PDF.
    
    Args:
        tailored_json_path: Path to tailored resume JSON
        output_pdf_path: Output PDF path
        include_notes: Whether to include internal notes section
    """
    logger.info(f"Rendering PDF from {tailored_json_path} to {output_pdf_path}")
    
    data = load_tailored_json(tailored_json_path)

    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, spaceAfter=8)
    h = ParagraphStyle("H", parent=styles["Heading2"], spaceBefore=10, spaceAfter=4)
    subh = ParagraphStyle("SubH", parent=styles["Heading3"], spaceBefore=6, spaceAfter=2)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10, leading=12)
    bullet_style = ParagraphStyle("Bullet", parent=body, leftIndent=0)
    revision_style = ParagraphStyle("Revision", parent=bullet_style, textColor=red)

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title="Tailored Resume",
        author="Resume Agent",
    )

    story = []

    # Header
    story.append(Paragraph(data.get("tailored_headline", "Resume"), title))
    story.append(Spacer(1, 8))

    # Summary
    story.append(Paragraph("SUMMARY", h))
    story.append(bullets(data.get("tailored_summary", []), bullet_style))
    story.append(Spacer(1, 8))

    # Skills
    story.append(Paragraph("SKILLS", h))
    skills = data.get("tailored_skills", [])
    
    # Handle categorized skills
    if skills and isinstance(skills[0], dict) and "category" in skills[0]:
        # Categorized skills
        for cat in skills:
            category_name = cat.get("category", "")
            category_skills = cat.get("skills", [])
            if category_name and category_skills:
                skills_line = f"<b>{category_name}:</b> {', '.join(category_skills)}"
                story.append(Paragraph(skills_line, body))
    else:
        # Flat list
        skills_line = ", ".join(skills) if skills else ""
        story.append(Paragraph(skills_line, body))
    
    story.append(Spacer(1, 10))

    # Experience
    story.append(Paragraph("EXPERIENCE", h))
    revision_count = 0
    for r in data.get("tailored_roles", []):
        role_line = f'{r.get("title","")} — {r.get("company","")} ({r.get("dates","")})'
        story.append(Paragraph(role_line, subh))
        
        # Count revisions in this role
        role_revisions = sum(1 for b in r.get("bullets", []) if b.get("needs_revision", False))
        revision_count += role_revisions
        
        story.append(role_bullets(r, bullet_style, revision_style))
        story.append(Spacer(1, 8))

    # Internal notes section (optional)
    if include_notes:
        story.append(Spacer(1, 10))
        story.append(Paragraph("NOTES (INTERNAL)", h))
        
        if data.get("change_log"):
            story.append(Paragraph("<b>Change log:</b>", body))
            story.append(bullets(data.get("change_log", []), bullet_style))
            story.append(Spacer(1, 6))
        
        if data.get("questions_for_user"):
            story.append(Paragraph("<b>Questions:</b>", body))
            story.append(bullets(data.get("questions_for_user", []), bullet_style))
            story.append(Spacer(1, 6))
        
        if data.get("gaps_to_confirm"):
            story.append(Paragraph("<b>Gaps to confirm:</b>", body))
            story.append(bullets(data.get("gaps_to_confirm", []), bullet_style))
            story.append(Spacer(1, 6))
        
        if revision_count > 0:
            story.append(Paragraph(
                f"<b><i>⚠️ {revision_count} bullet(s) flagged for revision - see red text above</i></b>",
                revision_style
            ))

    try:
        doc.build(story)
        logger.info(f"Successfully rendered PDF: {output_pdf_path}")
    except Exception as e:
        logger.error(f"Failed to render PDF: {e}")
        raise


if __name__ == "__main__":
    import sys
    from src.utils.logger import setup_logger
    
    setup_logger()
    
    if len(sys.argv) < 2:
        tailored_json = str(Config.OUTPUT_DIR / "tailored_resume.json")
    else:
        tailored_json = sys.argv[1]
    
    if len(sys.argv) < 3:
        out_pdf = str(Config.OUTPUT_DIR / "tailored_resume.pdf")
    else:
        out_pdf = sys.argv[2]
    
    try:
        render_pdf(tailored_json, out_pdf)
        print(f"✅ Wrote PDF: {out_pdf}")
    except Exception as e:
        logger.error(f"Failed to render PDF: {e}")
        sys.exit(1)
