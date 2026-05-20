import pytest
from unittest.mock import patch, MagicMock
from app.services.alch_service import AlchService
from app.utils.database import engine
from sqlalchemy import text

# Seed data helper
def _insert_item(item_id: int, name: str, highalch: int, ge_limit: int):
    with engine.connect() as conn:
        conn.execute(
            text(
                'INSERT INTO items (id, name, examine, members, lowalch, highalch, value, ge_limit) '
                'VALUES (:id, :name, \'Examine text\', true, 10, :highalch, 20, :ge_limit) '
                'ON CONFLICT (id) DO UPDATE SET highalch = EXCLUDED.highalch, ge_limit = EXCLUDED.ge_limit'
            ),
            {"id": item_id, "name": name, "highalch": highalch, "ge_limit": ge_limit}
        )
        conn.commit()

def test_get_profitable_alchs(client, synced_items):
    # Insert custom items for testing alchs
    _insert_item(1001, "Profitable Item A", 1000, 100) # High alch = 1000, buy = 500, limit = 100. Profit = 1000 - 500 - 90 = 410. Profit at limit = 41000
    _insert_item(1002, "Profitable Item B", 2000, 10)  # High alch = 2000, buy = 1200, limit = 10. Profit = 2000 - 1200 - 90 = 710. Profit at limit = 7100
    
    mock_prices = {
        "561": {"low": 90, "high": 92}, # Nature Rune
        "2": {"low": 150, "high": 160},  # Steel cannonball (highalch=5, negative profit, will be excluded)
        "4151": {"low": 115000, "high": 116000}, # Abyssal whip (highalch=120000, profit = 120000 - 115000 - 90 = 4910)
        "1001": {"low": 500, "high": 510},
        "1002": {"low": 1200, "high": 1210}
    }
    
    mock_volumes = {
        "2": {"lowPriceVolume": 1000, "highPriceVolume": 1000},
        "4151": {"lowPriceVolume": 5, "highPriceVolume": 5},
        "1001": {"lowPriceVolume": 20, "highPriceVolume": 30},
        "1002": {"lowPriceVolume": 50, "highPriceVolume": 50}
    }
    
    with patch("app.services.alch_service.fetch_latest_prices") as mock_latest, \
         patch("app.services.alch_service.fetch_volume_data") as mock_volume:
        mock_latest.return_value = {"data": mock_prices}
        mock_volume.return_value = {"data": mock_volumes}
        
        # Test direct service logic
        results = AlchService.get_profitable_alchs(min_volume=1)
        
        # Whip: profit = 120000 - 115090 = 4910, limit = 70. Profit at limit = 343,700
        # Item A: profit = 1000 - 590 = 410, limit = 100. Profit at limit = 41,000
        # Item B: profit = 2000 - 1290 = 710, limit = 10. Profit at limit = 7,100
        # Sort order should be: Whip (343,700), Item A (41,000), Item B (7,100)
        
        assert len(results) == 3
        
        # 1. Abyssal whip
        assert results[0]["id"] == 4151
        assert results[0]["profit_per_alch"] == 4910
        assert results[0]["profit_at_limit"] == 343700
        
        # 2. Profitable Item A
        assert results[1]["id"] == 1001
        assert results[1]["profit_per_alch"] == 410
        assert results[1]["profit_at_limit"] == 41000
        
        # 3. Profitable Item B
        assert results[2]["id"] == 1002
        assert results[2]["profit_per_alch"] == 710
        assert results[2]["profit_at_limit"] == 7100

def test_alch_endpoint(client, synced_items):
    _insert_item(1001, "Profitable Item A", 1000, 100)
    
    mock_prices = {
        "561": {"low": 90, "high": 92},
        "1001": {"low": 500, "high": 510}
    }
    mock_volumes = {
        "1001": {"lowPriceVolume": 20, "highPriceVolume": 30}
    }
    
    with patch("app.services.alch_service.fetch_latest_prices") as mock_latest, \
         patch("app.services.alch_service.fetch_volume_data") as mock_volume:
        mock_latest.return_value = {"data": mock_prices}
        mock_volume.return_value = {"data": mock_volumes}
        
        response = client.get("/api/alch/profitable?min_volume=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "Profitable Item A"
        assert data[0]["volume_1h"] == 50
