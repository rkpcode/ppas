from datetime import date
from app.models.medicine import Medicine, Batch

def test_medicine_batch_relationship(db):
    med = Medicine(name="Test Med", unit_price=10.50)
    batch = Batch(batch_number="B123", quantity=100, expiry_date=date(2027, 1, 1))
    med.batches.append(batch)
    db.add(med)
    db.commit()
    
    saved_med = db.query(Medicine).filter_by(name="Test Med").first()
    assert saved_med is not None
    assert len(saved_med.batches) == 1
    assert saved_med.batches[0].batch_number == "B123"
