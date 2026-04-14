import pytest

def test_account_operations(client):
    # 1. Create a new account
    acc_name = "NewTestAccount"
    response = client.post("/api/accounts/", json={"name": acc_name})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == acc_name
    new_acc_id = data["id"]
    
    # 2. List accounts
    response = client.get("/api/accounts/")
    assert response.status_code == 200
    accounts = response.json()
    assert any(acc["id"] == new_acc_id for acc in accounts)
    
    # 3. Check settings created for new account
    response = client.get("/api/settings", headers={"X-Account-Id": str(new_acc_id)})
    assert response.status_code == 200
    settings = response.json()
    assert settings["available_cash"] == 0
    
    # 4. Set cash for new account
    response = client.post("/api/settings/cash", json={"amount": 5000}, headers={"X-Account-Id": str(new_acc_id)})
    assert response.status_code == 200
    
    # 5. Verify settings updated
    response = client.get("/api/settings", headers={"X-Account-Id": str(new_acc_id)})
    assert response.status_code == 200
    assert response.json()["available_cash"] == 5000
