# OSRS Flipping Calculator Frontend

React SPA for finding profitable OSRS Grand Exchange flips and tracking your portfolio.

## Quick Start

```bash
npm install
npm run dev
```

Runs at `http://localhost:3000`. Requires the API server running at `http://localhost:8000` (requests are proxied via Vite).

### Mobile Access (Windows)

To expose the frontend to your local network (e.g. for phone access), run as Administrator in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File ".\start-frontend.ps1"
```

This sets up WSL port forwarding, adds a firewall rule, points the API proxy at your Windows host, and cleans everything up on Ctrl+C. Your phone can connect at the IP printed on startup.

**Note:** Requires the backend running separately (see backend README).

## Tech Stack

- **React 18** with Vite
- **TanStack Query v5** — server state, caching, retry logic
- **TanStack Table v8** — sortable data tables
- **Zustand** — client state (filters, active view)
- **Recharts** — price history charts
- **Tailwind CSS** — utility-first styling with OSRS color theme
- **Axios** — HTTP client with error interceptor

## Architecture

```
src/
├── main.jsx              # React root, QueryClient config (retry, staleTime)
├── App.jsx               # Layout, view routing, item sync
├── index.css             # Tailwind + custom component classes (btn, card, input)
├── components/
│   ├── Navigation.jsx        # Tab bar (Find Flips / Portfolio / History)
│   ├── FlipSearchFilters.jsx # Search filter form with K/M/B cash input
│   ├── FlipTable.jsx         # Results table with expandable detail rows
│   ├── ItemSearchBar.jsx     # Debounced item search with dropdown
│   ├── ItemDetailModal.jsx   # Item detail with live prices from API
│   ├── PriceHistoryModal.jsx # Recharts line chart (5m/1h/6h timesteps)
│   ├── BuyModal.jsx          # Log a buy with cost/profit preview
│   ├── ConfirmModal.jsx      # Generic confirmation dialog
│   └── PortfolioSummary.jsx  # 8-card stats grid
├── pages/
│   ├── FlipsView.jsx     # Item search + filters + flip table
│   ├── PortfolioView.jsx # Pending flips with sell/cancel forms
│   └── HistoryView.jsx   # Completed flips with sort options
├── hooks/
│   └── useApi.js         # TanStack Query hooks for all API endpoints
├── services/
│   └── api.js            # Axios instance, error interceptor, endpoint definitions
├── stores/
│   └── appStore.js       # Zustand store (filters, active view)
└── utils/
    └── formatters.js     # GP formatting (K/M/B), volume indicators, date utils
```

### Key Design Decisions

**Frontend stays dumb.** All profit, ROI, tax, and volume calculations happen in the API. The frontend only formats and displays data. This avoids duplicate logic and keeps the React code focused on presentation.

**Server state via TanStack Query.** Every API call goes through a query hook with sensible caching: 2 minutes default, 30 seconds for portfolio (invalidated on mutations), 5 minutes for price history.

**Client state via Zustand.** Only two things live in client state: the search filters and the active view tab. Everything else comes from the server.

**Error handling is layered.** Axios interceptor normalizes error messages, TanStack Query retries twice with exponential backoff, and components show error states.

## Features

### Find Flips
- Search with filters (profit, ROI, volume, cash stack, members/F2P)
- Results table with expandable rows showing full item details
- Item search bar with debounced dropdown for quick lookup
- Item detail modal with live prices from API
- Click any item name → price history chart
- One-click buy to portfolio

### Portfolio
- Pending flips with sell forms (per-item or total price mode)
- Intended quantity tracking for partial fills (prevents overbuying, shows progress)
- Partial sell support with running profit tracking
- Smart cancellation: partial flips with profit auto-promoted to completed
- Cancel flips with optional reason
- 8-card summary dashboard (investment, returns, profit, ROI, win rate)

### History
- Completed and partially completed flips (yellow badge for partial)
- Sorted by date, profit, or ROI
- Visual distinction: partial flips show yellow left border + "PARTIAL" badge
- Click item names → price history

### Price History
- Interactive line charts via Recharts
- Timestep selector (5 min / 1 hour / 6 hour)
- Current buy/sell/spread summary stats

## Custom Tailwind Theme

OSRS-themed colors defined in `tailwind.config.js`:

| Token | Color | Usage |
|-------|-------|-------|
| `osrs-gold` | `#FFA500` | Headers, profit, primary buttons |
| `osrs-green` | `#00FF00` | Sell prices, positive values |
| `osrs-red` | `#FF0000` | Buy prices, negative values |
| `osrs-blue` | `#0099FF` | Limit profit |

Component classes in `index.css`: `.btn`, `.btn-primary`, `.btn-secondary`, `.card`, `.input`

## Volume Indicators

| Emoji | Threshold | Label |
|-------|-----------|-------|
| 🟢 | ≥ 50,000 | High |
| 🟡 | ≥ 5,000 | Medium |
| 🔴 | ≥ 1,000 | Low |
| ⚪ | < 1,000 | Very Low |

## Configuration

| Setting | File | Default |
|---------|------|---------|
| Dev port | `vite.config.js` | 3000 |
| API proxy | `vite.config.js` | `http://localhost:8000` |
| Default cash | `appStore.js` | 10,000,000 gp |
| Query staleTime | `main.jsx` | 2 minutes |
| Query retries | `main.jsx` | 2 (exponential backoff) |

## Build

```bash
npm run build    # Production build → dist/
npm run preview  # Preview production build
```