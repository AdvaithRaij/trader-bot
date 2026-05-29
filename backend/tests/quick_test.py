#!/usr/bin/env python3
"""
Quick Test Script - Run without pytest

This script performs a quick validation of the critical path:
Screening → Data Aggregation → Multi-Strategy Analysis

Usage:
    python quick_test.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger


async def quick_test():
    """Run quick validation test."""
    
    logger.info("=" * 80)
    logger.info("QUICK VALIDATION TEST - Critical Path")
    logger.info("=" * 80)
    
    try:
        # Test 1: Screener
        logger.info("\n📊 Test 1: Stock Screener")
        from screener import StockScreener
        
        async with StockScreener() as screener:
            output = await screener.screen_stocks(max_stocks=2)
            
            if not output or len(output.candidates) == 0:
                logger.error("❌ Screening failed - no candidates")
                return False
            
            logger.success(f"✅ Screener: {len(output.candidates)} candidates")
            symbol = output.candidates[0].symbol
            logger.info(f"   Top pick: {symbol} (Score: {output.candidates[0].score:.1f})")
        
        # Test 2: Data Aggregator
        logger.info(f"\n📈 Test 2: Data Aggregation for {symbol}")
        from data_aggregator import DataAggregator
        from news_aggregator import NewsAggregator
        
        news_agg = NewsAggregator()
        data_agg = DataAggregator(news_aggregator=news_agg)
        
        stock_data = await data_agg.get_complete_stock_data(symbol)
        
        if not stock_data:
            logger.error("❌ Data aggregation failed")
            return False
        
        logger.success(f"✅ Data Aggregator: Price=₹{stock_data.current_price:.2f}")
        logger.info(f"   Fundamentals: P/E={stock_data.fundamentals.pe_ratio}")
        logger.info(f"   News: {stock_data.news.news_count_24h} articles")
        
        # Test 3: Multi-Strategy Analyzer
        logger.info(f"\n🧠 Test 3: Multi-Strategy Analysis for {symbol}")
        from multi_strategy_analyzer import MultiStrategyAnalyzer
        
        analyzer = MultiStrategyAnalyzer()
        result = await analyzer.analyze_stock(stock_data)
        
        if not result:
            logger.error("❌ Multi-strategy analysis failed")
            return False
        
        logger.success(f"✅ Multi-Strategy Analyzer:")
        logger.info(f"   Fundamental: {result.fundamental.direction} @ ₹{result.fundamental.entry:.2f}")
        logger.info(f"   News-based: {result.news_based.direction} @ ₹{result.news_based.entry:.2f}")
        logger.info(f"   Combined: {result.combined.direction} @ ₹{result.combined.entry:.2f}")
        logger.info(f"   📋 RECOMMENDATION: Use {result.recommendation.best_strategy} strategy")
        logger.info(f"      Confidence: {result.recommendation.confidence}%")
        logger.info(f"      Sentiment: {result.recommendation.overall_sentiment}")
        
        # Test 4: Risk Manager
        logger.info(f"\n🛡️ Test 4: Risk Management")
        from risk_manager import RiskManager

        risk_mgr = RiskManager()

        # Get the best strategy's analysis
        best_strategy_analysis = getattr(result, result.recommendation.best_strategy)

        if best_strategy_analysis.direction != "HOLD":
            metrics = risk_mgr.validate_trade_risk(
                symbol=symbol,
                entry_price=best_strategy_analysis.entry,
                stop_loss=best_strategy_analysis.stop_loss,
                target_price=best_strategy_analysis.target_1,
                confidence=best_strategy_analysis.confidence
            )

            logger.success(f"✅ Risk Manager:")
            logger.info(f"   Position size: {metrics.position_size} shares")
            logger.info(f"   Risk: {metrics.risk_pct:.2f}%")
            logger.info(f"   R:R: 1:{metrics.risk_reward_ratio:.2f}")
            logger.info(f"   Valid: {metrics.is_within_limits}")
        else:
            logger.info("   Skipped (HOLD recommendation)")
        
        # Test 5: Data Source Verification
        logger.info(f"\n🔍 Test 5: Data Source Verification")
        import yfinance as yf
        
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="1d")
        
        if hist.empty:
            logger.error("❌ yfinance data fetch failed")
            return False
        
        yf_price = hist['Close'].iloc[-1]
        logger.success(f"✅ yfinance: {symbol} @ ₹{yf_price:.2f}")
        
        # Verify prices match (within 1%)
        diff_pct = abs(stock_data.current_price - yf_price) / yf_price * 100
        if diff_pct < 1:
            logger.success(f"✅ Price verification: {diff_pct:.2f}% difference (OK)")
        else:
            logger.warning(f"⚠️ Price difference: {diff_pct:.2f}%")
        
        logger.info("\n" + "=" * 80)
        logger.success("✅ ALL TESTS PASSED - System is working with real data!")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Run test
    success = asyncio.run(quick_test())
    
    sys.exit(0 if success else 1)

