def test_fastapi_app_imports():
    from api.main import app

    paths = {route.path for route in app.routes}

    assert "/health" in paths
    assert "/ready" in paths
    assert "/api/dashboard" in paths
    assert "/" in paths
    assert "/identify" in paths
    assert "/species-log" in paths
    assert "/observations" in paths
