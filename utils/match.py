"""
Matching logic. Three independent pieces, each usable on its own:

1. compute_similarity      -- TF-IDF cosine score (classic ML, no API call)
2. compute_ats_keyword_score -- keyword-overlap score, mimicking how real
   Applicant Tracking Systems filter resumes (also no API call)
3. explain_match           -- one Gemini call returning STRUCTURED data:
   summary, matched skills, missing skills, and suggested resume bullet
   points to add -- so the UI can render tags and actionable suggestions
   instead of a wall of text.
"""

import os
import re
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from google import genai

_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
_MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """You are a hiring assistant. Given a resume and a job \
description, respond with ONLY a JSON object, no prose, no markdown fences, \
in exactly this shape:

{
  "summary": "<one punchy sentence on overall fit>",
  "matched_skills": ["<skill or experience from the resume that fits the JD>", ...],
  "missing_skills": ["<requirement from the JD not evident in the resume>", ...],
  "suggested_additions": ["<a specific resume bullet point the candidate could \
add to cover a missing requirement, written as if going straight onto the \
resume>", ...]
}

List 3-6 items in matched_skills and missing_skills. List 2-4 items in \
suggested_additions, one per major gap -- make them concrete and specific \
(name real tools/metrics), never generic filler."""


def compute_similarity(resume_text: str, jd_text: str) -> float:
    """TF-IDF cosine similarity, 0.0 to 1.0. Fast, deterministic, no API call."""
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume_text, jd_text])
    score = cosine_similarity(vectors[0], vectors[1])[0][0]
    return float(score)


def _extract_keywords(text: str, top_n: int = 25) -> set[str]:
    """
    Pulls out candidate 'keyword' tokens the way a simple ATS keyword filter
    would: words 3+ letters, not a stopword, deduplicated. Deliberately dumb
    and fast -- this is meant to mimic naive ATS behavior, not be smart.
    """
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#]*(?:\.[A-Za-z0-9+#]+)*", text)
    keywords = [
        w.lower().strip(".")
        for w in words
        if len(w) >= 3 and w.lower().strip(".") not in ENGLISH_STOP_WORDS
    ]
    keywords = [k for k in keywords if k]  # drop anything emptied by stripping
    seen_order = list(dict.fromkeys(keywords))
    return set(seen_order[:top_n])


def compute_ats_keyword_score(resume_text: str, jd_text: str) -> dict:
    """
    Returns {"score": 0-1, "matched": [...], "missing": [...]} based on
    literal keyword overlap between the JD and resume -- the blunt-instrument
    check real ATS keyword filters run before a human ever sees the resume.
    """
    jd_keywords = _extract_keywords(jd_text, top_n=25)
    resume_lower = resume_text.lower()

    matched = sorted(k for k in jd_keywords if k in resume_lower)
    missing = sorted(k for k in jd_keywords if k not in resume_lower)

    score = len(matched) / len(jd_keywords) if jd_keywords else 0.0
    return {"score": score, "matched": matched, "missing": missing}


def explain_match(resume_text: str, jd_text: str, score: float) -> dict:
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Match score: {round(score * 100)}%\n\n"
        f"Resume:\n{resume_text[:4000]}\n\n"
        f"Job description:\n{jd_text[:4000]}"
    )
    response = _client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config={
            "http_options": {"timeout": 20000},
            "response_mime_type": "application/json",
        },
    )
    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return {
            "summary": response.text or "Couldn't parse a structured explanation.",
            "matched_skills": [],
            "missing_skills": [],
            "suggested_additions": [],
        }
