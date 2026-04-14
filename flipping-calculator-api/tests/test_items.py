import pytest
from unittest.mock import patch, MagicMock

def test_sync_items(client):
    mock_item_data = [
        {"id": 2, "name": "Steel cannonball", "examine": "Ammo for the Dwarf Multicannon.", "members": True, "lowalch": 3, "highalch": 5, "value": 5, "limit": 7000},
        {"id": 4151, "name": "Abyssal whip", "examine": "A weapon from the Abyss.", "members": True, "lowalch": 72000, "highalch": 120000, "value": 120001, "limit": 70}
    ]
    
    with patch("app.utils.api_client.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_item_data
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client.post("/api/items/clear-cache")
        response = client.post("/api/items/sync")
        assert response.status_code == 200

def test_get_items(client, synced_items):
    response = client.get("/api/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 2
    assert any(item["name"] == "Steel cannonball" for item in items)
    assert any(item["name"] == "Abyssal whip" for item in items)

def test_search_items(client, synced_items):
    # Searching for "Abyssal whip" to be more specific if production data has many whips
    response = client.get("/api/items/search?q=Abyssal%20whip")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert items[0]["name"] == "Abyssal whip"

def test_get_item_by_id(client, synced_items):
    response = client.get("/api/items/4151")
    assert response.status_code == 200
    item = response.json()
    assert item["name"] == "Abyssal whip"
    assert item["ge_limit"] == 70

def test_get_item_with_prices(client, synced_items, auth_header):

    mock_prices = {

        "data": {

            "4151": {"high": 1400000, "highTime": 1600000000, "low": 1500000, "lowTime": 1600000000}

        }

    }

    mock_volume = {

        "data": {

            "4151": {"highPriceVolume": 100, "lowPriceVolume": 150}

        }

    }

    mock_volume_5m = {

        "data": {

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

        

        response = client.get("/api/items/4151/prices", headers=auth_header)

        assert response.status_code == 200

        data = response.json()

        assert data["name"] == "Abyssal whip"
