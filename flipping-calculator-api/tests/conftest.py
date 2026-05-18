import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys
from unittest.mock import patch, MagicMock

# Add the app directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set environment variable to use PostgreSQL for testing before importing app
os.environ["DATABASE_URL"] = "postgresql://flipping_user:flipping_dev_password@localhost/osrs_flipping_test"
os.environ["API_CACHE_DIR"] = "data/test_cache"

from app.main import app
from app.utils.database import get_db, Base, engine, SessionLocal, init_database

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Ensure we use Postgres for tests
    assert "postgresql" in str(engine.url)
    
    # Drop all tables to ensure clean schema
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text("DROP TABLE IF EXISTS flip_transactions CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS user_flips CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS user_settings CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS accounts CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS price_history CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS items CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS price_polling_metadata CASCADE"))
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise

    # Initialize database (create tables)
    init_database()
    
    # Create default test account if it doesn't exist
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (name) VALUES ('TestAccount') ON CONFLICT (name) DO NOTHING")
        cursor.execute("SELECT id FROM accounts WHERE name = 'TestAccount'")
        account_id = cursor.fetchone()['id']
        # Initialize settings for test account
        cursor.execute("INSERT INTO user_settings (account_id, available_cash) VALUES (?, 1000000000) ON CONFLICT (account_id) DO NOTHING", (account_id,))
        conn.commit()
    
    yield
    
    # Teardown: Clean up user data
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            # Only truncate tables that tests modify heavily
            tables_to_clean = ['user_flips', 'flip_transactions', 'user_settings', 'accounts']
            # Check if they exist before truncating
            for table in tables_to_clean:
                connection.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise

@pytest.fixture(scope="session")
def account_id(setup_test_db):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (name) VALUES ('QueenieTsuki') ON CONFLICT (name) DO NOTHING")
        cursor.execute("SELECT id FROM accounts WHERE name = 'QueenieTsuki'")
        acc_id = cursor.fetchone()['id']
        # Give some starting cash for tests
        cursor.execute("INSERT INTO user_settings (account_id, available_cash) VALUES (?, 100000000) ON CONFLICT (account_id) DO NOTHING", (acc_id,))
        conn.commit()
        return acc_id

@pytest.fixture
def auth_header(account_id):
    from app.utils.security import create_access_token
    token = create_access_token({"sub": "QueenieTsuki", "id": account_id})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="session")
def synced_items(setup_test_db):
    # Mock data for syncing - matching production names found in DB
    mock_item_data = [
        {"id": 2, "name": "Steel cannonball", "examine": "Ammo for the Dwarf Multicannon.", "members": True, "lowalch": 3, "highalch": 5, "value": 5, "limit": 7000},
        {"id": 4151, "name": "Abyssal whip", "examine": "A weapon from the Abyss.", "members": True, "lowalch": 72000, "highalch": 120000, "value": 120001, "limit": 70}
    ]
    
    with patch("app.utils.api_client.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_item_data
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        with TestClient(app) as client:
            client.post("/api/items/clear-cache")
            client.post("/api/items/sync")
    return mock_item_data

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()