from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFilter
from skimage import exposure


class DocumentPreprocessor:
    """Turns PDFs/images into a normalised list of PIL images."""

    def __init__(self, dpi: int = 300) -> None:
        self._dpi = dpi

    def to_images(self, document_path: Path) -> List[Image.Image]:
        suffix = document_path.suffix.lower()
        if suffix == ".pdf":
            images = convert_from_path(document_path.as_posix(), dpi=self._dpi)
        else:
            images = [Image.open(document_path).convert("RGB")]
        return [self._enhance(img) for img in images]

    def _enhance(self, image: Image.Image) -> Image.Image:
        # Convert to grayscale for denoising
        gray = image.convert("L")
        arr = np.asarray(gray).astype("float32")
        # Normalize to 0-1 range for equalize_adapthist
        arr = arr / 255.0
        arr = exposure.equalize_adapthist(arr, clip_limit=0.03)
        # Convert back to 0-255 range
        arr = (arr * 255).astype("uint8")
        enhanced = Image.fromarray(arr)
        enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))
        return enhanced
