"""
Fill Rate Monitoring Service

Tracks buy and sell offer fill rates to help users make data-driven decisions
about when to cancel slow-filling offers.

Calculates:
- Time since offer started
- Time since last activity
- Fill rate (items/hour)
- Expected fill rate based on volume
- Recommendation status (Keep/Monitor/Cancel)
"""

from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
from app.utils.database import get_db


class FillRateService:
    """Service for tracking and analyzing fill rates of buy/sell offers"""
    
    # Conservative multiplier for expected fill rate (volume / 10)
    EXPECTED_FILL_MULTIPLIER = 10
    
    # Recommendation thresholds
    KEEP_THRESHOLD = 0.50  # 50% of expected rate
    MONITOR_THRESHOLD = 0.20  # 20% of expected rate
    STAGNANT_HOURS = 2  # Hours before flagging stagnant offers
    PROGRESS_THRESHOLD = 0.10  # 10% progress in last hour is good
    
    @staticmethod
    def calculate_fill_metrics(flip: Dict, current_volume: Optional[int] = None) -> Dict:
        """
        Calculate fill rate metrics for a flip
        
        Args:
            flip: Flip record from database
            current_volume: Current hourly volume for the item (optional)
        
        Returns:
            Dict with metrics and recommendation
        """
        def ensure_aware(dt):
            if dt is None:
                return None
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        now = datetime.now(timezone.utc)
        metrics = {
            'buy_metrics': None,
            'sell_metrics': None,
            'overall_status': 'unknown'
        }
        
        # Retroactive fix for legacy data:
        # If we have items bought but last_buy_at is NULL, use buy_time as fallback
        last_buy = ensure_aware(flip.get('last_buy_at'))
        if last_buy is None and flip['quantity_total'] > 0:
            last_buy = ensure_aware(flip.get('buy_time'))

        # Calculate buy metrics if offer is pending
        if flip['status'] == 'pending' or flip['status'] == 'partially_completed':
            buy_started = ensure_aware(flip.get('buy_offer_started_at'))
            
            # If we don't have a specific offer start time, use buy_time
            if not buy_started:
                buy_started = ensure_aware(flip.get('buy_time'))
            
            if buy_started:
                buy_metrics = FillRateService._calculate_buy_metrics(
                    flip=flip,
                    now=now,
                    buy_started=buy_started,
                    last_buy=last_buy,
                    current_volume=current_volume
                )
                metrics['buy_metrics'] = buy_metrics
        
        # Calculate sell metrics if have inventory
        if flip['status'] == 'partially_completed' or flip['status'] == 'completed':
            sell_started = ensure_aware(flip.get('sell_offer_started_at'))
            last_sell = ensure_aware(flip.get('last_sell_at'))
            
            if sell_started and flip['status'] == 'partially_completed':
                sell_metrics = FillRateService._calculate_sell_metrics(
                    flip=flip,
                    now=now,
                    sell_started=sell_started,
                    last_sell=last_sell,
                    current_volume=current_volume
                )
                metrics['sell_metrics'] = sell_metrics
        
        # Determine overall status
        metrics['overall_status'] = FillRateService._determine_overall_status(
            metrics['buy_metrics'],
            metrics['sell_metrics']
        )
        
        return metrics
    
    @staticmethod
    def _calculate_buy_metrics(flip: Dict, now: datetime, buy_started: datetime, 
                               last_buy: Optional[datetime], current_volume: Optional[int]) -> Dict:
        """Calculate metrics for buy offers"""
        # Time calculations
        total_hours = (now - buy_started).total_seconds() / 3600
        hours_since_last = (now - last_buy).total_seconds() / 3600 if last_buy else total_hours
        
        # Quantity calculations
        # For buy metrics: quantity_bought = how much we've successfully purchased so far
        quantity_bought = flip['quantity_total']  # Total purchased so far
        intended_quantity = flip.get('intended_quantity') or flip['quantity_total']
        
        # Fill rate (items/hour)
        actual_fill_rate = quantity_bought / total_hours if total_hours > 0 else 0
        
        # Expected fill rate (conservative: volume / 10)
        expected_fill_rate = 0
        if current_volume:
            expected_fill_rate = current_volume / FillRateService.EXPECTED_FILL_MULTIPLIER
        
        # Fill progress
        fill_progress = quantity_bought / intended_quantity if intended_quantity > 0 else 0
        
        # Recent progress (last hour)
        recent_activity = False
        if last_buy and hours_since_last < 1.0:
            # If we bought something in the last hour, that's "recent activity"
            # We treat this as "good" regardless of the absolute quantity 
            # to prevent discouraging the user when things start moving.
            recent_activity = True
        
        # Recommendation
        recommendation = FillRateService._get_buy_recommendation(
            actual_fill_rate=actual_fill_rate,
            expected_fill_rate=expected_fill_rate,
            fill_progress=fill_progress,
            total_hours=total_hours,
            hours_since_last=hours_since_last,
            recent_activity=recent_activity
        )
        
        return {
            'offer_age_hours': round(total_hours, 1),
            'hours_since_last_buy': round(hours_since_last, 1),
            'quantity_bought': quantity_bought,
            'intended_quantity': intended_quantity,
            'fill_progress': round(fill_progress * 100, 1),  # as percentage
            'actual_fill_rate': round(actual_fill_rate, 2),
            'expected_fill_rate': round(expected_fill_rate, 2),
            'recommendation': recommendation['status'],
            'recommendation_text': recommendation['text'],
            'badge_color': recommendation['color']
        }
    
    @staticmethod
    def _calculate_sell_metrics(flip: Dict, now: datetime, sell_started: datetime,
                                last_sell: Optional[datetime], current_volume: Optional[int]) -> Dict:
        """Calculate metrics for sell offers"""
        # Time calculations
        total_hours = (now - sell_started).total_seconds() / 3600
        hours_since_last = (now - last_sell).total_seconds() / 3600 if last_sell else total_hours
        
        # Quantity calculations
        quantity_sold = flip['quantity_total'] - flip['quantity_remaining']
        quantity_in_inventory = flip['quantity_remaining']
        
        # Sell rate (items/hour)
        actual_sell_rate = quantity_sold / total_hours if total_hours > 0 else 0
        
        # Expected sell rate (conservative: volume / 10)
        expected_sell_rate = 0
        if current_volume:
            expected_sell_rate = current_volume / FillRateService.EXPECTED_FILL_MULTIPLIER
        
        # Recommendation
        recommendation = FillRateService._get_sell_recommendation(
            actual_sell_rate=actual_sell_rate,
            expected_sell_rate=expected_sell_rate,
            total_hours=total_hours,
            hours_since_last=hours_since_last,
            quantity_in_inventory=quantity_in_inventory
        )
        
        return {
            'time_in_inventory_hours': round(total_hours, 1),
            'hours_since_last_sell': round(hours_since_last, 1),
            'quantity_sold': quantity_sold,
            'quantity_in_inventory': quantity_in_inventory,
            'actual_sell_rate': round(actual_sell_rate, 1),
            'expected_sell_rate': round(expected_sell_rate, 1),
            'recommendation': recommendation['status'],
            'recommendation_text': recommendation['text'],
            'badge_color': recommendation['color']
        }
    
    @staticmethod
    def _get_buy_recommendation(actual_fill_rate: float, expected_fill_rate: float,
                                fill_progress: float, total_hours: float,
                                hours_since_last: float, recent_activity: bool) -> Dict:
        """Determine recommendation for buy offers"""
        # If we have no expected rate, can only use time-based heuristics
        if expected_fill_rate == 0:
            if recent_activity:
                return {'status': 'keep', 'text': 'Filling', 'color': 'green'}
            if total_hours < FillRateService.STAGNANT_HOURS:
                return {'status': 'monitor', 'text': 'Monitor', 'color': 'yellow'}
            elif hours_since_last > 1.0:
                return {'status': 'cancel', 'text': 'Consider Cancel', 'color': 'red'}
            else:
                return {'status': 'keep', 'text': 'Filling', 'color': 'green'}
        
        # Calculate fill rate ratio
        fill_rate_ratio = actual_fill_rate / expected_fill_rate if expected_fill_rate > 0 else 0
        
        # Green (Keep): Good progress or very recent activity
        if recent_activity:
            return {'status': 'keep', 'text': 'Recent Activity', 'color': 'green'}
            
        if fill_rate_ratio >= FillRateService.KEEP_THRESHOLD:
            return {'status': 'keep', 'text': 'Filling Well', 'color': 'green'}
        
        # Red (Cancel): Poor progress
        if fill_rate_ratio < FillRateService.MONITOR_THRESHOLD:
            if total_hours > FillRateService.STAGNANT_HOURS or hours_since_last > 1.0:
                return {'status': 'cancel', 'text': 'Consider Cancel', 'color': 'red'}
        
        # Yellow (Monitor): Moderate progress or early
        if total_hours < FillRateService.STAGNANT_HOURS:
            return {'status': 'monitor', 'text': 'Slow Fill', 'color': 'yellow'}
        
        return {'status': 'monitor', 'text': 'Slow Fill', 'color': 'yellow'}
    
    @staticmethod
    def _get_sell_recommendation(actual_sell_rate: float, expected_sell_rate: float,
                                 total_hours: float, hours_since_last: float,
                                 quantity_in_inventory: int) -> Dict:
        """Determine recommendation for sell offers"""
        # If we have no expected rate, use time-based heuristics
        if expected_sell_rate == 0:
            if total_hours < FillRateService.STAGNANT_HOURS:
                return {'status': 'monitor', 'text': 'Monitor', 'color': 'yellow'}
            elif hours_since_last > 1.0:
                return {'status': 'cancel', 'text': 'Price Too High?', 'color': 'red'}
            else:
                return {'status': 'keep', 'text': 'Selling', 'color': 'green'}
        
        # Calculate sell rate ratio
        sell_rate_ratio = actual_sell_rate / expected_sell_rate if expected_sell_rate > 0 else 0
        
        # Green (Keep): Good progress
        if sell_rate_ratio >= FillRateService.KEEP_THRESHOLD:
            return {'status': 'keep', 'text': 'Selling Well', 'color': 'green'}
        
        # Red (Cancel): Poor progress
        if sell_rate_ratio < FillRateService.MONITOR_THRESHOLD:
            if total_hours > FillRateService.STAGNANT_HOURS:
                return {'status': 'cancel', 'text': 'Price Too High?', 'color': 'red'}
        
        # Yellow (Monitor): Moderate progress
        return {'status': 'monitor', 'text': 'Slow Sell', 'color': 'yellow'}
    
    @staticmethod
    def _determine_overall_status(buy_metrics: Optional[Dict], sell_metrics: Optional[Dict]) -> str:
        """Determine overall status from buy and sell metrics"""
        if buy_metrics and sell_metrics:
            # Both active - use worst status
            statuses = [buy_metrics['recommendation'], sell_metrics['recommendation']]
            if 'cancel' in statuses:
                return 'cancel'
            elif 'monitor' in statuses:
                return 'monitor'
            else:
                return 'keep'
        elif buy_metrics:
            return buy_metrics['recommendation']
        elif sell_metrics:
            return sell_metrics['recommendation']
        else:
            return 'unknown'