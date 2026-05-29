"""
Screener output models matching PLAN_OF_ACTION.md schema.

Extended with FundamentalData and StockAnalysisData for multi-strategy analysis.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ============================================
# FUNDAMENTAL DATA MODELS (NEW)
# ============================================

class FundamentalData(BaseModel):
    """
    Fundamental metrics for a stock.
    Fetched from yfinance Ticker.info for multi-strategy analysis.
    """
    # Valuation metrics
    pe_ratio: Optional[float] = Field(None, description="Trailing P/E ratio")
    forward_pe: Optional[float] = Field(None, description="Forward P/E ratio")
    pb_ratio: Optional[float] = Field(None, description="Price to Book ratio")

    # Earnings metrics
    eps: Optional[float] = Field(None, description="Trailing EPS")
    eps_growth_yoy: Optional[float] = Field(None, description="EPS growth YoY %")

    # Size metrics
    market_cap_cr: float = Field(default=0, description="Market cap in Crores")

    # Financial health
    debt_to_equity: Optional[float] = Field(None, description="Debt to Equity ratio")
    current_ratio: Optional[float] = Field(None, description="Current ratio")

    # Profitability
    roe: Optional[float] = Field(None, description="Return on Equity %")
    roa: Optional[float] = Field(None, description="Return on Assets %")
    profit_margin: Optional[float] = Field(None, description="Profit margin %")

    # Dividend
    dividend_yield: Optional[float] = Field(None, description="Dividend yield %")

    # Book value
    book_value: Optional[float] = Field(None, description="Book value per share")

    # 52-week range
    week_52_high: Optional[float] = Field(None, description="52-week high price")
    week_52_low: Optional[float] = Field(None, description="52-week low price")
    week_52_change_pct: Optional[float] = Field(None, description="52-week price change %")

    # Classification
    sector: str = Field(default="Unknown", description="Sector classification")
    industry: str = Field(default="Unknown", description="Industry classification")

    # Data quality
    data_available: bool = Field(default=True, description="Whether fundamental data was available")
    last_updated: datetime = Field(default_factory=datetime.now)


class EnhancedNewsContext(BaseModel):
    """
    Enhanced news context with detailed sentiment analysis.
    Used for news-based strategy analysis.
    """
    has_recent_news: bool = Field(default=False, description="Has news in last 24h")
    news_count_24h: int = Field(default=0, description="Number of news articles in 24h")

    # Sentiment analysis
    sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        default="neutral", description="Overall sentiment"
    )
    sentiment_score: float = Field(
        default=0.0, ge=-1.0, le=1.0, description="Sentiment score -1 to 1"
    )

    # Impact assessment
    impact: Literal["HIGH", "MEDIUM", "LOW", "NONE"] = Field(
        default="NONE", description="News impact level"
    )

    # Latest news details
    latest_headline: Optional[str] = Field(None, description="Most recent headline")
    latest_summary: Optional[str] = Field(None, description="Summary of latest news")
    latest_source: Optional[str] = Field(None, description="Source of latest news")
    hours_since_latest: Optional[float] = Field(None, description="Hours since latest news")

    # Categories
    categories: List[str] = Field(
        default_factory=list, description="News categories (earnings, M&A, etc.)"
    )

    # Event flags
    is_earnings_related: bool = Field(default=False, description="Related to earnings")
    is_corporate_action: bool = Field(default=False, description="Related to corporate action")
    is_sector_news: bool = Field(default=False, description="Sector-wide news")


class StockAnalysisData(BaseModel):
    """
    Complete data package for multi-strategy analysis.
    Aggregates data from all sources for comprehensive stock evaluation.
    """
    # Identification
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    segment: str = Field(default="NSE_EQ", description="Market segment")

    # Live price data
    current_price: float = Field(..., description="Current/last traded price")
    prev_close: float = Field(..., description="Previous day close")
    day_change: float = Field(default=0, description="Absolute change today")
    day_change_pct: float = Field(default=0, description="Percentage change today")
    day_high: float = Field(default=0, description="Today's high")
    day_low: float = Field(default=0, description="Today's low")
    day_open: float = Field(default=0, description="Today's open")
    vwap: float = Field(default=0, description="Volume weighted average price")

    # Volume metrics
    volume: int = Field(default=0, description="Today's volume")
    avg_volume_10d: int = Field(default=0, description="10-day average volume")
    rvol: float = Field(default=1.0, description="Relative volume")

    # Fundamental data
    fundamentals: FundamentalData = Field(default_factory=FundamentalData)

    # Technical indicators
    rsi_14: float = Field(default=50, description="14-period RSI")
    atr: float = Field(default=0, description="14-period ATR")
    atr_pct: float = Field(default=0, description="ATR as % of price")
    above_20ema: bool = Field(default=False, description="Price above 20 EMA")
    above_50ema: bool = Field(default=False, description="Price above 50 EMA")
    trend: Literal["uptrend", "downtrend", "sideways"] = Field(
        default="sideways", description="Current trend"
    )

    # Pivot levels
    pivot_pp: float = Field(default=0, description="Pivot point")
    support_1: float = Field(default=0, description="Support level 1")
    support_2: float = Field(default=0, description="Support level 2")
    resistance_1: float = Field(default=0, description="Resistance level 1")
    resistance_2: float = Field(default=0, description="Resistance level 2")

    # News context
    news: EnhancedNewsContext = Field(default_factory=EnhancedNewsContext)

    # Market context
    nifty_trend: Literal["bullish", "bearish", "sideways"] = Field(
        default="sideways", description="NIFTY trend"
    )
    nifty_change_pct: float = Field(default=0, description="NIFTY change %")
    vix: float = Field(default=15, description="India VIX")
    sector_performance: float = Field(default=0, description="Sector performance %")

    # Screener score (from Stage 1)
    screener_score: float = Field(default=0, ge=0, le=100, description="Screening score")

    # Metadata
    data_timestamp: datetime = Field(default_factory=datetime.now)
    data_freshness_seconds: int = Field(default=0, description="Age of data in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "name": "Reliance Industries Ltd",
                "current_price": 2450.50,
                "day_change_pct": 1.2,
                "fundamentals": {
                    "pe_ratio": 24.5,
                    "eps": 98.5,
                    "market_cap_cr": 1850000,
                    "sector": "Energy"
                },
                "rsi_14": 58,
                "trend": "uptrend",
                "screener_score": 87
            }
        }


# ============================================
# ORIGINAL SCREENER MODELS
# ============================================

class MarketContext(BaseModel):
    """Market context for screening output."""
    nifty_trend: str = Field(..., description="bullish/bearish/sideways")
    nifty_change_pct: float = Field(..., description="NIFTY % change today")
    market_breadth: str = Field(..., description="positive/negative/neutral")
    vix: float = Field(..., description="India VIX value")
    timestamp: datetime = Field(default_factory=datetime.now)


class LiquidityMetrics(BaseModel):
    """Liquidity metrics for a stock."""
    today_turnover_cr: float = Field(..., description="Today's turnover in Crores")
    avg_10d_turnover_cr: float = Field(..., description="10-day avg turnover in Crores")
    rvol: float = Field(..., description="Relative volume (today/10d avg)")
    today_volume: int = Field(..., description="Today's volume")
    avg_10d_volume: int = Field(..., description="10-day average volume")


class PriceAction(BaseModel):
    """Price action metrics for a stock."""
    last_price: float = Field(..., description="Current/last traded price")
    prev_close: float = Field(..., description="Previous day close")
    today_open: float = Field(..., description="Today's open price")
    today_high: float = Field(..., description="Today's high")
    today_low: float = Field(..., description="Today's low")
    today_pct_change: float = Field(..., description="Today's % change")
    gap_pct: float = Field(..., description="Gap % from prev close to open")
    vwap: float = Field(..., description="Volume weighted average price")
    vwap_distance_pct: float = Field(..., description="% distance from VWAP")


class TechnicalIndicators(BaseModel):
    """Technical indicators for a stock."""
    rsi: float = Field(..., description="14-period RSI")
    above_20ema: bool = Field(..., description="Price above 20 EMA")
    above_50ema: bool = Field(..., description="Price above 50 EMA")
    atr: float = Field(..., description="14-period ATR")
    atr_pct: float = Field(..., description="ATR as % of price")
    trend_label: str = Field(..., description="uptrend/downtrend/sideways")
    near_day_high: bool = Field(..., description="Within 1% of day high")
    near_day_low: bool = Field(..., description="Within 1% of day low")


class PivotLevels(BaseModel):
    """Pivot point levels for a stock."""
    prev_high: float = Field(..., description="Previous day high")
    prev_low: float = Field(..., description="Previous day low")
    pivot_pp: float = Field(..., description="Pivot point")
    s1: float = Field(..., description="Support 1")
    s2: float = Field(..., description="Support 2")
    r1: float = Field(..., description="Resistance 1")
    r2: float = Field(..., description="Resistance 2")


class NewsContext(BaseModel):
    """News context for a stock."""
    has_fresh_news: bool = Field(default=False, description="Has news in last 24h")
    sentiment: str = Field(default="neutral", description="bullish/bearish/neutral")
    category: Optional[str] = Field(None, description="earnings/sector/macro/etc")
    summary: Optional[str] = Field(None, description="Brief news summary")
    is_event_today: bool = Field(default=False, description="Has event today")


class ScreenerCandidate(BaseModel):
    """A single screened stock candidate."""
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    segment: str = Field(default="NSE_EQ", description="Market segment")
    market_cap_cr: float = Field(..., description="Market cap in Crores")
    liquidity: LiquidityMetrics
    price_action: PriceAction
    technicals: TechnicalIndicators
    levels: PivotLevels
    news: NewsContext
    score: float = Field(..., ge=0, le=100, description="Screening score 0-100")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "name": "Reliance Industries Ltd",
                "segment": "NSE_EQ",
                "market_cap_cr": 1850000,
                "score": 85
            }
        }


class ScreenerOutput(BaseModel):
    """Complete screener output matching PLAN_OF_ACTION.md schema."""
    timestamp: datetime = Field(default_factory=datetime.now)
    market_context: MarketContext
    candidates: List[ScreenerCandidate] = Field(default_factory=list)
    total_scanned: int = Field(default=0, description="Total stocks scanned")
    passed_filters: int = Field(default=0, description="Stocks passing all filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T09:30:00",
                "total_scanned": 200,
                "passed_filters": 10
            }
        }

