"""Node: fetch all job listings from configured companies.

Dispatches to the correct fetcher based on each company's 'ats' field,
normalises results to JobListing schema, and accumulates non-fatal errors.
"""

from agent.state import AgentState


def fetch_jobs(state: AgentState) -> dict:
    """Fetch job listings from all companies in state['companies'].

    For each company, selects the appropriate fetcher:
        - ats == 'greenhouse' → GreenhouseFetcher
        - ats == 'lever'      → LeverFetcher
        - ats == 'workday'    → HtmlScraper
        - ats == 'scraper'    → HtmlScraper

    Non-fatal errors are caught per company and appended to state['errors'].
    The pipeline continues even if individual companies fail.

    Args:
        state: Current agent state with 'companies' populated from companies.yaml.

    Returns:
        Partial state dict with 'raw_listings' and 'errors' keys updated.
    """
    pass
