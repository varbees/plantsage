from agent.plant_agent import extract_json_object


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
