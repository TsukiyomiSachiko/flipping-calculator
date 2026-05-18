# Developer Guide

Welcome to the Developer Guide for the OSRS Flipping Calculator. This document covers architecture, advanced setup, deployment, database management, and future development plans.

---

## 🏗️ Architecture & Data Flow

The project is split into a clean separation of a React SPA frontend and a FastAPI backend.

### Backend Architecture
```
flipping-calculator-api/
├── app/
│   ├── main.py                  # FastAPI app, CORS, lifespan, router registration
│   ├── models/                  # Pydantic request/response schemas
│   ├── routes/                  # HTTP Endpoints (items, flips, portfolio)
│   ├── services/                # Business logic (ItemService, FlipService, PortfolioService)
│   └── utils/                   # Database connection context and OSRS Wiki API client
├── data/                        # SQLite DB and file-based API cache
└── migrations/                  # Database migration scripts
```
- **Service Layer Pattern:** Routes handle HTTP, Services handle business logic, Models validate data, and Utils manage infrastructure.
- **Data Flow:** 
  1. **Item Sync:** Fetches item mappings from the OSRS Wiki API → SQLite DB.
  2. **Flip Search:** Merges DB items with live `/latest` prices and `/1h` volume data, applies filters/scoring, and sorts.
  3. **Portfolio Ops:** Pure database operations—no external API calls.
  4. **Price History:** Polls and caches the Wiki timeseries endpoint.

### Frontend Architecture
```
flipping-calculator-frontend/
├── src/
│   ├── App.jsx                  # Layout, view routing
│   ├── components/              # Reusable UI (Navigation, Tables, Modals, Charts)
│   ├── pages/                   # Main views (Flips, Portfolio, History, Stats)
│   ├── hooks/                   # TanStack Query hooks (useApi.js)
│   ├── services/                # Axios instance and API calls
│   └── stores/                  # Zustand client state (appStore.js)
```
- **Dumb Frontend:** All complex profit, ROI, tax, and volume calculations happen in the backend. The frontend focuses purely on presentation.
- **State Management:** Server state is managed by TanStack Query (with caching and retry logic), while minimal client state (filters, active tabs) is managed by Zustand.

---

## 🚀 Advanced Setup & Start Scripts

For development, you have multiple ways to run the servers.

### Backend Start Scripts (WSL & Windows)

**Option 1: PowerShell Script (Windows)**
Run `.\start-backend.ps1` as Administrator.
- Automatically handles WSL execution.
- Opens firewall rules for port 8000 (accessible on your local network).
- Auto-converts Windows paths to WSL paths.

**Option 2: Bash Script (WSL)**
Run `./start-backend.sh` natively in WSL.
- Manages the Python `venv` automatically.
- No Windows dependencies.

### Frontend Start Script (Windows)

Run `.\start-frontend.ps1` as Administrator.
- Uses `netsh` to port forward port `3000` from your host to the WSL instance.
- Automatically handles the API proxy pointing to the correct host.
- Perfect for testing on a mobile device on your local Wi-Fi.

---

## 💾 Database & Migration

### Schema & Format
The application uses SQLite (`data/osrs_flipping.db`) by default but supports PostgreSQL. 
The schema includes:
- `items`: Static item data.
- `user_flips`: Flip lifecycle (`pending`, `partially_completed`, `completed`, `cancelled`).
- `flip_transactions`: Granular buy/sell log.
- `user_settings`: Cash stack and configurations.

### Migrating from CLI to API
If you previously used the CLI version of this tool, the database schema is 100% compatible! Simply copy your existing `osrs_flipping.db` into the `data/` folder before starting the API server.

---

## 📊 Rate Limits & Initial Seeding

While the OSRS Wiki API has no explicit rate limits, we enforce a **5-second delay** during bulk data seeding to respect their resources.

### The `seed_price_history.py` Script
This script populates your local `price_history` table. It uses **Smart Skipping** to avoid redundant API calls for items that already have 45+ days of data.

**Best Practices:**
1. **Initial Seed (Default 6h Timestep):** 
   ```bash
   python seed_price_history.py --top 50
   ```
   This takes ~4 minutes and gathers 91 days of historical data for the top 50 most traded items.
2. **Background Polling:**
   Once seeded, the backend will automatically poll the Wiki every 5 minutes to keep prices up-to-date.
3. **Granular Data:**
   Use specific timesteps for deep dives into single items:
   ```bash
   python seed_price_history.py --items 2,4,6 --timestep 5m
   ```

---

## 🚢 Production Deployment (Docker)

To deploy the application to a production environment (like an Ubuntu VPS), use Docker Compose. This packages the frontend, backend, and PostgreSQL database.

1. **Clone & Configure:**
   Clone the repo and configure credentials in `docker-compose.yml`. Change `POSTGRES_PASSWORD` and the `DATABASE_URL`.
2. **Start the Stack:**
   ```bash
   docker compose up -d --build
   ```
3. **Initial Sync:**
   Populate the database via the running container:
   ```bash
   docker compose exec backend curl -X POST http://localhost:8000/api/items/sync
   ```
4. **Reverse Proxy (Nginx):**
   Set up Nginx to proxy traffic to the exposed frontend port (default `3080`) and use Certbot to provision SSL certificates.

---

## 📝 Roadmap / TODO

### Planned Features
- **Long Term Flip Support:** Separate "Investment" view for items held for weeks/months, tracking performance against a market index.
- **Notifications/Alerts:** Browser/in-app notifications when a pending flip hits a target price.
- **Rebalance Trending Algorithm:** Increase the weight of trading volume to penalize high-margin/low-volume trap items.
- **Flip Notes & Tags:** Editable tags (e.g., "Quick flip", "Merch") for better portfolio organization.
- **Multi-Item Comparison:** Side-by-side comparison view in the frontend.
- **Authentication:** Add a simple login system for the production deployment.

### Tech Debt
- Refactor the codebase to consolidate duplicate price fetching logic.
- Monitor the accuracy of the Recovery Analysis (hold/sell recommendations) over time.
- Complete migration to 100% local timeseries data instead of relying on the Wiki `/timeseries` fallback.
