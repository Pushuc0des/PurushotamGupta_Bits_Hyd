from __future__ import annotations

import json
from typing import List

from loguru import logger

from bill_extraction_api.app.schemas import BillItem
from bill_extraction_api.services.ocr import OCRLine
from bill_extraction_api.settings import AppSettings

# The expert prompt for medical bill extraction
LLM_PROMPT_TEMPLATE = """You are an expert document understanding system trained for medical bill extraction.

Your job is to convert OCR text from a bill page into structured line items.

⚠ VERY IMPORTANT RULES:

- Only extract true bill line items (services/medications/charges).

- Ignore totals, sub-totals, taxes, discounts, summary sections.

- Do NOT include duplicate items.

- If the bill shows subtotal lines, ignore them completely.

- Extract item_name exactly as shown in the OCR text.

- Extract item_quantity, item_rate, item_amount exactly as printed.

- If a value is missing or unreadable, use null.

- Remove garbage OCR characters.

- Preserve ordering from top to bottom.

Your output MUST strictly follow this JSON format:

{{
  "page_type": "Bill Detail",
  "bill_items": [
    {{
      "item_name": "",
      "item_quantity": null,
      "item_rate": null,
      "item_amount": null
    }}
  ]
}}

Do not add any explanation outside the JSON.

Return ONLY the JSON object.

OCR Text from bill page:
{ocr_text}
"""


class TokenUsage:
    """Tracks token usage for LLM calls."""

    def __init__(self) -> None:
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens

    def to_dict(self) -> dict:
        return {
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


class LLMParser:
    """LLM-based parser that uses AI to extract structured line items from OCR text."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._token_usage = TokenUsage()
        self._client = self._create_client()

    def _create_client(self):
        """Create the appropriate LLM client based on provider."""
        if self._settings.parser_backend == "regex":
            return None

        provider = self._settings.llm_provider

        if provider == "openai":
            try:
                from openai import AsyncOpenAI

                api_key = self._settings.openai_api_key
                if not api_key:
                    raise ValueError(
                        "BILL_API_OPENAI_API_KEY environment variable is required for OpenAI provider"
                    )
                return AsyncOpenAI(api_key=api_key)
            except ImportError:
                raise RuntimeError(
                    "openai package is required. Install with: pip install openai"
                )

        elif provider == "anthropic":
            try:
                from anthropic import AsyncAnthropic

                api_key = self._settings.anthropic_api_key
                if not api_key:
                    raise ValueError(
                        "BILL_API_ANTHROPIC_API_KEY environment variable is required for Anthropic provider"
                    )
                return AsyncAnthropic(api_key=api_key)
            except ImportError:
                raise RuntimeError(
                    "anthropic package is required. Install with: pip install anthropic"
                )

        elif provider == "local":
            # For local models, you'd integrate with Ollama, vLLM, etc.
            raise NotImplementedError("Local model support not yet implemented")

        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    def _format_ocr_text(self, lines: List[OCRLine]) -> str:
        """Format OCR lines into a readable text block, preserving order."""
        sorted_lines = sorted(
            lines, key=lambda line: sum(pt[1] for pt in line.bbox) / len(line.bbox)
        )
        return "\n".join(line.text.strip() for line in sorted_lines if line.text.strip())

    async def _call_openai(self, prompt: str) -> tuple[str, dict]:
        """Call OpenAI API and return response with token usage."""
        response = await self._client.chat.completions.create(
            model=self._settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a medical bill extraction expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=self._settings.llm_temperature,
            max_tokens=self._settings.llm_max_tokens,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        usage = response.usage
        token_info = {
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
        return content, token_info

    async def _call_anthropic(self, prompt: str) -> tuple[str, dict]:
        """Call Anthropic API and return response with token usage."""
        response = await self._client.messages.create(
            model=self._settings.llm_model,
            max_tokens=self._settings.llm_max_tokens,
            temperature=self._settings.llm_temperature,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        content = response.content[0].text if response.content else "{}"
        token_info = {
            "input_tokens": response.usage.input_tokens if response.usage else 0,
            "output_tokens": response.usage.output_tokens if response.usage else 0,
        }
        return content, token_info

    async def parse(self, lines: List[OCRLine], page_number: int = 1) -> tuple[List[BillItem], str]:
        """
        Parse OCR lines using LLM and return bill items with page type.

        Returns:
            Tuple of (bill_items, page_type)
        """
        if not self._client:
            raise RuntimeError("LLM client not initialized. Check parser_backend setting.")

        ocr_text = self._format_ocr_text(lines)
        if not ocr_text.strip():
            logger.warning(f"Empty OCR text for page {page_number}")
            return [], "Bill Detail"

        prompt = LLM_PROMPT_TEMPLATE.format(ocr_text=ocr_text)

        try:
            provider = self._settings.llm_provider
            if provider == "openai":
                response_text, token_info = await self._call_openai(prompt)
            elif provider == "anthropic":
                response_text, token_info = await self._call_anthropic(prompt)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            # Track token usage
            self._token_usage.add(token_info["input_tokens"], token_info["output_tokens"])

            # Parse JSON response
            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}\nResponse: {response_text[:500]}")
                # Try to extract JSON from markdown code blocks
                if "```json" in response_text:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    if end > start:
                        response_text = response_text[start:end].strip()
                        response_json = json.loads(response_text)
                elif "```" in response_text:
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    if end > start:
                        response_text = response_text[start:end].strip()
                        response_json = json.loads(response_text)
                else:
                    raise

            # Extract bill items
            bill_items = []
            page_type = response_json.get("page_type", "Bill Detail")

            for item_data in response_json.get("bill_items", []):
                try:
                    bill_item = BillItem(
                        item_name=item_data.get("item_name", "").strip(),
                        item_amount=float(item_data["item_amount"])
                        if item_data.get("item_amount") is not None
                        else None,
                        item_rate=float(item_data["item_rate"])
                        if item_data.get("item_rate") is not None
                        else None,
                        item_quantity=float(item_data["item_quantity"])
                        if item_data.get("item_quantity") is not None
                        else None,
                    )
                    # Validate that item_amount is present (required field)
                    if bill_item.item_amount is not None:
                        bill_items.append(bill_item)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid bill item: {item_data}, error: {e}")
                    continue

            logger.info(
                f"LLM extracted {len(bill_items)} items from page {page_number} "
                f"(tokens: {token_info['input_tokens']} in, {token_info['output_tokens']} out)"
            )
            return bill_items, page_type

        except Exception as e:
            logger.error(f"LLM parsing failed for page {page_number}: {e}")
            raise

    def get_token_usage(self) -> dict[str, int]:
        """Get cumulative token usage statistics."""
        return self._token_usage.to_dict()

    def reset_token_usage(self) -> None:
        """Reset token usage counters."""
        self._token_usage = TokenUsage()

