"""Streamlit dashboard for the job search agent.

Provides a visual overview of the job search funnel, application history,
and scoring prompt management. Runs on port 8501 in GitHub Codespaces.

Start with:
    streamlit run dashboard/app.py
"""

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from database.db import get_all_applications, get_stats

DB_PATH = os.getenv("DB_PATH", "data/demo.db")
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "6"))
PROMPT_PATH = Path("config/scoring_prompt.txt")


def render_stats_section() -> None:
    """Render the funnel summary section (jobs surfaced → offer).

    Displays key metrics as Streamlit metric cards. Data loaded from
    database.db.get_stats() using settings.DB_PATH.
    """
    st.header("Funnel")
    try:
        stats = get_stats(DB_PATH)
    except Exception as e:
        st.error(f"Could not load stats: {e}")
        return

    cols = st.columns(7)
    labels = [
        ("Surfaced", stats["jobs_surfaced"]),
        ("Scored", stats["jobs_scored"]),
        (f"Qualified (≥{SCORE_THRESHOLD})", stats["jobs_qualified"]),
        ("Applied", stats["applied"]),
        ("Phone Screens", stats["phone_screens"]),
        ("Final Rounds", stats["final_rounds"]),
        ("Offers", stats["offers"]),
    ]
    for col, (label, value) in zip(cols, labels):
        col.metric(label, value)


def render_applications_table() -> None:
    """Render a sortable table of all logged applications and outcomes.

    Loads data from database.db.get_all_applications() and displays
    as a Streamlit dataframe with columns: date, company, title,
    fit_score, outcome.
    """
    st.header("Applications")
    try:
        rows = get_all_applications(DB_PATH)
    except Exception as e:
        st.error(f"Could not load applications: {e}")
        return

    if not rows:
        st.info("No applications logged yet.")
        return

    df = pd.DataFrame(rows)[["applied_date", "company", "title", "fit_score", "outcome", "url"]]
    df.columns = pd.Index(["Date", "Company", "Title", "Score", "Outcome", "URL"])
    df["Outcome"] = df["Outcome"].fillna("pending")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={"URL": st.column_config.LinkColumn("URL")},
    )


def render_prompt_viewer() -> None:
    """Render the current scoring prompt with last-updated metadata.

    Reads config/scoring_prompt.txt and displays in a code block.
    Shows the file's last modified timestamp.
    """
    st.header("Scoring Prompt")
    if not PROMPT_PATH.exists():
        st.warning("config/scoring_prompt.txt not found.")
        return

    mtime = datetime.fromtimestamp(PROMPT_PATH.stat().st_mtime)
    st.caption(f"Last updated: {mtime.strftime('%Y-%m-%d %H:%M')}")
    st.code(PROMPT_PATH.read_text(), language="text")


def main() -> None:
    """Compose and run the full Streamlit dashboard application."""
    st.set_page_config(page_title="Job Search Agent", layout="wide")
    st.title("Job Search Agent")
    st.caption(f"Database: `{DB_PATH}`")

    render_stats_section()
    st.divider()
    render_applications_table()
    st.divider()
    render_prompt_viewer()


if __name__ == "__main__":
    main()
