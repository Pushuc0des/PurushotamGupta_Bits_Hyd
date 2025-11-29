from __future__ import annotations

import mimetypes
import os
import tempfile
from pathlib import Path

import httpx

from bill_extraction_api.settings import AppSettings

SUPPORTED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}


class DocumentFetcher:
    """Download user-supplied documents to a temp file."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    async def fetch(self, url: str) -> Path:
        # Convert to string in case it's a Pydantic Url object
        url_str = str(url)
        timeout = httpx.Timeout(self._settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url_str)
            response.raise_for_status()

        content_type = response.headers.get("Content-Type") or mimetypes.guess_type(url_str)[0]
        if content_type not in SUPPORTED_MIME_TYPES:
            raise ValueError(f"Unsupported document type: {content_type}")

        max_bytes = self._settings.max_document_size_mb * 1024 * 1024
        if len(response.content) > max_bytes:
            raise ValueError("Document exceeds allowed size")

        suffix = SUPPORTED_MIME_TYPES[content_type]
        tmp_dir = Path(tempfile.mkdtemp(prefix="bill-api-"))
        tmp_path = tmp_dir / f"document{suffix}"
        tmp_path.write_bytes(response.content)
        return tmp_path

    @staticmethod
    def cleanup(path: Path) -> None:
        try:
            os.remove(path)
            os.rmdir(path.parent)
        except OSError:
            pass
