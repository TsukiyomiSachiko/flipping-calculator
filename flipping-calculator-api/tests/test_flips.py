import pytest
from unittest.mock import patch, MagicMock

def test_search_flips(client, synced_items, auth_header):
    # Match the app's reversed logic: buy=high, sell=low
    # To get profit, we need low > high + tax
    mock_prices = {
        "data": {
            "2": {"high": 160, "highTime": 1600000000, "low": 150, "lowTime": 1600000000},
            "4151": {"high": 1500000, "highTime": 1600000000, "low": 1400000, "lowTime": 1600000000}
        }
    }
    mock_volume = {
        "data": {
            "2": {"highPriceVolume": 100000, "lowPriceVolume": 150000},
            "4151": {"highPriceVolume": 100, "lowPriceVolume": 150}
        }
    }
    mock_volume_5m = {
        "data": {
            "2": {"highPriceVolume": 10000, "lowPriceVolume": 15000},
            "4151": {"highPriceVolume": 10, "lowPriceVolume": 15}
        }
    }
    
    with patch("app.utils.api_client.requests.get") as mock_get:
        def side_effect(url, headers=None, params=None):
            mock_res = MagicMock()
            mock_res.status_code = 200
            if "latest" in url:
                mock_res.json.return_value = mock_prices
            elif "1h" in url:
                mock_res.json.return_value = mock_volume
            elif "5m" in url:
                mock_res.json.return_value = mock_volume_5m
            return mock_res
            
        mock_get.side_effect = side_effect
        client.post("/api/items/clear-cache")
        
        # Test flip search with query parameters
        response = client.get("/api/flips/search?min_profit=5&min_volume=10&cash=100000000", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "flips" in data
        assert len(data["flips"]) >= 1
        
        # Verify specific flip details (Steel cannonball should be there)
        item_flip = next((f for f in data["flips"] if f["name"] == "Steel cannonball"), None)
        assert item_flip is not None
        assert item_flip["profit"] > 0

def test_trending_flips(client, synced_items, auth_header):
    mock_prices = {
        "data": {
            "2": {"high": 160, "highTime": 1600000000, "low": 150, "lowTime": 1600000000},
            "4151": {"high": 1500000, "highTime": 1600000000, "low": 1400000, "lowTime": 1600000000}
        }
    }
    mock_volume = {
        "data": {
            "2": {"highPriceVolume": 100000, "lowPriceVolume": 150000, "avgHighPrice": 155, "avgLowPrice": 145},
            "4151": {"highPriceVolume": 100, "lowPriceVolume": 150, "avgHighPrice": 1450000, "avgLowPrice": 1350000}
        }
    }
    mock_volume_5m = {
        "data": {
            "2": {"highPriceVolume": 10000, "lowPriceVolume": 15000, "avgHighPrice": 156, "avgLowPrice": 146},
            "4151": {"highPriceVolume": 10, "lowPriceVolume": 15, "avgHighPrice": 1460000, "avgLowPrice": 1360000}
        }
    }
    
    with patch("app.utils.api_client.requests.get") as mock_get:
        def side_effect(url, headers=None, params=None):
            mock_res = MagicMock()
            mock_res.status_code = 200
            if "latest" in url:
                mock_res.json.return_value = mock_prices
            elif "1h" in url:
                mock_res.json.return_value = mock_volume
            elif "5m" in url:
                mock_res.json.return_value = mock_volume_5m
            return mock_res
            
        mock_get.side_effect = side_effect
        client.post("/api/items/clear-cache")
        
        # Test trending flips endpoint
        response = client.get("/api/flips/trending?limit=5", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "count" in data
        assert "flips" in data
        assert isinstance(data["flips"], list)
        # Steel cannonball should be among the trending list
        assert any(item["name"] == "Steel cannonball" for item in data["flips"])

