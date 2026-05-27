import asyncio

import pytest

from api.vertex_identifier import _fallback_identification_from_text, identify_plant


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


def test_identifier_recovers_fields_from_malformed_gemini_json():
    raw = """{
      "scientific_name": "Tamarindus indica L.",
      "family": "Fabaceae",
      "telugu_name": "Chinta",
      "telugu_script": "చింత",
      "common_name_english": "Tamarind",
      "hindi_name": "Imli",
      "confidence": 0.8,
      "identification_basis": "The plant is an emerging seedling displaying large, fleshy, green
    """

    recovered = _fallback_identification_from_text(raw)

    assert recovered is not None
    assert recovered["scientific_name"] == "Tamarindus indica L."
    assert recovered["family"] == "Fabaceae"
    assert recovered["confidence"] == 0.8
    assert recovered["parse_recovered"] is True
