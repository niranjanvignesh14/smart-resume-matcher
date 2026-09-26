# Resume / JD Matcher

Upload one or more resumes (PDF) and paste a job description. Each resume
gets scored two ways, gets a visual matched/missing skill breakdown, and
gets concrete suggested resume bullet points to close the gaps. Upload more
than one resume and they're ranked against each other.

## Features
- **AI Match Score** — semantic similarity (TF-IDF + cosine), no API call.
- **ATS Keyword Score** — a separate, blunt keyword-overlap score that mimics
  how real Applicant Tracking Systems filter resumes before a human sees
  them. Deliberately dumb and literal, on purpose — that's what real ATS
  filters do.
- **Matched / missing skill tags** — from one structured Gemini call, so the
  UI shows tags instead of a paragraph.
- **Suggested resume additions** — specific bullet points the AI suggests
  adding to cover the JD's requirements, not just a list of what's missing.
- **Multi-resume ranking** — upload 2+ resumes against one JD, see them
  ranked by both scores side by side.

## How it works
1. **Text extraction** (`utils/extract.py`) — pulls plain text out of each PDF.
2. **AI Match Score** (`utils/match.py`, `compute_similarity`) — TF-IDF +
   cosine similarity. Fast, deterministic, runs with no API call.
3. **ATS Keyword Score** (`utils/match.py`, `compute_ats_keyword_score`) —
   extracts candidate keywords from the JD, checks literal presence in the
   resume. No API call either — this one's meant to be simple on purpose.
4. **AI explanation** (`utils/match.py`, `explain_match`) — one Gemini call,
   forced into JSON, returning a summary, matched skills, missing skills,
   and suggested resume bullet points.
5. **Streamlit UI** (`app.py`) — gauges for both scores, colored tags,
   suggestion cards, and a ranking leaderboard when multiple resumes are
   uploaded.

## Run it
```bash
bash run.sh          # Mac/Linux
run.bat               # Windows
```
It'll ask for your Gemini API key on first run (get one free at
https://aistudio.google.com/app/apikey), install dependencies, and open the
app in your browser automatically.

## Interview talking point
The AI score and ATS score are computed completely independently — one
never depends on the other being available. That's deliberate: the app
still gives useful output (ATS score, keyword gaps) even if the Gemini API
is down or rate-limited, and it means the ATS check can be trusted as an
objective baseline the AI explanation gets checked against, not just AI
output describing itself.
