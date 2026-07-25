import pytest
from unittest.mock import patch, MagicMock
from app.agents.inventory_agent.tools import search_medicine, check_stock, check_expiry, check_low_stock
from app.schemas.medicine import MedicineSearchResult

@patch("app.agents.inventory_agent.tools.SessionLocal")
@patch("app.agents.inventory_agent.tools.inventory_service.search_medicines")
def test_search_medicine(mock_search, mock_session):
    mock_search.return_value = [
        MedicineSearchResult(id=1, name="Test Med", unit_price=10.0, total_stock=50, is_schedule_h=False, generic_name=None, manufacturer=None, category=None)
    ]
    
    result = search_medicine.invoke({"name": "Test Med"})
    assert "matches" in result
    assert result["matches"][0]["name"] == "Test Med"

@patch("app.agents.inventory_agent.tools.SessionLocal")
@patch("app.agents.inventory_agent.tools.inventory_service.search_medicines")
def test_search_medicine_not_found(mock_search, mock_session):
    mock_search.return_value = []
    result = search_medicine.invoke({"name": "Nonexistent"})
    assert result["code"] == "NOT_FOUND"

@patch("app.agents.inventory_agent.tools.SessionLocal")
@patch("app.agents.inventory_agent.tools.inventory_service.search_medicines")
def test_check_stock(mock_search, mock_session):
    mock_search.return_value = [
        MedicineSearchResult(id=1, name="Stock Med", unit_price=10.0, total_stock=50, is_schedule_h=False, generic_name=None, manufacturer=None, category=None)
    ]
    result = check_stock.invoke({"name": "Stock Med"})
    assert result["name"] == "Stock Med"
    assert result["total_stock"] == 50

@patch("app.agents.inventory_agent.tools.SessionLocal")
@patch("app.agents.inventory_agent.tools.inventory_service.get_expiring_batches")
def test_check_expiry(mock_expiring, mock_session):
    mock_batch = MagicMock()
    mock_batch.medicine.name = "Expiry Med"
    mock_batch.batch_number = "B1"
    mock_batch.expiry_date.isoformat.return_value = "2027-01-01"
    mock_batch.quantity = 10
    
    mock_expiring.return_value = [mock_batch]
    
    result = check_expiry.invoke({"days": 5})
    assert "expiring_batches" in result
    assert result["expiring_batches"][0]["medicine_name"] == "Expiry Med"

@patch("app.agents.inventory_agent.tools.SessionLocal")
@patch("app.agents.inventory_agent.tools.inventory_service.get_low_stock_medicines")
def test_check_low_stock(mock_low_stock, mock_session):
    mock_low_stock.return_value = [
        MedicineSearchResult(id=1, name="Low Med", unit_price=10.0, total_stock=5, is_schedule_h=False, generic_name=None, manufacturer=None, category=None)
    ]
    
    result = check_low_stock.invoke({"threshold": 10})
    assert "low_stock_medicines" in result
    assert result["low_stock_medicines"][0]["name"] == "Low Med"
