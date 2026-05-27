"""Gemini API plant identifier."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

from agent.plant_agent import extract_json_object
from core.config import get_settings


DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL") or os.getenv("GEMINI_IDENTIFICATION_MODEL", "gemini-2.5-flash")


IDENTIFICATION_PROMPT = """
You are a botanist specializing in South Indian flora, especially Rayalaseema:
Tirupati, Srikalahasti, Kadapa, Anantapur, Kurnool, Chittoor, Annamayya,
Seshachalam and dry Deccan thorn scrub habitats.

Identify the plant in this photo as precisely as possible. Be conservative.
If the image is a phone gallery screenshot or contains camera metadata UI,
ignore the phone interface and identify only the plant specimen in the photo.
Return ONLY valid JSON with this schema:
{
  "scientific_name": "Genus species (Author)",
  "family": "Family name",
  "telugu_name": "Telugu vernacular transliterated",
  "telugu_script": "Telugu script if known",
  "common_name_english": "Common English name",
  "hindi_name": "Hindi name if known",
  "confidence": 0.85,
  "identification_basis": "visible plant parts used for identification, 240 characters or less",
  "distinctive_features": ["feature 1", "feature 2"],
  "similar_species": ["similar species to consider"],
  "rayalaseema_context": "local occurrence or role if known"
}

If identification is not possible, return:
{"scientific_name": null, "confidence": 0.0, "error": "reason"}
"""


def _extract_string_field(raw: str, field: str) -> str | None:
    pattern = rf'"{re.escape(field)}"\s*:\s*"((?:\\.|[^"\\])*)'
    match = re.search(pattern, raw, flags=re.DOTALL)
    if not match:
        return None
    value = match.group(1)
    try:
        return bytes(value, "utf-8").decode("unicode_escape").strip()
    except UnicodeDecodeError:
        return value.strip()


def _extract_number_field(raw: str, field: str) -> float | None:
    match = re.search(rf'"{re.escape(field)}"\s*:\s*([0-9]+(?:\.[0-9]+)?)', raw)
    if not match:
        return None
    return float(match.group(1))


def _fallback_identification_from_text(raw: str) -> dict[str, Any] | None:
    """Recover useful fields from malformed Gemini JSON.

    Gemini can occasionally stream a botanically useful JSON-looking response
    with a broken string or truncated tail. Returning confidence zero in that
    case is worse than preserving the conservative candidate and marking the
    parse recovery.
    """

    scientific_name = _extract_string_field(raw, "scientific_name")
    confidence = _extract_number_field(raw, "confidence")
    if not scientific_name or confidence is None:
        return None

    return {
        "scientific_name": scientific_name,
        "family": _extract_string_field(raw, "family"),
        "telugu_name": _extract_string_field(raw, "telugu_name"),
        "telugu_script": _extract_string_field(raw, "telugu_script"),
        "common_name_english": _extract_string_field(raw, "common_name_english"),
        "hindi_name": _extract_string_field(raw, "hindi_name"),
        "confidence": confidence,
        "identification_basis": _extract_string_field(raw, "identification_basis")
        or "Gemini returned malformed JSON; core identification fields were recovered.",
        "distinctive_features": [],
        "similar_species": [],
        "rayalaseema_context": _extract_string_field(raw, "rayalaseema_context"),
        "parse_recovered": True,
    }


def _mock_identification() -> dict[str, Any]:
    return {
        "scientific_name": "Azadirachta indica",
        "family": "Meliaceae",
        "telugu_name": "Vepa",
        "telugu_script": "వేప",
        "common_name_english": "Neem",
        "hindi_name": "Neem",
        "confidence": 0.92,
        "identification_basis": "Mock response enabled by PLANTSAGE_MOCK_IDENTIFY.",
        "distinctive_features": ["pinnate leaves", "compound leaflets"],
        "similar_species": [],
        "rayalaseema_context": "Commonly planted and naturalized around settlements.",
    }


async def identify_plant(image_bytes: bytes, *, mime_type: str = "image/jpeg") -> dict[str, Any]:
    """Identify a plant photo using the Gemini API."""

    if os.getenv("PLANTSAGE_MOCK_IDENTIFY"):
        return _mock_identification()

    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("Set GEMINI_API_KEY before calling the Gemini API.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("Install google-genai or set PLANTSAGE_MOCK_IDENTIFY=1") from exc

    client = genai.Client(api_key=settings.gemini_api_key)
    model_name = settings.gemini_model or DEFAULT_GEMINI_MODEL
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    def generate() -> Any:
        return client.models.generate_content(
            model=model_name,
            contents=[image_part, IDENTIFICATION_PROMPT],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
        )

    response = await asyncio.to_thread(generate)
    raw = getattr(response, "text", "") or ""
    try:
        parsed = extract_json_object(raw)
    except ValueError:
        recovered = _fallback_identification_from_text(raw)
        if recovered:
            return recovered
        return {
            "scientific_name": None,
            "confidence": 0.0,
            "error": f"Could not parse Gemini response: {raw[:300]}",
        }

    parsed.setdefault("confidence", 0.0)
    return parsed
