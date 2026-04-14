import requests
from datetime import datetime, timezone

API_ENDPOINT = "https://prices.runescape.wiki/api/v1/osrs"
USER_AGENT = "OSRS Flipping Calculator Diagnostic"

def check():
    headers = {'User-Agent': USER_AGENT}
    print("Fetching /5m data...")
    response = requests.get(f"{API_ENDPOINT}/5m", headers=headers)
    data = response.json()
    
    if 'data' not in data:
        print("Error: No data in response")
        return

    item_data = data['data']
    api_ts = data.get('timestamp')
    if api_ts:
        dt = datetime.fromtimestamp(api_ts, tz=timezone.utc)
        print(f"API Result Timestamp: {api_ts} ({dt.isoformat()})")
    
    print(f"Number of items in /5m: {len(item_data)}")
    
    # Check /latest too
    print("\nFetching /latest data...")
    response = requests.get(f"{API_ENDPOINT}/latest", headers=headers)
    data = response.json()
    item_data = data['data']
    
    # Check first item
    first_id = list(item_data.keys())[0]
    first_item = item_data[first_id]
    ts = first_item.get('highTime') or first_item.get('lowTime')
    if ts:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        print(f"First item ({first_id}) timestamp in /latest: {ts} ({dt.isoformat()})")

if __name__ == "__main__":
    check()
