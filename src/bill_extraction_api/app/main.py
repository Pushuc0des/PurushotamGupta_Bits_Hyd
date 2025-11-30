from __future__ import annotations
from loguru import logger
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from bill_extraction_api.app.schemas import ExtractionRequest, ExtractionResponse, TokenUsage
from bill_extraction_api.services.summarizer import ExtractionService
from bill_extraction_api.settings import AppSettings, get_settings

app = FastAPI(title="Bill Extraction API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_service(settings: AppSettings = Depends(get_settings)) -> ExtractionService:
    return ExtractionService(settings)


@app.post("/extract-bill-data", response_model=ExtractionResponse)
async def extract_bill_data(
    payload: ExtractionRequest, service: ExtractionService = Depends(get_service)
) -> ExtractionResponse:
    try:
        data = await service.extract(str(payload.document))
        token_usage_dict = service.get_token_usage()
        token_usage = TokenUsage.from_dict(token_usage_dict)
        return ExtractionResponse(
            is_success=True,
            data=data,
            token_usage=token_usage,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive path
        import traceback
        error_detail = str(exc)
        logger.error(f"Extraction failed: {error_detail}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {error_detail}") from exc


@app.post("/api/v1/hackrx/run", response_model=ExtractionResponse)
async def hackrx_webhook(
    payload: ExtractionRequest, service: ExtractionService = Depends(get_service)
) -> ExtractionResponse:
    """
    Webhook endpoint for HackRx platform.
    Accepts the same request format as /extract-bill-data and returns structured bill data.
    """
    try:
        logger.info(f"HackRx webhook called with document: {payload.document}")
        data = await service.extract(str(payload.document))
        token_usage_dict = service.get_token_usage()
        token_usage = TokenUsage.from_dict(token_usage_dict)
        return ExtractionResponse(
            is_success=True,
            data=data,
            token_usage=token_usage,
        )
    except ValueError as exc:
        logger.error(f"HackRx webhook validation error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive path
        import traceback
        error_detail = str(exc)
        logger.error(f"HackRx webhook failed: {error_detail}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {error_detail}") from exc
