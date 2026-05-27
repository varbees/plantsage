import asyncio

import pytest

from api.vertex_identifier import identify_plant


def test_identifier_mock_mode_returns_static_plant(monkeypatch):
    monkeypatch.setenv("PLANTSAGE_MOCK_IDENTIFY", "1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = asyncio.run(identify_plant(b"image-bytes", mime_type="image/jpeg"))

    assert result["scientific_name"] == "Azadirachta indica"
    assert result["confidence"] == 0.92


def test_identifier_requires_gemini_api_key(monkeypatch):
    monkeypatch.delenv("PLANTSAGE_MOCK_IDENTIFY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        asyncio.run(identify_plant(b"image-bytes", mime_type="image/jpeg"))
