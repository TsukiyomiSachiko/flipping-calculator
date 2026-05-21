from typing import List, Dict
from app.utils.database import get_db
from app.utils.api_client import fetch_latest_prices, fetch_volume_data, fetch_5m_volume_data
from app.services.item_service import ItemService, calculate_ge_tax
from app.services.data_quality_service import DataQualityService
from app.services.settings_service import SettingsService

class FlipService:
    @staticmethod
    def get_profitable_flips(account_id: int, params: Dict) -> List[Dict]:
        """Get profitable flips based on search parameters"""
        # Auto-fetch cash from user settings if not provided
        if params.get('cash') is None:
            user_settings = SettingsService.get_settings(account_id)
            params['cash'] = user_settings.get('available_cash', 0)
        
        # Fetch price and volume data
        latest_data = fetch_latest_prices(use_cache=True)
        volume_data = fetch_volume_data(use_cache=True)
        volume_5m_data = fetch_5m_volume_data(use_cache=True)
        
        # Get all items from database
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items')
            items = [dict(row) for row in cursor.fetchall()]
        
        # Merge price and volume data
        profitable_items = []
        
        for item in items:
            item_id = str(item['id'])
            
            # Get prices from /latest
            if item_id not in latest_data['data']:
                continue
            
            price_data = latest_data['data'][item_id]
            buy_price = price_data.get('low')  # Flipper's buy price (Wiki "low")
            sell_price = price_data.get('high')  # Flipper's sell price (Wiki "high")
            
            if not buy_price or not sell_price:
                continue
            
            # Get volume from /1h if available
            volume = 0
            if 'data' in volume_data and item_id in volume_data['data']:
                vol_data = volume_data['data'][item_id]
                high_vol = vol_data.get('highPriceVolume', 0) or 0
                low_vol = vol_data.get('lowPriceVolume', 0) or 0
                volume = high_vol + low_vol
            
            # Ensure volume is an integer
            volume = int(volume) if volume else 0
            
            # Compute momentum from price snapshots
            raw_1h = volume_data.get('data', {}).get(item_id, {})
            raw_5m = volume_5m_data.get('data', {}).get(item_id, {})
            momentum = ItemService.calculate_momentum(buy_price, sell_price, raw_1h, raw_5m)

            # Calculate profit
            profit_data = ItemService.calculate_profit(buy_price, sell_price)
            profit = profit_data['profit_per_item']
            roi = profit_data['roi']
            
            # Must be profitable
            if profit <= 0:
                continue
            
            # Apply filters
            if profit < params.get('min_profit', 0):
                continue
            
            if roi < params.get('min_roi', 0):
                continue
            
            max_roi = params.get('max_roi')
            if max_roi is not None and roi > max_roi:
                continue
            
            # Volume filters
            if params.get('high_volume_only', False) and volume < 50000:
                continue
            
            min_volume = params.get('min_volume', 0)
            if min_volume > 0 and volume < min_volume:
                continue
            
            # Calculate profit at limit
            ge_limit = item['ge_limit'] or 0
            profit_at_limit = profit * ge_limit if ge_limit > 0 else 0
            
            # Grindable filter: volume >= 10% of GE limit (can grind 2.5x per day)
            # GE limit resets every 4 hours (6 cycles/day)
            # 10% volume/hour means 40% of limit every 4 hours = 2.4x daily limit
            if params.get('require_grindable', False):
                required_volume = ge_limit * 0.10
                
                # Skip if limit too low (hard to flip items with small limits)
                if ge_limit < 50:
                    continue
                # Skip if no volume
                if volume is None or volume == 0:
                    continue
                # Skip if volume too low for the limit
                if volume < required_volume:
                    continue
            
            # Min limit profit filter
            min_limit_profit = params.get('min_limit_profit', 0)
            if min_limit_profit > 0 and profit_at_limit < min_limit_profit:
                continue
            
            # Cash constraint
            cash = params.get('cash')
            if cash is not None and buy_price > cash:
                continue
            
            # Members filter
            if params.get('members_only', False) and not item['members']:
                continue
            
            # F2P filter
            if params.get('f2p_only', False) and item['members']:
                continue
            
            # Build result
            max_qty = ge_limit
            your_profit = profit_at_limit
            
            if cash is not None and ge_limit > 0:
                affordable_qty = cash // buy_price
                if affordable_qty < ge_limit:
                    max_qty = affordable_qty
                    your_profit = profit * affordable_qty

            # Get 5m volume for Erebus score
            volume_5m = 0
            if 'data' in volume_5m_data and item_id in volume_5m_data['data']:
                vol_5m = volume_5m_data['data'][item_id]
                volume_5m = (vol_5m.get('highPriceVolume', 0) or 0) + (vol_5m.get('lowPriceVolume', 0) or 0)

            # Get long-term metrics
            trajectory = DataQualityService.get_historical_trajectory(item['id'])
            volatility = DataQualityService.get_historical_volatility(item['id'])
            max_drawdown_30d = DataQualityService.get_historical_drawdown(item['id'])
            price_percentile_30d = DataQualityService.get_historical_percentile(item['id'])
            crash_risk_score = DataQualityService.get_historical_crash_risk(item['id'])

            risk_to_reward_ratio = None
            if max_drawdown_30d is not None and roi is not None:
                risk_to_reward_ratio = round(max_drawdown_30d / roi, 2) if roi > 0 else 99.9

            expected_profit_7d = None
            expected_roi_7d = None
            expected_sell_price = None

            if trajectory is not None and trajectory > 0.0:
                expected_sell_price = int(sell_price * (1 + trajectory / 100))
                
                tax = calculate_ge_tax(expected_sell_price)
                expected_profit_7d = expected_sell_price - buy_price - tax
                if buy_price > 0:
                    expected_roi_7d = round((expected_profit_7d / buy_price) * 100, 2)
                else:
                    expected_roi_7d = 0.0

            score = ItemService.calculate_score(
                profit=profit, roi=roi, volume=volume,
                ge_limit=ge_limit, buy_price=buy_price, cash=cash,
                momentum=momentum,
            )
            
            risk_adjusted_score = score
            if crash_risk_score is not None:
                risk_adjusted_score = max(0.0, score - crash_risk_score * 0.35)

            profitable_items.append({
                "id": item['id'],
                "name": item['name'],
                "members": item['members'],
                "buy_price": buy_price,
                "sell_price": sell_price,
                "profit": profit,
                "limit_profit": profit_at_limit,  # Add this for frontend compatibility
                "roi": roi,
                "volume": volume,
                "volume_indicator": ItemService.get_volume_indicator(volume),
                "ge_limit": ge_limit,
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
                    buy_price=buy_price,
                    sell_price=sell_price,
                    volume_5m=volume_5m,
                    volume_1h=volume,
                ),
                "long_term_score": ItemService.calculate_long_term_score(
                    profit=profit,
                    roi=roi,
                    volume=volume,
                    trajectory=trajectory,
                    volatility=volatility,
                ),
                "trajectory": trajectory,
                "volatility": volatility,
                "expected_sell_price": expected_sell_price,
                "expected_profit_7d": expected_profit_7d,
                "expected_roi_7d": expected_roi_7d,
                "price_change_pct": 0,  # Needed for quality check (will be enriched if momentum available)
            })
        
        # Always calculate quality scores for all items
        for item in profitable_items:
            quality_data = DataQualityService.calculate_data_quality_score(
                item_id=item['id'],
                buy_price=item['buy_price'],
                sell_price=item['sell_price'],
                profit=item['profit'],
                volume_1h=item['volume'],
                ge_limit=item['ge_limit'],
                price_change_pct=item.get('price_change_pct', 0),
            )
            item['quality_score'] = quality_data['quality_score']
            item['quality_tier'] = quality_data['quality_tier']
            item['quality_flags'] = quality_data['flags']
        
        # Apply quality filtering if enabled (filters out low scores)
        enable_quality_filter = params.get('enable_quality_filter', False)
        if enable_quality_filter:
            min_quality = params.get('min_quality_score', 50.0)
            profitable_items = [
                item for item in profitable_items
                if item['quality_score'] >= min_quality
            ]
        
        # Sort items
        sort_by = params.get('sort_by', 'profit')
        if sort_by == 'profit':
            profitable_items.sort(key=lambda x: x['profit'], reverse=True)
        elif sort_by == 'roi':
            profitable_items.sort(key=lambda x: x['roi'], reverse=True)
        elif sort_by == 'limit':
            profitable_items.sort(key=lambda x: x['profit_at_limit'], reverse=True)
        elif sort_by == 'volume':
            profitable_items.sort(key=lambda x: x['volume'] or 0, reverse=True)
        elif sort_by == 'score':
            profitable_items.sort(key=lambda x: x['score'], reverse=True)
        elif sort_by == 'risk_adjusted':
            profitable_items.sort(key=lambda x: x['risk_adjusted_score'], reverse=True)
        elif sort_by == 'crash_risk':
            profitable_items.sort(key=lambda x: (x.get('crash_risk_score') is None, x.get('crash_risk_score') or 999.0))
        elif sort_by == 'erebus':
            profitable_items.sort(key=lambda x: (x['secondary_score'] is not None, x['secondary_score'] or 0), reverse=True)
        elif sort_by == 'long_term':
            # Filter out bad long term scores first
            profitable_items = [item for item in profitable_items if item['long_term_score'] > 0]
            profitable_items.sort(key=lambda x: x['long_term_score'], reverse=True)
        elif sort_by == 'quality':
            profitable_items.sort(key=lambda x: (x.get('quality_score') is not None, x.get('quality_score') or 0), reverse=True)
        
        # Limit results
        limit = params.get('limit', 20)
        return profitable_items[:limit]
    
    @staticmethod
    def get_flip_stats() -> Dict:
        """Get statistics about available flips"""
        latest_data = fetch_latest_prices(use_cache=True)
        volume_data = fetch_volume_data(use_cache=True)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM items')
            total_items = cursor.fetchone()['count']
        
        items_with_prices = len(latest_data.get('data', {}))
        items_with_volume = len(volume_data.get('data', {})) if volume_data else 0
        
        return {
            "total_items": total_items,
            "items_with_prices": items_with_prices,
            "items_with_volume": items_with_volume
        }