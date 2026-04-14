# Flip Score Algorithm

The composite flip score is a single **0–100** metric that ranks Grand Exchange flipping opportunities by balancing six factors: profitability, scale, liquidity, capital risk, spread reliability, and price momentum. It is calculated server-side in `ItemService.calculate_score()` and returned on every flip search result and item detail response.

## Overview

| Factor | Weight | What it measures |
|:---|:---:|:---|
| ROI | 15% | Capital efficiency — how much profit per GP invested |
| Profit at Limit | 30% | Total GP potential per 4-hour GE cycle |
| Volume | 20% | Trade activity — how fast your offers will fill |
| Cash Efficiency | 5% | Portfolio risk — how much of your cash stack one flip ties up |
| Spread Health | 15% | Margin reliability — whether the spread is realistic or likely stale |
| Momentum | 15% | Price trajectory — rewards items trending upward |

All six factors produce an individual sub-score from 0 to 100, then are combined using a weighted sum.

When momentum data is unavailable (e.g. a newly listed item with no 1h history), the momentum factor is dropped and the remaining five factors are weighted proportionally (ROI 18%, Profit at Limit 35%, Volume 24%, Cash Efficiency 6%, Spread Health 18%).

---

## Factor 1: ROI (15%)

**Purpose:** Measures capital efficiency — a 10% ROI flip is better use of capital than a 0.5% ROI flip, regardless of raw GP profit.

**Formula:**

```
roi_score = min(100, (log₁₀(max(roi, 0.1) + 1) / log₁₀(26)) × 100)
```

The logarithmic scale creates diminishing returns. Going from 1% to 5% ROI is a much bigger improvement than going from 20% to 25%.

**Reference values:**

| ROI | Sub-score |
|:---:|:---:|
| 1% | ~25 |
| 5% | ~57 |
| 10% | ~71 |
| 15% | ~80 |
| 25% | ~90 |

**Why log-scaled:** Without diminishing returns, extremely high ROI items (often low-volume or stale-priced) would dominate the rankings. The log curve rewards good ROI while preventing outliers from overwhelming other factors.

---

## Factor 2: Profit at Limit (30%)

**Purpose:** Measures total earning potential per 4-hour GE cycle. An item with 50gp profit but a limit of 10,000 earns 500K per cycle — far more useful than 5,000gp profit with a limit of 2.

**Formula:**

```
profit_at_limit = profit_per_item × ge_limit

pal_score = min(100, (log₁₀(profit_at_limit) / log₁₀(100,000,000)) × 100)
```

The denominator `log₁₀(100M)` means an item would need 100M profit-at-limit to score a perfect 100 on this factor (essentially unreachable, which is intentional).

**Reference values:**

| Profit at Limit | Sub-score |
|:---:|:---:|
| 10K | ~33 |
| 100K | ~50 |
| 1M | ~67 |
| 10M | ~83 |

Items with no GE limit data score 0 on this factor.

---

## Factor 3: Volume (20%)

**Purpose:** Higher trade volume means your buy/sell offers fill faster and the price data is more trustworthy. Low-volume items may show attractive margins that never actually execute.

**Formula:**

```
vol_score = min(100, (log₁₀(volume) / log₁₀(1,000,000)) × 100)
```

Uses the 1-hour combined volume (buy + sell transactions) from the OSRS Wiki API.

**Reference values:**

| 1h Volume | Sub-score |
|:---:|:---:|
| 100 | ~33 |
| 1,000 | ~50 |
| 5,000 | ~62 |
| 50,000 | ~78 |
| 500,000 | ~95 |

Items with zero volume score 0 on this factor.

---

## Factor 4: Cash Efficiency (5%)

**Purpose:** Penalises flips that either waste your capital (using 1% of your stack on a tiny flip) or concentrate too much risk (dumping 80% of your stack into one item). The sweet spot is 5–30% of your available cash.

**Formula:**

```
cost = buy_price × min(ge_limit, cash ÷ buy_price)
utilisation = cost / cash
```

The sub-score uses a piecewise function based on utilisation:

| Utilisation | Behaviour | Sub-score range |
|:---|:---|:---:|
| 0–5% | Ramp up (too small to matter) | 0 → 70 |
| 5–30% | Sweet spot (ideal allocation) | 100 |
| 30–60% | Gradual penalty (getting risky) | 100 → 50 |
| 60–100% | Heavy penalty (dangerous concentration) | 50 → 0 |

**When no cash is specified:** The sub-score defaults to 50 (neutral), so this factor neither helps nor hurts the overall score.

---

## Factor 5: Spread Health (15%)

**Purpose:** Evaluates whether the margin between buy and sell prices is realistic and likely to result in a completed trade. Very tight spreads risk being eaten by the 2% GE tax, while suspiciously wide spreads usually indicate stale or unreliable price data.

**Formula:**

```
spread_pct = (profit / buy_price) × 100
```

The sub-score uses a piecewise function based on spread percentage:

| Spread % | Behaviour | Sub-score range |
|:---|:---|:---:|
| ≤ 0% | No margin | 0 |
| 0–1% | Very tight, tax risk | 0 → 60 |
| 1–10% | Healthy range | 60 → 100 |
| 10–25% | Getting wide, may not fill | 100 → 60 |
| > 25% | Suspiciously wide, likely stale | 60 → 0 |

---

## Factor 6: Momentum (15%)

**Purpose:** Rewards items whose price is trending upward, penalises items in decline. An item with a rising price is more likely to maintain or widen its margin by the time your buy offer fills, while a declining item may see its sell price erode before you can sell.

**Data source:** Computed from three already-cached bulk API endpoints with no additional requests:
- `/latest` — current instant price
- `/1h` — 1-hour average price

**Formula:**

```
mid_now = (buy_price + sell_price) / 2
mid_1h  = (avg_high_1h + avg_low_1h) / 2

momentum = ((mid_now - mid_1h) / mid_1h) × 100     # % change over 1 hour

clamped  = clamp(momentum, -2.0, +2.0)
momentum_score = ((clamped + 2.0) / 4.0) × 100     # map to 0-100
```

**Reference values:**

| Price change (1h) | Sub-score |
|:---:|:---:|
| -2% or worse | 0 |
| -1% | 25 |
| 0% (flat) | 50 |
| +1% | 75 |
| +2% or more | 100 |

**Why clamped at ±2%?** Hourly price swings beyond 2% are rare for actively traded items and usually indicate either very low volume (unreliable signal) or a one-off spike. Clamping prevents outlier movements from dominating the score.

**When unavailable:** If 1-hour data doesn't exist for an item, the momentum factor is dropped entirely and the other five factors are weighted using their original proportions. This ensures items aren't penalised for missing data.

---

## Final Score

```
# With momentum data:
score = (roi × 0.15) + (pal × 0.30) + (vol × 0.20) + (cash × 0.05) + (spread × 0.15) + (momentum × 0.15)

# Without momentum data (fallback):
score = (roi × 0.18) + (pal × 0.35) + (vol × 0.24) + (cash × 0.06) + (spread × 0.18)
```

The result is clamped to **0–100** and rounded to one decimal place.

---

## Score Interpretation

| Score | Colour | Meaning |
|:---:|:---:|:---|
| 70+ | 🟢 Green | Strong flip — good balance of profit, volume, and risk |
| 45–69 | 🟡 Yellow | Decent flip — solid but may be weak in one area |
| 25–44 | 🟠 Orange | Marginal — likely low volume, tight spread, or poor capital fit |
| < 25 | ⚪ Grey | Weak — multiple factors are unfavourable |

---

## Design Decisions

**Why six factors instead of one formula?** A single formula like `profit × volume` tends to be dominated by whichever variable has the largest range. The weighted sub-score approach lets each factor contribute proportionally regardless of its natural scale.

**Why logarithmic scaling?** GP values in OSRS span many orders of magnitude (100gp to 100M+). Linear scaling would make the score meaningless for low-value items. Log scaling compresses the range so that improvements at every level of the scale are meaningfully rewarded.

**Why is ROI only 15%?** While ROI percentage matters for capital efficiency, items with very high ROI are often low-volume or low absolute profit. Reducing ROI weight from 20% to 15% prevents items like Water Runes (20% ROI but only 50K at limit) from dominating over more profitable flips.

**Why is Profit at Limit 30%?** This is now the highest-weighted factor (increased from 25%) because absolute GP profit per cycle is the most important metric for actual wealth building. A 500K flip is more useful than a 50K flip, even if the latter has better ROI.

**Why is cash efficiency only 5%?** It's the most personal factor — it depends entirely on the user's current wealth, which changes constantly. Reduced from 10% to 5% to further emphasize absolute profit over capital allocation preferences. At 5%, it acts as a minor tiebreaker.

**Why does no-cash default to 50?** Many users search without entering their cash stack. Defaulting to 0 or 100 would unfairly penalise or reward items. A neutral 50 means the other factors drive the ranking when cash isn't specified.

**Why is momentum 15%?** Increased from 10% to give more weight to market direction and prediction data. Items with positive momentum are more likely to maintain or improve their margins. This rewards flips where the market is moving in your favor.

**Why does the fallback use proportional weights?** When momentum data is missing, adding a neutral 50 score at 15% weight would systematically bias results downward for items without history. Dropping the factor entirely and redistributing weight keeps scores comparable regardless of data availability.