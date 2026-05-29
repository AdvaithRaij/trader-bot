# Trading Bot - Plan of Action

> **Objective**: Build an AI-powered intraday trading system for Indian equities (NSE) that generates high-probability trades with strict risk management.

---

## Table of Contents
1. [Current State](#current-state)
2. [Target Architecture](#target-architecture)
3. [Phase 1: Stock Screener](#phase-1-stock-screener)
4. [Phase 2: AI Insight Provider](#phase-2-ai-insight-provider)
5. [Phase 3: Trade Executor](#phase-3-trade-executor)
6. [Implementation Prompts](#implementation-prompts)
7. [Risk Management Rules](#risk-management-rules)
8. [Implementation Checklist](#implementation-checklist)

---

## Current State

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Screener | `screener.py` | ⚠️ Basic | Needs enhanced filtering |
| AI Decision Engine | `ai_decision_engine.py` | ⚠️ Partial | Needs structured prompts |
| Execution Engine | `execution_engine.py` | ⚠️ Partial | Needs risk validation |
| News Aggregator | `news_aggregator.py` | ✅ Working | Multi-source + Groq analysis |
| Risk Manager | `risk_manager.py` | ⚠️ Basic | Needs position sizing |
| Portfolio Manager | `portfolio_manager.py` | ✅ Working | MongoDB persistence |

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRADING PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   STAGE 1    │    │   STAGE 2    │    │   STAGE 3    │                   │
│  │   SCREENER   │───▶│  AI INSIGHT  │───▶│   EXECUTOR   │                   │
│  │              │    │   PROVIDER   │    │              │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ Top 10 Stocks│    │ Trade Plans  │    │ Live Orders  │                   │
│  │ with Scores  │    │ Entry/SL/TGT │    │ via Fyers    │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. **Screener** → Scans 200+ stocks → Outputs 10 high-potential candidates
2. **AI Insight** → Analyzes each candidate → Outputs detailed trade plans with levels
3. **Executor** → Validates against risk rules → Places orders via Fyers API

---

## Phase 1: Stock Screener

### Objective
Scan NSE stocks and filter to top 10 candidates with highest intraday potential.

### Screening Criteria

| Criteria | Threshold | Rationale |
|----------|-----------|-----------|
| **Liquidity** | Turnover ≥ ₹10 Cr/day | Ensures easy entry/exit |
| **Relative Volume** | RVOL ≥ 1.5x (vs 10-day avg) | High participation today |
| **Volatility** | ATR% 1.5-5% | Good movement, not crazy |
| **Market Cap** | ≥ ₹5,000 Cr | Avoid penny/operator stocks |
| **RSI** | 30-70 | Not overbought/oversold |
| **Trend** | Price vs 20/50 EMA | Clear direction |
| **Gap** | Gap% < 3% | Avoid gap-and-fade traps |

### Data Sources
- **Price Data**: Fyers API (real-time) + yfinance (historical)
- **Volume**: Fyers quotes endpoint
- **News**: MoneyControl, Economic Times, Yahoo Finance
- **Technicals**: Calculated from OHLCV data

### Output Schema (JSON)
```json
{
  "timestamp": "2024-01-15T09:30:00",
  "market_context": {
    "nifty_trend": "bullish",
    "nifty_change_pct": 0.45,
    "market_breadth": "positive",
    "vix": 12.5
  },
  "candidates": [
    {
      "symbol": "RELIANCE",
      "name": "Reliance Industries Ltd",
      "segment": "NSE_EQ",
      "market_cap_cr": 1850000,
      "liquidity": {
        "today_turnover_cr": 1250,
        "avg_10d_turnover_cr": 980,
        "rvol": 1.85,
        "today_volume": 12500000,
        "avg_10d_volume": 8500000
      },
      "price_action": {
        "last_price": 2450.50,
        "prev_close": 2425.00,
        "today_open": 2430.00,
        "today_high": 2465.00,
        "today_low": 2420.00,
        "today_pct_change": 1.05,
        "gap_pct": 0.21,
        "vwap": 2442.30,
        "vwap_distance_pct": 0.34
      },
      "technicals": {
        "rsi": 58,
        "above_20ema": true,
        "above_50ema": true,
        "atr": 42.50,
        "atr_pct": 1.74,
        "trend_label": "uptrend",
        "near_day_high": true,
        "near_day_low": false
      },
      "levels": {
        "prev_high": 2460.00,
        "prev_low": 2410.00,
        "pivot_pp": 2431.67,
        "s1": 2403.33,
        "s2": 2380.00,
        "r1": 2455.00,
        "r2": 2483.33
      },
      "news": {
        "has_fresh_news": true,
        "sentiment": "bullish",
        "category": "earnings",
        "summary": "Q3 results beat estimates by 12%",
        "is_event_today": false
      },
      "score": 85
    }
  ]
}
```

---

## Phase 2: AI Insight Provider

### Objective
Convert screened stocks into detailed trade plans with entry, stop-loss, and targets.

### Analysis Components
1. **Support/Resistance** - Using pivots, prev high/low, swing levels
2. **Entry Logic** - Near support for longs, near resistance for shorts
3. **Stop-Loss** - Beyond logical level, adjusted by ATR
4. **Targets** - T1 (1:1.5 R:R), T2 (1:2 R:R), T3 (1:3 R:R)
5. **Confidence** - Based on alignment with trend, news, liquidity
6. **Validity** - Time-bound (intraday only)

### Output Schema (JSON)
```json
{
  "analysis": [
    {
      "symbol": "RELIANCE",
      "side": "long",
      "market_condition": "trending",
      "entry_price": 2448.00,
      "support_levels": [2431.67, 2420.00, 2403.33],
      "resistance_levels": [2455.00, 2465.00, 2483.33],
      "stop_loss": 2420.00,
      "targets": [
        {"label": "T1", "price": 2470.00, "risk_reward": 1.57},
        {"label": "T2", "price": 2490.00, "risk_reward": 2.14},
        {"label": "T3", "price": 2510.00, "risk_reward": 2.71}
      ],
      "confidence_score": 78,
      "news_impact": "Supportive - positive earnings surprise driving momentum",
      "trade_validity": "Valid until 3:15 PM or if price breaks below 2420",
      "reasoning": [
        "Strong uptrend with price above both 20 and 50 EMA",
        "RVOL at 1.85x indicates high institutional participation",
        "Trading above VWAP with bullish momentum",
        "Positive earnings news providing catalyst",
        "Clear invalidation level at yesterday's low"
      ]
    }
  ]
}
```

---

## Phase 3: Trade Executor

### Objective
Validate trade plans against risk rules and execute via Fyers API.

### Validation Rules

| Rule | Threshold | Action if Breached |
|------|-----------|-------------------|
| **Confidence** | ≥ 75% | Reject trade |
| **Risk:Reward** | ≥ 1:1.5 to T1 | Reject trade |
| **Max Risk/Trade** | 1.5% of capital | Reduce position size |
| **Max Open Risk** | 5% of capital | Block new trades |
| **Max Daily Loss** | 3% of capital | Stop trading for day |
| **Max Trades/Day** | 10 | Block new trades |
| **Liquidity** | Turnover ≥ ₹10 Cr | Reject trade |

### Position Sizing Formula
```
max_money_risk = equity × max_risk_per_trade_pct / 100
risk_per_share = |entry_price - stop_loss|
quantity = floor(max_money_risk / risk_per_share)
```

### Order Placement
1. **Entry**: LIMIT order at planned price (or MARKET if urgent)
2. **Stop-Loss**: SL-M order at stop_loss price
3. **Target**: LIMIT order at T1/T2 price
4. **Validity**: Intraday only (DAY)

---

## Implementation Prompts

### PROMPT 1: Enhance Stock Screener

```
I need you to enhance the stock screener in `backend/src/screener.py` to implement the following:

**Current State:**
- Basic screening using yfinance data
- Simple volume and RSI filters

**Required Enhancements:**

1. **Expand Universe:**
   - Add full NIFTY 200 stock list
   - Include F&O segment stocks
   - Store in config file for easy updates

2. **Add New Filters:**
   - Relative Volume (RVOL): today_volume / avg_10d_volume >= 1.5
   - Turnover filter: today_turnover_cr >= 10
   - ATR% filter: 1.5% <= atr_pct <= 5%
   - Market cap filter: >= 5000 Cr
   - Gap filter: |gap_pct| <= 3%
   - Spread filter: bid_ask_spread_pct <= 0.1%

3. **Calculate Additional Metrics:**
   - VWAP and distance from VWAP
   - Pivot points (PP, S1, S2, R1, R2)
   - Trend label based on EMA alignment
   - Correlation with NIFTY (optional)

4. **Improve Scoring:**
   - Weight factors: liquidity (30%), volatility (25%), trend (25%), news (20%)
   - Normalize all scores to 0-100 range
   - Rank and return top 10

5. **Output Format:**
   - Return structured JSON matching the schema in PLAN_OF_ACTION.md
   - Include market_context with NIFTY trend and VIX
   - Include full candidate objects with all metrics

6. **Performance:**
   - Use async/await for parallel data fetching
   - Cache data to reduce API calls
   - Add rate limiting for Fyers API

**Files to Modify:**
- `backend/src/screener.py` - Main screening logic
- `backend/src/config.py` - Add new config parameters
- `backend/src/models.py` - Add Pydantic models for output schema

**Testing:**
- Add unit tests for each filter
- Test with mock data for edge cases
- Verify output matches expected schema
```

---

### PROMPT 2: Build AI Insight Provider

```
I need you to enhance the AI decision engine in `backend/src/ai_decision_engine.py` to implement a structured trade plan generator.

**Current State:**
- Basic LLM integration with Gemini/OpenAI
- Simple prompt for trading decisions

**Required Enhancements:**

1. **Create New Method: `generate_trade_plans()`**
   - Input: Screener output (candidates array)
   - Output: Detailed trade plans for each candidate

2. **Use Structured System Prompt:**
   ```
   You are an intraday trading analyst for Indian equities. Your job is to convert
   structured market data into concrete trade plans with precise levels.

   For each stock, analyze:
   - Support/resistance using pivot points, prev high/low, VWAP
   - Entry logic based on price action and trend
   - Stop-loss using logical invalidation + ATR buffer
   - Targets at 1:1.5, 1:2, 1:3 risk-reward ratios
   - Confidence based on alignment of technicals, news, and market

   Rules:
   - Use ONLY the data provided, do not invent prices
   - Minimum R:R of 1:1.5 for any trade
   - Lower confidence if news contradicts price action
   - Mark as "no_trade" if setup is unclear or liquidity is poor
   ```

3. **Implement Structured Output:**
   - Use JSON mode or function calling
   - Validate output against Pydantic schema
   - Handle parsing errors gracefully

4. **Add Calculation Helpers:**
   - `calculate_risk_reward(entry, stop_loss, target)`
   - `determine_market_condition(trend_label, atr_pct, rsi)`
   - `validate_trade_levels(entry, sl, targets)`

5. **Error Handling:**
   - Retry on LLM failures (max 3 attempts)
   - Fallback to rule-based analysis if LLM unavailable
   - Log all decisions for debugging

**Files to Modify:**
- `backend/src/ai_decision_engine.py` - Main logic
- `backend/src/prompts/trade_plan.md` - Create new prompt template
- `backend/src/models.py` - Add TradePlan model

**Testing:**
- Test with sample screener output
- Verify all required fields are present
- Check R:R calculations are correct
```

---

### PROMPT 3: Build Trade Executor with Risk Validation

```
I need you to enhance the execution engine in `backend/src/execution_engine.py` to implement strict risk validation before order placement.

**Current State:**
- Basic order placement via Fyers
- Simple position tracking

**Required Enhancements:**

1. **Add Risk Validation Method: `validate_trade(trade_plan, account_state)`**
   
   Checks to implement:
   - confidence_score >= 75
   - risk_reward to T1 >= 1.5
   - max_risk_per_trade: position_risk <= 1.5% of equity
   - max_total_open_risk: all open risk <= 5% of equity
   - max_daily_loss: realized_pnl_today >= -3% of equity
   - max_trades_per_day: trade_count_today <= 10
   - liquidity_check: turnover >= 10 Cr

2. **Position Sizing Method: `calculate_position_size(entry, stop_loss, equity)`**
   ```python
   max_money_risk = equity * 0.015  # 1.5% risk per trade
   risk_per_share = abs(entry - stop_loss)
   quantity = floor(max_money_risk / risk_per_share)
   # Round to lot size if required
   return quantity
   ```

3. **Order Placement Method: `execute_trade(trade_plan, quantity)`**
   - Place entry order (LIMIT or MARKET)
   - Place SL-M order immediately after fill
   - Place target order(s)
   - Update portfolio state
   - Log to MongoDB
   - Send Telegram notification

4. **Pre-Execution Checks:**
   - Verify current price is within 0.5% of planned entry
   - Check stock is not in circuit/freeze/auction
   - Verify sufficient margin available
   - Check market hours (9:15 AM - 3:15 PM)

5. **Create Risk Summary:**
   ```json
   {
     "equity": 100000,
     "realized_pnl_today": -500,
     "open_risk_amount": 2500,
     "projected_risk_after_trade": 4000,
     "trading_allowed": true,
     "rejection_reason": null
   }
   ```

**Files to Modify:**
- `backend/src/execution_engine.py` - Main logic
- `backend/src/risk_manager.py` - Risk calculations
- `backend/src/broker.py` - Order placement helpers

**Testing:**
- Test risk rejection scenarios
- Test position sizing with various SL distances
- Test order placement in paper mode first
```

---

### PROMPT 4: Integrate Full Pipeline

```
I need you to integrate all three stages (Screener → AI Insight → Executor) into a cohesive trading pipeline in `backend/src/strategy_engine.py`.

**Pipeline Flow:**

1. **Every 10 Minutes (9:15 AM - 2:30 PM):**
   ```
   run_screening_cycle()
   ├── screener.screen_top_stocks()
   ├── news_aggregator.get_relevant_news(symbols)
   ├── ai_engine.generate_trade_plans(candidates)
   ├── For each plan where side != "no_trade":
   │   ├── executor.validate_trade(plan)
   │   ├── If valid: executor.execute_trade(plan)
   │   └── Log result (executed/rejected/failed)
   └── Update dashboard via WebSocket
   ```

2. **Every 1 Minute:**
   ```
   run_monitoring_cycle()
   ├── Update all position P&Ls
   ├── Check for SL/Target hits
   ├── Check for manual exit signals
   └── Send WebSocket updates
   ```

3. **At 3:15 PM:**
   ```
   run_eod_cycle()
   ├── Square off all open positions
   ├── Generate daily report
   ├── Send Telegram summary
   └── Reset daily counters
   ```

**State Management:**
- Track all trades in MongoDB
- Maintain in-memory cache for performance
- Sync state on restart

**API Endpoints to Add:**
- `POST /api/pipeline/start` - Start automated pipeline
- `POST /api/pipeline/stop` - Stop pipeline
- `GET /api/pipeline/status` - Get current state
- `POST /api/trade/manual` - Execute manual trade

**WebSocket Events:**
- `pipeline_status` - Pipeline start/stop
- `new_candidates` - Screener results
- `new_trade_plan` - AI analysis complete
- `trade_executed` - Order placed
- `position_update` - P&L update

**Files to Modify:**
- `backend/src/strategy_engine.py` - Pipeline orchestration
- `backend/src/main.py` - Add new endpoints
- `frontend/src/lib/api.ts` - Add WebSocket handlers

**Testing:**
- Run in paper trading mode first
- Simulate full day with historical data
- Test all failure scenarios
```

---

### PROMPT 5: Add Dashboard Enhancements

```
I need you to enhance the frontend dashboard to display the full trading pipeline status.

**New Components Needed:**

1. **Pipeline Control Panel:**
   - Start/Stop buttons
   - Status indicator (Running/Stopped/Error)
   - Next cycle countdown
   - Today's stats (trades, P&L, win rate)

2. **Screener Results Table:**
   - Show top 10 candidates
   - Columns: Symbol, Price, Change%, RVOL, Score, News Sentiment
   - Click to view detailed analysis

3. **Trade Plans View:**
   - Show AI-generated plans
   - Entry/SL/Target levels with chart visualization
   - Confidence meter
   - Approve/Reject buttons for semi-auto mode

4. **Live Positions Panel:**
   - Show all open positions
   - Real-time P&L with color coding
   - Progress bar to SL/Target
   - Manual exit button

5. **Risk Dashboard:**
   - Capital utilization gauge
   - Daily P&L chart
   - Open risk meter
   - Trading status (Allowed/Blocked)

**Files to Modify:**
- `frontend/src/pages/Dashboard.tsx` - Main layout
- `frontend/src/components/PipelineControl.tsx` - New component
- `frontend/src/components/ScreenerResults.tsx` - New component
- `frontend/src/components/TradePlans.tsx` - New component
- `frontend/src/components/RiskDashboard.tsx` - New component
- `frontend/src/lib/api.ts` - WebSocket handlers

**Styling:**
- Use existing Tailwind/shadcn components
- Match current dark theme
- Mobile responsive
```

---

## Risk Management Rules

### Position-Level Rules
| Rule | Value | Description |
|------|-------|-------------|
| Max Risk Per Trade | 1.5% | Maximum capital at risk per trade |
| Stop-Loss Distance | 0.5-2% ATR | Based on volatility |
| Min Risk:Reward | 1:1.5 | Minimum R:R to T1 |
| Position Size Cap | 20% | Max capital per position |

### Portfolio-Level Rules
| Rule | Value | Description |
|------|-------|-------------|
| Max Open Risk | 5% | Total risk across all positions |
| Max Positions | 5 | Concurrent open positions |
| Max Daily Loss | 3% | Stop trading if breached |
| Max Daily Trades | 10 | Prevent overtrading |

### Session Rules
| Rule | Value | Description |
|------|-------|-------------|
| Trading Hours | 9:15 AM - 3:15 PM | No trades outside window |
| Last Entry | 2:30 PM | No new positions after |
| EOD Square Off | 3:15 PM | Close all positions |
| Circuit Stocks | Avoid | No trades in circuit/frozen stocks |

---

## Implementation Checklist

### Phase 1: Screener Enhancement ⬜
- [ ] Add NIFTY 200 stock list
- [ ] Implement RVOL filter
- [ ] Implement turnover filter
- [ ] Calculate pivot points
- [ ] Calculate VWAP distance
- [ ] Add market context (NIFTY trend, VIX)
- [ ] Improve scoring algorithm
- [ ] Add unit tests
- [ ] Test with live data

### Phase 2: AI Insight Provider ⬜
- [ ] Create trade plan prompt template
- [ ] Implement structured JSON output
- [ ] Add R:R calculation helpers
- [ ] Add confidence scoring logic
- [ ] Implement retry logic
- [ ] Add fallback analysis
- [ ] Test with sample data
- [ ] Validate output schema

### Phase 3: Trade Executor ⬜
- [ ] Implement risk validation
- [ ] Implement position sizing
- [ ] Add pre-execution checks
- [ ] Implement order placement
- [ ] Add SL/Target order logic
- [ ] Integrate with Telegram
- [ ] Test in paper mode
- [ ] Test risk rejection scenarios

### Phase 4: Pipeline Integration ⬜
- [ ] Build main orchestrator
- [ ] Add 10-min screening cycle
- [ ] Add 1-min monitoring cycle
- [ ] Add EOD cycle
- [ ] Add API endpoints
- [ ] Add WebSocket events
- [ ] Test full flow
- [ ] Run paper trading for 1 week

### Phase 5: Dashboard ⬜
- [ ] Build pipeline control panel
- [ ] Build screener results table
- [ ] Build trade plans view
- [ ] Build positions panel
- [ ] Build risk dashboard
- [ ] Add WebSocket handlers
- [ ] Test responsiveness
- [ ] User testing

---

## LLM Provider Recommendations

| Provider | Use Case | Cost | Latency | Notes |
|----------|----------|------|---------|-------|
| **Groq** | News analysis, batch sentiment | Low | Very Fast | Best for high-volume analysis |
| **Gemini 2.5 Flash** | Trade plan generation | Low | Fast | Good balance of cost/quality |
| **Claude 3.5 Sonnet** | Complex market analysis | Medium | Medium | Best reasoning quality |
| **GPT-4o** | Fallback/verification | High | Medium | Most reliable for finance |

**Recommended Setup:**
- Primary: Gemini 2.5 Flash for trade plans
- Batch Analysis: Groq for news sentiment
- Fallback: Claude/GPT-4o for critical decisions

---

## Quick Start Commands

```bash
# Start backend
cd backend/src && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Start frontend  
cd frontend && npm run dev

# Run screener test
cd backend/src && python -c "from screener import StockScreener; import asyncio; asyncio.run(StockScreener().screen_top_stocks())"

# Run pipeline test (paper mode)
cd backend/src && python -c "from strategy_engine import StrategyEngine; import asyncio; asyncio.run(StrategyEngine().run_test_cycle())"
```

---

*Last Updated: December 2024*
