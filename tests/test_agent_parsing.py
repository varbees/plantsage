import asyncio
from types import SimpleNamespace

from agent.plant_agent import extract_grounding_metadata, extract_json_object, research_plant


def test_extract_json_object_strips_markdown_fence():
    raw = """```json
    {"scientific_name": "Azadirachta indica", "confidence": 0.91}
    ```"""

    parsed = extract_json_object(raw)

    assert parsed["scientific_name"] == "Azadirachta indica"
    assert parsed["confidence"] == 0.91


def test_extract_json_object_finds_embedded_json():
    raw = 'Here is the report: {"scientific_name": "Calotropis gigantea", "safety": {"toxicity": "high"}}'

    parsed = extract_json_object(raw)

    assert parsed["scientific_name"] == "Calotropis gigantea"
    assert parsed["safety"]["toxicity"] == "high"


def test_extract_grounding_metadata_collects_unique_sources():
    response = SimpleNamespace(
        candidates=[
            SimpleNamespace(
                grounding_metadata=SimpleNamespace(
                    web_search_queries=["Azadirachta indica POWO"],
                    grounding_chunks=[
                        SimpleNamespace(web=SimpleNamespace(title="POWO", uri="https://powo.science.kew.org/taxon/123")),
                        SimpleNamespace(web=SimpleNamespace(title="POWO duplicate", uri="https://powo.science.kew.org/taxon/123")),
                        SimpleNamespace(web=SimpleNamespace(title="GBIF", uri="https://www.gbif.org/species/123")),
                    ],
                )
            )
        ]
    )

    metadata = extract_grounding_metadata(response)

    assert metadata["search_queries"] == ["Azadirachta indica POWO"]
    assert metadata["sources"] == [
        "POWO: https://powo.science.kew.org/taxon/123",
        "GBIF: https://www.gbif.org/species/123",
    ]


def test_gemini_research_adds_grounding_sources(monkeypatch):
    class FakeModels:
        def __init__(self):
            self.request = None

        def generate_content(self, **kwargs):
            self.request = kwargs
            return SimpleNamespace(
                text='{"scientific_name":"Azadirachta indica","sources":[],"how_to_use":[]}',
                candidates=[
                    SimpleNamespace(
                        grounding_metadata=SimpleNamespace(
                            web_search_queries=["Azadirachta indica medicinal uses"],
                            grounding_chunks=[
                                SimpleNamespace(web=SimpleNamespace(title="NCBI", uri="https://www.ncbi.nlm.nih.gov/example")),
                            ],
                        )
                    )
                ],
            )

    fake_models = FakeModels()
    fake_client = SimpleNamespace(models=fake_models)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("PLANTSAGE_MOCK_RESEARCH", raising=False)
    monkeypatch.delenv("PLANTSAGE_RESEARCH_PROVIDER", raising=False)

    report = asyncio.run(
        research_plant(
            {"scientific_name": "Azadirachta indica", "family": "Meliaceae", "confidence": 0.9},
            {"district": "Tirupati"},
            client=fake_client,
        )
    )

    assert fake_models.request["model"] == "gemini-2.5-flash"
    assert "NCBI: https://www.ncbi.nlm.nih.gov/example" in report["sources"]
    assert report["research_metadata"]["provider"] == "gemini"
    assert report["research_metadata"]["grounded"] is True
