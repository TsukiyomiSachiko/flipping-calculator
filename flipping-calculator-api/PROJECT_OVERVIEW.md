# OSRS Flipping Calculator API - Project Overview

## 🎯 What You Got

A complete FastAPI-based REST API for OSRS flipping with:
- ✅ Flip discovery with advanced filtering
- ✅ Portfolio tracking with partial flip support
- ✅ Volume data from 1-hour rolling averages
- ✅ Comprehensive documentation
- ✅ Clean, maintainable architecture

## 📁 Project Structure

```
osrs-api/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── models/
│   │   └── schemas.py               # Pydantic models for request/response
│   ├── routes/
│   │   ├── items.py                 # Item endpoints (sync, search, get)
│   │   ├── flips.py                 # Flip search endpoints
│   │   └── portfolio.py             # Portfolio tracking endpoints
│   ├── services/
│   │   ├── item_service.py          # Item business logic
│   │   ├── flip_service.py          # Flip discovery logic
│   │   └── portfolio_service.py     # Portfolio tracking logic
│   └── utils/
│       ├── database.py              # Database utilities & setup
│       └── api_client.py            # OSRS Wiki API client & caching
├── data/                            # Created on first run
│   ├── osrs_flipping.db            # SQLite database
│   └── cache/                      # API response cache
├── README.md                        # Getting started guide
├── API_DOCS.md                      # Complete API reference
├── MIGRATION_GUIDE.md               # CLI → API migration guide
├── requirements.txt                 # Python dependencies
├── run.sh                          # Startup script
└── .gitignore                      # Git ignore rules
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd osrs-api
pip install -r requirements.txt
```

### 2. Start the Server
```bash
./run.sh
```
Or manually:
```bash
uvicorn app.main:app --reload
```

### 3. Access the API
- **API:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 4. First-Time Setup
```bash
curl -X POST http://localhost:8000/api/items/sync
```

## 📚 Documentation Files

### README.md
- Quick start guide
- Installation instructions
- Basic usage examples
- Project structure overview

### API_DOCS.md
- Complete endpoint reference
- Request/response examples
- Query parameter details
- Error responses
- Common workflows

### MIGRATION_GUIDE.md
- CLI → API command mapping
- Database migration instructions
- Integration examples
- Comparison of CLI vs API

## 🔌 Main Endpoints

### Items
- `POST /api/items/sync` - Sync items from OSRS Wiki
- `GET /api/items` - Get all items
- `GET /api/items/search?q=dragon` - Search items
- `GET /api/items/{item_id}` - Get single item

### Flips
- `GET /api/flips/search` - Find profitable flips
- `POST /api/flips/search` - Find flips (JSON body)
- `GET /api/flips/stats` - Get flip statistics

### Portfolio
- `POST /api/portfolio/buy` - Log purchase
- `POST /api/portfolio/add` - Add to flip
- `POST /api/portfolio/sell` - Log sale
- `POST /api/portfolio/cancel` - Cancel flip
- `GET /api/portfolio/pending` - Get pending flips
- `GET /api/portfolio/completed` - Get completed flips
- `GET /api/portfolio/cancelled` - Get cancelled flips
- `GET /api/portfolio/flips/{id}` - Get flip details
- `GET /api/portfolio/summary` - Get portfolio stats

## 🏗️ Architecture Highlights

### Clean Separation of Concerns
- **Routes:** Handle HTTP requests/responses
- **Services:** Business logic and data processing
- **Models:** Data validation with Pydantic
- **Utils:** Database and API client utilities

### Service Layer Pattern
Each service handles a specific domain:
- `ItemService` - Item data and calculations
- `FlipService` - Flip discovery and filtering
- `PortfolioService` - Portfolio tracking

### Benefits
- ✅ Easy to test
- ✅ Easy to extend
- ✅ Clear responsibilities
- ✅ Maintainable code

## 🔄 Data Flow

### Flip Discovery
```
Client Request
    ↓
routes/flips.py (validate params)
    ↓
flip_service.py (business logic)
    ↓
├─ api_client.py (fetch prices/volume)
├─ database.py (get items)
└─ item_service.py (calculate profit)
    ↓
Response to client
```

### Portfolio Tracking
```
Client Request
    ↓
routes/portfolio.py (validate)
    ↓
portfolio_service.py (logic)
    ↓
database.py (read/write)
    ↓
Response to client
```

## 💾 Database

### SQLite Schema
- `items` - OSRS items (~3,000)
- `user_flips` - Your flip history
- `flip_transactions` - Buy/sell transaction log

### Features
- Weighted average buy price
- Partial flip tracking
- Transaction history
- Status management (pending/completed/cancelled)

### Compatible with CLI
Same schema as the CLI version - you can migrate your existing database!

## 🎨 Key Features

### 1. Advanced Flip Search
- Profit thresholds
- ROI ranges (default 25% cap)
- Volume filtering (1h rolling)
- Capital constraints
- Members/F2P filtering
- Multiple sort options

### 2. Partial Flip Support
- Buy in multiple trades (weighted average)
- Sell in multiple trades (cumulative profit)
- Complete transaction history

### 3. Volume Indicators
- 🟢 HIGH (50k+) - Very active
- 🟡 MED (5k-50k) - Moderate
- 🔴 LOW (<5k) - Slow
- ⚪ N/A - No recent trades

### 4. Smart Caching
- Item mapping: 24 hours
- Latest prices: 5 minutes
- Volume data: 15 minutes

## 🛠️ Technology Stack

- **FastAPI** - Modern, fast web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **SQLite** - Database
- **Requests** - HTTP client for OSRS Wiki API

## 📊 Example Usage

### Find Flips (curl)
```bash
curl "http://localhost:8000/api/flips/search?min_profit=100&min_volume=5000&cash=10000000"
```

### Find Flips (Python)
```python
import requests

response = requests.get('http://localhost:8000/api/flips/search', params={
    'min_profit': 100,
    'min_volume': 5000,
    'cash': 10000000,
    'sort_by': 'profit',
    'limit': 10
})

flips = response.json()['flips']
for flip in flips:
    print(f"{flip['name']}: {flip['profit']:,} gp profit")
```

### Log a Flip (Python)
```python
import requests

# Buy
buy = requests.post('http://localhost:8000/api/portfolio/buy', json={
    'item_name': 'dragon bones',
    'quantity': 10000,
    'price': 2500
})

flip_id = buy.json()['flip_id']

# Sell
sell = requests.post('http://localhost:8000/api/portfolio/sell', json={
    'flip_id': flip_id,
    'price': 2650
})

print(sell.json()['message'])
# Output: "Flip completed! Total profit: 970,000 gp"
```

## 🔐 Security Notes

### Current State (Development)
- ❌ No authentication
- ❌ No rate limiting
- ❌ CORS open to all origins

### For Production
Consider adding:
- JWT authentication
- API key system
- Rate limiting (per user/IP)
- CORS restrictions
- Input sanitization (already have Pydantic validation)
- HTTPS

## 🚀 Next Steps

### Immediate
1. Start the API
2. Explore the docs at /docs
3. Try some endpoints

### Short Term
- Build a simple frontend (React/Vue)
- Create Discord bot integration
- Add more filtering options

### Long Term
- Real-time price updates (WebSocket)
- User accounts
- Price history tracking
- Flip recommendations (ML)
- Mobile app

## 💡 Why API vs CLI?

### API Advantages
- ✅ No terminal needed
- ✅ Integration ready
- ✅ Multiple clients
- ✅ Web/mobile friendly
- ✅ Better for automation
- ✅ Interactive documentation

### CLI Advantages
- ✅ Simple single-file operations
- ✅ No server needed
- ✅ Quick one-off commands

### Best of Both?
You can use both! They share the same database.

## 📝 Files You Need to Read

1. **README.md** - Start here
2. **API_DOCS.md** - Full endpoint reference
3. **MIGRATION_GUIDE.md** - If coming from CLI

## 🎯 What Makes This Good

### Clean Architecture
- Services handle business logic
- Routes handle HTTP
- Models handle validation
- Utils handle infrastructure

### Well Documented
- Inline docstrings
- OpenAPI/Swagger docs
- Comprehensive markdown guides
- Example code

### Production Ready
- Error handling
- Input validation
- Caching
- Database transactions

### Extensible
- Easy to add endpoints
- Easy to add features
- Easy to modify logic
- Easy to test

## 🐛 Troubleshooting

### Database locked
- SQLite doesn't handle concurrent writes well
- Don't run CLI and API simultaneously with write operations

### Port already in use
```bash
# Use different port
uvicorn app.main:app --port 3000
```

### Items not synced
```bash
curl -X POST http://localhost:8000/api/items/sync
```

## 📞 Support

- Check the docs at `/docs` when server is running
- Review API_DOCS.md for endpoint details
- Check MIGRATION_GUIDE.md for CLI comparison

## ✨ Summary

You now have a fully functional REST API for OSRS flipping that:
- Finds profitable flips with advanced filtering
- Tracks your portfolio with partial flip support
- Provides volume data for better decisions
- Has clean, maintainable code architecture
- Includes comprehensive documentation
- Is ready for integration with frontends/bots/tools

The API maintains all features from the CLI while being much more flexible and integration-friendly!

Happy flipping! 🎉
