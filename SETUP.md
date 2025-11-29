# Quick Setup Guide

This is a condensed setup guide for quick reference. For detailed instructions, see [README.md](README.md).

## 🚀 Quick Start (5 minutes)

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install -y poppler-utils libglib2.0-0 libgl1 python3-pip python3-venv
```

**macOS:**
```bash
brew install poppler
```

### 2. Clone and Setup

```bash
# Clone repository
git clone https://github.com/Pushuc0des/PurushotamGupta_Bits_Hyd.git
cd PurushotamGupta_Bits_Hyd

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -e .
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python3 -c "from rapidocr_onnxruntime import RapidOCR; print('✓ OK')"
pdftoppm -v  # Should show version
```

### 4. Run the Server

```bash
uvicorn bill_extraction_api.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test the API

Open in browser: http://localhost:8000/docs

Or use curl:
```bash
curl -X POST http://localhost:8000/extract-bill-data \
  -H 'Content-Type: application/json' \
  -d '{"document":"https://hackrx.blob.core.windows.net/assets/datathon-IIT/Sample%20Document%201.pdf?sv=2025-07-05&spr=https&st=2025-11-28T10%3A08%3A01Z&se=2025-11-30T10%3A08%3A00Z&sr=b&sp=r&sig=RSfZaGfX%2Fym%2BQT6BqwjAV6hlI1ehE%2FkTDN4sEAJQoPE%3D"}'
```

## ✅ Checklist

- [ ] Python 3.10+ installed
- [ ] System dependencies installed (poppler-utils)
- [ ] Virtual environment created and activated
- [ ] Package installed in editable mode (`pip install -e .`)
- [ ] All Python dependencies installed
- [ ] Server starts without errors
- [ ] API documentation accessible at /docs

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: bill_extraction_api` | Run `pip install -e .` |
| `pdftoppm: command not found` | Install poppler-utils |
| `rapidocr-onnxruntime` fails | Use Python 3.10+ and `pip install "rapidocr-onnxruntime>=1.3.19"` |
| Port 8000 in use | Use `--port 8001` |

For more details, see [README.md](README.md).

