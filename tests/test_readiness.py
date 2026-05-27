from core.config import Settings


def test_readiness_reports_missing_live_credentials(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("PLANTSAGE_MOCK_IDENTIFY", raising=False)
    monkeypatch.delenv("PLANTSAGE_MOCK_RESEARCH", raising=False)

    readiness = Settings.from_env().readiness()

    assert readiness["mode"] == "live"
    assert "research credential" in readiness["missing"]
    assert "identifier credential" in readiness["missing"]
    assert readiness["missing_count"] == 2
    assert "missing_env" not in readiness


def test_readiness_can_include_internal_missing_env_names(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("PLANTSAGE_MOCK_IDENTIFY", raising=False)
    monkeypatch.delenv("PLANTSAGE_MOCK_RESEARCH", raising=False)

    readiness = Settings.from_env().readiness(include_internal=True)

    assert "ANTHROPIC_API_KEY" in readiness["missing_env"]
    assert "GEMINI_API_KEY" in readiness["missing_env"]
    assert "configured" in readiness


def test_readiness_allows_mock_mode(monkeypatch):
    monkeypatch.setenv("PLANTSAGE_MOCK_IDENTIFY", "1")
    monkeypatch.setenv("PLANTSAGE_MOCK_RESEARCH", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

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


def test_gemini_api_key_satisfies_identifier_readiness(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("PLANTSAGE_MOCK_IDENTIFY", raising=False)
    monkeypatch.delenv("PLANTSAGE_MOCK_RESEARCH", raising=False)

    readiness = Settings.from_env().readiness()

    assert readiness["ready"] is True
    assert readiness["missing"] == []
    assert readiness["services"] == {"identifier": "gemini", "research": "claude"}
    assert readiness["models"]["identifier"] == "gemini-2.5-flash"
