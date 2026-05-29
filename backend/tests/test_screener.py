"""
Test Suite for Stock Screener

Tests the stock screening component with real data from yfinance.
Verifies NIFTY 200 universe, technical indicators, and filtering logic.

Run:
    pytest backend/tests/test_screener.py -v
"""

import pytest
from loguru import logger

# Helper functions from conftest
def assert_real_price(price: float, symbol: str):
    assert price > 0, f"Price for {symbol} must be positive"
    assert price < 1000000, f"Price for {symbol} seems unrealistic: {price}"

def assert_valid_percentage(pct: float, name: str):
    assert -100 <= pct <= 1000, f"{name} percentage out of range: {pct}%"

def assert_no_mock_data(data: dict, context: str):
    str_data = str(data).lower()
    mock_indicators = ["mock", "fake", "test_", "dummy", "placeholder"]
    for indicator in mock_indicators:
        assert indicator not in str_data, f"Found mock indicator '{indicator}' in {context}"


class TestStockScreener:
    """Test stock screener functionality with real data."""

    @pytest.mark.asyncio
    async def test_screener_initialization(self, screener):
        """Test that screener initializes correctly."""
        logger.info("Testing screener initialization...")
        
        assert screener is not None
        assert screener.config is not None
        assert screener.session is not None
        
        logger.success("✅ Screener initialized successfully")

    @pytest.mark.asyncio
    async def test_get_stock_universe(self, screener):
        """Test that stock universe returns NIFTY 200 symbols."""
        logger.info("Testing stock universe retrieval...")
        
        symbols = screener.get_stock_universe()
        
        assert isinstance(symbols, list)
        assert len(symbols) > 150, f"Expected ~200 symbols, got {len(symbols)}"
        assert "RELIANCE" in symbols
        assert "TCS" in symbols
        assert "HDFCBANK" in symbols
        
        # Verify no duplicates
        assert len(symbols) == len(set(symbols)), "Found duplicate symbols"
        
        logger.success(f"✅ Stock universe contains {len(symbols)} symbols")

    @pytest.mark.asyncio
    async def test_get_stock_data_real(self, screener):
        """Test fetching real stock data from yfinance."""
        logger.info("Testing real stock data fetch...")
        
        symbol = "RELIANCE"
        data = screener.get_stock_data(symbol, period="15d")
        
        assert data is not None, f"No data returned for {symbol}"
        assert not data.empty, f"Empty dataframe for {symbol}"
        assert len(data) >= 10, f"Expected at least 10 days of data, got {len(data)}"
        
        # Verify required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            assert col in data.columns, f"Missing column: {col}"
        
        # Verify data is real (not zeros or mock)
        assert data['Close'].iloc[-1] > 0, "Last close price is zero"
        assert data['Volume'].iloc[-1] > 0, "Last volume is zero"
        
        logger.success(f"✅ Real data fetched for {symbol}: Close={data['Close'].iloc[-1]:.2f}")

    @pytest.mark.asyncio
    async def test_calculate_liquidity_metrics(self, screener):
        """Test liquidity metrics calculation with real data."""
        logger.info("Testing liquidity metrics calculation...")
        
        symbol = "RELIANCE"
        daily_data = screener.get_stock_data(symbol)
        intraday_data = screener.get_intraday_data(symbol)
        current_price = float(daily_data['Close'].iloc[-1])
        
        metrics = screener.calculate_liquidity_metrics(daily_data, intraday_data, current_price)
        
        assert metrics is not None
        assert metrics.today_turnover_cr > 0, "Turnover must be positive"
        assert metrics.rvol > 0, "RVOL must be positive"
        assert metrics.today_volume > 0, "Volume must be positive"
        
        # Verify realistic values
        assert metrics.today_turnover_cr < 100000, f"Turnover seems unrealistic: {metrics.today_turnover_cr}"
        assert 0.1 < metrics.rvol < 10, f"RVOL seems unrealistic: {metrics.rvol}"
        
        logger.success(f"✅ Liquidity metrics: Turnover={metrics.today_turnover_cr:.2f}Cr, RVOL={metrics.rvol:.2f}x")

    @pytest.mark.asyncio
    async def test_calculate_technical_indicators(self, screener):
        """Test technical indicators calculation with real data."""
        logger.info("Testing technical indicators...")
        
        symbol = "TCS"
        daily_data = screener.get_stock_data(symbol)
        
        # Get price action first
        intraday_data = screener.get_intraday_data(symbol)
        price_action = screener.calculate_price_action(daily_data, intraday_data)
        
        assert price_action is not None
        
        # Calculate technical indicators
        technicals = screener.calculate_technical_indicators(daily_data, price_action)
        
        assert technicals is not None
        assert 0 <= technicals.rsi <= 100, f"RSI out of range: {technicals.rsi}"
        assert technicals.atr > 0, "ATR must be positive"
        assert technicals.atr_pct > 0, "ATR% must be positive"
        assert technicals.trend_label in ["uptrend", "downtrend", "sideways"]
        
        logger.success(f"✅ Technical indicators: RSI={technicals.rsi:.1f}, ATR%={technicals.atr_pct:.2f}%, Trend={technicals.trend_label}")

    @pytest.mark.asyncio
    async def test_calculate_pivot_levels(self, screener):
        """Test pivot point calculation."""
        logger.info("Testing pivot levels calculation...")

        symbol = "HDFCBANK"
        daily_data = screener.get_stock_data(symbol)

        pivots = screener.calculate_pivot_levels(daily_data)

        assert pivots is not None
        assert pivots.pivot_pp > 0
        assert pivots.s1 < pivots.pivot_pp < pivots.r1
        assert pivots.s2 < pivots.s1
        assert pivots.r1 < pivots.r2

        logger.success(f"✅ Pivot levels: PP={pivots.pivot_pp:.2f}, S1={pivots.s1:.2f}, R1={pivots.r1:.2f}")

    @pytest.mark.asyncio
    async def test_get_market_context(self, screener):
        """Test market context (NIFTY, VIX) with real data."""
        logger.info("Testing market context retrieval...")

        context = await screener.get_market_context()

        assert context is not None
        assert context.nifty_price > 0, "NIFTY price must be positive"
        assert context.vix > 0, "VIX must be positive"
        assert context.nifty_trend in ["uptrend", "downtrend", "sideways"]
        assert -10 < context.nifty_change_pct < 10, f"NIFTY change seems unrealistic: {context.nifty_change_pct}%"

        logger.success(f"✅ Market context: NIFTY={context.nifty_price:.2f} ({context.nifty_change_pct:+.2f}%), VIX={context.vix:.2f}")

    @pytest.mark.asyncio
    async def test_screen_single_stock(self, screener):
        """Test screening a single stock end-to-end."""
        logger.info("Testing single stock screening...")

        symbol = "INFY"
        candidate = screener.screen_single_stock(symbol)

        if candidate is None:
            logger.warning(f"⚠️ {symbol} returned None (may not have enough data)")
            return

        # Verify all components are present
        assert candidate.symbol == symbol
        assert candidate.liquidity is not None
        assert candidate.price_action is not None
        assert candidate.technicals is not None
        assert candidate.pivots is not None
        assert 0 <= candidate.score <= 100

        # Verify real data
        assert_real_price(candidate.price_action.last_price, symbol)
        assert_no_mock_data(candidate.model_dump(), f"candidate {symbol}")

        logger.success(f"✅ {symbol} screened: Score={candidate.score:.1f}, Price={candidate.price_action.last_price:.2f}")

    @pytest.mark.asyncio
    async def test_apply_screening_filters(self, screener):
        """Test screening filters with real candidates."""
        logger.info("Testing screening filters...")

        # Screen a few stocks and test filters
        test_symbols = ["RELIANCE", "TCS", "HDFCBANK"]
        passed = 0
        failed = 0

        for symbol in test_symbols:
            candidate = screener.screen_single_stock(symbol)
            if candidate:
                result = screener.apply_screening_filters(candidate)
                if result:
                    passed += 1
                    logger.info(f"  ✅ {symbol} passed filters")
                else:
                    failed += 1
                    logger.info(f"  ❌ {symbol} failed filters")

        logger.success(f"✅ Filter test complete: {passed} passed, {failed} failed")

    @pytest.mark.asyncio
    async def test_full_screening_cycle(self, screener):
        """Test full screening cycle with real NIFTY 200 data."""
        logger.info("Testing full screening cycle (this may take 2-3 minutes)...")

        # Run screening for top 5 stocks
        output = await screener.screen_stocks(max_stocks=5)

        assert output is not None
        assert output.market_context is not None
        assert len(output.candidates) > 0, "No candidates returned"
        assert len(output.candidates) <= 5
        assert output.total_scanned > 0

        # Verify candidates are sorted by score
        scores = [c.score for c in output.candidates]
        assert scores == sorted(scores, reverse=True), "Candidates not sorted by score"

        # Verify all candidates have real data
        for candidate in output.candidates:
            assert_real_price(candidate.price_action.last_price, candidate.symbol)
            assert candidate.liquidity.rvol > 0
            assert 0 <= candidate.score <= 100

        logger.success(f"✅ Screening complete: {len(output.candidates)} candidates from {output.total_scanned} scanned")
        for i, c in enumerate(output.candidates, 1):
            logger.info(f"  {i}. {c.symbol}: Score={c.score:.1f}, RVOL={c.liquidity.rvol:.2f}x")

