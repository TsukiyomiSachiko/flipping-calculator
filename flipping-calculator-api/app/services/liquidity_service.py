"""
Liquidity Timing Analysis Service

Analyzes volume patterns from price_history to help users understand:
- When items typically fill (hourly patterns)
- Whether liquidity is consistent or intermittent
- Estimated time-to-fill based on historical data
- Best trading times for specific items
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from app.utils.database import get_db, execute_query, executemany_query
import statistics


class LiquidityService:
    
    @staticmethod
    def get_liquidity_insights(item_id: int, hours: int = 168) -> Dict:
        """
        Analyze liquidity patterns for an item over the specified time window.
        
        Args:
            item_id: Item ID to analyze
            hours: Hours of history to analyze (default: 7 days)
        
        Returns:
            Dict with liquidity insights including:
            - pattern: "consistent", "intermittent", "sparse"
            - best_hours: List of hours with highest fill rates
            - avg_fill_time_minutes: Estimated time to fill
            - volume_distribution: Hourly volume breakdown
        """
        with get_db() as session:
            
            # Get volume data for the time window
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            _res = execute_query(session, '''
                SELECT 
                    timestamp,
                    volume_high + volume_low as total_volume
                FROM price_history
                WHERE item_id = ? AND timestamp > ?
                ORDER BY timestamp ASC
            ''', (item_id, cutoff))
            
            rows = _res.mappings().fetchall()
            
        if not rows or len(rows) < 10:
            return {
                "pattern": "insufficient_data",
                "message": "Not enough historical data to analyze liquidity patterns",
                "data_points": len(rows)
            }
        
        # Extract volumes and timestamps
        # PostgreSQL returns timestamp as datetime object already, no need to parse
        volume_data = [(row['timestamp'], row['total_volume']) 
                       for row in rows if row['total_volume'] > 0]
        
        if not volume_data:
            return {
                "pattern": "no_volume",
                "message": "No trading volume detected in the time window"
            }
        
        # Analyze hourly patterns
        hourly_volumes = {}  # hour_of_day -> [volumes]
        for timestamp, volume in volume_data:
            hour = timestamp.hour
            if hour not in hourly_volumes:
                hourly_volumes[hour] = []
            hourly_volumes[hour].append(volume)
        
        # Calculate average volume per hour
        hourly_avg = {hour: statistics.mean(vols) for hour, vols in hourly_volumes.items()}
        
        # Find best trading hours (top 5)
        sorted_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)
        best_hours = sorted_hours[:5]
        
        # Analyze day-of-week patterns
        weekday_volumes = {}  # 0=Monday, 6=Sunday
        weekend_volumes = []
        weekday_only_volumes = []
        
        for timestamp, volume in volume_data:
            day = timestamp.weekday()
            if day not in weekday_volumes:
                weekday_volumes[day] = []
            weekday_volumes[day].append(volume)
            
            if day >= 5:  # Saturday or Sunday
                weekend_volumes.append(volume)
            else:
                weekday_only_volumes.append(volume)
        
        # Determine pattern consistency
        volumes_only = [v for _, v in volume_data]
        pattern = LiquidityService._classify_pattern(volumes_only)
        
        # Calculate time between volume spikes
        spike_intervals = LiquidityService._calculate_spike_intervals(volume_data)
        avg_fill_time = statistics.mean(spike_intervals) if spike_intervals else None
        
        # Build response
        result = {
            "pattern": pattern,
            "best_hours": [
                {
                    "hour": hour,
                    "hour_label": LiquidityService._format_hour(hour),
                    "avg_volume": round(avg_vol)
                }
                for hour, avg_vol in best_hours
            ],
            "avg_fill_time_minutes": round(avg_fill_time) if avg_fill_time else None,
            "total_data_points": len(volume_data),
            "pattern_description": LiquidityService._get_pattern_description(pattern),
            "hourly_distribution": [
                {"hour": h, "avg_volume": round(v)} 
                for h, v in sorted(hourly_avg.items())
            ]
        }
        
        # Add weekend vs weekday comparison if we have enough data
        if weekend_volumes and weekday_only_volumes:
            weekend_avg = statistics.mean(weekend_volumes)
            weekday_avg = statistics.mean(weekday_only_volumes)
            result["weekend_multiplier"] = round(weekend_avg / weekday_avg, 2) if weekday_avg > 0 else 1.0
        
        return result
    
    @staticmethod
    def _classify_pattern(volumes: List[float]) -> str:
        """
        Classify liquidity pattern based on volume variance.
        
        Returns:
            "consistent" - steady volume throughout
            "intermittent" - volume comes in waves
            "sparse" - very low, sporadic volume
        """
        if not volumes:
            return "no_data"
        
        avg_volume = statistics.mean(volumes)
        
        # Very low average volume = sparse
        if avg_volume < 100:
            return "sparse"
        
        # Calculate coefficient of variation (CV = stdev / mean)
        if len(volumes) > 1:
            stdev = statistics.stdev(volumes)
            cv = stdev / avg_volume if avg_volume > 0 else 0
            
            # High variance = intermittent (comes in waves)
            # Low variance = consistent
            if cv > 1.5:
                return "intermittent"
            elif cv < 0.5:
                return "consistent"
            else:
                return "moderate"
        
        return "insufficient_data"
    
    @staticmethod
    def _calculate_spike_intervals(volume_data: List[tuple]) -> List[float]:
        """
        Calculate time intervals between volume spikes.
        
        Args:
            volume_data: List of (timestamp, volume) tuples
        
        Returns:
            List of intervals in minutes between spikes
        """
        if len(volume_data) < 2:
            return []
        
        volumes = [v for _, v in volume_data]
        avg_volume = statistics.mean(volumes)
        
        # A "spike" is volume > 150% of average
        threshold = avg_volume * 1.5
        
        spike_times = [ts for ts, vol in volume_data if vol > threshold]
        
        if len(spike_times) < 2:
            return []
        
        # Calculate intervals between spikes
        intervals = []
        for i in range(1, len(spike_times)):
            delta = spike_times[i] - spike_times[i-1]
            intervals.append(delta.total_seconds() / 60)  # Convert to minutes
        
        return intervals
    
    @staticmethod
    def _format_hour(hour: int) -> str:
        """Format hour as 12-hour time with AM/PM"""
        if hour == 0:
            return "12 AM"
        elif hour < 12:
            return f"{hour} AM"
        elif hour == 12:
            return "12 PM"
        else:
            return f"{hour - 12} PM"
    
    @staticmethod
    def _get_pattern_description(pattern: str) -> str:
        """Get user-friendly description of liquidity pattern"""
        descriptions = {
            "consistent": "Fills steadily throughout the day",
            "intermittent": "Fills in waves - be patient between volume spikes",
            "moderate": "Moderately consistent fill rate",
            "sparse": "Very low volume - may take a long time to fill",
            "no_volume": "No recent trading activity detected",
            "insufficient_data": "Not enough data to determine pattern"
        }
        return descriptions.get(pattern, "Unknown pattern")