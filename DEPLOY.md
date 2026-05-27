# PlantSage Deployment

## Local production rehearsal

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Environment:

```bash
export GEMINI_API_KEY="AIza..."
export GEMINI_MODEL="gemini-2.5-flash"
export GEMINI_RESEARCH_MODEL="gemini-2.5-flash"
export PLANTSAGE_RESEARCH_PROVIDER="gemini"
```

Check live readiness without exposing secrets:

```bash
python scripts/check_live_ready.py
curl http://127.0.0.1:8080/ready
```

Run:

```bash
scripts/run_local_prod.sh
```

## Gemini API setup

Create a Gemini API key in Google AI Studio and set it as `GEMINI_API_KEY`.
No GCP project or service account JSON is required for the identifier path.

## Deploy to Cloud Run

This repo includes a Dockerfile because PDF generation benefits from system libraries for WeasyPrint. The app now uses Gemini API key auth, so the container only needs API-key secrets.

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
gcloud iam service-accounts create plantsage-sa \
  --display-name="PlantSage Service Account"

printf '%s' 'AIza...' | gcloud secrets create GEMINI_API_KEY --data-file=-
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:plantsage-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud run deploy plantsage \
  --source . \
  --platform managed \
  --region asia-south1 \
  --service-account plantsage-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_MODEL=gemini-2.5-flash,GEMINI_RESEARCH_MODEL=gemini-2.5-flash,PLANTSAGE_RESEARCH_PROVIDER=gemini" \
  --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest" \
  --memory 2Gi \
  --timeout 300s
```

## Test

```bash
curl -X POST https://YOUR_SERVICE_URL/identify \
  -F "image=@/path/to/plant.jpg" \
  -F "latitude=13.7483" \
  -F "longitude=79.6986" \
  -F "district=Tirupati"
```

Expected live runtime is usually 20-60 seconds because Gemini Search grounding may run multiple searches before returning the report.

## Deploy to Vercel with pnpm dlx

Vercel uses the root `app.py` FastAPI entrypoint, which re-exports the real application from `api.main`. This follows Vercel's FastAPI detector while keeping local runs on `python -m uvicorn api.main:app`.

Login/link:

```bash
pnpm dlx vercel login
pnpm dlx vercel link
```

Production env vars:

```bash
pnpm dlx vercel env add GEMINI_API_KEY production
pnpm dlx vercel env add GEMINI_MODEL production
pnpm dlx vercel env add GEMINI_RESEARCH_MODEL production
pnpm dlx vercel env add PLANTSAGE_RESEARCH_PROVIDER production
```

Recommended values:

```text
GEMINI_MODEL=gemini-2.5-flash
GEMINI_RESEARCH_MODEL=gemini-2.5-flash
PLANTSAGE_RESEARCH_PROVIDER=gemini
```

Use `GEMINI_API_KEY` for Vercel. Do not add local credential JSON files to Vercel or git.

Preview caveat: `main` is the production branch for this project. Vercel will not attach Preview env vars to `main`; for a non-production branch use:

```bash
pnpm dlx vercel env add GEMINI_API_KEY preview your-branch
pnpm dlx vercel env add GEMINI_MODEL preview your-branch
pnpm dlx vercel env add GEMINI_RESEARCH_MODEL preview your-branch
pnpm dlx vercel env add PLANTSAGE_RESEARCH_PROVIDER preview your-branch
```

For one-off preview deploys from `main`, pass runtime env flags with `pnpm dlx vercel -e ...`.

Deploy:

```bash
pnpm dlx vercel --prod
```

Verify:

```bash
pnpm dlx vercel curl /ready --environment production
pnpm dlx vercel logs --environment production --level error --since 10m
```

## Data and orchestration notes

- Local runtime uploads: `data/uploads/`
- Local runtime reports: `generated_reports/`
- Local SQLite database: `plantsage_observations.db`
- Vercel prototype runtime: `/tmp/plantsage/...` for uploads, reports, and SQLite
- Current orchestration: one FastAPI service. Do not add Compose/Kubernetes until a second runtime service exists.
- Gemini Deep Research is a strong candidate for the research layer, but it is a background Interactions API flow that must be started and polled. The prototype now has a `research_jobs` table; the next production step is moving long research from synchronous `/identify` into a worker that claims those jobs.
- Next likely data-engineering upgrade: background job table plus worker for long research runs, then Postgres or Cloud SQL when multi-user persistence matters.

## Credentials needed for live local E2E

- `GEMINI_API_KEY`

Optional overrides:

- `GEMINI_MODEL`
- `GEMINI_RESEARCH_MODEL`
- `PLANTSAGE_RESEARCH_PROVIDER=anthropic` plus `ANTHROPIC_API_KEY` if you want the old Claude research fallback
