"""Upload ingestion primitives for hash-addressed plant image storage."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import Path


ALLOWED_IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


@dataclass(frozen=True)
class UploadedImage:
    sha256: str
    path: Path
    mime_type: str
    size_bytes: int


def infer_extension(mime_type: str | None) -> str:
    normalized = (mime_type or "image/jpeg").split(";")[0].strip().lower()
    if normalized not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"Unsupported image MIME type: {mime_type or 'unknown'}")
    return ALLOWED_IMAGE_EXTENSIONS[normalized]


async def persist_upload(
    image_bytes: bytes,
    mime_type: str | None,
    *,
    upload_dir: str | Path = Path("data/uploads"),
) -> UploadedImage:
    if not image_bytes:
        raise ValueError("Cannot persist an empty upload.")

    extension = infer_extension(mime_type)
    digest = hashlib.sha256(image_bytes).hexdigest()
    target_dir = Path(upload_dir)
    target_path = target_dir / f"{digest}{extension}"

    def write_once() -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        if not target_path.exists():
            target_path.write_bytes(image_bytes)

    await asyncio.to_thread(write_once)
    return UploadedImage(
        sha256=digest,
        path=target_path,
        mime_type=(mime_type or "image/jpeg").split(";")[0].strip().lower(),
        size_bytes=len(image_bytes),
    )
