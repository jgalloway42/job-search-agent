"""Streamlit dashboard for the job search agent.

Provides a visual overview of the job search funnel, application history,
and scoring prompt management. Runs on port 8501 in GitHub Codespaces.

Start with:
    streamlit run dashboard/app.py
"""



def render_stats_section() -> None:
    """Render the funnel summary section (jobs surfaced → offer).

    Displays key metrics as Streamlit metric cards. Data loaded from
    database.db.get_stats() using settings.DB_PATH.
    """
    pass


def render_applications_table() -> None:
    """Render a sortable table of all logged applications and outcomes.

    Loads data from database.db.get_all_applications() and displays
    as a Streamlit dataframe with columns: date, company, title,
    fit_score, outcome.
    """
    pass


def render_prompt_viewer() -> None:
    """Render the current scoring prompt with last-updated metadata.

    Reads config/scoring_prompt.txt and displays in a code block.
    Shows the file's last modified timestamp.
    """
    pass


def main() -> None:
    """Compose and run the full Streamlit dashboard application."""
    pass


if __name__ == "__main__":
    main()
