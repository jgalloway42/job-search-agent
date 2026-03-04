"""Seed data/demo.db with realistic fake job search data for portfolio demos.

Generates and inserts:
    - ~200 job listings across the configured companies (all tiers)
    - 18 logged applications with varying applied_dates
    - 6 phone screens, 2 final rounds, 1 offer, 4 rejections

Run via:
    make seed-demo
    python scripts/seed_demo.py

Always writes to data/demo.db (hardcoded for this script only — not settings.DB_PATH).
Drops and recreates all tables before inserting, so re-running is idempotent.
"""

import random
import sqlite3
from datetime import date, timedelta

DEMO_DB_PATH = "data/demo.db"

random.seed(42)

# ── Company definitions (mirrors companies.yaml) ──────────────────────────────

COMPANIES = [
    {"name": "Stripe",     "tier": 1, "ats": "greenhouse",
     "roles": ["Staff Data Scientist", "ML Engineer", "Data Scientist"]},
    {"name": "GitLab",     "tier": 1, "ats": "greenhouse",
     "roles": ["Senior Data Scientist", "Staff Data Scientist"]},
    {"name": "Datadog",    "tier": 1, "ats": "greenhouse",
     "roles": ["Senior Data Scientist", "Staff Data Scientist", "ML Engineer"]},
    {"name": "Snowflake",  "tier": 1, "ats": "greenhouse",
     "roles": ["Principal Data Scientist", "Senior Data Scientist"]},
    {"name": "Databricks", "tier": 1, "ats": "greenhouse",
     "roles": ["Senior Data Scientist", "Staff Data Scientist"]},
    {"name": "HubSpot",    "tier": 2, "ats": "greenhouse",
     "roles": ["Principal Data Scientist", "Senior Data Scientist"]},
    {"name": "Klaviyo",    "tier": 2, "ats": "greenhouse",
     "roles": ["Senior Data Scientist", "Staff Data Scientist"]},
    {"name": "DraftKings", "tier": 2, "ats": "greenhouse",
     "roles": ["Senior Data Scientist"]},
    {"name": "Toast",      "tier": 2, "ats": "lever",
     "roles": ["Principal Data Scientist", "Senior Data Scientist"]},
    {"name": "Wayfair",    "tier": 2, "ats": "lever",
     "roles": ["Principal Data Scientist"]},
    {"name": "Honeywell",  "tier": 3, "ats": "workday",
     "roles": ["Principal Data Scientist", "Industrial AI Engineer"]},
    {"name": "GE Vernova", "tier": 3, "ats": "workday",
     "roles": ["Principal Data Scientist", "Energy Systems Analyst"]},
    {"name": "Eversource", "tier": 3, "ats": "workday",
     "roles": ["Principal Data Scientist", "Grid Analytics Lead"]},
    {"name": "Amazon",     "tier": 4, "ats": "scraper",
     "roles": ["OR Scientist", "Operations Research Scientist"]},
    {"name": "Uber",       "tier": 4, "ats": "scraper",
     "roles": ["OR Scientist", "Marketplace Optimization Scientist"]},
]

LOCATIONS = [
    "Remote", "New York, NY", "San Francisco, CA", "Boston, MA",
    "Seattle, WA", "Austin, TX", "Chicago, IL", "Hybrid - NYC",
]

SCORE_REASONS = [
    "Strong match on causal inference and experimentation background.",
    "Excellent fit for ML platform work; Python and Spark experience align well.",
    "Good match but role skews more product analytics than applied ML.",
    "Deep alignment on NLP and recommendation systems work.",
    "Role requires more MLOps than research; partial technical match.",
    "Strong operations research background matches OR Scientist requirements.",
    "Energy sector experience not present; otherwise strong technical fit.",
    "Experimentation and A/B testing focus is a near-perfect match.",
    "Title likely IC4 equivalent — may represent a lateral move.",
    "Causal ML background directly matches stated job requirements.",
    "Insufficient seniority signal in the posting; apply anyway given tier.",
    "Heavy data engineering component; 60% DS 40% DE split per JD.",
]


# ── generate_jobs ─────────────────────────────────────────────────────────────


def generate_jobs() -> list[dict]:
    """Generate ~200 realistic fake job listings spread across all companies.

    Each listing has a stable fake job_id, realistic title drawn from
    target_roles in companies.yaml, plausible location, and a pre-assigned
    fit_score so the digest email renders without needing a real Gemini call.

    Returns:
        List of dicts matching the jobs table schema.
    """
    today = date.today()
    jobs = []
    job_num = 1

    for company in COMPANIES:
        # 13-14 jobs per company → ~200 total across 15 companies
        count = random.randint(12, 15)
        slug = str(company["name"]).lower().replace(" ", "-")

        for _ in range(count):
            role: str = random.choice(company["roles"])  # type: ignore[arg-type]
            location = random.choice(LOCATIONS)
            first_seen = today - timedelta(days=random.randint(0, 90))
            posted = first_seen - timedelta(days=random.randint(0, 7))

            # ~30% unscored (pipeline didn't run yet or was filtered early)
            if random.random() < 0.30:
                fit_score = None
                score_reason = None
            else:
                fit_score = random.randint(1, 10)
                score_reason = random.choice(SCORE_REASONS)

            jobs.append({
                "job_id": f"{company['ats']}-{slug}-{job_num:04d}",
                "company": company["name"],
                "title": role,
                "location": location,
                "url": f"https://example.com/jobs/{slug}/{job_num:04d}",
                "posted_date": posted.isoformat(),
                "tier": company["tier"],
                "ats": company["ats"],
                "fit_score": fit_score,
                "score_reason": score_reason,
                "first_seen_date": first_seen.isoformat(),
            })
            job_num += 1

    return jobs


# ── generate_applications ─────────────────────────────────────────────────────


def generate_applications(jobs: list[dict]) -> list[dict]:
    """Select 18 jobs from the generated set and produce application records.

    Assigns outcomes to simulate a realistic funnel:
        18 applied → 6 phone_screen → 2 final_round → 1 offer, 4 rejected

    Spreads applied_dates over the past 90 days.

    Args:
        jobs: The full list of generated job dicts (must include job_id).

    Returns:
        List of dicts matching the applications table schema.
    """
    today = date.today()

    # Apply to qualified jobs (fit_score >= 6) — same logic the real pipeline uses
    qualified = [j for j in jobs if j["fit_score"] is not None and j["fit_score"] >= 6]
    applied = random.sample(qualified, 18)

    # Sort by applied_date descending (most recent first) to look realistic
    applied_dates = sorted(
        [today - timedelta(days=random.randint(1, 90)) for _ in range(18)],
        reverse=True,
    )

    # Outcome assignment matching the target funnel:
    #   1 offer, 2 final_round, 6 phone_screen, 4 rejected, 5 None
    outcome_map = {
        0: "offer",
        1: "final_round",
        2: "final_round",
        3: "phone_screen",
        4: "phone_screen",
        5: "phone_screen",
        6: "phone_screen",
        7: "phone_screen",
        8: "phone_screen",
        9: "rejected",
        10: "rejected",
        11: "rejected",
        12: "rejected",
    }

    apps = []
    for i, job in enumerate(applied):
        applied_date = applied_dates[i]
        outcome = outcome_map.get(i)

        if outcome:
            days_after = random.randint(7, 45)
            outcome_date = (applied_date + timedelta(days=days_after)).isoformat()
        else:
            outcome_date = None

        apps.append({
            "job_id": job["job_id"],
            "applied_date": applied_date.isoformat(),
            "outcome": outcome,
            "outcome_date": outcome_date,
            "notes": None,
        })

    return apps


# ── seed ──────────────────────────────────────────────────────────────────────


def seed() -> None:
    """Drop all tables, recreate schema, and insert generated fake data.

    Always targets DEMO_DB_PATH (data/demo.db), never settings.DB_PATH.
    Prints a summary on completion.
    """
    jobs = generate_jobs()
    apps = generate_applications(jobs)

    with sqlite3.connect(DEMO_DB_PATH) as conn:
        conn.executescript("""
            DROP TABLE IF EXISTS applications;
            DROP TABLE IF EXISTS jobs;
            CREATE TABLE jobs (
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
            CREATE TABLE applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL REFERENCES jobs(job_id),
                applied_date TEXT NOT NULL,
                outcome TEXT DEFAULT NULL,
                outcome_date TEXT DEFAULT NULL,
                notes TEXT DEFAULT NULL
            );
        """)

        conn.executemany(
            """
            INSERT INTO jobs
                (job_id, company, title, location, url, posted_date,
                 tier, ats, fit_score, score_reason, first_seen_date)
            VALUES
                (:job_id, :company, :title, :location, :url, :posted_date,
                 :tier, :ats, :fit_score, :score_reason, :first_seen_date)
            """,
            jobs,
        )

        conn.executemany(
            """
            INSERT INTO applications (job_id, applied_date, outcome, outcome_date, notes)
            VALUES (:job_id, :applied_date, :outcome, :outcome_date, :notes)
            """,
            apps,
        )

    # Summary
    scored = sum(1 for j in jobs if j["fit_score"] is not None)
    qualified = sum(1 for j in jobs if j["fit_score"] is not None and j["fit_score"] >= 6)
    outcomes = [a["outcome"] for a in apps]

    print(f"Seeded {DEMO_DB_PATH}")
    print(f"  jobs_surfaced : {len(jobs)}")
    print(f"  jobs_scored   : {scored}")
    print(f"  jobs_qualified: {qualified}")
    print(f"  applied       : {len(apps)}")
    print(f"  phone_screens : {outcomes.count('phone_screen')}")
    print(f"  final_rounds  : {outcomes.count('final_round')}")
    print(f"  offers        : {outcomes.count('offer')}")
    print(f"  rejected      : {outcomes.count('rejected')}")


if __name__ == "__main__":
    seed()
