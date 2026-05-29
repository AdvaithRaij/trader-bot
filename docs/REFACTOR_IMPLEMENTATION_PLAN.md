# Trading Bot Architecture Refactor: Multi-Strategy Analysis Pipeline

## Executive Summary

This document outlines the comprehensive refactoring plan to transform the trading bot into a **strategy-driven pipeline with multi-strategy analysis**. The goal is to provide users with clear, actionable trade recommendations backed by three distinct analytical approaches.

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Target Architecture](#target-architecture)
3. [The Three Strategies](#the-three-strategies)
4. [Data Requirements](#data-requirements)
5. [Backend Changes](#backend-changes)
6. [Frontend Changes](#frontend-changes)
7. [API Contract Changes](#api-contract-changes)
8. [Implementation Phases](#implementation-phases)
9. [UI/UX Flow](#uiux-flow)
10. [Success Criteria](#success-criteria)

---

## Current State Analysis

### What Exists Today

| Component | Status | Location |
|-----------|--------|----------|
| **3 Preset Strategies** | ✅ Exists | `seed_strategies.py` - News Momentum, Conservative, Aggressive |
| **Stock Screener** | ✅ Works | `screener.py` - RVOL, ATR, pivots, technicals |
| **AI Insight Provider** | ✅ Works | `ai_insight_provider.py` - Single plan generation |
| **Pipeline Orchestrator** | ✅ Works | `pipeline_orchestrator.py` - 3-stage flow |
| **News Aggregator** | ✅ Works | `news_aggregator.py` - Multi-source with AI analysis |
| **Broker API** | ✅ Works | `broker.py` - Fyers integration, live LTP |
| **Trade Executor** | ✅ Works | `trade_executor.py` - Risk validation, orders |
| **Strategy Manager UI** | ⚠️ To Remove | `frontend/src/pages/StrategyManager.tsx` |

### Current Data Gaps

| Data Type | Current State | Required Action |
|-----------|---------------|-----------------|
| **Live Price** | ✅ Available via `broker.get_ltp()` | None |
| **OHLCV History** | ✅ Available via `yfinance` | None |
| **Technical Indicators** | ✅ RSI, ATR, VWAP, pivots | None |
| **P/E Ratio** | ❌ Not fetched | Add `yfinance.Ticker.info` |
| **Market Cap** | ⚠️ Static in `nifty_stocks.py` | Fetch live from yfinance |
| **EPS, D/E Ratio** | ❌ Not fetched | Add `yfinance.Ticker.info` |
| **Sector/Industry** | ⚠️ Partial | Enhance from yfinance |
| **News Sentiment** | ✅ Available | Integrate into screener |

---

## Target Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRADING PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 1: STOCK SCREENING                                              │   │
│  │                                                                        │   │
│  │  Input: NIFTY 200 Universe                                            │   │
│  │  Process: Technical filters (RVOL, ATR, RSI, Gap, Liquidity)          │   │
│  │  Output: Top 5-10 candidates with scores                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 2: DATA AGGREGATION (NEW)                                       │   │
│  │                                                                        │   │
│  │  For each screened stock, fetch:                                      │   │
│  │  ├── Live Price (Broker API)                                          │   │
│  │  ├── Fundamental Data (yfinance.info)                                 │   │
│  │  ├── Technical Indicators (calculated)                                │   │
│  │  └── News & Sentiment (NewsAggregator)                                │   │
│  │                                                                        │   │
│  │  Output: Complete StockAnalysisData for each candidate                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 3: MULTI-STRATEGY AI ANALYSIS (ENHANCED)                        │   │
│  │                                                                        │   │
│  │  For each stock, generate 3 strategy analyses:                        │   │
│  │                                                                        │   │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │   │
│  │  │ FUNDAMENTAL     │ │ NEWS-BASED      │ │ COMBINED        │          │   │
│  │  │ STRATEGY        │ │ STRATEGY        │ │ STRATEGY        │          │   │
│  │  │                 │ │                 │ │                 │          │   │
│  │  │ Focus: P/E, EPS │ │ Focus: News     │ │ Focus: All      │          │   │
│  │  │ Market Cap, D/E │ │ Sentiment,      │ │ factors         │          │   │
│  │  │ Sector trends   │ │ Impact, Timing  │ │ weighted        │          │   │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘          │   │
│  │                                                                        │   │
│  │  Each strategy outputs:                                               │   │
│  │  - Entry, SL, T1, T2 levels                                           │   │
│  │  - Confidence score (0-100%)                                          │   │
│  │  - Risk assessment                                                    │   │
│  │  - Detailed reasoning                                                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 4: AI RECOMMENDATION (NEW)                                      │   │
│  │                                                                        │   │
│  │  Compare all 3 strategies for each stock                              │   │
│  │  Generate: "Best Strategy" recommendation with reasoning              │   │
│  │  Output: Ranked strategies per stock                                  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    ↓                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ STAGE 5: USER APPROVAL & EXECUTION                                    │   │
│  │                                                                        │   │
│  │  User reviews multi-strategy analysis                                 │   │
│  │  User selects stocks + preferred strategy for each                    │   │
│  │  User approves → Trade Executor places orders                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Three Strategies

### Strategy 1: Fundamental Analysis

**Focus:** Value-based decision making using company fundamentals

| Metric | Weight | Criteria |
|--------|--------|----------|
| P/E Ratio | 25% | Compare to sector average |
| Market Cap | 15% | Large-cap preferred for stability |
| EPS Growth | 20% | Positive YoY growth |
| Debt-to-Equity | 15% | Lower is better |
| Sector Momentum | 15% | Sector performance vs market |
| 52-Week Position | 10% | Distance from high/low |

**Best For:** Swing trades, lower volatility, value plays

**Risk Profile:** Conservative (SL: 1.5%, Target: 3-4%)

---

### Strategy 2: News-Based Analysis

**Focus:** Event-driven trading based on news sentiment and impact

| Metric | Weight | Criteria |
|--------|--------|----------|
| News Sentiment | 30% | Positive/Negative/Neutral |
| News Impact | 25% | HIGH/MEDIUM/LOW |
| News Recency | 20% | Within last 24h preferred |
| News Relevance | 15% | Direct company mention |
| Event Type | 10% | Earnings, M&A, Policy, etc. |

**Best For:** Momentum trades, quick moves, event-driven plays

**Risk Profile:** Moderate-Aggressive (SL: 2%, Target: 5%)

---

### Strategy 3: Combined Analysis (Hybrid)

**Focus:** Holistic view combining fundamentals, technicals, and news

| Component | Weight | Source |
|-----------|--------|--------|
| Technical Score | 35% | RSI, VWAP, ATR, Trend |
| Fundamental Score | 30% | P/E, EPS, Market Cap |
| News Score | 25% | Sentiment, Impact |
| Market Context | 10% | NIFTY trend, VIX |

**Best For:** Balanced approach, higher confidence trades

**Risk Profile:** Adaptive (SL: 1.5-2.5%, Target: 3-6% based on confidence)

---

## Data Requirements

### Complete Stock Analysis Data Model

```python
class StockAnalysisData:
    """Complete data package for multi-strategy analysis."""

    # Identification
    symbol: str
    name: str
    sector: str
    industry: str

    # Live Price Data
    current_price: float
    prev_close: float
    day_change_pct: float
    day_high: float
    day_low: float
    vwap: float

    # Fundamental Data (NEW)
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    eps: Optional[float]
    market_cap_cr: float
    debt_to_equity: Optional[float]
    book_value: Optional[float]
    dividend_yield: Optional[float]
    roe: Optional[float]  # Return on Equity

    # Technical Data
    rsi_14: float
    atr_pct: float
    above_20ema: bool
    above_50ema: bool
    trend: str  # uptrend/downtrend/sideways
    rvol: float

    # Pivot Levels
    pivot_pp: float
    support_1: float
    support_2: float
    resistance_1: float
    resistance_2: float

    # News Data
    has_recent_news: bool
    news_sentiment: str  # bullish/bearish/neutral
    news_impact: str  # HIGH/MEDIUM/LOW
    news_summary: Optional[str]
    news_count_24h: int

    # Market Context
    nifty_trend: str
    vix: float
    sector_performance: float

    # Metadata
    data_timestamp: datetime
    data_freshness_seconds: int
```

### Data Sources Mapping

| Data Field | Source | Method | Latency |
|------------|--------|--------|---------|
| `current_price` | Fyers API | `broker.get_ltp()` | Real-time |
| `pe_ratio`, `eps`, `market_cap` | yfinance | `Ticker.info` | ~1-2s |
| `rsi_14`, `atr_pct` | Calculated | From OHLCV | ~1s |
| `news_sentiment` | NewsAggregator | AI analysis | ~2-3s |
| `nifty_trend`, `vix` | yfinance | `^NSEI`, `^INDIAVIX` | ~1s |

---

## Backend Changes

### New Files to Create

#### 1. `backend/src/data_aggregator.py`

```python
"""
Data Aggregator Service
Fetches and combines all data sources for multi-strategy analysis.
"""

class DataAggregator:
    """
    Aggregates data from multiple sources for comprehensive stock analysis.

    Sources:
    - Broker API: Live prices
    - yfinance: Fundamentals, historical data
    - NewsAggregator: News and sentiment
    - Screener: Technical indicators
    """

    async def get_complete_stock_data(self, symbol: str) -> StockAnalysisData:
        """Fetch all data for a single stock."""
        pass

    async def get_batch_stock_data(self, symbols: List[str]) -> List[StockAnalysisData]:
        """Fetch data for multiple stocks in parallel."""
        pass

    def get_fundamental_data(self, symbol: str) -> FundamentalData:
        """Fetch fundamental data from yfinance."""
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        return FundamentalData(
            pe_ratio=info.get('trailingPE'),
            forward_pe=info.get('forwardPE'),
            eps=info.get('trailingEps'),
            market_cap=info.get('marketCap'),
            debt_to_equity=info.get('debtToEquity'),
            book_value=info.get('bookValue'),
            dividend_yield=info.get('dividendYield'),
            roe=info.get('returnOnEquity'),
            sector=info.get('sector'),
            industry=info.get('industry')
        )
```

#### 2. `backend/src/multi_strategy_analyzer.py`

```python
"""
Multi-Strategy Analyzer
Generates trade plans using three distinct analytical approaches.
"""

class MultiStrategyAnalyzer:
    """
    Analyzes stocks using three strategies:
    1. Fundamental Analysis
    2. News-Based Analysis
    3. Combined Analysis
    """

    async def analyze_stock(self, data: StockAnalysisData) -> MultiStrategyResult:
        """Generate all three strategy analyses for a stock."""

        fundamental_plan = await self._analyze_fundamental(data)
        news_plan = await self._analyze_news_based(data)
        combined_plan = await self._analyze_combined(data)

        recommendation = await self._generate_recommendation(
            fundamental_plan, news_plan, combined_plan
        )

        return MultiStrategyResult(
            symbol=data.symbol,
            fundamental=fundamental_plan,
            news_based=news_plan,
            combined=combined_plan,
            recommendation=recommendation
        )
```

### Files to Modify

#### 1. `backend/src/models/screener.py` - Add FundamentalData

```python
class FundamentalData(BaseModel):
    """Fundamental metrics for a stock."""
    pe_ratio: Optional[float] = Field(None, description="Trailing P/E ratio")
    forward_pe: Optional[float] = Field(None, description="Forward P/E ratio")
    eps: Optional[float] = Field(None, description="Earnings per share")
    market_cap_cr: float = Field(..., description="Market cap in Crores")
    debt_to_equity: Optional[float] = Field(None, description="D/E ratio")
    book_value: Optional[float] = Field(None, description="Book value per share")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield %")
    roe: Optional[float] = Field(None, description="Return on Equity %")
    sector: str = Field(default="Unknown", description="Sector classification")
    industry: str = Field(default="Unknown", description="Industry classification")
    week_52_high: Optional[float] = Field(None, description="52-week high")
    week_52_low: Optional[float] = Field(None, description="52-week low")
```

#### 2. `backend/src/screener.py` - Integrate NewsAggregator

Current `NewsContext` is placeholder. Need to:
- Inject `NewsAggregator` dependency
- Fetch real news for each screened stock
- Calculate sentiment score

#### 3. `backend/src/pipeline_orchestrator.py` - Add Multi-Strategy Stage

- Add `DataAggregator` and `MultiStrategyAnalyzer` as dependencies
- Modify pipeline flow to include data aggregation stage
- Store multi-strategy results instead of single trade plans

#### 4. `backend/src/main.py` - New API Endpoints

See [API Contract Changes](#api-contract-changes) section.

### Files to Deprecate/Remove

| File | Action | Reason |
|------|--------|--------|
| `strategy_engine.py` | Deprecate | Functionality merged into pipeline |
| `ai_trade_assistant.py` | Deprecate | Use `MultiStrategyAnalyzer` instead |
| `strategies/news_picker.py` | Keep | Used by news-based strategy |

---

## Frontend Changes

### Pages to Keep

| Page | Path | Changes |
|------|------|---------|
| **Pipeline** | `/pipeline` | Major enhancement (see below) |
| **Market News** | `/news` | No changes |
| **Trade View** | `/trade` | Minor - add link from Pipeline |
| **Dashboard** | `/` | No changes |
| **Settings** | `/settings` | No changes |

### Pages to Remove

| Page | Path | Reason |
|------|------|--------|
| **Strategy Manager** | `/strategies` | Strategies are now fixed |
| **Strategy Center** | `/strategy` | Redundant |
| **Screener** | `/screener` | Merged into Pipeline |

### Sidebar Navigation Update

```
Before:                          After:
├── Dashboard                    ├── Dashboard
├── Pipeline                     ├── Pipeline (Enhanced)
├── Strategies ❌                ├── Trade View
├── Trade View                   ├── Market News
├── Screener ❌                  ├── Trade Logs
├── Trade Logs                   ├── Risk Manager
├── Market News                  ├── Backtest
├── Strategy Center ❌           └── Settings
├── Risk Manager
├── Backtest
└── Settings
```

### Enhanced Pipeline Page UI

#### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TRADING PIPELINE                                           [Run Screening]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STAGE PROGRESS BAR                                                   │    │
│  │ [●] Screening → [○] Data Fetch → [○] AI Analysis → [○] Execution    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ MARKET CONTEXT                                                       │    │
│  │ NIFTY: 22,450 (+0.8%) ▲  │  VIX: 12.5  │  Breadth: Positive         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ SCREENED STOCKS (5 candidates)                    [Select All] [▼]  │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │ [☑] RELIANCE                                    Score: 87   │    │    │
│  │  │     ₹2,450.50 (+1.2%)  │  RVOL: 2.1x  │  RSI: 58           │    │    │
│  │  │     ──────────────────────────────────────────────────────  │    │    │
│  │  │                                                              │    │    │
│  │  │  📊 FUNDAMENTAL DATA                                         │    │    │
│  │  │  ┌────────────┬────────────┬────────────┬────────────┐      │    │    │
│  │  │  │ P/E: 24.5  │ EPS: ₹98   │ MCap: 18L  │ D/E: 0.45  │      │    │    │
│  │  │  │ Sector: Energy │ 52W: ₹2,100-2,600 │ ROE: 12%   │      │    │    │
│  │  │  └────────────┴────────────┴────────────┴────────────┘      │    │    │
│  │  │                                                              │    │    │
│  │  │  📰 NEWS CONTEXT                                             │    │    │
│  │  │  "Reliance announces Q3 results beat, refinery margins up"  │    │    │
│  │  │  Sentiment: BULLISH  │  Impact: HIGH  │  2 hours ago        │    │    │
│  │  │                                                              │    │    │
│  │  │  ──────────────────────────────────────────────────────     │    │    │
│  │  │                                                              │    │    │
│  │  │  🎯 STRATEGY ANALYSES                              [Expand ▼]│    │    │
│  │  │                                                              │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │    │    │
│  │  │  │ FUNDAMENTAL STRATEGY                    Confidence: 72%│    │    │
│  │  │  │ ─────────────────────────────────────────────────────│    │    │    │
│  │  │  │ Direction: BUY                                        │    │    │    │
│  │  │  │ Entry: ₹2,445  │  SL: ₹2,408 (-1.5%)  │  T1: ₹2,520   │    │    │    │
│  │  │  │ T2: ₹2,570  │  R:R = 1:2.0                            │    │    │    │
│  │  │  │                                                        │    │    │    │
│  │  │  │ Reasoning: P/E below sector avg (28), strong EPS      │    │    │    │
│  │  │  │ growth, low debt. Conservative entry near VWAP.       │    │    │    │
│  │  │  │                                                        │    │    │    │
│  │  │  │ Risk: Market volatility, crude price dependency       │    │    │    │
│  │  │  └─────────────────────────────────────────────────────┘    │    │    │
│  │  │                                                              │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │    │    │
│  │  │  │ NEWS-BASED STRATEGY                     Confidence: 85%│    │    │    │
│  │  │  │ ─────────────────────────────────────────────────────│    │    │    │
│  │  │  │ Direction: BUY                                        │    │    │    │
│  │  │  │ Entry: ₹2,455  │  SL: ₹2,406 (-2%)  │  T1: ₹2,577     │    │    │    │
│  │  │  │ T2: ₹2,650  │  R:R = 1:2.5                            │    │    │    │
│  │  │  │                                                        │    │    │    │
│  │  │  │ Reasoning: High-impact positive earnings news.        │    │    │    │
│  │  │  │ Momentum expected in next 2-3 hours. RVOL confirms.   │    │    │    │
│  │  │  │                                                        │    │    │    │
│  │  │  │ Risk: News already priced in, gap-up reversal         │    │    │    │
│  │  │  └─────────────────────────────────────────────────────┘    │    │    │
│  │  │                                                              │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │    │    │
│  │  │  │ COMBINED STRATEGY ⭐ RECOMMENDED        Confidence: 82%│    │    │    │
│  │  │  │ ─────────────────────────────────────────────────────│    │    │    │
│  │  │  │ Direction: BUY                                        │    │    │    │
│  │  │  │ Entry: ₹2,450  │  SL: ₹2,410 (-1.6%)  │  T1: ₹2,530   │    │    │    │
│  │  │  │ T2: ₹2,600  │  R:R = 1:2.0                            │    │    │    │
│  │  │  │                                                        │    │    │    │
│  │  │  │ Reasoning: Strong confluence - fundamentals support   │    │    │    │
│  │  │  │ valuation, news provides catalyst, technicals confirm │    │    │    │
│  │  │  │ uptrend. Best risk-adjusted entry.                    │    │    │    │
│  │  │  │                                                        │    │    │    │
│  │  │  │ Risk: Moderate - diversified analysis reduces risk    │    │    │    │
│  │  │  └─────────────────────────────────────────────────────┘    │    │    │
│  │  │                                                              │    │    │
│  │  │  ──────────────────────────────────────────────────────     │    │    │
│  │  │                                                              │    │    │
│  │  │  🤖 AI RECOMMENDATION                                        │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │    │    │
│  │  │  │ Best Strategy: COMBINED (82% confidence)              │    │    │    │
│  │  │  │                                                        │    │    │    │
│  │  │  │ "The Combined strategy offers the best risk-adjusted  │    │    │    │
│  │  │  │ return for RELIANCE. While News-Based has higher      │    │    │    │
│  │  │  │ confidence (85%), the Combined approach provides      │    │    │    │
│  │  │  │ tighter stop-loss with similar upside, reducing       │    │    │    │
│  │  │  │ drawdown risk. Fundamental support adds conviction."  │    │    │    │
│  │  │  └─────────────────────────────────────────────────────┘    │    │    │
│  │  │                                                              │    │    │
│  │  │  SELECT STRATEGY: [Fundamental ▼] [News-Based ▼] [Combined ●]│    │    │
│  │  │                                                              │    │    │
│  │  │  [View Chart →]                                              │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  ... (more stock cards)                                              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  Selected: 3 stocks  │  Total Capital: ₹1,50,000                    │    │
│  │                                                                      │    │
│  │  [Cancel]                                    [Approve & Execute →]   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Key UI Components

1. **Stock Card (Expandable)**
   - Header: Symbol, price, change, score, checkbox
   - Fundamental Data Grid: P/E, EPS, MCap, D/E, Sector, 52W range
   - News Context: Latest headline, sentiment badge, impact badge
   - Strategy Analyses: 3 collapsible sections with full details
   - AI Recommendation: Highlighted best strategy with reasoning
   - Strategy Selector: Radio buttons or dropdown to choose strategy
   - Trade View Link: Navigate to chart page

2. **Strategy Analysis Card**
   - Strategy name with confidence badge
   - Direction (BUY/SELL) with color coding
   - Levels: Entry, SL, T1, T2 with percentages
   - R:R ratio display
   - Reasoning text (2-3 sentences)
   - Risk assessment

3. **Execution Summary Bar**
   - Selected stock count
   - Total capital allocation
   - Cancel and Execute buttons

---

## API Contract Changes

### New Endpoints

#### 1. `POST /api/pipeline/analyze`

**Purpose:** Run multi-strategy analysis on screened stocks

**Request:**
```json
{
  "symbols": ["RELIANCE", "TCS", "INFY"],  // Optional, uses screener results if empty
  "force_refresh": false
}
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2024-01-15T10:30:00",
  "market_context": {
    "nifty_trend": "bullish",
    "nifty_change_pct": 0.8,
    "vix": 12.5,
    "market_breadth": "positive"
  },
  "analyses": [
    {
      "symbol": "RELIANCE",
      "name": "Reliance Industries Ltd",
      "current_price": 2450.50,
      "day_change_pct": 1.2,

      "fundamental_data": {
        "pe_ratio": 24.5,
        "forward_pe": 22.1,
        "eps": 98.5,
        "market_cap_cr": 1850000,
        "debt_to_equity": 0.45,
        "roe": 12.5,
        "sector": "Energy",
        "industry": "Oil & Gas Refining",
        "week_52_high": 2600,
        "week_52_low": 2100
      },

      "technical_data": {
        "rsi_14": 58,
        "atr_pct": 1.8,
        "rvol": 2.1,
        "vwap": 2445,
        "trend": "uptrend",
        "above_20ema": true,
        "above_50ema": true
      },

      "news_data": {
        "has_recent_news": true,
        "sentiment": "bullish",
        "impact": "HIGH",
        "headline": "Reliance announces Q3 results beat",
        "summary": "Refinery margins up 15% YoY...",
        "news_count_24h": 5,
        "hours_ago": 2
      },

      "strategies": {
        "fundamental": {
          "strategy_name": "Fundamental Analysis",
          "direction": "BUY",
          "confidence": 72,
          "entry": 2445,
          "stop_loss": 2408,
          "stop_loss_pct": -1.5,
          "target_1": 2520,
          "target_1_pct": 3.1,
          "target_2": 2570,
          "target_2_pct": 5.1,
          "risk_reward": 2.0,
          "reasoning": "P/E below sector average, strong EPS growth...",
          "risks": ["Market volatility", "Crude price dependency"],
          "timeframe": "2-5 days"
        },
        "news_based": {
          "strategy_name": "News-Based Analysis",
          "direction": "BUY",
          "confidence": 85,
          "entry": 2455,
          "stop_loss": 2406,
          "stop_loss_pct": -2.0,
          "target_1": 2577,
          "target_1_pct": 5.0,
          "target_2": 2650,
          "target_2_pct": 7.9,
          "risk_reward": 2.5,
          "reasoning": "High-impact positive earnings news...",
          "risks": ["News priced in", "Gap-up reversal"],
          "timeframe": "Intraday to 1 day"
        },
        "combined": {
          "strategy_name": "Combined Analysis",
          "direction": "BUY",
          "confidence": 82,
          "entry": 2450,
          "stop_loss": 2410,
          "stop_loss_pct": -1.6,
          "target_1": 2530,
          "target_1_pct": 3.3,
          "target_2": 2600,
          "target_2_pct": 6.1,
          "risk_reward": 2.0,
          "reasoning": "Strong confluence across all factors...",
          "risks": ["Moderate overall risk"],
          "timeframe": "1-3 days"
        }
      },

      "recommendation": {
        "best_strategy": "combined",
        "reasoning": "The Combined strategy offers the best risk-adjusted return..."
      },

      "screener_score": 87
    }
  ],
  "analysis_duration_ms": 3500
}
```

#### 2. `POST /api/pipeline/execute-multi`

**Purpose:** Execute trades with selected strategies per stock

**Request:**
```json
{
  "trades": [
    {
      "symbol": "RELIANCE",
      "strategy": "combined",
      "quantity": 10
    },
    {
      "symbol": "TCS",
      "strategy": "news_based",
      "quantity": 5
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "executed": [
    {
      "symbol": "RELIANCE",
      "order_id": "ORD123456",
      "status": "COMPLETE",
      "filled_price": 2451.50,
      "quantity": 10
    }
  ],
  "failed": [],
  "total_capital_used": 75000
}
```

#### 3. `GET /api/strategies/preset`

**Purpose:** Get the 3 fixed strategies for display

**Response:**
```json
{
  "strategies": [
    {
      "id": "fundamental",
      "name": "Fundamental Analysis",
      "description": "Value-based decisions using P/E, EPS, market cap",
      "risk_profile": "Conservative",
      "typical_sl_pct": 1.5,
      "typical_target_pct": 3.5,
      "best_for": "Swing trades, lower volatility"
    },
    {
      "id": "news_based",
      "name": "News-Based Analysis",
      "description": "Event-driven trading based on news sentiment",
      "risk_profile": "Moderate-Aggressive",
      "typical_sl_pct": 2.0,
      "typical_target_pct": 5.0,
      "best_for": "Momentum trades, quick moves"
    },
    {
      "id": "combined",
      "name": "Combined Analysis",
      "description": "Holistic view combining all factors",
      "risk_profile": "Adaptive",
      "typical_sl_pct": 1.8,
      "typical_target_pct": 4.5,
      "best_for": "Balanced, high-confidence trades"
    }
  ]
}
```

### Deprecated Endpoints

| Endpoint | Replacement |
|----------|-------------|
| `POST /api/strategies/create-from-description` | Remove |
| `POST /api/strategies/{id}/refine` | Remove |
| `POST /api/strategies/{id}/toggle` | Remove |
| `POST /api/strategies/{id}/run` | Use `/api/pipeline/analyze` |

---

## Implementation Phases

### Phase 1: Data Layer (3-4 days)

**Goal:** Establish complete data fetching infrastructure

| Task | File | Priority |
|------|------|----------|
| Create `FundamentalData` model | `models/screener.py` | P0 |
| Create `DataAggregator` service | `data_aggregator.py` (new) | P0 |
| Add `yfinance.info` fetching | `data_aggregator.py` | P0 |
| Integrate `NewsAggregator` into screener | `screener.py` | P0 |
| Add caching for fundamental data | `data_aggregator.py` | P1 |
| Add data freshness validation | `data_aggregator.py` | P1 |

**Deliverables:**
- [ ] `DataAggregator` class with `get_complete_stock_data()`
- [ ] `FundamentalData` model with all fields
- [ ] Unit tests for data fetching

### Phase 2: Multi-Strategy Analysis (4-5 days)

**Goal:** Implement three-strategy AI analysis

| Task | File | Priority |
|------|------|----------|
| Create `MultiStrategyAnalyzer` | `multi_strategy_analyzer.py` (new) | P0 |
| Create `StrategyAnalysisResult` model | `models/trade_plan.py` | P0 |
| Implement Fundamental strategy prompt | `multi_strategy_analyzer.py` | P0 |
| Implement News-Based strategy prompt | `multi_strategy_analyzer.py` | P0 |
| Implement Combined strategy prompt | `multi_strategy_analyzer.py` | P0 |
| Implement recommendation generator | `multi_strategy_analyzer.py` | P0 |
| Add parallel AI calls for efficiency | `multi_strategy_analyzer.py` | P1 |

**Deliverables:**
- [ ] `MultiStrategyAnalyzer` with 3 strategy methods
- [ ] AI prompts for each strategy
- [ ] Recommendation comparison logic
- [ ] Unit tests for analysis

### Phase 3: Pipeline Integration (2-3 days)

**Goal:** Wire everything into the pipeline

| Task | File | Priority |
|------|------|----------|
| Add `DataAggregator` to pipeline | `pipeline_orchestrator.py` | P0 |
| Add `MultiStrategyAnalyzer` to pipeline | `pipeline_orchestrator.py` | P0 |
| Create new API endpoints | `main.py` | P0 |
| Update WebSocket events | `main.py` | P1 |
| Deprecate old strategy endpoints | `main.py` | P2 |

**Deliverables:**
- [ ] Updated `PipelineOrchestrator` with new stages
- [ ] New API endpoints working
- [ ] WebSocket events for progress

### Phase 4: Frontend Enhancement (4-5 days)

**Goal:** Build the enhanced Pipeline UI

| Task | File | Priority |
|------|------|----------|
| Remove Strategy Manager page | `App.tsx`, `Sidebar.tsx` | P0 |
| Remove Screener page | `App.tsx`, `Sidebar.tsx` | P0 |
| Create `StockAnalysisCard` component | `components/` (new) | P0 |
| Create `StrategyAnalysisPanel` component | `components/` (new) | P0 |
| Create `FundamentalDataGrid` component | `components/` (new) | P0 |
| Update Pipeline page layout | `pages/Pipeline.tsx` | P0 |
| Add strategy selector per stock | `pages/Pipeline.tsx` | P0 |
| Add Trade View navigation | `pages/Pipeline.tsx` | P1 |
| Update API service | `lib/trading-api.ts` | P0 |

**Deliverables:**
- [ ] Enhanced Pipeline page with multi-strategy UI
- [ ] Removed deprecated pages
- [ ] Updated navigation

### Phase 5: Testing & Polish (2-3 days)

**Goal:** Ensure everything works end-to-end

| Task | Priority |
|------|----------|
| End-to-end pipeline test | P0 |
| UI/UX review and fixes | P0 |
| Performance optimization | P1 |
| Error handling improvements | P1 |
| Documentation update | P2 |

**Deliverables:**
- [ ] All tests passing
- [ ] Smooth user experience
- [ ] Updated documentation

---

## Success Criteria

### Functional Requirements

- [ ] Only 3 fixed strategies exist (Fundamental, News-Based, Combined)
- [ ] Strategy Manager UI is removed
- [ ] Pipeline shows multi-strategy analysis for each screened stock
- [ ] All data is fetched from live sources (no mock data in production)
- [ ] Fundamental data (P/E, EPS, MCap, D/E) displayed prominently
- [ ] News context displayed with sentiment and impact
- [ ] AI analysis includes Entry, SL, T1, T2, R:R, Confidence, Reasoning
- [ ] User can select different strategies for different stocks
- [ ] AI recommendation explains best strategy choice
- [ ] Trade View links work for each stock
- [ ] Execution works with selected strategies

### Non-Functional Requirements

- [ ] Data aggregation completes in < 5 seconds for 5 stocks
- [ ] AI analysis completes in < 10 seconds for 5 stocks (parallel)
- [ ] UI is responsive and doesn't freeze during loading
- [ ] Error states are handled gracefully
- [ ] Loading states provide feedback to user

### Data Quality Requirements

- [ ] All prices are real-time (< 5 second delay)
- [ ] Fundamental data is from yfinance (not hardcoded)
- [ ] News is from last 24 hours
- [ ] Technical indicators calculated from live OHLCV
- [ ] Data timestamps are visible to user

---

## Appendix: File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `backend/src/data_aggregator.py` | Aggregate data from all sources |
| `backend/src/multi_strategy_analyzer.py` | 3-strategy AI analysis |
| `frontend/src/components/StockAnalysisCard.tsx` | Stock card with all data |
| `frontend/src/components/StrategyAnalysisPanel.tsx` | Strategy details panel |
| `frontend/src/components/FundamentalDataGrid.tsx` | Fundamental metrics grid |

### Modified Files

| File | Changes |
|------|---------|
| `backend/src/models/screener.py` | Add `FundamentalData` model |
| `backend/src/models/trade_plan.py` | Add `MultiStrategyResult` model |
| `backend/src/screener.py` | Integrate news, add fundamental fetch |
| `backend/src/pipeline_orchestrator.py` | Add new stages |
| `backend/src/main.py` | New endpoints, deprecate old ones |
| `frontend/src/App.tsx` | Remove routes |
| `frontend/src/components/Sidebar.tsx` | Update navigation |
| `frontend/src/pages/Pipeline.tsx` | Major UI enhancement |
| `frontend/src/lib/trading-api.ts` | New API methods |

### Deprecated Files

| File | Action |
|------|--------|
| `frontend/src/pages/StrategyManager.tsx` | Delete |
| `frontend/src/pages/StrategyCenter.tsx` | Delete |
| `frontend/src/pages/Screener.tsx` | Delete |
| `backend/src/strategy_engine.py` | Mark deprecated |
| `backend/src/ai_trade_assistant.py` | Mark deprecated |

---

## Appendix: AI Prompt Templates

### Fundamental Strategy Prompt

```
You are a fundamental analyst evaluating {symbol} for a potential trade.

FUNDAMENTAL DATA:
- P/E Ratio: {pe_ratio} (Sector Avg: {sector_pe})
- EPS: ₹{eps}
- Market Cap: ₹{market_cap_cr} Cr
- Debt-to-Equity: {debt_to_equity}
- ROE: {roe}%
- 52-Week Range: ₹{week_52_low} - ₹{week_52_high}
- Current Price: ₹{current_price}

TECHNICAL CONTEXT:
- RSI: {rsi}
- Trend: {trend}
- VWAP: ₹{vwap}

Generate a trade plan focusing on fundamental value. Be conservative with stop-loss (1-2%).
Consider if the stock is undervalued/overvalued relative to sector.

Output JSON:
{
  "direction": "BUY" or "SELL",
  "confidence": 0-100,
  "entry": price,
  "stop_loss": price,
  "target_1": price,
  "target_2": price,
  "reasoning": "2-3 sentences",
  "risks": ["risk1", "risk2"],
  "timeframe": "expected holding period"
}
```

### News-Based Strategy Prompt

```
You are a news-driven trader evaluating {symbol} based on recent news.

NEWS DATA:
- Headline: {headline}
- Summary: {summary}
- Sentiment: {sentiment}
- Impact: {impact}
- Published: {hours_ago} hours ago
- News Count (24h): {news_count}

PRICE ACTION:
- Current Price: ₹{current_price}
- Day Change: {day_change_pct}%
- RVOL: {rvol}x

Generate a trade plan based on news momentum. Consider if news is already priced in.
Be aggressive with targets (4-8%) but use appropriate stop-loss (2-3%).

Output JSON:
{
  "direction": "BUY" or "SELL",
  "confidence": 0-100,
  "entry": price,
  "stop_loss": price,
  "target_1": price,
  "target_2": price,
  "reasoning": "2-3 sentences",
  "risks": ["risk1", "risk2"],
  "timeframe": "expected holding period"
}
```

### Combined Strategy Prompt

```
You are a senior trader evaluating {symbol} using all available data.

FUNDAMENTAL DATA:
{fundamental_summary}

TECHNICAL DATA:
{technical_summary}

NEWS DATA:
{news_summary}

MARKET CONTEXT:
- NIFTY Trend: {nifty_trend}
- VIX: {vix}
- Sector Performance: {sector_perf}%

Generate a balanced trade plan considering all factors. Weight them appropriately.
Aim for best risk-adjusted return with moderate stop-loss (1.5-2.5%).

Output JSON:
{
  "direction": "BUY" or "SELL",
  "confidence": 0-100,
  "entry": price,
  "stop_loss": price,
  "target_1": price,
  "target_2": price,
  "reasoning": "2-3 sentences explaining confluence",
  "risks": ["risk1", "risk2"],
  "timeframe": "expected holding period"
}
```

---

*Document Version: 1.0*
*Created: 2024-01-28*
*Author: Trading Bot Development Team*


