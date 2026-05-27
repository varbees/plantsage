"""Worker orchestration for queued PlantSage research jobs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Awaitable, Callable

from agent.plant_agent import research_plant
from core.config import get_settings
from db.species_log import SpeciesLog, default_log
from reports.generator import generate_all_reports

ResearchFn = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
ReportFn = Callable[[dict[str, Any], dict[str, Any]], Awaitable[dict[str, Any]]]


class ResearchJobWorker:
    def __init__(
        self,
        *,
        species_log: SpeciesLog | None = None,
        research_fn: Callable[..., Awaitable[dict[str, Any]]] = research_plant,
        report_fn: Callable[..., Awaitable[dict[str, Any]]] = generate_all_reports,
        reports_dir: str | Path | None = None,
    ) -> None:
        settings = get_settings()
        self.species_log = species_log or default_log
        self.research_fn = research_fn
        self.report_fn = report_fn
        self.reports_dir = Path(reports_dir) if reports_dir else settings.reports_dir

    async def process_next_job(self) -> dict[str, Any]:
        job = await self.species_log.claim_next_research_job()
        if not job:
            return {"status": "idle"}

        job_id = int(job["id"])
        try:
            plant_id = self._plant_id_from_job(job)
            location_context = self._location_context_from_job(job)
            research = await self.research_fn(plant_id, location_context=location_context)
            reports = await self.report_fn(plant_id, research, output_dir=self.reports_dir)
            report_run_id = await self.species_log.register_report(
                observation_id=job.get("observation_id"),
                scientific_name=research.get("scientific_name") or plant_id["scientific_name"],
                slug=reports["slug"],
                artifacts={
                    "json": reports.get("json_path"),
                    "markdown": reports.get("markdown_path"),
                    "pdf": reports.get("pdf_path"),
                },
                sources=research.get("sources") or [],
            )
            await self.species_log.update_research_job(job_id, status="complete", report_run_id=report_run_id)
            return {"status": "complete", "job_id": job_id, "report_run_id": report_run_id}
        except Exception as exc:
            await self.species_log.update_research_job(job_id, status="failed", error_message=str(exc))
            raise

    def _plant_id_from_job(self, job: dict[str, Any]) -> dict[str, Any]:
        return {
            "scientific_name": job["scientific_name"],
            "family": job.get("family"),
            "telugu_name": job.get("telugu_name"),
            "confidence": job.get("confidence"),
        }

    def _location_context_from_job(self, job: dict[str, Any]) -> dict[str, Any]:
        return {
            "latitude": job.get("latitude"),
            "longitude": job.get("longitude"),
            "district": job.get("district"),
        }
