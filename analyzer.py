"""
analyzer.py
------------
Core Resume Analysis Logic for the Intelligent Resume Analyzer.

This module performs the entire comparison pipeline manually, without any
Artificial Intelligence, Machine Learning, or NLP libraries:

    1. Extract candidate "skill" keywords from the Resume text.
    2. Extract required "skill" keywords from the Job Description text.
    3. Compare the two sets of skills using built-in set operations.
    4. Identify Matched Skills, Missing Skills, and Additional Skills.
    5. Calculate the Resume Match Percentage.
    6. Generate a Candidate Recommendation based on the percentage.

Only Python's Standard Library is used (re, string, difflib, collections).
"""

import math

from utils import clean_text, tokenize


# --------------------------------------------------------------------------
# SKILL KEYWORD DATABASE
# --------------------------------------------------------------------------
# Since no NLP/ML libraries are allowed, skills are identified by matching
# cleaned resume/JD words against this manually curated reference list of
# common technical and professional skill keywords. This keeps the matching
# process fast, deterministic, and fully explainable (ideal for a college
# project demonstration).
#
# The list intentionally covers programming languages, frameworks, tools,
# databases, concepts, and common soft skills so that a wide range of
# sample resumes and job descriptions can be analyzed meaningfully.

SKILL_KEYWORDS = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c", "c++", "csharp", "c#",
    "php", "ruby", "swift", "kotlin", "go", "golang", "rust", "scala", "r",
    "matlab", "perl", "dart", "sql", "html", "css", "bash", "shell",

    # Web Development
    "react", "reactjs", "angular", "vue", "vuejs", "nodejs", "node", "express",
    "django", "flask", "fastapi", "spring", "springboot", "laravel", "bootstrap",
    "tailwind", "jquery", "rest", "restapi", "graphql", "webpack", "nextjs",

    # Data / AI / ML
    "machinelearning", "deeplearning", "artificialintelligence", "nlp",
    "computervision", "datascience", "dataanalysis", "dataanalytics",
    "pandas", "numpy", "scikitlearn", "tensorflow", "pytorch", "keras",
    "opencv", "tableau", "powerbi", "excel", "statistics", "bigdata",
    "hadoop", "spark", "kafka", "hive", "etl", "datawarehouse",

    # Databases
    "mysql", "postgresql", "postgres", "mongodb", "sqlite", "oracle",
    "redis", "cassandra", "database", "dbms", "firebase", "elasticsearch",

    # Cloud / DevOps
    "aws", "azure", "gcp", "cloudcomputing", "docker", "kubernetes",
    "jenkins", "git", "github", "gitlab", "cicd", "linux", "devops",
    "terraform", "ansible", "nginx", "microservices",

    # Software Engineering / CS Fundamentals
    "algorithms", "datastructures", "oop", "objectoriented", "systemdesign",
    "softwareengineering", "debugging", "testing", "unittesting", "agile",
    "scrum", "api", "networking", "operatingsystem", "compiler",
    "distributedsystems", "multithreading", "designpatterns",

    # Mobile Development
    "android", "ios", "flutter", "reactnative", "xamarin",

    # Tools
    "jira", "figma", "postman", "vscode", "intellij", "eclipse", "slack",
    "confluence", "trello",

    # Soft Skills
    "communication", "leadership", "teamwork", "problemsolving",
    "criticalthinking", "timemanagement", "adaptability", "creativity",
    "collaboration", "presentation", "negotiation", "mentoring",
    "projectmanagement", "analyticalskills", "decisionmaking",

    # Certifications / Concepts
    "certification", "security", "cybersecurity", "encryption",
    "blockchain", "iot", "automation", "analytics", "cloudsecurity",

    # QA / Testing (extension - additive, does not alter existing logic)
    "selenium", "cypress", "qa", "manualtesting", "automationtesting",
}


def _normalize_word(word: str) -> str:
    """
    Normalize a single word so that minor formatting differences (like
    hyphens, dots, or spaces inside multi-word tech terms) do not prevent
    a correct match. For example "scikit-learn" and "scikit learn" both
    normalize toward "scikitlearn".

    Args:
        word (str): A raw word token.

    Returns:
        str: Normalized word with non-alphanumeric characters removed.
    """
    return "".join(ch for ch in word if ch.isalnum())


def _build_candidate_tokens(text: str) -> set:
    """
    Build the full set of candidate tokens found in the given text,
    covering both single words (unigrams) and adjacent word pairs
    (bigrams). Bigrams are included so that two-word skill phrases in
    the reference database (e.g. "data structures", "machine learning",
    "problem solving") can still be detected even though the text is
    tokenized on whitespace.

    Args:
        text (str): Raw Resume or Job Description text.

    Returns:
        set: Normalized single-word and two-word (joined) tokens.
    """
    cleaned = clean_text(text)
    words = [w for w in tokenize(cleaned) if w.strip() != ""]

    candidates = set()

    # Unigrams (single words)
    for word in words:
        candidates.add(_normalize_word(word))

    # Bigrams (adjacent word pairs joined together) - catches two-word
    # skill phrases such as "data structures" -> "datastructures".
    for i in range(len(words) - 1):
        bigram = _normalize_word(words[i]) + _normalize_word(words[i + 1])
        candidates.add(bigram)

    return candidates


def extract_skills(text: str) -> set:
    """
    Extract skill keywords found in the given text by comparing
    normalized single-word and two-word candidate tokens against the
    SKILL_KEYWORDS reference database.

    Args:
        text (str): Raw Resume or Job Description text.

    Returns:
        set: Set of recognized skill keywords present in the text.
    """
    candidate_tokens = _build_candidate_tokens(text)

    found_skills = set()
    for skill in SKILL_KEYWORDS:
        normalized_skill = _normalize_word(skill)
        if normalized_skill in candidate_tokens:
            found_skills.add(skill)

    return found_skills


def compare_skills(resume_skills: set, jd_skills: set) -> dict:
    """
    Compare Resume skills against Job Description skills using fast,
    built-in set operations.

    Args:
        resume_skills (set): Skills extracted from the Resume.
        jd_skills (set): Skills extracted from the Job Description.

    Returns:
        dict: {
            "matched": set of skills present in both Resume and JD,
            "missing": set of skills required by JD but absent in Resume,
            "additional": set of skills present in Resume but not required by JD
        }
    """
    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills
    additional = resume_skills - jd_skills

    return {
        "matched": matched,
        "missing": missing,
        "additional": additional,
    }


def calculate_match_percentage(matched_count: int, total_required: int) -> int:
    """
    Calculate the Resume Match Percentage using the formula:

        Match % = (Matched Skills / Total Required Skills) * 100

    The result is rounded to the nearest whole number.

    Args:
        matched_count (int): Number of matched skills.
        total_required (int): Total number of skills required by the JD.

    Returns:
        int: Resume Match Percentage (0-100). Returns 0 if there are no
             required skills to avoid division by zero.
    """
    if total_required <= 0:
        return 0

    percentage = (matched_count / total_required) * 100
    # Use standard "round half up" rounding (e.g. 62.5 -> 63) instead of
    # Python's built-in round(), which uses banker's rounding and would
    # incorrectly round 62.5 down to 62.
    return math.floor(percentage + 0.5)


def get_recommendation(percentage: int) -> tuple:
    """
    Generate a candidate recommendation label and associated color code
    based on the Resume Match Percentage.

    Args:
        percentage (int): Resume Match Percentage (0-100).

    Returns:
        tuple: (recommendation_label: str, color_hex: str)
    """
    if percentage >= 90:
        return "Excellent Match", "#2e7d32"      # Green
    elif percentage >= 75:
        return "Good Match", "#66bb6a"            # Light Green
    elif percentage >= 60:
        return "Average Match", "#fbc02d"         # Yellow
    elif percentage >= 40:
        return "Needs Improvement", "#f57c00"     # Orange
    else:
        return "Poor Match", "#c62828"            # Red


def analyze_resume(resume_text: str, jd_text: str) -> dict:
    """
    Run the complete Resume Analysis pipeline from raw text to final result.

    Args:
        resume_text (str): Raw Resume text content.
        jd_text (str): Raw Job Description text content.

    Returns:
        dict: Complete analysis result containing matched/missing/additional
              skills, match percentage, and recommendation.
    """
    jd_skills = extract_skills(jd_text)
    return analyze_resume_against_skills(resume_text, jd_skills)


def analyze_resume_against_skills(resume_text: str, jd_skills: set) -> dict:
    """
    Run the Resume Analysis pipeline against an already-extracted set of
    Job Description skills. Used when comparing many resumes against the
    same Job Description, so the JD only needs to be processed once
    instead of being re-extracted for every resume (keeps batch
    comparisons fast and lightweight).

    Args:
        resume_text (str): Raw Resume text content.
        jd_skills (set): Skill keywords already extracted from the JD.

    Returns:
        dict: Complete analysis result containing matched/missing/additional
              skills, match percentage, and recommendation.
    """
    resume_skills = extract_skills(resume_text)
    comparison = compare_skills(resume_skills, jd_skills)

    matched_count = len(comparison["matched"])
    total_required = len(jd_skills)

    percentage = calculate_match_percentage(matched_count, total_required)
    recommendation, color = get_recommendation(percentage)

    return {
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "matched": sorted(comparison["matched"]),
        "missing": sorted(comparison["missing"]),
        "additional": sorted(comparison["additional"]),
        "matched_count": matched_count,
        "total_required": total_required,
        "percentage": percentage,
        "recommendation": recommendation,
        "color": color,
    }


def analyze_multiple_resumes(resume_texts: dict, jd_text: str) -> list:
    """
    Compare many resumes against a single Job Description in one batch.

    The Job Description is analyzed only once (its skill set is
    extracted a single time) and then reused for every resume, which
    keeps the comparison fast even for a large folder of resumes.

    Args:
        resume_texts (dict): Mapping of {filename: raw_resume_text}.
        jd_text (str): Raw Job Description text content.

    Returns:
        list: List of result dicts (see analyze_resume_against_skills),
              each with an added "resume_file" key, sorted by Resume
              Match Percentage from highest to lowest. Ties are broken
              alphabetically by filename for a stable, predictable order.
    """
    jd_skills = extract_skills(jd_text)

    results = []
    for filename, resume_text in resume_texts.items():
        result = analyze_resume_against_skills(resume_text, jd_skills)
        result["resume_file"] = filename
        results.append(result)

    results.sort(key=lambda r: (-r["percentage"], r["resume_file"].lower()))

    for rank, result in enumerate(results, start=1):
        result["rank"] = rank

    return results


def count_skill_occurrences(text: str, skills) -> dict:
    """
    Count how many times each given skill keyword appears in the text
    (as a unigram or bigram token). This is an additive helper used only
    for richer candidate insights (e.g. tiering a matched skill as
    "Excellent" vs "Average" based on how often it is emphasized in the
    Resume, or flagging a "Critical Missing" skill based on how often it
    is emphasized in the Job Description). It does not affect the core
    Match Percentage formula, matched/missing/additional sets, or the
    existing recommendation logic in any way - those are computed purely
    from set membership as before.

    Args:
        text (str): Raw Resume or Job Description text.
        skills: Iterable of skill keywords (from SKILL_KEYWORDS) to count.

    Returns:
        dict: {skill: occurrence_count} for every skill in `skills`.
              A skill absent from the text has a count of 0.
    """
    cleaned = clean_text(text)
    words = [w for w in tokenize(cleaned) if w.strip() != ""]

    normalized_words = [_normalize_word(w) for w in words]
    bigrams = [
        normalized_words[i] + normalized_words[i + 1]
        for i in range(len(normalized_words) - 1)
    ]

    counts = {}
    for skill in skills:
        normalized_skill = _normalize_word(skill)
        count = normalized_words.count(normalized_skill) + bigrams.count(normalized_skill)
        counts[skill] = count

    return counts
