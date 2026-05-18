# OSRS Flipping Calculator

A complete full-stack application (FastAPI backend + React frontend) for finding profitable Old School RuneScape Grand Exchange flips and tracking your portfolio.

## 🌟 Features

- **Advanced Flip Search:** Find flips with filters for profit, ROI, volume, cash stack constraints, and members/F2P items.
- **Portfolio Tracking:** Log purchases, track partial fills/sales, and calculate weighted average buy prices.
- **Price History Charts:** Interactive line charts showing 5m, 1h, and 6h historical price trends.
- **Data Quality & Manipulation Detection:** Statistical outlier detection filters out manipulated, stale, or unreliable price data using a 5-factor scoring system.
- **Item Scoring System:** Ranks flipping opportunities using a 0-100 score balancing ROI, volume, margin health, and momentum.
- **Volume Indicators:** Instant visual indicators (🟢 High to 🔴 Low) of trading activity based on hourly volume.

## 🚀 Quick Start

Get up and running in 3 steps!

### Prerequisites
- **Python 3.8+** (for the backend API)
- **Node.js 18+** (for the frontend)

### Step 1: Start Backend API

```bash
cd flipping-calculator-api
pip install -r requirements.txt
./run.sh
```
*Keep this terminal open. API runs at `http://localhost:8000`*

**First-time setup:** Sync items from the OSRS Wiki (takes ~1-2 min)
```bash
curl -X POST http://localhost:8000/api/items/sync
```

### Step 2: Start Frontend

In a new terminal:
```bash
cd flipping-calculator-frontend
npm install
npm run dev
```
*Keep this terminal open. Frontend runs at `http://localhost:3000`*

### Step 3: Open Browser

Go to: `http://localhost:3000`

You're done! 🎉 You can now start searching for flips, adding them to your portfolio, and tracking your history.

## 🛠️ Technology Stack

**Backend:**
- **FastAPI** + **Uvicorn** — ASGI web framework
- **Pydantic** — Request/response validation
- **Requests** — HTTP client for OSRS Wiki API
- **PostgreSQL / SQLite** — Database (default is SQLite, easily migrated to Postgres)

**Frontend:**
- **React 18** with Vite
- **TanStack Query v5** — Server state, caching, retry logic
- **TanStack Table v8** — Sortable data tables
- **Zustand** — Client state (filters, active view)
- **Recharts** — Price history charts
- **Tailwind CSS** — Utility-first styling with custom OSRS color theme

## 📚 Documentation

Detailed documentation has been consolidated into the following guides:

- **[Developer Guide](DEVELOPER_GUIDE.md):** Architecture, detailed setup, start scripts, production deployment via Docker, database migration, and rate limits.
- **[API & Scoring Reference](API_AND_SCORING_REFERENCE.md):** Complete REST API endpoint documentation, the Flip Scoring Algorithm, and the Data Quality Scoring System.
