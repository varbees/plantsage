"""Markdown, JSON, and optional PDF report generator for PlantSage."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


GENERATED_REPORTS_DIR = Path(os.getenv("PLANTSAGE_REPORTS_DIR", "/tmp/plantsage/generated_reports" if os.getenv("VERCEL") else "generated_reports"))


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "unknown_plant").lower()).strip("_")
    return slug or "unknown_plant"


async def generate_all_reports(
    plant_id: dict[str, Any],
    research: dict[str, Any],
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Write JSON, Markdown, and PDF-if-available reports."""

    report_dir = Path(output_dir) if output_dir else GENERATED_REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify(research.get("scientific_name") or plant_id.get("scientific_name") or "unknown_plant")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{slug}_{timestamp}"

    json_path = report_dir / f"{base_name}.json"
    json_path.write_text(json.dumps(research, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = await generate_markdown(research, base_name, output_dir=report_dir)
    pdf_result = await generate_pdf(research, base_name, md_path, output_dir=report_dir)

    result: dict[str, Any] = {
        "slug": slug,
        "base_name": base_name,
        "json_path": str(json_path),
        "json_filename": json_path.name,
        "markdown_path": str(md_path),
        "markdown_filename": md_path.name,
    }
    if pdf_result.get("path"):
        pdf_path = Path(pdf_result["path"])
        result["pdf_path"] = str(pdf_path)
        result["pdf_filename"] = pdf_path.name
    if pdf_result.get("error"):
        result["pdf_error"] = pdf_result["error"]
    return result


def _append_mapping(lines: list[str], mapping: dict[str, Any], keys: list[tuple[str, str]]) -> None:
    for label, key in keys:
        value = mapping.get(key)
        if value:
            lines.append(f"**{label}:** {value}")


def _append_list(lines: list[str], items: list[Any] | None) -> None:
    for item in items or []:
        if item:
            lines.append(f"- {item}")


async def generate_markdown(
    research: dict[str, Any],
    base_name: str,
    *,
    output_dir: str | Path | None = None,
) -> Path:
    report_dir = Path(output_dir) if output_dir else GENERATED_REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    sci = research.get("scientific_name") or "Unknown plant"
    family = research.get("family") or "Unknown family"
    telugu = research.get("telugu_name") or "Unknown Telugu name"
    telugu_script = research.get("telugu_script") or ""

    lines = [
        f"# {sci}",
        "",
        f"**Family:** {family}",
        f"**Telugu:** {telugu}{f' ({telugu_script})' if telugu_script else ''}",
        f"**Generated:** {datetime.now().strftime('%d %B %Y, %H:%M')}",
        "",
        "> Educational field report only. Consult a qualified Ayurvedic practitioner before internal use of any new herb.",
        "",
        "---",
        "",
    ]

    names = research.get("names_by_language") or {}
    if names:
        lines += ["## Names across languages", ""]
        for language, name in names.items():
            if name:
                lines.append(f"- **{language}:** {name}")
        lines.append("")

    botany = research.get("botanical_description") or {}
    if botany:
        lines += ["## What it looks like", ""]
        _append_mapping(
            lines,
            botany,
            [
                ("Habit", "habit"),
                ("Height", "height_m"),
                ("Leaves", "leaves"),
                ("Flowers", "flowers"),
                ("Fruit/seed", "fruit_seed"),
            ],
        )
        marks = botany.get("distinctive_field_marks") or []
        if marks:
            lines += ["", "**Field ID marks:**"]
            _append_list(lines, marks)
        lines.append("")

    habitat = research.get("rayalaseema_habitat") or {}
    if habitat:
        lines += ["## Where to find it in Rayalaseema", ""]
        _append_mapping(
            lines,
            habitat,
            [
                ("Ecoregion", "ecoregion"),
                ("Microhabitat", "microhabitat"),
                ("Altitude", "altitude_m"),
                ("Seasonality", "seasonality"),
            ],
        )
        if habitat.get("districts"):
            lines.append(f"**Districts:** {', '.join(habitat['districts'])}")
        if habitat.get("associated_species"):
            lines.append(f"**Associated species:** {', '.join(habitat['associated_species'])}")
        lines.append("")

    folk_uses = research.get("folk_medicine_AP") or []
    if folk_uses:
        lines += ["## What tribal communities use it for", ""]
        for use in folk_uses:
            lines.append(f"### {use.get('ailment') or 'Documented use'}")
            _append_mapping(
                lines,
                use,
                [
                    ("Community", "community"),
                    ("Part used", "part_used"),
                    ("Preparation", "preparation"),
                    ("How to use", "dosage_usage"),
                    ("Source", "source_citation"),
                ],
            )
            lines.append("")

    how_to_use = research.get("how_to_use") or []
    lines += ["## How to use it", ""]
    if how_to_use:
        for index, method in enumerate(how_to_use, 1):
            lines.append(f"### {index}. {method.get('purpose') or 'Use'}")
            _append_mapping(
                lines,
                method,
                [
                    ("Part", "part_used"),
                    ("Method", "method"),
                    ("Quantity", "quantity"),
                    ("Frequency", "frequency"),
                ],
            )
            if method.get("safety_note"):
                lines.append(f"> CAUTION: {method['safety_note']}")
            lines.append("")
    else:
        lines += [
            "No practical use method was found in the researched sources.",
            "",
            "> CAUTION: Do not infer medicinal use from identification alone.",
            "",
        ]

    ayurveda = research.get("ayurveda") or {}
    if ayurveda:
        lines += ["## Ayurvedic profile", ""]
        _append_mapping(
            lines,
            ayurveda,
            [
                ("Classical name", "classical_name"),
                ("Virya", "virya"),
                ("Vipaka", "vipaka"),
                ("Dosha action", "dosha_action"),
            ],
        )
        for label, key in [("Rasa", "rasa"), ("Guna", "guna"), ("Karma", "karma")]:
            if ayurveda.get(key):
                lines.append(f"**{label}:** {', '.join(ayurveda[key])}")
        if ayurveda.get("classical_indications"):
            lines += ["", "**Classical indications:**"]
            _append_list(lines, ayurveda["classical_indications"])
        if ayurveda.get("formulations"):
            lines += ["", "**Formulations:**"]
            _append_list(lines, ayurveda["formulations"])
        lines.append("")

    compounds = research.get("active_compounds") or []
    if compounds:
        lines += ["## Key active compounds", ""]
        for compound in compounds:
            cite = f" [{compound['citation']}]" if compound.get("citation") else ""
            lines.append(
                f"- **{compound.get('compound') or 'Compound'}**"
                f" ({compound.get('type') or 'type unknown'}): {compound.get('activity') or ''}{cite}"
            )
        lines.append("")

    safety = research.get("safety") or {}
    if safety:
        lines += ["## Safety information", ""]
        _append_mapping(
            lines,
            safety,
            [
                ("Toxicity", "toxicity"),
                ("Toxic parts", "toxic_parts"),
                ("Drug interactions", "drug_interactions"),
                ("First aid", "first_aid"),
            ],
        )
        if safety.get("known_hazards"):
            lines += ["", "**Known hazards:**"]
            _append_list(lines, safety["known_hazards"])
        if safety.get("contraindications"):
            lines += ["", "**Contraindications:**"]
            _append_list(lines, safety["contraindications"])
        lines.append("")

    ecology = research.get("ecology") or {}
    if ecology:
        lines += ["## Ecological role", ""]
        _append_mapping(
            lines,
            ecology,
            [
                ("Role", "role"),
                ("Wildlife value", "wildlife_value"),
                ("Invasive status", "invasive_status"),
                ("Conservation status", "conservation_status"),
            ],
        )
        if ecology.get("pollinators"):
            lines.append(f"**Pollinators:** {', '.join(ecology['pollinators'])}")
        if ecology.get("seed_dispersers"):
            lines.append(f"**Seed dispersers:** {', '.join(ecology['seed_dispersers'])}")
        lines.append("")

    culture = research.get("cultural_significance") or {}
    if culture:
        lines += ["## Cultural and religious significance", ""]
        _append_mapping(
            lines,
            culture,
            [
                ("Religious use", "religious_use"),
                ("Srikalahasti connection", "srikalahasti_connection"),
                ("Telugu proverbs", "telugu_proverbs"),
            ],
        )
        if culture.get("folk_beliefs"):
            lines += ["", "**Folk beliefs:**"]
            _append_list(lines, culture["folk_beliefs"])
        if culture.get("practical_traditional_uses"):
            lines += ["", "**Practical traditional uses:**"]
            _append_list(lines, culture["practical_traditional_uses"])
        lines.append("")

    skill = research.get("skill_insights") or {}
    if skill:
        lines += ["## Field skills", ""]
        if skill.get("identification_tips"):
            lines += ["**Quick ID tips:**"]
            _append_list(lines, skill["identification_tips"])
        if skill.get("common_confusions"):
            lines += ["", "**Do not confuse with:**"]
            _append_list(lines, skill["common_confusions"])
        _append_mapping(
            lines,
            skill,
            [
                ("Best observation season", "best_observation_season"),
                ("Forager notes", "forager_notes"),
            ],
        )
        lines.append("")

    sources = research.get("sources") or []
    if sources:
        lines += ["## Sources and citations", ""]
        _append_list(lines, sources)
        lines.append("")

    md_path = report_dir / f"{base_name}.md"
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return md_path


async def generate_pdf(
    research: dict[str, Any],
    base_name: str,
    md_path: Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, str | None]:
    report_dir = Path(output_dir) if output_dir else GENERATED_REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    try:
        import markdown2
        from weasyprint import HTML
    except Exception as exc:
        pdf_path = report_dir / f"{base_name}.pdf"
        generate_fallback_pdf(research.get("scientific_name") or "PlantSage report", md_path.read_text(encoding="utf-8"), pdf_path)
        return {"path": str(pdf_path), "error": f"WeasyPrint unavailable; fallback PDF generated ({exc.__class__.__name__})."}

    md_content = md_path.read_text(encoding="utf-8")
    html_body = markdown2.markdown(md_content, extras=["tables", "fenced-code-blocks"])
    title = research.get("scientific_name") or "PlantSage report"
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PlantSage - {title}</title>
<style>
  @page {{ margin: 20mm 18mm; }}
  body {{ color: #142018; font-family: Georgia, serif; line-height: 1.55; }}
  h1 {{ color: #123d2d; font-size: 28px; border-bottom: 2px solid #3a7a55; padding-bottom: 8px; }}
  h2 {{ color: #276047; font-size: 19px; margin-top: 28px; }}
  h3 {{ color: #345235; font-size: 15px; margin-bottom: 4px; }}
  blockquote {{ border-left: 4px solid #b45f2a; margin-left: 0; padding: 8px 14px; background: #fff4e7; }}
  li {{ margin-bottom: 3px; }}
  code {{ background: #eff4ee; padding: 1px 4px; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    pdf_path = report_dir / f"{base_name}.pdf"
    try:
        HTML(string=html).write_pdf(str(pdf_path))
        return {"path": str(pdf_path), "error": None}
    except Exception as exc:
        generate_fallback_pdf(title, md_content, pdf_path)
        return {"path": str(pdf_path), "error": f"WeasyPrint failed; fallback PDF generated ({exc.__class__.__name__})."}


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generate_fallback_pdf(title: str, text: str, path: Path) -> Path:
    """Write a small valid text-only PDF without native dependencies."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [title, "", *text.splitlines()]
    visible_lines = [line[:96] for line in lines if line.strip()][:42]

    content_lines = ["BT", "/F1 12 Tf", "50 790 Td", "16 TL"]
    for index, line in enumerate(visible_lines):
        if index:
            content_lines.append("T*")
        content_lines.append(f"({_pdf_escape(line)}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    output = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(bytes(output))
    return path
