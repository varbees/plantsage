from core.config import Settings


def test_readiness_reports_missing_live_credentials(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("PLANTSAGE_MOCK_IDENTIFY", raising=False)
    monkeypatch.delenv("PLANTSAGE_MOCK_RESEARCH", raising=False)

    readiness = Settings.from_env().readiness()

    assert readiness["mode"] == "live"
    assert "ANTHROPIC_API_KEY" in readiness["missing"]
    assert "GCP_PROJECT_ID" in readiness["missing"]


def test_readiness_allows_mock_mode(monkeypatch):
    monkeypatch.setenv("PLANTSAGE_MOCK_IDENTIFY", "1")
    monkeypatch.setenv("PLANTSAGE_MOCK_RESEARCH", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)

    readiness = Settings.from_env().readiness()

    assert readiness["mode"] == "mock"
    assert readiness["ready"] is True
    assert readiness["missing"] == []


def test_vercel_defaults_use_tmp_runtime_paths(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("PLANTSAGE_REPORTS_DIR", raising=False)
    monkeypatch.delenv("PLANTSAGE_UPLOADS_DIR", raising=False)
    monkeypatch.delenv("PLANTSAGE_DB_PATH", raising=False)

    settings = Settings.from_env()

    assert str(settings.reports_dir).startswith("/tmp/plantsage")
    assert str(settings.uploads_dir).startswith("/tmp/plantsage")
    assert str(settings.db_path).startswith("/tmp/plantsage")


def test_google_credentials_json_satisfies_readiness(monkeypatch):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setenv("GCP_PROJECT_ID", "plantsage-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", '{"type":"service_account"}')
    monkeypatch.delenv("PLANTSAGE_MOCK_IDENTIFY", raising=False)
    monkeypatch.delenv("PLANTSAGE_MOCK_RESEARCH", raising=False)

    readiness = Settings.from_env().readiness()

    assert readiness["ready"] is True
    assert readiness["missing"] == []
