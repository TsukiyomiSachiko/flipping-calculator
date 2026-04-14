# OSRS Wiki API - Seeding Time Guide

## 📊 Rate Limiting Strategy

**The OSRS Wiki API has no explicit rate limit**, but we use a conservative **5-second delay** to be respectful of their resources and avoid overwhelming the server.

You can adjust this with `--delay` if needed.

---

## ⏰ Understanding Timesteps

The OSRS Wiki API returns a **maximum of 365 datapoints** per request. The amount of historical data you get depends on your chosen timestep:

| Timestep | Coverage | Best For |
|----------|----------|----------|
| **5m** | 30 hours (365 × 5min) | Granular recent data, intraday analysis |
| **1h** | 15 days (365 × 1h) | Recent trends, short-term flipping |
| **6h** | 91 days (365 × 6h) | **Long-term trends, meets 45-day requirement** ✅ |

**Default:** The script uses **6h timestep** to ensure you get 45+ days of data for the smart skipping feature to work properly.

### Why 6h is Default

The smart skipping feature checks if items have **45+ days of data**. With:
- ✅ **6h timestep:** 91 days coverage - easily meets requirement
- ⚠️ **1h timestep:** 15 days coverage - won't meet requirement, will re-seed every time
- ❌ **5m timestep:** 30 hours coverage - nowhere near requirement

**Recommendation:** Use **6h for initial seeds**, then use **5m or 1h** for specific items where you want granular recent data.

---

## ⏱️ Seeding Time Estimates

With the **default 5-second delay** (recommended):

| Items | Time Required |
|-------|---------------|
| 10    | ~50 seconds   |
| 50    | ~4 minutes    |
| 100   | ~8 minutes    |
| 500   | ~42 minutes   |
| 1000  | ~1.4 hours    |
| 3000  | ~4.2 hours    |

**Note:** These are maximum times. The script automatically **skips items with 45+ days of data**, so re-runs are much faster!

---

## 🧠 Smart Skipping

The seeding script now **intelligently skips** items that already have sufficient data:

### What gets skipped?
✅ Items with 45+ days of historical data  
✅ Automatically detected on every run  
✅ Prevents redundant API calls  

### Example:
```bash
# First run - seeds 50 items (~4 minutes)
python seed_price_history.py --top 50

# Second run same day - skips all 50 items (instant!)
python seed_price_history.py --top 50
# Output: "✅ All items already have sufficient data!"

# Run after background polling has collected more data
python seed_price_history.py --top 100
# Output: "✓ Skipping 50 items that already have sufficient data"
#         "📝 Will seed 50 items that need data"
# Time: ~4 minutes (only seeds the 50 new items)
```

### Force Re-seeding
If you want to re-seed items anyway:
```bash
python seed_price_history.py --top 50 --force
```

---

## 🚀 Recommended Seeding Strategies

### Strategy 1: Top Traded Items (Best for Quick Start)
```bash
# Seed the most liquid items (default 6h timestep for 91 days coverage)
python seed_price_history.py --top 50
# Time: ~4 minutes
# Coverage: 90% of common flips, 91 days of history
```

**Why this works:**
- Top 50 items account for most trading volume
- Default 6h timestep provides 91 days of historical data
- Meets 45-day requirement for smart skipping
- Your app has data for popular flips immediately
- Background polling fills in the rest naturally
- Re-runs are instant (smart skipping)

### Strategy 2: Specific Item Categories
```bash
# Seed items you personally flip
python seed_price_history.py --items 2,4,6,554,1514,1516
# Time: ~30 seconds for 6 items
```

### Strategy 3: Comprehensive Initial Load
```bash
# Seed top 500 items (default 6h for long-term coverage)
python seed_price_history.py --top 500
# Time: ~42 minutes
# Coverage: Virtually all actively traded items, 91 days each
```

### Strategy 4: Complete Historical Database
```bash
# Seed ALL items (only if you need comprehensive data)
python seed_price_history.py --all
# Time: ~4 hours
# Coverage: Every item in OSRS, 91 days of history
```

---

## 🎯 Timestep Strategy Guide

### When to Use Each Timestep

**6h (Default - Recommended for bulk seeding):**
```bash
python seed_price_history.py --top 100
# ✅ 91 days of data
# ✅ Meets smart-skip requirement
# ✅ Good for long-term trend analysis
# ✅ Smaller database size
```

**1h (For medium-term analysis):**
```bash
python seed_price_history.py --items 2,4,6 --timestep 1h
# ⚠️ Only 15 days of data
# ⚠️ Won't meet 45-day smart-skip requirement
# ✅ Good for recent price movements
# ✅ More granular than 6h
```

**5m (For granular recent data):**
```bash
python seed_price_history.py --items 554 --timestep 5m
# ⚠️ Only 30 hours of data
# ⚠️ Won't meet 45-day smart-skip requirement
# ✅ Perfect for intraday flipping analysis
# ✅ See exact price movements
```

**Best Practice:**
1. Initial seed with 6h: `--top 100` (meets skip requirement)
2. Specific items with 5m/1h for granular data as needed
3. Background polling maintains current prices automatically

---

## 💡 Pro Tips

### Tip 1: Default 6h Timestep is Smart
```bash
# The default gives you the best balance
python seed_price_history.py --top 50
# ✅ 91 days of data (covers smart-skip requirement)
# ✅ Reasonable database size
# ✅ Good for trend analysis

# Only use denser timesteps when you need them
python seed_price_history.py --items 2 --timestep 5m
# For specific items where you want granular recent data
```

### Tip 2: Increase Delay for Extra Safety
```bash
# If being extra cautious about server load:
python seed_price_history.py --top 100 --delay 10
# Time: ~17 minutes (vs ~8 minutes with default)
```

### Tip 3: Leverage Smart Skipping
```bash
# Seed progressively larger sets without wasting time
python seed_price_history.py --top 50   # Day 1: ~4 min
python seed_price_history.py --top 100  # Day 2: ~4 min (skips first 50)
python seed_price_history.py --top 500  # Week 1: ~33 min (skips first 100)
```

### Tip 4: Monitor Progress
The script shows:
- How many items will be skipped (already have data)
- Progress percentage every 10 items
- Estimated time remaining
- Total time elapsed at completion

---

## 📈 Example Workflows

### For Development/Testing
```bash
# Quick seed for testing (default 6h = 91 days)
python seed_price_history.py --top 10
# Time: ~50 seconds
```

### For Production Launch
```bash
# Comprehensive initial seed (6h = 91 days coverage)
python seed_price_history.py --top 100
# Time: ~8 minutes first run, instant after

# Let background polling handle the rest
# (runs every 5 minutes automatically)
```

### For Intraday Analysis
```bash
# Get granular recent data for active flips
python seed_price_history.py --items 2,4,6,554 --timestep 5m
# Time: ~20 seconds
# Coverage: Last 30 hours at 5-minute intervals
```

### For Recent Trends
```bash
# Get 15 days of hourly data for specific items
python seed_price_history.py --items 1514,1516 --timestep 1h
# Time: ~10 seconds
# Coverage: Last 15 days at 1-hour intervals
```

---

## 🔄 Background Polling vs Manual Seeding

### Background Polling (Automatic)
- **Rate:** 1 request per 5 minutes
- **Coverage:** All items gradually
- **Time:** Builds over days/weeks
- **Best for:** Normal operation, staying current

### Manual Seeding (One-time)
- **Rate:** 1 request per 5 seconds (default)
- **Coverage:** Targeted items, backfills history
- **Time:** Minutes to hours
- **Best for:** Initial setup, filling gaps

**Optimal Strategy:** 
1. Seed top 50-100 items manually (~4-8 min)
2. Let background polling maintain current prices
3. Re-run seed script monthly to catch new popular items (smart skipping makes this instant)

---

## 🎯 New Features

### Smart Skipping (Automatic)
✅ Checks each item for 45+ days of data  
✅ Skips items that already have sufficient history  
✅ Shows how many items were skipped  
✅ Dramatically speeds up re-runs  

### Force Mode
```bash
# Override smart skipping
python seed_price_history.py --top 50 --force
```

### Progress Tracking
- Real-time progress percentage
- ETA calculations
- Items skipped vs seeded count

---

## 📊 Performance Comparison

### Without Smart Skipping (Old Behavior)
```bash
# Day 1
python seed_price_history.py --top 50  # 4 minutes

# Day 2 (re-run)
python seed_price_history.py --top 50  # 4 minutes (redundant!)

# Day 3 (expand)
python seed_price_history.py --top 100 # 8 minutes (re-seeds first 50!)
```

### With Smart Skipping (New Behavior)
```bash
# Day 1
python seed_price_history.py --top 50  # 4 minutes

# Day 2 (re-run)
python seed_price_history.py --top 50  # < 1 second (all skipped!)

# Day 3 (expand)
python seed_price_history.py --top 100 # 4 minutes (only seeds 50 new items!)
```

**Result:** Up to **50% time savings** when expanding coverage!

---

## ⚙️ Delay Options

| Delay | Items/Hour | Use Case |
|-------|------------|----------|
| 1s    | 3600       | Aggressive (not recommended) |
| 5s    | 720        | **Default (balanced)** |
| 10s   | 360        | Conservative |
| 30s   | 120        | Very safe (probably overkill) |

**Recommendation:** Stick with the 5s default unless you have a specific reason to change it.

---

## 📝 Summary

### Key Changes from Old Guide
- ❌ No official OSRS Wiki API rate limit exists
- ✅ 5-second delay is self-imposed and conservative
- ✅ Smart skipping dramatically reduces re-run times
- ✅ Force flag to override skipping if needed
- ✅ Much faster seeding times (50 items in 4 min vs 25 min)

### Best Practice
1. **First run:** `python seed_price_history.py --top 50` (~4 min)
2. **Let it run:** Background polling handles ongoing updates
3. **Expand as needed:** Smart skipping makes adding more items fast
4. **Re-run safely:** Items with sufficient data are skipped automatically

You're now optimized for fast, efficient historical data collection! 🚀
