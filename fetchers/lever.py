"""Lever ATS fetcher using the public JSON API.

API endpoint (no auth required):
    GET https://api.lever.co/v0/postings/{slug}?mode=json

Returns a JSON array of posting objects directly (no wrapper).
"""

from datetime import datetime, timezone

import requests

from agent.state import JobListing
from fetchers.base import BaseFetcher

LEVER_API_BASE = "https://api.lever.co/v0/postings/{slug}?mode=json"


class LeverFetcher(BaseFetcher):
    """Fetches job listings from the Lever public JSON API."""

    def fetch(self, company: dict) -> list[JobListing]:
        """Fetch all open jobs for a company from the Lever API.

        Calls GET /v0/postings/{ats_slug}?mode=json and normalises each
        posting object. Does not filter by target_roles.

        Args:
            company: Company config dict. Must include 'ats_slug', 'name',
                     and 'tier'.

        Returns:
            List of normalised JobListing dicts for all open positions.
        """
        url = LEVER_API_BASE.format(slug=company["ats_slug"])
        response = requests.get(url)
        response.raise_for_status()
        postings = response.json()
        return [
            {**self.normalize(posting), "company": company["name"], "tier": company["tier"]}
            for posting in postings
        ]

    def normalize(self, raw: dict) -> JobListing:
        """Normalize a single Lever posting record to JobListing schema.

        Lever posting record keys used:
            - id                      → job_id
            - text                    → title
            - categories.location     → location
            - hostedUrl               → url
            - createdAt               → posted_date (epoch ms → ISO string)
            - descriptionPlain or description → description

        Args:
            raw: A single posting dict from the Lever API array.

        Returns:
            Normalised JobListing dict. 'ats' is set to 'lever'.
            'company' and 'tier' are injected by the caller.
        """
        created_at = raw.get("createdAt", 0)
        if created_at:
            posted_date = (
                datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
                .date()
                .isoformat()
            )
        else:
            posted_date = ""

        return {
            "job_id": raw.get("id", ""),
            "company": "",
            "title": raw.get("text", ""),
            "location": (raw.get("categories") or {}).get("location", ""),
            "url": raw.get("hostedUrl", ""),
            "posted_date": posted_date,
            "description": raw.get("descriptionPlain") or raw.get("description") or "",
            "tier": 0,
            "ats": "lever",
        }
