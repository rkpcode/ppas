from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Annotated
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.staff import Staff
from app.services.auth_service import get_current_user

from app.services.sales_service import process_voice_sale_draft, record_confirmed_sale
from app.models.sale import Sale

router = APIRouter(prefix="/sales", tags=["Sales"])

class ParseTextRequest(BaseModel):
    text: str = Field(..., description="Spoken sales text (e.g. 'Dolo 650 2 strip 60 rupees')")

class ConfirmSaleRequest(BaseModel):
    medicine_id: Optional[int] = None
    medicine_name: Optional[str] = None
    quantity: int = Field(..., gt=0)
    total_amount: float = Field(..., ge=0)
    customer_name: Optional[str] = None

class SaleItemResponse(BaseModel):
    id: int
    medicine_id: int
    quantity: int
    price_at_sale: float

class SaleResponse(BaseModel):
    id: int
    staff_id: int
    total_amount: float
    status: str
    customer_id: Optional[int] = None
    items: List[SaleItemResponse]

@router.post("/parse-voice")
async def parse_voice_sale(
    current_user: Annotated[Staff, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    """
    Parses voice recording OR text into a structured sales draft for UI review using Gemini Multimodal.
    """
    if file:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file provided.")
        draft = process_voice_sale_draft(db, audio_bytes=audio_bytes)
    elif text:
        input_text = text.strip()
        if not input_text:
            raise HTTPException(status_code=400, detail="Empty text provided.")
        draft = process_voice_sale_draft(db, text=input_text)
    else:
        raise HTTPException(status_code=400, detail="Either audio file or text must be provided.")
        
    return draft

@router.post("/confirm", response_model=SaleResponse)
def confirm_sale(
    request: ConfirmSaleRequest,
    current_user: Annotated[Staff, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Confirms a sale after user review, deducts stock from batches (FIFO), and records sale.
    """
    try:
        sale = record_confirmed_sale(
            db=db,
            staff_id=current_user.id,
            medicine_id=request.medicine_id,
            medicine_name=request.medicine_name,
            quantity=request.quantity,
            total_amount=request.total_amount,
            customer_name=request.customer_name
        )
        return SaleResponse(
            id=sale.id,
            staff_id=sale.staff_id,
            total_amount=float(sale.total_amount),
            status=sale.status,
            customer_id=sale.customer_id,
            items=[
                SaleItemResponse(
                    id=item.id,
                    medicine_id=item.medicine_id,
                    quantity=item.quantity,
                    price_at_sale=float(item.price_at_sale)
                ) for item in sale.items
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history", response_model=List[SaleResponse])
def get_sales_history(
    current_user: Annotated[Staff, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20
):
    """
    Fetch recent sales history.
    """
    sales = db.query(Sale).order_by(Sale.created_at.desc()).limit(limit).all()
    return [
        SaleResponse(
            id=sale.id,
            staff_id=sale.staff_id,
            total_amount=float(sale.total_amount),
            status=sale.status,
            customer_id=sale.customer_id,
            items=[
                SaleItemResponse(
                    id=item.id,
                    medicine_id=item.medicine_id,
                    quantity=item.quantity,
                    price_at_sale=float(item.price_at_sale)
                ) for item in sale.items
            ]
        ) for sale in sales
    ]
