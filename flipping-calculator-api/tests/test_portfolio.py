import pytest
from unittest.mock import patch, MagicMock


def test_portfolio_flow(client, synced_items, auth_header):
    # 1. Check initial summary
    response = client.get("/api/portfolio/summary", headers=auth_header)
    assert response.status_code == 200
    initial_summary = response.json()
    
    # 2. Log a buy
    buy_data = {
        "item_name": "Steel cannonball",
        "quantity": 1000,
        "price": 150
    }
    response = client.post("/api/portfolio/buy", json=buy_data, headers=auth_header)
    assert response.status_code == 200
    buy_res = response.json()
    assert buy_res["item_name"] == "Steel cannonball"
    flip_id = buy_res["flip_id"]
    
    # 3. Check pending flips
    response = client.get("/api/portfolio/pending", headers=auth_header)
    assert response.status_code == 200
    pending = response.json()
    assert any(f["id"] == flip_id for f in pending)
    
    # 4. Log a sell (partial)
    sell_data = {
        "flip_id": flip_id,
        "quantity": 400,
        "price": 160
    }
    response = client.post("/api/portfolio/sell", json=sell_data, headers=auth_header)
    assert response.status_code == 200
    sell_res = response.json()
    assert "Sold 400x" in sell_res["message"]
    
    # 5. Check pending again (should still be pending as only 400/1000 sold)
    response = client.get("/api/portfolio/pending", headers=auth_header)
    assert response.status_code == 200
    pending = response.json()
    flip = next(f for f in pending if f["id"] == flip_id)
    assert flip["quantity_remaining"] == 600
    
    # 6. Log remaining sell
    sell_data = {
        "flip_id": flip_id,
        "quantity": 600,
        "price": 165
    }
    response = client.post("/api/portfolio/sell", json=sell_data, headers=auth_header)
    assert response.status_code == 200
    
    # 7. Check completed flips
    response = client.get("/api/portfolio/completed", headers=auth_header)
    assert response.status_code == 200
    completed = response.json()
    assert any(f["id"] == flip_id for f in completed)
    
    # 8. Check summary updated
    response = client.get("/api/portfolio/summary", headers=auth_header)
    assert response.status_code == 200
    new_summary = response.json()
    assert new_summary["total_profit"] > initial_summary.get("total_profit", 0)

def test_cancel_flip(client, synced_items, auth_header):
    # Log a buy
    buy_data = {
        "item_name": "Abyssal whip",
        "quantity": 1,
        "price": 1500000
    }
    response = client.post("/api/portfolio/buy", json=buy_data, headers=auth_header)
    flip_id = response.json()["flip_id"]
    
    # Cancel it
    cancel_data = {
        "flip_id": flip_id,
        "reason": "Price dropped"
    }
    response = client.post("/api/portfolio/cancel", json=cancel_data, headers=auth_header)
    assert response.status_code == 200
    
    # Check cancelled flips
    response = client.get("/api/portfolio/cancelled", headers=auth_header)
    assert response.status_code == 200
    cancelled = response.json()
    assert any(f["id"] == flip_id for f in cancelled)

def test_portfolio_advanced_operations(client, synced_items, auth_header):
    # 1. Log a buy with an intended quantity higher than actual quantity (partial fill)
    buy_data = {
        "item_name": "Steel cannonball",
        "quantity": 500,
        "price": 150,
        "intended_quantity": 1000
    }
    response = client.post("/api/portfolio/buy", json=buy_data, headers=auth_header)
    assert response.status_code == 200
    buy_res = response.json()
    flip_id = buy_res["flip_id"]

    # 2. Get pending projections (mock prices first)
    mock_prices = {
        "data": {
            "2": {"high": 160, "highTime": 1600000000, "low": 150, "lowTime": 1600000000}
        }
    }
    with patch("app.services.portfolio_service.fetch_latest_prices") as mock_fetch:
        mock_fetch.return_value = mock_prices
        response = client.get("/api/portfolio/pending/projections", headers=auth_header)
        assert response.status_code == 200
        projections = response.json()
        assert "flips" in projections
        assert any(f["id"] == flip_id for f in projections["flips"])

    # 3. Update the buy price for the pending flip
    response = client.patch(f"/api/portfolio/flip/{flip_id}/buy-price", json={"new_price": 145}, headers=auth_header)
    assert response.status_code == 200
    assert response.json()["new_price"] == 145

    # 4. Adjust the intended quantity to match what was actually bought (frees up reserved cash)
    response = client.patch(f"/api/portfolio/flip/{flip_id}/adjust-intended", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["new_intended"] == 500

    # 5. Get portfolio statistics
    response = client.get("/api/portfolio/statistics", headers=auth_header)
    assert response.status_code == 200
    stats = response.json()
    assert "best_items" in stats
    assert "worst_items" in stats

    # 6. Export portfolio to CSV
    response = client.get("/api/portfolio/export", headers=auth_header)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "item_name" in response.text

    # 7. Delete the flip permanently
    response = client.delete(f"/api/portfolio/flip/{flip_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True