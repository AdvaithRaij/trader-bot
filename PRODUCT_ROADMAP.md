# AI Trading Bot - Product Roadmap & Issue Tracker

## 🎯 Product Vision
A complete AI-powered autonomous intraday trading platform for the Indian stock market (NSE) that enables traders to:
- Create and backtest trading strategies
- Paper trade to validate strategies without risk
- Execute automated live trades with AI-assisted decision making
- Monitor portfolio, risk, and performance in real-time

---

## 📊 FEATURE STATUS OVERVIEW

| Feature | Status | Priority | Notes |
|---------|--------|----------|-------|
| **Backtesting** | ❌ Broken | P0 | MongoDB connection issue |
| **Auto Trading** | ❌ Broken | P0 | Components don't initialize |
| **Paper Trading** | ⚠️ Partial | P0 | Works but no persistence |
| **Trade Execution** | ⚠️ Partial | P1 | Manual trades work, auto doesn't |
| **AI Suggestions** | ✅ Working | - | Groq LLM integrated |
| **Strategy Management** | ✅ Working | - | CRUD operations work |
| **News Aggregation** | ✅ Working | - | Multiple sources |
| **Stock Screener** | ⚠️ Partial | P2 | Basic screening works |
| **Portfolio View** | ⚠️ Partial | P1 | Shows mock data |
| **Trade Logs** | ❌ Broken | P1 | Uses mock data |
| **Risk Manager** | ❌ Broken | P1 | Uses mock data |
| **Settings** | ❌ Broken | P2 | Placeholder only |
| **Charts** | ✅ Working | - | TradingView-style |

---

## 🔴 CRITICAL ISSUES (P0 - Must Fix)

### 1. Backtesting Not Working
**File:** `backend/src/backtester.py`
**Issue:** `Backtester` creates `StrategyManager()` without MongoDB collection
**Error:** `"Strategy news_momentum_v1 not found"`
**Fix:** Pass MongoDB connection to StrategyManager in Backtester

### 2. Auto Trading Bot Not Initializing
**File:** `backend/src/main.py`
**Issue:** Health check shows all components "disconnected/not_initialized"
**Components affected:**
- broker: disconnected
- database: disconnected  
- ai_engine: not_initialized
- screener: not_initialized
- sentiment: not_initialized
- bot: stopped
**Fix:** Initialize components on app startup, not just when bot starts

### 3. Paper Trading Not Persisting
**File:** `backend/src/broker_fyers.py`
**Issue:** Paper trades exist only in memory, lost on restart
**Fix:** Persist paper trades to MongoDB

### 4. No UI Control for Bot
**File:** `frontend/src/components/Sidebar.tsx`, `frontend/src/pages/TradingDashboard.tsx`
**Issue:** No button to start/stop trading bot, no mode toggle
**Fix:** Add bot control panel with start/stop and paper/live toggle

---

## 🟡 HIGH PRIORITY ISSUES (P1)

### 5. TradeLogs Uses Mock Data
**File:** `frontend/src/pages/TradeLogs.tsx`
**Issue:** Imports from `mockData.ts` instead of calling API
**Fix:** Connect to `/api/trades/history` endpoint

### 6. RiskManager Uses Mock Data  
**File:** `frontend/src/pages/RiskManager.tsx`
**Issue:** Uses static mock data, Parameters/Alerts tabs are placeholders
**Fix:** Connect to `/risk/metrics` API, implement full functionality

### 7. Portfolio Shows Mock Values
**File:** `frontend/src/pages/TradingDashboard.tsx`
**Issue:** Some values are static/mock
**Fix:** Ensure all data comes from live API

### 8. Sidebar Shows Fake Bot Status
**File:** `frontend/src/components/Sidebar.tsx`
**Issue:** Hardcoded "Active" status with fake P&L values
**Fix:** Connect to `/status` endpoint for real data

---

## 🟢 MEDIUM PRIORITY ISSUES (P2)

### 9. Settings Page is Placeholder
**File:** `frontend/src/pages/Settings.tsx`
**Issue:** No actual functionality
**Fix:** Implement API keys config, trading preferences, broker settings

### 10. Watchlist Not Editable
**File:** `frontend/src/pages/TradeView.tsx`
**Issue:** Static watchlist, can't add/remove stocks
**Fix:** Add watchlist management with persistence

### 11. Stock Screener Limited
**File:** `frontend/src/pages/Screener.tsx`
**Issue:** Basic functionality only
**Fix:** Add more filters, save screener presets

### 12. No Real-time Data
**Issue:** No WebSocket for live price updates
**Fix:** Implement WebSocket connection for live quotes

---

## 📋 IMPLEMENTATION PLAN

### Phase 1: Core Trading (Week 1)
- [ ] Fix Backtester MongoDB connection
- [ ] Fix TradingBot component initialization
- [ ] Add bot control UI (start/stop/mode toggle)
- [ ] Persist paper trades to database
- [ ] Connect TradeLogs to real API

### Phase 2: Monitoring & Risk (Week 2)
- [ ] Fix RiskManager with real data
- [ ] Fix Sidebar with real bot status
- [ ] Implement Settings page
- [ ] Add position management (close/modify)

### Phase 3: Enhancement (Week 3)
- [ ] Editable watchlist
- [ ] Enhanced screener
- [ ] WebSocket for live data
- [ ] Alert system
- [ ] Performance analytics

---

## 🏗️ ARCHITECTURE

```
Frontend (React + TypeScript + Vite)
├── TradingDashboard - Main dashboard with portfolio overview
├── TradeView - Charts + order placement + AI suggestions
├── StrategyManager - Create/edit/toggle strategies
├── Backtest - Strategy backtesting
├── Screener - Stock screening
├── TradeLogs - Trade history
├── RiskManager - Risk metrics and limits
├── MarketNews - News aggregation
└── Settings - Configuration

Backend (Python + FastAPI)
├── TradingBot - Main orchestrator
├── StrategyEngine - Strategy execution
├── ExecutionEngine - Trade execution
├── Backtester - Historical testing
├── AITradeAssistant - Groq LLM integration
├── NewsAggregator - Multi-source news
├── RiskManager - Risk calculations
├── PortfolioManager - Position tracking
└── FyersBroker - Broker integration
```

---

## 📝 NOTES

- **Database:** MongoDB (local or Atlas)
- **Broker:** Fyers API (paper + live modes)
- **AI:** Groq (llama-3.3-70b-versatile)
- **Charts:** lightweight-charts v5

Last Updated: 2025-12-16

