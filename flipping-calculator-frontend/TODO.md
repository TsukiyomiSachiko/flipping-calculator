# OSRS Flipping Calculator - TODO List

## 📅 Recent Session (Feb 14, 2026)
**Completed:**
- ✅ Production Setup Guide - Docker-based deployment with Nginx reverse proxy and PostgreSQL
- ✅ CSV Export/Import - Backup and restore portfolio/history data with transaction synthesis
- ✅ Item Conversions System - Full implementation (Backend + UI) for processing profitability
- ✅ Advanced Statistics - Enhanced StatsView with daily profit trends and category breakdowns
- ✅ Polling & Sync Controls - UI controls for real-time price polling and manual Wiki sync
- ✅ Data Quality Dashboard - Integration of 5-factor scoring into the UI for manipulation detection

**Files Modified:**
- Backend: `portfolio_service.py`, `routes/portfolio.py`, `database.py`, `docker-compose.yml`, `PRODUCTION_GUIDE.md`
- Frontend: `api.js`, `PortfolioView.jsx`, `Dockerfile`, `nginx.conf`
- Docs: `TODO.md`

## 🔥 High Priority Features

### [x] Price History Charts ✅
- [x] Fetch timeseries data from OSRS Wiki API
- [x] Create chart component (use recharts library)
- [x] Show buy/sell price trends over time
- [x] Add timestep selector (5m, 1h, 6h)
- [x] Display as modal on item name click (all pages)

### [x] Comprehensive Regression Testing ✅
- [x] Implement robust test suite for all core API endpoints
- [x] Set up dedicated PostgreSQL test database
- [x] Clone production data for realistic integration testing
- [x] Automated table cleanup between test runs
- [x] Resolve all deprecation warnings for clean test output

### [x] Permanent Price History Storage ✅
- [x] Create price_history table in database
- [x] Implement background task to poll /latest and /5m endpoints
- [x] Save timestamped price snapshots (high/low/volume)
- [x] Build own timeseries from accumulated data
- [x] Replace Wiki's /timeseries dependency with local data
- [x] Add data retention policy (e.g., keep 30 days)
- [x] Optimize storage (avoid duplicate timestamps)

### [x] Profit Projections ✅
- [x] Fetch current market prices for pending flips
- [x] Calculate "if sold now" profit for each pending flip
- [x] Show projected profit vs actual partial profit
- [x] Add "Sell at current price" quick action button
- [x] Display total projected profit on portfolio summary

### [x] Quick Flip Suggestions ✅
- [x] Create preset filter templates
  - [x] "Top 5 under 1M"
  - [x] "Best high-volume flips"
  - [x] "Quick flips (high ROI, low volume)"
  - [x] "Safe flips (stable prices)"
  - [x] Bonus: "Limit Grinders", "Best Score", "Trending"
- [x] Add quick-select buttons to flip search page
- [x] Save custom filter presets (via preset system)

### [ ] Long Term Flip Support
- [ ] **Concept:** Track long-term investments (holding items for weeks/months) distinct from active flipping.
- [ ] **Features:**
  - Separate "Investment" view or tag in Portfolio.
  - Performance tracking against market index (if available) or general inflation.
  - "Days Held" metric and annualized ROI calculation.
  - Alerts for significant price movements over long periods.
  - Option to hide from daily active flip summary to avoid skewing daily stats.

### [x] Item Conversions System (Major Feature) ✅
- [x] **Phase 1: Foundation (Backend)**
  - [x] Create `item_conversions` table to store recipe data.
  - [x] Create `user_conversions` table (if needed for tracking).
  - [x] Build API to calculate "Profit per Hour".
- [x] **Phase 2: Management UI**
  - [x] Build "Conversions Dashboard" showing live profitability.
- [x] **Phase 3: Integration**
  - [x] Integrate with Portfolio for cash reservation.
- [x] **Phase 4: Automation**
  - [x] Manual population and Wiki sync logic implemented.

### [ ] Notifications/Alerts
- [ ] Add target price field to pending flips
- [ ] Check current prices against targets periodically
- [ ] Browser notification when target hit
- [ ] In-app notification badge/list
- [ ] Option to enable/disable alerts per flip

### [x] Manipulated Price Data Detection ✅
- [x] Statistical outlier detection (Z-score analysis)
- [x] Minimum absolute price threshold
- [x] Spread sanity checks
- [x] Volume-to-price-change correlation
- [x] Historical stability scoring
- [x] Created comprehensive DataQualityService with 5-factor scoring (0-100)
- [x] Frontend displays quality scores and warning flags
- [x] Full documentation in DATA_QUALITY.md

### [ ] Rebalance Trending Algorithm - Volume Weight Too Low
- [ ] **Problem:** Low-volume items rank too high despite terrible hourly profit potential
- [ ] **Root cause analysis:**
  - Current volume weight in scoring is insufficient
  - Need to penalize items where `(profit_per_item × volume_per_hour) < threshold`
- [ ] **Solution approaches:**
  - [ ] Increase volume weight in base scoring formula
  - [ ] Add "hourly profit potential" metric: `(profit_per_item × min(volume, limit)) / hours_to_limit`
- [ ] **Priority:** High - directly impacts flip quality and user experience

### [x] Fix Limit Grinders Quick Preset ✅
- [x] Implemented "grindable" filter - volume must be >= 25% of GE limit
- [x] Added `requireGrindable` filter parameter
- [x] Backend checks: `volume >= (ge_limit * 0.25)`
- [x] Sorts by limit profit to show most profitable grindable items first

### [x] Buy Trend Analysis (Fill Rate Monitoring) ✅
- [x] **Solution: Track fill rate and recommend actions**
  - [x] Database schema changes: `buy_offer_started_at`, `last_buy_at`, `sell_offer_started_at`, `last_sell_at`
  - [x] Created `fill_rate_service.py` with comprehensive metrics calculation
  - [x] Recommendation logic for BUY/SELL offers (Keep/Monitor/Cancel)
  - [x] Display on portfolio card with status badges
- [x] **Benefits:** Data-driven decision making on when to abandon slow offers

### [x] Log Partial Buys (Log Additional Purchase) ✅
- [x] Add "Log Buy" button/action on pending flip cards
- [x] Opens modal to add additional quantity at specified price
- [x] Backend calculates weighted average buy price automatically

### [x] Intended Sell Price Capture ✅
- [x] Capture sell price from flip table at buy time
- [x] Store as intended_sell_price in database
- [x] Display "Target Sell Price" on portfolio cards

### [x] Adjust Intended Quantity (Free Reserved Cash) ✅
- [x] "Adjust Target" button on portfolio cards
- [x] Sets intended_quantity to match quantity_total
- [x] Frees up reserved cash for cancelled portion

### [x] Liquidity Timing Analytics ✅
- [x] Track fill patterns from price history data (hourly heatmap)
- [x] Identify "best trading times" for each item
- [x] Display in item detail modal: Best 5 trading hours (GMT)

---

## 💡 Medium Priority Features

### [x] Margin Tracking Over Time ✅
- [x] Track margin snapshots (profit margin % over time)
- [x] Chart showing how margins change throughout day/week

### [x] Export to CSV/Excel ✅
- [x] Export completed and pending flips to CSV
- [x] Import CSV back to database with transaction synthesis
- [x] "Export" and "Import" buttons added to Portfolio page

### [x] Edit Buy Price on Pending Flips ✅
- [x] Add functionality to update buy_price without cancelling flip
- [x] Automatically adjust reserved cash based on price difference
- [x] Service method `update_buy_price` and PATCH route implemented

### [ ] Flip Notes & Tags
- [ ] Add notes field to flips (editable)
- [ ] Create strategy tags (Quick flip, Long-term, Merch)
- [ ] Filter/search by tags

### [ ] Multi-Item Comparison
- [ ] Select 2-3 items from search results
- [ ] Side-by-side comparison view

### [ ] Quick Buy from Portfolio Page
- [ ] Add "Log a Buy" button to portfolio page header
- [ ] Selecting item opens BuyModal with pre-filled item data

---

## 🎯 Polish & UX Improvements

### [ ] Mobile Responsiveness
- [ ] Test all pages on mobile devices
- [ ] Improve table layouts for small screens

### [ ] Keyboard Shortcuts
- [ ] Define shortcut mapping (Ctrl+B: Quick buy, Ctrl+F: Search, etc.)

### [ ] Tutorial/Onboarding
- [ ] Explain GE limits, 2% tax, ROI, etc.

---

## 🐛 Bug Fixes / Tech Debt

### [x] Remove Debug Fields ✅
- [x] Remove `debug_pending_flips` from API response
- [x] Clean up logging and console output

### [x] Optimize API Calls ✅
- [x] Review React Query cache times
- [x] Reduce unnecessary re-fetches

### [x] Error Handling ✅
- [x] Better error messages for API failures
- [x] Retry logic for failed requests

### [x] Fix Margin Chart & Liquidity API 500 Errors ✅
- [x] Investigate 500 errors when opening item detail modal
- [x] Verify database queries in margin/liquidity endpoints

### [x] Fix Pending Flips Count on Portfolio Summary ✅
- [x] Include `partially_completed` status in active flips count

### [x] Replace Browser Alerts with In-App Toast Notifications ✅
- [x] Created Toast.jsx component
- [x] Replaced browser `alert()` calls with polish notifications

### [x] Fix ROI In-Progress Calculation on Partially Completed Flips ✅
- [x] Calculate ROI including projected profit on remaining inventory

### [ ] Monitor Recovery Analysis Accuracy
- [ ] Track predictability of hold/sell recommendations over time

### [ ] Migrate to Local Timeseries Data
- [x] Seeding complete: All ~3000 items timeseries data seeded ✅
- [ ] Current status: Using hybrid approach (local data when available, Wiki API fallback)
- [ ] Next step (optional): Migrate to 100% local data by updating services

### [x] Move to PostgreSQL ✅
- [x] Migrate from SQLite to PostgreSQL for better concurrency
- [x] All concurrent access issues resolved

### [x] Critical Cash Flow Bugs ✅
- [x] Fixed double cash deduction in add_to_flip
- [x] Fixed cancel refunding inventory items
- [x] Fixed partial sells not setting sell_price
- [x] Fixed status checks being too restrictive

### [x] UX Improvements ✅
- [x] Inventory warning on cancel
- [x] Confirmation modal for Adjust Target
- [x] Default price in AddBuyModal

### [ ] Comprehensive Codebase Refactoring
- [ ] Consolidate duplicate price fetching and common calculation patterns
- [ ] Standardize error handling and response formats

---

## 🎨 Nice to Have

### [ ] Authentication & Login System
- [ ] Simple password-protected access for production deployment

### [x] Statistics Dashboard ✅
- [x] Implementation: StatsView page with comprehensive analytics

### [ ] Flip Calendar
- [ ] Calendar view of all flips to track trading patterns

### [ ] Advanced Filters
- [ ] Filter by item category, exclude specific items, etc.

### [ ] Portfolio Analytics
- [ ] Visual breakdown of investments and profit timelines

---

## 📝 Documentation

### [ ] User Guide
- [ ] Best practices for flipping and understanding metrics

### [x] API Documentation ✅
- [x] Complete API endpoint reference and integration guide
- [x] Production deployment guide (Docker/PostgreSQL) implemented
