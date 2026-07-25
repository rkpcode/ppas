import pytest
from datetime import date
from app.models.medicine import Medicine, Batch
from app.models.staff import Staff
from app.services.auth_service import get_password_hash
from app.services.sales_service import record_confirmed_sale, process_voice_sale_draft

def test_record_confirmed_sale(db):
    # Setup test staff
    staff = Staff(name="Test Pharmacist", username="pharmacist_test", hashed_password=get_password_hash("pass"), role="pharmacist")
    db.add(staff)
    
    # Setup test medicine & batch
    medicine = Medicine(name="Test Paracetamol 500mg", generic_name="Paracetamol", unit_price=10.0)
    db.add(medicine)
    db.flush()
    
    batch = Batch(medicine_id=medicine.id, batch_number="BATCH001", quantity=50, expiry_date=date(2030, 1, 1))
    db.add(batch)
    db.commit()
    
    # Record sale of 5 units
    sale = record_confirmed_sale(
        db=db,
        staff_id=staff.id,
        medicine_id=medicine.id,
        quantity=5,
        total_amount=50.0,
        customer_name="Test Customer"
    )
    
    assert sale.id is not None
    assert sale.status == "confirmed"
    assert sale.total_amount == 50.0
    
    # Verify stock deducted in batch
    updated_batch = db.query(Batch).filter(Batch.id == batch.id).first()
    assert updated_batch.quantity == 45

def test_record_sale_auto_fulfill_transition(db):
    """Verifies that during transition phase, selling more than current stock does NOT raise an error."""
    staff = Staff(name="Test Staff", username="staff_test", hashed_password=get_password_hash("pass"), role="staff")
    db.add(staff)
    
    medicine = Medicine(name="Test Transition Med", generic_name="TestGen", unit_price=20.0)
    db.add(medicine)
    db.flush()
    
    batch = Batch(medicine_id=medicine.id, batch_number="BATCH002", quantity=2, expiry_date=date(2030, 1, 1))
    db.add(batch)
    db.commit()
    
    # Requesting 10 units when only 2 exist -> Should auto-fulfill transition batch
    sale = record_confirmed_sale(
        db=db,
        staff_id=staff.id,
        medicine_id=medicine.id,
        quantity=10,
        total_amount=200.0,
        customer_name="Transition Customer"
    )
    
    assert sale.id is not None
    assert sale.status == "confirmed"
    assert sale.total_amount == 200.0
    assert len(sale.items) >= 1
