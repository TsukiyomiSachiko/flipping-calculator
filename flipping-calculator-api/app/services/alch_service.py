from typing import List, Dict, Optional
import logging
from app.utils.database import get_db
from app.utils.api_client import fetch_latest_prices, fetch_volume_data

logger = logging.getLogger(__name__)

# Nature Rune item ID
NATURE_RUNE_ID = 561

class AlchService:
    @staticmethod
    def get_profitable_alchs(limit: int = 500, min_volume: int = 1) -> List[Dict]:
        """
        Fetch items with highalch > 0, calculate alchemy profit using live GE prices
        and the cost of a nature rune, and return a list sorted by profit at GE limit.
        
        Args:
            limit: Maximum number of records to return
            min_volume: Minimum hourly volume filter (hides inactive/untradable items)
            
        Returns:
            A list of dicts representing profitable high-alch opportunities.
        """
        latest_prices = fetch_latest_prices(use_cache=True).get("data", {})
        volume_data = fetch_volume_data(use_cache=True).get("data", {})
        
        # Get Nature Rune price
        nat_rune_data = latest_prices.get(str(NATURE_RUNE_ID), {})
        # Use low (slow buy) if available, fallback to high (instant buy), default to 90
        nat_rune_price = nat_rune_data.get("low") or nat_rune_data.get("high") or 90
        
        with get_db() as conn:
            cursor = conn.cursor()
            # Select all columns from items with highalch > 0.
            # Selecting all avoids SQL reserved word (like "limit") parsing conflicts in Postgres/SQLite.
            cursor.execute("SELECT * FROM items WHERE highalch > 0")
            items = [dict(row) for row in cursor.fetchall()]
            
        profitable_alchs = []
        
        for item in items:
            item_id = item["id"]
            
            # Skip Nature Rune itself
            if item_id == NATURE_RUNE_ID:
                continue
                
            price_info = latest_prices.get(str(item_id), {})
            high_price = price_info.get("high")
            low_price = price_info.get("low")
            
            # We need at least one price to determine market cost
            if not high_price and not low_price:
                continue
                
            # Default buy price to low (slow buy) as it's how players buy in bulk, fallback to high
            buy_price = low_price if low_price is not None else high_price
            
            # Profit per alch
            profit_per_alch = item["highalch"] - (buy_price + nat_rune_price)
            
            # Only include actually profitable items
            if profit_per_alch <= 0:
                continue
                
            # Calculate profit for instant-buy (using high price) if available
            profit_instant = None
            if high_price is not None:
                profit_instant = item["highalch"] - (high_price + nat_rune_price)
                
            # ROI
            roi = (profit_per_alch / (buy_price + nat_rune_price) * 100) if (buy_price + nat_rune_price) > 0 else 0
            
            # GE limit and profit potential at limit
            ge_limit = item.get("ge_limit") or 0
            profit_at_limit = profit_per_alch * ge_limit
            
            # Volume (sum of low & high price volumes in the last hour)
            vol_info = volume_data.get(str(item_id), {})
            volume_1h = vol_info.get("lowPriceVolume", 0) + vol_info.get("highPriceVolume", 0)
            
            # Filter by minimum volume (default is 1 to hide items with 0 trading volume)
            if volume_1h < min_volume:
                continue
                
            profitable_alchs.append({
                "id": item_id,
                "name": item["name"],
                "members": item["members"],
                "highalch": item["highalch"],
                "limit": ge_limit,
                "buy_price": buy_price,
                "high_price": high_price,
                "low_price": low_price,
                "profit_per_alch": profit_per_alch,
                "profit_instant": profit_instant,
                "roi": round(roi, 2),
                "profit_at_limit": profit_at_limit,
                "volume_1h": volume_1h
            })
            
        # Sort by profit at GE limit descending
        profitable_alchs.sort(key=lambda x: x["profit_at_limit"], reverse=True)
        
        # Apply the return limit
        return profitable_alchs[:limit]
