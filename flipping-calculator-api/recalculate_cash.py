"""
Recalculate cash stack based on current flip state

Calculates what available_cash SHOULD be based on:
- All pending/partially_completed flips (reserved cash)
- All completed sales (realized revenue after tax)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import get_db


def calculate_ge_tax(price):
    """Calculate GE tax per item"""
    if price <= 100:
        return 0
    return max(1, int(price * 0.01))


def recalculate_cash(starting_cash=10_000_000):
    """Recalculate what cash should be"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        print(f"Starting cash: {starting_cash:,} gp\n")
        
        # Get all active flips
        cursor.execute("""
            SELECT * FROM user_flips 
            WHERE status IN ('pending', 'partially_completed')
            ORDER BY id
        """)
        flips = cursor.fetchall()
        
        total_reserved = 0
        total_revenue = 0
        
        for flip in flips:
            flip_dict = dict(flip)
            flip_id = flip_dict['id']
            item_name = flip_dict['item_name']
            buy_price = flip_dict['buy_price']
            sell_price = flip_dict.get('sell_price')
            quantity_total = flip_dict['quantity_total']
            quantity_remaining = flip_dict['quantity_remaining']
            intended_quantity = flip_dict.get('intended_quantity')
            
            print(f"Flip #{flip_id}: {item_name}")
            print(f"  Buy price: {buy_price} gp")
            print(f"  Quantity: {quantity_total} bought, {quantity_remaining} remaining")
            
            # Calculate reserved cash (based on intended_quantity)
            if intended_quantity:
                reserved = intended_quantity * buy_price
                print(f"  Reserved: {reserved:,} gp (for {intended_quantity} intended)")
            else:
                reserved = quantity_total * buy_price
                print(f"  Reserved: {reserved:,} gp (for {quantity_total} bought)")
            
            total_reserved += reserved
            
            # Calculate realized revenue from sells
            sold_qty = quantity_total - quantity_remaining
            if sold_qty > 0 and sell_price:
                gross_revenue = sold_qty * sell_price
                tax_per_item = calculate_ge_tax(sell_price)
                total_tax = tax_per_item * sold_qty
                net_revenue = gross_revenue - total_tax
                
                print(f"  Sold: {sold_qty} @ {sell_price} gp")
                print(f"  Revenue: {net_revenue:,} gp (after {total_tax} gp tax)")
                total_revenue += net_revenue
            
            print()
        
        # Calculate expected cash
        expected_cash = starting_cash - total_reserved + total_revenue
        
        print("=" * 60)
        print(f"Total reserved: {total_reserved:,} gp")
        print(f"Total revenue: {total_revenue:,} gp")
        print(f"Expected available cash: {expected_cash:,} gp")
        print("=" * 60)
        
        # Get current cash
        cursor.execute("SELECT available_cash FROM user_settings WHERE id = 1")
        current = cursor.fetchone()['available_cash']
        print(f"\nCurrent cash in database: {current:,} gp")
        print(f"Difference: {expected_cash - current:,} gp")
        
        # Ask to update
        response = input(f"\nSet available_cash to {expected_cash:,} gp? (yes/no): ")
        if response.lower() == 'yes':
            cursor.execute("""
                UPDATE user_settings 
                SET available_cash = ? 
                WHERE id = 1
            """, (expected_cash,))
            conn.commit()
            print(f"✓ Updated available_cash to {expected_cash:,} gp")
        else:
            print("Cancelled.")


if __name__ == "__main__":
    # Default starting cash is 10M, but you can override
    import sys
    starting = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000_000
    recalculate_cash(starting)
