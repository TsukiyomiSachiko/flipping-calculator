import pytest
from datetime import timedelta
from jose import jwt
from app.utils.security import SECRET_KEY, ALGORITHM, create_access_token, create_refresh_token

def test_register(client):
    response = client.post("/api/auth/register", json={"name": "newuser", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
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
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_login_invalid(client):
    response = client.post(
        "/api/auth/token",
        data={"username": "loginuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

def test_refresh_token_flow(client):
    # 1. Register a user and get tokens
    response = client.post("/api/auth/register", json={"name": "refreshuser", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    refresh_token = data["refresh_token"]
    
    # 2. Call refresh endpoint
    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"

def test_refresh_token_type_checks(client):
    # Register to get valid details
    response = client.post("/api/auth/register", json={"name": "typeuser", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # 1. Trying to refresh using an access_token should fail (wrong type claim)
    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": access_token})
    assert refresh_response.status_code == 401

    # 2. Trying to access protected route with a refresh_token should fail
    protected_response = client.get("/api/accounts", headers={"Authorization": f"Bearer {refresh_token}"})
    assert protected_response.status_code == 401

def test_refresh_expired_token(client):
    # Generate an expired refresh token manually
    expired_token = create_refresh_token(
        data={"sub": "expireduser", "id": 9999},
        expires_delta=timedelta(seconds=-1)
    )
    
    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": expired_token})
    assert refresh_response.status_code == 401

