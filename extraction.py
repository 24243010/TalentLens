"""
extraction.py
--------------
Best-effort extraction of structured candidate fields (Name, Email,
Phone Number, Department, Years of Experience, Education Level) from
plain-text Resumes.

Resumes in this project are unstructured .txt files, so every field
here is a heuristic guess based on regular expressions and simple
keyword rules - there is no guarantee of accuracy for every resume
format, and every function returns a clear "not found" style value
when nothing suitable is detected. No AI, Machine Learning, or NLP
libraries are used - only Python's built-in `re` module.
"""

import re


# --------------------------------------------------------------------------
# EMAIL / PHONE
# --------------------------------------------------------------------------

_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Matches common phone formats: optional country code, optional
# separators (space, dash, dot), 10-digit numbers, optional parentheses
# around an area code.
_PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(\d{2,4}\)[\s-]?)?\d{3,5}[\s-]?\d{3,4}[\s-]?\d{0,4}"
)


def extract_email(text: str) -> str:
    """
    Find the first email address in the given text.

    Args:
        text (str): Raw Resume text.

    Returns:
        str: The first email address found, or "Not found".
    """
    match = _EMAIL_PATTERN.search(text)
    return match.group(0) if match else "Not found"


def extract_phone(text: str) -> str:
    """
    Find the first plausible phone number in the given text. A match is
    only accepted if it contains at least 10 digits, to avoid mistaking
    short numbers (years, percentages, list numbering) for a phone
    number.

    Args:
        text (str): Raw Resume text.

    Returns:
        str: The first phone number found, or "Not found".
    """
    for match in _PHONE_PATTERN.finditer(text):
        digit_count = sum(ch.isdigit() for ch in match.group(0))
        if digit_count >= 10:
            return match.group(0).strip()
    return "Not found"


# --------------------------------------------------------------------------
# NAME
# --------------------------------------------------------------------------

def extract_name(text: str, fallback_filename: str = "") -> str:
    """
    Guess the candidate's name using the common resume convention of
    putting the full name on the very first non-empty line, as long as
    that line looks like a plausible name (short, mostly alphabetic, no
    email/phone/digits). Falls back to a cleaned-up version of the
    resume's filename if no suitable line is found.

    Args:
        text (str): Raw Resume text.
        fallback_filename (str): The resume's filename (without path),
            used as a fallback if no name-like first line is found.

    Returns:
        str: Best-effort candidate name.
    """
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Reject lines that look like emails, phone numbers, headers,
        # or are simply too long to plausibly be just a person's name.
        if "@" in line or any(ch.isdigit() for ch in line):
            break
        word_count = len(line.split())
        if 1 <= word_count <= 4 and len(line) <= 40:
            return line
        break

    if fallback_filename:
        name_guess = fallback_filename.rsplit(".", 1)[0]
        name_guess = re.sub(r"[_\-]+", " ", name_guess).strip()
        if name_guess:
            return name_guess.title()

    return "Not found"


# --------------------------------------------------------------------------
# EXPERIENCE (YEARS)
# --------------------------------------------------------------------------

_YEARS_PATTERN = re.compile(r"(\d{1,2})\s*\+?\s*(?:years|yrs)", re.IGNORECASE)


def extract_experience_years(text: str) -> int:
    """
    Best-effort estimate of total years of professional experience.

    Two strategies are tried, in order:
        1. Look for an explicit phrase like "5 years" or "3+ yrs" and
           take the largest number mentioned (a resume's own stated
           experience is the most reliable signal available).
        2. If no explicit phrase is found, look for date ranges such as
           "2020 - Present" or "2018-2020" in an Experience section and
           sum up the approximate span of each range.

    Args:
        text (str): Raw Resume text.

    Returns:
        int: Best-effort total years of experience. Returns 0 if no
             signal could be found (treated as "Not specified" by
             calling code).
    """
    explicit_matches = _YEARS_PATTERN.findall(text)
    if explicit_matches:
        return max(int(y) for y in explicit_matches)

    total_years = 0
    current_year = 2026  # Fixed reference year for deterministic, offline estimates.
    for match in re.finditer(
        r"((?:19|20)\d{2})\s*[-–to]+\s*(present|current|(?:19|20)\d{2})",
        text, re.IGNORECASE
    ):
        start_year = int(match.group(1))
        end_token = match.group(2).lower()
        end_year = current_year if end_token in ("present", "current") else int(end_token)
        if end_year >= start_year:
            total_years += (end_year - start_year)

    return total_years


# --------------------------------------------------------------------------
# EDUCATION LEVEL
# --------------------------------------------------------------------------

_EDUCATION_KEYWORDS = [
    ("PhD / Doctorate", ["phd", "ph.d", "doctorate"]),
    ("Master's Degree", ["master", "m.tech", "mtech", "m.e", "msc", "m.sc", "mba", "mca"]),
    ("Bachelor's Degree", ["bachelor", "b.tech", "btech", "b.e", "bsc", "b.sc", "bca", "be "]),
    ("Diploma", ["diploma"]),
]


def extract_education_level(text: str) -> str:
    """
    Guess the candidate's highest education level by searching for
    common degree keywords, checked from highest to lowest level so
    that a resume mentioning both "Bachelor's" and "Master's" is
    correctly classified by its highest qualification.

    Args:
        text (str): Raw Resume text.

    Returns:
        str: One of "PhD / Doctorate", "Master's Degree",
             "Bachelor's Degree", "Diploma", or "Not specified".
    """
    lowered = text.lower()
    for level_label, keywords in _EDUCATION_KEYWORDS:
        for keyword in keywords:
            if keyword in lowered:
                return level_label
    return "Not specified"


# --------------------------------------------------------------------------
# DEPARTMENT (based on which skill category dominates)
# --------------------------------------------------------------------------

DEPARTMENT_SKILL_MAP = {
    "Web / Full Stack Development": {
        "react", "reactjs", "angular", "vue", "vuejs", "nodejs", "node",
        "express", "django", "flask", "fastapi", "spring", "springboot",
        "laravel", "html", "css", "bootstrap", "tailwind", "jquery",
        "rest", "restapi", "graphql", "webpack", "nextjs",
    },
    "Data & Analytics": {
        "machinelearning", "deeplearning", "artificialintelligence", "nlp",
        "computervision", "datascience", "dataanalysis", "dataanalytics",
        "pandas", "numpy", "scikitlearn", "tensorflow", "pytorch", "keras",
        "opencv", "tableau", "powerbi", "statistics", "bigdata", "hadoop",
        "spark", "kafka", "hive", "etl", "datawarehouse",
    },
    "DevOps & Cloud": {
        "aws", "azure", "gcp", "cloudcomputing", "docker", "kubernetes",
        "jenkins", "gitlab", "cicd", "linux", "devops", "terraform",
        "ansible", "nginx", "microservices",
    },
    "Mobile Development": {
        "android", "ios", "flutter", "reactnative", "xamarin",
    },
    "Quality Assurance": {
        "testing", "unittesting", "selenium", "cypress", "qa",
        "manualtesting", "automationtesting",
    },
    "Software Engineering": {
        "algorithms", "datastructures", "oop", "objectoriented",
        "systemdesign", "softwareengineering", "debugging", "api",
        "networking", "operatingsystem", "compiler", "distributedsystems",
        "multithreading", "designpatterns",
    },
}


def guess_department(resume_skills) -> str:
    """
    Guess the candidate's department by finding which predefined skill
    category the Resume's detected skills overlap with the most.

    Args:
        resume_skills: Iterable of skill keywords detected in the Resume.

    Returns:
        str: The best-matching department name, or "General / Unspecified"
             if the Resume's skills don't clearly favor any one category.
    """
    resume_skill_set = set(resume_skills)

    best_department = "General / Unspecified"
    best_overlap = 0

    for department, department_skills in DEPARTMENT_SKILL_MAP.items():
        overlap = len(resume_skill_set & department_skills)
        if overlap > best_overlap:
            best_overlap = overlap
            best_department = department

    return best_department


# --------------------------------------------------------------------------
# COMBINED EXTRACTION
# --------------------------------------------------------------------------

def extract_candidate_profile(text: str, resume_skills, filename: str = "") -> dict:
    """
    Run every extraction heuristic and return a single combined profile
    for the candidate.

    Args:
        text (str): Raw Resume text.
        resume_skills: Iterable of skill keywords detected in the Resume.
        filename (str): The resume's filename, used as a name fallback.

    Returns:
        dict: {
            "name": str, "email": str, "phone": str,
            "department": str, "experience_years": int,
            "education_level": str
        }
    """
    return {
        "name": extract_name(text, fallback_filename=filename),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "department": guess_department(resume_skills),
        "experience_years": extract_experience_years(text),
        "education_level": extract_education_level(text),
    }
