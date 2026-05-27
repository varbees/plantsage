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
export ANTHROPIC_API_KEY="sk-ant-..."
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/credentials.json"
export VERTEX_LOCATION="us-central1"
export VERTEX_GEMINI_MODEL="gemini-2.5-flash"
export ANTHROPIC_MODEL="claude-sonnet-4-6"
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

## Google Cloud setup

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com

gcloud iam service-accounts create plantsage-sa \
  --display-name="PlantSage Service Account"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:plantsage-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

For local development, a temporary service account key can be used:

```bash
gcloud iam service-accounts keys create credentials.json \
  --iam-account=plantsage-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

For Cloud Run, prefer service-account identity and Secret Manager instead of shipping a key file.

## Deploy to Cloud Run

This repo includes a Dockerfile because PDF generation needs system libraries for WeasyPrint.

```bash
printf '%s' 'sk-ant-...' | gcloud secrets create ANTHROPIC_API_KEY --data-file=-
gcloud secrets add-iam-policy-binding ANTHROPIC_API_KEY \
  --member="serviceAccount:plantsage-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud run deploy plantsage \
  --source . \
  --platform managed \
  --region asia-south1 \
  --service-account plantsage-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=YOUR_PROJECT_ID,VERTEX_LOCATION=us-central1,VERTEX_GEMINI_MODEL=gemini-2.5-flash,ANTHROPIC_MODEL=claude-sonnet-4-6" \
  --set-secrets "ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest" \
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

Expected live runtime is usually 45-90 seconds because Claude web search runs several search calls.

## Deploy to Vercel with pnpm dlx

Vercel uses the root `app.py` FastAPI entrypoint, which re-exports the real application from `api.main`. This follows Vercel's FastAPI detector while keeping local runs on `python -m uvicorn api.main:app`.

Login/link:

```bash
pnpm dlx vercel login
pnpm dlx vercel link
```

Production env vars:

```bash
pnpm dlx vercel env add ANTHROPIC_API_KEY production
pnpm dlx vercel env add GCP_PROJECT_ID production
pnpm dlx vercel env add GOOGLE_APPLICATION_CREDENTIALS_JSON production
pnpm dlx vercel env add VERTEX_LOCATION production
pnpm dlx vercel env add VERTEX_GEMINI_MODEL production
pnpm dlx vercel env add ANTHROPIC_MODEL production
```

Recommended values:

```text
VERTEX_LOCATION=us-central1
VERTEX_GEMINI_MODEL=gemini-2.5-flash
ANTHROPIC_MODEL=claude-sonnet-4-6
```

Use `GOOGLE_APPLICATION_CREDENTIALS_JSON` for Vercel, not `GOOGLE_APPLICATION_CREDENTIALS`, because Vercel does not have your local credentials file. Paste the full service-account JSON as one env var.

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
- Next likely data-engineering upgrade: background job table plus worker for long Claude research runs, then Postgres or Cloud SQL when multi-user persistence matters.

## Credentials needed for live local E2E

- `ANTHROPIC_API_KEY`
- `GCP_PROJECT_ID`
- `GOOGLE_APPLICATION_CREDENTIALS` pointing to a temporary service account JSON file with Vertex AI user permissions
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` for Vercel deployments

Optional overrides:

- `VERTEX_LOCATION`
- `VERTEX_GEMINI_MODEL`
- `ANTHROPIC_MODEL`
