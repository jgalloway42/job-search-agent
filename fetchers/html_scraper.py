"""BeautifulSoup HTML scraper for Workday and custom career pages.

Used as a fallback for companies that do not offer a stable JSON API
(Workday, custom career pages). Non-fatal on failure — scraper breakage
due to site redesigns is expected and handled by the caller.

Each company's scraper logic may need to be tailored. The normalize()
method attempts a best-effort extraction of common HTML patterns.
"""

import requests
from bs4 import BeautifulSoup

from agent.state import JobListing
from fetchers.base import BaseFetcher


class HtmlScraper(BaseFetcher):
    """Scrapes job listings from HTML career pages using BeautifulSoup.

    Designed for Workday-hosted pages and other non-API career portals.
    Expected to be fragile — callers must treat all exceptions as non-fatal.
    """

    def fetch(self, company: dict) -> list[JobListing]:
        """Fetch job listings by scraping the company's careers_url.

        Sends a GET request to company['careers_url'], parses the HTML with
        BeautifulSoup, and attempts to extract job listings. The parsing
        logic is best-effort and site-specific.

        Args:
            company: Company config dict. Must include 'careers_url', 'name',
                     and 'tier'. Does not use 'ats_slug'.

        Returns:
            List of normalised JobListing dicts. May be empty or incomplete
            if the page structure is not recognised.

        Raises:
            requests.HTTPError: On non-2xx responses.
            Exception: On parse failures. Caller handles as non-fatal.
        """
        pass

    def normalize(self, raw: dict) -> JobListing:
        """Normalize a scraped job record to JobListing schema.

        Scraped records are free-form dicts assembled during HTML parsing.
        This method maps whatever fields were extracted to the canonical
        JobListing schema, using empty strings for missing fields.

        Note: job_id for scraped listings is typically constructed from
        a URL hash or a data attribute — not a guaranteed stable ID.

        Args:
            raw: Dict of extracted fields from HTML parsing.

        Returns:
            Normalised JobListing dict. 'ats' is set to 'scraper'.
        """
        pass
