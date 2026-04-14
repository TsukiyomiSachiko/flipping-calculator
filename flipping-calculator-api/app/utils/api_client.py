import requests
from typing import Dict, Optional
import json
import os
from datetime import datetime, timedelta, timezone

API_ENDPOINT = "https://prices.runescape.wiki/api/v1/osrs"
USER_AGENT = "OSRS Flipping Calculator API/2.0"
CACHE_DIR = os.getenv("API_CACHE_DIR", "data/cache")

class CacheManager:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
    
    def get_cache_path(self, key: str) -> str:
        return os.path.join(CACHE_DIR, f"{key}.json")
    
    def get(self, key: str, max_age_minutes: int) -> Optional[Dict]:
        cache_path = self.get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        # Check age
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path), tz=timezone.utc)
        if datetime.now(timezone.utc) - file_time > timedelta(minutes=max_age_minutes):
            return None
        
        with open(cache_path, 'r') as f:
            return json.load(f)
    
    def set(self, key: str, data: Dict):
        cache_path = self.get_cache_path(key)
        with open(cache_path, 'w') as f:
            json.dump(data, f)
    
    def clear(self, key: str):
        cache_path = self.get_cache_path(key)
        if os.path.exists(cache_path):
            os.remove(cache_path)

cache = CacheManager()

def fetch_item_mapping(use_cache: bool = True) -> Dict:
    """Fetch item mapping from OSRS Wiki API"""
    if use_cache:
        cached = cache.get('item_mapping', max_age_minutes=1440)  # 24 hours
        if cached:
            return cached
    
    headers = {'User-Agent': USER_AGENT}
    response = requests.get(f"{API_ENDPOINT}/mapping", headers=headers)
    response.raise_for_status()
    data = response.json()
    
    cache.set('item_mapping', data)
    return data

def fetch_latest_prices(use_cache: bool = True) -> Dict:
    """Fetch latest prices from /latest endpoint"""
    if use_cache:
        cached = cache.get('latest_prices', max_age_minutes=5)
        if cached:
            return cached
    
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] 📡 Fetching fresh data from OSRS Wiki /latest...")
    headers = {'User-Agent': USER_AGENT}
    response = requests.get(f"{API_ENDPOINT}/latest", headers=headers)
    response.raise_for_status()
    data = response.json()
    
    cache.set('latest_prices', data)
    return data

def fetch_volume_data(use_cache: bool = True) -> Dict:
    """Fetch volume data from /1h endpoint"""
    if use_cache:
        cached = cache.get('1h_volume', max_age_minutes=15)
        if cached:
            return cached
    
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] 📡 Fetching fresh data from OSRS Wiki /1h...")
    headers = {'User-Agent': USER_AGENT}
    response = requests.get(f"{API_ENDPOINT}/1h", headers=headers)
    response.raise_for_status()
    data = response.json()
    
    cache.set('1h_volume', data)
    return data

def fetch_5m_volume_data(use_cache: bool = True) -> Dict:
    """Fetch volume data from /5m endpoint (used for Erebus scoring)"""
    if use_cache:
        cached = cache.get('5m_volume', max_age_minutes=5)
        if cached:
            return cached
    
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] 📡 Fetching fresh data from OSRS Wiki /5m...")
    headers = {'User-Agent': USER_AGENT}
    response = requests.get(f"{API_ENDPOINT}/5m", headers=headers)
    response.raise_for_status()
    data = response.json()
    
    cache.set('5m_volume', data)
    return data

def fetch_price_timeseries(item_id: int, timestep: str = '5m') -> Dict:
    """
    Fetch price history timeseries for a specific item
    
    Args:
        item_id: The item ID to fetch data for
        timestep: Time interval - '5m', '1h', or '6h'
    
    Returns:
        Dict with 'data' containing list of {timestamp, avgHighPrice, avgLowPrice, highPriceVolume, lowPriceVolume}
    """
    # Cache key includes item_id and timestep
    cache_key = f'timeseries_{item_id}_{timestep}'
    
    # Cache for different durations based on timestep
    cache_minutes = {
        '5m': 5,   # 5 minute data - cache for 5 minutes
        '1h': 30,  # 1 hour data - cache for 30 minutes
        '6h': 120  # 6 hour data - cache for 2 hours
    }.get(timestep, 5)
    
    cached = cache.get(cache_key, max_age_minutes=cache_minutes)
    if cached:
        return cached
    
    headers = {'User-Agent': USER_AGENT}
    response = requests.get(f"{API_ENDPOINT}/timeseries", 
                           params={'timestep': timestep, 'id': item_id},
                           headers=headers)
    response.raise_for_status()
    data = response.json()
    
    cache.set(cache_key, data)
    return data

def clear_all_caches():
    """Clear all cached data"""
    cache.clear('latest_prices')
    cache.clear('1h_volume')
    cache.clear('5m_volume')
    cache.clear('item_mapping')
    # Note: timeseries caches are item-specific and cleared automatically by age