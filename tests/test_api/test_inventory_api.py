from datetime import date
from app.models.medicine import Medicine, Batch

def test_search_medicines_api(client, db):
    med = Medicine(name="Dolo 650", unit_price=30.0)
    med.batches.append(Batch(batch_number="B1", quantity=100, expiry_date=date(2027, 1, 1)))
    db.add(med)
    db.commit()
    
    response = client.get("/inventory/search?name=dolo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Dolo 650"
    assert data[0]["total_stock"] == 100
