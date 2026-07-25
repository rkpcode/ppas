from datetime import date, timedelta
from app.models.medicine import Medicine, Batch
from app.services import inventory_service

def test_search_medicines(db):
    med = Medicine(name="Crocin 500", unit_price=15.0)
    med.batches.append(Batch(batch_number="B1", quantity=50, expiry_date=date(2027, 1, 1)))
    db.add(med)
    db.commit()
    
    results = inventory_service.search_medicines(db, "crocin")
    assert len(results) == 1
    assert results[0].name == "Crocin 500"
    assert results[0].total_stock == 50

def test_get_low_stock(db):
    med1 = Medicine(name="Low Stock Med", unit_price=10.0)
    med1.batches.append(Batch(batch_number="B1", quantity=5, expiry_date=date(2027, 1, 1)))
    
    med2 = Medicine(name="High Stock Med", unit_price=10.0)
    med2.batches.append(Batch(batch_number="B2", quantity=20, expiry_date=date(2027, 1, 1)))
    
    db.add(med1)
    db.add(med2)
    db.commit()
    
    results = inventory_service.get_low_stock_medicines(db, threshold=10)
    assert len(results) == 1
    assert results[0].name == "Low Stock Med"
