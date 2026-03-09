[![CI](https://github.com/jgalloway42/job-search-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/jgalloway42/job-search-agent/actions/workflows/ci.yml)

# job-search-agent

A self-improving LangGraph agent that monitors target company career pages daily, scores job listings for relevance using Google Gemini, and delivers a digest email with direct apply links. Logs application outcomes to refine its own scoring over time.

Built as a functional job search tool and a portfolio demonstration of end-to-end AI agent development with CI/CD.

---

## How It Works

### Daily Pipeline
```
Fetch job listings → Deduplicate → Score with Gemini → Email digest
```

The agent scrapes career pages from a curated list of target companies, filters out jobs already seen, scores each new listing 1–10 for fit, and sends an HTML email digest grouped by company tier — with a direct apply link for every listing.

### Weekly Learning Pipeline
```
Load outcomes → Analyze patterns → Rewrite scoring prompt
```

Once a week, the agent reviews which jobs you applied to and whether you heard back, then asks Gemini to refine the scoring prompt based on those patterns. The more you use it, the better it gets at predicting what you'll actually apply to.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  GitHub Codespaces                   │
│         Dev environment, demo runs, dashboard        │
└─────────────────────────────────────────────────────┘
          │  git push
          ▼
┌─────────────────────────────────────────────────────┐
│              GitHub Actions CI/CD                    │
│  lint + typecheck + test on every push               │
│  weekly agent run every Monday 8am UTC               │
└─────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│           LangGraph Agent Pipeline                   │
│                                                      │
│  [fetch_jobs] → [deduplicate] →                     │
│  [score_filter] → [format_report] → Gmail            │
└─────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│              SQLite + Feedback Loop                  │
│  jobs.db tracks seen jobs + application outcomes     │
│  Weekly pipeline rewrites scoring_prompt.txt         │
└─────────────────────────────────────────────────────┘
```

### Project Layout

```
job-search-agent/
├── agent/                  # Daily LangGraph pipeline
│   ├── graph.py
│   ├── state.py
│   └── nodes/              # fetch, deduplicate, score, format
├── fetchers/               # Greenhouse API, Lever API, HTML scraper
├── learning/               # Weekly self-improvement pipeline
├── database/               # SQLite wrapper
├── notifications/          # Gmail SMTP digest
├── cli/                    # Log applications and outcomes
├── dashboard/              # Streamlit UI (Codespaces port 8501)
├── config/
│   ├── companies.yaml      # Target companies and roles
│   └── scoring_prompt.txt  # Active Gemini scoring prompt
├── data/
│   └── demo.db             # Seeded demo database (see Demo section)
└── tests/
```

---

## Stack

| Component | Choice | Cost |
|-----------|--------|------|
| Agent framework | LangGraph | Free |
| LLM | Google Gemini 2.0 Flash | Free (1,500 req/day) |
| Job data | Greenhouse + Lever JSON APIs, HTML scraper | Free |
| Email | Gmail SMTP | Free |
| Database | SQLite | Free (stdlib) |
| CI/CD | GitHub Actions | Free |
| Dev environment | GitHub Codespaces | Free (60 hrs/month) |

**Total cost to run: $0**

---

## Target Companies

Companies are configured in `config/companies.yaml` across four tiers:

| Tier | Type | Examples |
|------|------|---------|
| 1 | Remote-first tech | Stripe, Datadog, GitLab, Snowflake, Databricks |
| 2 | Boston hybrid | HubSpot, Wayfair, Toast, Klaviyo, DraftKings |
| 3 | Energy / Industrial | Honeywell, GE Vernova, Eversource |
| 4 | Operations Research | Amazon, Uber |

Jobs are fetched directly from each company's career page using Greenhouse or Lever JSON APIs where available, Workday for others, and a BeautifulSoup HTML scraper as fallback.

---

## Local Setup

### Prerequisites
- Python 3.11+
- A Gmail account with [App Password enabled](https://myaccount.google.com/apppasswords)
- A [Google AI Studio](https://aistudio.google.com) API key (free)

### Install

```bash
git clone git@github.com:jgalloway42/job-search-agent.git
cd job-search-agent
pip install -r requirements.txt
```

> **SSH note:** this repo uses SSH for git. You'll need an SSH key added to your GitHub account.
> Generate one with `ssh-keygen -t ed25519 -C "your@email.com"`, then add `~/.ssh/id_ed25519.pub`
> at [github.com/settings/keys](https://github.com/settings/keys).

### Configure

```bash
cp .env.example .env
# Fill in your values:
#   GEMINI_API_KEY
#   GMAIL_ADDRESS
#   GMAIL_APP_PASSWORD
#   DIGEST_EMAIL
#   SCORE_THRESHOLD (default: 6)
#   DB_PATH (default: data/jobs.db)
```

### Run

```bash
make run          # run the full agent pipeline
make stats        # view your application funnel
make learn        # run the weekly learning pipeline manually
```

---

## Logging Applications & Outcomes

```bash
# After applying to a job from your digest
make apply JOB_ID=stripe-12345

# When you hear back
make outcome JOB_ID=stripe-12345 OUTCOME=phone_screen
make outcome JOB_ID=stripe-12345 OUTCOME=final_round
make outcome JOB_ID=stripe-12345 OUTCOME=offer
make outcome JOB_ID=stripe-12345 OUTCOME=rejected
```

The weekly learning pipeline uses these outcomes to rewrite `config/scoring_prompt.txt`, gradually improving match quality over time.

---

## Application Stats

```bash
make stats
```

```
Jobs surfaced:        199
Jobs scored:          135
Jobs qualified (>=6):  75
Applied:               18
Phone screens:          6   (33% response rate)
Final rounds:           2
Offers:                 1
```

---

## Demo

This repo includes `data/demo.db` — a pre-seeded database with realistic fake data for portfolio demonstration purposes.

To run the agent against the demo database:

```bash
DB_PATH=data/demo.db make run
```

In GitHub Codespaces, `demo.db` is used automatically. The Streamlit dashboard is also available:

```bash
make dashboard    # opens on port 8501
```

> **Note:** `data/jobs.db` (real application data) is gitignored and never committed to this repo.

---

## CI/CD

Every push triggers lint, type checking, and tests via GitHub Actions:

```
ruff → mypy → pytest
```

The agent also runs automatically every Monday at 8am UTC against the demo database. See `.github/workflows/` for full configuration.

---

## Development

```bash
make test             # pytest
make lint             # ruff + mypy
make check-fetchers   # test each career page fetcher
make clean-today      # rollback today's seen jobs (re-run fresh)
make seed-demo        # regenerate data/demo.db with fake data
```

### Adding a Company

Edit `config/companies.yaml`:

```yaml
- name: Acme Corp
  tier: 1
  ats: greenhouse          # greenhouse | lever | workday | scraper
  ats_slug: acmecorp       # slug used in the ATS API URL
  target_roles:
    - "Senior Data Scientist"
    - "ML Engineer"
```

---

## Troubleshooting

### Gemini quota error on first run

**Symptom:** The `score_filter` node fails with a quota or rate-limit error.

**Cause:** On a first run (or after `make clean-today`), the agent may encounter 50–100 new jobs. Greenhouse and Lever responses include full HTML job descriptions — often thousands of tokens each. Batching all of them into one prompt can hit Gemini's free-tier tokens-per-minute (TPM) limit even though only one API call is made.

**Fix:** Descriptions are truncated to 800 characters in `agent/nodes/score_filter.py` before the prompt is built. This reduces prompt size ~10x and should keep you well within the free tier on any normal run.

**If it still recurs:** The next step would be splitting `deduplicated` into batches of ~30 jobs with a short sleep between calls. Open an issue if you hit this.

---

## Full Specification

See [SPEC.md](SPEC.md) for complete architecture documentation, all design decisions, database schema, and build phase plan.
