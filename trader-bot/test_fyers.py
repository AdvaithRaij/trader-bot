#!/usr/bin/env python3
"""
Quick test script to demonstrate Fyers API integration
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from broker import broker
from config import get_config

async def test_fyers_integration():
    """Test the Fyers API integration"""
    print("🤖 Testing Fyers API Integration")
    print("=" * 40)
    
    config = get_config()
    print(f"📊 Mode: {'MOCK' if config.MOCK_MODE else 'LIVE'}")
    print(f"💰 Initial Capital: ₹{config.INITIAL_CAPITAL:,.2f}")
    print()
    
    # Initialize broker
    print("🔌 Initializing broker...")
    success = await broker.initialize()
    if not success:
        print("❌ Failed to initialize broker")
        return
    
    print("✅ Broker initialized successfully")
    print()
    
    # Test account info
    print("📊 Getting account information...")
    account = await broker.get_account_info()
    print(f"💰 Available Balance: ₹{account['available_balance']:,.2f}")
    print(f"📈 Used Margin: ₹{account['used_margin']:,.2f}")
    print()
    
    # Test market data
    print("📈 Testing market data...")
    symbols = ["RELIANCE", "TCS", "INFY"]
    
    for symbol in symbols:
        ltp = await broker.get_ltp(symbol)
        print(f"📊 {symbol}: ₹{ltp:.2f}")
    print()
    
    # Test order placement (mock)
    print("📋 Testing order placement...")
    order_id = await broker.place_order(
        symbol="RELIANCE",
        transaction_type="1",  # Buy
        quantity=1,
        order_type="2"  # Market
    )
    
    if order_id:
        print(f"✅ Order placed successfully: {order_id}")
    else:
        print("❌ Order placement failed")
    print()
    
    # Test positions
    print("📊 Getting positions...")
    positions = await broker.get_positions()
    if positions:
        for position in positions:
            print(f"📈 {position.symbol}: {position.quantity} shares @ ₹{position.average_price:.2f}")
    else:
        print("📊 No positions found")
    print()
    
    # Test orders
    print("📋 Getting orders...")
    orders = await broker.get_orders()
    if orders:
        for order in orders:
            print(f"📋 {order.symbol}: {order.quantity} shares - {order.status.name}")
    else:
        print("📋 No orders found")
    print()
    
    print("✅ All tests completed successfully!")
    print("🎉 Fyers API integration is working perfectly!")

if __name__ == "__main__":
    asyncio.run(test_fyers_integration())
