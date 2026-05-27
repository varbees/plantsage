import asyncio

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
