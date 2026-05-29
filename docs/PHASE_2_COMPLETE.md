# Phase 2: Strategy Engine - COMPLETE ✅

## Overview
Phase 2 builds the intelligent brain of the trading bot: stock picking, AI-assisted level calculation, and automated signal generation.

---

## Components Built

### 1. **News-Based Stock Picker** (`backend/src/strategies/news_picker.py`)

**Purpose:** Filter high-impact news and extract tradeable stocks

**Features:**
- ✅ Filter news by impact (HIGH/MEDIUM/LOW)
- ✅ Filter by sentiment (POSITIVE/NEGATIVE/NEUTRAL)
- ✅ Filter by relevance score (0-100)
- ✅ Filter by timeframe (IMMEDIATE/SHORT_TERM/LONG_TERM)
- ✅ Extract stock symbols from `relatedStocks`
- ✅ Rank stocks by score (relevance × impact weight)
- ✅ Get news context for specific symbols

**Example Usage:**
```python
news_picker = NewsBasedStockPicker(news_aggregator)

# Pick stocks based on config
stock_picks = await news_picker.pick_stocks(config)
# Returns: [
#   {
#     "symbol": "RELIANCE",
#     "score": 285,
#     "newsCount": 3,
#     "news": [...],
#     "reasoning": "HIGH impact, positive sentiment - Strong positive news on green energy"
#   }
# ]

# Get context for specific stock
context = await news_picker.get_stock_context("RELIANCE")
# Returns: {
#   "symbol": "RELIANCE",
#   "newsCount": 3,
#   "avgRelevance": 88,
#   "dominantSentiment": "POSITIVE"
# }
```

---

### 2. **AI Trade Assistant** (`backend/src/ai_trade_assistant.py`)

**Purpose:** Use Gemini AI to suggest optimal entry/exit levels

**Features:**
- ✅ Analyze stock + news context
- ✅ Calculate entry price (support level)
- ✅ Calculate stop loss (respects strategy %)
- ✅ Calculate target 1 (conservative)
- ✅ Calculate target 2 (aggressive)
- ✅ Provide confidence score (0-100)
- ✅ Generate reasoning
- ✅ Fallback to rule-based levels if AI fails

**Example Usage:**
```python
ai_assistant = AITradeAssistant()

levels = await ai_assistant.suggest_levels(
    symbol="RELIANCE",
    current_price=2450.0,
    direction=TradeDirection.BUY,
    news_context=[...],
    execution_config=strategy.execution
)

# Returns: {
#   "entryPrice": 2450.0,
#   "stopLoss": 2400.0,
#   "target1": 2525.0,
#   "target2": 2575.0,
#   "confidence": 85,
#   "reasoning": "Strong positive news on green energy investment...",
#   "expectedMove": "+3.5%",
#   "riskRewardRatio": 1.5
# }
```

**AI Prompt:** `backend/prompts/trade_levels.txt`
- Analyzes news impact, technical levels, risk-reward
- Ensures minimum 1.5:1 risk-reward ratio
- Respects strategy's stop loss and take profit percentages

---

### 3. **Strategy Manager** (`backend/src/strategy_manager.py`)

**Purpose:** CRUD operations for trading strategies

**Features:**
- ✅ Create/Read/Update/Delete strategies
- ✅ Load/save to MongoDB
- ✅ Toggle strategy status (ACTIVE/PAUSED/DISABLED)
- ✅ Validate strategy configurations
- ✅ Update performance metrics after trades
- ✅ Get strategy summaries for API

**Example Usage:**
```python
strategy_manager = StrategyManager(db_collection=db.strategies)

# Load all strategies
await strategy_manager.load_strategies()

# Get active strategies
active = await strategy_manager.get_active_strategies()

# Toggle strategy
new_status = await strategy_manager.toggle_strategy("news_momentum_v1")

# Update performance after trade
await strategy_manager.update_strategy_performance(
    "news_momentum_v1",
    {"pnl": 450.0}
)
```

---

### 4. **Strategy Engine** (`backend/src/strategy_engine.py`)

**Purpose:** Orchestrate stock picking and signal generation

**Features:**
- ✅ Run all active strategies
- ✅ Run specific strategy by ID
- ✅ Pick stocks using configured picker
- ✅ Generate trade signals with AI levels
- ✅ Schedule periodic execution (every N minutes)
- ✅ Manual signal generation for specific symbols

**Example Usage:**
```python
strategy_engine = StrategyEngine(
    strategy_manager=strategy_manager,
    news_aggregator=news_aggregator,
    broker=broker,
    ai_assistant=ai_assistant
)

# Run all active strategies
signals = await strategy_engine.run_all_strategies()

# Run specific strategy
signals = await strategy_engine.run_strategy("news_momentum_v1")

# Start scheduler (runs every 15 minutes)
await strategy_engine.start_scheduler(interval_minutes=15)

# Generate manual signal
signal = await strategy_engine.generate_manual_signal("RELIANCE")
```

**Complete Flow:**
```
1. Load active strategies
2. For each strategy:
   a. Pick stocks (news-based)
   b. For each stock:
      - Get current price
      - Get AI-suggested levels
      - Create TradeSignal
3. Return all signals
```

---

### 5. **Default Strategies** (`backend/src/seed_strategies.py`)

**Three pre-configured strategies:**

#### **Strategy 1: News-Driven Momentum** (ACTIVE)
```json
{
  "strategyId": "news_momentum_v1",
  "name": "News-Driven Momentum",
  "stockPicking": {
    "type": "NEWS_BASED",
    "filters": {
      "impact": "HIGH",
      "sentiment": "POSITIVE",
      "relevance": ">=80"
    },
    "maxStocks": 5
  },
  "execution": {
    "type": "AI_ASSISTED",
    "stopLossPercent": 2.0,
    "takeProfitPercent": 5.0,
    "useMultipleTargets": true,
    "exitAtEOD": true
  },
  "riskManagement": {
    "maxPositionSize": 20.0,
    "maxDailyLoss": 5.0,
    "maxOpenPositions": 5
  }
}
```

#### **Strategy 2: Conservative News Trading** (PAUSED)
- Lower risk: 1.5% SL, 3% TP
- Max 3 positions
- Uses trailing stop loss

#### **Strategy 3: Aggressive News Scalping** (PAUSED)
- Higher risk: 3% SL, 8% TP
- Max 2 positions
- Exits earlier (3:00 PM)

**Seed Command:**
```bash
cd backend/src
python seed_strategies.py
```

---

### 6. **API Endpoints** (Added to `backend/src/main.py`)

#### **Strategy Management:**

```bash
# Get all strategies
GET /strategies
# Returns: { "strategies": [...], "total": 3 }

# Get specific strategy
GET /strategies/{strategy_id}
# Returns: { "strategy": {...} }

# Toggle strategy (ACTIVE <-> PAUSED)
POST /strategies/{strategy_id}/toggle
# Returns: { "message": "...", "status": "ACTIVE" }

# Run strategy manually
POST /strategies/{strategy_id}/run
# Returns: { "message": "Generated 2 signals", "signals": [...] }

# Generate signal for specific symbol
POST /signals/generate
# Body: { "symbol": "RELIANCE", "strategyId": "news_momentum_v1" }
# Returns: { "signal": {...} }
```

---

## Complete Integration Example

### **Autonomous Trading Flow:**

```python
# 1. Initialize components
from motor.motor_asyncio import AsyncIOMotorClient
from strategy_manager import StrategyManager
from strategy_engine import StrategyEngine
from execution_engine import ExecutionEngine
from portfolio_manager import PortfolioManager
from ai_trade_assistant import AITradeAssistant
from news_aggregator import NewsAggregator
from broker import FyersBroker

# Connect to MongoDB
client = AsyncIOMotorClient(config.MONGODB_URL)
db = client[config.MONGODB_DB_NAME]

# Initialize managers
strategy_manager = StrategyManager(db_collection=db.strategies)
await strategy_manager.load_strategies()

portfolio = PortfolioManager(
    initial_capital=100000,
    db_collection=db.portfolio
)
await portfolio.load_from_db()

broker = FyersBroker()
await broker.initialize()

execution = ExecutionEngine(
    broker=broker,
    portfolio_manager=portfolio,
    db_collection=db.trades
)

ai_assistant = AITradeAssistant()
news_aggregator = NewsAggregator()

strategy_engine = StrategyEngine(
    strategy_manager=strategy_manager,
    news_aggregator=news_aggregator,
    broker=broker,
    ai_assistant=ai_assistant
)

# 2. Start strategy scheduler (runs every 15 minutes)
await strategy_engine.start_scheduler(interval_minutes=15)

# 3. Main trading loop
while True:
    # Strategy engine generates signals automatically
    signals = await strategy_engine.run_all_strategies()
    
    # Execute each signal
    for signal in signals:
        trade = await execution.execute_signal(signal)
        if trade:
            logger.info(f"✅ Trade executed: {trade.symbol}")
    
    await asyncio.sleep(60)  # Check every minute
```

---

## What This Enables

Your bot can now:

1. **📰 Scan news every 15 minutes** (configurable)
2. **🎯 Pick high-impact stocks** (RELIANCE, TCS, etc.)
3. **🤖 Ask Gemini AI for levels** (entry, SL, targets)
4. **📊 Generate trade signals** automatically
5. **⚡ Execute trades** (via Phase 1 components)
6. **👁️ Monitor positions** and auto-exit on SL/TP
7. **📈 Track performance** by strategy

---

## Files Created

```
backend/src/
├── strategies/
│   ├── __init__.py              # Package exports
│   └── news_picker.py           # News-based stock picking
├── ai_trade_assistant.py        # AI level suggestions
├── strategy_manager.py          # Strategy CRUD
├── strategy_engine.py           # Main orchestrator
└── seed_strategies.py           # Default strategies

backend/prompts/
└── trade_levels.txt             # AI prompt for levels

docs/
└── PHASE_2_COMPLETE.md          # This file
```

**Updated Files:**
- `backend/src/main.py` - Added 5 strategy API endpoints
- `backend/src/prompt_loader.py` - Added `get_trade_levels_prompt()`

---

## Testing Phase 2

### **1. Seed Strategies:**
```bash
cd backend/src
python seed_strategies.py
```

### **2. Test Strategy Engine:**
```bash
# Start backend
python main.py --mode web

# Test endpoints
curl http://localhost:8000/strategies
curl http://localhost:8000/strategies/news_momentum_v1
curl -X POST http://localhost:8000/strategies/news_momentum_v1/run
curl -X POST http://localhost:8000/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE"}'
```

### **3. Expected Output:**
```json
{
  "message": "Generated 2 signals",
  "signals": [
    {
      "symbol": "RELIANCE",
      "direction": "BUY",
      "entryPrice": 2450.0,
      "stopLoss": 2400.0,
      "target1": 2525.0,
      "target2": 2575.0,
      "confidence": 85,
      "reasoning": "HIGH impact positive news on green energy investment..."
    }
  ]
}
```

---

## Next Steps: Phase 3 - UI Transformation

Now that we have autonomous signal generation, we need to:

1. **Build Dashboard** - Portfolio overview, P&L, active positions
2. **Add TradingView Charts** - Visualize stocks with entry/exit levels
3. **Create Strategy Manager UI** - Enable/disable strategies, view performance
4. **Build Trade History View** - See all trades with filters
5. **Add Real-time Updates** - WebSocket for live position updates

**Should I start Phase 3?** 🚀

