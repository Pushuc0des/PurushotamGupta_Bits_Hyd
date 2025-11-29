from __future__ import annotations

import re
from typing import List, Sequence

from bill_extraction_api.app.schemas import BillItem
from bill_extraction_api.services.ocr import OCRLine

_AMOUNT_RE = re.compile(r"(?<!\d)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.\d+)(?!\d)")
_SECTION_HINTS = {"charges", "services", "fee", "room", "surgery", "pharmacy", "summary"}


def _to_float(token: str) -> float:
    token = token.replace(",", "")
    try:
        return float(token)
    except ValueError:
        return 0.0


def _looks_like_section(text: str) -> bool:
    lower = text.lower()
    return any(hint in lower for hint in _SECTION_HINTS) and not _AMOUNT_RE.search(text)


def _strip_numbers(text: str, matches: Sequence[re.Match[str]]) -> str:
    cleaned = text
    for match in reversed(matches):
        cleaned = cleaned[: match.start()] + cleaned[match.end() :]
    return " ".join(cleaned.split()).strip("-|: ")


class LineItemParser:
    """Best-effort parser that converts OCR lines into structured rows."""

    def parse(self, lines: Sequence[OCRLine]) -> List[BillItem]:
        sorted_lines = sorted(lines, key=lambda line: sum(pt[1] for pt in line.bbox) / len(line.bbox))
        section_prefix = ""
        items: List[BillItem] = []
        for line in sorted_lines:
            text = line.text.strip()
            if not text:
                continue

            matches = list(_AMOUNT_RE.finditer(text))
            if not matches:
                if _looks_like_section(text):
                    section_prefix = text.strip()
                continue

            amount = _to_float(matches[-1].group())
            rate = _to_float(matches[-2].group()) if len(matches) >= 2 else None
            quantity = _to_float(matches[-3].group()) if len(matches) >= 3 else None

            if quantity is not None and quantity == 0:
                quantity = None
            if rate is not None and rate == 0:
                rate = None

            descriptor = _strip_numbers(text, matches).strip()
            if not descriptor:
                descriptor = "Line Item"
            if section_prefix:
                descriptor = f"{section_prefix} | {descriptor}"

            items.append(
                BillItem(
                    item_name=descriptor,
                    item_amount=round(amount, 2),
                    item_rate=round(rate, 2) if rate is not None else None,
                    item_quantity=round(quantity, 2) if quantity is not None else None,
                )
            )
        return items
