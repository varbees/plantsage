import asyncio

from db.species_log import SpeciesLog


def test_dashboard_summary_counts_observations_reports_and_species(tmp_path):
    log = SpeciesLog(tmp_path / "plants.db")
    observation_id = asyncio.run(
        log.log_observation(
            scientific_name="Azadirachta indica",
            telugu_name="Vepa",
            family="Meliaceae",
            district="Tirupati",
            confidence=0.91,
            image_sha256="hash",
            image_path="data/uploads/hash.jpg",
            mime_type="image/jpeg",
        )
    )
    asyncio.run(
        log.register_report(
            observation_id=observation_id,
            scientific_name="Azadirachta indica",
            slug="azadirachta_indica",
            artifacts={"json": "report.json", "markdown": "report.md", "pdf": "report.pdf"},
            sources=["eFlora India"],
        )
    )

    summary = asyncio.run(log.get_dashboard_summary())

    assert summary["total_observations"] == 1
    assert summary["total_species"] == 1
    assert summary["total_report_runs"] == 1
    assert summary["total_sources"] == 1


def test_recent_reports_do_not_duplicate_artifacts_when_sources_exist(tmp_path):
    log = SpeciesLog(tmp_path / "plants.db")
    observation_id = asyncio.run(log.log_observation(scientific_name="Tamarindus indica L."))
    asyncio.run(
        log.register_report(
            observation_id=observation_id,
            scientific_name="Tamarindus indica L.",
            slug="tamarindus_indica_l",
            artifacts={"json": "report.json", "markdown": "report.md", "pdf": "report.pdf"},
            sources=["POWO", "IBIS", "GBIF"],
        )
    )

    reports = asyncio.run(log.get_recent_reports())
    artifact_items = reports[0]["artifacts"].split("||")

    assert reports[0]["artifact_count"] == 3
    assert reports[0]["source_count"] == 3
    assert artifact_items == ["json:report.json", "markdown:report.md", "pdf:report.pdf"]
