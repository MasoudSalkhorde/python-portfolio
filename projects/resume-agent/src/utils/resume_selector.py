import json
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from pathlib import Path

from src.utils.io_pdf import pdf_to_text

@dataclass
class ResumeCandidate:
    id: str
    path: str
    label: str
    keywords: List[str]

def load_candidates(index_path: str) -> List[ResumeCandidate]:
    with open(index_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    return [ResumeCandidate(**x) for x in items]

def keyword_score(jd_text: str, keywords: list[str]) -> float:
    jd = jd_text.lower()
    jd_tokens = set(jd.split())
    score = 0.0

    for kw in keywords:
        kw_l = kw.lower()
        kw_tokens = set(kw_l.split())

        if kw_l in jd:
            score += 2.0            # strong signal
        elif kw_tokens & jd_tokens:
            score += 1.0            # weaker signal

    return score


def choose_resume_pdf(jd_text: str, index_path: str = "src/data/resumes/resume_index.json") -> Tuple[ResumeCandidate, Dict[str, float]]:
    candidates = load_candidates(index_path)
    scores = {}
    for c in candidates:
        scores[c.id] = keyword_score(jd_text, c.keywords)

    best = max(candidates, key=lambda c: scores[c.id])
    return best, scores
