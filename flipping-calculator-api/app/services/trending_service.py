import math
from typing import List, Dict, Optional
from app.utils.database import get_db
from app.utils.api_client import fetch_latest_prices, fetch_volume_data, fetch_5m_volume_data
from app.services.item_service import ItemService
from app.services.data_quality_service import DataQualityService
from app.services.settings_service import SettingsService


class TrendingService:
    """
    Identifies trending items by computing price momentum from three
    already-cached price snapshots: /latest, /5m, and /1h.

    No additional API calls required — piggybacks on the same bulk
    endpoints used by FlipService.

    Items must be genuinely profitable AND trending to qualify.

    Filters:
      - profit >= 5 gp        (no zero-margin items)
      - ROI >= 0.5%           (meaningful return)
      - volume >= 1000        (real liquidity)

    Score formula:
      - Momentum:           overall_change_pct * 2.0   (price direction)
      - Acceleration:       acceleration * 1.0          (price speeding up)
      - Volume:             vol_factor * 4.5            (signal reliability - CRITICAL per live testing)
      - Profitability:      roi_factor * 3.0            (percentage return)
      - Spread health:      spread_factor * 2.0         (healthy margin)
      - Absolute profit:    absolute_profit_factor * 8.0 (real GP gains - prevents cheap item spam)
    """

    @staticmethod
    def get_trending_flips(account_id: int, cash: Optional[int] = None, limit: int = 10) -> list:
        # Auto-fetch cash from user settings if not provided
        if cash is None:
            user_settings = SettingsService.get_settings(account_id)
            cash = user_settings.get('available_cash', 0)
        latest_data = fetch_latest_prices(use_cache=True)
        volume_1h_data = fetch_volume_data(use_cache=True)
        volume_5m_data = fetch_5m_volume_data(use_cache=True)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items')
            items = {str(row['id']): dict(row) for row in cursor.fetchall()}

        candidates = []

        for item_id_str, price_data in latest_data.get('data', {}).items():
            if item_id_str not in items:
                continue

            item = items[item_id_str]

            buy_now = price_data.get('low')
            sell_now = price_data.get('high')
            if not buy_now or not sell_now or buy_now <= 0 or sell_now <= 0:
                continue

            if cash is not None and buy_now > cash:
                continue

            # 1h data
            data_1h = volume_1h_data.get('data', {}).get(item_id_str, {})
            avg_high_1h = data_1h.get('avgHighPrice')
            avg_low_1h = data_1h.get('avgLowPrice')
            vol_1h = (data_1h.get('highPriceVolume', 0) or 0) + (data_1h.get('lowPriceVolume', 0) or 0)

            # 5m data
            data_5m = volume_5m_data.get('data', {}).get(item_id_str, {})
            avg_high_5m = data_5m.get('avgHighPrice')
            avg_low_5m = data_5m.get('avgLowPrice')
            vol_5m = (data_5m.get('highPriceVolume', 0) or 0) + (data_5m.get('lowPriceVolume', 0) or 0)

            if not avg_high_1h or not avg_low_1h:
                continue

            # Hard gates - must have significant volume
            # Based on live testing: low volume items don't fill even with high profit
            if vol_1h < 1000:
                continue
            
            # Safety check: never score items with 0 volume
            if vol_1h == 0:
                continue

            profit_data = ItemService.calculate_profit(buy_now, sell_now)
            profit = profit_data['profit_per_item']
            roi = profit_data['roi']

            if profit < 5:
                continue
            if roi < 0.5:
                continue

            # Midpoint prices at each snapshot
            mid_now = (buy_now + sell_now) / 2
            mid_1h = (avg_high_1h + avg_low_1h) / 2
            mid_5m = ((avg_high_5m + avg_low_5m) / 2) if (avg_high_5m and avg_low_5m) else mid_now

            if mid_1h <= 0:
                continue

            # Momentum metrics
            overall_change_pct = ((mid_now - mid_1h) / mid_1h) * 100
            medium_change_pct = ((mid_5m - mid_1h) / mid_1h) * 100 if mid_1h > 0 else 0
            short_change_pct = ((mid_now - mid_5m) / mid_5m) * 100 if mid_5m > 0 else 0
            acceleration = short_change_pct - medium_change_pct
            vol_factor = math.log10(max(vol_1h, 1)) / 5

            # Cap momentum and acceleration to prevent cheap item spam
            # 0.25gp -> 1gp = 300% change, but shouldn't dominate real flips
            capped_momentum = max(min(overall_change_pct, 20), -20)  # Cap at ±20%
            capped_acceleration = max(min(acceleration, 10), -10)     # Cap at ±10%

            # Profitability and spread factors (both 0-1, capped)
            roi_factor = min(roi, 10) / 10
            spread_pct = (profit / buy_now) * 100 if buy_now > 0 else 0
            spread_factor = min(spread_pct, 5) / 5
            
            # Absolute profit penalty - heavily penalize low absolute profit items
            # Items with <100gp profit get 0, items with 1000gp+ get full score
            profit_at_limit_gp = profit * (item.get('ge_limit', 0) or 0)
            absolute_profit_factor = min(profit_at_limit_gp, 50000) / 50000

            # Trending score (using capped values)
            momentum_score = (
                capped_momentum * 2.0
                + capped_acceleration * 1.0
                + vol_factor * 4.5  # Heavily weighted - volume is CRITICAL per live testing
                + roi_factor * 3.0
                + spread_factor * 2.0
                + absolute_profit_factor * 8.0  # Very heavy weight for absolute profit - prevents junk items
            )
            
            # Debug logging for Iron Kiteshield
            if item['id'] == 1191:  # Iron kiteshield ID
                print(f"\n=== IRON KITESHIELD DEBUG ===")
                print(f"Profit: {profit} gp")
                print(f"GE Limit: {item.get('ge_limit', 0)}")
                print(f"Profit at limit: {profit_at_limit_gp} gp")
                print(f"Absolute profit factor: {absolute_profit_factor}")
                print(f"Absolute profit score: {absolute_profit_factor * 4.0}")
                print(f"Raw momentum: {overall_change_pct}% -> Capped: {capped_momentum}%")
                print(f"Raw acceleration: {acceleration}% -> Capped: {capped_acceleration}%")
                print(f"Momentum score contribution: {capped_momentum * 2.0}")
                print(f"Acceleration score contribution: {capped_acceleration * 1.0}")
                print(f"Overall momentum score: {momentum_score}")
                print(f"ROI factor score: {roi_factor * 3.0}")
                print(f"Spread factor score: {spread_factor * 2.0}")
                print(f"===========================\n")

            # Direction label
            if overall_change_pct > 1.0:
                direction = 'surging'
            elif overall_change_pct > 0.3:
                direction = 'rising'
            elif overall_change_pct > -0.3:
                direction = 'stable'
            elif overall_change_pct > -1.0:
                direction = 'falling'
            else:
                direction = 'dropping'

            ge_limit = item.get('ge_limit', 0) or 0
            profit_at_limit = profit * ge_limit if ge_limit > 0 else 0

            max_qty = ge_limit
            your_profit = profit_at_limit
            if cash is not None and ge_limit > 0 and buy_now > 0:
                affordable_qty = cash // buy_now
                if affordable_qty < ge_limit:
                    max_qty = affordable_qty
                    your_profit = profit * affordable_qty

            # Use calculate_momentum for the composite score
            momentum_for_score = ItemService.calculate_momentum(buy_now, sell_now, data_1h, data_5m)

            candidates.append({
                "id": item['id'],
                "name": item['name'],
                "members": item['members'],
                "buy_price": buy_now,
                "sell_price": sell_now,
                "profit": profit,
                "limit_profit": profit_at_limit,
                "roi": roi,
                "volume": vol_1h,
                "volume_indicator": ItemService.get_volume_indicator(vol_1h),
                "ge_limit": ge_limit,
                "profit_at_limit": profit_at_limit,
                "max_qty": max_qty,
                "your_profit": your_profit,
                "ge_tax": profit_data.get('ge_tax', 0),
                "score": ItemService.calculate_score(
                    profit=profit, roi=roi, volume=vol_1h,
                    ge_limit=ge_limit, buy_price=buy_now, cash=cash,
                    momentum=momentum_for_score,
                ),
                "secondary_score": ItemService.calculate_erebus_score(
                    buy_price=buy_now, sell_price=sell_now,
                    volume_5m=vol_5m, volume_1h=vol_1h,
                ),
                "momentum_score": round(momentum_score, 1),
                "price_change_pct": round(overall_change_pct, 2),
                "acceleration": round(acceleration, 2),
                "direction": direction,
            })

        # Apply data quality filtering (removes manipulated/suspicious items)
        candidates = DataQualityService.filter_suspicious_items(
            candidates, min_quality_score=50.0
        )

        candidates.sort(key=lambda x: x['momentum_score'], reverse=True)
        return candidates[:limit]