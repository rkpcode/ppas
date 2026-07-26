import json
import logging
from datetime import date
from decimal import Decimal
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
import google.generativeai as genai

from app.config import settings
from app.models.medicine import Medicine, Batch
from app.schemas.medicine import (
    MedicineCreate, MedicineUpdate, BatchCreate, BatchUpdate, BulkStockItem
)

logger = logging.getLogger(__name__)

# ── Gemini AI Helpers ────────────────────────────────────

def _get_gemini_model():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-1.5-flash')


RECEIPT_PROMPT = """You are a pharmacy inventory AI assistant. Analyze this purchase receipt/invoice image from an Indian pharmacy distributor.

Extract ALL medicines listed in the receipt. For each medicine, extract:
- "medicine_name": string (exact name as printed, e.g. "Dolo 650", "Azithral 500")
- "generic_name": string or null (generic/salt name if visible)
- "manufacturer": string or null (company name if visible)
- "batch_number": string or null (batch/lot number if visible)
- "quantity": integer (number of strips/units received)
- "unit_type": string ("tablet", "strip", "bottle", "piece") - default "strip" for tablet packs, "bottle" for liquids, "piece" for ointments
- "unit_price": float or null (price per unit in rupees)
- "expiry_date": string or null (in YYYY-MM-DD format if visible, e.g. "2026-03-01")

Return ONLY a valid JSON array of objects. No markdown, no extra text.

Example output:
[{"medicine_name": "Dolo 650", "generic_name": "Paracetamol", "manufacturer": "Micro Labs", "batch_number": "DL2401", "quantity": 50, "unit_type": "strip", "unit_price": 25.5, "expiry_date": "2026-06-01"}]

If you cannot read the receipt clearly, return an empty array: []
"""

STOCK_VOICE_PROMPT = """You are a pharmacy inventory AI assistant. Extract stock entry details from the following input (audio or text in Hindi/English/Hinglish).

The user is adding new stock to their retail pharmacy. Extract:
- "medicine_name": string (name of medicine)
- "generic_name": string or null
- "batch_number": string or null
- "quantity": integer (number of units, default 1)
- "unit_type": string ("tablet", "strip", "bottle", "piece") - if user says "tablet" or "tab", use "tablet"; if "bottle", use "bottle"; if "piece", "pcs", "pics", "piece", or "box", use "piece"; else default "strip"
- "unit_price": float or null (price per unit in rupees)
- "expiry_date": string or null (in YYYY-MM-DD format if mentioned)

Return ONLY a valid JSON object without any extra text or markdown syntax.

Example output:
{"medicine_name": "Cerelac", "generic_name": null, "batch_number": "DL2401", "quantity": 6, "unit_type": "piece", "unit_price": 250.5, "expiry_date": "2026-06-01"}
"""


def _clean_json_response(content: str) -> str:
    """Strip markdown fences from Gemini response."""
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def parse_receipt_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> List[Dict[str, Any]]:
    """Send receipt image to Gemini Vision and extract medicine list."""
    model = _get_gemini_model()
    image_part = {"mime_type": mime_type, "data": image_bytes}

    try:
        response = model.generate_content([RECEIPT_PROMPT, image_part])
        content = _clean_json_response(response.text)
        items = json.loads(content)
        if isinstance(items, list):
            return items
        return [items]
    except Exception as e:
        logger.error(f"Receipt parse failed: {e}")
        return []


def _clean_mime_type(mime_type: Optional[str]) -> str:
    if not mime_type:
        return "audio/webm"
    clean = mime_type.split(";")[0].strip().lower()
    if clean in ["audio/webm", "audio/mp4", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/aac", "audio/m4a", "audio/flac"]:
        return clean
    if "webm" in clean:
        return "audio/webm"
    if "mp4" in clean or "m4a" in clean:
        return "audio/mp4"
    if "ogg" in clean:
        return "audio/ogg"
    if "wav" in clean:
        return "audio/wav"
    return "audio/webm"


def parse_stock_voice(audio_bytes: Optional[bytes] = None, text: Optional[str] = None, mime_type: str = "audio/webm") -> Dict[str, Any]:
    """Send voice/text to Gemini and extract stock entry details using 2-step transcription + extraction."""
    model = _get_gemini_model()
    spoken_text = text.strip() if text else None

    if audio_bytes:
        clean_mime = _clean_mime_type(mime_type)
        content_parts = {"mime_type": clean_mime, "data": audio_bytes}
        
        # Step 1: Transcribe Spoken Audio
        stt_prompt = (
            "You are an expert speech recognition model for Indian Pharmacies. "
            "Transcribe the spoken audio accurately in Hindi, English, or Hinglish. "
            "Focus on medicine names, quantities, numbers, prices, and expiry. "
            "Return ONLY the transcribed text. Do not add formatting or markdown. "
            "If the audio is completely silent or contains no speech, return empty string."
        )
        import tempfile
        import os
        ext = ".webm" if "webm" in clean_mime else ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name
            
        try:
            uploaded_file = genai.upload_file(temp_path, mime_type="video/webm" if "webm" in ext else "video/mp4")
            stt_response = model.generate_content([stt_prompt, uploaded_file])
            if stt_response and stt_response.text:
                spoken_text = stt_response.text.strip()
                logger.info(f"STT transcribed: '{spoken_text}'")
            try:
                uploaded_file.delete()
            except:
                pass
        except Exception as e:
            logger.error(f"Gemini STT failed: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if not spoken_text or spoken_text.lower() in ["unknown", "empty", ""]:
        return {
            "medicine_name": "",
            "quantity": 1,
            "unit_price": None,
            "batch_number": None,
            "expiry_date": None,
            "transcribed_text": None,
            "error_message": "Audio samajh nahi aaya ya silent tha. Please saaf aawaz mein dobara bolein."
        }

    # Step 2: Parse structured fields from the transcribed text
    extraction_prompt = f"""{STOCK_VOICE_PROMPT}

Spoken Input: "{spoken_text}"
"""
    try:
        response = model.generate_content(extraction_prompt)
        content = _clean_json_response(response.text)
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            parsed["transcribed_text"] = spoken_text
            if not parsed.get("medicine_name") or parsed.get("medicine_name") == "Unknown":
                parsed["medicine_name"] = spoken_text
            return parsed
    except Exception as e:
        logger.error(f"JSON extraction failed: {e}")

    return {
        "medicine_name": spoken_text,
        "quantity": 1,
        "unit_price": None,
        "batch_number": None,
        "expiry_date": None,
        "transcribed_text": spoken_text
    }


# ── CRUD Operations ──────────────────────────────────────

def create_medicine(db: Session, data: MedicineCreate) -> Medicine:
    """Register a new medicine in the database."""
    med = Medicine(
        name=data.name,
        generic_name=data.generic_name,
        manufacturer=data.manufacturer,
        category=data.category,
        unit_price=data.unit_price,
        unit_type=getattr(data, "unit_type", "strip") or "strip",
        is_schedule_h=data.is_schedule_h,
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


def update_medicine(db: Session, medicine_id: int, data: MedicineUpdate) -> Medicine:
    """Update an existing medicine's details."""
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise ValueError(f"Medicine with id {medicine_id} not found")

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        if value is not None:
            setattr(med, field, value)

    db.commit()
    db.refresh(med)
    return med


def add_batch(db: Session, medicine_id: int, data: BatchCreate) -> Batch:
    """Add a new batch/stock entry for a medicine."""
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise ValueError(f"Medicine with id {medicine_id} not found")

    batch = Batch(
        medicine_id=medicine_id,
        batch_number=data.batch_number,
        quantity=data.quantity,
        expiry_date=data.expiry_date,
        received_date=data.received_date or date.today(),
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def update_batch(db: Session, batch_id: int, data: BatchUpdate) -> Batch:
    """Update an existing batch's quantity or expiry."""
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise ValueError(f"Batch with id {batch_id} not found")

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        if value is not None:
            setattr(batch, field, value)

    db.commit()
    db.refresh(batch)
    return batch


def bulk_stock_entry(db: Session, items: List[BulkStockItem]) -> Dict[str, Any]:
    """Process bulk stock entry from receipt or voice — create medicines if needed, add batches."""
    results = []

    for item in items:
        # Try to find existing medicine
        medicine = db.query(Medicine).filter(
            Medicine.name.ilike(f"%{item.medicine_name}%")
        ).first()

        if not medicine:
            # Auto-create new medicine
            medicine = Medicine(
                name=item.medicine_name,
                generic_name=item.generic_name,
                manufacturer=item.manufacturer,
                unit_price=item.unit_price or Decimal("0.00"),
                unit_type=getattr(item, "unit_type", "strip") or "strip",
            )
            db.add(medicine)
            db.flush()  # Get the ID without full commit

        # Add batch
        batch = Batch(
            medicine_id=medicine.id,
            batch_number=item.batch_number or "RECEIPT",
            quantity=item.quantity,
            expiry_date=item.expiry_date or date(2099, 12, 31),  # Default far future if unknown
            received_date=date.today(),
        )
        db.add(batch)

        results.append({
            "medicine_name": medicine.name,
            "medicine_id": medicine.id,
            "quantity_added": item.quantity,
            "batch_number": batch.batch_number,
            "is_new_medicine": medicine.id is None,
        })

    db.commit()

    return {
        "total_items": len(results),
        "items": results,
        "message": f"{len(results)} medicines ka stock successfully add ho gaya!"
    }

def delete_medicine(db: Session, medicine_id: int):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise ValueError("Medicine not found")
    
    # Check if there are sales records linked to this medicine
    from app.models.sale import SaleItem
    if db.query(SaleItem).filter(SaleItem.medicine_id == medicine_id).first():
        raise ValueError("Cannot delete this medicine because it has existing sales records.")
        
    db.delete(medicine)
    db.commit()
    return {"message": "Medicine deleted successfully"}
