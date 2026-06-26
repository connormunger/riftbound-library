#!/usr/bin/env python3
import sqlite3
import urllib.request
import urllib.error
import json
import sys
import os
from datetime import datetime, timezone

# Use absolute paths so systemd can find everything
DB_PATH = "/home/connormunger/tcg-app/tcg.db"
KEY_FILE = "/home/connormunger/tcg-app/data/tcgapi_key.txt"
API_BASE = "https://api.tcgapi.dev/v1"

def get_api_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            return f.read().strip()
    print("No API key found. Ensure data/tcgapi_key.txt exists.")
    sys.exit(1)

def api_get(path, api_key):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={
        "X-API-Key": api_key,
        "User-Agent": "riftbound-library/2.0 (SQLite)"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
            return body.get("data"), body.get("rate_limit", {})
    except urllib.error.HTTPError as e:
        raise e

def sync_prices():
    api_key = get_api_key()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get the queue: Only cards in inventory, sorted by the oldest price check
    c.execute('''
        SELECT DISTINCT 
            c.id, c.tcgplayer_id, c.name, 
            MAX(ph.updated_at) as last_fetched
        FROM cards c
        JOIN inventory i ON c.id = i.card_id
        LEFT JOIN price_history ph ON c.id = ph.card_id
        WHERE c.tcgplayer_id IS NOT NULL AND c.tcgplayer_id != ''
        GROUP BY c.id
        ORDER BY last_fetched ASC
    ''')
    
    queue = c.fetchall()
    print(f"Queue loaded. {len(queue)} unique owned products to check.")

    fetched_count = 0
    inserted_count = 0

    for card_id, tcg_id, name, last_fetched in queue:
        try:
            data, rate_limit = api_get(f"/cards/tcgplayer/{tcg_id}", api_key)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("Daily 100-request rate limit reached.")
                break
            print(f"Error fetching {name} ({tcg_id}): HTTP {e.code}")
            continue
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            continue

        fetched_count += 1
        
        if not data or "prices" not in data:
            continue

        prices = data["prices"]
        if isinstance(prices, dict):
            prices = [prices]

        now = datetime.now(timezone.utc).isoformat()
        updated_printings = []
        
        # Save EVERY valid market price (Normal and Foil) independently
        for p in prices:
            if p.get("market_price"):
                market_price = float(p.get("market_price"))
                is_holo_val = 1 if p.get("printing", "").lower() == "foil" else 0
                
                c.execute("INSERT INTO price_history (card_id, price, updated_at, is_holo) VALUES (?, ?, ?, ?)", 
                          (card_id, market_price, now, is_holo_val))
                inserted_count += 1
                updated_printings.append(f"{p.get('printing')} ${market_price:.2f}")

        if updated_printings:
            print(f"[{fetched_count}] {name} updated: {', '.join(updated_printings)}")

        # Check API limit headers to gracefully stop
        if rate_limit.get("daily_remaining", 1) <= 0:
            print("Daily quota exhausted. Stopping.")
            break

    conn.commit()
    conn.close()
    print(f"Sync complete. Fetched {fetched_count} APIs, inserted {inserted_count} new prices.")

if __name__ == '__main__':
    sync_prices()
