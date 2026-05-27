import asyncio
import sqlite3

from db.species_log import SpeciesLog


def test_report_artifacts_and_sources_are_registered(tmp_path):
    log = SpeciesLog(tmp_path / "plants.db")

    observation_id = asyncio.run(
        log.log_observation(
            scientific_name="Azadirachta indica",
            telugu_name="Vepa",
            family="Meliaceae",
            district="Tirupati",
            confidence=0.91,
            image_sha256="abc123",
            image_path="data/uploads/abc123.jpg",
            mime_type="image/jpeg",
        )
    )
    asyncio.run(
        log.register_report(
            observation_id=observation_id,
            scientific_name="Azadirachta indica",
            slug="azadirachta_indica",
            artifacts={
                "json": "generated_reports/azadirachta_indica.json",
                "markdown": "generated_reports/azadirachta_indica.md",
                "pdf": "generated_reports/azadirachta_indica.pdf",
            },
            sources=["eFlora India", "PubMed PMID test"],
        )
    )

    reports = asyncio.run(log.get_reports_for_species("Azadirachta indica"))

    assert reports[0]["slug"] == "azadirachta_indica"
    assert reports[0]["artifact_count"] == 3
    assert reports[0]["source_count"] == 2


def test_existing_database_is_migrated_with_ingestion_columns(tmp_path):
    log = SpeciesLog(tmp_path / "plants.db")
    asyncio.run(log.init_db())

    observation_id = asyncio.run(
        log.log_observation(
            scientific_name="Calotropis gigantea",
            image_sha256="hash",
            image_path="data/uploads/hash.jpg",
            mime_type="image/jpeg",
        )
    )

    rows = asyncio.run(log.get_observations(limit=1))

    assert rows[0]["id"] == observation_id
    assert rows[0]["image_sha256"] == "hash"


def test_database_has_agentic_research_schema_tables(tmp_path):
    log = SpeciesLog(tmp_path / "plants.db")
    asyncio.run(log.init_db())

    with sqlite3.connect(tmp_path / "plants.db") as db:
        table_rows = db.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()

    table_names = {row[0] for row in table_rows}

    assert {
        "determinations",
        "research_jobs",
        "source_documents",
        "plant_claims",
        "vernacular_names",
        "region_occurrences",
        "review_events",
    }.issubset(table_names)


def test_research_jobs_and_source_documents_are_queryable(tmp_path):
    log = SpeciesLog(tmp_path / "plants.db")
    observation_id = asyncio.run(
        log.log_observation(
            scientific_name="Tamarindus indica L.",
            family="Fabaceae",
            district="Tirupati",
            confidence=0.8,
            image_sha256="seedling-hash",
            image_path="data/uploads/seedling.jpg",
            mime_type="image/jpeg",
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
    asyncio.run(log.update_research_job(job_id, status="running"))
    report_run_id = asyncio.run(
        log.register_report(
            observation_id=observation_id,
            scientific_name="Tamarindus indica L.",
            slug="tamarindus_indica",
            artifacts={"json": "report.json", "markdown": "report.md"},
            sources=[
                "POWO - https://powo.science.kew.org/taxon/example",
                "IBIS Flora baseline reference",
            ],
        )
    )
    asyncio.run(log.update_research_job(job_id, status="complete", report_run_id=report_run_id))

    jobs = asyncio.run(log.get_recent_research_jobs(limit=5))
    documents = asyncio.run(log.get_source_documents_for_report(report_run_id))
    summary = asyncio.run(log.get_dashboard_summary())

    assert jobs[0]["id"] == job_id
    assert jobs[0]["status"] == "complete"
    assert jobs[0]["report_run_id"] == report_run_id
    assert documents[0]["url"] == "https://powo.science.kew.org/taxon/example"
    assert documents[1]["source_text"] == "IBIS Flora baseline reference"
    assert summary["total_research_jobs"] == 1
    assert summary["total_source_documents"] == 2
