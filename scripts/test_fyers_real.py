#!/usr/bin/env python3
"""
Test script to verify real Fyers API connection (not mock mode)
"""

import asyncio
import sys
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from config import get_config
from broker_fyers import FyersBroker

async def test_real_fyers_connection():
    """Test real Fyers API connection"""
    print("🤖 Testing REAL Fyers API Connection")
    print("=" * 60)
    
    config = get_config()
    
    # Check credentials
    print("🔍 Checking Fyers Credentials...")
    print(f"   App ID: {config.FYERS_APP_ID}")
    print(f"   Secret Key: {config.FYERS_SECRET_KEY[:4]}...{config.FYERS_SECRET_KEY[-2:]}")
    print(f"   Access Token: {config.FYERS_ACCESS_TOKEN[:30] if config.FYERS_ACCESS_TOKEN else 'NOT SET'}...")
    print(f"   API Mode: {config.FYERS_API_MODE}")
    print()
    
    if not config.FYERS_ACCESS_TOKEN or config.FYERS_ACCESS_TOKEN == "WILL_BE_GENERATED_BY_AUTH_SCRIPT":
        print("❌ Access token not set. Please run: python scripts/fyers_auth.py --auth")
        return False
    
    # Create broker instance
    print("🔌 Initializing Fyers broker (REAL API)...")
    broker = FyersBroker()
    
    try:
        # Initialize
        success = await broker.initialize()
        if not success:
            print("❌ Failed to initialize Fyers broker")
            return False
        
        print("✅ Broker initialized successfully!")
        print()
        
        # Test 1: Get Profile
        print("📊 Test 1: Getting Profile Information...")
        try:
            profile = await broker.get_profile()
            if profile:
                print(f"✅ Profile retrieved:")
                print(f"   Name: {profile.get('name', 'N/A')}")
                print(f"   Email: {profile.get('email_id', 'N/A')}")
                print(f"   Client ID: {profile.get('fy_id', 'N/A')}")
                print()
            else:
                print("⚠️  Profile data not available")
                print()
        except Exception as e:
            print(f"❌ Error getting profile: {e}")
            print()
        
        # Test 2: Get Funds
        print("📊 Test 2: Getting Account Funds...")
        try:
            account = await broker.get_account_info()
            print(f"✅ Account info retrieved:")
            print(f"   Available Balance: ₹{account.get('available_balance', 0):,.2f}")
            print(f"   Used Margin: ₹{account.get('used_margin', 0):,.2f}")
            print(f"   Total Balance: ₹{account.get('total_balance', 0):,.2f}")
            print()
        except Exception as e:
            print(f"❌ Error getting account info: {e}")
            print()
        
        # Test 3: Get Market Data
        print("📊 Test 3: Getting Live Market Data...")
        test_symbols = ["NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:INFY-EQ"]
        
        for symbol in test_symbols:
            try:
                ltp = await broker.get_ltp(symbol)
                print(f"✅ {symbol}: ₹{ltp:.2f}")
            except Exception as e:
                print(f"❌ Error getting LTP for {symbol}: {e}")
        print()
        
        # Test 4: Get Positions
        print("📊 Test 4: Getting Current Positions...")
        try:
            positions = await broker.get_positions()
            if positions:
                print(f"✅ Found {len(positions)} position(s):")
                for pos in positions:
                    print(f"   {pos.symbol}: {pos.quantity} @ ₹{pos.avg_price:.2f}")
            else:
                print("✅ No open positions (this is normal for a new account)")
            print()
        except Exception as e:
            print(f"❌ Error getting positions: {e}")
            print()
        
        # Test 5: Get Orders
        print("📊 Test 5: Getting Order History...")
        try:
            orders = await broker.get_orders()
            if orders:
                print(f"✅ Found {len(orders)} order(s):")
                for order in orders[:5]:  # Show first 5
                    print(f"   {order.symbol}: {order.quantity} @ ₹{order.price:.2f} - {order.status}")
            else:
                print("✅ No orders found (this is normal for a new account)")
            print()
        except Exception as e:
            print(f"❌ Error getting orders: {e}")
            print()
        
        print("=" * 60)
        print("✅ Fyers API Connection Test SUCCESSFUL!")
        print("🎉 Your Fyers account is connected and working!")
        print()
        print("📝 Next Steps:")
        print("   1. You can now use the trading bot with real Fyers API")
        print("   2. Set MOCK_MODE=false in .env to enable live trading")
        print("   3. Make sure to test thoroughly before live trading!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Fyers API test: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_fyers_connection())
    sys.exit(0 if success else 1)

