"""
dashboard.py
-------------
Aggregation logic for the HR Dashboard: turns a batch of enriched
candidate result dicts (analyzer.py output + insights.py output +
extraction.py profile) into the KPI numbers and chart-ready data series
used by the Overview and Skill Gap tabs in ui.py.

Kept separate from ui.py so the aggregation math can be tested and
reasoned about independently of any Tkinter code. Only Python's
Standard Library (collections.Counter) is used.

Note on chart consolidation: the original feature list requested both
a "Skills Frequency Analysis" and a "Top 10 Most Common Skills" chart,
and both a "Candidate Ranking Chart" and a "Match Score Comparison"
chart. These pairs describe the same underlying data, so each pair is
served by a single chart (top skills frequency, and candidate ranking)
rather than drawing two identical charts side by side.
"""

from collections import Counter


SHORTLIST_THRESHOLD = 60  # Match % at or above this is considered "Shortlisted"


def compute_kpis(results: list, total_uploaded: int) -> dict:
    """
    Compute the KPI card values for the dashboard.

    Args:
        results (list): List of enriched candidate result dicts.
        total_uploaded (int): Total .txt files found in the selected
            folder, including any that were later skipped.

    Returns:
        dict: {
            "total_uploaded": int, "total_candidates": int,
            "shortlisted": int, "rejected": int,
            "average_score": int, "highest_score": int,
        }
    """
    total_candidates = len(results)
    scores = [r["percentage"] for r in results]

    shortlisted = sum(1 for s in scores if s >= SHORTLIST_THRESHOLD)
    rejected = total_candidates - shortlisted

    average_score = round(sum(scores) / total_candidates) if total_candidates else 0
    highest_score = max(scores) if scores else 0

    return {
        "total_uploaded": total_uploaded,
        "total_candidates": total_candidates,
        "shortlisted": shortlisted,
        "rejected": rejected,
        "average_score": average_score,
        "highest_score": highest_score,
    }


def score_distribution(results: list) -> tuple:
    """
    Bucket every candidate's Match Percentage into 5 fixed ranges.

    Args:
        results (list): List of enriched candidate result dicts.

    Returns:
        tuple: (labels, counts) - parallel lists ready for BarChart.
    """
    buckets = [("0-20%", 0, 20), ("21-40%", 21, 40), ("41-60%", 41, 60),
               ("61-80%", 61, 80), ("81-100%", 81, 100)]
    counts = [0] * len(buckets)

    for result in results:
        score = result["percentage"]
        for i, (_, low, high) in enumerate(buckets):
            if low <= score <= high:
                counts[i] += 1
                break

    labels = [label for label, _, _ in buckets]
    return labels, counts


def top_skills_frequency(results: list, top_n: int = 10) -> tuple:
    """
    Count how often each skill appears across every candidate's Resume
    (matched + additional skills, i.e. every skill actually detected in
    each Resume) and return the top N most common.

    Args:
        results (list): List of enriched candidate result dicts.
        top_n (int): Number of top skills to return.

    Returns:
        tuple: (labels, counts) - parallel lists, most frequent first.
    """
    counter = Counter()
    for result in results:
        detected_skills = set(result["matched"]) | set(result["additional"])
        counter.update(detected_skills)

    most_common = counter.most_common(top_n)
    labels = [skill.title() for skill, _ in most_common]
    counts = [count for _, count in most_common]
    return labels, counts


def candidate_ranking_chart_data(results: list, top_n: int = 10) -> tuple:
    """
    Build the data series for the Candidate Ranking / Match Score
    Comparison chart: the top N candidates by Match Percentage.

    Args:
        results (list): List of enriched candidate result dicts,
            already sorted by rank (highest score first).
        top_n (int): Number of top candidates to chart.

    Returns:
        tuple: (labels, values) - parallel lists.
    """
    top_results = results[:top_n]
    labels = [r["resume_file"] for r in top_results]
    values = [r["percentage"] for r in top_results]
    return labels, values


def experience_distribution(results: list) -> tuple:
    """
    Bucket every candidate's extracted experience rating into counts.

    Args:
        results (list): List of enriched candidate result dicts (each
            with a "profile" containing "experience_years").

    Returns:
        tuple: (labels, counts) - parallel lists.
    """
    order = ["Not specified", "Entry-Level (0-1 yrs)", "Junior (2-4 yrs)",
              "Mid-Level (5-7 yrs)", "Senior (8+ yrs)"]
    counter = Counter(r["insights"]["experience_rating"] for r in results)

    labels = [label.split(" (")[0] for label in order if counter.get(label, 0) > 0]
    counts = [counter[label] for label in order if counter.get(label, 0) > 0]
    return labels, counts


def education_distribution(results: list) -> tuple:
    """
    Count candidates by detected education level.

    Args:
        results (list): List of enriched candidate result dicts.

    Returns:
        tuple: (labels, counts) - parallel lists.
    """
    counter = Counter(r["profile"]["education_level"] for r in results)
    labels = list(counter.keys())
    counts = [counter[label] for label in labels]
    return labels, counts


def department_distribution(results: list) -> tuple:
    """
    Count candidates by guessed department.

    Args:
        results (list): List of enriched candidate result dicts.

    Returns:
        tuple: (labels, counts) - parallel lists, most common first.
    """
    counter = Counter(r["profile"]["department"] for r in results)
    most_common = counter.most_common()
    labels = [label for label, _ in most_common]
    counts = [count for _, count in most_common]
    return labels, counts


def shortlisted_vs_rejected(results: list) -> tuple:
    """
    Count candidates above/below the shortlist threshold.

    Args:
        results (list): List of enriched candidate result dicts.

    Returns:
        tuple: (labels, counts) - ["Shortlisted", "Rejected"].
    """
    shortlisted = sum(1 for r in results if r["percentage"] >= SHORTLIST_THRESHOLD)
    rejected = len(results) - shortlisted
    return ["Shortlisted", "Rejected"], [shortlisted, rejected]


def missing_skills_analysis(results: list, top_n: int = 10) -> tuple:
    """
    Count how often each skill is missing across every candidate, to
    highlight the JD requirements the current candidate pool most often
    lacks.

    Args:
        results (list): List of enriched candidate result dicts.
        top_n (int): Number of top missing skills to return.

    Returns:
        tuple: (labels, counts) - parallel lists, most common first.
    """
    counter = Counter()
    for result in results:
        counter.update(result["missing"])

    most_common = counter.most_common(top_n)
    labels = [skill.title() for skill, _ in most_common]
    counts = [count for _, count in most_common]
    return labels, counts
