"""
Development utilities and helper functions for the trading bot.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from config import get_config
from screener import screen_top_stocks
from sentiment import analyze_sentiment
from risk_manager import RiskManager


async def generate_sample_data():
    """Generate sample trading data for testing."""
    print("📊 Generating sample trading data...")
    
    # Sample screening data
    stocks = await screen_top_stocks(5)
    print(f"Generated {len(stocks)} sample stocks")
    
    # Sample sentiment data
    if stocks:
        symbols = [stock['symbol'] for stock in stocks]
        sentiment_results = await analyze_sentiment(symbols[:2])  # Limit to 2 for speed
        print(f"Generated sentiment data for {len(sentiment_results)} stocks")
    
    return stocks, sentiment_results


def create_sample_config():
    """Create a sample configuration file."""
    config_data = {
        "trading": {
            "initial_capital": 100000,
            "max_trades": 2,
            "risk_per_trade": 0.01,
            "confidence_threshold": 0.8
        },
        "market_hours": {
            "open": "09:15",
            "close": "15:30",
            "force_exit": "15:10"
        },
        "api_endpoints": {
            "mock_mode": True,
            "data_source": "yfinance"
        }
    }
    
    config_path = Path("config/sample_config.json")
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"✅ Sample config created at {config_path}")


def create_sample_watchlist():
    """Create a sample watchlist file."""
    watchlist = {
        "name": "NSE Top 50",
        "symbols": [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", 
            "KOTAKBANK", "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC",
            "ASIANPAINT", "MARUTI", "BAJFINANCE", "HCLTECH", "AXISBANK",
            "LT", "DMART", "SUNPHARMA", "TITAN", "ULTRACEMCO"
        ],
        "created": datetime.now().isoformat(),
        "description": "Top 20 NSE stocks by market cap"
    }
    
    watchlist_path = Path("data/sample_watchlist.json")
    watchlist_path.parent.mkdir(exist_ok=True)
    
    with open(watchlist_path, 'w') as f:
        json.dump(watchlist, f, indent=2)
    
    print(f"✅ Sample watchlist created at {watchlist_path}")


async def test_risk_scenarios():
    """Test various risk management scenarios."""
    print("🛡️ Testing risk management scenarios...")
    
    rm = RiskManager()
    
    scenarios = [
        {
            "name": "Conservative Trade",
            "entry": 2500, "stop": 2475, "target": 2550,
            "confidence": 0.85
        },
        {
            "name": "Aggressive Trade", 
            "entry": 1500, "stop": 1450, "target": 1600,
            "confidence": 0.9
        },
        {
            "name": "Poor R:R Trade",
            "entry": 1000, "stop": 950, "target": 1025,
            "confidence": 0.8
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 Testing: {scenario['name']}")
        
        risk_metrics = rm.validate_trade_risk(
            symbol="TEST",
            entry_price=scenario['entry'],
            stop_loss=scenario['stop'],
            target_price=scenario['target'],
            confidence=scenario['confidence']
        )
        
        print(f"   Valid: {risk_metrics.is_within_limits}")
        print(f"   R:R Ratio: {risk_metrics.risk_reward_ratio:.2f}")
        print(f"   Position Size: {risk_metrics.position_size}")
        
        if not risk_metrics.is_within_limits:
            print(f"   Rejection Reason: {risk_metrics.rejection_reason}")


async def create_mock_trading_session():
    """Create a mock trading session for demonstration."""
    print("🎭 Creating mock trading session...")
    
    # Simulate a trading day
    session_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "market_open": "09:15:00",
        "screening_completed": "09:30:00",
        "trades": [
            {
                "time": "10:15:00",
                "symbol": "RELIANCE",
                "action": "BUY",
                "quantity": 40,
                "price": 2500.0,
                "stop_loss": 2450.0,
                "target": 2600.0,
                "reasoning": "Strong bullish breakout with high volume"
            },
            {
                "time": "11:30:00",
                "symbol": "TCS",
                "action": "BUY", 
                "quantity": 25,
                "price": 3800.0,
                "stop_loss": 3750.0,
                "target": 3900.0,
                "reasoning": "Positive earnings sentiment and technical setup"
            },
            {
                "time": "14:45:00",
                "symbol": "RELIANCE",
                "action": "SELL",
                "quantity": 40,
                "price": 2580.0,
                "exit_reason": "TARGET_HIT",
                "pnl": 3200.0
            }
        ],
        "daily_summary": {
            "total_trades": 2,
            "winning_trades": 1,
            "total_pnl": 3200.0,
            "win_rate": 50.0,
            "max_drawdown": 0.0
        }
    }
    
    session_path = Path("data/mock_session.json")
    session_path.parent.mkdir(exist_ok=True)
    
    with open(session_path, 'w') as f:
        json.dump(session_data, f, indent=2, default=str)
    
    print(f"✅ Mock session data created at {session_path}")
    return session_data


def analyze_mock_session(session_data: Dict):
    """Analyze mock trading session performance."""
    print("\n📈 Analyzing mock session performance...")
    
    trades = session_data.get('trades', [])
    summary = session_data.get('daily_summary', {})
    
    print(f"Date: {session_data['date']}")
    print(f"Total Trades: {summary.get('total_trades', 0)}")
    print(f"Winning Trades: {summary.get('winning_trades', 0)}")
    print(f"Win Rate: {summary.get('win_rate', 0):.1f}%")
    print(f"Total P&L: ₹{summary.get('total_pnl', 0):,.2f}")
    
    print("\nTrade Details:")
    for i, trade in enumerate(trades, 1):
        action = trade.get('action', 'UNKNOWN')
        symbol = trade.get('symbol', 'UNKNOWN')
        price = trade.get('price', 0)
        
        if 'pnl' in trade:
            pnl = trade['pnl']
            print(f"  {i}. {action} {symbol} @ ₹{price} → P&L: ₹{pnl:,.2f}")
        else:
            print(f"  {i}. {action} {symbol} @ ₹{price}")


async def main():
    """Main development utility runner."""
    print("🛠️ Trading Bot Development Utilities")
    print("=" * 50)
    
    try:
        # Create sample files
        create_sample_config()
        create_sample_watchlist()
        
        # Generate sample data
        await generate_sample_data()
        
        # Test risk scenarios
        await test_risk_scenarios()
        
        # Create mock session
        session_data = await create_mock_trading_session()
        analyze_mock_session(session_data)
        
        print("\n✅ All development utilities completed successfully!")
        print("\nGenerated files:")
        print("- config/sample_config.json")
        print("- data/sample_watchlist.json")
        print("- data/mock_session.json")
        
    except Exception as e:
        print(f"❌ Error in development utilities: {e}")


if __name__ == "__main__":
    asyncio.run(main())
