# CLAUDE.md

This file provides guidance to Claude Code when working on this repository.

---

## Project Summary

A LangGraph-based job search agent that scrapes target company career pages daily, scores listings with Gemini 2.0 Flash, delivers a digest email with direct apply links, and self-improves from application outcome feedback. Built as both a functional job search tool and a portfolio demonstration of end-to-end AI agent CI/CD.

Full specification: see `SPEC.md`

---

## Architecture

```
agent/graph.py            — daily LangGraph pipeline (fetch → deduplicate → score → report)
learning/graph.py         — weekly LangGraph pipeline (feedback → analyze → update prompt)
fetchers/                 — Greenhouse JSON API, Lever JSON API, BeautifulSoup scraper
database/db.py            — SQLite wrapper (no ORM, raw sqlite3 stdlib)
notifications/email.py    — Gmail SMTP HTML digest
cli/log.py                — application + outcome logging
dashboard/app.py          — Streamlit UI (Codespaces port 8501)
config/companies.yaml     — target companies, ATS type, target roles
config/scoring_prompt.txt — active Gemini scoring prompt (auto-updated by learning pipeline)
config/settings.py        — all env var loading via python-dotenv
scripts/seed_demo.py      — one-off dev script: drops + recreates data/demo.db with fake data
```

---

## Core Conventions

### Stubs first
The developer writes all implementations. When scaffolding, create complete type signatures, docstrings, and `pass` bodies only. Do not implement logic unless explicitly asked.

### Non-fatal error handling
All node errors are non-fatal. Catch exceptions per company/job, append a message to `state["errors"]`, and continue. Never crash the full pipeline on a single company failure. Errors surface in the email footer.

### Deduplication key
Always use the ATS job ID (`job_id`) for deduplication. Never use title or URL — both can change.

### LLM calls
- Batch all jobs into a single Gemini prompt per run — never one API call per job
- Scoring prompt is always loaded from `config/scoring_prompt.txt` at runtime, never hardcoded
- Use `ChatGoogleGenerativeAI` from LangChain — not the raw `google-generativeai` SDK directly

### Database
- Use raw `sqlite3` from Python stdlib — no SQLAlchemy or other ORM
- All DB access goes through `database/db.py` — nodes never import `sqlite3` directly
- DB path always comes from `settings.DB_PATH` (loaded from `DB_PATH` env var)
- Never reference `data/jobs.db` or `data/demo.db` by name outside of `settings.py` and docs
- **Exception:** `scripts/seed_demo.py` hardcodes `data/demo.db` intentionally — it is a dev-only tool that always targets the demo database regardless of env

### Secrets
- Never hardcode secrets, paths, or magic strings
- All config via `config/settings.py` which loads from environment via `python-dotenv`
- See `.env.example` for all required variables

---

## Environment Variables

```bash
GEMINI_API_KEY        # Google AI Studio free tier
GMAIL_ADDRESS         # sender Gmail address
GMAIL_APP_PASSWORD    # 16-char Google App Password (not your real password)
DIGEST_EMAIL          # recipient address
SCORE_THRESHOLD       # int, default 6 — minimum fit score (1-10) to include in digest
DB_PATH               # data/jobs.db locally | data/demo.db in CI and Codespaces
```

---

## Database: Two Files

| File | Committed? | Used in |
|------|-----------|---------|
| `data/jobs.db` | NO — gitignored | Local development only |
| `data/demo.db` | YES | GitHub Actions + Codespaces |

The active database is always `settings.DB_PATH`. Do not reference file paths directly anywhere in code.

`demo.db` contains realistic fake data (200 jobs surfaced, 18 applications, 6 phone screens, 1 offer) for portfolio demo purposes. Real application data stays private on the developer's machine.

---

## LangGraph State

```python
class AgentState(TypedDict):
    companies: list[dict]      # loaded from companies.yaml
    raw_listings: list[dict]   # fetched, pre-dedup
    deduplicated: list[dict]   # new jobs only
    scored_jobs: list[dict]    # with fit_score + reason
    report: str                # final HTML email body
    errors: list[str]          # non-fatal runtime errors
```

---

## Fetcher Routing

Selected by `ats` field in `companies.yaml`:

| ats value | Fetcher class | API |
|-----------|--------------|-----|
| `greenhouse` | `GreenhouseFetcher` | `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs` |
| `lever` | `LeverFetcher` | `https://api.lever.co/v0/postings/{slug}?mode=json` |
| `workday` | `HtmlScraper` | BeautifulSoup, non-fatal on failure |
| `scraper` | `HtmlScraper` | BeautifulSoup, non-fatal on failure |

---

## Makefile Targets

```makefile
make run                                  # run daily agent locally
make learn                                # run weekly learning pipeline
make test                                 # pytest
make lint                                 # ruff + mypy
make apply JOB_ID=xxx                     # log an application
make outcome JOB_ID=xxx OUTCOME=phone_screen
make stats                                # print funnel summary
make clean-today                          # rollback today's seen IDs (re-run fresh)
make check-fetchers                       # test all fetchers, report failures
make seed-demo                            # regenerate data/demo.db
```

---

## CI/CD

- `ci.yml` — runs on every push/PR: lint → typecheck → pytest
- `weekly_agent.yml` — Monday 8am UTC, uses `DB_PATH=data/demo.db`
- `devcontainer.json` — sets `DB_PATH=data/demo.db` so Codespaces always uses demo data
- GitHub Secrets needed: `GEMINI_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `DIGEST_EMAIL`, `SCORE_THRESHOLD`

---

## Local Development Environment

### Virtual environment
The project uses a `.venv` at the repo root (Python 3.12, gitignored).

- **Codespaces / devcontainer:** venv is created automatically by `postCreateCommand`; VS Code activates it in every terminal via `python.defaultInterpreterPath`.
- **Local machine (first time):**
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements-dev.txt
  ```
- **Local machine (subsequent sessions):** `source .venv/bin/activate`

### Minimum `.env` for Phase 2+ (database work)
Only `DB_PATH` is required to run the database and CLI layers. Gemini/Gmail vars are needed from Phase 4/5 onward.
```bash
DB_PATH=data/jobs.db
```

---

## Testing Guidelines

- `tests/fixtures/sample_listings.json` — mock Greenhouse/Lever responses
- Mock all external HTTP calls — no live API calls in CI
- Mock Gemini — no real API key used in tests
- Mock Gmail SMTP — no real emails sent in tests
- Each node should be testable in isolation with mocked state input

### Implement → Test Loop

Follow this pattern for every function, every phase:

1. Read the stub docstring — it specifies the contract exactly
2. Implement the function
3. Run its specific test class: `pytest tests/test_db.py::TestInitDb -v`
4. Move to the next function

### Database tests (`tests/test_db.py`)

Use pytest's `tmp_path` fixture for all DB tests — gives a real isolated temp file, no mocking needed:

```python
@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path
```

Run a single class while implementing: `pytest tests/test_db.py::TestIsSeen -v`
Run all DB tests when done: `pytest tests/test_db.py -v`

### Node/graph tests (`tests/test_nodes.py`, `tests/test_graph.py`)

Use `unittest.mock.patch` to mock external calls:
- HTTP fetchers: `patch("fetchers.greenhouse.requests.get")`
- Gemini: `patch("langchain_google_genai.ChatGoogleGenerativeAI")`
- SMTP: `patch("smtplib.SMTP")`
- DB calls: pass `tmp_path`-based db_path through state

---

## Build Phase Reference

Work through phases in order. Do not proceed to next phase without developer confirmation.

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Scaffold — state, config, settings, gitignore, Makefile stubs | ✅ Done |
| 2 | Database — db.py, schema, seed-demo | ✅ Done |
| 3 | Fetchers — base, greenhouse, lever, html_scraper | Pending |
| 4 | Daily agent — graph.py + 4 nodes |
| 5 | Notifications — email.py, HTML template |
| 6 | CLI — log.py, apply/outcome/stats |
| 7 | Learning pipeline — learning/ graph + 3 nodes |
| 8 | CI/CD — workflows, devcontainer |
| 9 | Dashboard — Streamlit, port 8501 |
| 10 | Polish — README, architecture diagram, seeded demo.db |
