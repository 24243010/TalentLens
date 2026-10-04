"""Backend glue: analyze resumes against a JD and enrich the results."""
from analyzer import analyze_multiple_resumes
from extraction import extract_candidate_profile
from insights import build_candidate_insights


def run_analysis(resume_texts: dict, jd_text: str) -> list:
    resume_texts = {k: v for k, v in resume_texts.items() if v.strip()}
    results = analyze_multiple_resumes(resume_texts, jd_text)
    for r in results:
        text = resume_texts[r["resume_file"]]
        profile = extract_candidate_profile(text, r["resume_skills"], filename=r["resume_file"])
        r["profile"] = profile
        r["insights"] = build_candidate_insights(r, text, jd_text, profile)
    return results
