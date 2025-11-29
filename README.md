# Bill Extraction API

FastAPI-powered service that ingests multi-page medical bills (PDFs or images), runs OCR + document understanding to extract structured line items, and returns the schema mandated by the HackRx Datathon submission guidelines. The pipeline is designed to maximise accuracy while remaining fully modular so that stronger OCR or LLM summarizers can be swapped in without touching the HTTP layer.

## Problem Context
Bajaj Health processes thousands of OPD/IPD claims a day and needs to “pay right” by digitising invoices accurately. Each file can have 30–40 scanned pages, with a mix of tabular and free-form sections. The API exposed by this repository mirrors the published Postman collection and expects a public `document` URL pointing at the source file (e.g. [`Sample Document 1.pdf`](https://hackrx.blob.core.windows.net/assets/datathon-IIT/Sample%20Document%201.pdf?sv=2025-07-05&spr=https&st=2025-11-28T10%3A08%3A01Z&se=2025-11-30T10%3A08%3A00Z&sr=b&sp=r&sig=RSfZaGfX%2Fym%2BQT6BqwjAV6hlI1ehE%2FkTDN4sEAJQoPE%3D)). Training samples (~15 docs) are available via the organisers’ ZIP bundle for experimentation.

## High-Level Architecture
1. **Document fetcher** – downloads the remote file, validates MIME type, streams to local temp storage.
2. **Pre-processor** – converts PDF pages to images (`pdf2image` + `poppler`) or normalises incoming images (deskew, denoise, contrast boost).
3. **OCR engine** – default implementation relies on `rapidocr-onnxruntime` (pure Python + ONNXRuntime) but the interface supports plugging `PaddleOCR`, `EasyOCR`, or vendor APIs.
4. **Layout-aware parser** – groups OCR lines into candidate tables, extracts amount, quantity, rate columns via regex + fuzzy headers, and tracks section-level subtotals without double counting.
5. **Aggregator** – builds the response schema, enforces float precision, deduplicates rows, and computes `total_item_count` + overall totals for QA traces.

```
FastAPI Router -> ExtractionService -> {DocumentFetcher, Preprocessor, OCREngine, LineItemParser} -> Response DTOs
```

## Getting Started
```bash
# optional: use uv for blazing-fast deps
curl -LsSf https://astral.sh/uv/install.sh | sh

cd bill-extraction-api
uv python install 3.11  # or use pyenv/conda
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

If you prefer plain `pip`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Native Dependencies
- `poppler-utils` for `pdf2image`
- `libgl1` / `libglib2.0-0` for OpenCV / RapidOCR
- Optional: `tesseract-ocr` if you switch to the Tesseract backend

On Ubuntu:
```bash
sudo apt-get update && sudo apt-get install -y poppler-utils libglib2.0-0 libgl1
```

## Running the API
```bash
uvicorn bill_extraction_api.app.main:app --reload --host 0.0.0.0 --port 8000
```
Then call the endpoint:
```bash
curl -X POST http://localhost:8000/extract-bill-data \
  -H 'Content-Type: application/json' \
  -d '{"document":"https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?..."}'
```

## Response Contract
Matches the organiser spec:
```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 0,
    "input_tokens": 0,
    "output_tokens": 0
  },
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [
          {
            "item_name": "Consultation Charge | DR PREETHI MARY JOSEPH--",
            "item_amount": 300.0,
            "item_rate": 300.0,
            "item_quantity": 1.0
          }
        ]
      }
    ],
    "total_item_count": 1
  }
}
```
`token_usage` acts as a telemetry field if you integrate any LLM steps; the default implementation simply reports zeros.

## Project Layout
```
├── README.md
├── requirements.txt
├── pyproject.toml
├── src/
│   └── bill_extraction_api/
│       ├── app/
│       │   ├── main.py
│       │   └── schemas.py
│       ├── services/
│       │   ├── document_fetcher.py
│       │   ├── preprocess.py
│       │   ├── ocr.py
│       │   ├── parser.py
│       │   └── summarizer.py
│       ├── settings.py
│       └── __init__.py
└── tests/
    └── test_api.py
```

## Roadmap
- [ ] Plug transformer-based table structure recogniser (LayoutLMv3 / docTR)
- [ ] Add confidence-weighted reconciliation (row-level QA checks)
- [ ] Persist extraction audit trail & intermediate artefacts
- [ ] Streaming inference for 40-page PDFs with progress events

## License
MIT (add your preferred license here).
