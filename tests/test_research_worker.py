import asyncio

from agent.research_worker import ResearchJobWorker
from db.species_log import SpeciesLog


def test_claim_next_research_job_returns_context_and_marks_running(tmp_path):
    log = SpeciesLog(tmp_path / "plants.db")
    observation_id = asyncio.run(
        log.log_observation(
            scientific_name="Tamarindus indica L.",
            family="Fabaceae",
            telugu_name="Chinta",
            district="Tirupati",
            latitude=13.7483,
            longitude=79.6986,
            confidence=0.9,
            image_sha256="seedling",
            image_path="data/uploads/seedling.png",
            mime_type="image/png",
        )
    )
    first_job_id = asyncio.run(
        log.create_research_job(
            observation_id=observation_id,
            scientific_name="Tamarindus indica L.",
            mode="deep_report",
            provider="gemini",
        )
    )
    asyncio.run(
        log.create_research_job(
            observation_id=observation_id,
            scientific_name="Tamarindus indica L.",
            mode="deep_report",
            provider="gemini",
        )
    )

    claimed = asyncio.run(log.claim_next_research_job())
    jobs = asyncio.run(log.get_recent_research_jobs())

    assert claimed is not None
    assert claimed["id"] == first_job_id
    assert claimed["status"] == "running"
    assert claimed["family"] == "Fabaceae"
    assert claimed["telugu_name"] == "Chinta"
    assert claimed["district"] == "Tirupati"
    assert claimed["latitude"] == 13.7483
    assert {job["id"]: job["status"] for job in jobs}[first_job_id] == "running"


def test_research_worker_processes_next_job_into_report_run(tmp_path):
    log = SpeciesLog(tmp_path / "plants.db")
    observation_id = asyncio.run(
        log.log_observation(
            scientific_name="Tamarindus indica L.",
            family="Fabaceae",
            telugu_name="Chinta",
            district="Tirupati",
            latitude=13.7483,
            longitude=79.6986,
            confidence=0.9,
        )
    )
    job_id = asyncio.run(
        log.create_research_job(
            observation_id=observation_id,
            scientific_name="Tamarindus indica L.",
            mode="deep_report",
            provider="gemini",
        )
    )
    seen: dict[str, object] = {}

    async def fake_research(plant_id, *, location_context):
        seen["plant_id"] = plant_id
        seen["location_context"] = location_context
        return {
            "scientific_name": plant_id["scientific_name"],
            "family": plant_id["family"],
            "telugu_name": plant_id["telugu_name"],
            "sources": ["POWO - https://powo.science.kew.org/taxon/example"],
        }

    async def fake_reports(plant_id, research, *, output_dir):
        return {
            "slug": "tamarindus_indica_l",
            "json_path": str(output_dir / "report.json"),
            "markdown_path": str(output_dir / "report.md"),
            "pdf_path": str(output_dir / "report.pdf"),
        }

    worker = ResearchJobWorker(
        species_log=log,
        research_fn=fake_research,
        report_fn=fake_reports,
        reports_dir=tmp_path / "reports",
    )

    result = asyncio.run(worker.process_next_job())
    jobs = asyncio.run(log.get_recent_research_jobs())
    reports = asyncio.run(log.get_recent_reports())

    assert result == {"status": "complete", "job_id": job_id, "report_run_id": reports[0]["id"]}
    assert jobs[0]["status"] == "complete"
    assert jobs[0]["report_run_id"] == reports[0]["id"]
    assert reports[0]["artifact_count"] == 3
    assert reports[0]["source_count"] == 1
    assert seen["plant_id"]["confidence"] == 0.9
    assert seen["location_context"] == {"latitude": 13.7483, "longitude": 79.6986, "district": "Tirupati"}
