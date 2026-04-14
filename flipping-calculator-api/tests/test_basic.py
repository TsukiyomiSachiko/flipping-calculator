import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.database import get_db, Base, engine, SessionLocal
import os

# Use a separate test database
TEST_DATABASE_URL = "sqlite:///./test_osrs_flipping.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # In a real scenario, we might want to use a different engine/session for tests
    # but for simplicity in this regression test, we'll try to use the existing ones
    # if we can override them.
    pass

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "OSRS Flipping Calculator API" in response.json()["message"]

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
