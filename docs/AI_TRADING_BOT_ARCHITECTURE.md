# AI Trading Bot - Complete Architecture

## Vision
Transform from news screener → **Autonomous AI Trading Bot** with:
- Multiple configurable strategies (stock picking + trade execution)
- Real-time trade execution with AI-assisted levels
- Portfolio management with ₹100,000 capital
- TradingView chart integration with trade levels
- Trade history tracking & performance analytics
- Backtesting framework for strategy validation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
├─────────────────────────────────────────────────────────────────┤
│  Dashboard  │  Strategies  │  Active Trades  │  History  │  BT  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      STRATEGY ENGINE                             │
├─────────────────────────────────────────────────────────────────┤
│  Stock Picking Strategies    │    Trade Execution Strategies    │
│  - News-based (AI)           │    - Breakout                    │
│  - Technical indicators      │    - Mean reversion              │
│  - Momentum                  │    - Scalping                    │
│  - AI recommendations        │    - AI-assisted levels          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PORTFOLIO MANAGER                              │
├─────────────────────────────────────────────────────────────────┤
│  Capital: ₹100,000  │  Position Sizing  │  Risk Management     │
│  Max positions: 5   │  Per trade: 20%   │  Stop loss: Auto     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION ENGINE                              │
├─────────────────────────────────────────────────────────────────┤
│  Order Management  │  Real-time Monitoring  │  Auto SL/TP       │
│  - Market orders   │  - Price tracking      │  - Trailing SL    │
│  - Limit orders    │  - Position updates    │  - Target exits   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│  News Feed  │  Market Data  │  Broker API  │  Historical Data   │
│  (Current)  │  (Fyers)      │  (Fyers)     │  (For backtesting) │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components to Build

### 1. **Strategy Management System**

**File:** `backend/src/strategy_engine.py`

**Features:**
- Define multiple strategies (JSON/Python configs)
- Stock picking strategies:
  - News-based (HIGH impact + POSITIVE sentiment → BUY signal)
  - Technical (RSI, MACD, Moving averages)
  - Momentum (Volume + Price action)
  - AI recommendations (Gemini analyzes and suggests)
- Trade execution strategies:
  - Entry/exit rules
  - Position sizing
  - Stop loss/take profit logic
- Strategy backtesting on historical data

**Example Strategy Config:**
```json
{
  "id": "news_momentum_v1",
  "name": "News-Driven Momentum",
  "stockPicking": {
    "type": "news_based",
    "filters": {
      "impact": "HIGH",
      "sentiment": "POSITIVE",
      "relevance": ">= 80"
    },
    "maxStocks": 5
  },
  "execution": {
    "type": "breakout",
    "entryCondition": "price > resistance",
    "stopLoss": "2%",
    "takeProfit": "5%",
    "trailingStop": true
  },
  "riskManagement": {
    "maxPositionSize": "20%",
    "maxDailyLoss": "5%"
  }
}
```

---

### 2. **Portfolio Manager**

**File:** `backend/src/portfolio_manager.py`

**Features:**
- Track total capital (₹100,000)
- Allocate capital across positions (max 5 positions = ₹20k each)
- Calculate position sizes based on risk
- Monitor P&L in real-time
- Enforce risk limits (max 5% daily loss)

**Key Methods:**
```python
class PortfolioManager:
    def __init__(self, initial_capital: float = 100000):
        self.capital = initial_capital
        self.positions = {}  # {symbol: Position}
        self.available_capital = initial_capital
    
    def allocate_capital(self, symbol: str, strategy: dict) -> float:
        """Calculate position size based on strategy"""
        
    def can_open_position(self, symbol: str, price: float) -> bool:
        """Check if we have capital and risk capacity"""
        
    def update_position(self, symbol: str, current_price: float):
        """Update P&L and check stop loss/take profit"""
```

---

### 3. **Execution Engine**

**File:** `backend/src/execution_engine.py`

**Features:**
- Place orders via Fyers API (market/limit)
- Monitor open positions in real-time
- Auto-execute stop loss/take profit
- Handle order failures and retries
- Real-time position updates

**Key Methods:**
```python
class ExecutionEngine:
    def __init__(self, fyers_client, portfolio_manager):
        self.fyers = fyers_client
        self.portfolio = portfolio_manager
        self.active_orders = {}
    
    async def execute_trade(self, signal: TradeSignal):
        """Execute buy/sell based on strategy signal"""
        
    async def monitor_positions(self):
        """Real-time monitoring loop for SL/TP"""
        
    async def close_position(self, symbol: str, reason: str):
        """Close position (SL hit, TP reached, EOD)"""
```

---

### 4. **AI Trade Assistant**

**File:** `backend/src/ai_trade_assistant.py`

**Features:**
- Analyze stock + news → suggest entry/exit levels
- Calculate support/resistance using AI
- Recommend stop loss and take profit levels
- Provide trade rationale

**Prompt Example:**
```
Stock: RELIANCE
Current Price: ₹2,450
News: "Reliance announces major expansion in renewable energy"
AI Analysis: HIGH impact, POSITIVE sentiment

Task: Suggest intraday trade levels
- Entry price (support/resistance)
- Stop loss (risk management)
- Target 1, Target 2 (profit booking)
- Trade rationale
```

---

### 5. **TradingView Chart Integration**

**Frontend:** `frontend/src/components/TradingViewChart.tsx`

**Features:**
- Embed TradingView lightweight charts
- Show current price + candlesticks
- Overlay AI-suggested levels:
  - 🟢 Entry level (green line)
  - 🔴 Stop loss (red line)
  - 🟡 Target 1, Target 2 (yellow lines)
- Show active positions with entry price
- Real-time price updates

**Library:** `lightweight-charts` (TradingView's official library)

---

### 6. **Trade History & Analytics**

**File:** `backend/src/trade_tracker.py`

**Features:**
- Store all trades in MongoDB
- Calculate performance metrics:
  - Win rate
  - Average profit/loss
  - Sharpe ratio
  - Max drawdown
- Daily/weekly/monthly reports
- Strategy-wise performance comparison

**Database Schema:**
```python
{
  "tradeId": "uuid",
  "symbol": "RELIANCE",
  "strategy": "news_momentum_v1",
  "entryTime": "2025-11-12T10:30:00",
  "entryPrice": 2450,
  "exitTime": "2025-11-12T14:15:00",
  "exitPrice": 2485,
  "quantity": 8,
  "pnl": 280,
  "pnlPercent": 1.43,
  "reason": "TARGET_1_HIT",
  "aiAnalysis": {...}
}
```

---

### 7. **Backtesting Framework**

**File:** `backend/src/backtester.py`

**Features:**
- Test strategies on historical data
- Simulate trades with realistic slippage
- Calculate hypothetical P&L
- Compare multiple strategies
- Optimize strategy parameters

**Usage:**
```python
backtester = Backtester(
    strategy="news_momentum_v1",
    start_date="2024-01-01",
    end_date="2024-11-01",
    initial_capital=100000
)
results = await backtester.run()
# Returns: total_pnl, win_rate, max_drawdown, trades
```

---

## New UI Structure

### **Dashboard** (Main view)
```
┌─────────────────────────────────────────────────────────────┐
│  Portfolio: ₹102,450 (+2.45%)  │  Active: 3  │  Today: +₹1,200 │
├─────────────────────────────────────────────────────────────┤
│  Active Positions                                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ RELIANCE  │ +1.2%  │ ₹2,485  │ [Chart] [Close]         ││
│  │ TCS       │ -0.5%  │ ₹3,890  │ [Chart] [Close]         ││
│  │ INFY      │ +2.1%  │ ₹1,650  │ [Chart] [Close]         ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  Trade Signals (from active strategies)                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🟢 BUY HDFC @ ₹1,720 (News: Positive earnings)         ││
│  │    SL: ₹1,685  │  Target: ₹1,780  │  [Execute Trade]   ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### **Strategy Manager**
```
┌─────────────────────────────────────────────────────────────┐
│  Active Strategies                          [+ New Strategy] │
├─────────────────────────────────────────────────────────────┤
│  ✅ News Momentum v1        │ 3 trades today  │ +₹1,200     │
│  ✅ Breakout Scanner        │ 1 trade today   │ +₹450       │
│  ⏸️  Mean Reversion (Paused)│ 0 trades        │ -           │
├─────────────────────────────────────────────────────────────┤
│  Strategy Details: News Momentum v1                          │
│  Stock Picking: News-based (Impact: HIGH, Sentiment: POS)   │
│  Execution: Breakout (SL: 2%, TP: 5%)                       │
│  Performance: 65% win rate, Avg profit: 1.8%                │
│  [Edit] [Backtest] [Pause] [Delete]                         │
└─────────────────────────────────────────────────────────────┘
```

### **Trade View** (Individual stock)
```
┌─────────────────────────────────────────────────────────────┐
│  RELIANCE - ₹2,485 (+1.2%)                                  │
├─────────────────────────────────────────────────────────────┤
│  [TradingView Chart with levels]                            │
│  🟢 Entry: ₹2,450                                           │
│  🔴 Stop Loss: ₹2,400                                       │
│  🟡 Target 1: ₹2,500 (reached!)                             │
│  🟡 Target 2: ₹2,550                                        │
├─────────────────────────────────────────────────────────────┤
│  AI Analysis:                                                │
│  "Strong bullish momentum after renewable energy news.      │
│   Support at ₹2,440. Resistance at ₹2,550. Recommend        │
│   trailing stop loss to ₹2,470 to lock profits."           │
│  [Close Position] [Modify SL/TP]                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### **Phase 1: Core Trading Infrastructure** (Week 1-2)
- [ ] Build Portfolio Manager
- [ ] Build Execution Engine (Fyers integration)
- [ ] Create Trade Tracker (MongoDB schema)
- [ ] Test paper trading flow end-to-end

### **Phase 2: Strategy Engine** (Week 2-3)
- [ ] Design strategy config format
- [ ] Implement news-based stock picking
- [ ] Implement basic execution strategies (breakout, mean reversion)
- [ ] Add AI trade assistant for levels

### **Phase 3: UI Transformation** (Week 3-4)
- [ ] Build new Dashboard (portfolio overview)
- [ ] Add TradingView chart component
- [ ] Create Strategy Manager UI
- [ ] Build Trade History view

### **Phase 4: Advanced Features** (Week 4-5)
- [ ] Backtesting framework
- [ ] Performance analytics
- [ ] Real-time monitoring & alerts
- [ ] Strategy optimization

### **Phase 5: Production Ready** (Week 5-6)
- [ ] Risk management safeguards
- [ ] Error handling & recovery
- [ ] Logging & monitoring
- [ ] Live trading mode (with safety limits)

---

## Immediate Next Steps

1. **Database Setup**: Add MongoDB collections for trades, strategies, portfolio
2. **Portfolio Manager**: Build capital allocation and position tracking
3. **Execution Engine**: Integrate Fyers order placement
4. **Simple Strategy**: Implement one news-based strategy end-to-end
5. **Dashboard UI**: Replace news screener with portfolio dashboard

Would you like me to start implementing this architecture? I suggest we begin with:
1. Setting up the database schema
2. Building the Portfolio Manager
3. Creating a simple news-based strategy
4. Testing the full flow in paper trading mode

Let me know which component you'd like to prioritize!

