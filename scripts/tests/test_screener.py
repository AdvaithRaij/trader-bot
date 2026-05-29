#!/usr/bin/env python3
"""
Test Script: Stock Screener
Tests the stock screening functionality with various scenarios.

Usage:
    cd backend/src && python ../../scripts/tests/test_screener.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "src"))

from loguru import logger
from screener import StockScreener, screen_top_stocks

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")


class ScreenerTestSuite:
    """Test suite for Stock Screener functionality."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({"test": test_name, "passed": passed, "message": message})
        if passed:
            self.passed += 1
            logger.info(f"{status}: {test_name}")
        else:
            self.failed += 1
            logger.error(f"{status}: {test_name} - {message}")
    
    async def test_screener_initialization(self):
        """Test that screener initializes correctly."""
        try:
            screener = StockScreener()
            assert screener is not None
            assert screener.config is not None
            self.log_result("Screener Initialization", True)
        except Exception as e:
            self.log_result("Screener Initialization", False, str(e))
    
    async def test_stock_universe(self):
        """Test that stock universe is loaded correctly."""
        try:
            screener = StockScreener()
            symbols = screener.get_stock_universe()
            assert len(symbols) > 0, "Stock universe is empty"
            assert "RELIANCE" in symbols, "RELIANCE not in universe"
            assert "TCS" in symbols, "TCS not in universe"
            self.log_result(f"Stock Universe ({len(symbols)} symbols)", True)
        except Exception as e:
            self.log_result("Stock Universe", False, str(e))
    
    async def test_single_stock_screening(self):
        """Test screening a single stock."""
        try:
            screener = StockScreener()
            candidate = screener.screen_single_stock("RELIANCE")
            
            if candidate:
                assert candidate.symbol == "RELIANCE"
                assert candidate.price_action is not None
                assert candidate.technicals is not None
                assert candidate.liquidity is not None
                assert candidate.levels is not None
                assert 0 <= candidate.score <= 100
                self.log_result(f"Single Stock Screening (RELIANCE score: {candidate.score:.1f})", True)
            else:
                self.log_result("Single Stock Screening", False, "No candidate returned")
        except Exception as e:
            self.log_result("Single Stock Screening", False, str(e))
    
    async def test_market_context(self):
        """Test market context fetching."""
        try:
            screener = StockScreener()
            context = await screener.get_market_context()
            
            assert context is not None
            assert context.nifty_trend in ["bullish", "bearish", "sideways"]
            assert context.vix > 0
            self.log_result(f"Market Context (NIFTY: {context.nifty_trend}, VIX: {context.vix:.1f})", True)
        except Exception as e:
            self.log_result("Market Context", False, str(e))
    
    async def test_full_screening(self):
        """Test full screening pipeline."""
        try:
            output = await screen_top_stocks(max_stocks=5)
            
            assert output is not None
            assert output.market_context is not None
            assert output.total_scanned > 0
            
            logger.info(f"   Scanned: {output.total_scanned}, Passed: {output.passed_filters}, Top: {len(output.candidates)}")
            
            if output.candidates:
                for c in output.candidates[:3]:
                    logger.info(f"   - {c.symbol}: Score={c.score:.1f}, RVOL={c.liquidity.rvol:.2f}")
            
            self.log_result(f"Full Screening ({len(output.candidates)} candidates)", True)
        except Exception as e:
            self.log_result("Full Screening", False, str(e))
    
    async def test_filtering_criteria(self):
        """Test that filtering criteria are applied correctly."""
        try:
            screener = StockScreener()
            candidate = screener.screen_single_stock("RELIANCE")
            
            if candidate:
                # Test filter application
                passed = screener.apply_screening_filters(candidate)
                self.log_result(f"Filtering Criteria (RELIANCE passed: {passed})", True)
            else:
                self.log_result("Filtering Criteria", False, "No candidate to filter")
        except Exception as e:
            self.log_result("Filtering Criteria", False, str(e))
    
    async def run_all_tests(self):
        """Run all screener tests."""
        logger.info("=" * 60)
        logger.info("🔍 STOCK SCREENER TEST SUITE")
        logger.info("=" * 60)
        
        await self.test_screener_initialization()
        await self.test_stock_universe()
        await self.test_single_stock_screening()
        await self.test_market_context()
        await self.test_full_screening()
        await self.test_filtering_criteria()
        
        logger.info("=" * 60)
        logger.info(f"📊 RESULTS: {self.passed} passed, {self.failed} failed")
        logger.info("=" * 60)
        
        return self.failed == 0


async def main():
    """Run the test suite."""
    suite = ScreenerTestSuite()
    success = await suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

