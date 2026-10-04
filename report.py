"""
report.py
----------
Generates the downloadable HR candidate report as a plain CSV file
(readable by Excel, Google Sheets, etc.) using only Python's built-in
`csv` module.

Note on formatting: true Excel-native styling - cell background colors,
borders, conditional formatting, bold headings, auto-adjusted column
widths - requires a third-party library such as openpyxl, which this
project intentionally does not depend on (Standard Library only, no
pip installs). To stay professional within a plain-text CSV, this
report instead includes:
    - A company-style header block (title, generation date/time)
    - A summary statistics section (KPI totals)
    - A clearly laid out, fully-labeled candidate table, ranked
      highest to lowest, with every field the JD requested

Opening the resulting .csv in Excel and applying a header style/bold
row is a one-click manual step if the polished spreadsheet look is
needed; this file focuses on getting complete, correctly organized
data into the user's hands offline.
"""

import csv
import io

from utils import get_current_date, get_current_time
from dashboard import compute_kpis


def build_hr_report_rows(results: list, jd_file: str, total_uploaded: int) -> list:
    """
    Build the full set of rows for the HR candidate report, including
    the header block, summary statistics, and the candidate table.

    Args:
        results (list): List of enriched candidate result dicts (each
            with "profile" and "insights" sub-dicts already merged in).
        jd_file (str): Job Description filename used for this batch.
        total_uploaded (int): Total .txt files found in the folder
            (including any later skipped).

    Returns:
        list[list[str]]: Rows ready to be written with csv.writer.
    """
    kpis = compute_kpis(results, total_uploaded)

    rows = []
    rows.append(["INTELLIGENT RESUME ANALYZER - HR CANDIDATE REPORT"])
    rows.append([f"Job Description: {jd_file}"])
    rows.append([f"Generated: {get_current_date()} {get_current_time()}"])
    rows.append([])

    rows.append(["SUMMARY STATISTICS"])
    rows.append(["Total Resumes Uploaded", kpis["total_uploaded"]])
    rows.append(["Total Candidates Analyzed", kpis["total_candidates"]])
    rows.append(["Shortlisted Candidates", kpis["shortlisted"]])
    rows.append(["Rejected Candidates", kpis["rejected"]])
    rows.append(["Average Match Score", f"{kpis['average_score']}%"])
    rows.append(["Highest Match Score", f"{kpis['highest_score']}%"])
    rows.append([])

    rows.append(["CANDIDATE RANKING"])
    rows.append([
        "Rank", "Candidate Name", "Email", "Phone Number", "Resume File",
        "Resume Match Score", "Skills Found", "Missing Skills",
        "Strengths", "Weaknesses", "ATS Score", "Interview Readiness",
        "Recommendation", "Final Decision", "HR Feedback",
    ])

    for result in results:
        profile = result["profile"]
        insights = result["insights"]

        rows.append([
            result["rank"],
            profile["name"],
            profile["email"],
            profile["phone"],
            result["resume_file"],
            f"{result['percentage']}%",
            "; ".join(result["matched"]),
            "; ".join(result["missing"]),
            "; ".join(insights["strengths"]),
            "; ".join(insights["weaknesses"]),
            f"{insights['ats_score']}%",
            f"{insights['interview_readiness']}%",
            result["recommendation"],
            insights["final_recommendation"]["label"],
            insights["overall_feedback"],
        ])

    return rows


def format_hr_report_csv(results: list, jd_file: str, total_uploaded: int) -> str:
    """
    Render the full HR candidate report as CSV text.

    Args:
        results (list): List of enriched candidate result dicts.
        jd_file (str): Job Description filename used for this batch.
        total_uploaded (int): Total .txt files found in the folder.

    Returns:
        str: Complete CSV file content, ready to be written to disk.
    """
    rows = build_hr_report_rows(results, jd_file, total_uploaded)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    return buffer.getvalue()


def save_hr_report_csv(results: list, jd_file: str, total_uploaded: int, save_path: str) -> None:
    """
    Build and write the HR candidate report directly to a .csv file.

    Args:
        results (list): List of enriched candidate result dicts.
        jd_file (str): Job Description filename used for this batch.
        total_uploaded (int): Total .txt files found in the folder.
        save_path (str): Destination file path.
    """
    rows = build_hr_report_rows(results, jd_file, total_uploaded)

    with open(save_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
