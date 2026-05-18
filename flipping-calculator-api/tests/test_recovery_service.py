import pytest
from unittest.mock import patch, MagicMock
from app.services.recovery_service import RecoveryAnalysisService

@patch('app.services.recovery_service.fetch_price_timeseries')
def test_break_even_profitability(mock_fetch):
    # Setup mock data
    # Item ID: 123
    # Buy Price: 19
    # Current Sell Price: 19
    # Tax: 0 (price <= 50)
    # Expected: distance_gp = 0, distance_pct = 0
    
    mock_data = {
        'data': [
            {'timestamp': 1000, 'avgHighPrice': 20, 'avgLowPrice': 18, 'highPriceVolume': 100, 'lowPriceVolume': 100},
            {'timestamp': 2000, 'avgHighPrice': 20, 'avgLowPrice': 18, 'highPriceVolume': 100, 'lowPriceVolume': 100},
            {'timestamp': 3000, 'avgHighPrice': 20, 'avgLowPrice': 18, 'highPriceVolume': 100, 'lowPriceVolume': 100},
            {'timestamp': 4000, 'avgHighPrice': 19, 'avgLowPrice': 18, 'highPriceVolume': 100, 'lowPriceVolume': 100}, # Current
        ]
    }
    mock_fetch.return_value = mock_data

    item_id = 123
    buy_price = 19
    
    result = RecoveryAnalysisService.analyse_recovery(item_id, buy_price)
    
    assert result is not None
    assert result['distance_gp'] == 0
    assert result['recommendation'] == "SELL"
    assert result['reasoning'] == "Break-even at current market prices."

@patch('app.services.recovery_service.fetch_price_timeseries')
def test_already_profitable(mock_fetch):
    # Setup mock data for profitable case
    # Buy Price: 19
    # Current Sell Price: 21
    # Tax: 0 (price <= 50)
    # Profit: 21 - 19 = 2
    
    mock_data = {
        'data': [
            {'timestamp': 1000, 'avgHighPrice': 20, 'avgLowPrice': 18, 'highPriceVolume': 100, 'lowPriceVolume': 100},
            {'timestamp': 2000, 'avgHighPrice': 20, 'avgLowPrice': 18, 'highPriceVolume': 100, 'lowPriceVolume': 100},
            {'timestamp': 3000, 'avgHighPrice': 20, 'avgLowPrice': 18, 'highPriceVolume': 100, 'lowPriceVolume': 100},
            {'timestamp': 4000, 'avgHighPrice': 21, 'avgLowPrice': 18, 'highPriceVolume': 100, 'lowPriceVolume': 100}, # Profitable
        ]
    }
    mock_fetch.return_value = mock_data

    item_id = 123
    buy_price = 19
    
    result = RecoveryAnalysisService.analyse_recovery(item_id, buy_price)
    
    assert result is not None
    assert result['distance_gp'] > 0
    assert result['recommendation'] == "SELL"
    assert result['reasoning'] == "Already profitable at current market prices."
