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


def test_crash_risk_sorting_secondary_score(client, synced_items, auth_header):
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
    
    with patch("app.utils.api_client.requests.get") as mock_get, \
         patch("app.services.data_quality_service.DataQualityService.get_historical_crash_risk") as mock_crash_risk, \
         patch("app.services.item_service.ItemService.calculate_score") as mock_calc_score:
        
        # Both items return same crash risk score
        mock_crash_risk.return_value = 15.0
        
        # Mock scores: Item 2 has score 50, Item 4151 has score 80
        # Since crash_risk is the same, 4151 (higher score) should appear before 2
        def score_side_effect(*args, **kwargs):
            buy_price = kwargs.get("buy_price")
            if buy_price == 150:
                return 50
            return 80
        mock_calc_score.side_effect = score_side_effect
        
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
        
        # Test sorting by crash_risk
        response = client.get("/api/flips/search?min_profit=0&sort_by=crash_risk&cash=100000000", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "flips" in data
        flips = data["flips"]
        
        assert len(flips) >= 2
        # Abyssal whip (4151) has score 80, Steel cannonball (2) has score 50.
        # Identical crash risk (15.0).
        # Abyssal whip should be first.
        idx_whip = next(i for i, f in enumerate(flips) if f["id"] == 4151)
        idx_cannonball = next(i for i, f in enumerate(flips) if f["id"] == 2)
        assert idx_whip < idx_cannonball


def test_risk_to_reward_sorting(client, synced_items, auth_header):
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
    
    with patch("app.utils.api_client.requests.get") as mock_get, \
         patch("app.services.data_quality_service.DataQualityService.get_historical_crash_risk") as mock_crash_risk, \
         patch("app.services.item_service.ItemService.calculate_score") as mock_calc_score, \
         patch("app.services.data_quality_service.DataQualityService.get_historical_drawdown") as mock_drawdown:
        
        # Mock historical drawdown: Item 2 has drawdown 5.0%, Item 4151 has drawdown 1.0%
        # Item 2: buy_price=150, profit=7 -> ROI ~ 4.67%. R2R = 5.0 / 4.67 = 1.07
        # Item 4151: buy_price=1400000, profit=72000 -> ROI ~ 5.14%. R2R = 1.0 / 5.14 = 0.19
        # Lower risk-to-reward ratio is better, so 4151 should sort before 2.
        def drawdown_side_effect(item_id, *args, **kwargs):
            if item_id == 2:
                return 5.0
            return 1.0
        mock_drawdown.side_effect = drawdown_side_effect
        mock_crash_risk.return_value = 10.0
        
        def score_side_effect(*args, **kwargs):
            return 75.0
        mock_calc_score.side_effect = score_side_effect
        
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
        
        # Test sorting by risk_reward
        response = client.get("/api/flips/search?min_profit=0&sort_by=risk_reward&cash=100000000", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "flips" in data
        flips = data["flips"]
        
        assert len(flips) >= 2
        
        # Verify 4151 (R2R ratio 0.19) comes before 2 (R2R ratio 1.07)
        idx_whip = next(i for i, f in enumerate(flips) if f["id"] == 4151)
        idx_cannonball = next(i for i, f in enumerate(flips) if f["id"] == 2)
        assert idx_whip < idx_cannonball

