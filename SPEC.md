# Job Search Agent — Software Specification

## Overview

A daily job search agent built with LangGraph that scrapes target company career pages, scores job listings for relevance using an LLM, delivers a digest email with apply links, and learns over time from application outcomes. Designed as both a functional job search tool and a portfolio demonstration of end-to-end AI agent development with CI/CD.

---

## Goals

1. Surface relevant job listings from target companies daily with direct apply links
2. Score and filter listings using LLM-based relevance matching
3. Deliver results via email digest to the user's inbox
4. Log applications and outcomes to enable self-improving scoring over time
5. Demonstrate end-to-end AI agent architecture for portfolio purposes
6. Run automatically via CI/CD with zero manual intervention

---

## Stack & Technology Decisions

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Agent framework | LangGraph | Portfolio demo target, Python-native, integrates with LangChain ecosystem |
| LLM provider | Google Gemini 2.0 Flash | Free tier (1,500 req/day), sufficient for scoring ~50 jobs/day |
| LLM SDK | LangChain `ChatGoogleGenerativeAI` | Clean LangGraph integration, provider-swappable |
| Job data source | Direct company career pages | Fresher data than aggregators, Greenhouse/Lever have free JSON APIs |
| Email delivery | Gmail SMTP + App Password | Free, no third-party account needed, sufficient for 1 email/day |
| Database | SQLite | Zero infrastructure, built into Python stdlib, queryable |
| CI/CD | GitHub Actions | Free tier, native GitHub integration |
| Dev environment | GitHub Codespaces | Free (60 hrs/month), consistent environment, portfolio demo target |
| Secrets management | .env locally, GitHub Secrets in CI, Codespaces Secrets in dev | Standard pattern, nothing hardcoded |

**Total infrastructure cost: $0**

---

## Environment Variables

All secrets loaded via `python-dotenv` in `config/settings.py`. Never hardcoded.

```bash
# .env.example — committed to repo as template
GEMINI_API_KEY=           # Google AI Studio free tier key
GMAIL_ADDRESS=            # sender Gmail address
GMAIL_APP_PASSWORD=       # 16-char App Password (Google Account → Security → 2FA → App Passwords)
DIGEST_EMAIL=             # recipient address (can be same as GMAIL_ADDRESS)
SCORE_THRESHOLD=6         # minimum fit score (1-10) to include in digest
DB_PATH=data/jobs.db      # path to SQLite database (change per environment)
```

### DB_PATH Per Environment

| Environment | DB_PATH value | Set in |
|-------------|--------------|--------|
| Local machine | `data/jobs.db` | `.env` |
| GitHub Actions | `data/demo.db` | workflow `env:` block |
| Codespaces | `data/demo.db` | `devcontainer.json` remoteEnv |

---

## Project Structure

```
job-search-agent/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # lint + test on every push/PR
│       └── weekly_agent.yml        # cron: 8am UTC every Monday
│
├── .devcontainer/
│   └── devcontainer.json           # Codespaces: Python 3.11, DB_PATH=data/demo.db
│
├── agent/
│   ├── __init__.py
│   ├── graph.py                    # LangGraph graph definition + edge logic
│   ├── state.py                    # AgentState TypedDict
│   └── nodes/
│       ├── __init__.py
│       ├── fetch_jobs.py           # node: fetch all companies via fetchers
│       ├── deduplicate.py          # node: filter already-seen job IDs
│       ├── score_filter.py         # node: Gemini relevance scoring
│       └── format_report.py        # node: build HTML email digest
│
├── fetchers/
│   ├── __init__.py
│   ├── base.py                     # abstract BaseFetcher class
│   ├── greenhouse.py               # Greenhouse JSON API fetcher
│   ├── lever.py                    # Lever JSON API fetcher
│   └── html_scraper.py             # BeautifulSoup fallback for Workday/custom
│
├── learning/
│   ├── __init__.py
│   ├── graph.py                    # separate LangGraph graph for weekly learning
│   └── nodes/
│       ├── load_feedback.py        # load applications + outcomes from DB
│       ├── analyze_patterns.py     # Gemini analyzes what applied jobs had in common
│       └── update_prompt.py        # rewrites config/scoring_prompt.txt
│
├── config/
│   ├── companies.yaml              # target companies, ATS type, roles
│   ├── settings.py                 # loads all env vars via python-dotenv
│   └── scoring_prompt.txt          # current scoring prompt (auto-updated by learning pipeline)
│
├── notifications/
│   ├── __init__.py
│   └── email.py                    # Gmail SMTP HTML digest sender
│
├── database/
│   ├── __init__.py
│   └── db.py                       # SQLite wrapper: init_db(), insert_jobs(), log_application(), etc.
│
├── cli/
│   ├── __init__.py
│   └── log.py                      # CLI for logging applications and outcomes
│
├── data/
│   ├── jobs.db                     # GITIGNORED — real application data
│   └── demo.db                     # COMMITTED — seeded with realistic fake data
│
├── tests/
│   ├── __init__.py
│   ├── test_fetchers.py
│   ├── test_nodes.py
│   ├── test_graph.py
│   └── fixtures/
│       └── sample_listings.json
│
├── dashboard/
│   └── app.py                      # Streamlit dashboard (Codespaces port 8501)
│
├── .env.example
├── .gitignore                      # includes .env, data/jobs.db
├── requirements.txt
├── requirements-dev.txt            # pytest, ruff, mypy
├── Makefile
└── README.md
```

---

## LangGraph Agent State

```python
# agent/state.py
class AgentState(TypedDict):
    companies: list[dict]        # loaded from companies.yaml at graph entry
    raw_listings: list[dict]     # all fetched jobs, unnormalized
    deduplicated: list[dict]     # new jobs only (not already in DB)
    scored_jobs: list[dict]      # each job + fit_score (1-10) + reason string
    report: str                  # final HTML digest string
    errors: list[str]            # non-fatal per-node errors
```

---

## Daily Agent Pipeline

```
START
  │
[fetch_jobs]
  - Loops over companies in companies.yaml
  - Dispatches to correct fetcher based on ats: field
  - Normalizes all results to JobListing schema
  - Logs non-fatal errors per company to state.errors
  │
[deduplicate]
  - Loads seen job IDs from SQLite
  - Filters raw_listings to only new jobs
  - Writes new job IDs to DB
  │
[score_filter]
  - Batches all deduplicated jobs into a single Gemini prompt
  - Prompt loaded from config/scoring_prompt.txt
  - Returns score (1-10) + reason per job
  - Filters to scored_jobs where score >= SCORE_THRESHOLD
  │
  ▼ (conditional: if scored_jobs empty → format_report with "no new matches")
  │
[format_report]
  - Builds HTML email grouped by tier
  - Each job: title, company, score, reason, apply link
  - Errors from state.errors appear in email footer
  │
Gmail SMTP → digest to DIGEST_EMAIL
  │
END
```

---

## Weekly Learning Pipeline

Separate LangGraph graph, weekly cron (Monday 8am UTC).

```
START
  │
[load_feedback]     — queries SQLite for all applications + outcomes
  │
[analyze_patterns]  — Gemini analyzes patterns: what applied/responded jobs had in common
  │
[update_prompt]     — rewrites config/scoring_prompt.txt with refined criteria
  │
END
```

---

## Fetcher Strategy

| ATS | Companies | Method |
|-----|-----------|--------|
| Greenhouse | Stripe, Datadog, GitLab, HubSpot, Klaviyo, DraftKings | `GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs` — free JSON, no auth |
| Lever | Toast, Wayfair | `GET https://api.lever.co/v0/postings/{slug}?mode=json` — free JSON, no auth |
| Workday/custom | Honeywell, GE Vernova, Eversource | BeautifulSoup HTML scraper — non-fatal on failure |
| Unknown | Amazon, Uber | Verify ATS, default to scraper |

### BaseFetcher Interface

```python
class BaseFetcher(ABC):
    def fetch(self, company: dict) -> list[JobListing]: ...
    def normalize(self, raw: dict) -> JobListing: ...
```

### JobListing Schema

```python
class JobListing(TypedDict):
    job_id: str          # stable ATS ID — used for deduplication
    company: str
    title: str
    location: str
    url: str             # direct apply link
    posted_date: str
    description: str     # used for LLM scoring
    tier: int            # 1-4 from companies.yaml
    ats: str             # greenhouse | lever | scraper
```

---

## companies.yaml

```yaml
companies:
  - name: Stripe
    tier: 1
    ats: greenhouse
    ats_slug: stripe
    target_roles: ["Staff Data Scientist", "ML Engineer", "Data Scientist"]

  - name: GitLab
    tier: 1
    ats: greenhouse
    ats_slug: gitlab
    target_roles: ["Senior Data Scientist", "Staff Data Scientist"]

  - name: Datadog
    tier: 1
    ats: greenhouse
    ats_slug: datadog
    target_roles: ["Senior Data Scientist", "Staff Data Scientist", "ML Engineer"]

  - name: Snowflake
    tier: 1
    ats: greenhouse
    ats_slug: snowflake
    target_roles: ["Principal Data Scientist", "Senior Data Scientist"]

  - name: Databricks
    tier: 1
    ats: greenhouse
    ats_slug: databricks
    target_roles: ["Senior Data Scientist", "Staff Data Scientist"]

  - name: HubSpot
    tier: 2
    ats: greenhouse
    ats_slug: hubspot
    target_roles: ["Principal Data Scientist", "Senior Data Scientist"]

  - name: Klaviyo
    tier: 2
    ats: greenhouse
    ats_slug: klaviyo
    target_roles: ["Senior Data Scientist", "Staff Data Scientist"]

  - name: DraftKings
    tier: 2
    ats: greenhouse
    ats_slug: draftkings
    target_roles: ["Senior Data Scientist"]

  - name: Toast
    tier: 2
    ats: lever
    ats_slug: toast
    target_roles: ["Principal Data Scientist", "Senior Data Scientist"]

  - name: Wayfair
    tier: 2
    ats: lever
    ats_slug: wayfair
    target_roles: ["Principal Data Scientist"]

  - name: Honeywell
    tier: 3
    ats: workday
    careers_url: "https://careers.honeywell.com"
    target_roles: ["Principal Data Scientist", "Industrial AI"]

  - name: GE Vernova
    tier: 3
    ats: workday
    careers_url: "https://jobs.gecareers.com/vernova"
    target_roles: ["Principal Data Scientist", "Energy Systems"]

  - name: Eversource
    tier: 3
    ats: workday
    careers_url: "https://jobs.eversource.com"
    target_roles: ["Principal Data Scientist", "Grid Analytics"]

  - name: Amazon
    tier: 4
    ats: scraper
    careers_url: "https://www.amazon.jobs"
    target_roles: ["OR Scientist", "Operations Research"]

  - name: Uber
    tier: 4
    ats: scraper
    careers_url: "https://www.uber.com/us/en/careers"
    target_roles: ["OR Scientist", "Marketplace Optimization"]
```

---

## Database Schema (SQLite)

```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT,
    url TEXT NOT NULL,
    posted_date TEXT,
    tier INTEGER,
    ats TEXT,
    fit_score INTEGER,
    score_reason TEXT,
    first_seen_date TEXT NOT NULL
);

CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(job_id),
    applied_date TEXT NOT NULL,
    outcome TEXT DEFAULT NULL,
    outcome_date TEXT DEFAULT NULL,
    notes TEXT DEFAULT NULL
);
```

Outcome values: `NULL` → `phone_screen` → `final_round` → `offer` / `rejected`

---

## Database Wrapper Interface

```python
# database/db.py
def init_db(db_path: str) -> None: ...
def is_seen(db_path: str, job_id: str) -> bool: ...
def insert_jobs(db_path: str, jobs: list[JobListing]) -> None: ...
def log_application(db_path: str, job_id: str) -> None: ...
def update_outcome(db_path: str, job_id: str, outcome: str) -> None: ...
def get_all_applications(db_path: str) -> list[dict]: ...
def get_stats(db_path: str) -> dict: ...
```

---

## Demo Database

`data/demo.db` is committed to the repo with realistic fake data:
- ~200 jobs surfaced, ~60 scored ≥ 6/10, 18 applications, 6 phone screens, 2 final rounds, 1 offer
- Used in Codespaces and GitHub Actions via `DB_PATH=data/demo.db`
- Real `data/jobs.db` is gitignored — never committed

Rationale: protects real application data (response rates, outcomes) from being visible to
potential employers who may review the portfolio repo.

---

## CI/CD Workflows

### ci.yml — every push and PR
```
checkout → setup Python 3.11 → pip install -r requirements-dev.txt →
ruff lint → mypy → pytest tests/
```

### weekly_agent.yml — Monday 8am UTC
```yaml
schedule: '0 8 * * 1'
env:
  DB_PATH: data/demo.db
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
  GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
  DIGEST_EMAIL: ${{ secrets.DIGEST_EMAIL }}
  SCORE_THRESHOLD: ${{ secrets.SCORE_THRESHOLD }}
```

GitHub Secrets required: `GEMINI_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `DIGEST_EMAIL`, `SCORE_THRESHOLD`

---

## Makefile Targets

```makefile
make run                               # run full daily agent pipeline locally
make learn                             # run weekly learning pipeline manually
make test                              # pytest
make lint                              # ruff + mypy
make apply JOB_ID=xxx                  # log a job application to DB
make outcome JOB_ID=xxx OUTCOME=phone_screen
make stats                             # print funnel summary from DB
make clean-today                       # rollback today's seen job IDs (re-run fresh)
make check-fetchers                    # test each fetcher, report failures
make seed-demo                         # regenerate data/demo.db with fake data
```

---

## Known Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| HTML scrapers break on site redesigns | Non-fatal errors, `make check-fetchers`, error summary in email footer |
| GitHub Actions IPs blocked by career sites | Realistic request headers, delays between requests, non-fatal fallback |
| Gemini rate limits (15 RPM free tier) | Batch all jobs into single prompt per run |
| Deduplication key instability | Use ATS job ID (stable), never title or URL |
| Real data visible in public repo | `data/jobs.db` gitignored, `demo.db` used in all public environments |
| Role title variation | LLM scoring handles fuzzy matching — do not use string comparison |

---

## Phased Build Order

| Phase | Deliverables |
|-------|-------------|
| 1 | Scaffold: `state.py`, `companies.yaml`, `settings.py`, `.env.example`, `.gitignore`, `Makefile` stubs |
| 2 | Database: `database/db.py`, SQLite schema init, `make seed-demo` |
| 3 | Fetchers: `base.py`, `greenhouse.py`, `lever.py`, `html_scraper.py` |
| 4 | Daily agent: `agent/graph.py` + all 4 nodes end-to-end |
| 5 | Notifications: `notifications/email.py`, Gmail SMTP, HTML template |
| 6 | CLI: `cli/log.py`, `make apply`, `make outcome`, `make stats` |
| 7 | Learning pipeline: `learning/` graph + 3 nodes, `config/scoring_prompt.txt` |
| 8 | CI/CD: `ci.yml`, `weekly_agent.yml`, `devcontainer.json` |
| 9 | Dashboard: `dashboard/app.py` Streamlit on Codespaces port 8501 |
| 10 | Polish: `README.md` with architecture diagram, seeded `demo.db` |
