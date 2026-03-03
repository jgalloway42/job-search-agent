"""State definitions for the job search agent LangGraph pipeline."""

from typing import TypedDict


class JobListing(TypedDict):
    """Normalized job listing schema used across all fetchers and pipeline nodes.

    The job_id field is the stable ATS identifier and is the canonical
    deduplication key. Never use title or url for deduplication.
    """

    job_id: str       # stable ATS ID — used for deduplication
    company: str
    title: str
    location: str
    url: str          # direct apply link
    posted_date: str
    description: str  # full text used for LLM scoring
    tier: int         # 1-4 from companies.yaml
    ats: str          # greenhouse | lever | workday | scraper


class AgentState(TypedDict):
    """Shared mutable state passed between all nodes in the daily agent pipeline.

    Each node receives the full state and returns a partial dict with only
    the keys it modified. LangGraph merges the updates automatically.
    """

    companies: list[dict]       # loaded from companies.yaml at graph entry
    raw_listings: list[dict]    # all fetched jobs, pre-deduplication
    deduplicated: list[dict]    # new jobs only (not already in DB)
    scored_jobs: list[dict]     # each job dict extended with fit_score + reason
    report: str                 # final HTML digest string
    errors: list[str]           # non-fatal per-company/per-job error messages
