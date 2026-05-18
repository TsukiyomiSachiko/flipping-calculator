import pytest

def test_cashflow_profit_take(client, synced_items, auth_header):
    # Set cash to 1_000_000 and profit_take to 10%
    client.post("/api/settings/cash", json={"amount": 1000000}, headers=auth_header)
    client.post("/api/settings/cashflow", json={"profit_take_pct": 10.0, "loss_refill_pct": 0.0}, headers=auth_header)

    # Buy 1 whip for 100k
    buy_data = {
        "item_name": "Abyssal whip",
        "quantity": 1,
        "price": 100000
    }
    response = client.post("/api/portfolio/buy", json=buy_data, headers=auth_header)
    flip_id = response.json()["flip_id"]

    # Cash should be 900,000
    settings = client.get("/api/settings", headers=auth_header).json()
    assert settings["available_cash"] == 900000

    # Sell 1 whip for 110k
    sell_data = {
        "flip_id": flip_id,
        "price": 110000,
        "quantity": 1
    }
    client.post(f"/api/portfolio/sell", json=sell_data, headers=auth_header)

    # Tax on 110k is 2200.
    # Revenue = 107800
    # Cost = 100000
    # Profit = 7800
    # Profit take = 7800 * 0.1 = 780
    # Adjusted revenue = 107800 - 780 = 107020
    # New cash should be 900000 + 107020 = 1007020

    settings = client.get("/api/settings", headers=auth_header).json()
    assert settings["available_cash"] == 1007020

def test_cashflow_loss_refill(client, synced_items, auth_header):
    # Set cash to 1_000_000 and loss refill to 10%
    client.post("/api/settings/cash", json={"amount": 1000000}, headers=auth_header)
    client.post("/api/settings/cashflow", json={"profit_take_pct": 0.0, "loss_refill_pct": 10.0}, headers=auth_header)

    # Buy 1 whip for 100k
    buy_data = {
        "item_name": "Abyssal whip",
        "quantity": 1,
        "price": 100000
    }
    response = client.post("/api/portfolio/buy", json=buy_data, headers=auth_header)
    flip_id = response.json()["flip_id"]

    # Cash should be 900,000
    settings = client.get("/api/settings", headers=auth_header).json()
    assert settings["available_cash"] == 900000

    # Sell 1 whip for 90k
    sell_data = {
        "flip_id": flip_id,
        "price": 90000,
        "quantity": 1
    }
    client.post(f"/api/portfolio/sell", json=sell_data, headers=auth_header)

    # Tax on 90k is 1800.
    # Revenue = 88200
    # Cost = 100000
    # Profit = -11800 (Loss of 11800)
    # Refill = 11800 * 0.1 = 1180
    # Adjusted revenue = 88200 + 1180 = 89380
    # New cash should be 900000 + 89380 = 989380

    settings = client.get("/api/settings", headers=auth_header).json()
    assert settings["available_cash"] == 989380
