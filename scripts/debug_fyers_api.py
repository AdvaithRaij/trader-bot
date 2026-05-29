#!/usr/bin/env python3
"""
Debug script to see actual Fyers API responses
"""

import sys
import json
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from config import get_config
from fyers_apiv3 import fyersModel

def debug_fyers_api():
    """Debug Fyers API responses"""
    print("🔍 Debugging Fyers API Responses")
    print("=" * 60)
    
    config = get_config()
    
    # Initialize Fyers API
    fyers = fyersModel.FyersModel(
        client_id=config.FYERS_APP_ID,
        is_async=False,
        token=config.FYERS_ACCESS_TOKEN,
        log_path=""
    )
    
    print("✅ Fyers API initialized\n")
    
    # Test 1: Get Profile
    print("📊 Test 1: Get Profile")
    print("-" * 60)
    try:
        profile = fyers.get_profile()
        print(json.dumps(profile, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 2: Get Funds
    print("📊 Test 2: Get Funds")
    print("-" * 60)
    try:
        funds = fyers.funds()
        print(json.dumps(funds, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 3: Get Quotes
    print("📊 Test 3: Get Quotes for NSE:RELIANCE-EQ")
    print("-" * 60)
    try:
        quotes = fyers.quotes({"symbols": "NSE:RELIANCE-EQ"})
        print(json.dumps(quotes, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 4: Get Positions
    print("📊 Test 4: Get Positions")
    print("-" * 60)
    try:
        positions = fyers.positions()
        print(json.dumps(positions, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")
    print()
    
    # Test 5: Get Orders
    print("📊 Test 5: Get Orders")
    print("-" * 60)
    try:
        orders = fyers.orderbook()
        print(json.dumps(orders, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")
    print()

if __name__ == "__main__":
    debug_fyers_api()

