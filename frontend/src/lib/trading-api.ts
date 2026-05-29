const API_BASE_URL = 'http://localhost:8000'

// ============================================
// PIPELINE TYPES (matching backend models)
// ============================================

export type PipelineState =
  | 'IDLE'
  | 'SCREENING'
  | 'ANALYZING'
  | 'EXECUTING'
  | 'MONITORING'
  | 'SQUARING_OFF'
  | 'STOPPED'

export interface PipelineStatus {
  state: PipelineState
  is_running: boolean
  current_cycle: number
  last_screening_time: string | null
  last_execution_time: string | null
  next_screening_time: string | null
  market_status: 'PRE_MARKET' | 'OPEN' | 'CLOSED'
  metrics: PipelineMetrics
}

export interface PipelineMetrics {
  total_screenings: number
  total_analyses: number
  total_executions: number
  successful_trades: number
  failed_trades: number
  total_pnl: number
  open_positions: number
  open_risk_percent: number
  daily_loss_percent: number
  trades_today: number
}

export interface ScreenerCandidate {
  symbol: string
  name: string
  current_price: number
  change_percent: number
  screening_score: number
  relative_volume: number
  turnover_cr: number
  atr_percent: number
  rsi: number
  gap_percent: number
  vwap_distance_percent: number
  market_cap_cr: number
  trend: string
  news_context: {
    has_news: boolean
    sentiment: string
    summary: string | null
  }
}

export interface ScreenerOutput {
  timestamp: string
  market_context: {
    nifty_trend: 'BULLISH' | 'BEARISH' | 'SIDEWAYS'
    vix_level: number
    vix_status: 'LOW' | 'NORMAL' | 'HIGH'
    market_status: string
  }
  candidates: ScreenerCandidate[]
  total_scanned: number
  filters_applied: string[]
}

export interface TradePlanLevels {
  entry: number
  stop_loss: number
  target_1: number
  target_2: number
  risk_reward_ratio: number
}

export interface TradePlan {
  symbol: string
  direction: 'BUY' | 'SELL'
  confidence: number
  levels: TradePlanLevels
  rationale: {
    setup_type: string
    key_levels: string[]
    catalysts: string[]
    risks: string[]
    summary: string
  }
  generated_at: string
  valid_until: string
}

export interface ExecutorStatus {
  is_active: boolean
  open_positions: number
  pending_orders: number
  trades_today: number
  max_trades_per_day: number
  daily_pnl: number
  daily_pnl_percent: number
  open_risk_percent: number
  max_open_risk_percent: number
  last_trade_time: string | null
  positions: ExecutorPosition[]
}

export interface ExecutorPosition {
  symbol: string
  direction: 'BUY' | 'SELL'
  quantity: number
  entry_price: number
  current_price: number
  stop_loss: number
  target_1: number
  target_2: number | null
  unrealized_pnl: number
  unrealized_pnl_percent: number
  entry_time: string
  risk_percent: number
}

// Type definitions
export interface PortfolioSummary {
  totalCapital: number
  availableCash: number
  allocatedCapital: number
  totalPnl: number
  totalPnlPercent: number
  todayPnl: number
  todayPnlPercent: number
  openPositions: number
  maxPositions: number
  currentDrawdown: number
  maxDrawdown: number
  winRate: number
  totalTrades: number
}

export interface ActivePosition {
  symbol: string
  direction: 'BUY' | 'SELL'
  quantity: number
  entryPrice: number
  currentPrice: number
  stopLoss: number
  target1: number
  target2?: number
  pnl: number
  pnlPercent: number
  status: 'OPEN' | 'PENDING_EXIT' | 'CLOSED'
  strategyId: string
  strategyName: string
  entryTime: string
}

export interface TradeSignal {
  symbol: string
  direction: 'BUY' | 'SELL'
  strategyId: string
  strategyName: string
  entryPrice: number
  stopLoss: number
  target1: number
  target2?: number
  confidence: number
  reasoning: string
  newsContext?: any[]
  aiAnalysis?: {
    expectedMove?: number
    riskRewardRatio?: number
    stockScore?: number
  }
}

export interface Strategy {
  strategyId: string
  name: string
  description: string
  status: 'ACTIVE' | 'PAUSED' | 'DISABLED'
  stockPicking: {
    type: 'NEWS_BASED' | 'TECHNICAL' | 'MOMENTUM' | 'AI_RECOMMENDED'
    filters: Record<string, any>
    maxStocks: number
  }
  execution: {
    type: 'BREAKOUT' | 'MEAN_REVERSION' | 'SCALPING' | 'AI_ASSISTED'
    entryCondition: string
    stopLossPercent: number
    takeProfitPercent: number
    useTrailingStop: boolean
    trailingStopPercent?: number
    useMultipleTargets: boolean
    exitAtEOD: boolean
    eodExitTime: string
    useAILevels: boolean
  }
  riskManagement: {
    maxPositionSize: number
    maxDailyLoss: number
    maxDrawdown: number
    maxOpenPositions: number
  }
  performance: {
    totalTrades: number
    winningTrades: number
    losingTrades: number
    totalPnl: number
    winRate: number
    avgPnl: number
    bestTrade: number
    worstTrade: number
    sharpeRatio: number
  }
  createdAt: string
  updatedAt: string
}

// Multi-Strategy Analysis Types
export interface StrategyAnalysis {
  direction: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  entry: number
  stop_loss: number
  target_1: number
  risk_reward: number
  reasoning: string
}

export interface StrategyRecommendation {
  best_strategy: 'fundamental' | 'news_based' | 'combined'
  confidence: number
  reasoning: string
  overall_sentiment: 'bullish' | 'bearish' | 'neutral'
  trade_quality: 'excellent' | 'good' | 'fair' | 'poor'
}

export interface MultiStrategyAnalysis {
  symbol: string
  name: string
  current_price: number
  day_change_pct: number
  screener_score: number
  strategies: {
    fundamental: StrategyAnalysis
    news_based: StrategyAnalysis
    combined: StrategyAnalysis
  }
  recommendation: StrategyRecommendation
}

export interface MultiStrategyResponse {
  success: boolean
  timestamp: string
  total_analyzed: number
  duration_ms: number
  analyses: MultiStrategyAnalysis[]
  message?: string
}

export interface NewsItem {
  id: string
  title: string
  summary: string
  sentiment: 'positive' | 'negative' | 'neutral'
  sentimentScore: number
  source: string
  publishedAt: string
  url?: string
  symbols?: string[]
  categories?: string[]
  category?: 'market' | 'company' | 'economy' | 'technology' | 'policy' | 'finance' | 'corporate'
  content?: string
  confidence?: number
  readTime?: number
  author?: string
  aiAnalysis?: {
    impact: 'HIGH' | 'MEDIUM' | 'LOW'
    sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
    relatedStocks: string[]
    analysis: string
    timeframe: 'IMMEDIATE' | 'SHORT_TERM' | 'LONG_TERM'
    relevance?: number
  }
}

export interface NewsResponse {
  news: NewsItem[]
  pagination: {
    currentPage: number
    totalPages: number
    totalItems: number
    itemsPerPage: number
    hasNext: boolean
    hasPrevious: boolean
  }
  filters: {
    category: string
    availableCategories: string[]
    availableSources: string[]
    availableSentiments: string[]
  }
}

// API Service
class TradingApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error)
      throw error
    }
  }

  async getPortfolioSummary(): Promise<PortfolioSummary> {
    return this.request<PortfolioSummary>('/api/portfolio/summary')
  }

  async getActivePositions(): Promise<ActivePosition[]> {
    return this.request<ActivePosition[]>('/api/portfolio/positions')
  }

  async getStrategies(): Promise<Strategy[]> {
    return this.request<Strategy[]>('/api/strategies')
  }

  async getStrategy(strategyId: string): Promise<Strategy> {
    return this.request<Strategy>(`/api/strategies/${strategyId}`)
  }

  async toggleStrategy(strategyId: string): Promise<{ message: string; strategy: Strategy }> {
    return this.request(`/api/strategies/${strategyId}/toggle`, { method: 'POST' })
  }

  async runStrategy(strategyId: string): Promise<{ signals: TradeSignal[] }> {
    return this.request(`/api/strategies/${strategyId}/run`, { method: 'POST' })
  }

  async getNews(params: {
    page?: number
    limit?: number
    category?: string
    source?: string
    refresh?: boolean
  }): Promise<NewsResponse> {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', params.page.toString())
    if (params.limit) queryParams.append('limit', params.limit.toString())
    if (params.category) queryParams.append('category', params.category)
    if (params.source) queryParams.append('source', params.source)
    if (params.refresh) queryParams.append('refresh', 'true')

    return this.request<NewsResponse>(`/api/news?${queryParams.toString()}`)
  }

  async generateSignal(symbol: string, strategyId?: string): Promise<{ signal: TradeSignal }> {
    return this.request<{ signal: TradeSignal }>('/api/signals/generate', {
      method: 'POST',
      body: JSON.stringify({ symbol, strategyId })
    })
  }

  async executeTrade(order: {
    symbol: string
    side: 'buy' | 'sell'
    quantity: number
    orderType: 'market' | 'limit'
    price?: number
  }): Promise<{ success: boolean; orderId?: string; message?: string }> {
    return this.request('/api/trades/execute', {
      method: 'POST',
      body: JSON.stringify(order)
    })
  }

  async getPerformanceMetrics(): Promise<{
    totalTrades: number
    winRate: number
    totalPnl: number
    avgPnl: number
    sharpeRatio: number
    maxDrawdown: number
  }> {
    return this.request('/api/performance')
  }

  async searchStocks(query: string = '', limit: number = 20): Promise<{
    stocks: Array<{ symbol: string; name: string; sector: string }>
    count: number
  }> {
    return this.request(`/api/stocks/search?query=${encodeURIComponent(query)}&limit=${limit}`)
  }

  async getStockQuote(symbol: string): Promise<{
    symbol: string
    price: number
    change: number
    changePercent: number
    high: number
    low: number
    open: number
    volume: number
  }> {
    return this.request(`/api/stocks/${symbol}/quote`)
  }

  async getBatchQuotes(symbols: string[]): Promise<{
    quotes: Array<{
      symbol: string
      price: number
      change: number
      changePercent: number
      high: number
      low: number
      open: number
      volume: number
    }>
    count: number
  }> {
    return this.request('/api/stocks/quotes/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbols })
    })
  }

  // Bot Control APIs
  async getBotStatus(): Promise<{
    is_running: boolean
    mode: string
    uptime: string
    todayTrades: number
    todayPnl: number
    capital: number
    activePositions: number
  }> {
    return this.request('/status')
  }

  async getHealthStatus(): Promise<{
    status: string
    timestamp: string
    components: {
      broker: string
      database: string
      ai_engine: string
      screener: string
      sentiment: string
      bot: string
    }
  }> {
    return this.request('/health')
  }

  async getTradingMode(): Promise<{
    mode: string
    mockMode: boolean
  }> {
    return this.request('/api/trading/mode')
  }

  async startBot(): Promise<{ message: string }> {
    return this.request('/start', { method: 'POST' })
  }

  async stopBot(): Promise<{ message: string }> {
    return this.request('/stop', { method: 'POST' })
  }

  // Trade History APIs
  async getTrades(limit: number = 50): Promise<{
    trades: Array<{
      id: string
      symbol: string
      side: string
      quantity: number
      price: number
      timestamp: string
      status: string
      pnl: number
      reason: string
    }>
    count: number
  }> {
    return this.request(`/trades?limit=${limit}`)
  }

  async getTradeHistory(days: number = 7): Promise<{
    trades: Array<{
      id: string
      symbol: string
      side: string
      quantity: number
      price: number
      timestamp: string
      status: string
      pnl: number
      reason: string
    }>
    count: number
  }> {
    return this.request(`/trades/history?days=${days}`)
  }

  async getTodayTrades(): Promise<{
    trades: Array<{
      id: string
      symbol: string
      side: string
      quantity: number
      price: number
      timestamp: string
      status: string
      pnl: number
    }>
  }> {
    return this.request('/trades/today')
  }

  // Risk Management APIs
  async getRiskMetrics(): Promise<{
    maxDrawdown: number
    currentDrawdown: number
    sharpeRatio: number
    winRate: number
    avgWin: number
    avgLoss: number
    totalTrades: number
  }> {
    return this.request('/risk/metrics')
  }

  async updateRiskLimits(limits: {
    maxDrawdown?: number
    maxDailyLoss?: number
    maxPositionSize?: number
  }): Promise<{ success: boolean; message: string }> {
    return this.request('/risk/limits', {
      method: 'PUT',
      body: JSON.stringify(limits)
    })
  }

  // Settings APIs
  async getSettings(): Promise<{
    trading: {
      initialCapital: number
      maxCapitalPerTrade: number
      maxActiveTrades: number
      maxDailyLosses: number
      maxDailyDrawdown: number
      minRiskRewardRatio: number
      aiConfidenceThreshold: number
    }
    marketHours: {
      tradingStart: string
      tradingEnd: string
      forceExitTime: string
    }
    broker: {
      connected: boolean
      mode: string
      provider: string
      hasApiKey: boolean
    }
    ai: {
      provider: string
      model: string
      hasApiKey: boolean
    }
    notifications: {
      telegramEnabled: boolean
      hasTelegramToken: boolean
    }
    database: {
      connected: boolean
      url: string
    }
  }> {
    return this.request('/api/settings')
  }

  async getApiStatus(): Promise<{
    broker: { name: string; connected: boolean; mode: string }
    ai: { name: string; connected: boolean; model: string }
    database: { name: string; connected: boolean }
    telegram: { name: string; connected: boolean }
    news: { name: string; connected: boolean; sources: string[] }
  }> {
    return this.request('/api/settings/api-status')
  }

  // Watchlist APIs
  async getWatchlist(): Promise<{
    watchlist: Array<{
      symbol: string
      name: string
      price: number
      change: number
      changePercent: number
      lastUpdated?: string
    }>
    count: number
  }> {
    return this.request('/api/watchlist')
  }

  async addToWatchlist(symbol: string): Promise<{
    success: boolean
    message?: string
    error?: string
    symbols?: string[]
  }> {
    return this.request('/api/watchlist/add', {
      method: 'POST',
      body: JSON.stringify({ symbol })
    })
  }

  async removeFromWatchlist(symbol: string): Promise<{
    success: boolean
    message?: string
    error?: string
    symbols?: string[]
  }> {
    return this.request('/api/watchlist/remove', {
      method: 'POST',
      body: JSON.stringify({ symbol })
    })
  }

  // ============================================
  // PIPELINE APIs (3-Stage Architecture)
  // ============================================

  async getPipelineStatus(): Promise<PipelineStatus> {
    return this.request<PipelineStatus>('/api/pipeline/status')
  }

  async startPipeline(): Promise<{ success: boolean; message: string }> {
    return this.request('/api/pipeline/start', { method: 'POST' })
  }

  async stopPipeline(): Promise<{ success: boolean; message: string }> {
    return this.request('/api/pipeline/stop', { method: 'POST' })
  }

  async triggerScreening(): Promise<{ success: boolean; message: string }> {
    return this.request('/api/pipeline/screen', { method: 'POST' })
  }

  // Screener APIs
  async getScreenerResults(): Promise<ScreenerOutput> {
    return this.request<ScreenerOutput>('/api/screener/results')
  }

  async runScreener(): Promise<ScreenerOutput> {
    return this.request<ScreenerOutput>('/api/screener/run', { method: 'POST' })
  }

  // Trade Plan APIs
  async getTradePlans(): Promise<{ plans: TradePlan[]; count: number }> {
    return this.request('/api/trade-plans')
  }

  async generateTradePlan(symbol: string): Promise<{ plan: TradePlan }> {
    return this.request('/api/trade-plans/generate', {
      method: 'POST',
      body: JSON.stringify({ symbol })
    })
  }

  async approveTradePlan(symbol: string): Promise<{ success: boolean; message: string }> {
    return this.request('/api/trade-plans/approve', {
      method: 'POST',
      body: JSON.stringify({ symbol })
    })
  }

  async rejectTradePlan(symbol: string): Promise<{ success: boolean; message: string }> {
    return this.request('/api/trade-plans/reject', {
      method: 'POST',
      body: JSON.stringify({ symbol })
    })
  }

  // Multi-Strategy Analysis APIs
  async runMultiStrategyAnalysis(symbols?: string[]): Promise<MultiStrategyResponse> {
    return this.request('/api/pipeline/analyze-multi', {
      method: 'POST',
      body: symbols && symbols.length > 0 ? JSON.stringify({ symbols }) : undefined
    })
  }

  async getMultiStrategyResults(): Promise<MultiStrategyResponse> {
    return this.request('/api/pipeline/multi-strategy-results')
  }

  // Executor APIs
  async getExecutorStatus(): Promise<ExecutorStatus> {
    return this.request<ExecutorStatus>('/api/executor/status')
  }

  async executeTradePlan(symbol: string): Promise<{
    success: boolean
    order_id?: string
    message: string
  }> {
    return this.request('/api/executor/execute', {
      method: 'POST',
      body: JSON.stringify({ symbol })
    })
  }

  async squareOffPosition(symbol: string): Promise<{ success: boolean; message: string }> {
    return this.request('/api/executor/square-off', {
      method: 'POST',
      body: JSON.stringify({ symbol })
    })
  }

  async squareOffAll(): Promise<{ success: boolean; message: string; closed_count: number }> {
    return this.request('/api/executor/square-off-all', { method: 'POST' })
  }

  // Pipeline Metrics
  async getPipelineMetrics(): Promise<PipelineMetrics> {
    return this.request<PipelineMetrics>('/api/pipeline/metrics')
  }
}

export const apiService = new TradingApiService()

// WebSocket service for real-time updates
export interface PriceUpdate {
  symbol: string
  price: number
  change: number
  changePercent: number
  high?: number
  low?: number
  volume?: number
}

export class PriceWebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private subscribedSymbols: Set<string> = new Set()
  private onPriceUpdate: ((prices: PriceUpdate[]) => void) | null = null
  private onConnectionChange: ((connected: boolean) => void) | null = null

  connect(
    onPriceUpdate: (prices: PriceUpdate[]) => void,
    onConnectionChange?: (connected: boolean) => void
  ) {
    this.onPriceUpdate = onPriceUpdate
    this.onConnectionChange = onConnectionChange || null

    try {
      this.ws = new WebSocket('ws://localhost:8000/ws/prices')

      this.ws.onopen = () => {
        console.log('Price WebSocket connected')
        this.reconnectAttempts = 0
        this.onConnectionChange?.(true)

        // Re-subscribe to symbols if any
        if (this.subscribedSymbols.size > 0) {
          this.subscribe(Array.from(this.subscribedSymbols))
        }
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'prices' && data.data) {
            this.onPriceUpdate?.(data.data)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('Price WebSocket disconnected')
        this.onConnectionChange?.(false)
        this.reconnect()
      }

      this.ws.onerror = (error) => {
        console.error('Price WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to connect Price WebSocket:', error)
      this.reconnect()
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

      console.log(`Attempting to reconnect Price WebSocket in ${delay}ms (attempt ${this.reconnectAttempts})`)

      setTimeout(() => {
        if (this.onPriceUpdate) {
          this.connect(this.onPriceUpdate, this.onConnectionChange || undefined)
        }
      }, delay)
    } else {
      console.error('Max Price WebSocket reconnection attempts reached')
    }
  }

  subscribe(symbols: string[]) {
    symbols.forEach(s => this.subscribedSymbols.add(s))
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        symbols: symbols
      }))
    }
  }

  unsubscribe(symbols: string[]) {
    symbols.forEach(s => this.subscribedSymbols.delete(s))
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        symbols: symbols
      }))
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.subscribedSymbols.clear()
  }
}

export const priceWebSocket = new PriceWebSocketService()

// ============================================
// PIPELINE WEBSOCKET SERVICE
// ============================================

export interface PipelineEvent {
  type: 'state_change' | 'screening_complete' | 'analysis_complete' | 'trade_executed' | 'position_update' | 'metrics_update' | 'error'
  data: any
  timestamp: string
}

export class PipelineWebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private onEvent: ((event: PipelineEvent) => void) | null = null
  private onConnectionChange: ((connected: boolean) => void) | null = null

  connect(
    onEvent: (event: PipelineEvent) => void,
    onConnectionChange?: (connected: boolean) => void
  ) {
    this.onEvent = onEvent
    this.onConnectionChange = onConnectionChange || null

    try {
      this.ws = new WebSocket('ws://localhost:8000/ws/pipeline')

      this.ws.onopen = () => {
        console.log('Pipeline WebSocket connected')
        this.reconnectAttempts = 0
        this.onConnectionChange?.(true)
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.onEvent?.(data as PipelineEvent)
        } catch (error) {
          console.error('Failed to parse Pipeline WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('Pipeline WebSocket disconnected')
        this.onConnectionChange?.(false)
        this.reconnect()
      }

      this.ws.onerror = (error) => {
        console.error('Pipeline WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to connect Pipeline WebSocket:', error)
      this.reconnect()
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

      console.log(`Attempting to reconnect Pipeline WebSocket in ${delay}ms (attempt ${this.reconnectAttempts})`)

      setTimeout(() => {
        if (this.onEvent) {
          this.connect(this.onEvent, this.onConnectionChange || undefined)
        }
      }, delay)
    } else {
      console.error('Max Pipeline WebSocket reconnection attempts reached')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }
}

export const pipelineWebSocket = new PipelineWebSocketService()

// ============================================
// ALERTS API
// ============================================

export interface Alert {
  _id?: string
  id?: string
  symbol: string
  type: 'price_above' | 'price_below' | 'percent_change' | 'volume_spike'
  condition: {
    value: number
    comparison?: 'above' | 'below' | 'crosses'
  }
  enabled: boolean
  notification: {
    push: boolean
    telegram: boolean
    sound: boolean
  }
  triggered: boolean
  triggered_at?: string
  trigger_price?: number
  created_at: string
}

export async function getAlerts(): Promise<Alert[]> {
  const response = await fetch(`${API_BASE_URL}/api/alerts`)
  const data = await response.json()
  return data.alerts || []
}

export async function createAlert(alert: Omit<Alert, '_id' | 'id' | 'triggered' | 'triggered_at' | 'created_at'>): Promise<{ success: boolean; alert?: Alert; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/api/alerts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(alert)
  })
  return response.json()
}

export async function updateAlert(alertId: string, updates: Partial<Alert>): Promise<{ success: boolean; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  })
  return response.json()
}

export async function deleteAlert(alertId: string): Promise<{ success: boolean; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}`, {
    method: 'DELETE'
  })
  return response.json()
}

export async function toggleAlert(alertId: string): Promise<{ success: boolean; enabled?: boolean; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/toggle`, {
    method: 'POST'
  })
  return response.json()
}

export async function checkAlerts(): Promise<{ triggered: Array<{ symbol: string; type: string; price: number; message: string }>; count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/alerts/check`)
  return response.json()
}