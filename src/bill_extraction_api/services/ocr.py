from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol

import numpy as np
from PIL import Image

from bill_extraction_api.settings import AppSettings


@dataclass
class OCRLine:
    text: str
    bbox: List[List[float]]
    confidence: float


class OCREngine(Protocol):
    def extract(self, image: Image.Image) -> List[OCRLine]:
        ...


class RapidOCREngine:
    def __init__(self) -> None:
        try:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore
        except ImportError as exc:  # pragma: no cover - import safety
            raise RuntimeError(
                "rapidocr-onnxruntime is required for the default OCR backend"
            ) from exc

        self._ocr = RapidOCR()

    def extract(self, image: Image.Image) -> List[OCRLine]:
        np_img = np.array(image.convert("RGB"))
        result, _ = self._ocr(np_img)
        lines: List[OCRLine] = []
        if not result:
            return lines
        for box, text, score in result:
            if not text:
                continue
            lines.append(OCRLine(text=text.strip(), bbox=box, confidence=float(score)))
        return lines


class DummyOCREngine:
    """Fallback that returns an empty result set."""

    def extract(self, image: Image.Image) -> List[OCRLine]:  # pragma: no cover - trivial
        return []


def resolve_engine(settings: AppSettings) -> OCREngine:
    if settings.ocr_backend == "rapidocr":
        return RapidOCREngine()
    return DummyOCREngine()
