"""
Test Suite for End-to-End Pipeline

Tests the complete trading pipeline from screening to paper trade execution.
This is the most critical test - verifies the entire workflow with real data.

Run:
    pytest backend/tests/test_end_to_end.py -v
"""

import pytest
from loguru import logger
from conftest import assert_real_price, assert_no_mock_data


class TestEndToEndPipeline:
    """Test complete pipeline: screening → analysis → signal → paper trade."""

    @pytest.mark.asyncio
    async def test_full_pipeline_screening_to_analysis(self):
        """Test: Screen stocks → Aggregate data → Multi-strategy analysis."""
        logger.info("=" * 80)
        logger.info("STARTING END-TO-END PIPELINE TEST")
        logger.info("=" * 80)
        
        # STAGE 1: SCREENING
        logger.info("\n📊 STAGE 1: Stock Screening")
        from screener import StockScreener
        
        async with StockScreener() as screener:
            output = await screener.screen_stocks(max_stocks=3)
            
            assert output is not None
            assert len(output.candidates) > 0
            
            logger.success(f"✅ Screened {output.total_scanned} stocks, found {len(output.candidates)} candidates")
            
            for i, candidate in enumerate(output.candidates, 1):
                logger.info(f"  {i}. {candidate.symbol}: Score={candidate.score:.1f}, RVOL={candidate.liquidity.rvol:.2f}x")
            
            # Take top candidate for further analysis
            top_candidate = output.candidates[0]
            symbol = top_candidate.symbol
            
            logger.info(f"\n🎯 Selected {symbol} for detailed analysis")
        
        # STAGE 2: DATA AGGREGATION
        logger.info(f"\n📈 STAGE 2: Data Aggregation for {symbol}")
        from data_aggregator import DataAggregator
        from news_aggregator import NewsAggregator
        
        news_agg = NewsAggregator()
        data_agg = DataAggregator(news_aggregator=news_agg)
        
        stock_data = await data_agg.get_complete_stock_data(symbol)
        
        assert stock_data is not None
        assert stock_data.symbol == symbol
        assert_real_price(stock_data.current_price, symbol)
        
        logger.success(f"✅ Data aggregated:")
        logger.info(f"  Price: ₹{stock_data.current_price:.2f}")
        logger.info(f"  P/E: {stock_data.fundamentals.pe_ratio}")
        logger.info(f"  News: {stock_data.news.news_count_24h} articles, Sentiment: {stock_data.news.sentiment}")
        logger.info(f"  RSI: {stock_data.rsi_14:.1f}")
        
        # STAGE 3: MULTI-STRATEGY ANALYSIS
        logger.info(f"\n🧠 STAGE 3: Multi-Strategy Analysis for {symbol}")
        from multi_strategy_analyzer import MultiStrategyAnalyzer
        
        analyzer = MultiStrategyAnalyzer()
        result = await analyzer.analyze_stock(stock_data)
        
        assert result is not None
        assert result.fundamental is not None
        assert result.news_based is not None
        assert result.combined is not None
        assert result.recommendation is not None
        
        logger.success(f"✅ Multi-strategy analysis complete:")
        logger.info(f"  Fundamental: {result.fundamental.direction} @ ₹{result.fundamental.entry:.2f} (Confidence: {result.fundamental.confidence}%)")
        logger.info(f"  News-based: {result.news_based.direction} @ ₹{result.news_based.entry:.2f} (Confidence: {result.news_based.confidence}%)")
        logger.info(f"  Combined: {result.combined.direction} @ ₹{result.combined.entry:.2f} (Confidence: {result.combined.confidence}%)")
        logger.info(f"  📋 RECOMMENDATION: {result.recommendation.action} via {result.recommendation.primary_strategy}")
        logger.info(f"     Entry: ₹{result.recommendation.entry_price:.2f}")
        logger.info(f"     Stop-Loss: ₹{result.recommendation.stop_loss:.2f}")
        logger.info(f"     Target: ₹{result.recommendation.target_price:.2f}")
        logger.info(f"     Confidence: {result.recommendation.confidence}%")
        
        # Verify no mock data in entire pipeline
        assert_no_mock_data(output.model_dump(), "screening output")
        assert_no_mock_data(stock_data.model_dump(), "stock data")
        assert_no_mock_data(result.model_dump(), "analysis result")
        
        logger.info("\n" + "=" * 80)
        logger.success("✅ END-TO-END PIPELINE TEST PASSED")
        logger.info("=" * 80)
        
        return result

    @pytest.mark.asyncio
    async def test_pipeline_with_paper_trade_validation(self, risk_manager):
        """Test: Analysis → Risk validation → Paper trade signal."""
        logger.info("\n💰 STAGE 4: Risk Management & Paper Trade Validation")

        # Use result from previous test or create new one
        from screener import StockScreener
        from data_aggregator import DataAggregator
        from news_aggregator import NewsAggregator
        from multi_strategy_analyzer import MultiStrategyAnalyzer

        # Quick screening
        async with StockScreener() as screener:
            output = await screener.screen_stocks(max_stocks=1)
            symbol = output.candidates[0].symbol

        # Get data and analyze
        news_agg = NewsAggregator()
        data_agg = DataAggregator(news_aggregator=news_agg)
        stock_data = await data_agg.get_complete_stock_data(symbol)

        analyzer = MultiStrategyAnalyzer()
        result = await analyzer.analyze_stock(stock_data)

        rec = result.recommendation

        if rec.action == "HOLD":
            logger.info(f"  Recommendation is HOLD, skipping trade validation")
            return

        # RISK VALIDATION
        logger.info(f"\n🛡️ Validating trade risk for {symbol}...")

        risk_metrics = risk_manager.validate_trade_risk(
            symbol=symbol,
            entry_price=rec.entry_price,
            stop_loss=rec.stop_loss,
            target_price=rec.target_price,
            confidence=rec.confidence
        )

        assert risk_metrics is not None
        logger.info(f"  Risk per trade: {risk_metrics.risk_pct:.2f}%")
        logger.info(f"  Position size: {risk_metrics.position_size} shares")
        logger.info(f"  Risk-Reward: 1:{risk_metrics.risk_reward_ratio:.2f}")
        logger.info(f"  Within limits: {risk_metrics.is_within_limits}")

        if not risk_metrics.is_within_limits:
            logger.warning(f"  ⚠️ Trade rejected: {risk_metrics.rejection_reason}")
        else:
            logger.success(f"  ✅ Trade validated and ready for execution")

        # PAPER TRADE SIGNAL
        if risk_metrics.is_within_limits:
            logger.info(f"\n📝 Paper Trade Signal Generated:")
            logger.info(f"  Symbol: {symbol}")
            logger.info(f"  Action: {rec.action}")
            logger.info(f"  Entry: ₹{rec.entry_price:.2f}")
            logger.info(f"  Stop-Loss: ₹{rec.stop_loss:.2f}")
            logger.info(f"  Target: ₹{rec.target_price:.2f}")
            logger.info(f"  Quantity: {risk_metrics.position_size} shares")
            logger.info(f"  Strategy: {rec.primary_strategy}")
            logger.info(f"  Confidence: {rec.confidence}%")

            logger.success("✅ Paper trade signal ready for execution")

    @pytest.mark.asyncio
    async def test_multiple_stocks_pipeline(self):
        """Test pipeline with multiple stocks (batch processing)."""
        logger.info("\n🔄 Testing batch processing of multiple stocks...")

        from screener import StockScreener
        from data_aggregator import DataAggregator
        from news_aggregator import NewsAggregator
        from multi_strategy_analyzer import MultiStrategyAnalyzer

        # Screen top 3 stocks
        async with StockScreener() as screener:
            output = await screener.screen_stocks(max_stocks=3)

        symbols = [c.symbol for c in output.candidates]
        logger.info(f"  Processing {len(symbols)} stocks: {', '.join(symbols)}")

        # Analyze each
        news_agg = NewsAggregator()
        data_agg = DataAggregator(news_aggregator=news_agg)
        analyzer = MultiStrategyAnalyzer()

        results = []
        for symbol in symbols:
            stock_data = await data_agg.aggregate_stock_data(symbol)
            result = await analyzer.analyze_stock(stock_data)
            results.append(result)

            logger.info(f"  {symbol}: {result.recommendation.action} (Confidence: {result.recommendation.confidence}%)")

        assert len(results) == len(symbols)

        # Count actionable signals
        buy_signals = sum(1 for r in results if r.recommendation.action == "BUY")
        sell_signals = sum(1 for r in results if r.recommendation.action == "SELL")
        hold_signals = sum(1 for r in results if r.recommendation.action == "HOLD")

        logger.success(f"✅ Batch processing complete: {buy_signals} BUY, {sell_signals} SELL, {hold_signals} HOLD")

    @pytest.mark.asyncio
    async def test_data_source_verification(self):
        """Verify all data comes from real sources (no mocks)."""
        logger.info("\n🔍 Verifying data sources...")

        from screener import StockScreener
        import yfinance as yf

        symbol = "RELIANCE"

        # Test yfinance directly
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        hist = ticker.history(period="1d")

        assert info is not None
        assert not hist.empty
        assert 'regularMarketPrice' in info or 'currentPrice' in info

        logger.success(f"✅ yfinance working: {symbol} price = ₹{hist['Close'].iloc[-1]:.2f}")

        # Test screener uses real data
        async with StockScreener() as screener:
            data = screener.get_stock_data(symbol)
            assert data is not None
            assert not data.empty

            # Compare with direct yfinance call
            screener_price = data['Close'].iloc[-1]
            yf_price = hist['Close'].iloc[-1]

            # Prices should be very close (within 1%)
            diff_pct = abs(screener_price - yf_price) / yf_price * 100
            assert diff_pct < 1, f"Screener price differs from yfinance by {diff_pct:.2f}%"

        logger.success("✅ All data sources verified as real")

