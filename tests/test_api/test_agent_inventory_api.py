import pytest
from unittest.mock import patch

@pytest.fixture
def auth_headers(client, db):
    from app.models.staff import Staff
    from app.services.auth_service import get_password_hash
    staff = Staff(name="Test Agent", username="agent.test", hashed_password=get_password_hash("password"), role="pharmacist")
    db.add(staff)
    db.commit()
    
    resp = client.post("/auth/login", data={"username": "agent.test", "password": "password"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@patch("app.api.v1.agent_inventory.run_inventory_agent")
def test_agent_inventory_query(mock_run, client, auth_headers):
    mock_run.return_value = "Yes, Crocin is available. We have 50 in stock."
    
    response = client.post(
        "/agents/inventory/query",
        json={"message": "Crocin hai kya?"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["response"] == "Yes, Crocin is available. We have 50 in stock."
    mock_run.assert_called_once_with("Crocin hai kya?")
