# backend/app/routers/ocr.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.schemas import OCRResponse, OCRItem
from app.services.ocr_service import process_receipt

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("", response_model=OCRResponse)
async def ocr_process(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Process a receipt image and extract items.

    Accepts: JPEG, PNG, HEIC
    Max size: 10MB
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/heic", "image/heif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    # Read file content
    content = await file.read()

    # Check file size (10MB max)
    max_size = 10 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB"
        )

    try:
        # Process the receipt
        items, raw_text = await process_receipt(content)

        return OCRResponse(
            items=items,
            raw_text=raw_text,
            success=True
        )

    except Exception as e:
        return OCRResponse(
            items=[],
            success=False,
            error_message=str(e)
        )
