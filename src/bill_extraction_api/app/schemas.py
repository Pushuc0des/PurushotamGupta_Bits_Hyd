from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, HttpUrl


class TokenUsage(BaseModel):
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    
    @classmethod
    def from_dict(cls, data: dict) -> "TokenUsage":
        """Create TokenUsage from dictionary."""
        return cls(
            total_tokens=data.get("total_tokens", 0),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
        )


class BillItem(BaseModel):
    item_name: str
    item_amount: float = Field(..., description="Net amount post discount")
    item_rate: float | None = None
    item_quantity: float | None = None


class PageLineItems(BaseModel):
    page_no: str
    page_type: str = "Bill Detail"
    bill_items: List[BillItem]


class ExtractionData(BaseModel):
    pagewise_line_items: List[PageLineItems]
    total_item_count: int


class ExtractionResponse(BaseModel):
    is_success: bool = True
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    data: ExtractionData


class ExtractionRequest(BaseModel):
    document: HttpUrl = Field(..., description="Publicly accessible document URL")
