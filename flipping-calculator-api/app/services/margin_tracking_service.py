"""
Margin Tracking Service

Analyzes historical price data to identify margin trends over time.
Helps users identify optimal trading times by showing when buy-sell spreads
are widest.

Key Metrics:
- Margin % = ((sell_price - buy_price) / buy_price) * 100
- Peak times = Hours/days with consistently higher margins
- Trend analysis = Is margin increasing, decreasing, or stable?
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from app.services.price_history_service import PriceHistoryService
from app.utils.database import get_db, execute_query, executemany_query


class MarginTrackingService:
    """Service for analyzing profit margins over time"""
    
    @staticmethod
    def analyze_item_margins(
        item_id: int,
        hours: int = 168,  # 7 days default
        interval: str = '1h'
    ) -> Optional[Dict]:
        """
        Analyze historical margins for an item
        
        Args:
            item_id: The item to analyze
            hours: How many hours of history to analyze
            interval: Grouping interval ('1h', '6h', '1d')
        
        Returns:
            Dictionary with margin analysis or None if insufficient data
        """
        print(f"DEBUG: Fetching history for item {item_id}, hours={hours}")
        # Get historical price data
        history = PriceHistoryService.get_item_history(item_id, hours=hours)
        
        print(f"DEBUG: Retrieved {len(history) if history else 0} history records")
        if not history or len(history) < 10:
            print(f"DEBUG: Insufficient data - need at least 10 records, got {len(history) if history else 0}")
            return None
        
        print(f"DEBUG: Sample history point: {history[0] if history else 'none'}")
        
        # Calculate margins for each data point
        margin_data = []
        for point in history:
            high = point.get('price_high')
            low = point.get('price_low')
            
            if high and low and low > 0:
                # Based on correct mapping:
                # sell_price = price_high
                # buy_price = price_low
                spread = high - low
                margin_percent = (spread / low) * 100
                
                margin_data.append({
                    'timestamp': point['timestamp'],
                    'margin_percent': round(margin_percent, 2),
                    'buy_price': low,
                    'sell_price': high,
                    'spread': spread,
                    'volume': point.get('volume_high', 0) + point.get('volume_low', 0)
                })
        
        print(f"DEBUG: Calculated {len(margin_data)} margin data points")
        
        if not margin_data:
            return None
        
        # Aggregate by interval
        aggregated = MarginTrackingService._aggregate_by_interval(
            margin_data, interval
        )
        
        # Calculate statistics
        margins = [d['margin_percent'] for d in margin_data]
        current_margin = margin_data[0]['margin_percent']  # Most recent
        avg_margin = sum(margins) / len(margins)
        max_margin = max(margins)
        min_margin = min(margins)
        
        # Identify peak trading times
        peak_times = MarginTrackingService._identify_peak_times(margin_data)
        
        # Calculate trend
        trend = MarginTrackingService._calculate_trend(margin_data)
        
        # Get item name
        item_name = MarginTrackingService._get_item_name(item_id)
        
        return {
            'item_id': item_id,
            'item_name': item_name,
            'period_hours': hours,
            'interval': interval,
            'current_margin': round(current_margin, 2),
            'avg_margin': round(avg_margin, 2),
            'max_margin': round(max_margin, 2),
            'min_margin': round(min_margin, 2),
            'trend': trend,
            'peak_times': peak_times,
            'data': aggregated
        }
    
    @staticmethod
    def _aggregate_by_interval(data: List[Dict], interval: str) -> List[Dict]:
        """
        Aggregate margin data by time interval
        
        Args:
            data: List of margin data points
            interval: '1h', '6h', or '1d'
        
        Returns:
            List of aggregated data points
        """
        interval_seconds = {
            '1h': 3600,
            '6h': 6 * 3600,
            '1d': 24 * 3600,
        }.get(interval, 3600)
        
        # Group by interval
        buckets = defaultdict(list)
        
        for point in data:
            # Convert datetime to Unix timestamp for bucketing
            ts = point['timestamp']
            if isinstance(ts, datetime):
                timestamp_unix = int(ts.timestamp())
            else:
                timestamp_unix = int(ts)
            
            bucket_key = (timestamp_unix // interval_seconds) * interval_seconds
            buckets[bucket_key].append(point)
        
        # Calculate averages for each bucket
        aggregated = []
        for timestamp_unix in sorted(buckets.keys(), reverse=True):
            points = buckets[timestamp_unix]
            
            avg_margin = sum(p['margin_percent'] for p in points) / len(points)
            avg_buy = sum(p['buy_price'] for p in points) / len(points)
            avg_sell = sum(p['sell_price'] for p in points) / len(points)
            total_volume = sum(p['volume'] for p in points)
            
            aggregated.append({
                'timestamp': timestamp_unix,  # Return as Unix timestamp for consistency
                'margin_percent': round(avg_margin, 2),
                'buy_price': int(avg_buy),
                'sell_price': int(avg_sell),
                'spread': int(avg_sell - avg_buy),
                'volume': total_volume,
                'sample_count': len(points)
            })
        
        return aggregated
    
    @staticmethod
    def _identify_peak_times(data: List[Dict]) -> List[Dict]:
        """
        Identify hours and days with consistently high margins
        
        Returns:
            List of peak time patterns sorted by margin
        """
        # Group by hour of day and day type (weekday/weekend)
        hour_margins = defaultdict(list)
        
        for point in data:
            # Handle both datetime objects and Unix timestamps
            ts = point['timestamp']
            if isinstance(ts, datetime):
                dt = ts
            else:
                dt = datetime.fromtimestamp(ts)
            
            hour = dt.hour
            is_weekend = dt.weekday() >= 5  # Saturday=5, Sunday=6
            day_type = 'weekend' if is_weekend else 'weekday'
            
            key = (hour, day_type)
            hour_margins[key].append(point['margin_percent'])
        
        # Calculate average margin for each hour/day combination
        peak_times = []
        for (hour, day_type), margins in hour_margins.items():
            if len(margins) >= 3:  # Need at least 3 samples
                avg_margin = sum(margins) / len(margins)
                peak_times.append({
                    'hour': hour,
                    'day_type': day_type,
                    'avg_margin': round(avg_margin, 2),
                    'sample_count': len(margins)
                })
        
        # Sort by average margin descending
        peak_times.sort(key=lambda x: x['avg_margin'], reverse=True)
        
        # Return top 5 peak times
        return peak_times[:5]
    
    @staticmethod
    def _calculate_trend(data: List[Dict]) -> Dict:
        """
        Calculate margin trend (increasing/decreasing/stable)
        
        Uses simple linear regression on recent data
        """
        if len(data) < 10:
            return {'direction': 'unknown', 'strength': 0}
        
        # Use most recent 50 points or all data if less
        recent = data[:min(50, len(data))]
        
        # Simple linear regression
        n = len(recent)
        x = list(range(n))  # Time index (0 = most recent)
        y = [p['margin_percent'] for p in recent]
        
        # Calculate slope
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Classify trend
        # Slope is negative because x=0 is most recent (we're going backwards)
        if slope < -0.05:
            direction = 'increasing'  # Negative slope = increasing over time
            strength = min(abs(slope) * 20, 100)  # Scale to 0-100
        elif slope > 0.05:
            direction = 'decreasing'  # Positive slope = decreasing over time
            strength = min(abs(slope) * 20, 100)
        else:
            direction = 'stable'
            strength = 0
        
        return {
            'direction': direction,
            'strength': round(strength, 1),
            'slope': round(slope, 4)
        }
    
    @staticmethod
    def _get_item_name(item_id: int) -> str:
        """Get item name from database"""
        try:
            with get_db() as session:
                _res = execute_query(session, 'SELECT name FROM items WHERE id = ?', (item_id,))
                row = _res.mappings().fetchone()
                return row['name'] if row else f"Item {item_id}"
        except Exception:
            return f"Item {item_id}"