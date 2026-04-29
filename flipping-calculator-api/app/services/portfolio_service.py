from typing import List, Dict, Optional
import csv
import io
from datetime import datetime, timezone
from app.utils.database import get_db, engine, execute_query, executemany_query
from app.utils.api_client import fetch_latest_prices, fetch_volume_data
from app.services.item_service import ItemService
from app.services.settings_service import SettingsService
from app.services.fill_rate_service import FillRateService
def calculate_ge_tax(price: int) -> int:
    """
    Calculate GE tax with proper cap
    Tax is 2% of sale price, capped at 5M per item
    Only applies to items > 50 gp
    """
    if price <= 50:
        return 0
    tax = int(price * 0.02)
    return min(tax, 5_000_000)  # Cap at 5M
class PortfolioService:
    @staticmethod
    def log_buy(account_id: int, item_name: str, quantity: int, price: int, intended_quantity: Optional[int] = None, 
                intended_sell_price: Optional[int] = None, notes: Optional[str] = None) -> Dict:
        """
        Log a buy transaction with optional intended quantity for partial fills.
        """
        # Search for item
        with get_db() as session:
            # Case-insensitive search, exact match sorted first
            _res = execute_query(session, '''
                SELECT * FROM items 
                WHERE LOWER(name) LIKE LOWER(?)
                ORDER BY 
                    CASE WHEN LOWER(TRIM(name)) = LOWER(TRIM(?)) THEN 0 ELSE 1 END,
                    name
            ''', (f'%{item_name}%', item_name))
            items = _res.mappings().fetchall()
            if not items:
                return {"error": "No items found matching query"}
            # Check if first result is an exact match
            first_item = items[0]
            is_exact_match = first_item['name'].lower().strip() == item_name.lower().strip()
            # If exact match exists, auto-select it (for buy/sell operations)
            if is_exact_match:
                item = dict(first_item)
            # If no exact match and multiple items, show error with matches
            elif len(items) > 1:
                return {
                    "error": "Multiple items found",
                    "matches": [{"id": item['id'], "name": item['name']} for item in items]
                }
            # Single partial match, use it
            else:
                item = dict(items[0])
            # Default intended_quantity to actual quantity if not specified
            if intended_quantity is None:
                intended_quantity = quantity
            # Validate: if quantity is 0, must have intended_quantity > 0
            if quantity == 0 and intended_quantity == 0:
                return {"error": "Cannot log buy with both quantity and intended_quantity as 0"}
            # Insert flip with timestamp tracking
            now = datetime.now(timezone.utc)
            last_buy = now if quantity > 0 else None
            _res = execute_query(session, '''
                INSERT INTO user_flips (
                    account_id, item_id, item_name, quantity_total, quantity_remaining, buy_price, 
                    intended_quantity, intended_sell_price, notes,
                    buy_offer_started_at, last_buy_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (account_id, item['id'], item['name'], quantity, quantity, price, intended_quantity, intended_sell_price, notes, now, last_buy))
            flip_id = _res.scalar()
            # Only log transaction if quantity > 0 (actual items bought)
            if quantity > 0:
                _res = execute_query(session, '''
                    INSERT INTO flip_transactions (flip_id, transaction_type, mutation_type, quantity, price, notes)
                    VALUES (?, 'buy', 'trade', ?, ?, ?)
                ''', (flip_id, quantity, price, notes))
            session.commit()
            # Adjust available cash based on intended quantity (reserves cash for the offer)
            # If quantity > 0, use that (partial fill). Otherwise use intended_quantity (offer placed)
            cash_reserve = quantity if quantity > 0 else intended_quantity
            total_cost = cash_reserve * price
            SettingsService.adjust_cash(account_id, -total_cost, f"Reserve for: {intended_quantity}x {item['name']}")
            if quantity == 0:
                message = f"Logged offer: 0/{intended_quantity}x {item['name']} @ {price:,} gp (cash reserved)"
            else:
                message = f"Logged buy: {quantity}x {item['name']} @ {price:,} gp" + (f" (target: {intended_quantity})" if intended_quantity != quantity else "")
            return {
                "flip_id": flip_id,
                "item_name": item['name'],
                "quantity": quantity,
                "price": price,
                "intended_quantity": intended_quantity,
                "message": message
            }
    @staticmethod
    def add_to_flip(flip_id: int, quantity: int, price: int, notes: Optional[str] = None) -> Dict:
        """Add more quantity to existing flip"""
        with get_db() as session:
            _res = execute_query(session, 'SELECT * FROM user_flips WHERE id = ?', (flip_id,))
            flip = _res.mappings().fetchone()
            if not flip:
                return {"error": "Flip not found"}
            account_id = flip['account_id']
            if flip['status'] not in ['pending', 'partially_completed']:
                return {"error": f"Cannot add to flip with status '{flip['status']}'"}
            # Check if adding would exceed intended quantity
            intended_qty = flip['intended_quantity'] if 'intended_quantity' in flip.keys() else None
            if intended_qty is not None:
                new_total = flip['quantity_total'] + quantity
                if new_total > intended_qty:
                    return {
                        "error": f"Cannot add {quantity} - would exceed intended quantity of {intended_qty:,}. Currently have {flip['quantity_total']:,}, can add up to {intended_qty - flip['quantity_total']:,} more.",
                        "current_quantity": flip['quantity_total'],
                        "intended_quantity": intended_qty,
                        "max_can_add": intended_qty - flip['quantity_total']
                    }
            # Calculate new weighted average
            # Special case: if quantity_total is 0 (offer placed, nothing filled yet), use the new price
            if flip['quantity_total'] == 0:
                new_avg_price = price
                new_total_qty = quantity
            else:
                old_total_cost = flip['buy_price'] * flip['quantity_total']
                new_cost = price * quantity
                new_total_qty = flip['quantity_total'] + quantity
                new_avg_price = int((old_total_cost + new_cost) / new_total_qty)
            # Calculate new remaining quantity
            new_remaining = flip['quantity_remaining'] + quantity
            # Update flip with timestamp tracking
            now = datetime.now(timezone.utc)
            # Determine if this is first time getting inventory (sell offer starts)
            had_no_inventory = flip['quantity_remaining'] == 0
            will_have_inventory = new_remaining > 0
            sell_offer_started = None
            if had_no_inventory and will_have_inventory:
                # First time getting inventory - set sell_offer_started_at
                sell_offer_started = now
                _res = execute_query(session, '''
                    UPDATE user_flips 
                    SET quantity_total = ?, quantity_remaining = ?, buy_price = ?,
                        last_buy_at = ?, sell_offer_started_at = ?
                    WHERE id = ?
                ''', (new_total_qty, new_remaining, new_avg_price, now, sell_offer_started, flip_id))
            else:
                # Just update last_buy_at
                _res = execute_query(session, '''
                    UPDATE user_flips 
                    SET quantity_total = ?, quantity_remaining = ?, buy_price = ?,
                        last_buy_at = ?
                    WHERE id = ?
                ''', (new_total_qty, new_remaining, new_avg_price, now, flip_id))
            # Log transaction
            _res = execute_query(session, '''
                INSERT INTO flip_transactions (flip_id, transaction_type, mutation_type, quantity, price, notes)
                VALUES (?, 'buy', 'trade', ?, ?, ?)
            ''', (flip_id, quantity, price, notes))
            session.commit()
            # Adjust available cash
            intended_qty = flip['intended_quantity'] if 'intended_quantity' in flip.keys() else None
            if intended_qty is not None:
                # Cash was already reserved for intended_quantity
                # Only deduct if we're exceeding the intended amount
                if new_total_qty > intended_qty:
                    # We're buying more than intended - deduct the excess
                    excess_qty = new_total_qty - intended_qty
                    excess_cost = excess_qty * price
                    SettingsService.adjust_cash(account_id, -excess_cost, f"Additional purchase beyond intended for flip #{flip_id}")
                # Otherwise, no cash adjustment needed (already reserved)
            else:
                # No intended quantity set - deduct the full cost
                total_cost = quantity * price
                SettingsService.adjust_cash(account_id, -total_cost, f"Add to flip #{flip_id}")
            return {
                "flip_id": flip_id,
                "added_quantity": quantity,
                "new_total": new_total_qty,
                "new_avg_price": new_avg_price,
                "message": f"Added {quantity}x to flip, new average: {new_avg_price:,} gp"
            }
    @staticmethod
    def log_sell(flip_id: int, price: Optional[int], price_total: Optional[int], 
                 quantity: Optional[int], notes: Optional[str] = None) -> Dict:
        """Log a sell transaction"""
        with get_db() as session:
            _res = execute_query(session, 'SELECT * FROM user_flips WHERE id = ?', (flip_id,))
            flip = _res.mappings().fetchone()
            if not flip:
                return {"error": "Flip not found"}
            account_id = flip['account_id']
            if flip['status'] not in ['pending', 'partially_completed']:
                return {"error": f"Cannot sell flip with status '{flip['status']}'"}
            # Determine quantity
            sell_qty = quantity if quantity is not None else flip['quantity_remaining']
            if sell_qty > flip['quantity_remaining']:
                return {"error": f"Cannot sell {sell_qty}, only {flip['quantity_remaining']} remaining"}
            # Calculate per-item price
            if price_total is not None:
                if quantity is None:
                    return {"error": "--price-total requires --quantity"}
                price_per_item = int(price_total / sell_qty)
            elif price is not None:
                price_per_item = price
            else:
                return {"error": "Must provide either price or price_total"}
            # Calculate profit
            buy_price = flip['buy_price']
            ge_tax = calculate_ge_tax(price_per_item)
            profit_per = price_per_item - buy_price - ge_tax
            profit_this_sale = profit_per * sell_qty
            roi = (profit_per / buy_price * 100) if buy_price > 0 else 0
            # Update remaining
            new_remaining = flip['quantity_remaining'] - sell_qty
            # Log transaction
            _res = execute_query(session, '''
                INSERT INTO flip_transactions (flip_id, transaction_type, mutation_type, quantity, price, notes)
                VALUES (?, 'sell', 'trade', ?, ?, ?)
            ''', (flip_id, sell_qty, price_per_item, notes))
            # Update flip
            if new_remaining == 0:
                intended_qty = flip['intended_quantity'] if 'intended_quantity' in flip.keys() else None
                total_bought = flip['quantity_total']
                should_complete = (intended_qty is None) or (total_bought >= intended_qty)
                if should_complete:
                    total_profit = (flip['profit'] or 0) + profit_this_sale
                    now = datetime.now(timezone.utc)
                    _res = execute_query(session, '''
                        UPDATE user_flips 
                        SET quantity_remaining = 0, sell_price = ?, sell_time = ?, 
                            profit = ?, roi = ?, status = 'completed',
                            last_sell_at = ?
                        WHERE id = ?
                    ''', (price_per_item, now, total_profit, roi, now, flip_id))
                    status_msg = "completed"
                else:
                    total_profit = (flip['profit'] or 0) + profit_this_sale
                    now = datetime.now(timezone.utc)
                    _res = execute_query(session, '''
                        UPDATE user_flips 
                        SET quantity_remaining = 0, sell_price = ?, sell_time = ?, 
                            profit = ?, roi = ?, status = 'partially_completed',
                            last_sell_at = ?
                        WHERE id = ?
                    ''', (price_per_item, now, total_profit, roi, now, flip_id))
                    status_msg = f"partially_completed (sold all {total_bought}, target was {intended_qty})"
                sell_revenue = sell_qty * (price_per_item - ge_tax)
                session.commit()
                SettingsService.adjust_cash(account_id, sell_revenue, f"Sell: {sell_qty}x @ {price_per_item}")
                return {
                    "flip_id": flip_id,
                    "sold_quantity": sell_qty,
                    "profit": profit_this_sale,
                    "total_profit": total_profit,
                    "roi": round(roi, 2),
                    "status": status_msg,
                    "message": f"Sold {sell_qty}x @ {price_per_item:,} gp (profit: {profit_this_sale:,} gp)"
                }
            else:
                total_profit = (flip['profit'] or 0) + profit_this_sale
                sold_so_far = flip['quantity_total'] - new_remaining
                if flip['sell_price'] is None:
                    avg_sell_price = price_per_item
                else:
                    prev_sold = flip['quantity_total'] - flip['quantity_remaining']
                    prev_revenue = prev_sold * flip['sell_price']
                    this_revenue = sell_qty * price_per_item
                    avg_sell_price = int((prev_revenue + this_revenue) / sold_so_far)
                current_status = flip['status']
                new_status = 'partially_completed' if current_status == 'pending' else current_status
                now = datetime.now(timezone.utc)
                is_first_sell = flip['sell_price'] is None
                if is_first_sell:
                    _res = execute_query(session, '''
                        UPDATE user_flips 
                        SET quantity_remaining = ?, profit = ?, sell_price = ?, status = ?,
                            sell_offer_started_at = ?, last_sell_at = ?
                        WHERE id = ?
                    ''', (new_remaining, total_profit, avg_sell_price, new_status, now, now, flip_id))
                else:
                    _res = execute_query(session, '''
                        UPDATE user_flips 
                        SET quantity_remaining = ?, profit = ?, sell_price = ?, status = ?,
                            last_sell_at = ?
                        WHERE id = ?
                    ''', (new_remaining, total_profit, avg_sell_price, new_status, now, flip_id))
                sell_revenue = sell_qty * (price_per_item - ge_tax)
                session.commit()
                SettingsService.adjust_cash(account_id, sell_revenue, f"Sell: {sell_qty}x @ {price_per_item}")
                return {
                    "flip_id": flip_id,
                    "sold_quantity": sell_qty,
                    "price_per_item": price_per_item,
                    "profit": profit_this_sale,
                    "roi": round(roi, 2),
                    "status": "partial",
                    "remaining": new_remaining,
                    "message": f"Sold {sell_qty}x, {new_remaining}x remaining"
                }
    @staticmethod
    def cancel_flip(flip_id: int, reason: Optional[str] = None) -> Dict:
        """Cancel a pending flip - promotes partially_completed to completed"""
        with get_db() as session:
            _res = execute_query(session, 'SELECT * FROM user_flips WHERE id = ?', (flip_id,))
            flip = _res.mappings().fetchone()
            if not flip:
                return {"error": "Flip not found"}
            if flip['status'] == 'completed':
                return {"error": "Cannot cancel completed flip"}
            account_id = flip['account_id']
            # Calculate cash to refund
            buy_price = flip['buy_price']
            quantity_total = flip['quantity_total']
            intended_quantity = flip['intended_quantity'] if 'intended_quantity' in flip.keys() else None
            if quantity_total == 0 and intended_quantity:
                cash_refund = buy_price * intended_quantity
                refund_reason = f"Cancel unfilled offer #{flip_id}: {intended_quantity}x @ {buy_price}"
            elif intended_quantity and quantity_total < intended_quantity:
                unfilled_qty = intended_quantity - quantity_total
                cash_refund = buy_price * unfilled_qty
                refund_reason = f"Cancel flip #{flip_id}: refund unfilled portion {unfilled_qty}x @ {buy_price}"
            else:
                cash_refund = 0
                refund_reason = f"Cancel flip #{flip_id}: no refund (items in inventory)"
            if flip['status'] == 'partially_completed':
                new_status = 'completed'
                message = f"Flip #{flip_id} marked as completed (had realized profit)"
            else:
                new_status = 'cancelled'
                message = f"Cancelled flip #{flip_id} (no sales made)"
            _res = execute_query(session, '''
                UPDATE user_flips 
                SET status = ?, cancel_reason = ?, sell_time = COALESCE(sell_time, ?)
                WHERE id = ?
            ''', (new_status, reason, datetime.now(timezone.utc), flip_id))
            
            # Log mutation
            _res = execute_query(session, '''
                INSERT INTO flip_transactions (flip_id, transaction_type, mutation_type, notes)
                VALUES (?, ?, 'cancel', ?)
            ''', (flip_id, new_status, reason or "Flip cancelled/completed"))
            
            session.commit()
            if cash_refund > 0:
                SettingsService.adjust_cash(account_id, cash_refund, refund_reason)
            return {
                "flip_id": flip_id,
                "status": new_status,
                "reason": reason,
                "cash_refunded": cash_refund,
                "message": message
            }
    @staticmethod
    def delete_flip(flip_id: int) -> Dict:
        """Permanently delete a flip and all its transactions."""
        with get_db() as session:
            _res = execute_query(session, 'SELECT * FROM user_flips WHERE id = ?', (flip_id,))
            flip = _res.mappings().fetchone()
            if not flip:
                return {"error": "Flip not found"}
            flip_dict = dict(flip)
            _res = execute_query(session, 'DELETE FROM flip_transactions WHERE flip_id = ?', (flip_id,))
            transactions_deleted = _res.rowcount
            _res = execute_query(session, 'DELETE FROM user_flips WHERE id = ?', (flip_id,))
            session.commit()
            return {
                "success": True,
                "flip_id": flip_id,
                "item_name": flip_dict['item_name'],
                "transactions_deleted": transactions_deleted,
                "message": f"Deleted flip #{flip_id} ({flip_dict['item_name']}) and {transactions_deleted} transactions"
            }
    @staticmethod
    def adjust_intended_quantity(flip_id: int) -> Dict:
        """Adjust intended_quantity to match quantity_total and free up reserved cash."""
        with get_db() as session:
            _res = execute_query(session, 'SELECT * FROM user_flips WHERE id = ?', (flip_id,))
            flip = _res.mappings().fetchone()
            if not flip:
                return {"error": "Flip not found"}
            account_id = flip['account_id']
            if flip['status'] not in ['pending', 'partially_completed']:
                return {"error": f"Cannot adjust intended quantity for flip with status '{flip['status']}'"}
            old_intended = flip['intended_quantity']
            new_intended = flip['quantity_total']
            if old_intended is None:
                return {"error": "This flip has no intended quantity set"}
            if old_intended == new_intended:
                return {"error": f"Intended quantity is already set to {new_intended}"}
            if new_intended > old_intended:
                return {"error": f"Cannot set intended quantity ({new_intended}) higher than original ({old_intended})"}
            cancelled_qty = old_intended - new_intended
            cash_to_free = cancelled_qty * flip['buy_price']
            _res = execute_query(session, 'UPDATE user_flips SET intended_quantity = ? WHERE id = ?', (new_intended, flip_id))
            
            # Log mutation
            _res = execute_query(session, '''
                INSERT INTO flip_transactions (flip_id, transaction_type, mutation_type, quantity, price, notes)
                VALUES (?, 'adjust', 'adjust_target', ?, ?, ?)
            ''', (flip_id, new_intended, flip['buy_price'], f"Target adjusted from {old_intended} to {new_intended}"))
            
            session.commit()
            SettingsService.adjust_cash(
                account_id, cash_to_free, 
                f"Freed reserved cash for cancelled portion of flip #{flip_id} ({cancelled_qty}x @ {flip['buy_price']})"
            )
            return {
                "flip_id": flip_id,
                "old_intended": old_intended,
                "new_intended": new_intended,
                "cancelled_quantity": cancelled_qty,
                "cash_freed": cash_to_free,
                "message": f"Adjusted intended quantity from {old_intended:,} to {new_intended:,}. Freed {cash_to_free:,} gp."
            }
    @staticmethod
    def update_buy_price(flip_id: int, new_price: int) -> Dict:
        """Update the buy price for a pending flip."""
        with get_db() as session:
            _res = execute_query(session, 'SELECT * FROM user_flips WHERE id = ?', (flip_id,))
            flip = _res.mappings().fetchone()
            if not flip:
                return {"error": "Flip not found"}
            account_id = flip['account_id']
            if flip['status'] not in ['pending', 'partially_completed']:
                return {"error": f"Cannot edit buy price for flip with status '{flip['status']}'"}
            old_price = flip['buy_price']
            if old_price == new_price:
                return {"error": f"Buy price is already {new_price} gp"}
            price_diff = new_price - old_price
            intended_qty = flip['intended_quantity']
            quantity_bought = flip['quantity_total']
            
            cash_adjustment = 0
            if intended_qty and quantity_bought < intended_qty:
                # Only adjust cash for the portion of the offer that hasn't filled yet
                unfilled_qty = intended_qty - quantity_bought
                cash_adjustment = price_diff * unfilled_qty
            
            _res = execute_query(session, 'UPDATE user_flips SET buy_price = ? WHERE id = ?', (new_price, flip_id))
            
            # Log mutation
            _res = execute_query(session, '''
                INSERT INTO flip_transactions (flip_id, transaction_type, mutation_type, price, notes)
                VALUES (?, 'update', 'price_update', ?, ?)
            ''', (flip_id, new_price, f"Buy price updated from {old_price} to {new_price}"))
            
            session.commit()
            if cash_adjustment != 0:
                SettingsService.adjust_cash(
                    account_id, -cash_adjustment,
                    f"Adjusted buy price for flip #{flip_id} from {old_price} to {new_price} gp"
                )
            return {
                "flip_id": flip_id,
                "old_price": old_price,
                "new_price": new_price,
                "message": f"Updated buy price from {old_price:,} to {new_price:,} gp."
            }
    @staticmethod
    def get_pending_flips(account_id: int) -> List[Dict]:
        """Get all pending and partially_completed flips for an account"""
        with get_db() as session:
            _res = execute_query(session, '''
                SELECT * FROM user_flips 
                WHERE account_id = ? AND status IN ('pending', 'partially_completed')
                ORDER BY buy_time DESC
            ''', (account_id,))
            return [dict(row) for row in _res.mappings().fetchall()]
    @staticmethod
    def get_pending_with_projections(account_id: int) -> Dict:
        """Get pending and partially_completed flips enriched for an account"""
        with get_db() as session:
            _res = execute_query(session, '''
                SELECT * FROM user_flips 
                WHERE account_id = ? AND status IN ('pending', 'partially_completed')
                ORDER BY buy_time DESC
            ''', (account_id,))
            flips = [dict(row) for row in _res.mappings().fetchall()]
        if not flips:
            return {"flips": [], "total_projected_profit": 0, "total_current_value": 0, "total_invested": 0}
        latest_data = fetch_latest_prices(use_cache=True)
        volume_data = fetch_volume_data(use_cache=True)
        total_projected_profit = 0
        total_current_value = 0
        total_invested = 0
        enriched = []
        for flip in flips:
            item_id_str = str(flip['item_id'])
            invested = flip['buy_price'] * flip['quantity_total']
            total_invested += invested
            current_sell_price = None
            current_buy_price = None
            projected_profit = None
            projected_profit_remaining = None
            projected_total_value = None
            current_volume = None
            if item_id_str in latest_data.get('data', {}):
                price_data = latest_data['data'][item_id_str]
                current_buy_price = price_data.get('low')
                current_sell_price = price_data.get('high')
                if current_sell_price:
                    ge_tax = calculate_ge_tax(current_sell_price)
                    net_sell = current_sell_price - ge_tax
                    profit_per_item = net_sell - flip['buy_price']
                    projected_profit_remaining = profit_per_item * flip['quantity_remaining']
                    projected_profit = (flip['profit'] or 0) + projected_profit_remaining
                    projected_total_value = current_sell_price * flip['quantity_remaining']
                    total_current_value += projected_total_value
                    total_projected_profit += projected_profit
            if item_id_str in volume_data.get('data', {}):
                vol_data = volume_data['data'][item_id_str]
                current_volume = (vol_data.get('highPriceVolume', 0) or 0) + (vol_data.get('lowPriceVolume', 0) or 0)
            fill_metrics = FillRateService.calculate_fill_metrics(flip, current_volume)
            realized_roi = None
            projected_roi = None
            if flip['profit'] and flip['quantity_total'] > flip['quantity_remaining']:
                quantity_sold = flip['quantity_total'] - flip['quantity_remaining']
                cost_of_sold_items = flip['buy_price'] * quantity_sold
                if cost_of_sold_items > 0:
                    realized_roi = round((flip['profit'] / cost_of_sold_items) * 100, 2)
            if projected_profit is not None and invested > 0:
                projected_roi = round((projected_profit / invested) * 100, 2)
            enriched.append({
                **flip,
                "current_sell_price": current_sell_price,
                "current_buy_price": current_buy_price,
                "projected_profit": projected_profit,
                "projected_profit_remaining": projected_profit_remaining,
                "projected_total_value": projected_total_value,
                "fill_metrics": fill_metrics,
                "realized_roi": realized_roi,
                "projected_roi": projected_roi,
            })
        return {
            "flips": enriched,
            "total_projected_profit": total_projected_profit,
            "total_current_value": total_current_value,
            "total_invested": total_invested,
        }
    @staticmethod
    def get_completed_flips(account_id: int, limit: int = 20) -> List[Dict]:
        """Get completed and partially_completed flips for an account"""
        with get_db() as session:
            _res = execute_query(session, '''
                SELECT * FROM user_flips 
                WHERE account_id = ? AND status IN ('completed', 'partially_completed')
                ORDER BY sell_time DESC
                LIMIT ?
            ''', (account_id, limit))
            return [dict(row) for row in _res.mappings().fetchall()]
    @staticmethod
    def get_cancelled_flips(account_id: int, limit: int = 20) -> List[Dict]:
        """Get cancelled flips for an account"""
        with get_db() as session:
            _res = execute_query(session, '''
                SELECT * FROM user_flips 
                WHERE account_id = ? AND status = 'cancelled'
                ORDER BY sell_time DESC
                LIMIT ?
            ''', (account_id, limit))
            return [dict(row) for row in _res.mappings().fetchall()]
    @staticmethod
    def get_recent_mutations(account_id: int, limit: int = 50) -> List[Dict]:
        """Get the most recent mutations/transactions across all flips for an account"""
        with get_db() as session:
            _res = execute_query(session, '''
                SELECT ft.*, uf.item_name, uf.item_id
                FROM flip_transactions ft
                JOIN user_flips uf ON ft.flip_id = uf.id
                WHERE uf.account_id = ?
                ORDER BY ft.timestamp DESC
                LIMIT ?
            ''', (account_id, limit))
            return [dict(row) for row in _res.mappings().fetchall()]

    @staticmethod
    def get_flip_details(flip_id: int) -> Optional[Dict]:
        """Get flip with all transactions - flip_id is unique"""
        with get_db() as session:
            _res = execute_query(session, 'SELECT * FROM user_flips WHERE id = ?', (flip_id,))
            flip = _res.mappings().fetchone()
            if not flip: return None
            _res = execute_query(session, 'SELECT * FROM flip_transactions WHERE flip_id = ? ORDER BY timestamp ASC', (flip_id,))
            transactions = [dict(row) for row in _res.mappings().fetchall()]
            return {"flip": dict(flip), "transactions": transactions}
    @staticmethod
    def get_summary(account_id: int) -> Dict:
        """Get portfolio summary for an account"""
        with get_db() as session:
            _res = execute_query(session, '''
                SELECT COUNT(*) as total_flips, SUM(profit) as total_profit, AVG(roi) as avg_roi,
                       SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_flips,
                       SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losing_flips,
                       MAX(profit) as best_flip, MIN(profit) as worst_flip,
                       SUM(buy_price * quantity_total) as total_invested
                FROM user_flips WHERE account_id = ? AND status = 'completed'
            ''', (account_id,))
            completed = dict(_res.mappings().fetchone())
            _res = execute_query(session, '''
                SELECT COUNT(*) as pending_flips, SUM(buy_price * quantity_remaining) as pending_capital,
                       SUM(COALESCE(profit, 0)) as pending_profit, SUM(buy_price * quantity_total) as pending_invested
                FROM user_flips WHERE account_id = ? AND status IN ('pending', 'partially_completed')
            ''', (account_id,))
            pending = dict(_res.mappings().fetchone())
            _res = execute_query(session, "SELECT COUNT(*) as cancelled_flips FROM user_flips WHERE account_id = ? AND status = 'cancelled'", (account_id,))
            cancelled = dict(_res.mappings().fetchone())
            total_profit_all = (completed['total_profit'] or 0) + (pending['pending_profit'] or 0)
            pending_sold_cost = (pending['pending_invested'] or 0) - (pending['pending_capital'] or 0)
            roi_in_progress = round((pending['pending_profit'] / pending_sold_cost) * 100, 2) if pending_sold_cost > 0 else 0
            settings = SettingsService.get_settings(account_id)
            available_cash = settings.get('available_cash', 0)
            return {
                "total_flips": completed['total_flips'] or 0, "winning_flips": completed['winning_flips'] or 0,
                "losing_flips": completed['losing_flips'] or 0, "total_profit": completed['total_profit'] or 0,
                "pending_profit": pending['pending_profit'] or 0, "total_profit_all": total_profit_all,
                "avg_roi": round(completed['avg_roi'], 2) if completed['avg_roi'] else 0, "roi_in_progress": roi_in_progress,
                "best_flip": completed['best_flip'] or 0, "worst_flip": completed['worst_flip'] or 0,
                "total_invested": completed['total_invested'] or 0, "pending_flips": pending['pending_flips'] or 0,
                "pending_capital": pending['pending_capital'] or 0, "cancelled_flips": cancelled['cancelled_flips'] or 0,
                "available_cash": available_cash,
            }
    @staticmethod
    def get_statistics(account_id: int) -> Dict:
        """Get detailed portfolio statistics for an account"""
        with get_db() as session:
            # Best and worst performing items (by total profit)
            _res = execute_query(session, '''
                SELECT item_id, item_name,
                       COUNT(*) as flip_count,
                       SUM(profit) as total_profit,
                       AVG(roi) as avg_roi,
                       SUM(quantity_total) as total_quantity
                FROM user_flips
                WHERE account_id = ? AND status = 'completed' AND profit IS NOT NULL
                GROUP BY item_id, item_name
                ORDER BY total_profit DESC
            ''', (account_id,))
            items_by_profit = [dict(row) for row in _res.mappings().fetchall()]
            best_items = items_by_profit[:5] if items_by_profit else []
            worst_items = list(reversed(items_by_profit[-5:])) if items_by_profit else []
            # Most traded items (by flip count)
            _res = execute_query(session, '''
                SELECT item_id, item_name,
                       COUNT(*) as flip_count,
                       SUM(profit) as total_profit,
                       SUM(quantity_total) as total_quantity
                FROM user_flips
                WHERE account_id = ? AND status = 'completed'
                GROUP BY item_id, item_name
                ORDER BY flip_count DESC
                LIMIT 5
            ''', (account_id,))
            most_traded = [dict(row) for row in _res.mappings().fetchall()]
            # Daily profit (last 30 days)
            # Use SQLite or Postgres compatible date function
            _res = execute_query(session, '''
                SELECT date_trunc('day', sell_time) as day,
                       COUNT(*) as flips,
                       SUM(profit) as profit,
                       SUM(roi) / COUNT(*) as avg_roi
                FROM user_flips
                WHERE account_id = ?
                  AND status = 'completed'
                  AND sell_time >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY date_trunc('day', sell_time)
                ORDER BY day ASC
            ''', (account_id,))
            daily_profit = [dict(row) for row in _res.mappings().fetchall()]
            # Best single flip
            _res = execute_query(session, '''
                SELECT item_id, item_name, profit, roi, quantity_total, buy_price, sell_price, sell_time
                FROM user_flips
                WHERE account_id = ? AND status = 'completed' AND profit IS NOT NULL
                ORDER BY profit DESC
                LIMIT 1
            ''', (account_id,))
            row = _res.mappings().fetchone()
            best_single = dict(row) if row else None
            # Worst single flip
            _res = execute_query(session, '''
                SELECT item_id, item_name, profit, roi, quantity_total, buy_price, sell_price, sell_time
                FROM user_flips
                WHERE account_id = ? AND status = 'completed' AND profit IS NOT NULL
                ORDER BY profit ASC
                LIMIT 1
            ''', (account_id,))
            row = _res.mappings().fetchone()
            worst_single = dict(row) if row else None
            # Members vs F2P breakdown
            _res = execute_query(session, '''
                SELECT i.members,
                       COUNT(*) as flip_count,
                       SUM(uf.profit) as total_profit,
                       AVG(uf.roi) as avg_roi
                FROM user_flips uf
                JOIN items i ON uf.item_id = i.id
                WHERE uf.account_id = ? AND uf.status = 'completed'
                GROUP BY i.members
            ''', (account_id,))
            members_breakdown = []
            for row in _res.mappings().fetchall():
                r = dict(row)
                r['category'] = 'Members' if r['members'] else 'F2P'
                members_breakdown.append(r)
            # Total volume traded
            _res = execute_query(session, '''
                SELECT SUM(quantity_total) as total_volume,
                       SUM(buy_price * quantity_total) as total_turnover
                FROM user_flips
                WHERE account_id = ? AND status = 'completed'
            ''', (account_id,))
            volume = dict(_res.mappings().fetchone())
            # Most profitable day
            best_day = max(daily_profit, key=lambda d: d['profit']) if daily_profit else None
            return {
                "best_items": best_items,
                "worst_items": worst_items,
                "most_traded": most_traded,
                "daily_profit": daily_profit,
                "best_single_flip": best_single,
                "worst_single_flip": worst_single,
                "members_breakdown": members_breakdown,
                "total_volume_traded": volume.get('total_volume') or 0,
                "total_turnover": volume.get('total_turnover') or 0,
                "best_day": best_day,
            }

    @staticmethod
    def export_csv(account_id: int) -> str:
        """Export all flips for an account to CSV"""
        with get_db() as session:
            _res = execute_query(session, '''
                SELECT * FROM user_flips 
                WHERE account_id = ?
                ORDER BY buy_time DESC
            ''', (account_id,))
            flips = [dict(row) for row in _res.mappings().fetchall()]
        
        output = io.StringIO()
        if not flips:
            return ""
            
        # Define headers
        fieldnames = [
            'item_id', 'item_name', 'quantity_total', 'quantity_remaining', 
            'buy_price', 'sell_price', 'intended_sell_price', 'intended_quantity',
            'buy_time', 'sell_time', 'profit', 'roi', 'status', 'notes'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for flip in flips:
            row = {k: flip.get(k) for k in fieldnames}
            # Format datetimes
            if row.get('buy_time') and isinstance(row['buy_time'], datetime):
                row['buy_time'] = row['buy_time'].isoformat()
            if row.get('sell_time') and isinstance(row['sell_time'], datetime):
                row['sell_time'] = row['sell_time'].isoformat()
            writer.writerow(row)
            
        return output.getvalue()

    @staticmethod
    def import_csv(account_id: int, file_content: str) -> Dict:
        """Import flips from CSV content"""
        # Handle potential BOM or encoding issues if passed as string
        reader = csv.DictReader(io.StringIO(file_content))
        
        stats = {"imported": 0, "errors": 0, "skipped": 0, "details": []}
        
        with get_db() as session:
            
            for i, row in enumerate(reader):
                try:
                    # Basic validation
                    if not row.get('item_id') or not row.get('quantity_total'):
                        stats['skipped'] += 1
                        continue
                        
                    # Parse fields
                    try:
                        item_id = int(row['item_id'])
                        qty_total = int(row['quantity_total'])
                        qty_remaining = int(row['quantity_remaining'])
                        buy_price = int(row['buy_price'])
                        sell_price = int(row['sell_price']) if row.get('sell_price') else None
                        intended_qty = int(row['intended_quantity']) if row.get('intended_quantity') else None
                        intended_sell_price = int(row['intended_sell_price']) if row.get('intended_sell_price') else None
                        profit = int(row['profit']) if row.get('profit') else None
                        roi = float(row['roi']) if row.get('roi') else None
                    except ValueError as e:
                        stats['errors'] += 1
                        stats['details'].append(f"Row {i+1}: Invalid number format - {e}")
                        continue

                    # Verify item exists
                    _res = execute_query(session, "SELECT id, name FROM items WHERE id = ?", (item_id,))
                    item = _res.mappings().fetchone()
                    
                    # If ID doesn't match, try name
                    if not item and row.get('item_name'):
                        _res = execute_query(session, "SELECT id, name FROM items WHERE lower(name) = lower(?)", (row['item_name'],))
                        item = _res.mappings().fetchone()
                        if item:
                            item_id = item['id'] # Update ID to match DB
                    
                    if not item:
                        stats['errors'] += 1
                        stats['details'].append(f"Row {i+1}: Item not found (ID: {item_id}, Name: {row.get('item_name')})")
                        continue
                    
                    item_name = item['name']
                    
                    # Handle dates
                    try:
                        buy_time = datetime.fromisoformat(row['buy_time']) if row.get('buy_time') else datetime.now(timezone.utc)
                        sell_time = datetime.fromisoformat(row['sell_time']) if row.get('sell_time') else None
                    except ValueError:
                        buy_time = datetime.now(timezone.utc)
                        sell_time = None
                    
                    status = row.get('status', 'pending')
                    
                    # Insert flip
                    _res = execute_query(session, '''
                        INSERT INTO user_flips (
                            account_id, item_id, item_name, quantity_total, quantity_remaining,
                            buy_price, sell_price, buy_time, sell_time,
                            profit, roi, status, notes, intended_quantity, intended_sell_price,
                            last_buy_at, last_sell_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        account_id, item_id, item_name, qty_total, qty_remaining,
                        buy_price, sell_price, buy_time, sell_time,
                        profit, roi, status, row.get('notes'),
                        intended_qty, intended_sell_price,
                        buy_time, sell_time if sell_time else None
                    ))
                    
                    flip_id = _res.scalar()
                    
                    # Synthesize transactions
                    # Buy
                    _res = execute_query(session, '''
                        INSERT INTO flip_transactions (flip_id, transaction_type, mutation_type, quantity, price, timestamp, notes)
                        VALUES (?, 'buy', 'import', ?, ?, ?, 'Imported buy')
                    ''', (flip_id, qty_total, buy_price, buy_time))
                    
                    # Sell (if applicable)
                    if sell_time and qty_total > qty_remaining:
                        qty_sold = qty_total - qty_remaining
                        sell_p = sell_price if sell_price else 0
                        _res = execute_query(session, '''
                            INSERT INTO flip_transactions (flip_id, transaction_type, mutation_type, quantity, price, timestamp, notes)
                            VALUES (?, 'sell', 'import', ?, ?, ?, 'Imported sell')
                        ''', (flip_id, qty_sold, sell_p, sell_time))
                        
                    stats['imported'] += 1
                    
                except Exception as e:
                    stats['errors'] += 1
                    stats['details'].append(f"Row {i+1}: Unexpected error - {e}")
            
            session.commit()
            
        return stats
