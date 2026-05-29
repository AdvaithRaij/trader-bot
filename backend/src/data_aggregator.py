"""
Data Aggregator Service for Multi-Strategy Analysis Pipeline.

Aggregates data from multiple sources:
- Broker API: Live prices
- yfinance: Fundamental data, historical OHLCV
- NewsAggregator: News and sentiment
- Screener: Technical indicators

Provides complete StockAnalysisData for each stock.
"""

import asyncio
import yfinance as yf
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from loguru import logger
import time
from functools import lru_cache

from config import get_config
from models.screener import (
    FundamentalData,
    EnhancedNewsContext,
    StockAnalysisData,
    MarketContext
)
from data.nifty_stocks import get_market_cap

config = get_config()


class DataAggregator:
    """
    Aggregates data from multiple sources for comprehensive stock analysis.
    
    Used in Stage 2 of the multi-strategy pipeline to prepare complete
    data packages for AI analysis.
    """
    
    # Cache settings
    FUNDAMENTAL_CACHE_TTL = 3600  # 1 hour for fundamentals
    NEWS_CACHE_TTL = 300  # 5 minutes for news
    PRICE_CACHE_TTL = 60  # 1 minute for prices
    
    def __init__(self, broker=None, news_aggregator=None, screener=None):
        """
        Initialize DataAggregator with dependencies.
        
        Args:
            broker: FyersBroker instance for live prices
            news_aggregator: NewsAggregator instance for news/sentiment
            screener: StockScreener instance for technical calculations
        """
        self.broker = broker
        self.news_aggregator = news_aggregator
        self.screener = screener
        
        # Caches
        self._fundamental_cache: Dict[str, Tuple[FundamentalData, float]] = {}
        self._news_cache: Dict[str, Tuple[EnhancedNewsContext, float]] = {}
        self._market_context_cache: Optional[Tuple[MarketContext, float]] = None
        
    def _is_cache_valid(self, cache_entry: Optional[Tuple[Any, float]], ttl: int) -> bool:
        """Check if cache entry is still valid."""
        if cache_entry is None:
            return False
        _, timestamp = cache_entry
        return (time.time() - timestamp) < ttl
    
    def get_fundamental_data(self, symbol: str) -> FundamentalData:
        """
        Fetch fundamental data from yfinance.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            
        Returns:
            FundamentalData with all available metrics
        """
        # Check cache first
        cache_key = symbol
        if cache_key in self._fundamental_cache:
            if self._is_cache_valid(self._fundamental_cache[cache_key], self.FUNDAMENTAL_CACHE_TTL):
                logger.debug(f"Using cached fundamental data for {symbol}")
                return self._fundamental_cache[cache_key][0]
        
        try:
            # Fetch from yfinance
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info
            
            if not info or info.get('regularMarketPrice') is None:
                logger.warning(f"No yfinance data available for {symbol}")
                return FundamentalData(data_available=False)
            
            # Extract fundamental metrics
            fundamental = FundamentalData(
                # Valuation
                pe_ratio=info.get('trailingPE'),
                forward_pe=info.get('forwardPE'),
                pb_ratio=info.get('priceToBook'),
                
                # Earnings
                eps=info.get('trailingEps'),
                eps_growth_yoy=None,  # Not directly available
                
                # Size
                market_cap_cr=round(info.get('marketCap', 0) / 10000000, 2),  # Convert to Cr
                
                # Financial health
                debt_to_equity=info.get('debtToEquity'),
                current_ratio=info.get('currentRatio'),
                
                # Profitability
                roe=info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else None,
                roa=info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else None,
                profit_margin=info.get('profitMargins', 0) * 100 if info.get('profitMargins') else None,
                
                # Dividend
                dividend_yield=info.get('dividendYield', 0) * 100 if info.get('dividendYield') else None,
                
                # Book value
                book_value=info.get('bookValue'),
                
                # 52-week range
                week_52_high=info.get('fiftyTwoWeekHigh'),
                week_52_low=info.get('fiftyTwoWeekLow'),
                week_52_change_pct=info.get('52WeekChange', 0) * 100 if info.get('52WeekChange') else None,
                
                # Classification
                sector=info.get('sector', 'Unknown'),
                industry=info.get('industry', 'Unknown'),
                
                data_available=True,
                last_updated=datetime.now()
            )
            
            # Cache the result
            self._fundamental_cache[cache_key] = (fundamental, time.time())
            logger.debug(f"Fetched fundamental data for {symbol}: P/E={fundamental.pe_ratio}")
            
            return fundamental
            
        except Exception as e:
            logger.error(f"Error fetching fundamental data for {symbol}: {e}")
            return FundamentalData(data_available=False)

    async def get_news_context(self, symbol: str) -> EnhancedNewsContext:
        """
        Get news context for a stock from NewsAggregator.

        Args:
            symbol: Stock symbol

        Returns:
            EnhancedNewsContext with sentiment and impact analysis
        """
        # Check cache first
        cache_key = symbol
        if cache_key in self._news_cache:
            if self._is_cache_valid(self._news_cache[cache_key], self.NEWS_CACHE_TTL):
                logger.debug(f"Using cached news context for {symbol}")
                return self._news_cache[cache_key][0]

        try:
            if not self.news_aggregator:
                logger.warning("NewsAggregator not available")
                return EnhancedNewsContext()

            # Get news with analysis
            all_news = await self.news_aggregator.get_news_with_analysis(limit=50, refresh=False)

            # Filter news related to this symbol
            symbol_lower = symbol.lower()
            stock_name = symbol_lower  # Use symbol as stock name

            related_news = []
            for news in all_news:
                title = news.get('title', '').lower()
                summary = news.get('summary', '').lower()
                related_stocks = [s.lower() for s in news.get('relatedStocks', [])]

                # Check if news is related to this stock
                if (symbol_lower in title or symbol_lower in summary or
                    symbol_lower in related_stocks or
                    (stock_name and stock_name in title)):
                    related_news.append(news)

            if not related_news:
                return EnhancedNewsContext(has_recent_news=False)

            # Analyze the related news
            latest = related_news[0]

            # Calculate aggregate sentiment
            sentiments = [n.get('sentiment', 'NEUTRAL') for n in related_news]
            positive_count = sum(1 for s in sentiments if s == 'POSITIVE')
            negative_count = sum(1 for s in sentiments if s == 'NEGATIVE')

            if positive_count > negative_count:
                overall_sentiment = "bullish"
                sentiment_score = min(1.0, positive_count / len(sentiments))
            elif negative_count > positive_count:
                overall_sentiment = "bearish"
                sentiment_score = -min(1.0, negative_count / len(sentiments))
            else:
                overall_sentiment = "neutral"
                sentiment_score = 0.0

            # Determine impact
            impacts = [n.get('impact', 'LOW') for n in related_news]
            if 'HIGH' in impacts:
                impact = "HIGH"
            elif 'MEDIUM' in impacts:
                impact = "MEDIUM"
            else:
                impact = "LOW"

            # Calculate hours since latest
            pub_time = latest.get('publishedAt')
            hours_since = None
            if pub_time:
                try:
                    if isinstance(pub_time, str):
                        pub_dt = datetime.fromisoformat(pub_time.replace('Z', '+00:00'))
                    else:
                        pub_dt = pub_time
                    hours_since = (datetime.now(pub_dt.tzinfo) - pub_dt).total_seconds() / 3600
                except:
                    pass

            # Detect categories
            categories = []
            title_lower = latest.get('title', '').lower()
            if any(w in title_lower for w in ['earnings', 'results', 'profit', 'revenue']):
                categories.append('earnings')
            if any(w in title_lower for w in ['merger', 'acquisition', 'buyout']):
                categories.append('M&A')
            if any(w in title_lower for w in ['dividend', 'bonus', 'split']):
                categories.append('corporate_action')

            news_context = EnhancedNewsContext(
                has_recent_news=True,
                news_count_24h=len(related_news),
                sentiment=overall_sentiment,
                sentiment_score=round(sentiment_score, 2),
                impact=impact,
                latest_headline=latest.get('title', '')[:200],
                latest_summary=latest.get('summary', '')[:300],
                latest_source=latest.get('source', 'Unknown'),
                hours_since_latest=round(hours_since, 1) if hours_since else None,
                categories=categories,
                is_earnings_related='earnings' in categories,
                is_corporate_action='corporate_action' in categories,
                is_sector_news=any(w in title_lower for w in ['sector', 'industry'])
            )

            # Cache the result
            self._news_cache[cache_key] = (news_context, time.time())
            logger.debug(f"Fetched news context for {symbol}: {len(related_news)} articles, sentiment={overall_sentiment}")

            return news_context

        except Exception as e:
            logger.error(f"Error fetching news context for {symbol}: {e}")
            return EnhancedNewsContext()

    async def get_complete_stock_data(
        self,
        symbol: str,
        screener_candidate: Optional[Any] = None
    ) -> StockAnalysisData:
        """
        Fetch complete data for a single stock.

        Aggregates:
        - Live price from broker
        - Fundamental data from yfinance
        - Technical indicators from screener
        - News context from news aggregator

        Args:
            symbol: Stock symbol
            screener_candidate: Optional ScreenerCandidate with pre-calculated data

        Returns:
            Complete StockAnalysisData for multi-strategy analysis
        """
        start_time = time.time()

        try:
            # Fetch data in parallel where possible
            fundamental_task = asyncio.get_event_loop().run_in_executor(
                None, self.get_fundamental_data, symbol
            )
            news_task = self.get_news_context(symbol)

            # Get live price from broker or yfinance
            current_price = 0.0
            prev_close = 0.0
            if self.broker:
                try:
                    current_price = await self.broker.get_ltp(symbol)
                except Exception as e:
                    logger.warning(f"Could not get LTP for {symbol}: {e}")

            # If no broker or broker failed, get from yfinance
            if current_price == 0:
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(f"{symbol}.NS")
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        current_price = float(hist['Close'].iloc[-1])
                        prev_close = float(hist['Open'].iloc[-1])
                except Exception as e:
                    logger.warning(f"Could not get price from yfinance for {symbol}: {e}")

            # Wait for parallel tasks
            fundamentals, news_context = await asyncio.gather(
                fundamental_task, news_task
            )

            # Use screener candidate data if available
            if screener_candidate:
                return StockAnalysisData(
                    symbol=symbol,
                    name=screener_candidate.name,
                    segment=screener_candidate.segment,
                    current_price=screener_candidate.price_action.last_price,
                    prev_close=screener_candidate.price_action.prev_close,
                    day_change=screener_candidate.price_action.last_price - screener_candidate.price_action.prev_close,
                    day_change_pct=screener_candidate.price_action.today_pct_change,
                    day_high=screener_candidate.price_action.today_high,
                    day_low=screener_candidate.price_action.today_low,
                    day_open=screener_candidate.price_action.today_open,
                    vwap=screener_candidate.price_action.vwap,
                    volume=screener_candidate.liquidity.today_volume,
                    avg_volume_10d=screener_candidate.liquidity.avg_10d_volume,
                    rvol=screener_candidate.liquidity.rvol,
                    fundamentals=fundamentals,
                    rsi_14=screener_candidate.technicals.rsi,
                    atr=screener_candidate.technicals.atr,
                    atr_pct=screener_candidate.technicals.atr_pct,
                    above_20ema=screener_candidate.technicals.above_20ema,
                    above_50ema=screener_candidate.technicals.above_50ema,
                    trend=screener_candidate.technicals.trend_label,
                    pivot_pp=screener_candidate.levels.pivot_pp,
                    support_1=screener_candidate.levels.s1,
                    support_2=screener_candidate.levels.s2,
                    resistance_1=screener_candidate.levels.r1,
                    resistance_2=screener_candidate.levels.r2,
                    news=news_context,
                    screener_score=screener_candidate.score,
                    data_timestamp=datetime.now(),
                    data_freshness_seconds=int(time.time() - start_time)
                )

            # Fallback: fetch technical data from yfinance
            stock_name = symbol  # Use symbol as name

            return StockAnalysisData(
                symbol=symbol,
                name=stock_name,
                current_price=current_price,
                prev_close=prev_close,
                fundamentals=fundamentals,
                news=news_context,
                data_timestamp=datetime.now(),
                data_freshness_seconds=int(time.time() - start_time)
            )

        except Exception as e:
            logger.error(f"Error aggregating data for {symbol}: {e}")
            return StockAnalysisData(
                symbol=symbol,
                name=symbol,
                current_price=0,
                prev_close=0,
                data_timestamp=datetime.now()
            )

    async def get_batch_stock_data(
        self,
        symbols: List[str],
        screener_candidates: Optional[List[Any]] = None
    ) -> List[StockAnalysisData]:
        """
        Fetch complete data for multiple stocks in parallel.

        Args:
            symbols: List of stock symbols
            screener_candidates: Optional list of ScreenerCandidate objects

        Returns:
            List of StockAnalysisData for all stocks
        """
        start_time = time.time()

        # Create candidate map if provided
        candidate_map = {}
        if screener_candidates:
            for candidate in screener_candidates:
                candidate_map[candidate.symbol] = candidate

        # Fetch all stocks in parallel
        tasks = [
            self.get_complete_stock_data(
                symbol,
                screener_candidate=candidate_map.get(symbol)
            )
            for symbol in symbols
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching data for {symbols[i]}: {result}")
            else:
                valid_results.append(result)

        logger.info(f"Aggregated data for {len(valid_results)}/{len(symbols)} stocks in {time.time() - start_time:.2f}s")

        return valid_results

    async def get_market_context(self) -> Dict[str, Any]:
        """
        Get current market context (NIFTY trend, VIX, breadth).

        Returns:
            Dictionary with market context data
        """
        try:
            # Check cache
            if self._market_context_cache:
                if self._is_cache_valid(self._market_context_cache, 300):  # 5 min cache
                    return self._market_context_cache[0]

            # Fetch NIFTY data
            nifty = yf.Ticker("^NSEI")
            nifty_hist = nifty.history(period="5d")

            if nifty_hist.empty:
                return {"error": "Could not fetch NIFTY data"}

            nifty_close = float(nifty_hist['Close'].iloc[-1])
            nifty_prev = float(nifty_hist['Close'].iloc[-2])
            nifty_change_pct = ((nifty_close - nifty_prev) / nifty_prev) * 100

            # Determine trend
            if nifty_change_pct > 0.5:
                nifty_trend = "bullish"
            elif nifty_change_pct < -0.5:
                nifty_trend = "bearish"
            else:
                nifty_trend = "sideways"

            # Fetch VIX
            try:
                vix = yf.Ticker("^INDIAVIX")
                vix_hist = vix.history(period="1d")
                vix_value = float(vix_hist['Close'].iloc[-1]) if not vix_hist.empty else 15.0
            except:
                vix_value = 15.0

            context = {
                "nifty_value": round(nifty_close, 2),
                "nifty_change_pct": round(nifty_change_pct, 2),
                "nifty_trend": nifty_trend,
                "vix": round(vix_value, 2),
                "market_breadth": "positive" if nifty_change_pct > 0 else "negative",
                "timestamp": datetime.now().isoformat()
            }

            # Cache the result
            self._market_context_cache = (context, time.time())

            return context

        except Exception as e:
            logger.error(f"Error fetching market context: {e}")
            return {
                "nifty_trend": "sideways",
                "nifty_change_pct": 0,
                "vix": 15.0,
                "error": str(e)
            }

    def clear_cache(self):
        """Clear all caches."""
        self._fundamental_cache.clear()
        self._news_cache.clear()
        self._market_context_cache = None
        logger.info("DataAggregator caches cleared")

