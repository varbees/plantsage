"""FastAPI entry point for PlantSage."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from agent.plant_agent import research_plant
from api.vertex_identifier import identify_plant
from core.config import get_settings
from db.species_log import (
    get_dashboard_summary,
    get_observations,
    get_recent_reports,
    get_reports_for_species,
    get_species_log,
    init_db,
    log_observation,
    register_report,
)
from pipeline.ingestion import persist_upload
from reports.generator import generate_all_reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PlantSage - Rayalaseema Flora Intelligence",
    description="Photo to plant ID, researched Rayalaseema flora report, and personal species log.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def field_console():
    page = Path("app.html")
    if not page.exists():
        raise HTTPException(status_code=404, detail="app.html not found")
    return FileResponse(page, media_type="text/html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon_ico():
    return RedirectResponse("/favicon.svg", status_code=307)


@app.get("/favicon.svg", include_in_schema=False)
async def favicon_svg():
    page = Path("public/favicon.svg")
    if not page.exists():
        raise HTTPException(status_code=404, detail="favicon.svg not found")
    return FileResponse(page, media_type="image/svg+xml")


@app.post("/identify")
async def identify_and_research(
    image: UploadFile = File(...),
    latitude: float = 13.7483,
    longitude: float = 79.6986,
    district: str = "Tirupati",
) -> dict[str, Any]:
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Upload a non-empty plant image.")

    settings = get_settings()
    try:
        uploaded = await persist_upload(image_bytes, image.content_type or "image/jpeg", upload_dir=settings.uploads_dir)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    try:
        plant_id = await identify_plant(image_bytes, mime_type=uploaded.mime_type)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Vertex identification failed: {exc}") from exc

    confidence = float(plant_id.get("confidence") or 0.0)
    if not plant_id.get("scientific_name") or confidence < 0.4:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Low confidence identification. Retake the plant with leaves, flowers, or fruit visible.",
                "plant_id": plant_id,
            },
        )

    try:
        research = await research_plant(
            plant_id,
            location_context={"latitude": latitude, "longitude": longitude, "district": district},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Claude research failed: {exc}") from exc

    reports = await generate_all_reports(plant_id, research, output_dir=settings.reports_dir)
    observation_id = await log_observation(
        scientific_name=plant_id["scientific_name"],
        family=plant_id.get("family"),
        telugu_name=plant_id.get("telugu_name"),
        latitude=latitude,
        longitude=longitude,
        district=district,
        confidence=confidence,
        image_path=str(uploaded.path),
        image_sha256=uploaded.sha256,
        mime_type=uploaded.mime_type,
    )
    report_run_id = await register_report(
        observation_id=observation_id,
        scientific_name=research.get("scientific_name") or plant_id["scientific_name"],
        slug=reports["slug"],
        artifacts={
            "json": reports.get("json_path"),
            "markdown": reports.get("markdown_path"),
            "pdf": reports.get("pdf_path"),
        },
        sources=research.get("sources") or [],
    )

    markdown_url = f"/reports/{reports['markdown_filename']}"
    json_url = f"/reports/{reports['json_filename']}"
    pdf_url = f"/reports/{reports['pdf_filename']}" if reports.get("pdf_filename") else None

    return {
        "status": "success",
        "plant_id": plant_id,
        "report": research,
        "reports": reports,
        "observation_id": observation_id,
        "report_run_id": report_run_id,
        "image": {
            "sha256": uploaded.sha256,
            "path": str(uploaded.path),
            "mime_type": uploaded.mime_type,
            "size_bytes": uploaded.size_bytes,
        },
        "json_url": json_url,
        "markdown_url": markdown_url,
        "pdf_url": pdf_url,
    }


@app.get("/reports/{filename:path}", name="download_report")
async def download_report(filename: str):
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Nested report paths are not allowed.")

    report_path = get_settings().reports_dir / safe_name
    if not report_path.exists() or not report_path.is_file():
        raise HTTPException(status_code=404, detail="Report not found.")

    media_type = "application/octet-stream"
    if report_path.suffix == ".pdf":
        media_type = "application/pdf"
    elif report_path.suffix == ".md":
        media_type = "text/markdown"
    elif report_path.suffix == ".json":
        media_type = "application/json"

    return FileResponse(report_path, media_type=media_type, filename=report_path.name)


@app.get("/report/pdf/{species_slug}")
async def latest_pdf_report(species_slug: str):
    if Path(species_slug).name != species_slug:
        raise HTTPException(status_code=400, detail="Invalid species slug.")

    matches = sorted(
        get_settings().reports_dir.glob(f"{species_slug}_*.pdf"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise HTTPException(status_code=404, detail="No PDF report found for that species slug.")
    return FileResponse(matches[0], media_type="application/pdf", filename=matches[0].name)


@app.get("/species-log")
async def species_log(district: str | None = None, limit: int = 50):
    return await get_species_log(district=district, limit=limit)


@app.get("/observations")
async def observations(limit: int = 50):
    return await get_observations(limit=limit)


@app.get("/species/{scientific_name}/reports")
async def species_reports(scientific_name: str, limit: int = 20):
    return await get_reports_for_species(scientific_name, limit=limit)


@app.get("/api/dashboard")
async def dashboard_data():
    return {
        "readiness": get_settings().readiness(),
        "summary": await get_dashboard_summary(),
        "species": await get_species_log(limit=20),
        "observations": await get_observations(limit=20),
        "reports": await get_recent_reports(limit=20),
    }


@app.get("/architecture")
async def architecture_page():
    page = Path("architecture.html")
    if not page.exists():
        raise HTTPException(status_code=404, detail="architecture.html not found")
    return FileResponse(page, media_type="text/html")


@app.get("/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "region": "Rayalaseema / Andhra Pradesh",
        "identifier_model": "Vertex AI Gemini",
        "research_model": "Claude Messages API",
        "reports_dir": str(settings.reports_dir),
        "uploads_dir": str(settings.uploads_dir),
    }


@app.get("/ready")
async def ready():
    return get_settings().readiness()
