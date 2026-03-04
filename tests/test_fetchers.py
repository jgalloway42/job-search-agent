"""Tests for fetcher classes: GreenhouseFetcher, LeverFetcher, HtmlScraper.

All external HTTP calls are mocked — no live API calls in CI.
Tests validate normalization logic, error handling, and job_id extraction.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from fetchers.greenhouse import GreenhouseFetcher
from fetchers.html_scraper import HtmlScraper
from fetchers.lever import LeverFetcher

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def greenhouse_response() -> dict:
    """Load mock Greenhouse API response from fixtures."""
    with open(FIXTURES_DIR / "sample_listings.json") as f:
        data = json.load(f)
    return data["greenhouse"]


@pytest.fixture
def lever_response() -> list:
    """Load mock Lever API response from fixtures."""
    with open(FIXTURES_DIR / "sample_listings.json") as f:
        data = json.load(f)
    return data["lever"]


@pytest.fixture
def stripe_company() -> dict:
    """Sample company config for Stripe (Greenhouse)."""
    return {
        "name": "Stripe",
        "tier": 1,
        "ats": "greenhouse",
        "ats_slug": "stripe",
        "target_roles": ["Staff Data Scientist", "ML Engineer"],
    }


@pytest.fixture
def toast_company() -> dict:
    """Sample company config for Toast (Lever)."""
    return {
        "name": "Toast",
        "tier": 2,
        "ats": "lever",
        "ats_slug": "toast",
        "target_roles": ["Principal Data Scientist", "Senior Data Scientist"],
    }


class TestGreenhouseFetcher:
    def test_fetch_returns_job_listings(self, stripe_company, greenhouse_response):
        """fetch() returns a non-empty list of JobListing dicts on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = greenhouse_response
        mock_response.raise_for_status.return_value = None

        with patch("fetchers.greenhouse.requests.get", return_value=mock_response):
            fetcher = GreenhouseFetcher()
            result = fetcher.fetch(stripe_company)

        assert len(result) == 3
        assert all(isinstance(job, dict) for job in result)
        assert all("job_id" in job for job in result)

    def test_normalize_maps_fields_correctly(self, stripe_company, greenhouse_response):
        """normalize() maps Greenhouse API fields to JobListing schema."""
        fetcher = GreenhouseFetcher()
        raw = greenhouse_response["jobs"][0]
        result = fetcher.normalize(raw)

        assert result["job_id"] == "7812341"
        assert result["title"] == "Staff Data Scientist, Risk"
        assert result["location"] == "Remote, United States"
        assert result["url"] == "https://boards.greenhouse.io/stripe/jobs/7812341"
        assert result["posted_date"] == "2026-02-28T14:30:00.000Z"
        assert result["ats"] == "greenhouse"
        assert "<p>" in result["description"]

    def test_normalize_job_id_is_string(self, stripe_company, greenhouse_response):
        """normalize() casts the integer id field to str for job_id."""
        fetcher = GreenhouseFetcher()
        raw = greenhouse_response["jobs"][0]
        result = fetcher.normalize(raw)

        assert isinstance(result["job_id"], str)
        assert result["job_id"] == "7812341"

    def test_fetch_raises_on_http_error(self, stripe_company):
        """fetch() raises an exception on non-2xx HTTP response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")

        with patch("fetchers.greenhouse.requests.get", return_value=mock_response):
            fetcher = GreenhouseFetcher()
            with pytest.raises(requests.HTTPError):
                fetcher.fetch(stripe_company)

    def test_fetch_injects_company_and_tier(self, stripe_company, greenhouse_response):
        """fetch() injects company name and tier from company config."""
        mock_response = MagicMock()
        mock_response.json.return_value = greenhouse_response
        mock_response.raise_for_status.return_value = None

        with patch("fetchers.greenhouse.requests.get", return_value=mock_response):
            fetcher = GreenhouseFetcher()
            result = fetcher.fetch(stripe_company)

        assert all(job["company"] == "Stripe" for job in result)
        assert all(job["tier"] == 1 for job in result)


class TestLeverFetcher:
    def test_fetch_returns_job_listings(self, toast_company, lever_response):
        """fetch() returns a non-empty list of JobListing dicts on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = lever_response
        mock_response.raise_for_status.return_value = None

        with patch("fetchers.lever.requests.get", return_value=mock_response):
            fetcher = LeverFetcher()
            result = fetcher.fetch(toast_company)

        assert len(result) == 2
        assert all(isinstance(job, dict) for job in result)
        assert all("job_id" in job for job in result)

    def test_normalize_maps_fields_correctly(self, toast_company, lever_response):
        """normalize() maps Lever API fields to JobListing schema."""
        fetcher = LeverFetcher()
        raw = lever_response[0]
        result = fetcher.normalize(raw)

        assert result["job_id"] == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert result["title"] == "Principal Data Scientist"
        assert result["location"] == "Boston, MA"
        assert result["url"] == "https://jobs.lever.co/toast/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert result["ats"] == "lever"
        assert "Principal Data Scientist" in result["description"]

    def test_normalize_epoch_ms_to_iso_date(self, toast_company, lever_response):
        """normalize() converts Lever's epoch-ms createdAt to an ISO date string."""
        fetcher = LeverFetcher()
        raw = lever_response[0]  # createdAt: 1740700800000
        result = fetcher.normalize(raw)

        assert result["posted_date"] == "2025-02-28"

    def test_fetch_raises_on_http_error(self, toast_company):
        """fetch() raises an exception on non-2xx HTTP response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("403")

        with patch("fetchers.lever.requests.get", return_value=mock_response):
            fetcher = LeverFetcher()
            with pytest.raises(requests.HTTPError):
                fetcher.fetch(toast_company)

    def test_fetch_injects_company_and_tier(self, toast_company, lever_response):
        """fetch() injects company name and tier from company config."""
        mock_response = MagicMock()
        mock_response.json.return_value = lever_response
        mock_response.raise_for_status.return_value = None

        with patch("fetchers.lever.requests.get", return_value=mock_response):
            fetcher = LeverFetcher()
            result = fetcher.fetch(toast_company)

        assert all(job["company"] == "Toast" for job in result)
        assert all(job["tier"] == 2 for job in result)


class TestHtmlScraper:
    def test_fetch_is_nonfatal_on_parse_failure(self):
        """fetch() raises an exception (caller catches as non-fatal) on bad HTML."""
        company = {"name": "Acme", "tier": 3, "ats": "scraper", "careers_url": "https://example.com/careers"}
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500")

        with patch("fetchers.html_scraper.requests.get", return_value=mock_response):
            scraper = HtmlScraper()
            with pytest.raises(requests.HTTPError):
                scraper.fetch(company)

    def test_normalize_uses_empty_string_for_missing_fields(self):
        """normalize() fills missing scraped fields with empty strings."""
        scraper = HtmlScraper()
        result = scraper.normalize({})

        assert result["job_id"] == ""
        assert result["title"] == ""
        assert result["location"] == ""
        assert result["url"] == ""
        assert result["posted_date"] == ""
        assert result["description"] == ""
        assert result["ats"] == "scraper"

    def test_normalize_generates_job_id_from_url(self):
        """normalize() generates a stable job_id from the URL hash."""
        scraper = HtmlScraper()
        raw = {"title": "Engineer", "url": "https://example.com/jobs/123", "location": "Remote", "description": ""}
        result = scraper.normalize(raw)

        assert result["job_id"] != ""
        assert len(result["job_id"]) == 32  # md5 hex digest length

    def test_fetch_returns_listings_from_html(self):
        """fetch() parses anchor tags from HTML and returns JobListing dicts."""
        company = {"name": "Acme", "tier": 3, "ats": "scraper", "careers_url": "https://example.com/careers"}
        html = """
        <html><body>
          <ul>
            <li><a href="/jobs/100">Senior Data Scientist</a></li>
            <li><a href="/jobs/101">ML Engineer, Recommendations</a></li>
          </ul>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status.return_value = None

        with patch("fetchers.html_scraper.requests.get", return_value=mock_response):
            scraper = HtmlScraper()
            result = scraper.fetch(company)

        assert len(result) == 2
        assert result[0]["title"] == "Senior Data Scientist"
        assert result[0]["company"] == "Acme"
        assert result[0]["tier"] == 3
        assert result[0]["ats"] == "scraper"
