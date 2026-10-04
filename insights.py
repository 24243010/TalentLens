"""
insights.py
------------
Generates the richer HR-style candidate insights layered on top of the
core Resume Analysis result from analyzer.py:

    - Star rating / candidate tier
    - Skill Strength rating
    - Experience rating
    - Education rating
    - ATS Compatibility Score
    - Interview Readiness Score
    - Final HR Recommendation (6-tier)
    - Skill Gap tiers (Excellent / Good / Average / Missing / Critical Missing)
    - Strengths, Areas for Improvement, and a written Overall Feedback
      paragraph

Everything here is computed with simple, transparent, rule-based
formulas and string templates - no AI, Machine Learning, or NLP
libraries are used, and the underlying Match Percentage / matched
skill sets from analyzer.py are never recalculated or altered, only
read.
"""

from analyzer import count_skill_occurrences


# --------------------------------------------------------------------------
# STAR RATING
# --------------------------------------------------------------------------

def star_rating(percentage: int) -> dict:
    """
    Convert a Match Percentage into a 1-5 star candidate tier.

    Args:
        percentage (int): Resume Match Percentage (0-100).

    Returns:
        dict: {"stars": int, "label": str, "display": str} e.g.
              {"stars": 5, "label": "Excellent Candidate", "display": "*****"}
    """
    if percentage >= 90:
        stars, label = 5, "Excellent Candidate"
    elif percentage >= 75:
        stars, label = 4, "Strong Candidate"
    elif percentage >= 60:
        stars, label = 3, "Moderate Candidate"
    elif percentage >= 40:
        stars, label = 2, "Weak Candidate"
    else:
        stars, label = 1, "Not Suitable"

    display = "\u2605" * stars + "\u2606" * (5 - stars)
    return {"stars": stars, "label": label, "display": display}


# --------------------------------------------------------------------------
# SKILL STRENGTH RATING
# --------------------------------------------------------------------------

def skill_strength_rating(matched_count: int) -> str:
    """
    Rate the candidate's overall skill strength based on how many
    required skills were matched (a distinct qualitative signal from
    the numeric Match Percentage, which is relative to the JD's size).

    Args:
        matched_count (int): Number of matched skills.

    Returns:
        str: "Very Strong", "Strong", "Moderate", or "Weak".
    """
    if matched_count >= 15:
        return "Very Strong"
    elif matched_count >= 10:
        return "Strong"
    elif matched_count >= 5:
        return "Moderate"
    else:
        return "Weak"


# --------------------------------------------------------------------------
# EXPERIENCE / EDUCATION RATINGS
# --------------------------------------------------------------------------

def experience_rating(years: int) -> str:
    """
    Rate the candidate's experience level based on best-effort extracted
    years of experience.

    Args:
        years (int): Extracted years of experience (0 if unknown).

    Returns:
        str: A human-readable experience tier.
    """
    if years <= 0:
        return "Not specified"
    elif years <= 1:
        return "Entry-Level (0-1 yrs)"
    elif years <= 4:
        return "Junior (2-4 yrs)"
    elif years <= 7:
        return "Mid-Level (5-7 yrs)"
    else:
        return "Senior (8+ yrs)"


_EDUCATION_RATING_MAP = {
    "PhD / Doctorate": "Excellent",
    "Master's Degree": "Excellent",
    "Bachelor's Degree": "Good",
    "Diploma": "Fair",
    "Not specified": "Unknown",
}


def education_rating(education_level: str) -> str:
    """
    Rate the candidate's education level.

    Args:
        education_level (str): Output of extraction.extract_education_level.

    Returns:
        str: "Excellent", "Good", "Fair", or "Unknown".
    """
    return _EDUCATION_RATING_MAP.get(education_level, "Unknown")


# --------------------------------------------------------------------------
# ATS COMPATIBILITY SCORE
# --------------------------------------------------------------------------

_ATS_SECTION_KEYWORDS = {
    "experience": ["experience", "work history", "employment"],
    "education": ["education", "academic", "qualification"],
    "skills": ["skills", "technical skills", "core competencies"],
}


def ats_compatibility_score(resume_text: str, resume_skills, email: str, phone: str) -> int:
    """
    Compute a simple, transparent ATS (Applicant Tracking System)
    compatibility score out of 100, based on characteristics that real
    ATS parsers commonly look for: presence of contact details and
    presence of standard resume section headers, plus having a
    reasonable number of recognizable skills listed.

    Scoring (20 points each, capped at 100):
        - Email address found
        - Phone number found
        - An "Experience" section header is present
        - An "Education" section header is present
        - At least 5 recognizable skills were detected

    Args:
        resume_text (str): Raw Resume text.
        resume_skills: Iterable of skill keywords detected in the Resume.
        email (str): Extracted email address ("Not found" if absent).
        phone (str): Extracted phone number ("Not found" if absent).

    Returns:
        int: ATS Compatibility Score from 0 to 100.
    """
    lowered = resume_text.lower()
    score = 0

    if email != "Not found":
        score += 20
    if phone != "Not found":
        score += 20
    if any(keyword in lowered for keyword in _ATS_SECTION_KEYWORDS["experience"]):
        score += 20
    if any(keyword in lowered for keyword in _ATS_SECTION_KEYWORDS["education"]):
        score += 20
    if len(set(resume_skills)) >= 5:
        score += 20

    return min(score, 100)


# --------------------------------------------------------------------------
# INTERVIEW READINESS SCORE
# --------------------------------------------------------------------------

def interview_readiness_score(match_percentage: int, ats_score: int, matched_count: int) -> int:
    """
    Compute a composite Interview Readiness Score by averaging the
    Match Percentage, the ATS Compatibility Score, and a skill-volume
    score (matched skill count scaled to a 0-100 range, capped at 100).

    Args:
        match_percentage (int): Resume Match Percentage (0-100).
        ats_score (int): ATS Compatibility Score (0-100).
        matched_count (int): Number of matched skills.

    Returns:
        int: Interview Readiness Score from 0 to 100.
    """
    skill_volume_score = min(matched_count * 5, 100)
    composite = (match_percentage + ats_score + skill_volume_score) / 3
    return round(composite)


# --------------------------------------------------------------------------
# FINAL HR RECOMMENDATION (6-tier)
# --------------------------------------------------------------------------

def final_recommendation(percentage: int) -> dict:
    """
    Generate the final HR-facing recommendation tier, distinct from (and
    more granular than) the existing 5-tier Candidate Recommendation
    used in the ranking table. This does not replace or alter the
    original recommendation logic - it is an additional, HR-oriented
    decision layer used for candidate detail views and report exports.

    Args:
        percentage (int): Resume Match Percentage (0-100).

    Returns:
        dict: {"label": str, "color": str, "explanation": str}
    """
    if percentage >= 90:
        return {
            "label": "Highly Recommended",
            "color": "#1B5E20",
            "explanation": (
                "This candidate's skill set very closely matches the Job "
                "Description and should be prioritized for an interview."
            ),
        }
    elif percentage >= 80:
        return {
            "label": "Recommended",
            "color": "#2E7D32",
            "explanation": (
                "This candidate matches most of the Job Description's "
                "requirements and is a strong candidate for interview."
            ),
        }
    elif percentage >= 65:
        return {
            "label": "Consider for Interview",
            "color": "#F9A825",
            "explanation": (
                "This candidate meets a reasonable portion of the "
                "requirements and could be worth an initial screening call."
            ),
        }
    elif percentage >= 50:
        return {
            "label": "Average Match",
            "color": "#EF6C00",
            "explanation": (
                "This candidate meets some requirements but has notable "
                "gaps against the Job Description."
            ),
        }
    elif percentage >= 35:
        return {
            "label": "Needs Improvement",
            "color": "#D84315",
            "explanation": (
                "This candidate's current skill set falls short of the "
                "Job Description in several key areas."
            ),
        }
    else:
        return {
            "label": "Not Suitable",
            "color": "#C62828",
            "explanation": (
                "This candidate's Resume shows little overlap with the "
                "Job Description's requirements."
            ),
        }


# --------------------------------------------------------------------------
# SKILL GAP ANALYSIS (tiered)
# --------------------------------------------------------------------------

def skill_gap_analysis(resume_text: str, jd_text: str, matched: list, missing: list) -> dict:
    """
    Break the existing Matched/Missing skill lists into finer tiers for
    a richer Skill Gap Analysis view, using how often each skill is
    emphasized in the Resume (for matched skills) or in the Job
    Description (for missing skills) as a simple, transparent proxy for
    importance - purely frequency-based, no AI/NLP involved.

    Args:
        resume_text (str): Raw Resume text.
        jd_text (str): Raw Job Description text.
        matched (list): Matched skill keywords (already computed).
        missing (list): Missing skill keywords (already computed).

    Returns:
        dict: {
            "excellent": list[str],   # matched, emphasized 3+ times in Resume
            "good": list[str],        # matched, emphasized 2 times
            "average": list[str],     # matched, mentioned once
            "missing": list[str],     # required but absent, non-critical
            "critical_missing": list[str],  # required, absent, and emphasized 2+ times in the JD
        }
    """
    resume_counts = count_skill_occurrences(resume_text, matched)
    jd_counts = count_skill_occurrences(jd_text, missing)

    excellent, good, average = [], [], []
    for skill in matched:
        count = resume_counts.get(skill, 1)
        if count >= 3:
            excellent.append(skill)
        elif count == 2:
            good.append(skill)
        else:
            average.append(skill)

    critical_missing, plain_missing = [], []
    for skill in missing:
        count = jd_counts.get(skill, 0)
        if count >= 2:
            critical_missing.append(skill)
        else:
            plain_missing.append(skill)

    return {
        "excellent": sorted(excellent),
        "good": sorted(good),
        "average": sorted(average),
        "missing": sorted(plain_missing),
        "critical_missing": sorted(critical_missing),
    }


# --------------------------------------------------------------------------
# STRENGTHS / WEAKNESSES / OVERALL FEEDBACK (templated text)
# --------------------------------------------------------------------------

def generate_strengths(matched: list, ats_score: int, education_level: str) -> list:
    """
    Generate a short list of candidate strengths from computed values.

    Args:
        matched (list): Matched skill keywords.
        ats_score (int): ATS Compatibility Score (0-100).
        education_level (str): Extracted education level.

    Returns:
        list[str]: Up to 5 strength statements.
    """
    strengths = []

    top_skills = matched[:3]
    for skill in top_skills:
        strengths.append(f"Strong {skill.title()} skills")

    if ats_score >= 80:
        strengths.append("ATS Friendly Resume with clear structure")

    if education_level in ("Master's Degree", "PhD / Doctorate"):
        strengths.append(f"Advanced qualification: {education_level}")

    if len(matched) >= 10:
        strengths.append("Broad skill set covering most job requirements")

    if not strengths:
        strengths.append("Resume was analyzed successfully; no standout strengths detected")

    return strengths[:5]


def generate_weaknesses(missing: list, critical_missing: list, ats_score: int) -> list:
    """
    Generate a short list of areas for improvement from computed values.

    Args:
        missing (list): Missing (non-critical) skill keywords.
        critical_missing (list): Critical missing skill keywords.
        ats_score (int): ATS Compatibility Score (0-100).

    Returns:
        list[str]: Up to 5 improvement suggestions.
    """
    weaknesses = []

    for skill in critical_missing[:3]:
        weaknesses.append(f"Add or highlight {skill.title()} experience (frequently required by the JD)")

    remaining_slots = 5 - len(weaknesses)
    for skill in missing[:remaining_slots]:
        weaknesses.append(f"Consider gaining exposure to {skill.title()}")

    if ats_score < 60:
        weaknesses.append("Improve resume structure with clear Skills/Experience/Education sections")

    if not weaknesses:
        weaknesses.append("No significant skill gaps detected against this Job Description")

    return weaknesses[:5]


def generate_overall_feedback(name: str, percentage: int, recommendation_label: str,
                               star_label: str, matched_count: int, total_required: int) -> str:
    """
    Generate a short, professional written summary paragraph for the
    candidate, built entirely from string templates and computed
    values (no AI/NLP generation involved).

    Args:
        name (str): Candidate name (or "This candidate" fallback).
        percentage (int): Resume Match Percentage (0-100).
        recommendation_label (str): Final HR recommendation label.
        star_label (str): Star-rating label (e.g. "Excellent Candidate").
        matched_count (int): Number of matched skills.
        total_required (int): Total required skills from the JD.

    Returns:
        str: A short feedback paragraph.
    """
    display_name = name if name and name != "Not found" else "This candidate"

    return (
        f"{display_name} achieved a Resume Match Score of {percentage}% "
        f"({matched_count} of {total_required} required skills matched), "
        f"placing them in the \"{star_label}\" tier. "
        f"Based on this analysis, the recommendation is \"{recommendation_label}\"."
    )


# --------------------------------------------------------------------------
# COMBINED INSIGHTS BUILDER
# --------------------------------------------------------------------------

def build_candidate_insights(result: dict, resume_text: str, jd_text: str, profile: dict) -> dict:
    """
    Combine every insight above into a single dict, ready to be merged
    into an existing analyzer.py result dict without altering any of
    its original keys.

    Args:
        result (dict): Output of analyzer.analyze_resume_against_skills
            (or analyze_resume) for this candidate.
        resume_text (str): Raw Resume text.
        jd_text (str): Raw Job Description text.
        profile (dict): Output of extraction.extract_candidate_profile
            for this candidate.

    Returns:
        dict: All computed insight fields, meant to be merged with
              `result` via `{**result, **insights}`.
    """
    stars = star_rating(result["percentage"])
    ats_score = ats_compatibility_score(
        resume_text, result["resume_skills"], profile["email"], profile["phone"]
    )
    readiness = interview_readiness_score(result["percentage"], ats_score, result["matched_count"])
    final_rec = final_recommendation(result["percentage"])
    gap = skill_gap_analysis(resume_text, jd_text, result["matched"], result["missing"])

    strengths = generate_strengths(result["matched"], ats_score, profile["education_level"])
    weaknesses = generate_weaknesses(gap["missing"], gap["critical_missing"], ats_score)
    feedback = generate_overall_feedback(
        profile["name"], result["percentage"], final_rec["label"],
        stars["label"], result["matched_count"], result["total_required"]
    )

    return {
        "star_rating": stars,
        "skill_strength": skill_strength_rating(result["matched_count"]),
        "experience_rating": experience_rating(profile["experience_years"]),
        "education_rating": education_rating(profile["education_level"]),
        "ats_score": ats_score,
        "interview_readiness": readiness,
        "final_recommendation": final_rec,
        "skill_gap": gap,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "overall_feedback": feedback,
    }
