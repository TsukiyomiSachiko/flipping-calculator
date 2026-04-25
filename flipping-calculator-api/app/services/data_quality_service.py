"""
Data Quality Service - Detects manipulated/suspicious price data

Implements statistical outlier detection using Z-score analysis, minimum price
thresholds, spread sanity checks, and volume-to-price correlation to filter
out manipulated or unreliable items from trending and flip recommendations.

Quality Score: 0-100 where higher = more trustworthy
- 80-100: High quality (green) - reliable data
- 50-79:  Medium quality (yellow) - use with caution  
- 0-49:   Low quality (red) - likely manipulated/stale
"""

import math
import logging
from typing import Dict, Optional, List, Tuple
from statistics import mean, stdev
from datetime import datetime, timedelta, timezone
from app.utils.database import get_db

logger = logging.getLogger(__name__)

class DataQualityService:
    """Analyzes price data quality and detects manipulation"""

    # Thresholds for quality scoring
    MIN_ABSOLUTE_PRICE = 50  # Items under 50gp often manipulated
    MAX_SPREAD_MULTIPLIER = 10.0  # Spread >1000% of buy price is suspicious
    MIN_VOLUME_FOR_PRICE_MOVE = 100  # Large price moves need minimum volume
    
    # Z-score thresholds
    EXTREME_ZSCORE = 3.0  # >3 standard deviations = extreme outlier
    SUSPICIOUS_ZSCORE = 2.0  # >2 standard deviations = suspicious

    # In-memory TTL Cache
    _volatility_cache: Dict[int, float] = {}
    _stability_cache: Dict[int, float] = {}
    _cache_timestamp: Optional[datetime] = None
    CACHE_TTL_HOURS = 1

    @classmethod
    def calculate_data_quality_score(
        cls,
        item_id: int,
        buy_price: int,
        sell_price: int,
        profit: int,
        volume_1h: int,
        ge_limit: int,
        price_change_pct: float,
        historical_volatility: Optional[float] = None,
    ) -> Dict:
        """
        Calculate comprehensive data quality score (0-100).
        
        Returns dict with:
        - quality_score: 0-100 overall score
        - flags: list of warning strings
        - quality_tier: 'high', 'medium', or 'low'
        - details: dict of sub-scores for debugging
        """
        flags = []
        sub_scores = {}
        
        # 1. Absolute price floor check (20% weight)
        price_floor_score = cls._check_price_floor(
            buy_price, sell_price
        )
        sub_scores['price_floor'] = price_floor_score
        if price_floor_score < 50:
            flags.append(f"Low absolute prices (buy: {buy_price}gp, sell: {sell_price}gp)")
        
        # 2. Spread sanity check (25% weight)
        spread_score, spread_flag = cls._check_spread_sanity(
            buy_price, sell_price, profit
        )
        sub_scores['spread_sanity'] = spread_score
        if spread_flag:
            flags.append(spread_flag)
        
        # 3. Volume-to-price correlation (20% weight)
        volume_score, volume_flag = cls._check_volume_correlation(
            price_change_pct, volume_1h
        )
        sub_scores['volume_correlation'] = volume_score
        if volume_flag:
            flags.append(volume_flag)
        
        # 4. Historical volatility Z-score (20% weight)
        volatility_score, volatility_flag = cls._check_volatility_zscore(
            item_id, price_change_pct, historical_volatility
        )
        sub_scores['volatility_zscore'] = volatility_score
        if volatility_flag:
            flags.append(volatility_flag)
        
        # 5. Price stability check (15% weight)
        stability_score, stability_flag = cls._check_price_stability(
            item_id, buy_price, sell_price
        )
        sub_scores['price_stability'] = stability_score
        if stability_flag:
            flags.append(stability_flag)
        
        # Calculate weighted overall score
        quality_score = (
            price_floor_score * 0.20 +
            spread_score * 0.25 +
            volume_score * 0.20 +
            volatility_score * 0.20 +
            stability_score * 0.15
        )
        
        # Determine quality tier
        if quality_score >= 80:
            tier = 'high'
        elif quality_score >= 50:
            tier = 'medium'
        else:
            tier = 'low'
        
        return {
            'quality_score': round(quality_score, 1),
            'quality_tier': tier,
            'flags': flags,
            'details': sub_scores,
        }
    
    @classmethod
    def _check_price_floor(cls, buy_price: int, sell_price: int) -> float:
        """
        Check if prices meet minimum absolute thresholds.
        
        Items under 50gp are often manipulated or inactive.
        Returns score 0-100.
        """
        min_price = min(buy_price, sell_price)
        
        if min_price < 10:
            return 0
        elif min_price < 25:
            return 30
        elif min_price < cls.MIN_ABSOLUTE_PRICE:
            return 60
        else:
            return 100
    
    @classmethod
    def _check_spread_sanity(
        cls, buy_price: int, sell_price: int, profit: int
    ) -> Tuple[float, Optional[str]]:
        """
        Check if buy/sell spread is realistic.
        
        Spreads >1000% often indicate stale/manipulated data.
        Returns (score 0-100, warning_message)
        """
        if buy_price <= 0:
            return 0, "Invalid buy price"
        
        spread_multiplier = sell_price / buy_price
        spread_pct = (profit / buy_price) * 100
        
        # Impossible spreads (1gp buy, 100gp+ sell on junk items)
        if spread_multiplier > cls.MAX_SPREAD_MULTIPLIER:
            return 0, f"Impossible spread: {spread_pct:.0f}% ({buy_price}gp → {sell_price}gp)"
        
        # Suspicious spreads
        if spread_multiplier > 5.0:
            return 30, f"Very wide spread: {spread_pct:.0f}% (likely stale data)"
        
        # Questionable spreads
        if spread_multiplier > 2.0:
            return 60, f"Wide spread: {spread_pct:.0f}% (check price recency)"
        
        # Healthy spreads
        return 100, None
    
    @classmethod
    def _check_volume_correlation(
        cls, price_change_pct: float, volume_1h: int
    ) -> Tuple[float, Optional[str]]:
        """
        Check if volume supports the price movement.
        
        Large price changes should require proportional volume.
        Returns (score 0-100, warning_message)
        """
        abs_change = abs(price_change_pct)
        
        # No significant price movement - volume doesn't matter
        if abs_change < 1.0:
            return 100, None
        
        # Calculate expected minimum volume for this price move
        # >5% change should need >1000 volume, >10% needs >5000, etc.
        if abs_change > 20:
            expected_min_volume = 20000
        elif abs_change > 10:
            expected_min_volume = 5000
        elif abs_change > 5:
            expected_min_volume = 1000
        else:
            expected_min_volume = cls.MIN_VOLUME_FOR_PRICE_MOVE
        
        # Score based on volume sufficiency
        volume_ratio = volume_1h / expected_min_volume
        
        if volume_ratio < 0.2:
            return 20, f"Price moved {price_change_pct:+.1f}% on only {volume_1h} volume"
        elif volume_ratio < 0.5:
            return 50, f"Low volume ({volume_1h}) for {price_change_pct:+.1f}% price move"
        elif volume_ratio < 1.0:
            return 75, None
        else:
            return 100, None
    
    @classmethod
    def _check_volatility_zscore(
        cls,
        item_id: int,
        current_change_pct: float,
        historical_volatility: Optional[float],
    ) -> Tuple[float, Optional[str]]:
        """
        Calculate Z-score of current price change vs historical volatility.
        
        Z-score > 3 means >3 standard deviations = extreme outlier.
        Returns (score 0-100, warning_message)
        """
        # If no historical volatility provided, calculate from price_history
        if historical_volatility is None:
            historical_volatility = cls._calculate_historical_volatility(item_id)
        
        # If still no data, assume medium quality
        if historical_volatility is None or historical_volatility == 0:
            return 70, None
        
        # Calculate Z-score
        z_score = abs(current_change_pct) / historical_volatility
        
        # Score based on Z-score
        if z_score > cls.EXTREME_ZSCORE:
            return 20, f"Extreme outlier: {z_score:.1f}σ (>{cls.EXTREME_ZSCORE}σ typical)"
        elif z_score > cls.SUSPICIOUS_ZSCORE:
            return 50, f"Suspicious movement: {z_score:.1f}σ (>{cls.SUSPICIOUS_ZSCORE}σ typical)"
        elif z_score > 1.5:
            return 75, None
        else:
            return 100, None
    
    @classmethod
    def _calculate_historical_volatility(
        cls, item_id: int, days: int = 7
    ) -> Optional[float]:
        """
        Calculate standard deviation of hourly price changes over past N days.
        Uses in-memory cache if available to prevent N+1 query problems.
        Returns volatility as % or None if insufficient data.
        """
        # Check cache
        if cls._cache_timestamp and (datetime.now(timezone.utc) - cls._cache_timestamp).total_seconds() < cls.CACHE_TTL_HOURS * 3600:
            if item_id in cls._volatility_cache:
                return cls._volatility_cache[item_id]

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Get hourly price snapshots for past N days
                since_datetime = datetime.now(timezone.utc) - timedelta(days=days)
                
                cursor.execute('''
                    SELECT timestamp, price_high, price_low
                    FROM price_history
                    WHERE item_id = ?
                    AND timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (item_id, since_datetime))
                
                rows = cursor.fetchall()
                
                if len(rows) < 24:  # Need at least 24 hours of data
                    cls._volatility_cache[item_id] = None
                    return None
                
                # Calculate hourly midpoint price changes
                changes = []
                for i in range(1, len(rows)):
                    prev_high = rows[i-1]['price_high']
                    prev_low = rows[i-1]['price_low']
                    curr_high = rows[i]['price_high']
                    curr_low = rows[i]['price_low']
                    
                    # Skip if any price is None
                    if prev_high is None or prev_low is None or curr_high is None or curr_low is None:
                        continue
                    
                    prev_mid = (prev_high + prev_low) / 2
                    curr_mid = (curr_high + curr_low) / 2
                    
                    if prev_mid > 0:
                        pct_change = ((curr_mid - prev_mid) / prev_mid) * 100
                        changes.append(pct_change)
                
                if len(changes) < 20:
                    cls._volatility_cache[item_id] = None
                    return None
                
                # Return standard deviation
                vol = stdev(changes)
                cls._volatility_cache[item_id] = vol
                return vol
                
        except Exception as e:
            logger.error(f"Error calculating volatility for item {item_id}: {e}")
            return None
    
    @classmethod
    def _check_price_stability(
        cls, item_id: int, buy_price: int, sell_price: int
    ) -> Tuple[float, Optional[str]]:
        """
        Check if current prices are consistent with recent history (24h ago).
        Uses in-memory cache to retrieve the 24h average.
        Detects sudden 10x+ spikes that indicate manipulation.
        Returns (score 0-100, warning_message)
        """
        avg_historical_mid = None
        is_cached = False
        
        # Check cache
        if cls._cache_timestamp and (datetime.now(timezone.utc) - cls._cache_timestamp).total_seconds() < cls.CACHE_TTL_HOURS * 3600:
            if item_id in cls._stability_cache:
                avg_historical_mid = cls._stability_cache[item_id]
                is_cached = True

        if not is_cached:
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    
                    # Get prices from 24 hours ago
                    day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
                    
                    # Added an upper bound to prevent full table scanning if exact 24h is missing
                    upper_bound = day_ago + timedelta(hours=2)
                    
                    cursor.execute('''
                        SELECT price_high, price_low
                        FROM price_history
                        WHERE item_id = ?
                        AND timestamp >= ?
                        AND timestamp <= ?
                        ORDER BY timestamp ASC
                        LIMIT 10
                    ''', (item_id, day_ago, upper_bound))
                    
                    historical_rows = cursor.fetchall()
                    
                    if len(historical_rows) >= 5:
                        historical_mids = []
                        for row in historical_rows:
                            if row['price_high'] is not None and row['price_low'] is not None:
                                historical_mids.append((row['price_high'] + row['price_low']) / 2)
                        
                        if len(historical_mids) >= 5:
                            avg_historical_mid = mean(historical_mids)
                            cls._stability_cache[item_id] = avg_historical_mid
                        else:
                            cls._stability_cache[item_id] = None
                    else:
                        cls._stability_cache[item_id] = None
                        
            except Exception as e:
                logger.error(f"Error checking price stability for item {item_id}: {e}")
                return 70, None

        if not avg_historical_mid or avg_historical_mid == 0:
            return 70, None
        
        current_mid = (buy_price + sell_price) / 2
        
        # Check for sudden spikes
        spike_multiplier = current_mid / avg_historical_mid
        
        if spike_multiplier > 10 or spike_multiplier < 0.1:
            return 10, f"Price spiked {spike_multiplier:.1f}x in 24h (manipulation likely)"
        elif spike_multiplier > 5 or spike_multiplier < 0.2:
            return 40, f"Price moved {spike_multiplier:.1f}x in 24h (suspicious)"
        elif spike_multiplier > 2 or spike_multiplier < 0.5:
            return 70, None
        else:
            return 100, None
    
    @classmethod
    def filter_suspicious_items(
        cls, items: List[Dict], min_quality_score: float = 50.0
    ) -> List[Dict]:
        """
        Filter out items with quality scores below threshold.
        
        Enriches each item with quality_data and filters by min_quality_score.
        """
        enriched_items = []
        
        for item in items:
            # Calculate quality score for this item
            quality_data = cls.calculate_data_quality_score(
                item_id=item.get('id'),
                buy_price=item.get('buy_price', 0),
                sell_price=item.get('sell_price', 0),
                profit=item.get('profit', 0),
                volume_1h=item.get('volume', 0),
                ge_limit=item.get('ge_limit', 0),
                price_change_pct=item.get('price_change_pct', 0),
            )
            
            # Add quality data to item
            item['quality_score'] = quality_data['quality_score']
            item['quality_tier'] = quality_data['quality_tier']
            item['quality_flags'] = quality_data['flags']
            
            # Filter based on minimum threshold
            if quality_data['quality_score'] >= min_quality_score:
                enriched_items.append(item)
        
        return enriched_items

    @classmethod
    def prewarm_cache(cls):
        """
        Precalculate and cache historical metrics for all items.
        Should be run periodically via a background task.
        """
        from app.services.item_service import ItemService
        logger.info("Pre-warming DataQualityService cache for all items...")
        
        try:
            items = ItemService.get_all_items()
            
            new_volatility = {}
            new_stability = {}
            
            day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            upper_bound = day_ago + timedelta(hours=2)
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            
            with get_db() as conn:
                cursor = conn.cursor()
                for item in items:
                    item_id = item['id']
                    
                    # 1. Precalculate Volatility
                    cursor.execute('''
                        SELECT timestamp, price_high, price_low
                        FROM price_history
                        WHERE item_id = ?
                        AND timestamp >= ?
                        ORDER BY timestamp ASC
                    ''', (item_id, week_ago))
                    rows = cursor.fetchall()
                    if len(rows) >= 24:
                        changes = []
                        for i in range(1, len(rows)):
                            prev_high = rows[i-1]['price_high']
                            prev_low = rows[i-1]['price_low']
                            curr_high = rows[i]['price_high']
                            curr_low = rows[i]['price_low']
                            
                            if prev_high is None or prev_low is None or curr_high is None or curr_low is None:
                                continue
                            
                            prev_mid = (prev_high + prev_low) / 2
                            curr_mid = (curr_high + curr_low) / 2
                            
                            if prev_mid > 0:
                                pct_change = ((curr_mid - prev_mid) / prev_mid) * 100
                                changes.append(pct_change)
                        
                        if len(changes) >= 20:
                            new_volatility[item_id] = stdev(changes)
                    
                    # 2. Precalculate Stability Baseline
                    cursor.execute('''
                        SELECT price_high, price_low
                        FROM price_history
                        WHERE item_id = ?
                        AND timestamp >= ?
                        AND timestamp <= ?
                        ORDER BY timestamp ASC
                        LIMIT 10
                    ''', (item_id, day_ago, upper_bound))
                    
                    hist_rows = cursor.fetchall()
                    if len(hist_rows) >= 5:
                        hist_mids = [(r['price_high'] + r['price_low'])/2 for r in hist_rows if r['price_high'] is not None and r['price_low'] is not None]
                        if len(hist_mids) >= 5:
                            new_stability[item_id] = mean(hist_mids)
            
            # Atomically swap caches
            cls._volatility_cache = new_volatility
            cls._stability_cache = new_stability
            cls._cache_timestamp = datetime.now(timezone.utc)
            
            logger.info(f"✅ DataQualityService cache pre-warmed. Volatility: {len(new_volatility)} items, Stability: {len(new_stability)} items.")
            
        except Exception as e:
            logger.error(f"Failed to pre-warm DataQualityService cache: {e}", exc_info=True)