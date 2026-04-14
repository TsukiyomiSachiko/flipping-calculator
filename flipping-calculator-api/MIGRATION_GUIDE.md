# Migration Guide: CLI to API

Guide for migrating from the CLI version to the FastAPI version.

## Database Compatibility

✅ **Good news:** The API uses the same database schema as the CLI!

Your existing `data/osrs_flipping.db` will work with the API without any changes.

## How to Migrate

### Option 1: Copy Your Database

1. Copy your existing database:
```bash
cp /path/to/old/flipping-calculator/data/osrs_flipping.db /path/to/osrs-api/data/
```

2. Start the API:
```bash
cd osrs-api
./run.sh
```

Your portfolio data will be immediately available via API!

### Option 2: Start Fresh

If you want to start with a clean database, just start the API and sync items:

```bash
./run.sh
```

Then in another terminal:
```bash
curl -X POST http://localhost:8000/api/items/sync
```

## CLI Command → API Endpoint Mapping

### Finding Flips

**CLI:**
```bash
python main.py --cash 10M --min-profit 100 --min-volume 5K
```

**API:**
```bash
curl "http://localhost:8000/api/flips/search?cash=10000000&min_profit=100&min_volume=5000"
```

---

### Portfolio Commands

#### Buy

**CLI:**
```bash
python portfolio.py buy "dragon bones" 10K 2.5K
```

**API:**
```bash
curl -X POST http://localhost:8000/api/portfolio/buy \
  -H "Content-Type: application/json" \
  -d '{"item_name": "dragon bones", "quantity": 10000, "price": 2500}'
```

#### Add to Flip

**CLI:**
```bash
python portfolio.py add 1 --quantity 5K --price 2.48K
```

**API:**
```bash
curl -X POST http://localhost:8000/api/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"flip_id": 1, "quantity": 5000, "price": 2480}'
```

#### Sell

**CLI:**
```bash
python portfolio.py sell 1 --price 2.65K --quantity 10K
```

**API:**
```bash
curl -X POST http://localhost:8000/api/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{"flip_id": 1, "price": 2650, "quantity": 10000}'
```

#### Sell with Total Price

**CLI:**
```bash
python portfolio.py sell 1 --price-total 26.5M --quantity 10K
```

**API:**
```bash
curl -X POST http://localhost:8000/api/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{"flip_id": 1, "price_total": 26500000, "quantity": 10000}'
```

#### View Pending

**CLI:**
```bash
python portfolio.py pending
```

**API:**
```bash
curl http://localhost:8000/api/portfolio/pending
```

#### View History

**CLI:**
```bash
python portfolio.py history --limit 50
```

**API:**
```bash
curl "http://localhost:8000/api/portfolio/completed?limit=50"
```

#### View Summary

**CLI:**
```bash
python portfolio.py summary
```

**API:**
```bash
curl http://localhost:8000/api/portfolio/summary
```

#### Cancel Flip

**CLI:**
```bash
python portfolio.py cancel 5 --reason "Price crashed"
```

**API:**
```bash
curl -X POST http://localhost:8000/api/portfolio/cancel \
  -H "Content-Type: application/json" \
  -d '{"flip_id": 5, "reason": "Price crashed"}'
```

#### View Details

**CLI:**
```bash
python portfolio.py details 1
```

**API:**
```bash
curl http://localhost:8000/api/portfolio/flips/1
```

---

## Advantages of API

### 1. No CLI Limitations
- No more typing long commands
- No terminal required
- Can be used from any programming language

### 2. Integration Ready
- Build web frontends
- Create mobile apps
- Integrate with Discord bots
- Connect to trading tools

### 3. Better for Automation
```python
import requests

# Find flips
response = requests.get('http://localhost:8000/api/flips/search', params={
    'min_profit': 100,
    'min_volume': 5000,
    'cash': 10000000,
    'limit': 10
})

flips = response.json()['flips']

# Auto-log buys
for flip in flips[:3]:
    requests.post('http://localhost:8000/api/portfolio/buy', json={
        'item_name': flip['name'],
        'quantity': flip['ge_limit'],
        'price': flip['buy_price']
    })
```

### 4. Interactive Documentation
- Browse API at `http://localhost:8000/docs`
- Try endpoints directly in browser
- See request/response schemas

### 5. Multiple Clients
- Use from multiple machines
- Share data across devices
- Concurrent access (with proper setup)

---

## What Stays the Same

- ✅ Database format (exact same)
- ✅ All features (buy, sell, add, cancel, etc.)
- ✅ GE tax calculation (2%)
- ✅ ROI calculations
- ✅ Volume indicators
- ✅ Partial flip support
- ✅ Price aggregation (/latest + /1h)

---

## What's Different

### Better Structure
- Organized into services, routes, models
- Easier to maintain and extend
- Better separation of concerns

### JSON Responses
- Structured data instead of formatted tables
- Easy to parse and process
- Better for automation

### HTTP-Based
- Access from anywhere
- Standard REST API
- Works with any HTTP client

---

## Quick Start Checklist

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ (Optional) Copy old database to `data/` folder
3. ✅ Start API: `./run.sh` or `uvicorn app.main:app --reload`
4. ✅ Open docs: http://localhost:8000/docs
5. ✅ (If new) Sync items: `POST /api/items/sync`
6. ✅ Start using API endpoints!

---

## Need Help?

- Check `README.md` for getting started guide
- Check `API_DOCS.md` for complete endpoint reference
- Visit http://localhost:8000/docs for interactive docs
- Database schema is unchanged, so your data is safe

---

## Can I Use Both?

Yes! The CLI and API can share the same database.

Just point both to the same `data/osrs_flipping.db` file.

**Note:** Don't run operations from both simultaneously (SQLite doesn't handle concurrent writes well).

---

## Next Steps

1. Start the API
2. Try a few endpoints with curl or in the browser docs
3. Consider building a simple frontend (React, Vue, etc.)
4. Or integrate with your existing tools/workflows

The API gives you complete flexibility! 🚀
