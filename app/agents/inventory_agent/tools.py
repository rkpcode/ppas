from langchain_core.tools import tool
from app.core.database import SessionLocal
from app.services import inventory_service

@tool
def search_medicine(name: str) -> dict:
    """
    Search for a medicine by name or partial name. Use this when the user asks if a medicine is available, or asks about a medicine generally. Returns stock level and price.
    """
    db = SessionLocal()
    try:
        results = inventory_service.search_medicines(db, name)
        if not results:
            return {"error": "Medicine not found", "code": "NOT_FOUND"}
        return {"matches": [r.model_dump() for r in results]}
    except Exception as e:
        return {"error": str(e), "code": "ERROR"}
    finally:
        db.close()

@tool
def check_stock(name: str) -> dict:
    """
    Check exact stock quantity for a specific medicine by name. Returns medicine name and total stock across batches, or a clear "not found" result if no match exists.
    """
    db = SessionLocal()
    try:
        results = inventory_service.search_medicines(db, name)
        if not results:
            return {"error": "Medicine not found", "code": "NOT_FOUND"}
        # Usually checking stock refers to a specific one, we return the top match
        med = results[0]
        return {"name": med.name, "total_stock": med.total_stock}
    except Exception as e:
        return {"error": str(e), "code": "ERROR"}
    finally:
        db.close()

@tool
def check_expiry(name: str = None, days: int = 30) -> dict:
    """
    Check expiring batches. If `name` is provided, scope to that medicine. If not, return all batches expiring within `days`.
    """
    db = SessionLocal()
    try:
        batches = inventory_service.get_expiring_batches(db, days)
        if name:
            batches = [b for b in batches if name.lower() in b.medicine.name.lower()]
        
        if not batches:
            return {"message": f"No batches expiring within {days} days.", "code": "NOT_FOUND"}
            
        results = []
        for b in batches:
            results.append({
                "medicine_name": b.medicine.name,
                "batch_number": b.batch_number,
                "expiry_date": b.expiry_date.isoformat(),
                "quantity": b.quantity
            })
        return {"expiring_batches": results}
    except Exception as e:
        return {"error": str(e), "code": "ERROR"}
    finally:
        db.close()

@tool
def check_low_stock(threshold: int = 75) -> dict:
    """
    Return medicines below the given stock threshold.
    """
    db = SessionLocal()
    try:
        medicines = inventory_service.get_low_stock_medicines(db, threshold)
        if not medicines:
            return {"message": "No medicines below threshold", "code": "NOT_FOUND"}
        return {"low_stock_medicines": [m.model_dump() for m in medicines]}
    except Exception as e:
        return {"error": str(e), "code": "ERROR"}
    finally:
        db.close()
