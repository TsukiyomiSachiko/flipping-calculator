#!/usr/bin/env python3
"""
Price History Seeding Script

This script helps seed the price history database with initial data.
It can backfill historical data by fetching from the Wiki's /timeseries endpoint
and importing it into the local database.

IMPORTANT - SELF-IMPOSED RATE LIMITS:
    The OSRS Wiki API has no explicit rate limit, but we use a conservative
    5-second delay to be respectful of their resources.
    
    With 5s delay:
        - 50 items = ~4 minutes
        - 100 items = ~8 minutes
        - 500 items = ~42 minutes
        - All items (~3000) = ~4 hours
    
    You can adjust the delay with --delay if needed.

TIMESTEP COVERAGE (Wiki API returns max 365 datapoints):
    - 5m timestep: 365 × 5min = 30 hours of data
    - 1h timestep: 365 × 1h = 15 days of data
    - 6h timestep: 365 × 6h = 91 days of data (DEFAULT - covers 45+ day requirement)

SMART SKIPPING:
    The script automatically skips items that already have sufficient historical
    data (45+ days back). This prevents redundant API calls and speeds up re-runs.

Usage:
    python seed_price_history.py --items 2,4,6  # Seed specific items
    python seed_price_history.py --top 100      # Seed top 100 traded items
    python seed_price_history.py --all          # Seed all items (~4 hours)
    python seed_price_history.py --top 50 --timestep 5m  # 30h of granular data
"""

import sys
import os
import argparse
import time
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.api_client import fetch_price_timeseries, fetch_latest_prices
from app.services.price_history_service import PriceHistoryService
from app.utils.database import init_database, get_db

logger = logging.getLogger(__name__)


def has_sufficient_data(item_id: int, days_required: int = 45) -> bool:
    """
    Check if an item already has sufficient historical data
    
    Args:
        item_id: The item to check
        days_required: Number of days of history required (default 45)
    
    Returns:
        True if item has at least days_required of data
    """
    try:
        from sqlalchemy import text
        with get_db() as session:
            result = session.execute(text('''
                SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest, COUNT(*) as count
                FROM price_history
                WHERE item_id = :item_id
            '''), {'item_id': item_id})
            row = result.fetchone()
            
            if not row or row[2] == 0:  # count is at index 2
                return False
            
            oldest = row[0]  # oldest at index 0
            newest = row[1]  # newest at index 1
            
            if not oldest or not newest:
                return False
            
            # Calculate days of coverage
            days_of_data = (newest - oldest).total_seconds() / (24 * 3600)
            
            return days_of_data >= days_required
            
    except Exception as e:
        # If there's any error checking, assume we don't have data
        logger.warning(f"Error checking data for item {item_id}: {e}")
        return False


def seed_item_history(item_id: int, timestep: str = '6h'):
    """
    Fetch historical data for an item and import it into local database
    
    Args:
        item_id: The item to seed
        timestep: Time interval to fetch ('5m', '1h', '6h')
                 
    Wiki API returns maximum 365 datapoints:
        - 5m timestep = 30 hours of data (365 × 5min)
        - 1h timestep = 15 days of data (365 × 1h)
        - 6h timestep = 91 days of data (365 × 6h) ✓ Covers 45-day requirement
    
    Returns:
        Number of snapshots saved
    """
    print(f"Seeding item {item_id} with {timestep} data...")
    
    try:
        # Fetch from Wiki API
        data = fetch_price_timeseries(item_id, timestep)
        
        if 'data' not in data or not data['data']:
            print(f"  ⚠️  No data available for item {item_id}")
            return 0
        
        # Convert to our format and save in batches
        snapshots = data['data']
        saved_count = 0
        
        # Debug: Check first and last timestamp
        if len(snapshots) > 0:
            first_ts = snapshots[0].get('timestamp')
            last_ts = snapshots[-1].get('timestamp')
            if first_ts and last_ts:
                from datetime import datetime
                first_date = datetime.fromtimestamp(first_ts)
                last_date = datetime.fromtimestamp(last_ts)
                print(f"  📅 Date range: {last_date.strftime('%Y-%m-%d')} to {first_date.strftime('%Y-%m-%d')}")
        
        for snapshot in snapshots:
            timestamp = snapshot.get('timestamp')
            if not timestamp:
                continue
            
            # Create a temporary item data dict for this snapshot
            item_data = {
                item_id: {
                    'high': snapshot.get('avgHighPrice'),
                    'low': snapshot.get('avgLowPrice'),
                    'highTime': timestamp,
                    'lowTime': timestamp,
                    'highPriceVolume': snapshot.get('highPriceVolume', 0),
                    'lowPriceVolume': snapshot.get('lowPriceVolume', 0),
                }
            }
            
            # Save this snapshot - each call is a separate transaction
            try:
                result = PriceHistoryService.save_price_snapshot(item_data)
                saved_count += result
            except Exception as e:
                # Skip this snapshot on error but continue with others
                logger.debug(f"Failed to save snapshot for item {item_id}: {e}")
                continue
        
        if saved_count == 0 and len(snapshots) > 0:
            print(f"  ⚠️  All {len(snapshots)} snapshots were duplicates (already in database)")
        else:
            print(f"  ✓ Saved {saved_count}/{len(snapshots)} snapshots for item {item_id}")
        return saved_count
        
    except Exception as e:
        print(f"  ❌ Failed to seed item {item_id}: {e}")
        return 0


def get_top_traded_items(limit: int = 100):
    """Get list of most traded items from current market data"""
    print(f"Fetching top {limit} traded items...")
    
    try:
        # Use /5m endpoint which has volume data
        from app.utils.api_client import fetch_5m_volume_data
        data = fetch_5m_volume_data(use_cache=False)
        
        if 'data' not in data:
            print("Failed to fetch volume data")
            return []
        
        # Sort by trading activity (high + low volumes)
        items_with_volume = []
        for item_id, prices in data['data'].items():
            high_vol = prices.get('highPriceVolume', 0)
            low_vol = prices.get('lowPriceVolume', 0)
            total_vol = high_vol + low_vol
            
            if total_vol > 0:
                items_with_volume.append((int(item_id), total_vol))
        
        # Sort by volume descending
        items_with_volume.sort(key=lambda x: x[1], reverse=True)
        
        top_items = [item_id for item_id, vol in items_with_volume[:limit]]
        print(f"Found {len(top_items)} items with trading volume")
        
        return top_items
        
    except Exception as e:
        print(f"Failed to fetch top items: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Seed price history database')
    parser.add_argument('--items', type=str, help='Comma-separated item IDs to seed')
    parser.add_argument('--top', type=int, help='Seed top N traded items')
    parser.add_argument('--all', action='store_true', help='Seed all items (very slow!)')
    parser.add_argument('--timestep', type=str, default='6h', choices=['5m', '1h', '6h'],
                       help='Time interval (default: 6h for 91 days coverage). 5m=30h, 1h=15d, 6h=91d')
    parser.add_argument('--delay', type=float, default=5.0,
                       help='Delay between requests in seconds (default: 5)')
    parser.add_argument('--force', action='store_true',
                       help='Force re-seed even if item has sufficient data (45+ days)')
    
    args = parser.parse_args()
    
    # Initialize database
    print("Initializing database...")
    init_database()
    
    # Calculate estimated time for user
    def format_duration(seconds):
        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            return f"{seconds/60:.1f} minutes"
        else:
            return f"{seconds/3600:.1f} hours"
    
    # Determine which items to seed
    items_to_seed = []
    
    if args.items:
        items_to_seed = [int(x.strip()) for x in args.items.split(',')]
        print(f"Seeding {len(items_to_seed)} specific items")
    elif args.top:
        items_to_seed = get_top_traded_items(args.top)
    elif args.all:
        print("⚠️  Seeding all items will take a very long time!")
        print("⚠️  The OSRS Wiki API allows 10 requests per 5 minutes.")
        
        # Fetch all items from the items table in database
        from sqlalchemy import text
        with get_db() as session:
            result = session.execute(text('SELECT id FROM items ORDER BY id'))
            all_items = [row[0] for row in result.fetchall()]
        
        item_count = len(all_items)
        estimated_time = item_count * args.delay
        print(f"⚠️  Found {item_count} items in database")
        print(f"⚠️  Estimated time with {args.delay}s delay: {format_duration(estimated_time)}")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted")
            return
        items_to_seed = all_items
        print(f"Will attempt to seed {len(items_to_seed)} items")
    else:
        print("Error: Must specify --items, --top, or --all")
        parser.print_help()
        return
    
    # Filter items based on existing data (unless --force)
    if not args.force:
        print(f"\n🔍 Checking which items already have sufficient data (45+ days)...")
        items_needing_seed = []
        items_skipped = 0
        
        for item_id in items_to_seed:
            if has_sufficient_data(item_id, days_required=45):
                items_skipped += 1
            else:
                items_needing_seed.append(item_id)
        
        if items_skipped > 0:
            print(f"✓ Skipping {items_skipped} items that already have sufficient data")
            print(f"📝 Will seed {len(items_needing_seed)} items that need data")
        
        items_to_seed = items_needing_seed
    else:
        print(f"\n⚠️  Force mode enabled - will re-seed all items")
    
    if len(items_to_seed) == 0:
        print("\n✅ All items already have sufficient data! Nothing to do.")
        return
    
    # Show estimated time
    if len(items_to_seed) > 10:
        estimated_time = len(items_to_seed) * args.delay
        print(f"\n⏱️  Estimated time: {format_duration(estimated_time)}")
        print(f"⏳ Delay: {args.delay}s between requests")
    
    # Seed each item
    total_seeded = 0
    total_skipped_no_data = 0
    print(f"\nSeeding {len(items_to_seed)} items with {args.timestep} data...")
    print(f"Delay between requests: {args.delay}s")
    print("-" * 50)
    
    start_time = time.time()
    
    for i, item_id in enumerate(items_to_seed, 1):
        print(f"[{i}/{len(items_to_seed)}]", end=' ')
        seeded = seed_item_history(item_id, args.timestep)
        
        if seeded == 0:
            total_skipped_no_data += 1
        else:
            total_seeded += seeded
        
        # Show progress with time estimate
        if i % 10 == 0 and i < len(items_to_seed):
            elapsed = time.time() - start_time
            items_remaining = len(items_to_seed) - i
            time_per_item = elapsed / i
            estimated_remaining = items_remaining * time_per_item
            print(f"  Progress: {i}/{len(items_to_seed)} ({(i/len(items_to_seed)*100):.1f}%) - ETA: {format_duration(estimated_remaining)}")
        
        # Respect self-imposed rate limit
        if i < len(items_to_seed):
            time.sleep(args.delay)
    
    elapsed_total = time.time() - start_time
    print("-" * 50)
    print(f"\n✅ Seeding complete!")
    print(f"Total snapshots imported: {total_seeded}")
    if total_skipped_no_data > 0:
        print(f"Items with no data available: {total_skipped_no_data}")
    print(f"Total time: {format_duration(elapsed_total)}")
    
    # Show stats
    try:
        stats = PriceHistoryService.get_database_stats()
        print(f"\nDatabase statistics:")
        print(f"  Total records: {stats['total_records']}")
        print(f"  Unique items: {stats['unique_items']}")
        print(f"  Date range: {stats['oldest_date']} to {stats['newest_date']}")
        print(f"  Coverage: {stats['date_range_hours']:.1f} hours")
    except Exception as e:
        print(f"\n⚠️  Could not fetch database stats: {e}")


if __name__ == '__main__':
    main()