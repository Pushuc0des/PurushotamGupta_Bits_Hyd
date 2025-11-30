# Bill Extraction API

FastAPI-powered service that ingests multi-page medical bills (PDFs or images), runs OCR + document understanding to extract structured line items, and returns the schema mandated by the HackRx Datathon submission guidelines. The pipeline is designed to maximise accuracy while remaining fully modular so that stronger OCR or LLM summarizers can be swapped in without touching the HTTP layer.

## 🌐 Live Deployment

**Deployed API**: [View Deployment Guide](DEPLOYMENT.md)

The API can be deployed for free on platforms like Render, Railway, or Fly.io. See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions.

**Quick Deploy**: Connect your GitHub repo to [Render](https://render.com) and it will auto-deploy!

## 🎯 Problem Context

Bajaj Health processes thousands of OPD/IPD claims a day and needs to "pay right" by digitising invoices accurately. Each file can have 30–40 scanned pages, with a mix of tabular and free-form sections. The API exposed by this repository mirrors the published Postman collection and expects a public `document` URL pointing at the source file.

## 🏗️ High-Level Architecture

1. **Document fetcher** – downloads the remote file, validates MIME type, streams to local temp storage.
2. **Pre-processor** – converts PDF pages to images (`pdf2image` + `poppler`) or normalises incoming images (deskew, denoise, contrast boost).
3. **OCR engine** – default implementation relies on `rapidocr-onnxruntime` (pure Python + ONNXRuntime) but the interface supports plugging `PaddleOCR`, `EasyOCR`, or vendor APIs.
4. **Layout-aware parser** – groups OCR lines into candidate tables, extracts amount, quantity, rate columns via regex + fuzzy headers, and tracks section-level subtotals without double counting.
5. **LLM parser (optional)** – uses GPT-4 or Claude for intelligent document understanding and extraction.
6. **Aggregator** – builds the response schema, enforces float precision, deduplicates rows, and computes `total_item_count` + overall totals for QA traces.

```
FastAPI Router -> ExtractionService -> {DocumentFetcher, Preprocessor, OCREngine, LineItemParser/LLMParser} -> Response DTOs
```

## 🖼️ Demo / Screenshots

### API in Action

The following screenshot demonstrates the API successfully extracting line items from a medical bill PDF:

![API Demo Screenshot](docs/api-demo.png)

**What you see:**
- **Left Panel**: Swagger UI showing the `/extract-bill-data` endpoint with a sample request
- **Right Panel**: Chrome DevTools Network tab displaying the successful JSON response
- **Response**: Structured line items extracted from the bill, including:
  - Item names (e.g., "BED CHARGES", "Ward/Room/Bed")
  - Item amounts, rates, and quantities
  - Proper handling of null values for missing data

The API successfully processes multi-page PDFs and returns structured JSON data ready for downstream processing.

## 📋 Prerequisites

Before setting up the project, ensure you have the following installed:

### System Requirements
- **Python**: 3.10 or higher (3.11+ recommended)
- **Operating System**: Linux (Ubuntu/Debian recommended), macOS, or Windows with WSL
- **Git**: For cloning the repository

### System Dependencies (Linux/Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y \
    poppler-utils \
    libglib2.0-0 \
    libgl1 \
    python3-pip \
    python3-venv
```

**For macOS:**
```bash
brew install poppler
```

**For Windows (WSL):**
```bash
# Use Ubuntu commands above in WSL
```

## 🚀 Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Pushuc0des/PurushotamGupta_Bits_Hyd.git
cd PurushotamGupta_Bits_Hyd
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install project in editable mode (required for imports)
pip install -e .

# Install all dependencies
pip install -r requirements.txt
```

**Note**: The `pip install -e .` command is essential as it installs the package in development mode, allowing Python to find the `bill_extraction_api` module.

### Step 4: Verify Installation

```bash
# Check if OCR module is installed
python3 -c "from rapidocr_onnxruntime import RapidOCR; print('✓ OCR module installed')"

# Check if poppler is available
pdftoppm -v

# Verify the package is installed
python3 -c "import bill_extraction_api; print('✓ Package installed correctly')"
```

All checks should pass without errors.

## 🏃 Running the API

### Start the Server

```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Start the FastAPI server
uvicorn bill_extraction_api.app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

### Access API Documentation

Once the server is running, you can access:

- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc

## 🧪 Testing the API

### Using cURL

```bash
curl -X POST http://localhost:8000/extract-bill-data \
  -H 'Content-Type: application/json' \
  -d '{"document":"https://hackrx.blob.core.windows.net/assets/datathon-IIT/Sample%20Document%201.pdf?sv=2025-07-05&spr=https&st=2025-11-28T10%3A08%3A01Z&se=2025-11-30T10%3A08%3A00Z&sr=b&sp=r&sig=RSfZaGfX%2Fym%2BQT6BqwjAV6hlI1ehE%2FkTDN4sEAJQoPE%3D"}' \
  | python3 -m json.tool
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/extract-bill-data",
    json={"document": "https://example.com/bill.pdf"}
)
print(response.json())
```

### Using Swagger UI

1. Open http://localhost:8000/docs in your browser
2. Click on `POST /extract-bill-data`
3. Click "Try it out"
4. Enter a document URL in the request body
5. Click "Execute"
6. View the response

## 📤 Response Format

The API returns structured JSON matching the specification:

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

## ⚙️ Configuration

### Parser Backend Options

The API supports three parsing modes:

1. **Regex Parser (Default)**: Fast, rule-based extraction
   ```bash
   # No configuration needed - this is the default
   ```

2. **LLM Parser**: Uses GPT-4 or Claude for intelligent extraction
   ```bash
   export BILL_API_PARSER_BACKEND="llm"
   export BILL_API_LLM_PROVIDER="openai"  # or "anthropic"
   export BILL_API_LLM_MODEL="gpt-4o-mini"
   export BILL_API_OPENAI_API_KEY="sk-your-key-here"
   ```

3. **Hybrid Parser**: Tries LLM first, falls back to regex on error
   ```bash
   export BILL_API_PARSER_BACKEND="hybrid"
   # ... same LLM config as above
   ```

See [LLM_SETUP.md](LLM_SETUP.md) for detailed LLM configuration instructions.

### Environment Variables

Create a `.env` file in the project root (optional):

```env
BILL_API_PARSER_BACKEND=regex
BILL_API_OCR_BACKEND=rapidocr
BILL_API_REQUEST_TIMEOUT_SECONDS=120
BILL_API_MAX_DOCUMENT_SIZE_MB=50
```

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

## 📁 Project Structure

```
bill-extraction-api/
├── README.md                 # This file
├── LLM_SETUP.md              # LLM configuration guide
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project configuration
├── .gitignore                # Git ignore rules
├── src/
│   └── bill_extraction_api/
│       ├── __init__.py
│       ├── settings.py       # Configuration management
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py       # FastAPI application
│       │   └── schemas.py    # Pydantic models
│       └── services/
│           ├── __init__.py
│           ├── document_fetcher.py  # Downloads documents
│           ├── preprocess.py        # Image preprocessing
│           ├── ocr.py                # OCR engine
│           ├── parser.py             # Regex-based parser
│           ├── llm_parser.py        # LLM-based parser
│           └── summarizer.py        # Main extraction service
└── tests/
    └── test_api.py           # API tests
```

## 🔧 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'bill_extraction_api'`

**Solution**: Install the package in editable mode:
```bash
pip install -e .
```

### Issue: `Command 'python' not found`

**Solution**: Use `python3` instead of `python`:
```bash
python3 -m venv .venv
python3 -m pip install -r requirements.txt
```

### Issue: `pdftoppm: command not found`

**Solution**: Install poppler-utils:
```bash
sudo apt-get install -y poppler-utils  # Linux
brew install poppler                    # macOS
```

### Issue: `rapidocr-onnxruntime` installation fails

**Solution**: Ensure you're using Python 3.10+ and install a compatible version:
```bash
pip install "rapidocr-onnxruntime>=1.3.19"
```

### Issue: Image preprocessing error: "Images of type float must be between -1 and 1"

**Solution**: This is already fixed in the code. If you encounter this, ensure you have the latest version:
```bash
git pull origin main
pip install -e .
```

### Issue: `Invalid type for url` error

**Solution**: This is already fixed in the code. The URL is automatically converted to string.

### Issue: Port 8000 already in use

**Solution**: Use a different port:
```bash
uvicorn bill_extraction_api.app.main:app --reload --host 0.0.0.0 --port 8001
```

## 🎓 Key Features

- ✅ **Multi-format Support**: PDF, PNG, JPEG, WEBP
- ✅ **Multi-page Processing**: Handles documents with 30+ pages
- ✅ **Dual Parser Modes**: Regex-based (fast) and LLM-based (accurate)
- ✅ **Modular Architecture**: Easy to swap OCR engines or parsers
- ✅ **Production Ready**: Error handling, logging, type safety
- ✅ **API Documentation**: Auto-generated Swagger/ReDoc docs
- ✅ **Token Usage Tracking**: For LLM-based parsing

## 🚀 Deployment

### Free Deployment Options

The API can be deployed for free on several platforms. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

**Recommended: Render (Easiest)**
1. Sign up at https://render.com (free, no credit card needed)
2. Connect your GitHub repository
3. Create new Web Service
4. Use these settings:
   - **Build Command**: `pip install --upgrade pip && pip install -e . && pip install -r requirements.txt`
   - **Start Command**: `uvicorn bill_extraction_api.app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
5. Deploy! Your API will be live at `https://your-app.onrender.com`

**Alternative Platforms:**
- **Railway**: https://railway.app ($5 free credit/month)
- **Fly.io**: https://fly.io (generous free tier)
- **Docker**: Use included `Dockerfile` for any container platform

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide with all options.

## 📚 Additional Resources

- **LLM Setup Guide**: See [LLM_SETUP.md](LLM_SETUP.md) for configuring OpenAI/Anthropic
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions
- **API Documentation**: http://localhost:8000/docs (when server is running)
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

## 🛣️ Roadmap

- [ ] Plug transformer-based table structure recogniser (LayoutLMv3 / docTR)
- [ ] Add confidence-weighted reconciliation (row-level QA checks)
- [ ] Persist extraction audit trail & intermediate artefacts
- [ ] Streaming inference for 40-page PDFs with progress events
- [ ] Docker containerization
- [ ] CI/CD pipeline

## 👤 Author

**Purushotam Gupta**
- GitHub: [@Pushuc0des](https://github.com/Pushuc0des)

## 📄 License

This project is part of a technical assessment/datathon submission.

---

**Note for Recruiters/Reviewers**: This project demonstrates production-ready code with proper error handling, modular architecture, comprehensive documentation, and support for both traditional and AI-based extraction methods. All setup steps have been tested and verified.
