import pytest
from unittest.mock import patch

def test_get_item_margin_analysis(client, auth_header):
    with patch("app.services.margin_tracking_service.MarginTrackingService.analyze_item_margins") as mock_analyze:
        mock_analyze.return_value = {
            "item_id": 4151,
            "current_margin": 100,
            "average_margin": 120,
            "trend": "stable"
        }
        
        response = client.get("/api/margins/item/4151", headers=auth_header)
        assert response.status_code == 200
        assert response.json()["item_id"] == 4151
        assert response.json()["trend"] == "stable"

def test_get_item_margin_analysis_not_found(client, auth_header):
    with patch("app.services.margin_tracking_service.MarginTrackingService.analyze_item_margins") as mock_analyze:
        mock_analyze.return_value = None
        
        response = client.get("/api/margins/item/99999", headers=auth_header)
        assert response.status_code == 404
