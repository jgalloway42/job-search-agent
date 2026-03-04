"""SQLite database wrapper for the job search agent.

All database access in this project goes through this module. Nodes and
CLI commands import these functions directly — they never import sqlite3.
The DB path always comes from settings.DB_PATH (loaded from env), never
hardcoded.

Schema:
    jobs         — all seen job listings with scores
    applications — logged applications and outcome tracking
"""

import sqlite3
from datetime import date
from typing import Any

from agent.state import JobListing


def init_db(db_path: str) -> None:
    """Create the database schema if it does not already exist.

    Creates the 'jobs' and 'applications' tables using IF NOT EXISTS,
    so it is safe to call on every startup.

    Schema:
        jobs(job_id PK, company, title, location, url, posted_date, tier,
             ats, fit_score, score_reason, first_seen_date)
        applications(id PK AUTOINCREMENT, job_id FK, applied_date, outcome,
                     outcome_date, notes)

    Args:
        db_path: Filesystem path to the SQLite database file. Will be
                 created if it does not exist.
    """
    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                url TEXT NOT NULL,
                posted_date TEXT,
                tier INTEGER,
                ats TEXT,
                fit_score INTEGER,
                score_reason TEXT,
                first_seen_date TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL REFERENCES jobs(job_id),
                applied_date TEXT NOT NULL,
                outcome TEXT DEFAULT NULL,
                outcome_date TEXT DEFAULT NULL,
                notes TEXT DEFAULT NULL
            );
        """)


def is_seen(db_path: str, job_id: str) -> bool:
    """Check whether a job ID has already been recorded in the database.

    Args:
        db_path: Path to the SQLite database file.
        job_id: The ATS job ID to look up.

    Returns:
        True if the job_id exists in the jobs table, False otherwise.
    """
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    return row is not None


def insert_jobs(db_path: str, jobs: list[JobListing]) -> None:
    """Insert new job listings into the database.

    Uses INSERT OR IGNORE to skip any job_id that already exists.
    Sets first_seen_date to the current UTC date (ISO format).

    Args:
        db_path: Path to the SQLite database file.
        jobs: List of JobListing dicts to insert. fit_score and
              score_reason are NULL at insert time; they are updated
              after LLM scoring if needed.
    """
    today = date.today().isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO jobs
                (job_id, company, title, location, url, posted_date, tier, ats, first_seen_date)
            VALUES
                (:job_id, :company, :title, :location, :url, :posted_date, :tier, :ats, :first_seen_date)
            """,
            [{**job, "first_seen_date": today} for job in jobs],
        )


def log_application(db_path: str, job_id: str) -> None:
    """Record that the user applied to a job.

    Inserts a row into the applications table with applied_date set to
    today's UTC date and outcome set to NULL.

    Args:
        db_path: Path to the SQLite database file.
        job_id: The ATS job ID that was applied to. Must exist in the
                jobs table (foreign key).

    Raises:
        ValueError: If job_id does not exist in the jobs table.
    """
    if not is_seen(db_path, job_id):
        raise ValueError(f"job_id '{job_id}' not found in jobs table")
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO applications (job_id, applied_date) VALUES (?, ?)",
            (job_id, date.today().isoformat()),
        )


def update_outcome(db_path: str, job_id: str, outcome: str) -> None:
    """Update the outcome of a logged application.

    Valid outcome values: 'phone_screen', 'final_round', 'offer', 'rejected'.
    Sets outcome_date to today's UTC date.

    Args:
        db_path: Path to the SQLite database file.
        job_id: The ATS job ID whose outcome is being updated.
        outcome: One of: 'phone_screen', 'final_round', 'offer', 'rejected'.

    Raises:
        ValueError: If outcome is not one of the valid values.
        ValueError: If no application exists for this job_id.
    """
    valid = {"phone_screen", "final_round", "offer", "rejected"}
    if outcome not in valid:
        raise ValueError(f"Invalid outcome '{outcome}'. Must be one of: {valid}")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE applications
               SET outcome = ?, outcome_date = ?
             WHERE job_id = ?
            """,
            (outcome, date.today().isoformat(), job_id),
        )
    if cursor.rowcount == 0:
        raise ValueError(f"No application found for job_id '{job_id}'")


def get_all_applications(db_path: str) -> list[dict]:
    """Return all application rows joined with job metadata.

    Joins applications with jobs on job_id to include title, company,
    tier, fit_score, and score_reason alongside outcome data.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        List of dicts, one per application row. Empty list if no applications.
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT a.id, a.job_id, a.applied_date, a.outcome, a.outcome_date, a.notes,
                   j.company, j.title, j.tier, j.fit_score, j.score_reason, j.url
              FROM applications a
              JOIN jobs j USING (job_id)
             ORDER BY a.applied_date DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_stats(db_path: str) -> dict[str, Any]:
    """Return funnel summary statistics for the current database.

    Computes:
        - jobs_surfaced: total rows in jobs table
        - jobs_scored: rows with fit_score IS NOT NULL
        - jobs_qualified: rows with fit_score >= SCORE_THRESHOLD
        - applied: count of applications
        - phone_screens: count where outcome = 'phone_screen'
        - final_rounds: count where outcome = 'final_round'
        - offers: count where outcome = 'offer'

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Dict with the above keys and integer values.
    """
    from config.settings import SCORE_THRESHOLD

    with sqlite3.connect(db_path) as conn:
        def count(query, params=()):
            return conn.execute(query, params).fetchone()[0]

        return {
            "jobs_surfaced": count("SELECT COUNT(*) FROM jobs"),
            "jobs_scored":   count("SELECT COUNT(*) FROM jobs WHERE fit_score IS NOT NULL"),
            "jobs_qualified": count("SELECT COUNT(*) FROM jobs WHERE fit_score >= ?", (SCORE_THRESHOLD,)),
            "applied":       count("SELECT COUNT(*) FROM applications"),
            "phone_screens": count("SELECT COUNT(*) FROM applications WHERE outcome = 'phone_screen'"),
            "final_rounds":  count("SELECT COUNT(*) FROM applications WHERE outcome = 'final_round'"),
            "offers":        count("SELECT COUNT(*) FROM applications WHERE outcome = 'offer'"),
        }
