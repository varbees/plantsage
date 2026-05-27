from fastapi.testclient import TestClient


def test_identify_can_enqueue_research_without_running_report(monkeypatch, tmp_path):
    monkeypatch.setenv("PLANTSAGE_MOCK_IDENTIFY", "1")
    monkeypatch.setenv("PLANTSAGE_ASYNC_RESEARCH", "1")
    monkeypatch.setenv("PLANTSAGE_UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("PLANTSAGE_REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("PLANTSAGE_DB_PATH", str(tmp_path / "plants.db"))

    from api import main
    from db.species_log import SpeciesLog

    log = SpeciesLog(tmp_path / "plants.db")
    monkeypatch.setattr(main, "log_observation", log.log_observation)
    monkeypatch.setattr(main, "create_research_job", log.create_research_job)

    with TestClient(main.app) as client:
        response = client.post(
            "/identify",
            files={"image": ("plant.png", b"not-a-real-image-but-mock-mode", "image/png")},
            data={"latitude": "13.7483", "longitude": "79.6986", "district": "Tirupati"},
        )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["report"] is None
    assert body["report_run_id"] is None
    assert body["research_job_id"] == 1
    assert body["plant_id"]["scientific_name"] == "Azadirachta indica"
