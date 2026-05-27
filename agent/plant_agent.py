"""Claude-backed plant research agent for PlantSage.

The Anthropic web search tool is a server-side Messages API tool: the API
performs the search iterations inside a single request and returns the final
answer with search-result blocks/citations in the response content.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any


DEFAULT_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
DEFAULT_WEB_SEARCH_TOOL = os.getenv("ANTHROPIC_WEB_SEARCH_TOOL", "web_search_20250305")
DEFAULT_MAX_SEARCHES = int(os.getenv("PLANTSAGE_MAX_SEARCHES", "12"))


RESEARCH_SYSTEM = """
You are PlantSage: an expert botanist, ethnobotanist, and Ayurvedic
pharmacology research agent specializing in Rayalaseema, Andhra Pradesh.

Region focus:
- Districts: Tirupati, Srikalahasti, Kadapa/YSR, Anantapur, Kurnool, Chittoor,
  Annamayya
- Ecoregion: Deccan thorn scrub forest and Southern Tropical Thorn Forest
- Communities: Yanadi, Chenchu, Yerukala, Sugali, Konda Reddy
- Sacred context: Srikalahasti, Shiva worship, Vayu sthala, Tirumala/Seshachalam

Research priority order:
1. Botany and distribution: eFlora of India, Flora of Andhra Pradesh, GBIF,
   Plants of the World Online, district floras
2. Rayalaseema ethnomedicine: Chittoor/Kadapa/Kurnool/Tirupati surveys,
   Seshachalam Biosphere Reserve, Lankamalleswara WLS, Vedavathy 1997 Chittoor
3. Ayurveda: classical drug names, Nighantu entries, rasa/guna/virya/vipaka,
   formulations, known practitioner cautions
4. Phytochemistry/pharmacology: PubMed, PMC, DOI-backed sources
5. Practical how-to-use: exact preparation methods, quantities, route,
   frequency, and safety caveats only where supported
6. Ecology and culture: dry scrubland role, pollinators, invasiveness,
   practical traditional uses, Srikalahasti/Shaiva context when relevant

Return ONLY valid JSON. Do not wrap in markdown. Follow this schema:
{
  "scientific_name": "Genus species (Author)",
  "family": "Family",
  "telugu_name": "primary Telugu name",
  "telugu_variants": ["variant"],
  "telugu_script": "Telugu script",
  "names_by_language": {
    "Hindi": "", "Tamil": "", "Kannada": "", "Sanskrit": "",
    "Malayalam": "", "Marathi": ""
  },
  "botanical_description": {
    "habit": "",
    "height_m": "",
    "leaves": "",
    "flowers": "",
    "fruit_seed": "",
    "distinctive_field_marks": []
  },
  "rayalaseema_habitat": {
    "ecoregion": "",
    "microhabitat": "",
    "associated_species": [],
    "districts": [],
    "altitude_m": "",
    "seasonality": ""
  },
  "folk_medicine_AP": [
    {
      "community": "",
      "ailment": "",
      "part_used": "",
      "preparation": "",
      "dosage_usage": "",
      "source_citation": ""
    }
  ],
  "ayurveda": {
    "classical_name": "",
    "rasa": [],
    "guna": [],
    "virya": "",
    "vipaka": "",
    "dosha_action": "",
    "karma": [],
    "classical_indications": [],
    "classical_texts_cited": [],
    "formulations": []
  },
  "how_to_use": [
    {
      "purpose": "",
      "method": "",
      "part_used": "",
      "quantity": "",
      "frequency": "",
      "safety_note": ""
    }
  ],
  "active_compounds": [
    {
      "compound": "",
      "type": "",
      "activity": "",
      "citation": ""
    }
  ],
  "safety": {
    "toxicity": "",
    "toxic_parts": "",
    "known_hazards": [],
    "contraindications": [],
    "drug_interactions": "",
    "first_aid": ""
  },
  "ecology": {
    "role": "",
    "pollinators": [],
    "seed_dispersers": [],
    "wildlife_value": "",
    "invasive_status": "",
    "conservation_status": ""
  },
  "cultural_significance": {
    "religious_use": "",
    "srikalahasti_connection": "",
    "festivals": [],
    "folk_beliefs": [],
    "telugu_proverbs": "",
    "practical_traditional_uses": []
  },
  "skill_insights": {
    "identification_tips": [],
    "common_confusions": [],
    "best_observation_season": "",
    "nearby_associated_species": [],
    "forager_notes": ""
  },
  "sources": []
}

Safety rules:
- Always include a practical how_to_use section, but never invent quantities.
- If internal use is unsafe or undocumented, say so clearly in safety_note.
- Never recommend internal use of Calotropis latex, Datura, Nerium, Lantana, or
  Gloriosa.
- Always include: consult a qualified Ayurvedic practitioner before internal use.
"""


def _strip_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    return cleaned


def extract_json_object(raw: str) -> dict[str, Any]:
    """Extract a JSON object from a model response."""

    cleaned = _strip_markdown_fence(raw)
    decoder = json.JSONDecoder()

    try:
        parsed, _ = decoder.raw_decode(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    for match in re.finditer(r"\{", cleaned):
        candidate = cleaned[match.start() :].lstrip()
        try:
            parsed, _ = decoder.raw_decode(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("No valid JSON object found in model response")


def extract_text_from_response(response: Any) -> str:
    """Collect text blocks from an Anthropic Messages response."""

    chunks: list[str] = []
    for block in getattr(response, "content", []) or []:
        text = getattr(block, "text", None)
        block_type = getattr(block, "type", None)
        if text and (block_type in (None, "text") or hasattr(block, "text")):
            chunks.append(text)
    return "\n".join(chunks).strip()


def _research_prompt(plant_id: dict[str, Any], location_context: dict[str, Any] | None) -> str:
    district = (location_context or {}).get("district", "Tirupati")
    latitude = (location_context or {}).get("latitude")
    longitude = (location_context or {}).get("longitude")
    features = plant_id.get("distinctive_features") or []
    if isinstance(features, list):
        feature_text = ", ".join(str(feature) for feature in features)
    else:
        feature_text = str(features)

    return f"""Research this plant for the Rayalaseema Flora Knowledge Base.

Scientific name: {plant_id.get("scientific_name") or "unknown"}
Family: {plant_id.get("family") or "unknown"}
Telugu name from identifier: {plant_id.get("telugu_name") or "unknown"}
Observed near: {district}, Andhra Pradesh
Coordinates: {latitude}, {longitude}
Identifier confidence: {plant_id.get("confidence")}
Identifier notes: {plant_id.get("identification_basis") or ""}
Visible distinctive features: {feature_text}

Run focused web research across the priority source order in the system prompt.
Return the complete PlantSage Report JSON only."""


def _mock_research_report(plant_id: dict[str, Any], location_context: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "scientific_name": plant_id.get("scientific_name") or "Unknown plant",
        "family": plant_id.get("family") or "Unknown",
        "telugu_name": plant_id.get("telugu_name") or "",
        "telugu_variants": [],
        "telugu_script": plant_id.get("telugu_script") or "",
        "names_by_language": {},
        "botanical_description": {
            "habit": "",
            "height_m": "",
            "leaves": "",
            "flowers": "",
            "fruit_seed": "",
            "distinctive_field_marks": plant_id.get("distinctive_features") or [],
        },
        "rayalaseema_habitat": {
            "ecoregion": "Deccan thorn scrub / dry deciduous Rayalaseema context",
            "microhabitat": "",
            "associated_species": [],
            "districts": [(location_context or {}).get("district", "Tirupati")],
            "altitude_m": "",
            "seasonality": "",
        },
        "folk_medicine_AP": [],
        "ayurveda": {},
        "how_to_use": [
            {
                "purpose": "Learning placeholder",
                "method": "Live Claude research was skipped because PLANTSAGE_MOCK_RESEARCH is enabled.",
                "part_used": "",
                "quantity": "",
                "frequency": "",
                "safety_note": "Consult a qualified Ayurvedic practitioner before internal use of any new herb.",
            }
        ],
        "active_compounds": [],
        "safety": {
            "toxicity": "unknown",
            "known_hazards": ["Live safety research was not run."],
            "contraindications": ["Do not use medicinally from this mock report."],
        },
        "ecology": {},
        "cultural_significance": {},
        "skill_insights": {
            "identification_tips": plant_id.get("distinctive_features") or [],
            "common_confusions": plant_id.get("similar_species") or [],
        },
        "sources": [],
    }


async def research_plant(
    plant_id: dict[str, Any],
    location_context: dict[str, Any] | None = None,
    *,
    client: Any | None = None,
) -> dict[str, Any]:
    """Run Claude web research and return a structured PlantSage report."""

    if os.getenv("PLANTSAGE_MOCK_RESEARCH"):
        return _mock_research_report(plant_id, location_context)

    scientific_name = plant_id.get("scientific_name")
    if not scientific_name:
        return {
            "scientific_name": None,
            "error": "Cannot research plant without a scientific_name from the identifier.",
        }

    if client is None:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("Install anthropic or set PLANTSAGE_MOCK_RESEARCH=1") from exc
        client = anthropic.Anthropic()

    tools = [
        {
            "type": DEFAULT_WEB_SEARCH_TOOL,
            "name": "web_search",
            "max_uses": DEFAULT_MAX_SEARCHES,
            "user_location": {
                "type": "approximate",
                "city": "Srikalahasti",
                "region": "Andhra Pradesh",
                "country": "IN",
                "timezone": "Asia/Kolkata",
            },
        }
    ]

    def create_message() -> Any:
        return client.messages.create(
            model=DEFAULT_ANTHROPIC_MODEL,
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "12000")),
            system=RESEARCH_SYSTEM,
            messages=[{"role": "user", "content": _research_prompt(plant_id, location_context)}],
            tools=tools,
        )

    response = await asyncio.to_thread(create_message)
    text = extract_text_from_response(response)
    try:
        report = extract_json_object(text)
    except ValueError:
        return {
            "scientific_name": scientific_name,
            "raw_report": text,
            "error": "Claude response did not contain parseable PlantSage JSON.",
        }

    report.setdefault("scientific_name", scientific_name)
    report.setdefault("sources", [])
    return report
