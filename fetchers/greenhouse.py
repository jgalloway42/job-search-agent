"""Greenhouse ATS fetcher using the public JSON API.

API endpoint (no auth required):
    GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true

The 'content=true' parameter includes the full job description HTML,
which is required for LLM scoring.
"""

import requests

from agent.state import JobListing
from fetchers.base import BaseFetcher

GREENHOUSE_API_BASE = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"


class GreenhouseFetcher(BaseFetcher):
    """Fetches job listings from the Greenhouse public JSON API."""

    def fetch(self, company: dict) -> list[JobListing]:
        """Fetch all open jobs for a company from the Greenhouse API.

        Calls GET /v1/boards/{ats_slug}/jobs?content=true and normalises
        each result. Does not filter by target_roles — the LLM scoring
        step handles role matching.

        Args:
            company: Company config dict. Must include 'ats_slug', 'name',
                     and 'tier'.

        Returns:
            List of normalised JobListing dicts for all open positions.
        """
        pass

    def normalize(self, raw: dict) -> JobListing:
        """Normalize a single Greenhouse job record to JobListing schema.

        Greenhouse job record keys used:
            - id         → job_id (cast to str)
            - title      → title
            - location.name → location
            - absolute_url  → url
            - updated_at    → posted_date
            - content       → description (HTML, may be None)

        Args:
            raw: A single job dict from the Greenhouse API 'jobs' array.

        Returns:
            Normalised JobListing dict. 'ats' is set to 'greenhouse'.
            'company' and 'tier' must be injected by the caller (from
            the company config), as they are not in the API response.
        """
        pass
