import asyncio
import builtins
import json

from reports.generator import generate_all_reports, generate_fallback_pdf, generate_pdf, slugify


def test_slugify_handles_botanical_names():
    assert slugify("Azadirachta indica (A.Juss.)") == "azadirachta_indica_a_juss"


def test_generate_all_reports_writes_markdown_and_json(tmp_path):
    research = {
        "scientific_name": "Azadirachta indica",
        "family": "Meliaceae",
        "telugu_name": "Vepa",
        "telugu_script": "వేప",
        "how_to_use": [
            {
                "purpose": "Leaf wash",
                "part_used": "leaf",
                "method": "Boil washed leaves and cool the liquid.",
                "quantity": "one handful leaves in 500 ml water",
                "frequency": "external use as needed",
                "safety_note": "Do not ingest concentrated preparations without a practitioner.",
            }
        ],
        "safety": {
            "toxicity": "low",
            "known_hazards": ["Avoid seed oil during pregnancy."],
        },
        "sources": ["Test citation"],
    }

    result = asyncio.run(generate_all_reports({"scientific_name": "Azadirachta indica"}, research, output_dir=tmp_path))

    md = tmp_path / result["markdown_filename"]
    js = tmp_path / result["json_filename"]

    assert md.exists()
    assert js.exists()
    assert "How to use it" in md.read_text(encoding="utf-8")
    assert "one handful leaves" in md.read_text(encoding="utf-8")
    assert json.loads(js.read_text(encoding="utf-8"))["scientific_name"] == "Azadirachta indica"


def test_fallback_pdf_writes_valid_pdf_header(tmp_path):
    pdf = generate_fallback_pdf(
        "Fallback report",
        "Azadirachta indica\nPlantSage fallback PDF",
        tmp_path / "fallback.pdf",
    )

    assert pdf.exists()
    assert pdf.read_bytes().startswith(b"%PDF-1.4")


def test_generate_pdf_falls_back_when_native_weasyprint_loader_fails(tmp_path, monkeypatch):
    md_path = tmp_path / "report.md"
    md_path.write_text("# Azadirachta indica\n\nFallback body", encoding="utf-8")

    original_import = builtins.__import__

    def fail_weasyprint_import(name, *args, **kwargs):
        if name == "weasyprint":
            raise OSError("cannot load library 'libpango-1.0-0'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_weasyprint_import)

    result = asyncio.run(
        generate_pdf(
            {"scientific_name": "Azadirachta indica"},
            "azadirachta_indica_test",
            md_path,
            output_dir=tmp_path,
        )
    )

    assert result["error"] == "WeasyPrint unavailable; fallback PDF generated (OSError)."
    assert (tmp_path / "azadirachta_indica_test.pdf").read_bytes().startswith(b"%PDF-1.4")
