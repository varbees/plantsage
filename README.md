# PlantSage - Rayalaseema Flora Intelligence

PlantSage turns a plant photo into:

1. Hash-addressed upload ingestion under `data/uploads/`.
2. Vertex AI Gemini Vision identification.
3. Claude web-search research across botany, Rayalaseema ethnomedicine, Ayurveda, phytochemistry, ecology, and culture.
4. JSON, Markdown, and PDF reports under `generated_reports/`.
5. SQLite observation, species familiarity, report artifact, and source-citation records.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `ANTHROPIC_API_KEY`, `GCP_PROJECT_ID`, and `GOOGLE_APPLICATION_CREDENTIALS`, then:

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

## Data model

SQLite tables:

- `observations`: one row per uploaded plant observation, including district, GPS, confidence, upload path, image SHA-256, and MIME type.
- `species_knowledge`: one row per species with familiarity level: `new`, `learning`, `familiar`, `expert`.
- `report_runs`: one row per completed report generation.
- `report_artifacts`: generated JSON/Markdown/PDF file paths per report run.
- `report_sources`: source strings from the researched report for later citation/search ingestion.

No queue or Postgres is used yet. The synchronous pipeline is simpler and sufficient for local production testing. The schema is already shaped so a later background worker can pick up `report_runs` without changing the API contract.

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
agent/                  Claude web-search research
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

This repo includes `vercel.json`, `.python-version`, and `pyproject.toml` so Vercel can deploy `api/main.py` as a Python FastAPI function.

Deploy from the CLI:

```bash
pnpm dlx vercel link
pnpm dlx vercel env add ANTHROPIC_API_KEY production
pnpm dlx vercel env add GCP_PROJECT_ID production
pnpm dlx vercel env add GOOGLE_APPLICATION_CREDENTIALS_JSON production
pnpm dlx vercel env add VERTEX_LOCATION production
pnpm dlx vercel env add VERTEX_GEMINI_MODEL production
pnpm dlx vercel env add ANTHROPIC_MODEL production
pnpm dlx vercel --prod
```

For preview smoke testing without live APIs, set:

```bash
pnpm dlx vercel env add PLANTSAGE_MOCK_IDENTIFY preview
pnpm dlx vercel env add PLANTSAGE_MOCK_RESEARCH preview
```

Set both values to `1`.

Vercel note: serverless filesystem writes are ephemeral. In Vercel, PlantSage defaults SQLite, uploads, and generated reports to `/tmp/plantsage/...`. That is correct for this first prototype, but durable production persistence should move to Postgres/Cloud SQL plus object storage.
