"""TalentLens - Intelligent Resume Analyzer (Streamlit, pink & cream, multi-page flow)."""
import glob
import os
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import dashboard as dash
from engine import run_analysis
from loader import list_folder, read_file, read_folder, read_zip
from report import format_hr_report_csv

PINK, DEEP, CREAM = "#C72E5E", "#3F1B2B", "#FFF4E6"
st.set_page_config(page_title="TalentLens", page_icon="📄", layout="wide", initial_sidebar_state="collapsed")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;700&display=swap');
html, body, [class*="css"], .stApp {{ font-family:'DM Sans',sans-serif; color:{DEEP}; }}
.stApp {{ background:{CREAM}; }}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"],
[data-testid="stHeader"], #MainMenu, footer {{ display:none !important; }}
.block-container {{ max-width:1120px; padding-top:1.6rem; padding-bottom:4rem; }}
h1,h2,h3,h4 {{ font-family:'DM Serif Display',serif !important; font-weight:400 !important; color:{DEEP}; }}
.brand {{ display:flex; align-items:center; gap:12px; font-family:'DM Serif Display',serif; font-size:1.7rem; }}
.logo {{ width:42px; height:42px; border-radius:13px; background:{PINK}; display:flex; align-items:center; justify-content:center; }}
.hero {{ font-family:'DM Serif Display',serif; font-size:5rem; line-height:1; margin:3.5rem 0 1rem; }}
.hero span {{ color:{PINK}; }}
.sub {{ font-size:1.25rem; line-height:1.55; color:#6B3A4C; max-width:640px; margin-bottom:1.6rem; }}
.eyebrow {{ display:inline-block; background:#FFE3EB; color:#A21F4B; font-weight:700; font-size:.85rem;
  padding:6px 14px; border-radius:99px; letter-spacing:.04em; }}
.blob {{ position:absolute; right:-40px; top:90px; width:380px; height:380px; border-radius:50%;
  background:radial-gradient(circle at 30% 30%, #F7A8C0, {PINK}); opacity:.9; z-index:0; }}
.blob2 {{ position:absolute; right:260px; top:360px; width:120px; height:120px; border-radius:50%; background:#FFD9B8; z-index:0; }}
.card {{ background:#FFFDF8; border:1px solid #F3DDD3; border-radius:24px; padding:26px 28px; }}
.card h4 {{ margin:.2rem 0 .4rem; font-size:1.5rem; }}
.card p {{ color:#6B3A4C; margin:0; line-height:1.5; }}
.num {{ width:40px; height:40px; border-radius:50%; background:{PINK}; color:#fff; font-weight:700;
  display:flex; align-items:center; justify-content:center; margin-bottom:10px; }}
.steps {{ display:flex; gap:10px; margin:1.2rem 0 2rem; flex-wrap:wrap; }}
.step {{ padding:8px 18px; border-radius:99px; background:#F6E7DA; color:#8A6A5A; font-weight:700; font-size:.9rem; }}
.step.on {{ background:{PINK}; color:#fff; }} .step.done {{ background:#FFE3EB; color:#A21F4B; }}
.kpi {{ background:#FFFDF8; border:1px solid #F3DDD3; border-radius:20px; padding:18px 20px; }}
.kpi .l {{ font-size:.85rem; color:#6B3A4C; }} .kpi .v {{ font-family:'DM Serif Display',serif; font-size:2.3rem; }}
.kpi.hot {{ background:{PINK}; border-color:{PINK}; color:#fff; }} .kpi.hot .l {{ color:#fff; }}
.pod {{ background:#FFFDF8; border:1px solid #F3DDD3; border-radius:24px; padding:22px; text-align:center; }}
.pod.first {{ background:{PINK}; color:#fff; border-color:{PINK}; }}
.pod .m {{ font-family:'DM Serif Display',serif; font-size:3rem; line-height:1.1; }}
.pod .n {{ font-weight:700; font-size:1.1rem; }}
.chip {{ display:inline-block; padding:4px 12px; margin:3px; border-radius:99px; font-size:.85rem; }}
.ok {{ background:#FFE3EB; color:#A21F4B; }} .no {{ background:#EFE6E9; color:#5E4652; }}
[data-testid="stBaseButton-primary"] {{ background:{PINK}; color:#fff; border:0; border-radius:99px; padding:.65rem 1.8rem; font-weight:700; }}
[data-testid="stBaseButton-primary"]:hover {{ background:{DEEP}; color:#fff; }}
[data-testid="stBaseButton-secondary"] {{ background:transparent; color:{DEEP}; border:2px solid {DEEP}; border-radius:99px; padding:.6rem 1.6rem; font-weight:700; }}
[data-testid="stBaseButton-secondary"]:hover {{ background:{DEEP}; color:#fff; }}
.stDownloadButton button {{ background:{PINK}; color:#fff; border:0; border-radius:99px; font-weight:700; }}
[data-testid="stFileUploaderDropzone"] {{ background:#FFE9EF; border:2px dashed #E58BA8; border-radius:20px; }}
textarea {{ background:#FFFDF8 !important; border-radius:16px !important; }}
div[role="radiogroup"] label {{ background:#FFFDF8; border:1px solid #F3DDD3; border-radius:99px; padding:6px 16px; }}
</style>""", unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("page", "home")


def go_to(p):
    ss["page"] = p


def topbar():
    st.markdown(f'<div class="brand"><div class="logo"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" '
                f'stroke="#FFF4E6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l4 4v14H6z"/>'
                f'<path d="M9 13h7M9 17h5"/></svg></div>TalentLens</div>', unsafe_allow_html=True)


def stepper(active):
    names = ["Welcome", "Upload", "Analyze", "Results"]
    html = "".join(f'<div class="step {"on" if i == active else "done" if i < active else ""}">{i+1}. {n}</div>'
                   for i, n in enumerate(names))
    st.markdown(f'<div class="steps">{html}</div>', unsafe_allow_html=True)


def kpi(col, label, value, hot=False):
    col.markdown(f'<div class="kpi {"hot" if hot else ""}"><div class="l">{label}</div><div class="v">{value}</div></div>',
                 unsafe_allow_html=True)


def style(fig, h=330):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="DM Sans", color=DEEP),
                      margin=dict(l=10, r=10, t=50, b=10), height=h)
    return fig


def bar(labels, counts, title, horizontal=False):
    fig = go.Figure(go.Bar(x=counts if horizontal else labels, y=labels if horizontal else counts,
                           orientation="h" if horizontal else "v", marker_color=PINK))
    fig.update_layout(title=title)
    if horizontal:
        fig.update_yaxes(autorange="reversed")
    return style(fig)


def pie(labels, counts, title):
    fig = go.Figure(go.Pie(labels=labels, values=counts, hole=.55,
                           marker=dict(colors=[PINK, "#F2A3BC", "#F7C9A8", "#8A5A2B", "#D8B4C0", DEEP])))
    fig.update_layout(title=title)
    return style(fig)


def load_demo():
    jd = open("samples/sample_jd.txt", encoding="utf-8").read()
    texts = {os.path.basename(p): open(p, encoding="utf-8").read() for p in sorted(glob.glob("samples/demo_resumes/*.txt"))}
    ss.update(pending=(texts, jd), page="analyzing")


# ============================ PAGE 1: WELCOME ============================
if ss.page == "home":
    st.markdown('<div class="blob"></div><div class="blob2"></div>', unsafe_allow_html=True)
    topbar()
    st.markdown('<div style="position:relative;z-index:1"><span class="eyebrow">AI-STYLE RESUME SCREENING, 100% OFFLINE</span>'
                '<div class="hero">Welcome to<br><span>TalentLens.</span></div>'
                '<div class="sub">Drop in a job description and a pile of resumes. In seconds, see who fits best, '
                'what skills are missing, and who to interview first.</div></div>', unsafe_allow_html=True)
    b1, b2, _ = st.columns([1.2, 1.2, 4])
    b1.button("Get started", type="primary", on_click=go_to, args=("upload",))
    b2.button("Try demo", type="secondary", on_click=load_demo)
    st.write("")
    st.write("")
    c = st.columns(3)
    for col, n, t, d in [(c[0], "1", "Upload", "Add your job description and resumes in PDF, DOCX or TXT."),
                         (c[1], "2", "Analyze", "Every resume is scored against the skills the job needs."),
                         (c[2], "3", "Decide", "Get rankings, skill gaps, and a clear hiring recommendation.")]:
        col.markdown(f'<div class="card"><div class="num">{n}</div><h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)

# ============================ PAGE 2: UPLOAD ============================
elif ss.page == "upload":
    topbar()
    stepper(1)
    st.markdown("## Let's get your files")
    st.caption("Two quick things: tell us about the job, then add the resumes.")
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown('<div class="card"><div class="num">1</div><h4>Job description</h4></div>', unsafe_allow_html=True)
        mode = st.radio("How do you want to add it?", ["Paste text", "Upload file"], horizontal=True)
        jd_text = ""
        if mode == "Paste text":
            jd_text = st.text_area("Job description", height=220, placeholder="Paste the job description here...",
                                   label_visibility="collapsed")
        else:
            jf = st.file_uploader("JD file", type=["txt", "pdf", "docx"], key="jd", label_visibility="collapsed")
            if jf:
                jd_text = read_file(jf.name, jf.getvalue())
    with b:
        st.markdown('<div class="card"><div class="num">2</div><h4>Resumes</h4>'
                    '<p>Works for 1 or 200+ resumes.</p></div>', unsafe_allow_html=True)
        t_files, t_zip, t_dir = st.tabs(["Select files", "Upload ZIP folder", "Local folder path"])
        with t_files:
            files = st.file_uploader("Resumes", type=["txt", "pdf", "docx"], accept_multiple_files=True,
                                     label_visibility="collapsed")
            st.caption("Tip: in the file window press Ctrl + A to select every resume at once.")
        with t_zip:
            zips = st.file_uploader("ZIP", type=["zip"], accept_multiple_files=True, label_visibility="collapsed")
            st.caption("Right-click your resumes folder, Send to, Compressed (zipped) folder, then upload it here.")
        with t_dir:
            folder = st.text_input("Folder path", placeholder=r"C:\Users\you\Documents\resumes",
                                   label_visibility="collapsed")
            n_dir = len(list_folder(folder)) if folder and os.path.isdir(folder) else 0
            if folder and not n_dir:
                st.caption("No .pdf, .docx or .txt files found at that path.")
        total = len(files or []) + n_dir + len(zips or [])
        if total:
            st.success(f"Ready: {len(files or [])} file(s), {len(zips or [])} ZIP(s), {n_dir} file(s) from folder")
    st.write("")
    x, y, z, _ = st.columns([1.3, 1, 1.2, 3])
    ready = bool(jd_text.strip() and total)
    if x.button("Analyze resumes", type="primary", disabled=not ready):
        texts, skipped = {}, 0
        for f in files or []:
            try:
                texts[f.name] = read_file(f.name, f.getvalue())
            except Exception:
                skipped += 1
        for zf in zips or []:
            t, sk = read_zip(zf.getvalue())
            texts.update({k: v for k, v in t.items() if k not in texts})
            skipped += sk
        if n_dir:
            t, sk = read_folder(folder)
            texts.update({k: v for k, v in t.items() if k not in texts})
            skipped += sk
        ss.pending, ss.skipped, ss.page = (texts, jd_text), skipped, "analyzing"
        st.rerun()
    y.button("Back", type="secondary", on_click=go_to, args=("home",))
    z.button("Use demo data", type="secondary", on_click=load_demo)
    if not ready:
        st.caption("Add a job description and at least one resume to continue.")

# ============================ PAGE 3: ANALYZING ============================
elif ss.page == "analyzing":
    topbar()
    stepper(2)
    st.markdown("## Reading your resumes...")
    bar_ = st.progress(0)
    status = st.empty()
    texts, jd = ss.pending
    for pct, msg in [(15, "Extracting text from resumes"), (40, "Finding skills in the job description"),
                     (70, "Scoring every candidate"), (90, "Building insights and rankings")]:
        status.markdown(f"**{msg}...**")
        bar_.progress(pct)
        time.sleep(0.25)
    results = run_analysis(texts, jd)
    if not results:
        st.error("We couldn't read any text from those resumes. Try different files.")
        st.button("Back to upload", type="primary", on_click=go_to, args=("upload",))
        st.stop()
    bar_.progress(100)
    ss.update(results=results, total=len(texts), page="results", view="Overview")
    st.rerun()

# ============================ PAGE 4: RESULTS ============================
else:
    results = ss["results"]
    h1, h2 = st.columns([4, 1])
    with h1:
        topbar()
    h2.button("New analysis", type="secondary", on_click=go_to, args=("home",))
    stepper(3)
    if ss.get("skipped"):
        st.warning(f"{ss['skipped']} file(s) could not be read and were skipped.")
    view = st.radio("View", ["Overview", "Ranking", "Candidate details"], horizontal=True, key="view",
                    label_visibility="collapsed")
    st.write("")

    rows = [{"Rank": r["rank"], "Candidate": r["profile"]["name"], "File": r["resume_file"], "Match %": r["percentage"],
             "ATS": r["insights"]["ats_score"], "Interview readiness": r["insights"]["interview_readiness"],
             "Recommendation": r["insights"]["final_recommendation"]["label"]} for r in results]
    df = pd.DataFrame(rows)

    if view == "Overview":
        k = dash.compute_kpis(results, ss["total"])
        cols = st.columns(5)
        kpi(cols[0], "Resumes screened", k["total_uploaded"])
        kpi(cols[1], "Shortlisted", k["shortlisted"])
        kpi(cols[2], "Rejected", k["rejected"])
        kpi(cols[3], "Average match", f'{k["average_score"]}%')
        kpi(cols[4], "Top match", f'{k["highest_score"]}%', hot=True)
        st.markdown("### Top candidates")
        top = st.columns(min(3, len(results)))
        for i, col in enumerate(top):
            r = results[i]
            col.markdown(f'<div class="pod {"first" if i == 0 else ""}"><div>#{i+1}</div><div class="m">{r["percentage"]}%</div>'
                         f'<div class="n">{r["profile"]["name"]}</div>'
                         f'<div style="opacity:.85">{r["insights"]["final_recommendation"]["label"]}</div></div>',
                         unsafe_allow_html=True)
        st.write("")
        a, b = st.columns(2)
        a.plotly_chart(bar(*dash.score_distribution(results), "Match score distribution"), width="stretch")
        b.plotly_chart(pie(*dash.shortlisted_vs_rejected(results), "Shortlisted vs rejected"), width="stretch")
        c, d = st.columns(2)
        c.plotly_chart(bar(*dash.top_skills_frequency(results), "Most common skills", True), width="stretch")
        d.plotly_chart(bar(*dash.missing_skills_analysis(results), "Most missed skills", True), width="stretch")
        e, f = st.columns(2)
        e.plotly_chart(pie(*dash.education_distribution(results), "Education"), width="stretch")
        f.plotly_chart(bar(*dash.experience_distribution(results), "Experience (years)"), width="stretch")

    elif view == "Ranking":
        q, m = st.columns([2, 1])
        text = q.text_input("Search candidate")
        minimum = m.slider("Minimum match %", 0, 100, 0)
        sel = df[(df["Match %"] >= minimum) & df["Candidate"].str.contains(text, case=False, na=False)]
        st.dataframe(sel, width="stretch", hide_index=True,
                     column_config={"Match %": st.column_config.ProgressColumn("Match %", min_value=0, max_value=100, format="%d%%")})
        st.download_button("Download HR report (CSV)", format_hr_report_csv(results, "job_description", ss["total"]),
                           "hr_candidate_report.csv", "text/csv")

    else:
        pick = st.selectbox("Choose a candidate", [f'{r["rank"]}. {r["profile"]["name"]}' for r in results])
        r = results[int(pick.split(".")[0]) - 1]
        ins = r["insights"]
        g = st.columns(3)
        kpi(g[0], "Match score", f'{r["percentage"]}%', hot=True)
        kpi(g[1], "Skills matched", f'{r["matched_count"]} / {r["total_required"]}')
        kpi(g[2], "Recommendation", ins["final_recommendation"]["label"])
        st.write("")
        x, y = st.columns(2)
        x.markdown("#### Matched skills")
        x.markdown("".join(f'<span class="chip ok">{s}</span>' for s in r["matched"]) or "None", unsafe_allow_html=True)
        y.markdown("#### Missing skills")
        y.markdown("".join(f'<span class="chip no">{s}</span>' for s in r["missing"]) or "None", unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        s1.markdown("#### Strengths")
        for s in ins["strengths"]:
            s1.write(f"- {s}")
        s2.markdown("#### Weaknesses")
        for s in ins["weaknesses"]:
            s2.write(f"- {s}")
        st.markdown("#### Overall feedback")
        st.write(ins["overall_feedback"])
