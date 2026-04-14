import pytest

def test_settings_flow(client, auth_header):

    # Get initial settings

    response = client.get("/api/settings", headers=auth_header)

    assert response.status_code == 200

    settings = response.json()

    assert "available_cash" in settings

    

    # Set cash

    response = client.post("/api/settings/cash", json={"amount": 1000000}, headers=auth_header)

    assert response.status_code == 200

    assert response.json()["available_cash"] == 1000000



def test_trajectory(client, synced_items, auth_header):

    # Test trajectory endpoint for an item

    response = client.get("/api/trajectory/item/4151", headers=auth_header)

    assert response.status_code in [200, 404]



def test_liquidity(client, synced_items, auth_header):

    # Test liquidity analysis

    response = client.get("/api/liquidity/4151", headers=auth_header)

    assert response.status_code in [200, 404]
