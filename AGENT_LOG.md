# PlantSage Agent Ledger

Last updated: 2026-05-28

Purpose: keep the current prototype state, next tasks, and handoff commands visible for any coding agent without reading the full chat history.

## Done

- Built FastAPI backend, upload ingestion, Gemini identification, Gemini grounded research, SQLite logging, and report generation.
- Added the browser observation workspace with readiness, dashboard, research jobs, observations, species, and reports.
- Added async-ready tables: `research_jobs`, `source_documents`, `determinations`, `plant_claims`, `vernacular_names`, `region_occurrences`, and `review_events`.
- Added local async research mode: `PLANTSAGE_ASYNC_RESEARCH=1` makes `/identify` enqueue `research_jobs`; `scripts/run_research_worker.py` claims and processes queued jobs.
- Added competitor/data-source research at `docs/research/opensage-plant-intelligence-landscape.md`.
- Deployed the first Vercel prototype and verified live readiness with Gemini as identifier and research provider.

## Current Setup

- Local secrets live in ignored `.env`.
- `core.config.Settings.from_env()` loads `.env` automatically unless `PLANTSAGE_SKIP_DOTENV=1`.
- Tests set `PLANTSAGE_SKIP_DOTENV=1` so local credentials do not affect assertions.
- Vercel production has Gemini env vars set at project level.
- Vercel preview vars cannot target `main` because `main` is the production branch; use a non-production branch-specific preview env or pass `-e` flags for ad hoc preview deploys.

## Next Phase

1. Move the local worker claim loop from SQLite to managed Postgres.
2. Move uploads and generated report artifacts from local files or Vercel `/tmp` to object storage.
3. Extract source-backed `plant_claims` from reports and attach every claim to source documents.
4. Tighten the report/PDF canvas with image placement, source pruning, and field-safe practical sections.
5. Improve the UI from observation workspace toward an agentic research canvas while staying fast on mobile.

## Handoff Commands

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8080
PLANTSAGE_ASYNC_RESEARCH=1 python -m uvicorn api.main:app --reload --port 8080
python scripts/run_research_worker.py --once
pytest
python scripts/check_live_ready.py
```
