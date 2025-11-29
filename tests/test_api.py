from fastapi.testclient import TestClient

from bill_extraction_api.app.main import app, get_service
from bill_extraction_api.app.schemas import BillItem, ExtractionData, PageLineItems


class StubExtractionService:
    async def extract(self, document_url: str) -> ExtractionData:  # pragma: no cover - simple stub
        return ExtractionData(
            pagewise_line_items=[
                PageLineItems(
                    page_no="1",
                    page_type="Bill Detail",
                    bill_items=[
                        BillItem(
                            item_name="Consultation",
                            item_amount=1950.0,
                            item_rate=1950.0,
                            item_quantity=1.0,
                        )
                    ],
                )
            ],
            total_item_count=1,
        )


def test_extract_bill_data(monkeypatch):
    async def _stub_service_dependency():
        return StubExtractionService()

    app.dependency_overrides[get_service] = _stub_service_dependency
    client = TestClient(app)

    response = client.post(
        "/extract-bill-data", json={"document": "https://example.com/doc.pdf"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_success"] is True
    assert payload["data"]["total_item_count"] == 1
    assert payload["data"]["pagewise_line_items"][0]["bill_items"][0]["item_name"] == "Consultation"

    app.dependency_overrides.clear()
