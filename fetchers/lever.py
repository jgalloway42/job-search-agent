"""Lever ATS fetcher using the public JSON API.

API endpoint (no auth required):
    GET https://api.lever.co/v0/postings/{slug}?mode=json

Returns a JSON array of posting objects directly (no wrapper).
"""


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
        pass

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
        pass
