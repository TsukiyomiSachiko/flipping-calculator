# Data Quality Scoring System

The data quality scoring system detects manipulated, stale, or unreliable price data that could mislead traders. It uses statistical analysis and sanity checks to filter out suspicious items from flip recommendations.

## Overview

**Quality Score: 0-100** where higher = more trustworthy

| Score Range | Tier | Color | Meaning |
|:---:|:---:|:---:|:---|
| 80-100 | High | 🟢 Green | Reliable data - safe to trade |
| 50-79 | Medium | 🟡 Yellow | Use with caution - verify prices |
| 0-49 | Low | 🔴 Red | Likely manipulated/stale - avoid |

## How It Works

The quality score combines five independent checks, each producing a 0-100 sub-score:

### 1. Price Floor Check (20% weight)

**Problem:** Items trading under 50gp are often manipulated or inactive. A 0.25gp → 1gp change is 300% but meaningless.

**Detection:**
- Under 10gp → Score 0
- Under 25gp → Score 30
- Under 50gp → Score 60
- 50gp+ → Score 100

**Example Flags:**
- "Low absolute prices (buy: 5gp, sell: 12gp)"

### 2. Spread Sanity Check (25% weight)

**Problem:** Impossible spreads (1gp buy, 100gp+ sell) indicate stale data or manipulation. Junk items don't actually have 10,000% margins.

**Detection:**
- Spread >1000% → Score 0 (impossible)
- Spread >500% → Score 30 (very suspicious)
- Spread >200% → Score 60 (questionable)
- Spread <200% → Score 100 (reasonable)

**Example Flags:**
- "Impossible spread: 5000% (1gp → 51gp)"
- "Very wide spread: 850% (likely stale data)"

### 3. Volume-to-Price Correlation (20% weight)

**Problem:** Large price moves should require proportional trading volume. A 10% price spike on only 50 volume/hour is suspicious.

**Expected minimum volume:**
- >20% price change → 20,000+ volume
- >10% change → 5,000+ volume
- >5% change → 1,000+ volume
- >1% change → 100+ volume

**Detection:**
- Volume < 20% of expected → Score 20
- Volume 20-50% of expected → Score 50
- Volume 50-100% of expected → Score 75
- Volume >= expected → Score 100

**Example Flags:**
- "Price moved +8.5% on only 150 volume"
- "Low volume (800) for +12.3% price move"

### 4. Historical Volatility Z-Score (20% weight)

**Problem:** Price changes should be consistent with the item's normal volatility. A 15% hourly move for an item that normally moves ±0.5% is extreme.

**Z-score:** How many standard deviations the current change is from typical

**Detection:**
```
historical_volatility = stdev(last 7 days hourly changes)
z_score = abs(current_change_pct) / historical_volatility

z > 3.0 (extreme outlier) → Score 20
z > 2.0 (suspicious) → Score 50
z > 1.5 → Score 75
z ≤ 1.5 → Score 100
```

**Example Flags:**
- "Extreme outlier: 4.2σ (>3.0σ typical)"
- "Suspicious movement: 2.8σ (>2.0σ typical)"

**Note:** Requires at least 24 hours of price history. Items without history get neutral score (70).

### 5. Price Stability Check (15% weight)

**Problem:** Sudden 10x+ price spikes in 24 hours are usually manipulation, not legitimate market movement.

**Detection:**
- Spike >10x or <0.1x → Score 10
- Spike >5x or <0.2x → Score 40
- Spike >2x or <0.5x → Score 70
- Spike <2x → Score 100

**Example Flags:**
- "Price spiked 12.5x in 24h (manipulation likely)"
- "Price moved 6.2x in 24h (suspicious)"

## Final Score Calculation

```python
quality_score = (
    price_floor_score * 0.20 +
    spread_score * 0.25 +
    volume_score * 0.20 +
    volatility_score * 0.20 +
    stability_score * 0.15
)
```

Items scoring below 50 are filtered out when "Filter Suspicious Items" is enabled.

## Usage

### Backend Integration

The trending algorithm **always applies** quality filtering with minimum score 50:

```python
from app.services.data_quality_service import DataQualityService

# In TrendingService.get_trending_flips()
candidates = DataQualityService.filter_suspicious_items(
    candidates, min_quality_score=50.0
)
```

For flip search, quality filtering is **optional** (user toggle):

```python
# In FlipService.get_profitable_flips()
if params.get('enable_quality_filter', False):
    min_quality = params.get('min_quality_score', 50.0)
    items = DataQualityService.filter_suspicious_items(items, min_quality)
```

### Frontend Display

When quality filtering is enabled, each item includes:

```javascript
{
  quality_score: 72.5,
  quality_tier: "medium",  // "high" | "medium" | "low"
  quality_flags: [
    "Wide spread: 230% (check price recency)",
    "Low volume (1200) for +5.2% price move"
  ]
}
```

The expanded flip details show:
- **Data Quality:** Color-coded score (green/yellow/red)
- **Warning:** First quality flag if any exist

## Real-World Examples

### Example 1: Iron kiteshield (Manipulation)
```
Buy: 1gp, Sell: 100gp
Volume: 50/hour
Price change: +400% in 1 hour

Price Floor: 0 (under 10gp)
Spread Sanity: 0 (9900% spread)
Volume Correlation: 20 (insufficient for 400% move)
Volatility Z-Score: 20 (extreme outlier)
Stability: 10 (price spiked 50x)

Quality Score: 8/100 → FILTERED OUT
```

### Example 2: Thin snail meat (Low absolute profit)
```
Buy: 38gp, Sell: 76gp
Volume: 47/hour
Profit: 38gp after tax

Price Floor: 60 (under 50gp)
Spread Sanity: 100 (100% spread is reasonable)
Volume Correlation: 50 (low volume for item)
Volatility Z-Score: 75 (within normal range)
Stability: 100 (stable prices)

Quality Score: 75/100 → PASSES (but hourly profit terrible)
```

### Example 3: Lava rune (Legitimate flip)
```
Buy: 210gp, Sell: 220gp
Volume: 635,000/hour
Profit: 7gp after tax

Price Floor: 100 (well above 50gp)
Spread Sanity: 100 (4.7% spread is healthy)
Volume Correlation: 100 (massive volume)
Volatility Z-Score: 100 (stable item)
Stability: 100 (consistent prices)

Quality Score: 100/100 → PASSES
```

## Configuration

### Adjustable Thresholds

In `DataQualityService`:

```python
MIN_ABSOLUTE_PRICE = 50  # Items under this often manipulated
MAX_SPREAD_MULTIPLIER = 10.0  # Spread >1000% suspicious
MIN_VOLUME_FOR_PRICE_MOVE = 100  # Base volume requirement
EXTREME_ZSCORE = 3.0  # >3σ = extreme outlier
SUSPICIOUS_ZSCORE = 2.0  # >2σ = suspicious
```

### User Controls

**Frontend toggle:** "Filter Suspicious Items" checkbox
- Enabled: Only shows items with quality_score ≥ 50
- Disabled: Shows all items (no filtering)

**Trending preset:** Always applies filtering (hardcoded min_quality_score=50)

## Benefits

1. **Prevents wasted time:** No more sitting on offers for items that never fill
2. **Avoids manipulation:** Filters out artificially spiked items
3. **Improves trust:** Algorithm recommendations become more reliable
4. **Educational:** Quality flags help users learn what suspicious data looks like

## Limitations

1. **Requires price history:** Z-score analysis needs 24+ hours of data
2. **Conservative:** May filter some legitimate high-volatility items
3. **No manipulation prevention:** Only detects, doesn't stop manipulation
4. **Lag:** Historical checks may miss very recent manipulation

## Future Enhancements

- **Machine learning:** Train classifier on known manipulation examples
- **Cross-item analysis:** Detect manipulation patterns across similar items
- **User feedback:** Allow reporting of suspicious items to improve detection
- **Real-time alerts:** Notify when quality scores suddenly drop
- **Whitelist:** Exclude known-good items from filtering
