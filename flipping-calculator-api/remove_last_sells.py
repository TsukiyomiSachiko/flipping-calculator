"""
Remove the last 2 sell transactions and recalculate flip state

This script will:
1. Find the last 2 sell transactions
2. Remove them from flip_transactions
3. Recalculate the flip's quantity_remaining, profit, and status
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import get_db


def remove_last_sells():
    """Remove the last 2 sell transactions and fix flip state"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get the last 2 sell transactions
        cursor.execute("""
            SELECT id, flip_id, quantity, price, timestamp 
            FROM flip_transactions 
            WHERE transaction_type = 'sell' 
            ORDER BY timestamp DESC, id DESC 
            LIMIT 3
        """)
        
        transactions = cursor.fetchall()
        
        if len(transactions) == 0:
            print("No sell transactions found!")
            return
        
        print(f"\nFound {len(transactions)} sell transaction(s) to remove:")
        for txn in transactions:
            print(f"  Transaction #{txn['id']}: Flip #{txn['flip_id']} - {txn['quantity']}x @ {txn['price']} gp ({txn['timestamp']})")
        
        # Confirm
        response = input("\nRemove these transactions? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
        
        # Process each transaction
        for txn in transactions:
            flip_id = txn['flip_id']
            sell_qty = txn['quantity']
            sell_price = txn['price']
            
            # Get current flip state
            cursor.execute("SELECT * FROM user_flips WHERE id = ?", (flip_id,))
            flip = cursor.fetchone()
            
            if not flip:
                print(f"Warning: Flip #{flip_id} not found, skipping transaction #{txn['id']}")
                continue
            
            print(f"\nProcessing flip #{flip_id} ({flip['item_name']}):")
            print(f"  Current state: {flip['quantity_remaining']} remaining, profit: {flip['profit'] if flip['profit'] is not None else 0}")
            
            # Calculate GE tax that was deducted
            ge_tax_per_item = max(1, int(sell_price * 0.01)) if sell_price > 100 else 0
            ge_tax_total = ge_tax_per_item * sell_qty
            
            # Calculate profit that was recorded for this sale
            profit_per_item = sell_price - flip['buy_price'] - ge_tax_per_item
            profit_this_sale = profit_per_item * sell_qty
            
            # Reverse the changes
            new_remaining = flip['quantity_remaining'] + sell_qty
            new_profit = (flip['profit'] if flip['profit'] is not None else 0) - profit_this_sale
            
            # Reverse the cash adjustment (refund the sell revenue)
            sell_revenue = sell_qty * (sell_price - ge_tax_per_item)
            
            print(f"  Reversing: +{sell_qty} quantity, -{profit_this_sale} profit, -{sell_revenue} cash")
            
            # Delete the transaction
            cursor.execute("DELETE FROM flip_transactions WHERE id = ?", (txn['id'],))
            
            # Update flip state
            # Check if this was the only sale (going back to pending)
            cursor.execute("""
                SELECT COUNT(*) as count FROM flip_transactions 
                WHERE flip_id = ? AND transaction_type = 'sell'
            """, (flip_id,))
            remaining_sells = cursor.fetchone()['count']
            
            if remaining_sells == 0:
                # No more sells - back to pending
                new_status = 'pending'
                cursor.execute("""
                    UPDATE user_flips 
                    SET quantity_remaining = ?, profit = NULL, roi = NULL, 
                        sell_price = NULL, status = ?
                    WHERE id = ?
                """, (new_remaining, new_status, flip_id))
                print(f"  Updated flip: {new_remaining} remaining, status={new_status}, profit/roi cleared")
            else:
                # Still have other sells
                new_status = 'partially_completed' if new_remaining > 0 else flip['status']
                cursor.execute("""
                    UPDATE user_flips 
                    SET quantity_remaining = ?, profit = ?, status = ?
                    WHERE id = ?
                """, (new_remaining, new_profit, new_status, flip_id))
                print(f"  Updated flip: {new_remaining} remaining, profit={new_profit}, status={new_status}")
            
            # Reverse cash adjustment
            cursor.execute("""
                UPDATE user_settings 
                SET available_cash = available_cash - ?
                WHERE id = 1
            """, (sell_revenue,))
            print(f"  Reversed cash: -{sell_revenue} gp")
        
        conn.commit()
        print(f"\n✓ Successfully removed {len(transactions)} transaction(s) and updated flip state")


if __name__ == "__main__":
    remove_last_sells()