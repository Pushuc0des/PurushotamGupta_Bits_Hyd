# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for better Docker layer caching)
COPY pyproject.toml requirements.txt ./

# Install Python dependencies (without the package itself)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy README and application code (needed for package installation)
COPY README.md ./
COPY src/ ./src/
COPY tests/ ./tests/

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Expose port (will be set by platform)
EXPOSE 8000

# Health check (using curl which is available in the base image or a simple Python check)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs').read()" || exit 1

# Run the application
CMD ["uvicorn", "bill_extraction_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

