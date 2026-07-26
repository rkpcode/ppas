from typing import Annotated, Any, Dict, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.staff import Staff
from app.services.auth_service import get_current_user
from app.schemas.medicine import (
    MedicineCreate, MedicineUpdate, BatchCreate, BatchUpdate, BulkStockRequest, Medicine
)
from app.schemas.medicine import Batch as BatchSchema
from app.services import stock_service

router = APIRouter(prefix="/stock", tags=["Stock Entry"])

@router.post("/parse-receipt")
async def parse_receipt(
    current_user: Annotated[Staff, Depends(get_current_user)],
    file: UploadFile = File(...)
):
    """Parses a receipt image using Gemini Vision to extract medicines."""
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image provided.")
    
    items = stock_service.parse_receipt_image(image_bytes, file.content_type)
    return {"items": items}

@router.post("/parse-voice")
async def parse_stock_voice(
    current_user: Annotated[Staff, Depends(get_current_user)],
    file: UploadFile = File(None),
    text: str = Form(None)
):
    """Parses voice audio or text to extract stock entry details."""
    if file:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file provided.")
        item = stock_service.parse_stock_voice(audio_bytes=audio_bytes)
    elif text:
        input_text = text.strip()
        if not input_text:
            raise HTTPException(status_code=400, detail="Empty text provided.")
        item = stock_service.parse_stock_voice(text=input_text)
    else:
        raise HTTPException(status_code=400, detail="Either audio file or text must be provided.")
        
    return item

@router.post("/medicines", response_model=Medicine)
def create_medicine(
    data: MedicineCreate,
    current_user: Annotated[Staff, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Manually register a new medicine."""
    try:
        return stock_service.create_medicine(db, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/medicines/{medicine_id}", response_model=Medicine)
def update_medicine(
    medicine_id: int,
    data: MedicineUpdate,
    current_user: Annotated[Staff, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Update details of an existing medicine."""
    try:
        return stock_service.update_medicine(db, medicine_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/medicines/{medicine_id}/batches", response_model=BatchSchema)
def add_batch(
    medicine_id: int,
    data: BatchCreate,
    current_user: Annotated[Staff, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Add a new stock batch to an existing medicine."""
    try:
        return stock_service.add_batch(db, medicine_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/batches/{batch_id}", response_model=BatchSchema)
def update_batch(
    batch_id: int,
    data: BatchUpdate,
    current_user: Annotated[Staff, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Update an existing batch."""
    try:
        return stock_service.update_batch(db, batch_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/confirm-bulk")
def confirm_bulk_stock(
    data: BulkStockRequest,
    current_user: Annotated[Staff, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Process bulk stock entry from receipt or voice."""
    try:
        return stock_service.bulk_stock_entry(db, data.items)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bulk stock entry failed: {str(e)}")
