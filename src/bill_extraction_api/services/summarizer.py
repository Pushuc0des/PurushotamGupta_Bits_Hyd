from __future__ import annotations

from contextlib import suppress
from typing import List

from loguru import logger

from bill_extraction_api.app.schemas import ExtractionData, PageLineItems
from bill_extraction_api.services.document_fetcher import DocumentFetcher
from bill_extraction_api.services.llm_parser import LLMParser
from bill_extraction_api.services.ocr import resolve_engine
from bill_extraction_api.services.parser import LineItemParser
from bill_extraction_api.services.preprocess import DocumentPreprocessor
from bill_extraction_api.settings import AppSettings


class ExtractionService:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._fetcher = DocumentFetcher(settings)
        self._preprocessor = DocumentPreprocessor()
        self._ocr = resolve_engine(settings)
        
        # Initialize parser based on backend setting
        if settings.parser_backend in ("llm", "hybrid"):
            self._llm_parser = LLMParser(settings)
        else:
            self._llm_parser = None
            
        if settings.parser_backend in ("regex", "hybrid"):
            self._regex_parser = LineItemParser()
        else:
            self._regex_parser = None

    async def extract(self, document_url: str) -> ExtractionData:
        temp_path = await self._fetcher.fetch(document_url)
        try:
            images = self._preprocessor.to_images(temp_path)
            pages: List[PageLineItems] = []
            
            # Reset token usage at start of extraction
            if self._llm_parser:
                self._llm_parser.reset_token_usage()
            
            for idx, image in enumerate(images, start=1):
                lines = self._ocr.extract(image)
                
                # Use appropriate parser based on backend
                if self._settings.parser_backend == "llm":
                    bill_items, page_type = await self._llm_parser.parse(lines, page_number=idx)
                elif self._settings.parser_backend == "regex":
                    bill_items = self._regex_parser.parse(lines)
                    page_type = self._infer_page_type(lines)
                elif self._settings.parser_backend == "hybrid":
                    # Try LLM first, fallback to regex on error
                    try:
                        bill_items, page_type = await self._llm_parser.parse(lines, page_number=idx)
                    except Exception as e:
                        logger.warning(f"LLM parsing failed for page {idx}, falling back to regex: {e}")
                        bill_items = self._regex_parser.parse(lines)
                        page_type = self._infer_page_type(lines)
                else:
                    raise ValueError(f"Unknown parser_backend: {self._settings.parser_backend}")
                
                if not bill_items:
                    continue
                    
                pages.append(
                    PageLineItems(
                        page_no=str(idx),
                        page_type=page_type,
                        bill_items=bill_items,
                    )
                )
            total_items = sum(len(page.bill_items) for page in pages)
            return ExtractionData(pagewise_line_items=pages, total_item_count=total_items)
        finally:
            with suppress(Exception):
                DocumentFetcher.cleanup(temp_path)

    def get_token_usage(self) -> dict[str, int]:
        """Get token usage from LLM parser if available."""
        if self._llm_parser:
            return self._llm_parser.get_token_usage()
        return {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0}

    @staticmethod
    def _infer_page_type(lines):
        joined = " ".join(line.text.lower() for line in lines)
        if "final bill" in joined or "discharge summary" in joined:
            return "Final Bill"
        if "pharmacy" in joined:
            return "Pharmacy"
        return "Bill Detail"
