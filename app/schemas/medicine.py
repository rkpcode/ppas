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
