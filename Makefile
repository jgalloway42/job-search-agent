.PHONY: run learn test lint apply outcome stats clean-today check-fetchers seed-demo dashboard

# ── Daily agent ──────────────────────────────────────────────────────────────

run:
	## Run the full daily agent pipeline (fetch → deduplicate → score → email)
	python -m agent.graph

# ── Weekly learning pipeline ─────────────────────────────────────────────────

learn:
	## Run the weekly learning pipeline (feedback → analyze → update prompt)
	python -m learning.graph

# ── Testing & linting ────────────────────────────────────────────────────────

test:
	## Run the full test suite
	pytest tests/ -v

lint:
	## Run ruff linter and mypy type checker
	ruff check .
	mypy .

# ── CLI helpers ───────────────────────────────────────────────────────────────

apply:
	## Log a job application. Usage: make apply JOB_ID=xxx
	python -m cli.log apply --job-id $(JOB_ID)

outcome:
	## Record an application outcome. Usage: make outcome JOB_ID=xxx OUTCOME=phone_screen
	## Valid outcomes: phone_screen | final_round | offer | rejected
	python -m cli.log outcome --job-id $(JOB_ID) --outcome $(OUTCOME)

stats:
	## Print funnel summary (applied → phone screen → final round → offer)
	python -m cli.log stats

# ── Dev utilities ─────────────────────────────────────────────────────────────

clean-today:
	## Remove today's seen job IDs from the DB so the pipeline can re-run fresh
	python -m cli.log clean-today

check-fetchers:
	## Test each fetcher against live APIs and report pass/fail
	python -m cli.log check-fetchers

seed-demo:
	## Regenerate data/demo.db with realistic fake data for portfolio demo
	python scripts/seed_demo.py

dashboard:
	## Launch the Streamlit dashboard on port 8501
	PYTHONPATH=. streamlit run dashboard/app.py

# ── install dependencies ─────────────────────────────────────────────────────────────

install:
	pip install -r requirements.txt -r requirements-dev.txt