from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.medicine import MedicineSearchResult, MedicineDetail, Batch
from app.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("", response_model=list[MedicineSearchResult])
@router.get("/", response_model=list[MedicineSearchResult])
def list_inventory(search: str = "", db: Session = Depends(get_db)):
    return inventory_service.search_medicines(db, search or "")

@router.get("/search", response_model=list[MedicineSearchResult])
def search_medicines(name: str, db: Session = Depends(get_db)):
    return inventory_service.search_medicines(db, name)

@router.get("/low-stock", response_model=list[MedicineSearchResult])
def get_low_stock(threshold: int = 10, db: Session = Depends(get_db)):
    return inventory_service.get_low_stock_medicines(db, threshold)

@router.get("/expiring", response_model=list[Batch])
def get_expiring(days: int = 30, db: Session = Depends(get_db)):
    return inventory_service.get_expiring_batches(db, days)

@router.get("/{medicine_id}", response_model=MedicineDetail)
def get_medicine_detail(medicine_id: int, db: Session = Depends(get_db)):
    return inventory_service.get_medicine_detail(db, medicine_id)
