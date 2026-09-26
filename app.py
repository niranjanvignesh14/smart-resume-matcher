"""
Resume / JD Matcher
--------------------
Upload one or more resumes (PDF) and paste a job description. Each resume
gets an AI match score, a separate ATS keyword score, a matched/missing
skill breakdown, and concrete suggested bullet points to close the gaps.
With more than one resume, they're ranked against each other.

Run with:  streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
from utils.extract import extract_text_from_pdf
from utils.match import compute_similarity, compute_ats_keyword_score, explain_match

st.set_page_config(page_title="Resume / JD Matcher", page_icon="🧩", layout="centered")

# ---- Styling ----------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(160deg, #0f172a 0%, #1e1b4b 100%); }
    h1, h2, h3, p, label, .stMarkdown { color: #f1f5f9 !important; }
    .hero { text-align: center; padding: 8px 0 20px 0; }
    .hero h1 {
        font-size: 2.4rem;
        background: linear-gradient(90deg, #818cf8, #f472b6, #fbbf24);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 16px;
    }
    .tag {
        display: inline-block;
        padding: 6px 14px;
        margin: 4px 6px 4px 0;
        border-radius: 999px;
        font-size: 14px;
        font-weight: 600;
    }
    .tag-match { background: rgba(34,197,94,0.18); color: #4ade80; border: 1px solid rgba(74,222,128,0.4); }
    .tag-missing { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.4); }
    .suggestion {
        background: rgba(129,140,248,0.12);
        border-left: 3px solid #818cf8;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 14px;
    }
    .summary-line {
        font-size: 18px;
        font-weight: 600;
        color: #e0e7ff !important;
        margin-bottom: 14px;
    }
    .rank-badge {
        display: inline-block;
        width: 28px; height: 28px;
        border-radius: 50%;
        background: linear-gradient(90deg, #6366f1, #ec4899);
        color: white;
        text-align: center;
        line-height: 28px;
        font-weight: 700;
        margin-right: 8px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #6366f1, #ec4899);
        color: white; border: none; border-radius: 10px;
        font-weight: 700; padding: 12px 0;
        transition: transform 0.15s ease;
    }
    .stButton>button:hover { transform: scale(1.02); color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>🧩 Resume / JD Matcher</h1>'
    '<p>Upload one or more resumes, paste a job description, get a ranked, visual match.</p></div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("📄 Resume(s)")
    resume_files = st.file_uploader(
        "Upload one or more resumes (PDF)", type=["pdf"], accept_multiple_files=True
    )
with col2:
    st.subheader("🎯 Job Description")
    jd_text = st.text_area("Paste the job description here", height=220)

go_button = st.button("✨ Check Match", type="primary", use_container_width=True)


def gauge_color(score: float) -> str:
    if score >= 0.7:
        return "#4ade80"
    if score >= 0.4:
        return "#fbbf24"
    return "#f87171"


def render_gauge(score_pct: float, title: str = ""):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_pct,
            title={"text": title, "font": {"color": "#f1f5f9", "size": 14}},
            number={"suffix": "%", "font": {"color": "#f1f5f9", "size": 34}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#f1f5f9"},
                "bar": {"color": gauge_color(score_pct / 100)},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "rgba(248,113,113,0.15)"},
                    {"range": [40, 70], "color": "rgba(251,191,36,0.15)"},
                    {"range": [70, 100], "color": "rgba(74,222,128,0.15)"},
                ],
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=220,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_result_card(name: str, resume_text: str, jd_text: str):
    with st.spinner(f"Scoring {name}..."):
        ai_score = compute_similarity(resume_text, jd_text)
        ats = compute_ats_keyword_score(resume_text, jd_text)

    with st.spinner(f"Asking AI to break down {name}..."):
        result = explain_match(resume_text, jd_text, ai_score)

    g1, g2 = st.columns(2)
    with g1:
        render_gauge(round(ai_score * 100), "AI Match Score")
    with g2:
        render_gauge(round(ats["score"] * 100), "ATS Keyword Score")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        f'<p class="summary-line">💡 {result.get("summary", "")}</p>',
        unsafe_allow_html=True,
    )

    matched = result.get("matched_skills", [])
    missing = result.get("missing_skills", [])
    suggestions = result.get("suggested_additions", [])

    if matched:
        st.markdown("**✅ What matches**")
        st.markdown(
            "".join(f'<span class="tag tag-match">{s}</span>' for s in matched),
            unsafe_allow_html=True,
        )
    if missing:
        st.markdown("**⚠️ What's missing**")
        st.markdown(
            "".join(f'<span class="tag tag-missing">{s}</span>' for s in missing),
            unsafe_allow_html=True,
        )
    if suggestions:
        st.markdown("**✍️ Suggested resume additions**")
        for s in suggestions:
            st.markdown(f'<div class="suggestion">{s}</div>', unsafe_allow_html=True)

    if ats["missing"]:
        with st.expander(f"ATS keyword detail ({len(ats['matched'])}/{len(ats['matched']) + len(ats['missing'])} found)"):
            st.write("**Found in resume:** " + (", ".join(ats["matched"]) or "none"))
            st.write("**Missing from resume:** " + (", ".join(ats["missing"]) or "none"))

    st.markdown("</div>", unsafe_allow_html=True)
    return {"name": name, "ai_score": ai_score, "ats_score": ats["score"]}


if go_button:
    if not resume_files:
        st.error("Please upload at least one resume PDF.")
    elif not jd_text.strip():
        st.error("Please paste a job description.")
    else:
        st.divider()
        results = []

        for f in resume_files:
            resume_text = extract_text_from_pdf(f)
            st.subheader(f"📄 {f.name}")
            results.append(render_result_card(f.name, resume_text, jd_text))
            st.divider()

        # Ranking leaderboard, only shown when comparing multiple resumes
        if len(results) > 1:
            st.subheader("🏆 Ranking")
            ranked = sorted(results, key=lambda r: r["ai_score"], reverse=True)
            for i, r in enumerate(ranked, start=1):
                st.markdown(
                    f'<div class="card">'
                    f'<span class="rank-badge">{i}</span>'
                    f'<strong>{r["name"]}</strong> — '
                    f'AI: {round(r["ai_score"] * 100)}% &nbsp;|&nbsp; '
                    f'ATS: {round(r["ats_score"] * 100)}%'
                    f'</div>',
                    unsafe_allow_html=True,
                )
