from schemas import ResumeJSON, TailoredResumeJSON

def validate_tailored_resume(resume: ResumeJSON, tailored: TailoredResumeJSON) -> None:
    valid_ids = {b.id for r in resume.roles for b in r.bullets}
    valid_companies = {r.company for r in resume.roles}
    valid_skills = set(resume.skills)

    # Check bullet provenance
    for role in tailored.tailored_roles:
        if role.company not in valid_companies:
            raise ValueError(f"New company not allowed: {role.company}")
        for b in role.bullets:
            for sid in b.source_bullet_ids:
                if sid not in valid_ids:
                    raise ValueError(f"Invalid source bullet id: {sid}")

    # Optional: detect new tools (simple heuristic)
    # You can maintain a whitelist of tools from resume.skills and resume bullets.
