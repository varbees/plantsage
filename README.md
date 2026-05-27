# PlantSage - Rayalaseema Flora Intelligence

PlantSage turns a plant photo into:

1. Hash-addressed upload ingestion under `data/uploads/`.
2. Gemini API vision identification through an AI Studio API key.
3. Gemini grounded research across botany, Rayalaseema ethnomedicine, Ayurveda, phytochemistry, ecology, and culture.
4. JSON, Markdown, and PDF reports under `generated_reports/`.
5. SQLite observation, species familiarity, report artifact, and source-citation records.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `GEMINI_API_KEY`. The app loads `.env` automatically for local runs, so the normal command is:

```bash
python -m uvicorn api.main:app --reload --port 8080
```

Open:

- Field console: http://127.0.0.1:8080/
- API docs: http://127.0.0.1:8080/docs
- Architecture: http://127.0.0.1:8080/architecture
- Readiness: http://127.0.0.1:8080/ready
- Health: http://127.0.0.1:8080/health
- Latest PDF by slug: http://127.0.0.1:8080/report/pdf/azadirachta_indica

## Smoke test without API keys

```bash
PLANTSAGE_MOCK_IDENTIFY=1 PLANTSAGE_MOCK_RESEARCH=1 python -m uvicorn api.main:app --reload --port 8080
```

Then post any image:

```bash
curl -X POST http://127.0.0.1:8080/identify \
  -F "image=@/path/to/plant.jpg" \
  -F "latitude=13.7483" \
  -F "longitude=79.6986" \
  -F "district=Tirupati"
```

## Async research worker

The default `/identify` path still runs identification, research, and reports synchronously for simple local testing. To split slow report generation into a worker:

```bash
PLANTSAGE_ASYNC_RESEARCH=1 python -m uvicorn api.main:app --reload --port 8080
python scripts/run_research_worker.py --once
```

With async mode enabled, `/identify` returns `202` after creating an observation and queued `research_jobs` row. The worker claims queued jobs, runs Gemini grounded research, writes report artifacts, registers source documents, and marks the job complete or failed.

## Data model

SQLite tables:

- `observations`: one row per uploaded plant observation, including district, GPS, confidence, upload path, image SHA-256, and MIME type.
- `determinations`: model/user/expert identifications attached to an observation.
- `species_knowledge`: one row per species with familiarity level: `new`, `learning`, `familiar`, `expert`.
- `research_jobs`: async-ready lifecycle rows for field ID and deep report generation.
- `report_runs`: one row per completed report generation.
- `report_artifacts`: generated JSON/Markdown/PDF file paths per report run.
- `report_sources`: source strings from the researched report for later citation/search ingestion.
- `source_documents`: normalized source records with URL/title/hash where available.
- `plant_claims`, `vernacular_names`, `region_occurrences`, `review_events`: schema-ready tables for sourced plant knowledge, Indian local names, regional likelihood, and review history.

No external queue or Postgres is used yet. The local worker claims queued `research_jobs` rows from SQLite. The schema and API are shaped so a managed worker can move to Postgres/object storage without changing the user-facing `/identify` contract.

## Research direction

The next product/data pass is captured in
[`docs/research/opensage-plant-intelligence-landscape.md`](docs/research/opensage-plant-intelligence-landscape.md).
It covers competitor UX, India-scale plant data sources, pain points, region-by-region expansion, and the serverless architecture direction for turning PlantSage into a field research assistant rather than a one-shot identifier.

For agent handoff, current status, and next tasks, see [`AGENT_LOG.md`](AGENT_LOG.md).

## Container

Build and run the Cloud Run-style container locally:

```bash
docker build -t plantsage .
docker run --rm -p 8080:8080 \
  --env-file .env \
  -v "$PWD/generated_reports:/app/generated_reports" \
  -v "$PWD/data/uploads:/app/data/uploads" \
  -v "$PWD/plantsage_observations.db:/app/plantsage_observations.db" \
  plantsage
```

Docker Compose is intentionally absent for now: there is only one service and a local SQLite file. Add orchestration only when introducing a separate worker, object store emulator, Postgres, or queue.

## Project layout

```text
api/                    FastAPI routes
agent/                  Gemini grounded research
core/                   settings and readiness checks
db/                     SQLite schema and persistence
pipeline/               upload ingestion primitives
reports/                JSON, Markdown, PDF generation
skills/                 reusable Rayalaseema flora skill
app.html                local upload console
architecture.html       interactive architecture diagram
scripts/                local production helpers
```

The original `files(1)/` drop is left untouched. The canonical runnable app is the package layout above.

## Vercel prototype

This repo includes `app.py`, `.python-version`, and `pyproject.toml` so Vercel can detect the FastAPI app while local development continues to use `api.main:app`.

Deploy from the CLI:

```bash
pnpm dlx vercel link
pnpm dlx vercel env add GEMINI_API_KEY production
pnpm dlx vercel env add GEMINI_MODEL production
pnpm dlx vercel env add GEMINI_RESEARCH_MODEL production
pnpm dlx vercel env add PLANTSAGE_RESEARCH_PROVIDER production
pnpm dlx vercel --prod
```

For preview smoke testing without live APIs, set:

```bash
pnpm dlx vercel env add PLANTSAGE_MOCK_IDENTIFY preview
pnpm dlx vercel env add PLANTSAGE_MOCK_RESEARCH preview
```

Set both values to `1`.

For live Gemini preview, do not set either mock variable. `GEMINI_API_KEY`
powers both image identification and grounded research.

Vercel note: serverless filesystem writes are ephemeral. In Vercel, PlantSage defaults SQLite, uploads, and generated reports to `/tmp/plantsage/...`. That is correct for this first prototype, but durable production persistence should move to Postgres/Cloud SQL plus object storage.
