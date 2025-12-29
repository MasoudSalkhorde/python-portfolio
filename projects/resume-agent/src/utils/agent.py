import json
from typing import Type, TypeVar
from schemas import (
    JobDescriptionJSON, ResumeJSON, MatchJSON, TailoredResumeJSON
)
from io_pdf import pdf_to_text

T = TypeVar("T")

def call_llm(prompt: str) -> str:
    """
    Replace this with your model call.
    Must return raw text that is JSON (no markdown).
    """
    raise NotImplementedError

def llm_to_schema(prompt: str, schema: Type[T]) -> T:
    raw = call_llm(prompt)
    data = json.loads(raw)
    return schema.model_validate(data)

def run_pipeline(jd_text: str, resume_pdf_path: str) -> TailoredResumeJSON:
    resume_text = pdf_to_text(resume_pdf_path)

    from prompts import (
        prompt_extract_jd,
        prompt_extract_resume,
        prompt_match,
        prompt_tailor,
    )

    jd = llm_to_schema(prompt_extract_jd(jd_text), JobDescriptionJSON)
    resume = llm_to_schema(prompt_extract_resume(resume_text), ResumeJSON)
    match = llm_to_schema(prompt_match(jd, resume), MatchJSON)
    tailored = llm_to_schema(prompt_tailor(jd, resume, match), TailoredResumeJSON)

    # validators.py checks
    from validators import validate_tailored_resume
    validate_tailored_resume(resume, tailored)

    return tailored

if __name__ == "__main__":
    JD_TEXT = open("jd.txt", "r", encoding="utf-8").read()
    out = run_pipeline(JD_TEXT, "/mnt/data/250_EA.pdf")
    print(out.model_dump_json(indent=2))
