import pytest
from unittest.mock import patch, MagicMock

def test_get_conversions(client):
    response = client.get("/api/conversions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_sync_conversions(client):
    with patch("app.services.conversion_service.ConversionService.sync_conversions_from_wiki") as mock_sync:
        mock_sync.return_value = {"success": True, "conversions_added": 5}
        response = client.post("/api/conversions/sync")
        assert response.status_code == 200
        assert response.json() == {"success": True, "conversions_added": 5}
