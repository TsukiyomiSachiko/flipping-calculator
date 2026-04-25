import math
from typing import Dict, Optional, List
from app.utils.api_client import fetch_price_timeseries


class TrajectoryService:
    """
    Computes market trajectory for an item using historical price data.

    Algorithm:
    1. Compute midpoint price (avg of buy/sell) for each data point
    2. Apply Exponentially Weighted Moving Average (EWMA) to smooth noise
    3. Fit weighted linear regression (recent data weighted 2x more)
    4. Project forward using the regression slope
    5. Build confidence bands from historical volatility that widen with distance

    Returns a complete trajectory with smoothed history, projection, confidence
    bands, trend classification, and summary statistics.
    """

    @staticmethod
    def compute_trajectory(item_id: int, timestep: str = '1h') -> Optional[Dict]:
        """
        Compute market trajectory for an item.

        Args:
            item_id: OSRS item ID
            timestep: '5m', '1h', or '6h'

        Returns:
            Dictionary with trajectory data, trend info, and stats, or None
            if insufficient data.
        """
        try:
            ts_data = fetch_price_timeseries(item_id, timestep)
        except Exception:
            return None

        data_points = ts_data.get('data', [])
        if not data_points or len(data_points) < 6:
            return None

        # Filter valid points (need both buy and sell prices)
        valid = [
            dp for dp in data_points
            if dp.get('avgHighPrice') and dp.get('avgLowPrice')
        ]
        if len(valid) < 6:
            return None

        # Sort by timestamp ascending
        valid.sort(key=lambda x: x['timestamp'])

        buy_prices = [dp['avgLowPrice'] for dp in valid]
        sell_prices = [dp['avgHighPrice'] for dp in valid]
        timestamps = [dp['timestamp'] for dp in valid]
        midpoints = [(b + s) / 2 for b, s in zip(buy_prices, sell_prices)]

        n = len(midpoints)

        # --- Step 1: EWMA smoothing ---
        # More smoothing for noisier short-interval data
        alpha = {'5m': 0.15, '1h': 0.25, '6h': 0.35}.get(timestep, 0.25)
        smoothed = TrajectoryService._ewma(midpoints, alpha)

        # --- Step 2: Weighted linear regression ---
        slope, intercept = TrajectoryService._weighted_regression(smoothed, recent_bias=2.0)

        # --- Step 3: Volatility ---
        volatility = TrajectoryService._volatility(midpoints)

        # --- Step 4: Trend classification ---
        avg_price = sum(midpoints) / n
        slope_pct = (slope / avg_price) * 100 if avg_price > 0 else 0
        trend = TrajectoryService._classify_trend(slope_pct)

        # --- Step 5: Build trajectory data ---
        projection_steps = max(int(n * 0.2), 3)
        avg_interval = (timestamps[-1] - timestamps[0]) / (n - 1) if n > 1 else 300

        # Historical points with smoothed values
        history = []
        for i, dp in enumerate(valid):
            history.append({
                'timestamp': dp['timestamp'],
                'buyPrice': dp['avgLowPrice'],
                'sellPrice': dp['avgHighPrice'],
                'smoothed': round(smoothed[i]),
            })

        # Projection points
        projection = []
        for j in range(1, projection_steps + 1):
            idx = n - 1 + j
            proj_ts = int(timestamps[-1] + avg_interval * j)
            proj_value = intercept + slope * idx
            band_width = volatility * math.sqrt(j) * 1.5

            projection.append({
                'timestamp': proj_ts,
                'trendLine': max(1, round(proj_value)),
                'upper': max(1, round(proj_value + band_width)),
                'lower': max(1, round(proj_value - band_width)),
            })

        # --- Step 6: Summary stats ---
        current_smoothed = smoothed[-1]
        projected_end = intercept + slope * (n - 1 + projection_steps)
        projected_change = projected_end - current_smoothed
        projected_change_pct = (projected_change / current_smoothed * 100) if current_smoothed > 0 else 0

        time_labels = {'5m': 'min', '1h': 'h', '6h': 'h'}
        time_multipliers = {'5m': 5, '1h': 1, '6h': 6}
        unit = time_labels.get(timestep, 'steps')
        multiplier = time_multipliers.get(timestep, 1)
        projection_window = f"{projection_steps * multiplier}{unit}"

        return {
            'history': history,
            'projection': projection,
            'trend': {
                'direction': trend['label'],
                'color': trend['color'],
                'emoji': trend['emoji'],
                'slopePctPerStep': round(slope_pct, 3),
            },
            'stats': {
                'currentSmoothed': round(current_smoothed),
                'projectedEnd': round(projected_end),
                'projectedChange': round(projected_change),
                'projectedChangePct': round(projected_change_pct, 1),
                'volatility': round(volatility),
                'projectionWindow': projection_window,
                'dataPoints': n,
            },
            'lastHistoricalTimestamp': timestamps[-1],
        }

    @staticmethod
    def _ewma(values: List[float], alpha: float = 0.3) -> List[float]:
        """Exponentially Weighted Moving Average."""
        if not values:
            return []
        smoothed = [values[0]]
        for i in range(1, len(values)):
            smoothed.append(alpha * values[i] + (1 - alpha) * smoothed[i - 1])
        return smoothed

    @staticmethod
    def _weighted_regression(values: List[float], recent_bias: float = 2.0):
        """
        Weighted linear regression with recent data weighted more heavily.
        Returns (slope, intercept).
        """
        n = len(values)
        if n < 2:
            return 0, values[0] if values else 0

        # Linearly increasing weights, with extra bias on last 25%
        weights = []
        for i in range(n):
            base = 1 + i / n
            weights.append(base * recent_bias if i >= n * 0.75 else base)

        total_w = sum(weights)
        x_mean = sum(w * i for i, w in enumerate(weights)) / total_w
        y_mean = sum(w * v for w, v in zip(weights, values)) / total_w

        num = sum(w * (i - x_mean) * (v - y_mean) for i, (w, v) in enumerate(zip(weights, values)))
        den = sum(w * (i - x_mean) ** 2 for i, w in enumerate(weights))

        slope = num / den if den != 0 else 0
        intercept = y_mean - slope * x_mean
        return slope, intercept

    @staticmethod
    def _volatility(values: List[float]) -> float:
        """Standard deviation of absolute price changes."""
        if len(values) < 2:
            return 0
        changes = [abs(values[i] - values[i - 1]) for i in range(1, len(values)) if values[i - 1] > 0]
        if not changes:
            return 0
        mean = sum(changes) / len(changes)
        variance = sum((c - mean) ** 2 for c in changes) / len(changes)
        return math.sqrt(variance)

    @staticmethod
    def _classify_trend(slope_pct: float) -> Dict:
        """Classify trend direction based on slope as % of price per step."""
        if slope_pct > 0.3:
            return {'label': 'rising', 'color': '#10B981', 'emoji': '📈'}
        if slope_pct > 0.05:
            return {'label': 'slight_rise', 'color': '#6EE7B7', 'emoji': '↗️'}
        if slope_pct > -0.05:
            return {'label': 'stable', 'color': '#FBBF24', 'emoji': '➡️'}
        if slope_pct > -0.3:
            return {'label': 'slight_decline', 'color': '#F97316', 'emoji': '↘️'}
        return {'label': 'declining', 'color': '#EF4444', 'emoji': '📉'}
