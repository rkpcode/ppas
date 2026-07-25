from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Annotated
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.staff import Staff
from app.services.auth_service import get_current_user
from app.voice.stt import transcribe_audio
from app.services.sales_service import process_voice_sale_draft, record_confirmed_sale
from app.models.sale import Sale

router = APIRouter(prefix="/sales", tags=["Sales"])

class ParseTextRequest(BaseModel):
    text: str = Field(..., description="Spoken sales text (e.g. 'Dolo 650 2 strip 60 rupees')")

class ConfirmSaleRequest(BaseModel):
    medicine_id: int
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
    Parses voice recording OR text into a structured sales draft for UI review.
    """
    input_text = ""
    
    if file:
        audio_bytes = await file.read()
        try:
            input_text = await transcribe_audio(audio_bytes, language_hint="hi-IN")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Audio transcription failed: {str(e)}")
    elif text:
        input_text = text.strip()
    else:
        raise HTTPException(status_code=400, detail="Either audio file or text must be provided.")
        
    if not input_text:
        raise HTTPException(status_code=400, detail="Could not extract text from input.")
        
    draft = process_voice_sale_draft(input_text, db)
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
