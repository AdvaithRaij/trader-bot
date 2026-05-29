"""
Quick start script for testing the trading bot.
Run this to verify everything is working correctly.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from config import get_config, validate_config
from screener import screen_top_stocks
from sentiment import analyze_sentiment
from ai_decision_engine import make_trading_decision
from broker import initialize_broker, broker
from risk_manager import RiskManager
from telegram_notifier import TelegramNotifier
from trade_logger import initialize_trade_logger

config = get_config()


async def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")
    try:
        config = get_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   - Initial Capital: ₹{config.INITIAL_CAPITAL:,.2f}")
        print(f"   - Mock Mode: {config.MOCK_MODE}")
        print(f"   - Max Active Trades: {config.MAX_ACTIVE_TRADES}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


async def test_screener():
    """Test stock screening functionality."""
    print("\n📊 Testing stock screener...")
    try:
        stocks = await screen_top_stocks(3)
        print(f"✅ Screener working - found {len(stocks)} stocks")
        for i, stock in enumerate(stocks, 1):
            print(f"   {i}. {stock['symbol']} (Score: {stock.get('screening_score', 0):.2f})")
        return stocks
    except Exception as e:
        print(f"❌ Screener error: {e}")
        return []


async def test_sentiment_analysis():
    """Test sentiment analysis."""
    print("\n💭 Testing sentiment analysis...")
    try:
        test_symbols = ["RELIANCE", "TCS"]
        results = await analyze_sentiment(test_symbols)
        print(f"✅ Sentiment analysis working for {len(results)} stocks")
        for symbol, data in results.items():
            if 'error' not in data:
                sentiment = data.get('final_sentiment', 0)
                confidence = data.get('confidence', 0)
                print(f"   {symbol}: Sentiment={sentiment:.2f}, Confidence={confidence:.2f}")
        return results
    except Exception as e:
        print(f"❌ Sentiment analysis error: {e}")
        return {}


async def test_ai_decision_engine():
    """Test AI decision engine."""
    print("\n🤖 Testing AI decision engine...")
    try:
        # Mock data
        stock_data = {
            'symbol': 'RELIANCE',
            'current_price': 2500.0,
            'vwap': 2480.0,
            'rsi': 35.0,
            'volume_ratio': 2.1,
            'above_vwap': True
        }
        
        sentiment_data = {
            'final_sentiment': 0.6,
            'intraday_relevance': 0.7,
            'confidence': 0.8,
            'trade_signal': 'BULLISH'
        }
        
        decision = await make_trading_decision(stock_data, sentiment_data)
        print(f"✅ AI decision engine working")
        print(f"   Decision: {decision.get('final_action', 'UNKNOWN')}")
        print(f"   Should Trade: {decision.get('should_trade', False)}")
        
        if 'ai_decision' in decision:
            ai_dec = decision['ai_decision']
            print(f"   Confidence: {ai_dec.get('confidence', 0):.2f}")
            print(f"   R:R Ratio: {ai_dec.get('risk_reward_ratio', 0):.2f}")
        
        return True
    except Exception as e:
        print(f"❌ AI decision engine error: {e}")
        return False


async def test_broker_interface():
    """Test broker interface."""
    print("\n🏦 Testing broker interface...")
    try:
        success = await initialize_broker()
        if success:
            print("✅ Broker interface initialized")
            
            # Test price fetching
            price = await broker.get_current_price("RELIANCE")
            if price:
                print(f"   RELIANCE price: ₹{price:.2f}")
            
            # Test account info
            account = await broker.get_account_info()
            print(f"   Account balance: ₹{account.get('account_balance', 0):,.2f}")
            
            return True
        else:
            print("❌ Broker initialization failed")
            return False
    except Exception as e:
        print(f"❌ Broker interface error: {e}")
        return False


async def test_risk_manager():
    """Test risk management."""
    print("\n🛡️ Testing risk manager...")
    try:
        rm = RiskManager()
        
        # Test position sizing
        quantity, risk = rm.calculate_position_size(2500.0, 2450.0)
        print(f"✅ Risk manager working")
        print(f"   Position size: {quantity} shares")
        print(f"   Risk amount: ₹{risk:.2f}")
        
        # Test risk validation
        risk_metrics = rm.validate_trade_risk(
            "RELIANCE", 2500.0, 2450.0, 2600.0, 0.8
        )
        print(f"   Risk validation: {risk_metrics.is_within_limits}")
        
        return True
    except Exception as e:
        print(f"❌ Risk manager error: {e}")
        return False


async def test_trade_logger():
    """Test trade logging."""
    print("\n📝 Testing trade logger...")
    try:
        success = await initialize_trade_logger()
        print(f"✅ Trade logger initialized: {success}")
        return True
    except Exception as e:
        print(f"❌ Trade logger error: {e}")
        return False


async def test_telegram():
    """Test Telegram notifications."""
    print("\n📱 Testing Telegram...")
    try:
        notifier = TelegramNotifier()
        if notifier.is_configured():
            async with notifier:
                success = await notifier.test_connection()
                if success:
                    print("✅ Telegram working")
                else:
                    print("⚠️ Telegram configured but test failed")
        else:
            print("⚠️ Telegram not configured (optional)")
        return True
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🤖 AI Trading Bot - Quick Start Test")
    print("=" * 50)
    
    start_time = datetime.now()
    
    # Run all tests
    tests = [
        ("Configuration", test_configuration()),
        ("Stock Screener", test_screener()),
        ("Sentiment Analysis", test_sentiment_analysis()),
        ("AI Decision Engine", test_ai_decision_engine()),
        ("Broker Interface", test_broker_interface()),
        ("Risk Manager", test_risk_manager()),
        ("Trade Logger", test_trade_logger()),
        ("Telegram", test_telegram())
    ]
    
    results = []
    for test_name, test_coro in tests:
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Duration: {duration.total_seconds():.2f} seconds")
    
    if passed == total:
        print("\n🎉 All tests passed! The trading bot is ready to use.")
        print("\nNext steps:")
        print("1. Configure your API keys in .env file")
        print("2. Set MOCK_MODE=false for live trading")
        print("3. Run: python src/main.py --mode both")
        print("4. Access web dashboard at http://localhost:8000")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the errors above.")
        print("Make sure all dependencies are installed and configured correctly.")
    
    return passed == total


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
