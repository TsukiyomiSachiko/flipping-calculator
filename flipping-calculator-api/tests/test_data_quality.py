import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from app.services.data_quality_service import DataQualityService

def test_check_price_floor():
    # Min price < 10 -> score 0
    assert DataQualityService._check_price_floor(5, 8) == 0
    # Min price < 25 -> score 30
    assert DataQualityService._check_price_floor(15, 20) == 30
    # Min price < 50 -> score 60
    assert DataQualityService._check_price_floor(35, 45) == 60
    # Min price >= 50 -> score 100
    assert DataQualityService._check_price_floor(100, 110) == 100

def test_check_spread_sanity():
    # Invalid buy price
    score, msg = DataQualityService._check_spread_sanity(0, 100, 100)
    assert score == 0
    assert "Invalid buy price" in msg

    # Spread > 10x (Impossible spread)
    score, msg = DataQualityService._check_spread_sanity(10, 110, 100)
    assert score == 0
    assert "Impossible spread" in msg

    # Spread > 5x (Very wide spread)
    score, msg = DataQualityService._check_spread_sanity(10, 60, 50)
    assert score == 30
    assert "Very wide spread" in msg

    # Spread > 2x (Wide spread)
    score, msg = DataQualityService._check_spread_sanity(10, 25, 15)
    assert score == 60
    assert "Wide spread" in msg

    # Healthy spread
    score, msg = DataQualityService._check_spread_sanity(10, 12, 2)
    assert score == 100
    assert msg is None

def test_check_volume_correlation():
    # Small price change -> score 100
    score, msg = DataQualityService._check_volume_correlation(0.5, 10)
    assert score == 100
    assert msg is None

    # Big price change (> 20%) on low volume (< 20000)
    score, msg = DataQualityService._check_volume_correlation(25.0, 1000)
    assert score == 20
    assert "Price moved" in msg

    # Big price change (> 10%) on low volume (< 5000)
    score, msg = DataQualityService._check_volume_correlation(12.0, 500)
    assert score == 20

    # Big price change (> 5%) on moderate volume (e.g. 300, expected 1000)
    score, msg = DataQualityService._check_volume_correlation(6.0, 300)
    assert score == 50
    assert "Low volume" in msg

    # Healthy volume for price move
    score, msg = DataQualityService._check_volume_correlation(6.0, 2000)
    assert score == 100
    assert msg is None

def test_check_volatility_zscore():
    # Extreme outlier (Z-score > 3.0)
    # Volatility = 2.0, current change = 8.0 -> Z = 4.0
    score, msg = DataQualityService._check_volatility_zscore(1, 8.0, 2.0)
    assert score == 20
    assert "Extreme outlier" in msg

    # Suspicious movement (Z-score > 2.0)
    # Volatility = 2.0, current change = 5.0 -> Z = 2.5
    score, msg = DataQualityService._check_volatility_zscore(1, 5.0, 2.0)
    assert score == 50
    assert "Suspicious movement" in msg

    # Healthy movement
    score, msg = DataQualityService._check_volatility_zscore(1, 1.0, 2.0)
    assert score == 100
    assert msg is None

@patch("app.services.data_quality_service.DataQualityService._check_price_stability")
def test_calculate_data_quality_score(mock_stability):
    mock_stability.return_value = (100.0, None)
    
    # Check overall quality scoring combination
    result = DataQualityService.calculate_data_quality_score(
        item_id=4151,
        buy_price=1000,
        sell_price=1050,
        profit=50,
        volume_1h=5000,
        ge_limit=70,
        price_change_pct=1.0,
        historical_volatility=2.0
    )
    
    assert result["quality_score"] == 100.0
    assert result["quality_tier"] == "high"
    assert len(result["flags"]) == 0

@patch("app.services.data_quality_service.get_db")
@patch("app.services.item_service.ItemService.get_all_items")
def test_prewarm_cache(mock_get_all, mock_get_db):
    # Mock items list
    mock_get_all.return_value = [{"id": 4151, "name": "Abyssal whip"}]
    
    # Mock DB cursor/results
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Price history rows (30 points to satisfy min 24 requirements)
    history_rows = []
    base_time = datetime.now(timezone.utc)
    for i in range(30):
        history_rows.append({
            "timestamp": base_time + timedelta(hours=i),
            "price_high": 1000 + i * 2,
            "price_low": 980 + i * 2
        })
    
    # Stability check rows
    stability_rows = [
        {"price_high": 1050, "price_low": 1030},
        {"price_high": 1045, "price_low": 1025},
        {"price_high": 1048, "price_low": 1028},
        {"price_high": 1052, "price_low": 1032},
        {"price_high": 1050, "price_low": 1030},
    ]
    
    # Setup cursor side effects:
    # First query is for price history (30 rows)
    # Second query is for stability baseline (5 rows)
    mock_cursor.fetchall.side_effect = [history_rows, stability_rows]
    
    # Reset caches
    DataQualityService._volatility_cache = {}
    DataQualityService._stability_cache = {}
    DataQualityService._trajectory_cache = {}
    DataQualityService._cache_timestamp = None
    
    # Trigger prewarm
    DataQualityService.prewarm_cache()
    
    assert 4151 in DataQualityService._volatility_cache
    assert DataQualityService._volatility_cache[4151] is not None
    assert 4151 in DataQualityService._stability_cache
    assert DataQualityService._stability_cache[4151] == 1039.0
    assert 4151 in DataQualityService._trajectory_cache
    assert DataQualityService._cache_timestamp is not None
