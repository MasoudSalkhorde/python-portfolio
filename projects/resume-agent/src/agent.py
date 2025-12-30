import json
from typing import Type, TypeVar
from src.utils.schemas import (
    JobDescriptionJSON, ResumeJSON, MatchJSON, TailoredResumeJSON
)
from src.utils.io_pdf import pdf_to_text
import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

T = TypeVar("T")

def call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-5.1",  # or gpt-4.1 / gpt-4o-mini
        messages=[
            {"role": "system", "content": "You are a precise JSON-only generator."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()

def llm_to_schema(prompt: str, schema: Type[T]) -> T:
    raw = call_llm(prompt)
    data = json.loads(raw)
    return schema.model_validate(data)

def run_pipeline(jd_text: str, resume_pdf_path: str) -> TailoredResumeJSON:
    resume_text = pdf_to_text(resume_pdf_path)

    from src.utils.prompts import (
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
    from src.utils.validators import validate_tailored_resume
    validate_tailored_resume(resume, tailored)

    return tailored

if __name__ == "__main__":
    JD_TEXT = open("./src/data/jd.txt", "r", encoding="utf-8").read()
    tailored = run_pipeline(JD_TEXT, "./src/data/250_EA.pdf")

    with open("outputs/tailored_resume.json", "w") as f:
        f.write(tailored.model_dump_json(indent=2))
