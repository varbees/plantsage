from pathlib import Path


def test_field_console_has_complete_app_landmarks():
    html = Path("app.html").read_text(encoding="utf-8")

    required = [
        'id="dropzone"',
        'id="image-preview"',
        'id="run-button"',
        'id="readiness-card"',
        'id="pipeline-timeline"',
        'data-step="ingest"',
        'data-step="identify"',
        'data-step="research"',
        'data-step="reports"',
        'id="tab-summary"',
        'id="tab-research"',
        'id="tab-json"',
        'id="report-gallery"',
        'id="species-rail"',
        'id="recent-observations"',
        "window.PlantSageApp",
        'fetch("/api/dashboard")',
    ]

    for marker in required:
        assert marker in html


def test_field_console_uses_backend_as_state_source():
    html = Path("app.html").read_text(encoding="utf-8")

    assert 'fetch("/ready")' in html
    assert 'fetch("/identify"' in html
    assert 'fetch("/observations' not in html
    assert "localStorage.setItem" not in html
