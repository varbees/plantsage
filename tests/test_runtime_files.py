from pathlib import Path


def test_dockerfile_is_cloud_run_ready():
    dockerfile = Path("Dockerfile")
    assert dockerfile.exists()

    text = dockerfile.read_text(encoding="utf-8")
    assert "USER plantsage" in text
    assert "${PORT:-8080}" in text
    assert "HEALTHCHECK" in text
    assert "requirements.txt" in text


def test_dockerignore_excludes_runtime_artifacts():
    dockerignore = Path(".dockerignore")
    assert dockerignore.exists()

    text = dockerignore.read_text(encoding="utf-8")
    assert "generated_reports/" in text
    assert "plantsage_observations.db" in text
    assert "credentials.json" in text
    assert "data/uploads/" in text


def test_vercel_entrypoint_matches_fastapi_detector():
    config = Path("vercel.json")
    assert config.exists()
    assert Path("app.py").exists()

    entrypoint = Path("app.py").read_text(encoding="utf-8")
    assert "from api.main import app" in entrypoint

    config_text = config.read_text(encoding="utf-8")
    assert '"api/main.py"' not in config_text
    assert '"destination": "/api/main.py"' not in config_text


def test_gitignore_keeps_examples_and_excludes_secrets():
    text = Path(".gitignore").read_text(encoding="utf-8")

    assert ".env*" in text
    assert "!.env.example" in text
    assert ".vercel/" in text
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in text
