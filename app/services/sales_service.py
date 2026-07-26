import json
import logging
from datetime import date, datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from langchain_openai import ChatOpenAI
from app.config import settings
from app.models.medicine import Medicine, Batch
from app.models.sale import Sale, SaleItem
from app.models.customer import Customer

logger = logging.getLogger(__name__)

import google.generativeai as genai

def parse_sales_gemini(audio_bytes: Optional[bytes] = None, text: Optional[str] = None) -> Dict[str, Any]:
    """
    Uses Google Gemini 1.5 Flash to extract structured sales details from either audio or text.
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """You are a pharmacy AI assistant. Extract sale details from the following input (audio or text in Hindi/English/Hinglish).

Extract the following JSON fields:
- "medicine_name": string (name of the medicine spoken, e.g. "Dolo 650", "Crocin", "Azithral")
- "quantity": integer (number of units/strips/tablets, default 1 if not specified)
- "unit_type": string ("strip", "tablet", "bottle", "box", etc.)
- "claimed_price": float or null (total price if mentioned by user, e.g. 60.0)
- "customer_name": string or null (customer name if mentioned, otherwise null)

Return ONLY a valid JSON object without any extra text or markdown syntax.

Example output:
{"medicine_name": "Dolo 650", "quantity": 2, "unit_type": "strip", "claimed_price": 60.0, "customer_name": null}
"""
    
    if audio_bytes:
        content_parts = {"mime_type": "audio/webm", "data": audio_bytes}
    elif text:
        content_parts = f"Spoken text: \"{text}\""
    else:
        raise ValueError("Must provide either audio or text")

    try:
        response = model.generate_content([prompt, content_parts])
        content = response.text.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        return {
            "medicine_name": text if text else "Unknown Audio",
            "quantity": 1,
            "unit_type": "unit",
            "claimed_price": None,
            "customer_name": None
        }

def process_voice_sale_draft(db: Session, audio_bytes: Optional[bytes] = None, text: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses voice audio or text and matches against DB medicines to return a draft sale item.
    Auto-suggests entry if medicine isn't registered yet.
    """
    extracted = parse_sales_gemini(audio_bytes=audio_bytes, text=text)
    med_name = extracted.get("medicine_name", text if text else "Unknown")
    quantity = int(extracted.get("quantity", 1))
    
    # DB Lookup (case-insensitive fuzzy match)
    medicine = db.query(Medicine).filter(
        Medicine.name.ilike(f"%{med_name}%")
    ).first()
    
    if not medicine:
        medicine = db.query(Medicine).filter(
            Medicine.generic_name.ilike(f"%{med_name}%")
        ).first()
        
    if medicine:
        today = date.today()
        batches = db.query(Batch).filter(
            Batch.medicine_id == medicine.id,
            Batch.quantity > 0,
            Batch.expiry_date >= today
        ).all()
        
        total_stock = sum(b.quantity for b in batches)
        unit_price = float(medicine.unit_price)
        calculated_price = extracted.get("claimed_price") or (unit_price * quantity)
        
        return {
            "matched": True,
            "raw_text": text,
            "medicine_id": medicine.id,
            "medicine_name": medicine.name,
            "generic_name": medicine.generic_name,
            "quantity": quantity,
            "unit_type": extracted.get("unit_type", "strip"),
            "unit_price": unit_price,
            "total_price": float(calculated_price),
            "available_stock": total_stock,
            "is_schedule_h": medicine.is_schedule_h,
            "customer_name": extracted.get("customer_name")
        }
    else:
        # Medicine not in DB yet -> Auto-draft new medicine sale
        claimed_price = extracted.get("claimed_price") or 0.0
        unit_price = (claimed_price / quantity) if quantity > 0 else 0.0
        
        return {
            "matched": False,
            "auto_register": True,
            "raw_text": text,
            "medicine_id": None,
            "medicine_name": med_name,
            "generic_name": med_name,
            "quantity": quantity,
            "unit_type": extracted.get("unit_type", "strip"),
            "unit_price": unit_price,
            "total_price": float(claimed_price),
            "available_stock": 0,
            "is_schedule_h": False,
            "customer_name": extracted.get("customer_name"),
            "message": f"Medicine '{med_name}' is new. It will be registered automatically upon sale approval."
        }

def record_confirmed_sale(
    db: Session,
    staff_id: int,
    medicine_id: Optional[int] = None,
    medicine_name: Optional[str] = None,
    quantity: int = 1,
    total_amount: float = 0.0,
    customer_name: Optional[str] = None
) -> Sale:
    """
    Confirms a sale, saves Sale & SaleItem records to DB.
    Handles transition phase (auto-creates Medicine & temporary batch if stock not entered yet).
    """
    medicine = None
    if medicine_id:
        medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
        
    if not medicine and medicine_name:
        medicine = db.query(Medicine).filter(Medicine.name.ilike(medicine_name)).first()
        if not medicine:
            # Auto-create Medicine if not in DB yet
            unit_price = (total_amount / quantity) if quantity > 0 else 0.0
            medicine = Medicine(
                name=medicine_name,
                generic_name=medicine_name,
                unit_price=unit_price
            )
            db.add(medicine)
            db.flush()

    if not medicine:
        raise ValueError("Medicine not specified or found.")
        
    today = date.today()
    batches = db.query(Batch).filter(
        Batch.medicine_id == medicine.id,
        Batch.quantity > 0,
        Batch.expiry_date >= today
    ).order_by(Batch.expiry_date.asc()).all()
    
    total_stock = sum(b.quantity for b in batches)
    
    # Transition Phase Handling: If stock not entered yet, auto-create batch for exact sale quantity
    if total_stock < quantity:
        needed_qty = quantity - total_stock
        temp_batch = Batch(
            medicine_id=medicine.id,
            batch_number=f"TRANSITION_{int(datetime.utcnow().timestamp())}",
            quantity=needed_qty,
            expiry_date=date(2030, 12, 31)
        )
        db.add(temp_batch)
        db.flush()
        batches.append(temp_batch)
        
    # Handle Customer record if name provided
    customer_id = None
    if customer_name:
        customer = db.query(Customer).filter(Customer.name.ilike(customer_name)).first()
        if not customer:
            customer = Customer(name=customer_name)
            db.add(customer)
            db.flush()
        customer_id = customer.id

    # Create Permanent Sale Record in DB
    sale = Sale(
        staff_id=staff_id,
        customer_id=customer_id,
        total_amount=total_amount,
        status="confirmed"
    )
    db.add(sale)
    db.flush()
    
    # Deduct stock across batches (FIFO) & create SaleItem records
    remaining_qty = quantity
    for batch in batches:
        if remaining_qty <= 0:
            break
        
        deduct = min(batch.quantity, remaining_qty)
        batch.quantity -= deduct
        remaining_qty -= deduct
        
        sale_item = SaleItem(
            sale_id=sale.id,
            medicine_id=medicine.id,
            batch_id=batch.id,
            quantity=deduct,
            price_at_sale=medicine.unit_price
        )
        db.add(sale_item)
        
    db.commit()
    db.refresh(sale)
    return sale
