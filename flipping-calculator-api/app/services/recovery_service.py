import math
from typing import Dict, Optional, List
from app.utils.api_client import fetch_price_timeseries, fetch_latest_prices


def calculate_ge_tax(price: int) -> int:
    """Calculate GE tax with 5M cap (2% of price, max 5M, only applies > 50 gp)"""
    if price <= 50:
        return 0
    tax = int(price * 0.02)
    return min(tax, 5_000_000)


class RecoveryAnalysisService:
    """
    Analyses historical price data to estimate the probability of profit
    recovery for an item, helping users decide whether to hold or cut losses.

    Uses 6h timeseries granularity for trend analysis over the past week.
    """

    @staticmethod
    def analyse_recovery(item_id: int, buy_price: int) -> Optional[Dict]:
        """
        Analyse whether an item's price is likely to recover to a target buy price.

        Returns a recovery outlook with:
        - trend direction and strength
        - historical volatility
        - recovery probability estimate
        - actionable recommendation
        """
        try:
            ts_data = fetch_price_timeseries(item_id, timestep='6h')
        except Exception:
            return None

        data_points = ts_data.get('data', [])
        if not data_points or len(data_points) < 4:
            return None

        # Filter out data points with missing prices
        valid = [
            dp for dp in data_points
            if dp.get('avgHighPrice') and dp.get('avgLowPrice')
        ]

        if len(valid) < 4:
            return None

        # Sort by timestamp ascending
        valid.sort(key=lambda x: x['timestamp'])

        # Extract sell prices (avgLowPrice = what the flipper sells at in our system)
        # and buy prices for spread analysis
        sell_prices = [dp['avgLowPrice'] for dp in valid]
        buy_prices = [dp['avgHighPrice'] for dp in valid]
        volumes = [
            (dp.get('highPriceVolume', 0) or 0) + (dp.get('lowPriceVolume', 0) or 0)
            for dp in valid
        ]

        current_sell = sell_prices[-1]
        current_buy = buy_prices[-1]
        n = len(sell_prices)

        # --- 1. Trend Analysis (linear regression on sell prices) ---
        # Use index as x, sell_price as y
        x_mean = (n - 1) / 2
        y_mean = sum(sell_prices) / n

        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(sell_prices))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator > 0 else 0

        # Normalise slope as % of mean price per 6h window
        trend_pct_per_6h = (slope / y_mean) * 100 if y_mean > 0 else 0

        # Recent trend (last 4 windows = 24h)
        recent = sell_prices[-4:]
        recent_slope = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)
        recent_trend_pct = (recent_slope / y_mean) * 100 if y_mean > 0 else 0

        # Classify trend
        if recent_trend_pct > 0.5:
            trend_direction = "recovering"
        elif recent_trend_pct > 0.1:
            trend_direction = "stabilising"
        elif recent_trend_pct > -0.3:
            trend_direction = "flat"
        elif recent_trend_pct > -1.0:
            trend_direction = "declining"
        else:
            trend_direction = "crashing"

        # --- 2. Volatility (standard deviation of 6h % changes) ---
        pct_changes = []
        for i in range(1, len(sell_prices)):
            if sell_prices[i - 1] > 0:
                pct_changes.append(
                    ((sell_prices[i] - sell_prices[i - 1]) / sell_prices[i - 1]) * 100
                )

        if pct_changes:
            vol_mean = sum(pct_changes) / len(pct_changes)
            volatility = math.sqrt(
                sum((x - vol_mean) ** 2 for x in pct_changes) / len(pct_changes)
            )
        else:
            volatility = 0

        # --- 3. Distance to breakeven ---
        # How far is current sell price from the user's buy price?
        # Positive = already profitable, negative = underwater
        ge_tax = calculate_ge_tax(current_sell)
        net_sell = current_sell - ge_tax
        distance_gp = net_sell - buy_price
        distance_pct = (distance_gp / buy_price) * 100 if buy_price > 0 else 0

        # --- 4. Historical recovery count ---
        # Look at how often the sell price has been at or above the buy price
        # in the observed window
        recovery_count = sum(1 for p in sell_prices if p >= buy_price)
        recovery_rate = recovery_count / n

        # Count dip-and-recover patterns: how often did price drop below
        # buy_price and then come back above it?
        dip_recoveries = 0
        dip_opportunities = 0
        in_dip = False
        for p in sell_prices:
            if p < buy_price:
                if not in_dip:
                    dip_opportunities += 1
                    in_dip = True
            else:
                if in_dip:
                    dip_recoveries += 1
                    in_dip = False

        dip_recovery_rate = (
            dip_recoveries / dip_opportunities
            if dip_opportunities > 0
            else None
        )

        # --- 5. Price range analysis ---
        price_high = max(sell_prices)
        price_low = min(sell_prices)
        price_range_pct = ((price_high - price_low) / price_low) * 100 if price_low > 0 else 0

        # Where is buy_price within the historical range?
        if price_high > price_low:
            buy_in_range = ((buy_price - price_low) / (price_high - price_low)) * 100
        else:
            buy_in_range = 50

        # --- 6. Volume trend ---
        if len(volumes) >= 4:
            recent_vol = sum(volumes[-4:]) / 4
            older_vol = sum(volumes[:-4]) / max(len(volumes) - 4, 1)
            volume_trend = ((recent_vol - older_vol) / older_vol) * 100 if older_vol > 0 else 0
        else:
            recent_vol = sum(volumes) / len(volumes)
            volume_trend = 0

        # --- 7. Composite recovery probability ---
        # Weighted estimate combining all signals
        prob = 50.0  # Start neutral

        # Trend contribution (±20)
        if trend_direction == "recovering":
            prob += 15
        elif trend_direction == "stabilising":
            prob += 8
        elif trend_direction == "flat":
            prob += 0
        elif trend_direction == "declining":
            prob -= 12
        else:  # crashing
            prob -= 20

        # Recent momentum bonus (±10)
        prob += min(10, max(-10, recent_trend_pct * 5))

        # Volatility contribution (±10)
        # Higher volatility = more chance of recovery (but also more risk)
        if distance_pct < 0:  # Underwater
            prob += min(10, volatility * 2)  # volatility helps when underwater
        else:
            prob += 5  # Already profitable, mild bonus

        # Distance contribution (±15)
        if distance_pct >= 0:
            prob += 15  # Already profitable
        elif distance_pct >= -2:
            prob += 8  # Very close to breakeven
        elif distance_pct >= -5:
            prob += 0  # Moderate loss
        elif distance_pct >= -10:
            prob -= 8  # Significant loss
        else:
            prob -= 15  # Deep underwater

        # Historical recovery rate (±10)
        if dip_recovery_rate is not None:
            prob += (dip_recovery_rate - 0.5) * 20  # Scale around 50%
        elif recovery_rate > 0.7:
            prob += 8
        elif recovery_rate > 0.4:
            prob += 0
        else:
            prob -= 5

        # Buy price position in range (±5)
        if buy_in_range < 40:
            prob += 5  # Buy price is in the lower part of range — easier to reach
        elif buy_in_range > 80:
            prob -= 5  # Buy price is near the top — hard to reach

        # Volume trend (±5)
        if volume_trend > 20:
            prob += 5  # Increasing activity
        elif volume_trend < -20:
            prob -= 5  # Dying interest

        prob = round(min(95, max(5, prob)), 1)

        # --- 8. Generate recommendation ---
        if distance_gp > 0:
            recommendation = "SELL"
            reasoning = "Already profitable at current market prices."
        elif distance_gp == 0:
            recommendation = "SELL"
            reasoning = "Break-even at current market prices."
        elif prob >= 70:
            recommendation = "HOLD"
            reasoning = "Strong recovery signals. Price is trending upward with healthy volume."
        elif prob >= 55:
            recommendation = "HOLD_CAUTIOUS"
            reasoning = "Moderate recovery chance. Consider setting a time limit to cut losses if no improvement."
        elif prob >= 40:
            recommendation = "UNCERTAIN"
            reasoning = "Mixed signals. Recovery is possible but not favoured. Consider reducing position size."
        elif prob >= 25:
            recommendation = "CUT_LOSSES"
            reasoning = "Recovery is unlikely in the near term. Selling now frees up capital for better opportunities."
        else:
            recommendation = "CUT_LOSSES_URGENT"
            reasoning = "Strong downward pressure with low recovery probability. Recommend selling immediately."

        return {
            "item_id": item_id,
            "buy_price": buy_price,
            "current_sell_price": current_sell,
            "current_buy_price": current_buy,
            "distance_gp": distance_gp,
            "distance_pct": round(distance_pct, 2),
            "trend": {
                "direction": trend_direction,
                "overall_pct_per_6h": round(trend_pct_per_6h, 3),
                "recent_24h_pct": round(recent_trend_pct, 3),
            },
            "volatility": {
                "pct_per_6h": round(volatility, 2),
                "price_range_pct": round(price_range_pct, 2),
                "price_high": price_high,
                "price_low": price_low,
            },
            "historical": {
                "above_buy_rate": round(recovery_rate * 100, 1),
                "dip_recovery_rate": round(dip_recovery_rate * 100, 1) if dip_recovery_rate is not None else None,
                "data_points": n,
            },
            "volume": {
                "recent_avg": round(recent_vol, 0),
                "volume_trend_pct": round(volume_trend, 1),
            },
            "recovery_probability": prob,
            "recommendation": recommendation,
            "reasoning": reasoning,
        }