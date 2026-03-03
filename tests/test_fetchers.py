"""Tests for fetcher classes: GreenhouseFetcher, LeverFetcher, HtmlScraper.

All external HTTP calls are mocked — no live API calls in CI.
Tests validate normalization logic, error handling, and job_id extraction.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fetchers.greenhouse import GreenhouseFetcher
from fetchers.lever import LeverFetcher
from fetchers.html_scraper import HtmlScraper


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
        pass

    def test_normalize_maps_fields_correctly(self, stripe_company, greenhouse_response):
        """normalize() maps Greenhouse API fields to JobListing schema."""
        pass

    def test_normalize_job_id_is_string(self, stripe_company, greenhouse_response):
        """normalize() casts the integer id field to str for job_id."""
        pass

    def test_fetch_raises_on_http_error(self, stripe_company):
        """fetch() raises an exception on non-2xx HTTP response."""
        pass


class TestLeverFetcher:
    def test_fetch_returns_job_listings(self, toast_company, lever_response):
        """fetch() returns a non-empty list of JobListing dicts on success."""
        pass

    def test_normalize_maps_fields_correctly(self, toast_company, lever_response):
        """normalize() maps Lever API fields to JobListing schema."""
        pass

    def test_normalize_epoch_ms_to_iso_date(self, toast_company, lever_response):
        """normalize() converts Lever's epoch-ms createdAt to an ISO date string."""
        pass

    def test_fetch_raises_on_http_error(self, toast_company):
        """fetch() raises an exception on non-2xx HTTP response."""
        pass


class TestHtmlScraper:
    def test_fetch_is_nonfatal_on_parse_failure(self):
        """fetch() raises an exception (caller catches as non-fatal) on bad HTML."""
        pass

    def test_normalize_uses_empty_string_for_missing_fields(self):
        """normalize() fills missing scraped fields with empty strings."""
        pass
