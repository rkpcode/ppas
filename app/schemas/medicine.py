from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

class BatchBase(BaseModel):
    batch_number: str
    quantity: int
    expiry_date: date
    received_date: date

class Batch(BatchBase):
    id: int
    medicine_id: int
    model_config = ConfigDict(from_attributes=True)

class MedicineBase(BaseModel):
    name: str
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    unit_price: Decimal
    unit_type: str = "strip"
    is_schedule_h: bool = False

class Medicine(MedicineBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MedicineDetail(Medicine):
    batches: List[Batch]
    
class MedicineSearchResult(MedicineBase):
    id: int
    total_stock: int

# ── Stock Entry Schemas ──────────────────────────────────

class MedicineCreate(BaseModel):
    name: str
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    unit_price: Decimal
    unit_type: str = "strip"
    is_schedule_h: bool = False

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[Decimal] = None
    unit_type: Optional[str] = None
    is_schedule_h: Optional[bool] = None

class BatchCreate(BaseModel):
    batch_number: str
    quantity: int
    expiry_date: date
    received_date: Optional[date] = None

class BatchUpdate(BaseModel):
    quantity: Optional[int] = None
    expiry_date: Optional[date] = None

class BulkStockItem(BaseModel):
    medicine_name: str
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    batch_number: Optional[str] = "RECEIPT"
    quantity: int = 1
    unit_price: Optional[Decimal] = None
    unit_type: str = "strip"
    expiry_date: Optional[date] = None

class BulkStockRequest(BaseModel):
    items: list[BulkStockItem]
