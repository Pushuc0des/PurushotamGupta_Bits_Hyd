# LLM Integration Setup Guide

This guide explains how to configure and use LLM-based parsing for medical bill extraction.

## Overview

The system now supports three parsing modes:
- **`regex`** (default): Fast, rule-based parsing using regex patterns
- **`llm`**: AI-powered parsing using Large Language Models
- **`hybrid`**: Try LLM first, fallback to regex on errors

## Supported LLM Providers

### 1. OpenAI

**Setup:**
```bash
# Install OpenAI package
pip install openai

# Set environment variable
export BILL_API_OPENAI_API_KEY="sk-your-api-key-here"
```

**Configuration:**
```bash
export BILL_API_PARSER_BACKEND="llm"
export BILL_API_LLM_PROVIDER="openai"
export BILL_API_LLM_MODEL="gpt-4o-mini"  # or "gpt-4o", "gpt-4-turbo", etc.
```

**Recommended Models:**
- `gpt-4o-mini` - Fast and cost-effective (default)
- `gpt-4o` - More accurate, higher cost
- `gpt-4-turbo` - Best accuracy, highest cost

### 2. Anthropic (Claude)

**Setup:**
```bash
# Install Anthropic package
pip install anthropic

# Set environment variable
export BILL_API_ANTHROPIC_API_KEY="sk-ant-your-api-key-here"
```

**Configuration:**
```bash
export BILL_API_PARSER_BACKEND="llm"
export BILL_API_LLM_PROVIDER="anthropic"
export BILL_API_LLM_MODEL="claude-3-5-sonnet-20241022"  # or "claude-3-opus-20240229"
```

**Recommended Models:**
- `claude-3-5-sonnet-20241022` - Balanced performance
- `claude-3-opus-20240229` - Highest accuracy
- `claude-3-haiku-20240307` - Fastest, most cost-effective

### 3. Local Models (Future)

Support for local models (Ollama, vLLM, etc.) is planned but not yet implemented.

## Configuration Options

All settings use the `BILL_API_` prefix and can be set via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `PARSER_BACKEND` | `regex` | Parser mode: `regex`, `llm`, or `hybrid` |
| `LLM_PROVIDER` | `openai` | Provider: `openai`, `anthropic`, or `local` |
| `LLM_MODEL` | `gpt-4o-mini` | Model identifier |
| `LLM_TEMPERATURE` | `0.0` | Temperature (0.0 = deterministic) |
| `LLM_MAX_TOKENS` | `2000` | Maximum tokens in response |
| `OPENAI_API_KEY` | - | OpenAI API key (required for OpenAI) |
| `ANTHROPIC_API_KEY` | - | Anthropic API key (required for Anthropic) |

## Example `.env` File

```bash
# Parser Configuration
BILL_API_PARSER_BACKEND=llm
BILL_API_LLM_PROVIDER=openai
BILL_API_LLM_MODEL=gpt-4o-mini
BILL_API_LLM_TEMPERATURE=0.0
BILL_API_LLM_MAX_TOKENS=2000

# API Keys (NEVER commit these!)
BILL_API_OPENAI_API_KEY=sk-your-key-here
# BILL_API_ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Usage Modes

### Mode 1: Pure LLM (`parser_backend=llm`)

Uses only LLM for parsing. Best for:
- High accuracy requirements
- Complex document layouts
- When you have API budget

**Pros:**
- Best accuracy
- Handles complex layouts
- Understands context

**Cons:**
- Slower (API latency)
- Costs money per request
- Requires internet connection

### Mode 2: Hybrid (`parser_backend=hybrid`)

Tries LLM first, falls back to regex on errors. Best for:
- Production systems needing reliability
- Cost optimization (only use LLM when needed)
- Graceful degradation

**Pros:**
- Reliable fallback
- Cost-efficient
- Best of both worlds

**Cons:**
- Slightly more complex logic
- May have inconsistent results between modes

### Mode 3: Regex (`parser_backend=regex`)

Original rule-based parsing. Best for:
- Fast processing
- Zero cost
- Offline operation
- Simple document structures

## Token Usage Tracking

The API now properly tracks and returns token usage in the response:

```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 1250,
    "input_tokens": 980,
    "output_tokens": 270
  },
  "data": { ... }
}
```

This helps you:
- Monitor API costs
- Optimize prompts
- Track usage patterns

## Cost Estimation

### OpenAI Pricing (as of 2024)
- `gpt-4o-mini`: ~$0.15/$0.60 per 1M tokens (input/output)
- `gpt-4o`: ~$2.50/$10.00 per 1M tokens

**Example:** A 5-page bill with ~1000 input tokens per page:
- Input: 5000 tokens × $0.15/1M = $0.00075
- Output: ~1500 tokens × $0.60/1M = $0.0009
- **Total: ~$0.00165 per bill**

### Anthropic Pricing (as of 2024)
- `claude-3-5-sonnet`: ~$3.00/$15.00 per 1M tokens
- `claude-3-opus`: ~$15.00/$75.00 per 1M tokens

## Troubleshooting

### Error: "API key is required"
- Make sure you've set the correct environment variable
- Check that the variable name matches your provider
- Verify the key is valid and has credits

### Error: "Package is required"
- Install the provider package: `pip install openai` or `pip install anthropic`
- Make sure it's in your virtual environment

### Error: "Failed to parse LLM JSON response"
- The LLM may have returned invalid JSON
- Check logs for the raw response
- Try a different model or adjust temperature

### Poor extraction quality
- Try a more powerful model (e.g., `gpt-4o` instead of `gpt-4o-mini`)
- Lower temperature (already 0.0 by default)
- Check OCR quality - poor OCR = poor LLM results

## Security Best Practices

1. **Never commit API keys** to version control
2. Use `.env` files and add them to `.gitignore`
3. Use environment variables in production (not `.env` files)
4. Rotate API keys regularly
5. Monitor token usage to detect anomalies

## Testing

To test LLM integration:

```bash
# Set your API key
export BILL_API_OPENAI_API_KEY="sk-test-key"
export BILL_API_PARSER_BACKEND="llm"

# Run the API
uvicorn bill_extraction_api.app.main:app --reload

# Test with curl
curl -X POST http://localhost:8000/extract-bill-data \
  -H 'Content-Type: application/json' \
  -d '{"document":"https://example.com/bill.pdf"}'
```

Check the `token_usage` field in the response to verify LLM is being used.


