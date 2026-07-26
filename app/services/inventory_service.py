from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta
from app.models.medicine import Medicine, Batch
from app.schemas.medicine import MedicineSearchResult
from app.exceptions.domain_exceptions import MedicineNotFoundError

def require_confirmation(action: str, confirm_token: str | None = None) -> None:
    """
    Placeholder for the system-wide safety boundary.
    In later phases, every write-action service function (commit_sale,
    log_dispensing_entry, send_purchase_order) MUST call this first.
    Do not delete or bypass this function in future phases.
    """
    if not confirm_token:
        raise PermissionError(f"{action} requires human confirmation token")

def search_medicines(db: Session, query: str) -> list[MedicineSearchResult]:
    medicines = db.query(Medicine).options(joinedload(Medicine.batches)).filter(Medicine.name.ilike(f"%{query}%")).all()
    results = []
    for med in medicines:
        total_stock = sum(b.quantity for b in med.batches)
        results.append(MedicineSearchResult(
            id=med.id,
            name=med.name,
            generic_name=med.generic_name,
            manufacturer=med.manufacturer,
            category=med.category,
            unit_price=med.unit_price,
            unit_type=getattr(med, "unit_type", "strip") or "strip",
            is_schedule_h=med.is_schedule_h,
            total_stock=total_stock
        ))
    return results

def get_medicine_detail(db: Session, medicine_id: int) -> Medicine:
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        raise MedicineNotFoundError(medicine_id)
    return med

def get_low_stock_medicines(db: Session, threshold: int = 10) -> list[MedicineSearchResult]:
    medicines = db.query(Medicine).options(joinedload(Medicine.batches)).all()
    results = []
    for med in medicines:
        total_stock = sum(b.quantity for b in med.batches)
        if total_stock < threshold:
            results.append(MedicineSearchResult(
                id=med.id,
                name=med.name,
                generic_name=med.generic_name,
                manufacturer=med.manufacturer,
                category=med.category,
                unit_price=med.unit_price,
                unit_type=getattr(med, "unit_type", "strip") or "strip",
                is_schedule_h=med.is_schedule_h,
                total_stock=total_stock
            ))
    return results

def get_expiring_batches(db: Session, days: int = 30) -> list[Batch]:
    cutoff_date = date.today() + timedelta(days=days)
    batches = db.query(Batch).filter(Batch.expiry_date <= cutoff_date).all()
    return batches
