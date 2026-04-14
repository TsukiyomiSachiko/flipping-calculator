# OSRS Flipping Calculator API

FastAPI backend for finding profitable OSRS Grand Exchange flips and tracking your portfolio.

## Quick Start

```bash
./run.sh
```

This creates a virtual environment, installs dependencies, and starts the server at `http://localhost:8000`.

### Mobile Access (Windows)

To expose the backend to your local network (e.g. for phone access), run as Administrator in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File ".\start-backend.ps1"
```

This adds a firewall rule for port 8000, starts the server, and cleans up the rule on Ctrl+C.

First-time setup — sync items from the OSRS Wiki:
```bash
curl -X POST http://localhost:8000/api/items/sync
```

Interactive API docs: `http://localhost:8000/docs`

## Architecture

```
app/
├── main.py                  # FastAPI app, CORS, lifespan, router registration
├── models/
│   └── schemas.py           # Pydantic request/response models
├── routes/
│   ├── items.py             # Item CRUD + enriched price lookup
│   ├── flips.py             # Flip discovery with filtering
│   ├── portfolio.py         # Portfolio management (buy/sell/cancel)
│   └── price_history.py     # OSRS Wiki timeseries proxy
├── services/
│   ├── item_service.py      # Item DB ops, profit calculation, live price enrichment
│   ├── flip_service.py      # Merges DB items with live prices, applies filters
│   └── portfolio_service.py # Flip lifecycle, partial sells, summary stats
└── utils/
    ├── database.py          # SQLite setup + connection context manager
    └── api_client.py        # OSRS Wiki API client with file-based caching
```

### Data Flow

1. **Item sync** fetches ~3,000 items from the OSRS Wiki mapping endpoint → SQLite
2. **Flip search** merges DB items with live `/latest` prices and `/1h` volume data, then filters and sorts
3. **Portfolio ops** are pure SQLite — no external API calls
4. **Price history** proxies the Wiki timeseries endpoint with file-based caching

### External API

All market data comes from the [OSRS Wiki Prices API](https://prices.runescape.wiki/api/v1/osrs):

| Endpoint | Cache TTL | Used For |
|----------|-----------|----------|
| `/mapping` | 24h | Item database sync |
| `/latest` | 5min | Current buy/sell prices |
| `/1h` | 15min | Hourly trade volume |
| `/timeseries` | 5min–2h | Price history charts |

### Database

SQLite at `data/osrs_flipping.db` with three tables:

- **items** — static item data (id, name, members, ge_limit, alch values)
- **user_flips** — flip lifecycle with statuses:
  - `pending` — active flip, waiting for more buys/sells
  - `partially_completed` — profit realized but didn't reach intended quantity target
  - `completed` — reached intended quantity and sold everything
  - `cancelled` — abandoned before any sales
- **flip_transactions** — individual buy/sell transaction log

**Intended Quantity Tracking:** Flips can specify an `intended_quantity` target. When selling everything before reaching this target, the flip is marked `partially_completed` (not completed). Clicking "Cancel" on a partially_completed flip promotes it to `completed` status, ensuring profitable partial flips appear in history.

### GE Tax

The Grand Exchange applies a 2% tax on sell prices above 50 gp. This is calculated server-side in `ItemService.calculate_profit()` and `PortfolioService.log_sell()`. The frontend never calculates tax.

## API Reference

### Items

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/items/sync` | Sync items from OSRS Wiki (first-time setup) |
| `GET` | `/api/items` | List all items |
| `GET` | `/api/items/search?q=dragon` | Search items by name |
| `GET` | `/api/items/{id}` | Get item by ID (DB data only) |
| `GET` | `/api/items/{id}/prices?cash=10000000` | Get item enriched with live prices, profit, ROI, volume |
| `POST` | `/api/items/clear-cache` | Clear all API caches |

### Flips

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/flips/search` | Find profitable flips with query param filters |
| `POST` | `/api/flips/search` | Find profitable flips with JSON body |
| `GET` | `/api/flips/stats` | Item/price/volume counts |

**Search parameters:** `min_profit`, `min_roi`, `max_roi`, `min_limit_profit`, `min_volume`, `high_volume_only`, `cash`, `members_only`, `f2p_only`, `sort_by` (profit/roi/limit/volume), `limit`

### Portfolio

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/portfolio/buy` | Log a purchase |
| `POST` | `/api/portfolio/add` | Add quantity to existing flip (weighted avg) |
| `POST` | `/api/portfolio/sell` | Sell (full or partial, per-item or total price) |
| `POST` | `/api/portfolio/cancel` | Cancel a pending flip |
| `GET` | `/api/portfolio/pending` | List pending flips |
| `GET` | `/api/portfolio/completed` | List completed flips |
| `GET` | `/api/portfolio/cancelled` | List cancelled flips |
| `GET` | `/api/portfolio/flips/{id}` | Flip detail with transaction history |
| `GET` | `/api/portfolio/summary` | Portfolio stats (profit, ROI, win rate) |

### Price History

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/items/{id}/price-history?timestep=5m` | Timeseries data (5m, 1h, 6h) |

## Examples

```bash
# Find flips with 10M cash, minimum 5% ROI
curl "http://localhost:8000/api/flips/search?cash=10000000&min_roi=5&sort_by=roi&limit=10"

# Look up a specific item with live prices
curl "http://localhost:8000/api/items/13190/prices?cash=50000000"

# Log a buy
curl -X POST http://localhost:8000/api/portfolio/buy \
  -H "Content-Type: application/json" \
  -d '{"item_name": "dragon bones", "quantity": 10000, "price": 2500}'

# Sell using total price
curl -X POST http://localhost:8000/api/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{"flip_id": 1, "price_total": 26500000, "quantity": 10000}'

# Portfolio summary
curl http://localhost:8000/api/portfolio/summary
```

## Configuration

| Setting | Location | Default |
|---------|----------|---------|
| Database | `data/osrs_flipping.db` | Auto-created |
| Cache | `data/cache/` | Auto-created |
| Port | `run.sh` / CLI | 8000 |
| CORS | `main.py` | Allow all origins |
| User-Agent | `api_client.py` | `OSRS Flipping Calculator API/2.0` |

## Development

```bash
# Development with auto-reload (default in run.sh)
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Dependencies

- **FastAPI** + **Uvicorn** — ASGI web framework
- **Pydantic** — request/response validation
- **Requests** — OSRS Wiki API client
- **SQLite** — embedded database (no external DB required)