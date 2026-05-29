# TRADINGBOT MOBILE - React Native Application Build Prompt

## PROJECT OVERVIEW

Build a complete React Native (Expo) mobile application called **TradingBot Mobile** that serves as the mobile companion to the existing TradingBot web platform. This is a NEW project in a NEW folder (`/TradingBotMobile`) but it MUST reuse and reference the backend logic, API integrations, services, and data sources already implemented in the existing website project located at `../` (the parent directory or sibling web project folder).

**CRITICAL RULES:**
1. **NO MOCK DATA** — Every single data point must come from the same live APIs, services, and backends used by the existing web project. Reference the web project's service files, API utilities, and integration modules. If the web project calls Fyers API for price data, this app calls the same endpoints. If the web project uses a news aggregator service, this app uses the same service.
2. **Reference the existing web codebase** for ALL business logic — look at existing files for API keys, endpoints, data transformation functions, AI analysis pipelines, news sources, screener logic, and trading pipeline configuration. Copy and adapt the service layer, don't reinvent it.
3. The app does NOT need to execute trades (for now), but it MUST display all data as if it's production-ready: live prices, real news, real analysis, real predictions.
4. Push notifications must be implemented for alerts and high-priority news.

---

## DESIGN SYSTEM & THEME

### Visual Identity
- **Theme:** Dark glassmorphic design with depth and layering
- **Background:** Deep dark gradient — `#0A0E1A` → `#0F1629` → `#131B2E`
- **Glass cards:** `rgba(255,255,255,0.05)` background with `rgba(255,255,255,0.08)` border, `blur(20)` backdrop filter (use `expo-blur` or equivalent)
- **Primary accent gradient:** `#6C5CE7` → `#A855F7` (purple to violet — matching the web app's accent)
- **Secondary accent gradient:** `#00D2FF` → `#3A7BD5` (cyan to blue)
- **Success/Bullish:** `#00E676` (bright green)
- **Danger/Bearish:** `#FF5252` (bright red)  
- **Warning:** `#FFD740` (amber)
- **Neutral:** `#78909C` (blue-gray)
- **Text primary:** `#FFFFFF` at 95% opacity
- **Text secondary:** `#FFFFFF` at 60% opacity
- **Text muted:** `#FFFFFF` at 35% opacity

### Typography
- Use system fonts with these weights: 300 (light), 400 (regular), 500 (medium), 600 (semibold), 700 (bold)
- Headings: Bold, large, white
- Subheadings: Semibold, medium, white at 80%
- Body: Regular, secondary color
- Numbers/Data: Use a monospace-style rendering for financial figures (use `tabularNums` variant or Roboto Mono for numbers)

### Component Styling Rules
- **Cards:** All cards use glassmorphic styling — semi-transparent backgrounds, subtle borders, border-radius of 16px, soft inner shadows
- **Gradients everywhere:** Use `LinearGradient` from `expo-linear-gradient` on buttons, headers, accent elements, progress bars
- **Shadows:** Use subtle colored shadows (e.g., purple glow behind primary buttons)
- **Spacing:** Tight but readable — 8px base unit. Cards have 12-16px internal padding. Screen horizontal padding: 16px. Minimize empty space.
- **Charts/Graphs:** Use `react-native-chart-kit`, `victory-native`, or `react-native-gifted-charts` — style them with gradients, glow effects, and transparent backgrounds matching the glassmorphic theme
- **Animations:** Use `react-native-reanimated` for smooth transitions, card entrances (fade + slide up), tab switches, and number ticker animations
- **Haptic feedback:** Use `expo-haptics` on button presses and alert triggers
- **Status bar:** Light content, transparent background

### Bottom Tab Bar
- Glassmorphic tab bar with blur background
- 5 tabs with icons (use `@expo/vector-icons` — Ionicons or MaterialCommunityIcons):
  1. **Dashboard** — `grid-outline` / `view-dashboard`
  2. **News** — `newspaper-outline`
  3. **Analysis** — `analytics-outline` / `chart-line`
  4. **Predictions** — `bulb-outline` / `crystal-ball` (or `target`)
  5. **Alerts** — `notifications-outline` / `bell`
- Active tab: Gradient-filled icon with glow effect + label
- Inactive tab: Muted icon, no label
- Tab bar height: ~70px with safe area handling
- Notification badge on Alerts tab (count of unread/triggered alerts)

---

## TECH STACK

React Native (Expo SDK 51+)
Expo Router (file-based routing)
TypeScript (strict mode)
Zustand (state management — lightweight, matches the fast data update needs)
React Query / TanStack Query (for API data fetching, caching, background refetch)
react-native-reanimated (animations)
expo-blur (glassmorphic effects)
expo-linear-gradient (gradients)
expo-haptics (haptic feedback)
expo-notifications (push notifications)
react-native-gifted-charts OR victory-native (charts — bar, line, pie)
react-native-svg (custom visualizations)
@react-navigation/bottom-tabs + @react-navigation/native-stack
expo-secure-store (secure storage for API keys/tokens)
date-fns (date formatting)
socket.io-client OR WebSocket (for real-time price updates — check what the web project uses)
yaml
Copy code

---

## PROJECT STRUCTURE

Create this exact folder structure:

TradingBotMobile/
├── app/                              # Expo Router pages
│   ├── _layout.tsx                   # Root layout with providers
│   ├── (tabs)/                       # Tab-based navigation
│   │   ├── _layout.tsx               # Tab navigator config
│   │   ├── dashboard.tsx             # Dashboard tab
│   │   ├── news.tsx                  # News tab
│   │   ├── analysis.tsx              # Analysis tab (stock list + search)
│   │   ├── predictions.tsx           # Predictions tab
│   │   └── alerts.tsx                # Alerts tab
│   ├── stock/                        # Stock detail screens
│   │   └── [symbol].tsx              # Dynamic route for stock detail
│   ├── pipeline/                     # Trading pipeline screens
│   │   └── index.tsx                 # Pipeline monitor
│   └── settings/
│       └── index.tsx                 # Settings screen
├── src/
│   ├── components/
│   │   ├── ui/                       # Base UI components
│   │   │   ├── GlassCard.tsx
│   │   │   ├── GradientButton.tsx
│   │   │   ├── GradientText.tsx
│   │   │   ├── AnimatedNumber.tsx
│   │   │   ├── PriceTicker.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── Divider.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── TabSelector.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── SentimentGauge.tsx
│   │   │   └── PullToRefresh.tsx
│   │   ├── dashboard/
│   │   │   ├── ActiveTradesCard.tsx
│   │   │   ├── PortfolioSummary.tsx
│   │   │   ├── PriceTickerStrip.tsx
│   │   │   ├── HotNewsCarousel.tsx
│   │   │   ├── MarketOverview.tsx
│   │   │   ├── BotStatusCard.tsx
│   │   │   ├── PnLChart.tsx
│   │   │   ├── TopMoversCard.tsx
│   │   │   └── QuickStatsRow.tsx
│   │   ├── news/
│   │   │   ├── NewsCard.tsx
│   │   │   ├── NewsList.tsx
│   │   │   ├── NewsFilter.tsx
│   │   │   └── BreakingNewsBanner.tsx
│   │   ├── analysis/
│   │   │   ├── StockSearchList.tsx
│   │   │   ├── PerformanceSection.tsx
│   │   │   ├── FundamentalsGrid.tsx
│   │   │   ├── FinancialsChart.tsx
│   │   │   ├── TechnicalsSection.tsx
│   │   │   ├── SummaryGauge.tsx
│   │   │   ├── IndicatorsTable.tsx
│   │   │   ├── SupportResistanceCard.tsx
│   │   │   ├── MovingAveragesTable.tsx
│   │   │   ├── AboutCompany.tsx
│   │   │   ├── ShareholdingPattern.tsx
│   │   │   ├── DeliveryVolume.tsx
│   │   │   ├── SimilarStocks.tsx
│   │   │   ├── StockMiniChart.tsx
│   │   │   └── PriceRangeBar.tsx
│   │   ├── predictions/
│   │   │   ├── PredictionCard.tsx
│   │   │   ├── TargetLevelsCard.tsx
│   │   │   ├── StopLossCard.tsx
│   │   │   ├── ConfidenceGauge.tsx
│   │   │   ├── PredictionTimeline.tsx
│   │   │   └── AIReasoningCard.tsx
│   │   ├── alerts/
│   │   │   ├── AlertCard.tsx
│   │   │   ├── AlertsList.tsx
│   │   │   ├── CreateAlertModal.tsx
│   │   │   ├── AlertHistoryCard.tsx
│   │   │   └── AlertStatusBadge.tsx
│   │   └── pipeline/
│   │       ├── PipelineStatusCard.tsx
│   │       ├── PipelineStageIndicator.tsx
│   │       ├── ScreenerResults.tsx
│   │       └── TradeQueueCard.tsx
│   ├── services/                     # API & Business Logic (PORT FROM WEB)
│   │   ├── api/
│   │   │   ├── fyers.ts              # Fyers API integration — COPY from web project
│   │   │   ├── marketData.ts         # Market data fetching — COPY from web project
│   │   │   ├── newsApi.ts            # News aggregation — COPY from web project
│   │   │   ├── aiAnalysis.ts         # AI analysis engine — COPY from web project
│   │   │   ├── predictions.ts        # Prediction engine — COPY from web project
│   │   │   ├── screener.ts           # Stock screener — COPY from web project
│   │   │   └── pipeline.ts           # Trading pipeline status — COPY from web project
│   │   ├── websocket.ts              # Real-time price stream — REFERENCE web project
│   │   ├── notifications.ts          # Push notification service
│   │   └── storage.ts                # Local storage utilities
│   ├── stores/                       # Zustand stores
│   │   ├── useMarketStore.ts         # Live market data store
│   │   ├── useNewsStore.ts           # News data store
│   │   ├── useAlertsStore.ts         # Alerts store
│   │   ├── usePipelineStore.ts       # Pipeline status store
│   │   ├── usePredictionsStore.ts    # Predictions store
│   │   └── useAppStore.ts            # App-wide settings
│   ├── hooks/
│   │   ├── useStockData.ts           # Hook for fetching stock data
│   │   ├── useLivePrice.ts           # Hook for real-time price subscription
│   │   ├── useAnalysis.ts            # Hook for full stock analysis
│   │   ├── usePrediction.ts          # Hook for AI predictions
│   │   ├── useNews.ts                # Hook for news feed
│   │   └── useAlerts.ts              # Hook for alert management
│   ├── utils/
│   │   ├── formatters.ts             # Number, currency, percentage formatters
│   │   ├── colors.ts                 # Color constants and theme
│   │   ├── indicators.ts             # Technical indicator calculations — COPY from web
│   │   └── constants.ts              # App constants
│   └── types/
│       ├── market.ts                 # Market data types
│       ├── stock.ts                  # Stock detail types
│       ├── news.ts                   # News types
│       ├── alert.ts                  # Alert types
│       ├── prediction.ts             # Prediction types
│       └── pipeline.ts               # Pipeline types
├── assets/
│   ├── images/
│   └── fonts/
├── app.json
├── tsconfig.json
├── package.json
└── babel.config.js

yaml
Copy code

---

## TASK BREAKDOWN

Execute these tasks IN ORDER. Each task is a self-contained unit. Complete each fully before moving on.

---

### TASK 1: Project Initialization & Base Configuration
**File: `tasks/task-01-init.md`**

1. Initialize a new Expo project with TypeScript:
   ```bash
   npx create-expo-app TradingBotMobile --template expo-template-blank-typescript
Install ALL dependencies:

bash
Copy code
npx expo install expo-router expo-blur expo-linear-gradient expo-haptics expo-notifications expo-secure-store expo-font expo-splash-screen expo-status-bar react-native-reanimated react-native-gesture-handler react-native-safe-area-context react-native-screens react-native-svg @react-navigation/bottom-tabs @react-navigation/native-stack
npm install zustand @tanstack/react-query react-native-gifted-charts date-fns socket.io-client @expo/vector-icons axios
Configure app.json with:

App name: "TradingBot"
Scheme: "tradingbot"
iOS and Android splash screen (dark background #0A0E1A)
Notification permissions
Background fetch capability
Configure babel.config.js with reanimated plugin

Set up the root app/_layout.tsx:

Wrap with QueryClientProvider (TanStack Query)
Wrap with safe area provider
Set status bar to light content, translucent
Set navigation theme to dark
Initialize notification listeners
Create src/utils/colors.ts with complete color/theme constants:

typescript
Run Code
Copy code
export const Colors = {
  background: {
    primary: '#0A0E1A',
    secondary: '#0F1629',
    tertiary: '#131B2E',
    card: 'rgba(255,255,255,0.05)',
    cardBorder: 'rgba(255,255,255,0.08)',
    cardHover: 'rgba(255,255,255,0.08)',
    elevated: 'rgba(255,255,255,0.10)',
  },
  accent: {
    primary: '#6C5CE7',
    primaryLight: '#A855F7',
    secondary: '#00D2FF',
    secondaryDark: '#3A7BD5',
  },
  gradient: {
    primary: ['#6C5CE7', '#A855F7'],
    secondary: ['#00D2FF', '#3A7BD5'],
    success: ['#00E676', '#00C853'],
    danger: ['#FF5252', '#D32F2F'],
    background: ['#0A0E1A', '#0F1629', '#131B2E'],
    card: ['rgba(255,255,255,0.08)', 'rgba(255,255,255,0.02)'],
  },
  text: {
    primary: 'rgba(255,255,255,0.95)',
    secondary: 'rgba(255,255,255,0.60)',
    muted: 'rgba(255,255,255,0.35)',
  },
  success: '#00E676',
  danger: '#FF5252',
  warning: '#FFD740',
  neutral: '#78909C',
  bullish: '#00E676',
  bearish: '#FF5252',
};
Create src/utils/formatters.ts:

formatCurrency(value: number): string → ₹1,25,000.00 (Indian number system)
formatLargeCurrency(value: number): string → ₹18,80,746Cr
formatPercentage(value: number): string → +1.11%
formatNumber(value: number): string → 1,93,11,971
formatCompactNumber(value: number): string → 18.8L Cr
timeAgo(date: Date): string → "4 hours ago"
formatChange(value: number): { text: string, color: string, prefix: string }
Create src/utils/constants.ts with app-wide constants

Acceptance: Project builds and runs with a blank dark screen. All dependencies installed. Theme file complete.

TASK 2: Base UI Components Library
File: tasks/task-02-ui-components.md

Build every base UI component with full glassmorphic styling:

GlassCard.tsx:

Props: children, style?, intensity? (blur), gradient? (boolean), glow? (boolean), onPress?
Uses expo-blur BlurView with tint="dark" as background
Semi-transparent background with subtle border
Border-radius 16px
If gradient prop, use LinearGradient overlay
If glow prop, add colored shadow
Animated entrance with FadeIn.duration(300).springify()
If onPress provided, wrap with Pressable + haptic feedback + scale animation on press
GradientButton.tsx:

Props: title, onPress, variant ('primary' | 'success' | 'danger' | 'secondary'), size ('sm' | 'md' | 'lg'), icon?, loading?, disabled?, fullWidth?
LinearGradient background matching variant
Pressable with scale animation (0.97 on press)
Haptic feedback on press
Loading spinner state
Disabled state with reduced opacity
GradientText.tsx:

Props: text, colors? (gradient array), style?
Uses MaskedView + LinearGradient for gradient text effect
AnimatedNumber.tsx:

Props: value, prefix? (₹), suffix? (%), decimals?, color?, size?, format? ('currency' | 'percentage' | 'number')
Animates between old and new values using reanimated
Flashes green/red briefly when value increases/decreases
Uses monospace-style font for consistent width
PriceTicker.tsx:

Props: symbol, price, change, changePercent, onPress?
Compact horizontal layout: Symbol | Price | Change badge
Change badge is green (positive) or red (negative) with arrow icon
Animated price update flash
Badge.tsx:

Props: text, variant ('success' | 'danger' | 'warning' | 'neutral' | 'info'), size?, icon?
Pill-shaped with gradient or solid background matching variant
Skeleton.tsx:

Props: width, height, borderRadius?, variant? ('text' | 'card' | 'circle')
Animated shimmer effect using reanimated (gradient sweep)
Dark glassmorphic background
Divider.tsx:

Horizontal line with gradient fade from transparent → white(10%) → transparent
SearchBar.tsx:

Glassmorphic search input with icon
Animated expand on focus
Clear button when text present
Debounced onSearch callback
TabSelector.tsx:

Props: tabs: string[], activeTab, onTabChange
Horizontal scrollable tab bar
Active tab has gradient underline with glow
Smooth animated indicator slide
ProgressBar.tsx:

Props: value, min, max, markerValue?, color?, showLabels?
Used for price range (today's low/high, 52-week range)
Triangle marker showing current position
Gradient fill from left color to right color
Labels at both ends
SentimentGauge.tsx:

Props: bearishCount, neutralCount, bullishCount, overallSentiment
Horizontal bar divided into colored segments (red → gray → green)
Triangle marker showing overall position
Labels below: Bearish (count), Neutral (count), Bullish (count)
Matches the Groww-style technicals summary gauge from the screenshots
PullToRefresh.tsx:

Wrapper component with custom pull-to-refresh animation
Gradient spinner animation
Acceptance: All components render correctly in isolation. Consistent glassmorphic theme.

TASK 3: Service Layer — Port from Web Project
File: tasks/task-03-services.md

CRITICAL: Look at the existing web project's source code. Find every API integration, service file, and utility. Adapt them for React Native. DO NOT create mock implementations.

services/api/fyers.ts:

Look at the web project's Fyers integration
Port the authentication flow (token management)
Port market data endpoints: getQuotes(symbols), getMarketDepth(symbol), getHistoricalData(symbol, resolution, from, to)
Port positions/orders endpoints for displaying active trades: getPositions(), getOrders(), getHoldings()
Use expo-secure-store for storing Fyers tokens instead of localStorage
Handle token refresh
services/api/marketData.ts:

Port the web project's market data service
getLiveQuotes(symbols: string[]): Promise<Quote[]>
getStockDetails(symbol: string): Promise<StockDetails> — includes company info, fundamentals, performance data
getHistoricalCandles(symbol, resolution, from, to): Promise<Candle[]>
getMarketStatus(): Promise<MarketStatus>
getIndices(): Promise<Index[]> — NIFTY 50, SENSEX, BANK NIFTY, etc.
getTopGainers(): Promise<Stock[]>
getTopLosers(): Promise<Stock[]>
services/api/newsApi.ts:

Port the web project's news aggregation service
Find which sources the web project uses (ScoutQuest, Livesquawk, MoneyControl, CNBC TV18, Business Today, etc.)
getMarketNews(page, limit): Promise<NewsItem[]>
getStockNews(symbol, page, limit): Promise<NewsItem[]>
getBreakingNews(): Promise<NewsItem[]>
getNewsByCategory(category): Promise<NewsItem[]> — categories: market, economy, sector, global
Each news item should have: id, title, summary, source, timestamp, category, sentiment (positive/negative/neutral), relatedStocks, importance (high/medium/low), url
services/api/aiAnalysis.ts:

Port the web project's AI analysis engine
getStockAnalysis(symbol): Promise<StockAnalysis> — full analysis including:
Performance data (today's high/low, 52-week high/low, open, prev close, volume, circuits)
Fundamentals (mkt cap, ROE, P/E, EPS, P/B, div yield, industry P/E, book value, debt to equity, face value)
Financials (revenue, profit, net worth — quarterly and yearly arrays)
About company (CEO, founded, NSE symbol, description)
Shareholding pattern (promoters, FIIs, retail, DIIs — with historical quarters)
Technicals: Summary (bearish/neutral/bullish counts + overall sentiment), Indicators (RSI, MACD, Beta with values and verdicts), Support & Resistance (S1, S2, S3, R1, R2, R3 + pivot), Moving Averages (10D, 20D, 50D, 100D, 200D — both MA and EMA), Delivery volume (daily, weekly, monthly)
Similar stocks list
getTechnicalSummary(symbol): Promise<TechnicalSummary>
getAISentiment(symbol): Promise<AISentiment> — overall AI verdict on the stock
services/api/predictions.ts:

Port the web project's prediction engine
getPredictions(symbol): Promise<Prediction> — includes:
Entry price
Target levels: T1, T2, T3 with prices
Stop loss level
Confidence score (1-100)
Timeframe (intraday, swing, positional)
AI reasoning/rationale text
Risk-reward ratio
Overall verdict (Strong Buy / Buy / Hold / Sell / Strong Sell)
getActivePredictions(): Promise<Prediction[]> — all stocks currently being tracked
getPredictionHistory(): Promise<Prediction[]> — past predictions with actual outcomes
services/api/screener.ts:

Port the web project's stock screener
searchStocks(query: string): Promise<StockSearchResult[]> — for the search functionality
getScreenerResults(filters): Promise<ScreenerResult[]> — filtered stock list
getWatchlist(): Promise<Stock[]>
getSimilarStocks(symbol): Promise<Stock[]>
services/api/pipeline.ts:

Port the web project's trading pipeline service
getPipelineStatus(): Promise<PipelineStatus> — current state of the automated pipeline
getPipelineHistory(): Promise<PipelineRun[]> — past runs
getActiveStrategies(): Promise<Strategy[]>
services/websocket.ts:

Port the web project's WebSocket/real-time connection
Connect to the same price streaming service
subscribeToSymbols(symbols: string[], callback: (data) => void)
unsubscribeFromSymbols(symbols: string[])
Auto-reconnect logic
Handle market open/close gracefully
services/notifications.ts:

Set up expo-notifications:
Request permissions
Register for push notifications
Handle foreground notifications (show in-app banner)
Handle background notifications
Schedule local notifications for alert triggers
sendAlertNotification(alert: Alert) — when a price level is breached
sendNewsNotification(news: NewsItem) — when high-importance news arrives
sendPredictionNotification(prediction: Prediction) — when a prediction target is hit
services/storage.ts:

getSecure(key) / setSecure(key, value) / deleteSecure(key) — via expo-secure-store
getLocal(key) / setLocal(key, value) — via AsyncStorage
Store: API tokens, user preferences, watchlist, alert configurations
Acceptance: All services compile. They connect to the same backends/APIs as the web project. No mock data.

TASK 4: State Management (Zustand Stores)
File: tasks/task-04-stores.md

useMarketStore.ts:

typescript
Run Code
Copy code
interface MarketStore {
  quotes: Record<string, Quote>;  // symbol → latest quote
  indices: Index[];
  topGainers: Stock[];
  topLosers: Stock[];
  marketStatus: 'pre-open' | 'open' | 'closed' | 'post-close';
  watchlist: string[];
  isConnected: boolean;
  // Actions
  updateQuote: (symbol: string, quote: Quote) => void;
  setIndices: (indices: Index[]) => void;
  setMarketStatus: (status: string) => void;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
  fetchInitialData: () => Promise<void>;
}
useNewsStore.ts:

typescript
Run Code
Copy code
interface NewsStore {
  allNews: NewsItem[];
  breakingNews: NewsItem[];
  stockNews: Record<string, NewsItem[]>;
  activeCategory: string;
  isLoading: boolean;
  // Actions
  fetchNews: (category?: string) => Promise<void>;
  fetchStockNews: (symbol: string) => Promise<void>;
  fetchBreakingNews: () => Promise<void>;
  markAsRead: (newsId: string) => void;
}
useAlertsStore.ts:

typescript
Run Code
Copy code
interface Alert {
  id: string;
  symbol: string;
  stockName: string;
  type: 'price_above' | 'price_below' | 'target_hit' | 'stop_loss_hit' | 'percentage_change';
  targetValue: number;
  currentPrice: number;
  status: 'active' | 'triggered' | 'expired' | 'cancelled';
  createdAt: Date;
  triggeredAt?: Date;
  note?: string;
}

interface AlertsStore {
  alerts: Alert[];
  triggeredAlerts: Alert[];
  // Actions
  addAlert: (alert: Omit<Alert, 'id' | '