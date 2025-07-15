#!/usr/bin/env python3
"""
Trading Bot Startup Script
Demonstrates how to run the trading bot with different modes.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import TradingBot, app
from poller import poller
from config import get_config
from loguru import logger

async def run_demo():
    """Run a quick demo of the trading bot."""
    print("🤖 AI Trading Bot - Demo Mode")
    print("=" * 50)
    
    try:
        # Initialize configuration
        config = get_config()
        print(f"✅ Configuration loaded - Mock Mode: {config.MOCK_MODE}")
        
        # Initialize poller
        print("🔄 Initializing trading system...")
        success = await poller.initialize()
        
        if not success:
            print("❌ Failed to initialize trading system")
            return
        
        print("✅ Trading system initialized successfully")
        
        # Run daily screening
        print("🔍 Running daily market screening...")
        screened_stocks = await poller.daily_market_screening()
        
        if screened_stocks:
            print(f"✅ Found {len(screened_stocks)} stocks to monitor:")
            for stock in screened_stocks:
                print(f"   📈 {stock}")
        else:
            print("⚠️  No stocks passed screening criteria (this is normal)")
        
        # Get system status
        status = await poller.get_status()
        print(f"\n📊 System Status:")
        print(f"   • Monitored Stocks: {status['monitored_stocks']}")
        print(f"   • Active Trades: {status['active_trades']}")
        print(f"   • Market Hours: {status['is_market_hours']}")
        print(f"   • Screening Complete: {status['daily_screening_done']}")
        
        print("\n🎉 Demo completed successfully!")
        print("💡 To start live trading, run: python src/main.py")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")

def run_web_interface():
    """Start the web interface for monitoring."""
    print("🌐 Starting web interface...")
    print("🔗 Access at: http://localhost:8000")
    print("📊 API docs at: http://localhost:8000/docs")
    
    # Import uvicorn and start server
    import uvicorn
    from main import app
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "demo":
            asyncio.run(run_demo())
        elif mode == "web":
            run_web_interface()  # Remove async call
        elif mode == "live":
            # Start full trading bot
            bot = TradingBot()
            asyncio.run(bot.run())
        else:
            print("Usage: python run_bot.py [demo|web|live]")
            print("  demo - Run quick demonstration")
            print("  web  - Start web interface")
            print("  live - Start live trading")
    else:
        # Default to demo
        asyncio.run(run_demo())

if __name__ == "__main__":
    main()
