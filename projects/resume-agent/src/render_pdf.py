import json
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def load_tailored_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def bullets(items, style):
    return ListFlowable(
        [ListItem(Paragraph(i, style), leftIndent=14) for i in items],
        bulletType="bullet",
        leftIndent=18,
    )


def role_bullets(role, bullet_style):
    items = [b["text"] for b in role.get("bullets", [])]
    return bullets(items, bullet_style)


def render_pdf(tailored_json_path: str, output_pdf_path: str):
    data = load_tailored_json(tailored_json_path)

    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, spaceAfter=8)
    h = ParagraphStyle("H", parent=styles["Heading2"], spaceBefore=10, spaceAfter=4)
    subh = ParagraphStyle("SubH", parent=styles["Heading3"], spaceBefore=6, spaceAfter=2)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10, leading=12)
    bullet_style = ParagraphStyle("Bullet", parent=body, leftIndent=0)

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

    # Header (you can improve this by storing name/contact in your tailored JSON)
    story.append(Paragraph(data.get("tailored_headline", "Resume"), title))
    story.append(Spacer(1, 8))

    # Summary
    story.append(Paragraph("SUMMARY", h))
    story.append(bullets(data.get("tailored_summary", []), bullet_style))
    story.append(Spacer(1, 8))

    # Skills
    story.append(Paragraph("SKILLS", h))
    skills_line = ", ".join(data.get("tailored_skills", []))
    story.append(Paragraph(skills_line, body))
    story.append(Spacer(1, 10))

    # Experience
    story.append(Paragraph("EXPERIENCE", h))
    for r in data.get("tailored_roles", []):
        role_line = f'{r.get("title","")} — {r.get("company","")} ({r.get("dates","")})'
        story.append(Paragraph(role_line, subh))
        story.append(role_bullets(r, bullet_style))
        story.append(Spacer(1, 8))

    # Optional: questions / change log as appendix (usually not in final resume)
    # comment out if you don't want it in PDF
    story.append(Paragraph("NOTES (INTERNAL)", h))
    story.append(Paragraph("<b>Change log:</b>", body))
    story.append(bullets(data.get("change_log", []), bullet_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Questions:</b>", body))
    story.append(bullets(data.get("questions_for_user", []), bullet_style))

    doc.build(story)


if __name__ == "__main__":
    # Adjust these paths to match your project
    tailored_json = str(Path("outputs/tailored_resume.json"))
    out_pdf = str(Path("outputs/tailored_resume.pdf"))
    render_pdf(tailored_json, out_pdf)
    print("Wrote:", out_pdf)
