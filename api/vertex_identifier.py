"""Vertex AI Gemini Vision plant identifier."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from agent.plant_agent import extract_json_object
from core.config import get_settings


DEFAULT_VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
DEFAULT_VERTEX_MODEL = os.getenv("VERTEX_GEMINI_MODEL", "gemini-2.5-flash")


IDENTIFICATION_PROMPT = """
You are a botanist specializing in South Indian flora, especially Rayalaseema:
Tirupati, Srikalahasti, Kadapa, Anantapur, Kurnool, Chittoor, Annamayya,
Seshachalam and dry Deccan thorn scrub habitats.

Identify the plant in this photo as precisely as possible. Be conservative.
Return ONLY valid JSON with this schema:
{
  "scientific_name": "Genus species (Author)",
  "family": "Family name",
  "telugu_name": "Telugu vernacular transliterated",
  "telugu_script": "Telugu script if known",
  "common_name_english": "Common English name",
  "hindi_name": "Hindi name if known",
  "confidence": 0.85,
  "identification_basis": "visible plant parts used for identification",
  "distinctive_features": ["feature 1", "feature 2"],
  "similar_species": ["similar species to consider"],
  "rayalaseema_context": "local occurrence or role if known"
}

If identification is not possible, return:
{"scientific_name": null, "confidence": 0.0, "error": "reason"}
"""


def _project_id() -> str:
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
    if not project_id:
        raise RuntimeError("Set GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT before calling Vertex AI.")
    return project_id


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


def _part_from_bytes(part_cls: Any, image_cls: Any, image_bytes: bytes, mime_type: str) -> Any:
    if hasattr(part_cls, "from_data"):
        return part_cls.from_data(data=image_bytes, mime_type=mime_type)

    suffix = ".jpg"
    if mime_type == "image/png":
        suffix = ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(image_bytes)
        temp_path = Path(handle.name)
    try:
        return part_cls.from_image(image_cls.load_from_file(str(temp_path)))
    finally:
        temp_path.unlink(missing_ok=True)


async def identify_plant(image_bytes: bytes, *, mime_type: str = "image/jpeg") -> dict[str, Any]:
    """Identify a plant photo using Vertex AI Gemini Vision."""

    if os.getenv("PLANTSAGE_MOCK_IDENTIFY"):
        return _mock_identification()

    try:
        get_settings().ensure_google_credentials_file()
        import vertexai
        from vertexai.generative_models import GenerativeModel, Image, Part
    except ImportError as exc:
        raise RuntimeError("Install google-cloud-aiplatform or set PLANTSAGE_MOCK_IDENTIFY=1") from exc

    vertexai.init(project=_project_id(), location=DEFAULT_VERTEX_LOCATION)
    model = GenerativeModel(DEFAULT_VERTEX_MODEL)
    image_part = _part_from_bytes(Part, Image, image_bytes, mime_type)

    async def generate() -> Any:
        return await model.generate_content_async(
            [image_part, IDENTIFICATION_PROMPT],
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 2048,
                "response_mime_type": "application/json",
            },
        )

    response = await generate()
    raw = getattr(response, "text", "") or ""
    try:
        parsed = extract_json_object(raw)
    except ValueError:
        return {
            "scientific_name": None,
            "confidence": 0.0,
            "error": f"Could not parse Gemini response: {raw[:300]}",
        }

    parsed.setdefault("confidence", 0.0)
    return parsed
