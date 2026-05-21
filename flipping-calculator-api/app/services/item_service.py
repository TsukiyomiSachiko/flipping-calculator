from typing import List, Dict, Optional
import math
from app.utils.database import get_db
from app.utils.api_client import fetch_item_mapping, fetch_latest_prices, fetch_volume_data, fetch_5m_volume_data
from datetime import datetime, timezone


def calculate_ge_tax(price: int) -> int:
    """Calculate GE tax with 5M cap (2% of price, max 5M, only applies > 50 gp)"""
    if price <= 50:
        return 0
    tax = int(price * 0.02)
    return min(tax, 5_000_000)


class ItemService:

    @staticmethod
    def calculate_score(
        profit: int,
        roi: float,
        volume: int,
        ge_limit: int,
        buy_price: int,
        cash: Optional[int] = None,
        momentum: Optional[float] = None,
    ) -> float:
        """
        Calculate a composite flip score (0-100).

        Factors and weights (UPDATED - heavily favor volume per live testing):
          - ROI (15%):             Capital efficiency, log-scaled with diminishing returns
          - Profit at limit (25%): Total GP potential per 4h cycle, log-scaled (reduced from 30%)
          - Volume (35%):          Trade activity / fill speed, log-scaled (INCREASED - CRITICAL per live testing)
          - Cash efficiency (5%):  Penalises using too much or too little of your stack
          - Spread health (10%):   Rewards reasonable margins (reduced from 15%)
          - Momentum (10%):        Price trajectory — rewards items trending upward (reduced from 15%)

        When momentum data is not available, weight is redistributed to
        the other factors proportionally.
        
        CRITICAL: Items with 0 volume get score of 0 regardless of other factors.
        """
        # Hard filter: 0 volume = worthless regardless of profit
        if volume == 0:
            return 0.0
            
        if profit <= 0 or buy_price <= 0:
            return 0.0

        profit_at_limit = profit * ge_limit if ge_limit > 0 else 0

        # --- ROI score (0-100) ---
        # Log-scaled: 1% → ~25, 5% → ~57, 15% → ~80, 25% → ~90
        roi_score = min(100, (math.log10(max(roi, 0.1) + 1) / math.log10(26)) * 100)

        # --- Profit at limit score (0-100) ---
        # Log-scaled: 10K → ~33, 100K → ~50, 1M → ~67, 10M → ~83
        if profit_at_limit > 0:
            pal_score = min(100, (math.log10(profit_at_limit) / math.log10(100_000_000)) * 100)
        else:
            pal_score = 0

        # --- Volume score (0-100) ---
        # Log-scaled: 1K → ~43, 5K → ~53, 50K → ~67, 500K → ~82
        if volume > 0:
            vol_score = min(100, (math.log10(volume) / math.log10(1_000_000)) * 100)
        else:
            vol_score = 0

        # --- Cash efficiency score (0-100) ---
        # Sweet spot: 5-80% of cash stack on one flip (Extended from 30%)
        # Too low = wasting capital, too high = risky concentration
        if cash and cash > 0 and ge_limit > 0:
            cost = buy_price * min(ge_limit, cash // buy_price)
            utilisation = cost / cash
            if utilisation <= 0:
                cash_score = 0
            elif utilisation <= 0.05:
                # Below 5%: ramp up (small flip relative to stack)
                cash_score = (utilisation / 0.05) * 70
            elif utilisation <= 0.80:
                # 5-80%: sweet spot
                cash_score = 100
            else:
                # >80%: Gentle penalty. At 100% usage -> 50 score.
                cash_score = max(0, 100 - ((utilisation - 0.80) / 0.20) * 50)
        else:
            # No cash specified: neutral score
            cash_score = 50

        # --- Spread health score (0-100) ---
        # Rewards reasonable margins (1-10% of buy price), penalises extremes
        spread_pct = (profit / buy_price) * 100  # pre-tax margin
        if spread_pct <= 0:
            spread_score = 0
        elif spread_pct <= 1:
            # Very tight: risky, tax eats profit
            spread_score = spread_pct * 60
        elif spread_pct <= 10:
            # Healthy range
            spread_score = 60 + ((spread_pct - 1) / 9) * 40
        elif spread_pct <= 25:
            # Getting wide: might not fill
            spread_score = 100 - ((spread_pct - 10) / 15) * 40
        else:
            # Suspiciously wide: likely stale prices
            # EXCEPTION: If ROI is > 15%, we tolerate the volatility (set score to 60)
            if roi > 15:
                spread_score = 60
            else:
                spread_score = max(0, 60 - ((spread_pct - 25) / 25) * 60)

        # --- Momentum score (0-100) ---
        # Maps price change % to a 0-100 sub-score.
        # -2% or worse = 0, 0% = 50 (neutral), +2% or more = 100
        if momentum is not None:
            # Clamp to [-2, +2]% range, map to 0-100
            clamped = max(-2.0, min(2.0, momentum))
            momentum_score = ((clamped + 2.0) / 4.0) * 100
        else:
            momentum_score = None

        # --- Weighted total ---
        if momentum_score is not None:
            score = (
                roi_score * 0.15 +       # Capital efficiency
                pal_score * 0.25 +       # Profit potential (reduced from 0.30)
                vol_score * 0.35 +       # VOLUME - CRITICAL (increased from 0.20)
                cash_score * 0.05 +      # Cash utilization
                spread_score * 0.10 +    # Margin health (reduced from 0.15)
                momentum_score * 0.10    # Price direction (reduced from 0.15)
            )
        else:
            # No momentum data: redistribute its weight proportionally
            score = (
                roi_score * 0.17 +       # 15% + (10% * 0.17)
                pal_score * 0.28 +       # 25% + (10% * 0.28)
                vol_score * 0.39 +       # 35% + (10% * 0.39) - STILL HIGHEST
                cash_score * 0.06 +      # 5% + (10% * 0.06)
                spread_score * 0.11      # 10% + (10% * 0.11)
            )

        return round(min(100, max(0, score)), 1)

    @staticmethod
    def calculate_momentum(
        buy_now: Optional[int],
        sell_now: Optional[int],
        data_1h: dict,
        data_5m: dict,
    ) -> Optional[float]:
        """
        Calculate price momentum from three time snapshots.

        Returns the overall price change percentage (1h → now) or None
        if there isn't enough data. This value can be passed directly
        to calculate_score(momentum=...).

        Uses midpoint prices (average of buy/sell) at each snapshot:
          - 1h: avgHighPrice/avgLowPrice from /1h endpoint
          - 5m: avgHighPrice/avgLowPrice from /5m endpoint (fallback to current)
          - now: high/low from /latest endpoint

        No additional API calls — all data comes from already-cached bulk endpoints.
        """
        if not buy_now or not sell_now or buy_now <= 0 or sell_now <= 0:
            return None

        avg_high_1h = data_1h.get('avgHighPrice')
        avg_low_1h = data_1h.get('avgLowPrice')
        if not avg_high_1h or not avg_low_1h:
            return None

        mid_now = (buy_now + sell_now) / 2
        mid_1h = (avg_high_1h + avg_low_1h) / 2

        if mid_1h <= 0:
            return None

        overall_change_pct = ((mid_now - mid_1h) / mid_1h) * 100
        return round(overall_change_pct, 3)

    @staticmethod
    def calculate_erebus_score(
        buy_price: int,
        sell_price: int,
        volume_5m: int,
        volume_1h: int = 0,
    ) -> Optional[float]:
        """
        Erebus scoring algorithm: Score = P * log10(V + 1)

        Uses 5-minute volume window (falls back to 1h / 12 estimate).
        Tax model: 1% of sell price, capped at 5M GP.
        Returns None if data is incomplete or below guard thresholds.

        Note on naming: In our system buy_price < sell_price for profitable
        flips (buy_price = what the flipper pays, sell_price = what they
        receive). The Erebus spec's "High" maps to our sell_price and
        "Low" maps to our buy_price.

        Guards:
          - Incomplete price data → None
          - Net margin < 100 GP → None
          - Effective volume < 1 → None
        """
        # Truth marking: incomplete data
        if not buy_price or not sell_price:
            return None

        # Net margin: M = sell - buy - tax
        # Erebus tax: 1% of the sale price (their "High"), capped at 5M
        tax = min(0.01 * sell_price, 5_000_000)
        margin = sell_price - buy_price - tax

        # Minimum yield guard
        if margin < 100:
            return None

        # Use 5m volume if available, otherwise estimate from 1h
        volume = volume_5m if volume_5m > 0 else (volume_1h // 12)

        if volume < 1:
            return None

        # Profit coefficient: P = (M / buy cost) * 100
        profit_coeff = (margin / buy_price) * 100

        # Score = P * log10(V + 1)
        score = profit_coeff * math.log10(volume + 1)

        return round(score, 1)

    @staticmethod
    def calculate_long_term_score(
        profit: int,
        roi: float,
        volume: int,
        trajectory: Optional[float],
        volatility: Optional[float],
    ) -> float:
        """
        Calculate a score designed for 3-14 day holds.
        
        Weighting:
          - Trajectory (40%): Rewards steady growth, penalizes negative trends heavily.
          - Volatility (Penalty up to -100): Subtracts points for high volatility.
          - ROI (40%): Baseline profit check.
          - Volume (20%): Needs to be liquid enough to eventually sell.
          
        Guards:
          - If volume < 1000 (per day/hour depending on metric): score is heavily reduced.
          - If trajectory is < -5%: score is 0.
        """
        if profit <= 0 or volume <= 0 or trajectory is None or trajectory <= 0.0:
            return 0.0
            
        # --- Trajectory Score (0-100) ---
        if trajectory <= 15.0:
            # Steady climb (0 to +15%)
            traj_score = 50 + (trajectory / 15.0) * 50
        else:
            # Over 15%: Might be a pump and dump, cap it
            traj_score = 100

        # --- Volatility Penalty (0 to 100 subtracted) ---
        # A stable item has ~1-2% volatility. >5% is very chaotic.
        vol_penalty = 0
        if volatility is not None:
            if volatility > 2.0:
                # For every 1% above 2%, subtract 20 points, up to 100
                vol_penalty = min(100, (volatility - 2.0) * 20)
                
        # --- ROI Score (0-100) ---
        roi_score = min(100, (math.log10(max(roi, 0.1) + 1) / math.log10(26)) * 100)
        
        # --- Volume Score (0-100) ---
        vol_score = min(100, (math.log10(volume) / math.log10(1_000_000)) * 100)
        
        # --- Weighted Total ---
        score = (
            traj_score * 0.40 +
            roi_score * 0.40 +
            vol_score * 0.20
        ) - vol_penalty
        
        return round(min(100, max(0, score)), 1)
    @staticmethod
    def sync_items_from_api(force_update: bool = False):
        """
        Sync items from OSRS Wiki API to database.
        
        Args:
            force_update: If True, updates all existing items. 
                         If False, only adds missing items.
        """
        item_data = fetch_item_mapping(use_cache=not force_update)
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            if not force_update:
                # Get existing IDs to find truly new items
                cursor.execute('SELECT id FROM items')
                existing_ids = {row['id'] for row in cursor.fetchall()}
                items_to_sync = [item for item in item_data if item['id'] not in existing_ids]
            else:
                items_to_sync = item_data
            
            if not items_to_sync:
                # Still update the sync time even if no new items
                cursor.execute("UPDATE price_polling_metadata SET last_item_sync_time = ? WHERE id = 1", (datetime.now(timezone.utc),))
                conn.commit()
                return {"message": "No new items to sync", "count": 0}
            
            # Batch insert/update items
            items_to_insert = []
            now = datetime.now(timezone.utc)
            for item in items_to_sync:
                items_to_insert.append((
                    item['id'],
                    item['name'],
                    item.get('examine'),
                    item.get('members', False),
                    item.get('lowalch'),
                    item.get('highalch'),
                    item.get('value'),
                    item.get('limit', 0),
                    item.get('icon'),
                    now
                ))
            
            # Use ON CONFLICT for robustness even in incremental mode
            cursor.executemany('''
                INSERT INTO items 
                (id, name, examine, members, lowalch, highalch, value, ge_limit, icon, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    examine = EXCLUDED.examine,
                    members = EXCLUDED.members,
                    lowalch = EXCLUDED.lowalch,
                    highalch = EXCLUDED.highalch,
                    value = EXCLUDED.value,
                    ge_limit = EXCLUDED.ge_limit,
                    icon = EXCLUDED.icon,
                    last_updated = EXCLUDED.last_updated
            ''', items_to_insert)
            
            # Update last sync time in metadata
            cursor.execute("UPDATE price_polling_metadata SET last_item_sync_time = ? WHERE id = 1", (now,))
            
            conn.commit()
            return {"message": f"Synced {len(items_to_insert)} items", "count": len(items_to_insert)}
    
    @staticmethod
    def get_all_items() -> List[Dict]:
        """Get all items from database"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def search_items(query: str) -> List[Dict]:
        """Search items by name - case insensitive, exact match first"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM items 
                WHERE LOWER(name) LIKE LOWER(?)
                ORDER BY 
                    CASE WHEN LOWER(TRIM(name)) = LOWER(TRIM(?)) THEN 0 ELSE 1 END,
                    name
            ''', (f'%{query}%', query))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_item_by_id(item_id: int) -> Optional[Dict]:
        """Get single item by ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def calculate_profit(buy_price: int, sell_price: int, quantity: int = 1) -> Dict:
        """Calculate profit for an item"""
        if not buy_price or not sell_price:
            return {"profit": None, "roi": None, "ge_tax": 0}
        
        # Calculate GE tax (2% on items > 50gp, capped at 5M)
        ge_tax = calculate_ge_tax(sell_price)
        
        # Calculate profit per item
        profit_per_item = sell_price - buy_price - ge_tax
        
        # Calculate ROI
        roi = (profit_per_item / buy_price * 100) if buy_price > 0 else 0
        
        # Total profit
        total_profit = profit_per_item * quantity
        
        return {
            "profit_per_item": profit_per_item,
            "total_profit": total_profit,
            "roi": round(roi, 2),
            "ge_tax": ge_tax
        }
    
    @staticmethod
    def get_volume_indicator(volume: Optional[int]) -> str:
        """Get volume indicator emoji"""
        if volume is None or volume == 0:
            return "⚪ N/A"
        
        if volume >= 50000:
            return "🟢 HIGH"
        elif volume >= 5000:
            return "🟡 MED"
        else:
            return "🔴 LOW"

    @staticmethod
    def get_item_with_prices(item_id: int, cash: Optional[int] = None) -> Optional[Dict]:
        """Get a single item enriched with live price data"""
        item = ItemService.get_item_by_id(item_id)
        if not item:
            return None

        latest_data = fetch_latest_prices(use_cache=True)
        volume_data = fetch_volume_data(use_cache=True)
        volume_5m_data = fetch_5m_volume_data(use_cache=True)

        item_id_str = str(item_id)

        # Get prices
        buy_price = None
        sell_price = None
        if item_id_str in latest_data.get('data', {}):
            price_data = latest_data['data'][item_id_str]
            buy_price = price_data.get('low')
            sell_price = price_data.get('high')

        # Get 1h volume
        volume = 0
        if 'data' in volume_data and item_id_str in volume_data['data']:
            vol_data = volume_data['data'][item_id_str]
            volume = (vol_data.get('highPriceVolume', 0) or 0) + (vol_data.get('lowPriceVolume', 0) or 0)

        # Get 5m volume (for Erebus score)
        volume_5m = 0
        if 'data' in volume_5m_data and item_id_str in volume_5m_data['data']:
            vol_5m = volume_5m_data['data'][item_id_str]
            volume_5m = (vol_5m.get('highPriceVolume', 0) or 0) + (vol_5m.get('lowPriceVolume', 0) or 0)

        # Compute momentum from price snapshots
        raw_1h = volume_data.get('data', {}).get(item_id_str, {})
        raw_5m = volume_5m_data.get('data', {}).get(item_id_str, {})
        momentum = ItemService.calculate_momentum(buy_price, sell_price, raw_1h, raw_5m)

        # Calculate profit
        profit_data = ItemService.calculate_profit(buy_price, sell_price) if buy_price and sell_price else {}
        profit = profit_data.get('profit_per_item', 0)
        roi = profit_data.get('roi', 0)
        ge_tax = profit_data.get('ge_tax', 0)

        ge_limit = item.get('ge_limit') or 0
        profit_at_limit = profit * ge_limit if profit and ge_limit else 0

        max_qty = ge_limit
        your_profit = profit_at_limit
        if cash is not None and buy_price and ge_limit > 0:
            affordable_qty = cash // buy_price
            if affordable_qty < ge_limit:
                max_qty = affordable_qty
                your_profit = profit * affordable_qty

        # Get long-term metrics
        from app.services.data_quality_service import DataQualityService
        trajectory = DataQualityService.get_historical_trajectory(item_id)
        volatility = DataQualityService.get_historical_volatility(item_id)
        max_drawdown_30d = DataQualityService.get_historical_drawdown(item_id)
        price_percentile_30d = DataQualityService.get_historical_percentile(item_id)
        crash_risk_score = DataQualityService.get_historical_crash_risk(item_id)

        risk_to_reward_ratio = None
        if max_drawdown_30d is not None and roi is not None:
            risk_to_reward_ratio = round(max_drawdown_30d / roi, 2) if roi > 0 else 99.9

        expected_profit_7d = None
        expected_roi_7d = None
        expected_sell_price = None
        long_term_score = None

        if trajectory is not None and trajectory > 0.0:
            expected_sell_price = int(sell_price * (1 + trajectory / 100)) if sell_price else None
            if expected_sell_price and buy_price:
                tax = calculate_ge_tax(expected_sell_price)
                expected_profit_7d = expected_sell_price - buy_price - tax
                if buy_price > 0:
                    expected_roi_7d = round((expected_profit_7d / buy_price) * 100, 2)
                else:
                    expected_roi_7d = 0.0

        if buy_price and sell_price:
            long_term_score = ItemService.calculate_long_term_score(
                profit=profit,
                roi=roi,
                volume=volume,
                trajectory=trajectory,
                volatility=volatility,
            )

        # Get highalch profit (subtract buy_price and Nature Rune price)
        # Nature Rune ID is 561
        nat_rune_data = latest_data.get("data", {}).get("561", {})
        nat_rune_price = nat_rune_data.get("low") or nat_rune_data.get("high") or 90
        
        highalch_profit = None
        highalch_value = item.get("highalch") or 0
        if highalch_value > 0 and buy_price is not None:
            highalch_profit = highalch_value - (buy_price + nat_rune_price)

        score = ItemService.calculate_score(
            profit=profit, roi=roi, volume=volume,
            ge_limit=ge_limit, buy_price=buy_price or 0, cash=cash,
            momentum=momentum,
        )

        risk_adjusted_score = score
        if crash_risk_score is not None:
            risk_adjusted_score = max(0.0, score - crash_risk_score * 0.35)

        return {
            "id": item['id'],
            "name": item['name'],
            "members": item['members'],
            "examine": item.get('examine'),
            "ge_limit": ge_limit,
            "highalch": item.get('highalch'),
            "lowalch": item.get('lowalch'),
            "buy_price": buy_price,
            "sell_price": sell_price,
            "profit": profit,
            "roi": roi,
            "ge_tax": ge_tax,
            "volume": volume,
            "volume_indicator": ItemService.get_volume_indicator(volume),
            "profit_at_limit": profit_at_limit,
            "max_qty": max_qty,
            "your_profit": your_profit,
            "score": score,
            "risk_adjusted_score": risk_adjusted_score,
            "crash_risk_score": crash_risk_score,
            "max_drawdown_30d": max_drawdown_30d,
            "price_percentile_30d": price_percentile_30d,
            "risk_to_reward_ratio": risk_to_reward_ratio,
            "secondary_score": ItemService.calculate_erebus_score(
                buy_price=buy_price or 0,
                sell_price=sell_price or 0,
                volume_5m=volume_5m,
                volume_1h=volume,
            ),
            "trajectory": trajectory,
            "volatility": volatility,
            "expected_sell_price": expected_sell_price,
            "expected_profit_7d": expected_profit_7d,
            "expected_roi_7d": expected_roi_7d,
            "long_term_score": long_term_score,
            "highalch_profit": highalch_profit,
            "nature_rune_price": nat_rune_price,
        }