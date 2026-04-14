# API Documentation

Complete reference for OSRS Flipping Calculator API endpoints.

## Base URL

```
http://localhost:8000
```

---

## Items Endpoints

### Sync Items

**POST** `/api/items/sync`

First-time setup: Syncs ~3,000 items from OSRS Wiki API to database.

**Response:**
```json
{
  "message": "Synced 3124 items",
  "count": 3124
}
```

---

### Get All Items

**GET** `/api/items?limit=100&offset=0`

Get all items from database with pagination.

**Query Parameters:**
- `limit` (optional): Number of items to return
- `offset` (optional): Skip first N items

**Response:**
```json
[
  {
    "id": 534,
    "name": "Dragon bones",
    "examine": "Bones from a dragon.",
    "members": true,
    "limit": 10000,
    "icon": "..."
  }
]
```

---

### Search Items

**GET** `/api/items/search?q=dragon&limit=20`

Search items by name (partial match).

**Query Parameters:**
- `q` (required): Search query
- `limit` (optional): Max results (default: 20)

**Response:**
```json
[
  {
    "id": 534,
    "name": "Dragon bones",
    ...
  },
  {
    "id": 11286,
    "name": "Dragonfire shield",
    ...
  }
]
```

---

### Get Single Item

**GET** `/api/items/{item_id}`

Get item details by ID.

**Response:**
```json
{
  "id": 534,
  "name": "Dragon bones",
  "examine": "Bones from a dragon.",
  "members": true,
  "limit": 10000,
  "icon": "..."
}
```

---

### Clear Cache

**POST** `/api/items/clear-cache`

Clear all API response caches (prices, volume, items).

**Response:**
```json
{
  "message": "All caches cleared"
}
```

---

## Flips Endpoints

### Search Profitable Flips (GET)

**GET** `/api/flips/search`

Find profitable items to flip with advanced filtering.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_profit` | int | 0 | Minimum profit per flip (gp) |
| `min_roi` | float | 0 | Minimum ROI (%) |
| `max_roi` | float | 25.0 | Maximum ROI (%) |
| `min_limit_profit` | int | 0 | Minimum profit at GE limit (gp) |
| `min_volume` | int | 0 | Minimum hourly volume |
| `high_volume_only` | bool | false | Only 50k+ volume |
| `cash` | int | null | Your available cash (filters unaffordable) |
| `members_only` | bool | false | Only members items |
| `f2p_only` | bool | false | Only F2P items |
| `sort_by` | string | "profit" | Sort by: profit, roi, limit, volume |
| `limit` | int | 20 | Number of results (1-100) |

**Example Request:**
```
GET /api/flips/search?min_profit=100&min_volume=5000&cash=10000000&limit=10
```

**Response:**
```json
{
  "count": 10,
  "filters": {
    "min_profit": 100,
    "min_volume": 5000,
    "cash": 10000000,
    "sort_by": "profit",
    "limit": 10
  },
  "flips": [
    {
      "id": 534,
      "name": "Dragon bones",
      "members": true,
      "buy_price": 2500,
      "sell_price": 2650,
      "profit": 97,
      "roi": 3.88,
      "volume": 145230,
      "volume_indicator": "🟢 HIGH",
      "ge_limit": 10000,
      "profit_at_limit": 970000,
      "max_qty": 10000,
      "your_profit": 970000
    }
  ]
}
```

---

### Search Profitable Flips (POST)

**POST** `/api/flips/search`

Alternative to GET for complex queries using JSON body.

**Request Body:**
```json
{
  "min_profit": 100,
  "min_roi": 5,
  "max_roi": 20,
  "min_volume": 5000,
  "cash": 10000000,
  "sort_by": "profit",
  "limit": 20
}
```

**Response:** Same as GET version

---

### Get Flip Stats

**GET** `/api/flips/stats`

Get statistics about available flips.

**Response:**
```json
{
  "total_items": 3124,
  "items_with_prices": 2847,
  "items_with_volume": 1523
}
```

---

## Portfolio Endpoints

### Log Buy

**POST** `/api/portfolio/buy`

Log a purchase transaction (create new flip).

**Request Body:**
```json
{
  "item_name": "dragon bones",
  "quantity": 10000,
  "price": 2500,
  "notes": "Overnight flip"
}
```

**Response:**
```json
{
  "flip_id": 1,
  "item_name": "Dragon bones",
  "quantity": 10000,
  "price": 2500,
  "message": "Logged buy: 10000x Dragon bones @ 2,500 gp"
}
```

**Error Response (Multiple Matches):**
```json
{
  "error": "Multiple items found",
  "matches": [
    {"id": 534, "name": "Dragon bones"},
    {"id": 6812, "name": "Dragon bones (noted)"}
  ]
}
```

---

### Add to Flip

**POST** `/api/portfolio/add`

Add more quantity to existing flip (for multiple GE trades).
Calculates weighted average buy price.

**Request Body:**
```json
{
  "flip_id": 1,
  "quantity": 5000,
  "price": 2480,
  "notes": "Second batch"
}
```

**Response:**
```json
{
  "flip_id": 1,
  "added_quantity": 5000,
  "new_total": 15000,
  "new_avg_price": 2493,
  "message": "Added 5000x to flip, new average: 2,493 gp"
}
```

---

### Log Sell

**POST** `/api/portfolio/sell`

Log a sale (full or partial). Supports two price formats.

**Option 1: Per-Item Price**
```json
{
  "flip_id": 1,
  "price": 2650,
  "quantity": 10000
}
```

**Option 2: Total Price (calculates per-item)**
```json
{
  "flip_id": 1,
  "price_total": 26500000,
  "quantity": 10000
}
```

**Response (Completed):**
```json
{
  "flip_id": 1,
  "sold_quantity": 10000,
  "price_per_item": 2650,
  "profit": 970000,
  "roi": 3.88,
  "status": "completed",
  "total_profit": 970000,
  "message": "Flip completed! Total profit: 970,000 gp"
}
```

**Response (Partial):**
```json
{
  "flip_id": 1,
  "sold_quantity": 6000,
  "price_per_item": 2650,
  "profit": 582000,
  "roi": 3.88,
  "status": "partial",
  "remaining": 4000,
  "message": "Sold 6000x, 4000x remaining"
}
```

---

### Cancel Flip

**POST** `/api/portfolio/cancel`

Cancel a pending flip with optional reason.

**Request Body:**
```json
{
  "flip_id": 5,
  "reason": "Price crashed to 35k"
}
```

**Response:**
```json
{
  "flip_id": 5,
  "status": "cancelled",
  "reason": "Price crashed to 35k",
  "message": "Cancelled flip #5"
}
```

---

### Get Pending Flips

**GET** `/api/portfolio/pending`

Get all pending flips (items bought but not sold).

**Response:**
```json
[
  {
    "id": 1,
    "item_id": 534,
    "item_name": "Dragon bones",
    "quantity_total": 10000,
    "quantity_remaining": 4000,
    "buy_price": 2500,
    "sell_price": null,
    "buy_time": "2026-02-05T14:30:00",
    "sell_time": null,
    "profit": 582000,
    "roi": 3.88,
    "status": "pending",
    "cancel_reason": null,
    "notes": null
  }
]
```

---

### Get Completed Flips

**GET** `/api/portfolio/completed?limit=20`

Get completed flips (most recent first).

**Query Parameters:**
- `limit` (optional): Number of flips (default: 20, max: 100)

**Response:**
```json
[
  {
    "id": 15,
    "item_id": 534,
    "item_name": "Dragon bones",
    "quantity_total": 10000,
    "quantity_remaining": 0,
    "buy_price": 2500,
    "sell_price": 2650,
    "buy_time": "2026-02-05T14:30:00",
    "sell_time": "2026-02-05T16:00:00",
    "profit": 970000,
    "roi": 3.88,
    "status": "completed",
    "cancel_reason": null,
    "notes": null
  }
]
```

---

### Get Cancelled Flips

**GET** `/api/portfolio/cancelled?limit=20`

Get cancelled flips with reasons.

**Query Parameters:**
- `limit` (optional): Number of flips (default: 20, max: 100)

**Response:**
```json
[
  {
    "id": 5,
    "item_id": 1234,
    "item_name": "Rune platebody",
    "quantity_total": 100,
    "quantity_remaining": 100,
    "buy_price": 38000,
    "sell_price": null,
    "buy_time": "2026-02-05T12:00:00",
    "sell_time": "2026-02-05T13:00:00",
    "profit": null,
    "roi": null,
    "status": "cancelled",
    "cancel_reason": "Price crashed to 35k",
    "notes": null
  }
]
```

---

### Get Flip Details

**GET** `/api/portfolio/flips/{flip_id}`

Get complete flip history including all transactions.

**Response:**
```json
{
  "flip": {
    "id": 1,
    "item_id": 534,
    "item_name": "Dragon bones",
    "quantity_total": 10000,
    "quantity_remaining": 0,
    "buy_price": 2498,
    "sell_price": 2665,
    "buy_time": "2026-02-05T10:00:00",
    "sell_time": "2026-02-05T16:00:00",
    "profit": 1052000,
    "roi": 4.21,
    "status": "completed",
    "cancel_reason": null,
    "notes": null
  },
  "transactions": [
    {
      "id": 1,
      "flip_id": 1,
      "transaction_type": "buy",
      "quantity": 3000,
      "price": 2500,
      "timestamp": "2026-02-05T10:00:00",
      "notes": null
    },
    {
      "id": 2,
      "flip_id": 1,
      "transaction_type": "buy",
      "quantity": 4000,
      "price": 2480,
      "timestamp": "2026-02-05T10:30:00",
      "notes": "Second batch"
    },
    {
      "id": 3,
      "flip_id": 1,
      "transaction_type": "sell",
      "quantity": 6000,
      "price": 2650,
      "timestamp": "2026-02-05T14:00:00",
      "notes": null
    },
    {
      "id": 4,
      "flip_id": 1,
      "transaction_type": "sell",
      "quantity": 4000,
      "price": 2670,
      "timestamp": "2026-02-05T16:00:00",
      "notes": null
    }
  ]
}
```

---

### Get Portfolio Summary

**GET** `/api/portfolio/summary`

Get comprehensive portfolio statistics.

**Response:**
```json
{
  "total_flips": 45,
  "winning_flips": 38,
  "losing_flips": 7,
  "total_profit": 15234567,
  "avg_roi": 8.32,
  "best_flip": 2500000,
  "worst_flip": -450000,
  "total_invested": 183250000,
  "pending_flips": 3,
  "pending_capital": 34975000,
  "cancelled_flips": 5
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": {
    "error": "Cannot sell flip with status 'completed'"
  }
}
```

### 404 Not Found
```json
{
  "detail": "Item not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database connection failed"
}
```

---

## Common Workflows

### 1. First-Time Setup

```bash
# Sync items
curl -X POST http://localhost:8000/api/items/sync

# Check stats
curl http://localhost:8000/api/flips/stats
```

### 2. Find Flips

```bash
# Find safe, profitable flips
curl "http://localhost:8000/api/flips/search?min_profit=100&min_volume=5000&cash=10000000&limit=10"
```

### 3. Log a Flip

```bash
# Buy
curl -X POST http://localhost:8000/api/portfolio/buy \
  -H "Content-Type: application/json" \
  -d '{"item_name": "dragon bones", "quantity": 10000, "price": 2500}'

# Sell
curl -X POST http://localhost:8000/api/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{"flip_id": 1, "price": 2650}'

# Check summary
curl http://localhost:8000/api/portfolio/summary
```

### 4. Partial Flips

```bash
# Initial buy
curl -X POST http://localhost:8000/api/portfolio/buy \
  -H "Content-Type: application/json" \
  -d '{"item_name": "dragon bones", "quantity": 3000, "price": 2500}'

# Add more
curl -X POST http://localhost:8000/api/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"flip_id": 1, "quantity": 4000, "price": 2480}'

# Partial sell
curl -X POST http://localhost:8000/api/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{"flip_id": 1, "price": 2650, "quantity": 5000}'

# View details
curl http://localhost:8000/api/portfolio/flips/1
```

---

## Rate Limiting

No rate limiting currently implemented. Consider implementing if exposing publicly.

## Authentication

No authentication currently implemented. Add JWT or API keys for production use.
