import pytest
from unittest.mock import patch

def test_get_database_stats(client, auth_header):
    with patch("app.services.price_history_service.PriceHistoryService.get_database_stats") as mock_db, \
         patch("app.services.price_history_service.PriceHistoryService.get_polling_metadata") as mock_poll:
        
        mock_db.return_value = {"total_records": 100}
        mock_poll.return_value = {"polling_enabled": True}
        
        response = client.get("/api/price-history/stats", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["database"]["total_records"] == 100
        assert data["polling"]["polling_enabled"] == True

@pytest.mark.asyncio
def test_trigger_manual_poll(client, auth_header):
    with patch("app.services.price_polling_service.price_polling_service.poll_now") as mock_poll_now, \
         patch("app.services.price_history_service.PriceHistoryService.get_polling_metadata") as mock_metadata:
        
        mock_metadata.return_value = {"total_snapshots": 10}
        
        response = client.post("/api/price-history/poll/trigger", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["success"] == True

def test_enable_polling(client, auth_header):
    with patch("app.services.price_history_service.PriceHistoryService.set_polling_enabled") as mock_enable:
        response = client.post("/api/price-history/poll/enable?enabled=false", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["polling_enabled"] == False
        mock_enable.assert_called_once_with(False)
