import pytest

def test_register(client):
    response = client.post("/api/auth/register", json={"name": "newuser", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["name"] == "newuser"

    # Duplicate should fail
    response_dup = client.post("/api/auth/register", json={"name": "newuser", "password": "password123"})
    assert response_dup.status_code == 400

def test_login(client):
    # Ensure user exists
    client.post("/api/auth/register", json={"name": "loginuser", "password": "password123"})
    
    response = client.post(
        "/api/auth/token",
        data={"username": "loginuser", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid(client):
    response = client.post(
        "/api/auth/token",
        data={"username": "loginuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
