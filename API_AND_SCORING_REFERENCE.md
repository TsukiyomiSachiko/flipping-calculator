# API and Scoring Reference

This document serves as the complete technical reference for the OSRS Flipping Calculator. It covers the logic used to rank items, the system used to filter out manipulated prices, and the full REST API documentation.

---

## 🧮 Flip Score Algorithm

The composite flip score is a single **0–100** metric that ranks Grand Exchange flipping opportunities. It balances six factors: profitability, scale, liquidity, capital risk, spread reliability, and price momentum.

### The Six Factors

| Factor | Weight | What it measures |
|:---|:---:|:---|
| **ROI** | 15% | Capital efficiency — how much profit per GP invested. Uses a logarithmic scale to reward good ROI without letting extreme outliers dominate. |
| **Profit at Limit** | 30% | Total GP potential per 4-hour GE cycle. This is the highest-weighted factor because absolute GP profit is the most important metric for wealth building. |
| **Volume** | 20% | Trade activity. Higher volume means your offers fill faster and data is more trustworthy. |
| **Cash Efficiency** | 5% | Portfolio risk. Penalizes flips that waste capital (using 1%) or concentrate too much risk (dumping 80% into one item). |
| **Spread Health** | 15% | Margin reliability. Very tight spreads risk being eaten by the 2% GE tax; suspiciously wide spreads indicate stale data. |
| **Momentum** | 15% | Price trajectory. Rewards items trending upward based on 1h average vs latest price. Clamped at ±2% to ignore wild swings. |

### Final Score Calculation
```python
# With momentum data:
score = (roi * 0.15) + (pal * 0.30) + (vol * 0.20) + (cash * 0.05) + (spread * 0.15) + (momentum * 0.15)

# Without momentum data (fallback):
score = (roi * 0.18) + (pal * 0.35) + (vol * 0.24) + (cash * 0.06) + (spread * 0.18)
```
*Note: Scores above 70 (🟢 Green) represent strong flips, while scores below 25 (⚪ Grey) represent weak flips.*

---

## 🛡️ Data Quality Scoring System

The data quality scoring system (0-100) detects manipulated, stale, or unreliable price data that could mislead traders. Items scoring below 50 are filtered out when the "Filter Suspicious Items" toggle is enabled in the frontend.

### The Five Checks

1. **Price Floor Check (20% weight)**
   - Items trading under 50gp are often manipulated.
   - Under 10gp = Score 0; 50gp+ = Score 100.
2. **Spread Sanity Check (25% weight)**
   - Impossible spreads (e.g., 1000%+) indicate stale data.
   - Spread >1000% = Score 0; Spread <200% = Score 100.
3. **Volume-to-Price Correlation (20% weight)**
   - Large price moves require proportional volume (e.g., >20% change needs 20k+ volume).
   - Volume < 20% of expected = Score 20; Volume >= expected = Score 100.
4. **Historical Volatility Z-Score (20% weight)**
   - Analyzes whether the current price change is an extreme outlier compared to the 7-day hourly standard deviation.
   - Z-score > 3.0 = Score 20; Z-score ≤ 1.5 = Score 100.
5. **Price Stability Check (15% weight)**
   - Sudden 10x spikes in 24 hours are usually manipulation.
   - Spike > 10x = Score 10; Spike < 2x = Score 100.

---

## 🔌 REST API Documentation

**Base URL:** `http://localhost:8000/api`

### Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/items/sync` | Sync all items from the OSRS Wiki to the local DB. |
| `GET`  | `/items` | List all items with pagination (`?limit=100&offset=0`). |
| `GET`  | `/items/search` | Search items by name (`?q=dragon`). |
| `GET`  | `/items/{id}` | Get item by ID. |
| `GET`  | `/items/{id}/prices` | Get item enriched with live prices, profit, ROI, and volume. |
| `POST` | `/items/clear-cache` | Clear all API response caches. |

### Flips

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/flips/search` | Find flips using query params (`min_profit`, `min_roi`, `cash`, etc.). |
| `POST` | `/flips/search` | Find flips using JSON body. |
| `GET`  | `/flips/stats` | Get statistics about available items and prices. |

### Portfolio

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/portfolio/buy` | Log a purchase transaction (`item_name`, `quantity`, `price`). |
| `POST` | `/portfolio/add` | Add quantity to an existing flip (calculates weighted average). |
| `POST` | `/portfolio/sell` | Log a sale (`flip_id`, `price`, `quantity`). Supports partial sells. |
| `POST` | `/portfolio/cancel`| Cancel a pending flip with an optional reason. |
| `GET`  | `/portfolio/pending` | Get all pending and partially completed flips. |
| `GET`  | `/portfolio/completed` | Get completed flips (most recent first). |
| `GET`  | `/portfolio/cancelled` | Get cancelled flips. |
| `GET`  | `/portfolio/flips/{id}` | Get complete flip history including all transactions. |
| `GET`  | `/portfolio/summary` | Get portfolio statistics (total invested, profit, ROI, win rate). |

### Price History

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/items/{id}/price-history` | Get proxy timeseries data (`?timestep=5m` or `1h` or `6h`). |

---

## 🔒 Authentication & Rate Limiting

The API currently implements JWT-based Authentication via the `/api/auth/register` and `/api/auth/token` endpoints. Standard Bearer tokens should be included in the `Authorization` header for protected endpoints like Portfolio management. 

No strict rate-limiting is implemented at the application level. If exposing the API publicly in production, it is highly recommended to configure an Nginx rate limit or a middleware solution.
