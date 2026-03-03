"""Abstract base class for all job listing fetchers."""

from abc import ABC, abstractmethod

from agent.state import JobListing


class BaseFetcher(ABC):
    """Abstract interface that all ATS-specific fetchers must implement.

    Subclasses handle one ATS type (Greenhouse, Lever, HTML scraper) and
    are responsible for fetching raw data from the source and normalising
    it into the canonical JobListing schema.

    Error handling:
        Callers (fetch_jobs node) wrap each fetch() call in a try/except
        and append errors to state['errors']. Fetchers may raise freely —
        they should not suppress their own exceptions.
    """

    @abstractmethod
    def fetch(self, company: dict) -> list[JobListing]:
        """Fetch all job listings for a given company configuration.

        Args:
            company: Company config dict from companies.yaml. Keys vary by
                     ATS type: may include 'ats_slug', 'careers_url',
                     'target_roles', 'tier', 'name', 'ats'.

        Returns:
            List of normalized JobListing dicts. May be empty if no open
            positions match target roles or if the source returns no data.

        Raises:
            requests.HTTPError: On non-2xx API responses.
            Exception: Any other fetch or parse failure. Caller handles.
        """
        pass

    @abstractmethod
    def normalize(self, raw: dict) -> JobListing:
        """Normalize a single raw ATS response record to the JobListing schema.

        Args:
            raw: A single job object from the ATS API JSON or HTML parse result.

        Returns:
            A JobListing TypedDict with all required fields populated.
            Use empty string for optional fields that are missing in the source.
        """
        pass
