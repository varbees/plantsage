import asyncio

from pipeline.ingestion import infer_extension, persist_upload


def test_infer_extension_allows_supported_image_types():
    assert infer_extension("image/jpeg") == ".jpg"
    assert infer_extension("image/png") == ".png"
    assert infer_extension("image/webp") == ".webp"


def test_persist_upload_deduplicates_by_hash(tmp_path):
    payload = b"fake-image-bytes"

    first = asyncio.run(persist_upload(payload, "image/jpeg", upload_dir=tmp_path))
    second = asyncio.run(persist_upload(payload, "image/jpeg", upload_dir=tmp_path))

    assert first.sha256 == second.sha256
    assert first.path == second.path
    assert first.path.exists()
    assert first.size_bytes == len(payload)
