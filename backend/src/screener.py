"""
Stock Screener Module for Trading Bot.
Implements the 3-stage pipeline Stage 1: Stock Screener from PLAN_OF_ACTION.md.

Screening Criteria:
- Liquidity: Turnover ≥ ₹10 Cr/day
- RVOL: ≥ 1.5x (vs 10-day avg)
- ATR%: 1.5-5%
- Market Cap: ≥ ₹5,000 Cr
- RSI: 30-70
- Gap: < 3%

Scoring Weights:
- Liquidity: 30%
- Volatility: 25%
- Trend: 25%
- News: 20%
"""

import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
from loguru import logger
from functools import lru_cache
import time

from config import get_config
from data.nifty_stocks import get_all_symbols, get_market_cap, NIFTY_50
from models.screener import (
    MarketContext, LiquidityMetrics, PriceAction, TechnicalIndicators,
    PivotLevels, NewsContext, ScreenerCandidate, ScreenerOutput
)

config = get_config()


class StockScreener:
    """
    Enhanced Stock Screener implementing PLAN_OF_ACTION.md requirements.

    Features:
    - NIFTY 200 stock universe
    - RVOL, turnover, ATR%, market cap, gap filters
    - Pivot points and VWAP distance calculation
    - Market context (NIFTY trend, VIX)
    - Weighted scoring algorithm
    - Structured JSON output
    """

    # Scoring weights from PLAN_OF_ACTION.md
    WEIGHT_LIQUIDITY = 0.30
    WEIGHT_VOLATILITY = 0.25
    WEIGHT_TREND = 0.25
    WEIGHT_NEWS = 0.20

    def __init__(self):
        self.config = config
        self.session = None
        self._cache: Dict[str, Tuple[Any, float]] = {}  # symbol -> (data, timestamp)
        self._cache_ttl = 60  # 1 minute cache TTL
        self._market_context_cache: Optional[Tuple[MarketContext, float]] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid."""
        if symbol not in self._cache:
            return False
        _, timestamp = self._cache[symbol]
        return (time.time() - timestamp) < self._cache_ttl

    def get_stock_data(self, symbol: str, period: str = "15d") -> Optional[pd.DataFrame]:
        """
        Fetch stock data using yfinance with caching.
        Uses 15d period to calculate 10-day averages properly.

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            period: Data period (default '15d' for 10-day avg calculations)

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            # Check cache first
            if self._is_cache_valid(symbol):
                return self._cache[symbol][0]

            # Add .NS suffix for NSE stocks
            ns_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol

            ticker = yf.Ticker(ns_symbol)
            # Get daily data for historical calculations
            daily_data = ticker.history(period=period, interval="1d")

            if daily_data.empty:
                logger.warning(f"No data found for {symbol}")
                return None

            # Cache the data
            self._cache[symbol] = (daily_data, time.time())
            return daily_data

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def get_intraday_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch intraday data for today's metrics.

        Args:
            symbol: Stock symbol

        Returns:
            DataFrame with intraday OHLCV data
        """
        try:
            ns_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
            ticker = yf.Ticker(ns_symbol)
            data = ticker.history(period="1d", interval="5m")
            return data if not data.empty else None
        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None

    def calculate_liquidity_metrics(self, daily_data: pd.DataFrame,
                                     intraday_data: Optional[pd.DataFrame],
                                     current_price: float) -> Optional[LiquidityMetrics]:
        """
        Calculate liquidity metrics per PLAN_OF_ACTION.md.

        Metrics:
        - Today's turnover in Crores
        - 10-day average turnover
        - RVOL (relative volume vs 10-day avg)
        """
        if daily_data.empty or len(daily_data) < 2:
            return None

        try:
            # Calculate 10-day average volume
            last_10_days = daily_data.tail(10)
            avg_10d_volume = int(last_10_days['Volume'].mean())

            # Today's volume (from intraday or last daily bar)
            if intraday_data is not None and not intraday_data.empty:
                today_volume = int(intraday_data['Volume'].sum())
            else:
                today_volume = int(daily_data['Volume'].iloc[-1])

            # Calculate turnover (Volume * Price / 1Cr)
            today_turnover_cr = (today_volume * current_price) / 10000000
            avg_10d_turnover_cr = (avg_10d_volume * current_price) / 10000000

            # RVOL calculation
            rvol = today_volume / avg_10d_volume if avg_10d_volume > 0 else 0

            return LiquidityMetrics(
                today_turnover_cr=round(today_turnover_cr, 2),
                avg_10d_turnover_cr=round(avg_10d_turnover_cr, 2),
                rvol=round(rvol, 2),
                today_volume=today_volume,
                avg_10d_volume=avg_10d_volume
            )

        except Exception as e:
            logger.error(f"Error calculating liquidity metrics: {e}")
            return None

    def calculate_price_action(self, daily_data: pd.DataFrame,
                                intraday_data: Optional[pd.DataFrame]) -> Optional[PriceAction]:
        """
        Calculate price action metrics per PLAN_OF_ACTION.md.
        """
        if daily_data.empty or len(daily_data) < 2:
            return None

        try:
            # Previous day data
            prev_day = daily_data.iloc[-2] if len(daily_data) >= 2 else daily_data.iloc[-1]
            prev_close = float(prev_day['Close'])

            # Today's data
            if intraday_data is not None and not intraday_data.empty:
                today_open = float(intraday_data['Open'].iloc[0])
                today_high = float(intraday_data['High'].max())
                today_low = float(intraday_data['Low'].min())
                last_price = float(intraday_data['Close'].iloc[-1])

                # Calculate VWAP from intraday
                typical_price = (intraday_data['High'] + intraday_data['Low'] + intraday_data['Close']) / 3
                vwap = float((typical_price * intraday_data['Volume']).sum() / intraday_data['Volume'].sum())
            else:
                today = daily_data.iloc[-1]
                today_open = float(today['Open'])
                today_high = float(today['High'])
                today_low = float(today['Low'])
                last_price = float(today['Close'])
                vwap = (today_high + today_low + last_price) / 3

            # Calculate metrics
            today_pct_change = ((last_price - prev_close) / prev_close) * 100
            gap_pct = ((today_open - prev_close) / prev_close) * 100
            vwap_distance_pct = ((last_price - vwap) / vwap) * 100

            return PriceAction(
                last_price=round(last_price, 2),
                prev_close=round(prev_close, 2),
                today_open=round(today_open, 2),
                today_high=round(today_high, 2),
                today_low=round(today_low, 2),
                today_pct_change=round(today_pct_change, 2),
                gap_pct=round(gap_pct, 2),
                vwap=round(vwap, 2),
                vwap_distance_pct=round(vwap_distance_pct, 2)
            )

        except Exception as e:
            logger.error(f"Error calculating price action: {e}")
            return None

    def calculate_technical_indicators(self, daily_data: pd.DataFrame,
                                        price_action: PriceAction) -> Optional[TechnicalIndicators]:
        """
        Calculate technical indicators per PLAN_OF_ACTION.md.

        Includes:
        - RSI (14-period)
        - EMA (20, 50)
        - ATR (14-period)
        - Trend label
        """
        if daily_data.empty or len(daily_data) < 14:
            return None

        try:
            close = daily_data['Close']
            high = daily_data['High']
            low = daily_data['Low']

            # RSI calculation (14-period)
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

            # EMA calculations
            ema_20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
            ema_50 = close.ewm(span=min(50, len(close)), adjust=False).mean().iloc[-1]

            # ATR calculation (14-period)
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = float(tr.rolling(window=14).mean().iloc[-1])
            atr_pct = (atr / price_action.last_price) * 100

            # Trend determination
            above_20ema = price_action.last_price > ema_20
            above_50ema = price_action.last_price > ema_50

            if above_20ema and above_50ema:
                trend_label = "uptrend"
            elif not above_20ema and not above_50ema:
                trend_label = "downtrend"
            else:
                trend_label = "sideways"

            # Near day high/low
            day_range = price_action.today_high - price_action.today_low
            near_day_high = (price_action.today_high - price_action.last_price) <= (day_range * 0.01) if day_range > 0 else False
            near_day_low = (price_action.last_price - price_action.today_low) <= (day_range * 0.01) if day_range > 0 else False

            return TechnicalIndicators(
                rsi=round(current_rsi, 2),
                above_20ema=above_20ema,
                above_50ema=above_50ema,
                atr=round(atr, 2),
                atr_pct=round(atr_pct, 2),
                trend_label=trend_label,
                near_day_high=near_day_high,
                near_day_low=near_day_low
            )

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return None

    def calculate_pivot_levels(self, daily_data: pd.DataFrame) -> Optional[PivotLevels]:
        """
        Calculate pivot point levels from previous day's data.

        Formula:
        - PP = (H + L + C) / 3
        - R1 = 2*PP - L
        - R2 = PP + (H - L)
        - S1 = 2*PP - H
        - S2 = PP - (H - L)
        """
        if daily_data.empty or len(daily_data) < 2:
            return None

        try:
            prev_day = daily_data.iloc[-2]
            prev_high = float(prev_day['High'])
            prev_low = float(prev_day['Low'])
            prev_close = float(prev_day['Close'])

            # Pivot point calculation
            pp = (prev_high + prev_low + prev_close) / 3
            r1 = 2 * pp - prev_low
            r2 = pp + (prev_high - prev_low)
            s1 = 2 * pp - prev_high
            s2 = pp - (prev_high - prev_low)

            return PivotLevels(
                prev_high=round(prev_high, 2),
                prev_low=round(prev_low, 2),
                pivot_pp=round(pp, 2),
                s1=round(s1, 2),
                s2=round(s2, 2),
                r1=round(r1, 2),
                r2=round(r2, 2)
            )

        except Exception as e:
            logger.error(f"Error calculating pivot levels: {e}")
            return None

    async def get_market_context(self) -> MarketContext:
        """
        Get current market context (NIFTY trend, VIX).
        Cached for 5 minutes.
        """
        # Check cache
        if self._market_context_cache:
            ctx, timestamp = self._market_context_cache
            if (time.time() - timestamp) < 300:  # 5 min cache
                return ctx

        try:
            # Fetch NIFTY 50 data
            nifty = yf.Ticker("^NSEI")
            nifty_data = nifty.history(period="2d", interval="1d")

            if not nifty_data.empty and len(nifty_data) >= 2:
                nifty_prev = float(nifty_data['Close'].iloc[-2])
                nifty_curr = float(nifty_data['Close'].iloc[-1])
                nifty_change_pct = ((nifty_curr - nifty_prev) / nifty_prev) * 100

                if nifty_change_pct > 0.5:
                    nifty_trend = "bullish"
                elif nifty_change_pct < -0.5:
                    nifty_trend = "bearish"
                else:
                    nifty_trend = "sideways"
            else:
                nifty_change_pct = 0.0
                nifty_trend = "sideways"

            # Fetch India VIX
            vix = yf.Ticker("^INDIAVIX")
            vix_data = vix.history(period="1d")
            vix_value = float(vix_data['Close'].iloc[-1]) if not vix_data.empty else 15.0

            # Market breadth (simplified - would need advance/decline data)
            if nifty_change_pct > 0.3:
                market_breadth = "positive"
            elif nifty_change_pct < -0.3:
                market_breadth = "negative"
            else:
                market_breadth = "neutral"

            ctx = MarketContext(
                nifty_trend=nifty_trend,
                nifty_change_pct=round(nifty_change_pct, 2),
                market_breadth=market_breadth,
                vix=round(vix_value, 2)
            )

            self._market_context_cache = (ctx, time.time())
            return ctx

        except Exception as e:
            logger.error(f"Error fetching market context: {e}")
            return MarketContext(
                nifty_trend="sideways",
                nifty_change_pct=0.0,
                market_breadth="neutral",
                vix=15.0
            )

    def screen_single_stock(self, symbol: str) -> Optional[ScreenerCandidate]:
        """
        Screen a single stock and return structured candidate.

        Args:
            symbol: Stock symbol to screen

        Returns:
            ScreenerCandidate or None if failed/filtered
        """
        try:
            # Get daily and intraday data
            daily_data = self.get_stock_data(symbol)
            if daily_data is None or daily_data.empty:
                return None

            intraday_data = self.get_intraday_data(symbol)

            # Calculate price action first (needed for other calculations)
            price_action = self.calculate_price_action(daily_data, intraday_data)
            if price_action is None:
                return None

            # Calculate all metrics
            liquidity = self.calculate_liquidity_metrics(daily_data, intraday_data, price_action.last_price)
            technicals = self.calculate_technical_indicators(daily_data, price_action)
            levels = self.calculate_pivot_levels(daily_data)

            if not all([liquidity, technicals, levels]):
                return None

            # Get market cap
            market_cap_cr = get_market_cap(symbol)

            # Create news context (placeholder - would integrate with news_aggregator)
            news = NewsContext(
                has_fresh_news=False,
                sentiment="neutral",
                category=None,
                summary=None,
                is_event_today=False
            )

            # Calculate screening score
            score = self._calculate_score(liquidity, technicals, price_action, news)

            return ScreenerCandidate(
                symbol=symbol,
                name=symbol,  # Would fetch from master data
                segment="NSE_EQ",
                market_cap_cr=market_cap_cr,
                liquidity=liquidity,
                price_action=price_action,
                technicals=technicals,
                levels=levels,
                news=news,
                score=score
            )

        except Exception as e:
            logger.error(f"Error screening {symbol}: {e}")
            return None

    def _calculate_score(self, liquidity: LiquidityMetrics,
                          technicals: TechnicalIndicators,
                          price_action: PriceAction,
                          news: NewsContext) -> float:
        """
        Calculate weighted screening score (0-100).

        Weights from PLAN_OF_ACTION.md:
        - Liquidity: 30%
        - Volatility: 25%
        - Trend: 25%
        - News: 20%
        """
        # Liquidity score (0-100)
        rvol_score = min(liquidity.rvol / 3.0, 1.0) * 100  # Cap at 3x
        turnover_score = min(liquidity.today_turnover_cr / 50.0, 1.0) * 100  # Cap at 50Cr
        liquidity_score = (rvol_score * 0.6 + turnover_score * 0.4)

        # Volatility score (0-100) - prefer ATR% in sweet spot (2-3%)
        atr_pct = technicals.atr_pct
        if 2.0 <= atr_pct <= 3.0:
            volatility_score = 100
        elif 1.5 <= atr_pct < 2.0 or 3.0 < atr_pct <= 4.0:
            volatility_score = 75
        elif 1.0 <= atr_pct < 1.5 or 4.0 < atr_pct <= 5.0:
            volatility_score = 50
        else:
            volatility_score = 25

        # Trend score (0-100)
        trend_score = 0
        if technicals.trend_label == "uptrend":
            trend_score = 80
            if technicals.near_day_high:
                trend_score = 100
        elif technicals.trend_label == "downtrend":
            trend_score = 60  # Can still trade shorts
            if technicals.near_day_low:
                trend_score = 80
        else:
            trend_score = 50

        # Add RSI component
        rsi = technicals.rsi
        if 40 <= rsi <= 60:
            trend_score = min(trend_score + 10, 100)

        # News score (0-100)
        news_score = 50  # Neutral baseline
        if news.has_fresh_news:
            if news.sentiment == "bullish":
                news_score = 90
            elif news.sentiment == "bearish":
                news_score = 70  # Still tradeable for shorts
            else:
                news_score = 60

        # Weighted final score
        final_score = (
            liquidity_score * self.WEIGHT_LIQUIDITY +
            volatility_score * self.WEIGHT_VOLATILITY +
            trend_score * self.WEIGHT_TREND +
            news_score * self.WEIGHT_NEWS
        )

        return round(min(max(final_score, 0), 100), 2)

    def apply_screening_filters(self, candidate: ScreenerCandidate) -> bool:
        """
        Apply PLAN_OF_ACTION.md filtering criteria.

        Criteria:
        - Turnover ≥ ₹10 Cr/day
        - RVOL ≥ 1.5x
        - ATR% 1.5-5%
        - Market Cap ≥ ₹5,000 Cr
        - RSI 30-70
        - Gap < 3%

        Returns:
            True if candidate passes all filters
        """
        cfg = self.config

        # Turnover filter
        if candidate.liquidity.today_turnover_cr < cfg.SCREENER_MIN_TURNOVER_CR:
            logger.debug(f"❌ {candidate.symbol}: Turnover {candidate.liquidity.today_turnover_cr:.1f}Cr < {cfg.SCREENER_MIN_TURNOVER_CR}Cr")
            return False

        # RVOL filter
        if candidate.liquidity.rvol < cfg.SCREENER_MIN_RVOL:
            logger.debug(f"❌ {candidate.symbol}: RVOL {candidate.liquidity.rvol:.2f} < {cfg.SCREENER_MIN_RVOL}")
            return False

        # ATR% filter
        if not (cfg.SCREENER_MIN_ATR_PCT <= candidate.technicals.atr_pct <= cfg.SCREENER_MAX_ATR_PCT):
            logger.debug(f"❌ {candidate.symbol}: ATR% {candidate.technicals.atr_pct:.2f} not in [{cfg.SCREENER_MIN_ATR_PCT}, {cfg.SCREENER_MAX_ATR_PCT}]")
            return False

        # Market cap filter
        if candidate.market_cap_cr < cfg.SCREENER_MIN_MARKET_CAP_CR:
            logger.debug(f"❌ {candidate.symbol}: Market Cap {candidate.market_cap_cr:.0f}Cr < {cfg.SCREENER_MIN_MARKET_CAP_CR}Cr")
            return False

        # RSI filter
        if not (cfg.SCREENER_MIN_RSI <= candidate.technicals.rsi <= cfg.SCREENER_MAX_RSI):
            logger.debug(f"❌ {candidate.symbol}: RSI {candidate.technicals.rsi:.1f} not in [{cfg.SCREENER_MIN_RSI}, {cfg.SCREENER_MAX_RSI}]")
            return False

        # Gap filter
        if abs(candidate.price_action.gap_pct) > cfg.SCREENER_MAX_GAP_PCT:
            logger.debug(f"❌ {candidate.symbol}: Gap {candidate.price_action.gap_pct:.2f}% > {cfg.SCREENER_MAX_GAP_PCT}%")
            return False

        logger.info(f"✅ {candidate.symbol} passed all filters (Score: {candidate.score:.1f})")
        return True

    def get_stock_universe(self) -> List[str]:
        """
        Get the stock universe for screening.
        Uses NIFTY 200 from data module.
        """
        return get_all_symbols()

    async def screen_stocks(self, max_stocks: Optional[int] = None) -> ScreenerOutput:
        """
        Main screening function implementing Stage 1 of the pipeline.

        Process:
        1. Get market context (NIFTY trend, VIX)
        2. Screen all stocks in universe
        3. Apply PLAN_OF_ACTION.md filters
        4. Sort by score and return top candidates

        Args:
            max_stocks: Maximum number of stocks to return (default from config)

        Returns:
            ScreenerOutput with market context and candidates
        """
        if max_stocks is None:
            max_stocks = self.config.SCREENER_TOP_STOCKS

        try:
            logger.info(f"🔍 Starting stock screening for top {max_stocks} stocks")

            # Get market context first
            market_context = await self.get_market_context()
            logger.info(f"📊 Market Context: NIFTY {market_context.nifty_trend} ({market_context.nifty_change_pct:+.2f}%), VIX: {market_context.vix:.1f}")

            # Get stock universe
            symbols = self.get_stock_universe()
            total_scanned = len(symbols)
            logger.info(f"Screening {total_scanned} symbols from NIFTY 200 universe")

            # Screen each stock
            candidates: List[ScreenerCandidate] = []
            for symbol in symbols:
                candidate = self.screen_single_stock(symbol)
                if candidate and self.apply_screening_filters(candidate):
                    candidates.append(candidate)

                # Rate limiting to avoid API throttling
                await asyncio.sleep(0.05)

            passed_filters = len(candidates)
            logger.info(f"After filtering: {passed_filters}/{total_scanned} stocks passed")

            # Sort by score (descending) and take top N
            candidates.sort(key=lambda x: x.score, reverse=True)
            top_candidates = candidates[:max_stocks]

            logger.info(f"🎯 Selected top {len(top_candidates)} stocks for trading:")
            for i, c in enumerate(top_candidates, 1):
                logger.info(f"  {i}. {c.symbol}: Score={c.score:.1f}, RVOL={c.liquidity.rvol:.2f}, ATR%={c.technicals.atr_pct:.2f}")

            return ScreenerOutput(
                timestamp=datetime.now(),
                market_context=market_context,
                candidates=top_candidates,
                total_scanned=total_scanned,
                passed_filters=passed_filters
            )

        except Exception as e:
            logger.error(f"Error in stock screening: {e}")
            # Return empty output with market context
            return ScreenerOutput(
                timestamp=datetime.now(),
                market_context=await self.get_market_context(),
                candidates=[],
                total_scanned=0,
                passed_filters=0
            )

    async def screen_stocks_quick(self, symbols: List[str]) -> List[ScreenerCandidate]:
        """
        Quick screening for a specific list of symbols.
        Skips market context and returns raw candidates.

        Args:
            symbols: List of symbols to screen

        Returns:
            List of ScreenerCandidate objects
        """
        candidates = []
        for symbol in symbols:
            candidate = self.screen_single_stock(symbol)
            if candidate and self.apply_screening_filters(candidate):
                candidates.append(candidate)
            await asyncio.sleep(0.05)

        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates


# Standalone function for easy import
async def screen_top_stocks(max_stocks: int = 10) -> ScreenerOutput:
    """
    Convenience function to screen top stocks.

    Args:
        max_stocks: Maximum number of stocks to return

    Returns:
        ScreenerOutput with market context and candidates
    """
    async with StockScreener() as screener:
        return await screener.screen_stocks(max_stocks)


# Legacy function for backward compatibility
async def screen_top_stocks_legacy(max_stocks: int = 10) -> List[Dict]:
    """
    Legacy function returning dict format for backward compatibility.
    """
    output = await screen_top_stocks(max_stocks)
    return [c.model_dump() for c in output.candidates]


if __name__ == "__main__":
    # Test the screener
    async def test_screener():
        try:
            output = await screen_top_stocks(5)
            print(f"\n✅ Successfully screened stocks")
            print(f"📊 Market: NIFTY {output.market_context.nifty_trend} ({output.market_context.nifty_change_pct:+.2f}%)")
            print(f"📈 Scanned: {output.total_scanned}, Passed: {output.passed_filters}")

            if output.candidates:
                print("\nTop stocks for intraday trading:")
                for i, c in enumerate(output.candidates, 1):
                    print(f"  {i}. {c.symbol}: Score={c.score:.1f}, "
                          f"RVOL={c.liquidity.rvol:.2f}, "
                          f"ATR%={c.technicals.atr_pct:.2f}, "
                          f"RSI={c.technicals.rsi:.1f}")
            else:
                print("No stocks passed the screening criteria")

        except Exception as e:
            logger.error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(test_screener())
