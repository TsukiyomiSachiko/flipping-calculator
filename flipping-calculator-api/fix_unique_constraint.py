"""
Fix missing UNIQUE constraint on price_history table

This constraint is required for the ON CONFLICT clause to work properly
when seeding price history data.
"""
import sys
sys.path.append('.')

from app.utils.database import get_db
from sqlalchemy import text

print("🔧 Fixing missing UNIQUE constraint on price_history table...\n")

try:
    with get_db() as session:
        # First check for duplicates
        print("1. Checking for duplicate records...")
        result = session.execute(text('''
            SELECT COUNT(*) as duplicate_count
            FROM (
                SELECT item_id, timestamp, COUNT(*) as cnt
                FROM price_history
                GROUP BY item_id, timestamp
                HAVING COUNT(*) > 1
            ) duplicates
        '''))
        dup_count = result.fetchone()[0]
        
        if dup_count > 0:
            print(f"   ⚠️  Found {dup_count} duplicate (item_id, timestamp) combinations")
            print(f"   These must be removed before adding UNIQUE constraint")
            print(f"\n   Run this to remove duplicates (keeps oldest record):")
            print(f"   DELETE FROM price_history WHERE id NOT IN (")
            print(f"       SELECT MIN(id) FROM price_history GROUP BY item_id, timestamp")
            print(f"   );")
            sys.exit(1)
        else:
            print("   ✓ No duplicates found")
        
        # Add the UNIQUE constraint
        print("\n2. Adding UNIQUE constraint...")
        session.execute(text('''
            ALTER TABLE price_history 
            ADD CONSTRAINT price_history_item_timestamp_unique 
            UNIQUE (item_id, timestamp)
        '''))
        print("   ✓ Successfully added constraint!")
        
        # Verify it was added
        print("\n3. Verifying constraint...")
        result = session.execute(text('''
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'price_history' AND constraint_type = 'UNIQUE'
        '''))
        
        constraints = result.fetchall()
        if constraints:
            print("   ✓ UNIQUE constraints on price_history:")
            for row in constraints:
                print(f"      - {row[0]}: {row[1]}")
        else:
            print("   ❌ No UNIQUE constraints found!")
            
        print("\n✅ Done! You can now run the seed script successfully.")
            
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
