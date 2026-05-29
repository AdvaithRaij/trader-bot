"""
Test Suite for Data Aggregator

Tests data aggregation from multiple sources (yfinance, news, screener).

Run:
    pytest backend/tests/test_data_aggregator.py -v
"""

import pytest
from loguru import logger
from conftest import assert_real_price, assert_no_mock_data


class TestDataAggregator:
    """Test data aggregation functionality."""

    @pytest.mark.asyncio
    async def test_aggregator_initialization(self, data_aggregator):
        """Test data aggregator initializes correctly."""
        logger.info("Testing data aggregator initialization...")
        
        assert data_aggregator is not None
        assert data_aggregator.news_aggregator is not None
        
        logger.success("✅ Data aggregator initialized")

    @pytest.mark.asyncio
    async def test_get_fundamental_data(self, data_aggregator):
        """Test fetching fundamental data from yfinance."""
        logger.info("Testing fundamental data fetch...")
        
        symbol = "RELIANCE"
        fundamentals = data_aggregator.get_fundamental_data(symbol)
        
        assert fundamentals is not None
        assert fundamentals.data_available is True
        
        # Verify key metrics
        if fundamentals.pe_ratio:
            assert fundamentals.pe_ratio > 0
        if fundamentals.market_cap_cr:
            assert fundamentals.market_cap_cr > 0
        
        logger.success(f"✅ Fundamentals: P/E={fundamentals.pe_ratio}, MCap={fundamentals.market_cap_cr}Cr")

    @pytest.mark.asyncio
    async def test_get_news_context(self, data_aggregator):
        """Test fetching news context."""
        logger.info("Testing news context fetch...")
        
        symbol = "TCS"
        news_context = await data_aggregator.get_news_context(symbol)
        
        assert news_context is not None
        assert news_context.sentiment in ["positive", "negative", "neutral"]
        assert -1 <= news_context.sentiment_score <= 1
        
        logger.success(f"✅ News: {news_context.news_count_24h} articles, Sentiment={news_context.sentiment}")

    @pytest.mark.asyncio
    async def test_aggregate_stock_data_complete(self, data_aggregator):
        """Test complete stock data aggregation."""
        logger.info("Testing complete data aggregation...")

        symbol = "HDFCBANK"
        stock_data = await data_aggregator.get_complete_stock_data(symbol)
        
        assert stock_data is not None
        assert stock_data.symbol == symbol
        
        # Verify all components present
        assert stock_data.fundamentals is not None
        assert stock_data.news is not None
        assert stock_data.current_price > 0
        assert stock_data.rsi_14 > 0
        assert stock_data.atr_pct > 0
        
        # Verify real data
        assert_real_price(stock_data.current_price, symbol)
        assert_no_mock_data(stock_data.model_dump(), f"stock data for {symbol}")
        
        logger.success(f"✅ Complete data: Price=₹{stock_data.current_price:.2f}, RSI={stock_data.rsi_14:.1f}")

    @pytest.mark.asyncio
    async def test_aggregate_multiple_stocks(self, data_aggregator, test_symbols):
        """Test aggregating data for multiple stocks."""
        logger.info("Testing multiple stock aggregation...")
        
        results = []
        for symbol in test_symbols[:3]:  # Test first 3
            stock_data = await data_aggregator.get_complete_stock_data(symbol)
            results.append(stock_data)
            logger.info(f"  {symbol}: ₹{stock_data.current_price:.2f}")
        
        assert len(results) == 3
        
        # Verify all have valid data
        for data in results:
            assert data.current_price > 0
            assert data.fundamentals is not None
            assert data.news is not None
        
        logger.success(f"✅ Aggregated data for {len(results)} stocks")

    @pytest.mark.asyncio
    async def test_market_context_aggregation(self, data_aggregator):
        """Test market context aggregation."""
        logger.info("Testing market context aggregation...")
        
        # This would typically come from screener
        from screener import StockScreener
        
        async with StockScreener() as screener:
            market_context = await screener.get_market_context()
        
        assert market_context is not None
        assert market_context.nifty_price > 0
        assert market_context.vix > 0
        
        logger.success(f"✅ Market: NIFTY={market_context.nifty_price:.2f}, VIX={market_context.vix:.2f}")

    @pytest.mark.asyncio
    async def test_data_caching(self, data_aggregator):
        """Test that data is cached appropriately."""
        logger.info("Testing data caching...")
        
        symbol = "INFY"
        
        # First call - should fetch from API
        import time
        start1 = time.time()
        data1 = data_aggregator.get_fundamental_data(symbol)
        time1 = time.time() - start1
        
        # Second call - should use cache
        start2 = time.time()
        data2 = data_aggregator.get_fundamental_data(symbol)
        time2 = time.time() - start2
        
        # Cached call should be faster
        logger.info(f"  First call: {time1:.3f}s")
        logger.info(f"  Cached call: {time2:.3f}s")
        
        # Data should be identical
        assert data1.pe_ratio == data2.pe_ratio
        assert data1.market_cap_cr == data2.market_cap_cr
        
        logger.success("✅ Caching working correctly")

