from typing import List, Dict, Optional
import logging
from datetime import datetime, timezone
from app.utils.database import get_db
from app.utils.api_client import fetch_latest_prices, fetch_volume_data
from app.utils.wiki_scraper import WikiScraper
from app.services.item_service import calculate_ge_tax

logger = logging.getLogger(__name__)

class ConversionService:
    @staticmethod
    def sync_conversions_from_wiki():
        """Scrape OSRS Wiki and update item_conversions table."""
        scraper = WikiScraper()
        methods = scraper.scrape_processing_methods()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Use a transaction for the entire sync
            try:
                # We'll do a simple "delete and re-insert" for items,
                # but for conversions we want to keep IDs if possible.
                # However, for now, let's keep it simple.
                
                # 1. Get existing conversions to match by name
                cursor.execute("SELECT id, name FROM item_conversions")
                existing = {row["name"]: row["id"] for row in cursor.fetchall()}
                
                new_count = 0
                updated_count = 0
                
                for method in methods:
                    name = method["wiki_name"] or method["name"]
                    now = datetime.now(timezone.utc)
                    
                    if name in existing:
                        # Update
                        conv_id = existing[name]
                        cursor.execute('''
                            UPDATE item_conversions SET
                                category = ?,
                                conversion_rate_per_hour = ?,
                                skill_required = ?,
                                level_required = ?,
                                members = ?,
                                wiki_url = ?,
                                updated_at = ?
                            WHERE id = ?
                        ''', (
                            method.get("category"),
                            method.get("kph"),
                            method.get("skill_required"),
                            method.get("level_required"),
                            method.get("members"),
                            method.get("wiki_url"),
                            now,
                            conv_id
                        ))
                        # Clear old items
                        cursor.execute("DELETE FROM conversion_items WHERE conversion_id = ?", (conv_id,))
                        updated_count += 1
                    else:
                        # Insert
                        cursor.execute('''
                            INSERT INTO item_conversions 
                            (name, category, conversion_rate_per_hour, skill_required, level_required, members, wiki_url, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            RETURNING id
                        ''', (
                            name,
                            method.get("category"),
                            method.get("kph"),
                            method.get("skill_required"),
                            method.get("level_required"),
                            method.get("members"),
                            method.get("wiki_url"),
                            now,
                            now
                        ))
                        conv_id = cursor.fetchone()[0]
                        new_count += 1
                    
                    # Insert items
                    items_to_insert = []
                    for input_item in method["inputs"]:
                        items_to_insert.append((conv_id, input_item["id"], input_item["quantity"], True))
                    for output_item in method["outputs"]:
                        items_to_insert.append((conv_id, output_item["id"], output_item["quantity"], False))
                    
                    if items_to_insert:
                        cursor.executemany('''
                            INSERT INTO conversion_items (conversion_id, item_id, quantity, is_input)
                            VALUES (?, ?, ?, ?)
                        ''', items_to_insert)
                
                conn.commit()
                return {"message": f"Sync complete: {new_count} new, {updated_count} updated", "count": new_count + updated_count}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error syncing conversions: {e}")
                raise

    @staticmethod
    def get_conversions_with_prices() -> List[Dict]:
        """Fetch all conversions and enrich with live price data."""
        latest_prices = fetch_latest_prices(use_cache=True).get("data", {})
        volume_data = fetch_volume_data(use_cache=True).get("data", {})
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get all conversions
            cursor.execute("SELECT * FROM item_conversions ORDER BY name")
            conversions = [dict(row) for row in cursor.fetchall()]
            
            # Get all conversion items
            cursor.execute('''
                SELECT ci.*, i.name as item_name 
                FROM conversion_items ci
                LEFT JOIN items i ON ci.item_id = i.id
            ''')
            all_items = [dict(row) for row in cursor.fetchall()]
            
            # Map items to conversions
            conv_items_map = {}
            for item in all_items:
                cid = item["conversion_id"]
                if cid not in conv_items_map:
                    conv_items_map[cid] = {"inputs": [], "outputs": []}
                
                # Handle special items without an entry in 'items' table
                if item["item_id"] == -100:
                    item["item_name"] = "Coins"
                
                if item["is_input"]:
                    conv_items_map[cid]["inputs"].append(item)
                else:
                    conv_items_map[cid]["outputs"].append(item)
            
            results = []
            for conv in conversions:
                cid = conv["id"]
                items = conv_items_map.get(cid, {"inputs": [], "outputs": []})
                
                # Calculate costs and revenues
                total_cost = 0
                total_revenue = 0
                total_tax = 0
                
                inputs_detailed = []
                for inp in items["inputs"]:
                    item_id_str = str(inp["item_id"])
                    
                    if inp["item_id"] == -100: # Coins
                        buy_price = 1
                    else:
                        # For buying, we look at the 'high' price (instant buy) or 'low' (slow buy)
                        # For conversion inputs, we usually assume instant buy to be conservative
                        price_data = latest_prices.get(item_id_str, {})
                        buy_price = price_data.get("high") or 0
                    
                    cost = buy_price * inp["quantity"]
                    total_cost += cost
                    
                    inputs_detailed.append({
                        **inp,
                        "price": buy_price,
                        "total_cost": cost
                    })
                
                outputs_detailed = []
                for outp in items["outputs"]:
                    item_id_str = str(outp["item_id"])
                    
                    if outp["item_id"] == -100: # Coins
                        sell_price = 1
                    else:
                        # For selling, we look at 'low' price (instant sell)
                        price_data = latest_prices.get(item_id_str, {})
                        sell_price = price_data.get("low") or 0
                    
                    tax = calculate_ge_tax(sell_price) * outp["quantity"]
                    revenue = (sell_price * outp["quantity"]) - tax
                    
                    total_revenue += revenue
                    total_tax += tax
                    
                    outputs_detailed.append({
                        **outp,
                        "price": sell_price,
                        "tax": tax,
                        "revenue": revenue
                    })
                
                profit_per_conversion = total_revenue - total_cost
                kph = conv["conversion_rate_per_hour"] or 0
                profit_per_hour = profit_per_conversion * kph
                
                roi = (profit_per_conversion / total_cost * 100) if total_cost > 0 else 0
                
                results.append({
                    **conv,
                    "inputs": inputs_detailed,
                    "outputs": outputs_detailed,
                    "profit_per_conversion": profit_per_conversion,
                    "profit_per_hour": profit_per_hour,
                    "roi": round(roi, 2),
                    "total_cost": total_cost,
                    "total_revenue": total_revenue,
                    "total_tax": total_tax
                })
            
            # Sort by profit per hour descending
            results.sort(key=lambda x: x["profit_per_hour"], reverse=True)
            return results
