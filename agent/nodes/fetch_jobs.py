"""Node: fetch all job listings from configured companies.

Dispatches to the correct fetcher based on each company's 'ats' field,
normalises results to JobListing schema, and accumulates non-fatal errors.
"""

from agent.state import AgentState
from fetchers.greenhouse import GreenhouseFetcher
from fetchers.html_scraper import HtmlScraper
from fetchers.lever import LeverFetcher


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
    raw_listings: list[dict] = []
    errors: list[str] = list(state.get("errors", []))

    for company in state["companies"]:
        try:
            ats = company.get("ats", "")
            if ats == "greenhouse":
                fetcher = GreenhouseFetcher()
            elif ats == "lever":
                fetcher = LeverFetcher()
            else:
                fetcher = HtmlScraper()
            listings = fetcher.fetch(company)
            raw_listings.extend(listings)
        except Exception as e:
            errors.append(f"{company['name']}: {e}")

    return {"raw_listings": raw_listings, "errors": errors}
