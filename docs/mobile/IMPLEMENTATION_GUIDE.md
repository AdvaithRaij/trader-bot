# TradingBot Mobile - React Native Implementation Guide

## 🎯 Project Overview

This is a comprehensive React Native (Expo) mobile application for the TradingBot platform. It connects to the same backend APIs as the web application and provides a native mobile experience with live data, real-time updates, and push notifications.

## 📋 Project Status

**Current Status**: Project initialized with all dependencies installed.

**Completed**:
- ✅ Expo project created with TypeScript
- ✅ All dependencies installed (Expo Router, Zustand, React Query, etc.)
- ✅ app.json configured with dark theme and notifications
- ✅ babel.config.js configured with module resolver

**Next Steps**: Implement the folder structure and core files as outlined below.

## 🏗️ Folder Structure

```
TradingBotMobile/
├── app/                              # Expo Router pages
│   ├── _layout.tsx                   # Root layout with providers
│   ├── (tabs)/                       # Tab-based navigation
│   │   ├── _layout.tsx               # Tab navigator config
│   │   ├── dashboard.tsx             # Dashboard tab
│   │   ├── news.tsx                  # News tab
│   │   ├── analysis.tsx              # Analysis tab
│   │   ├── predictions.tsx           # Predictions tab
│   │   └── alerts.tsx                # Alerts tab
│   ├── stock/
│   │   └── [symbol].tsx              # Stock detail screen
│   ├── pipeline/
│   │   └── index.tsx                 # Pipeline monitor
│   └── settings/
│       └── index.tsx                 # Settings screen
├── src/
│   ├── components/
│   │   ├── ui/                       # Base UI components
│   │   ├── dashboard/                # Dashboard components
│   │   ├── news/                     # News components
│   │   ├── analysis/                 # Analysis components
│   │   ├── predictions/              # Prediction components
│   │   ├── alerts/                   # Alert components
│   │   └── pipeline/                 # Pipeline components
│   ├── services/                     # API & Business Logic
│   │   ├── api/
│   │   │   ├── client.ts             # Axios client with base config
│   │   │   ├── marketData.ts         # Market data API
│   │   │   ├── newsApi.ts            # News API
│   │   │   ├── analysis.ts           # Analysis API
│   │   │   ├── predictions.ts        # Predictions API
│   │   │   ├── pipeline.ts           # Pipeline API
│   │   │   └── portfolio.ts          # Portfolio API
│   │   ├── websocket.ts              # Real-time price updates
│   │   ├── notifications.ts          # Push notifications
│   │   └── storage.ts                # Secure storage
│   ├── stores/                       # Zustand stores
│   │   ├── useMarketStore.ts
│   │   ├── useNewsStore.ts
│   │   ├── useAlertsStore.ts
│   │   ├── usePipelineStore.ts
│   │   ├── usePredictionsStore.ts
│   │   └── useAppStore.ts
│   ├── hooks/                        # Custom hooks
│   │   ├── useStockData.ts
│   │   ├── useLivePrice.ts
│   │   ├── useAnalysis.ts
│   │   ├── usePrediction.ts
│   │   ├── useNews.ts
│   │   └── useAlerts.ts
│   ├── utils/
│   │   ├── formatters.ts             # Number/currency formatters
│   │   ├── colors.ts                 # Theme colors
│   │   ├── constants.ts              # App constants
│   │   └── indicators.ts             # Technical indicators
│   └── types/
│       ├── market.ts
│       ├── stock.ts
│       ├── news.ts
│       ├── alert.ts
│       ├── prediction.ts
│       └── pipeline.ts
├── assets/
├── app.json
├── babel.config.js
├── package.json
└── tsconfig.json
```

## 🔑 Key Implementation Details

### Backend API Connection

The app connects to the backend at `http://localhost:8001` (or your deployed backend URL).

**Available Endpoints** (from backend/src/main.py):
- `GET /api/news` - Get news with AI analysis
- `GET /api/pipeline/screen` - Get screened stocks
- `POST /api/pipeline/analyze-multi` - Analyze stocks
- `GET /api/portfolio/positions` - Get active positions
- `GET /api/performance` - Get performance metrics
- `GET /status` - Bot status
- `GET /health` - Health check

### Environment Variables

Create a `.env` file in the project root:

```env
API_BASE_URL=http://localhost:8001
WS_URL=ws://localhost:8001/ws
```

### Design System

**Colors** (from prompt.md):
- Background: `#0A0E1A` → `#0F1629` → `#131B2E`
- Primary Accent: `#6C5CE7` → `#A855F7`
- Secondary Accent: `#00D2FF` → `#3A7BD5`
- Success/Bullish: `#00E676`
- Danger/Bearish: `#FF5252`
- Warning: `#FFD740`

**Typography**:
- System fonts with weights: 300, 400, 500, 600, 700
- Monospace for numbers (tabular nums)

**Components**:
- Glassmorphic cards with blur effects
- Gradient buttons and accents
- Smooth animations with react-native-reanimated
- Haptic feedback on interactions

## 📱 Features to Implement

### 1. Dashboard Tab
- Active trades card
- Portfolio summary
- Price ticker strip (horizontal scroll)
- Hot news carousel
- Market overview (NIFTY, SENSEX, BANK NIFTY)
- Bot status card
- P&L chart
- Top movers (gainers/losers)
- Quick stats row

### 2. News Tab
- News list with infinite scroll
- Filter by category (market, economy, sector, global)
- Filter by source (Economic Times, MoneyControl, Google News)
- Breaking news banner
- AI sentiment badges (POSITIVE/NEGATIVE/NEUTRAL)
- Impact indicators (HIGH/MEDIUM/LOW)
- Related stocks chips

### 3. Analysis Tab
- Stock search with autocomplete
- Stock list (NIFTY 50, NIFTY 200, F&O stocks)
- Stock detail screen with:
  - Price chart with timeframes (1D, 1W, 1M, 3M, 6M, 1Y, 5Y, All)
  - Performance metrics (today's high/low, 52-week high/low, volume)
  - Fundamentals (P/E, EPS, Market Cap, ROE, etc.)
  - Financials chart (Revenue, Profit, Net Worth)
  - Technicals:
    - Summary gauge (Bearish/Neutral/Bullish)
    - Indicators table (RSI, MACD, Beta)
    - Support & Resistance levels
    - Moving Averages table
  - About company
  - Shareholding pattern chart
  - Similar stocks list

### 4. Predictions Tab
- Active predictions list
- Prediction cards with:
  - Entry price
  - Target levels (T1, T2, T3)
  - Stop loss
  - Confidence gauge
  - AI reasoning
  - Risk-reward ratio
  - Verdict badge (Strong Buy/Buy/Hold/Sell/Strong Sell)
- Prediction timeline
- Historical predictions with outcomes

### 5. Alerts Tab
- Active alerts list
- Create alert modal
- Alert types:
  - Price above/below
  - Target hit
  - Stop loss hit
  - Percentage change
- Alert history
- Triggered alerts with notifications

### 6. Pipeline Monitor
- Pipeline status card
- Stage indicators (Screening → Analysis → Risk Check → Signal)
- Screener results
- Trade queue
- Strategy status

## 🚀 Getting Started

1. **Start the backend server**:
   ```bash
   cd backend/src
   python main.py
   ```

2. **Start the Expo dev server**:
   ```bash
   cd "Trading App React Native/TradingBotMobile"
   npm start
   ```

3. **Run on device/simulator**:
   - Press `i` for iOS simulator
   - Press `a` for Android emulator
   - Scan QR code with Expo Go app for physical device

## 📝 Implementation Priority

1. **Phase 1**: Core infrastructure
   - Utils (colors, formatters, constants)
   - Types definitions
   - API client setup
   - Base UI components

2. **Phase 2**: Services & State
   - API services
   - Zustand stores
   - Custom hooks
   - WebSocket connection

3. **Phase 3**: Screens
   - Tab navigation layout
   - Dashboard tab
   - News tab
   - Analysis tab (list view)

4. **Phase 4**: Advanced Features
   - Stock detail screen
   - Predictions tab
   - Alerts tab
   - Pipeline monitor

5. **Phase 5**: Polish
   - Push notifications
   - Animations
   - Error handling
   - Loading states
   - Pull-to-refresh

## 🔗 Backend Reference

All API implementations should reference the existing backend code:
- `backend/src/main.py` - API endpoints
- `backend/src/news_aggregator.py` - News service
- `backend/src/broker_fyers.py` - Market data
- `backend/src/multi_strategy_analyzer.py` - AI analysis
- `backend/src/screener.py` - Stock screening

## ⚠️ Important Notes

- **NO MOCK DATA**: All data must come from live APIs
- **Backend URL**: Update API_BASE_URL when deploying
- **Fyers Token**: Backend handles Fyers authentication
- **Real-time Updates**: Use WebSocket for live prices
- **Push Notifications**: Implement for alerts and high-priority news
- **Error Handling**: Gracefully handle API failures
- **Caching**: Use React Query for efficient data caching
- **Performance**: Optimize FlatList rendering for large lists

## 📚 Next Steps

See the individual task files in the `tasks/` folder for detailed implementation instructions for each component.

