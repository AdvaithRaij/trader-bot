const API_BASE_URL = 'http://localhost:8001'

export interface StockData {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  marketCap?: number
  pe?: number
  sector?: string
  lastUpdated: string
}

export interface TradeLog {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  timestamp: string
  status: 'pending' | 'executed' | 'failed'
  pnl?: number
  reason?: string
}

export interface Portfolio {
  totalValue: number
  dayPnl: number
  dayPnlPercent: number
  positions: Position[]
  cash: number
}

export interface Position {
  symbol: string
  quantity: number
  avgPrice: number
  currentPrice: number
  pnl: number
  pnlPercent: number
  marketValue: number
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
    relevance?: number  // AI-provided relevance score (0-100)
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

export interface BotStatus {
  isRunning: boolean
  mode: 'demo' | 'live'
  lastUpdate: string
  tradesExecuted: number
  currentBalance: number
  dailyPnl: number
  systemHealth: 'healthy' | 'warning' | 'error'
}

export interface RiskMetrics {
  maxDrawdown: number
  currentDrawdown: number
  sharpeRatio: number
  winRate: number
  avgWin: number
  avgLoss: number
  totalTrades: number
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
  newsArticles?: NewsItem[]
  aiAnalysis?: {
    expectedMove?: string
    riskRewardRatio?: number
    stockScore?: number
  }
}

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

class ApiService {
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

  // Bot Status
  async getBotStatus(): Promise<BotStatus> {
    return this.request<BotStatus>('/status')
  }

  async startBot(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/start', { method: 'POST' })
  }

  async stopBot(): Promise<{ message: string }> {
    return this.request<{ message: string }>('/stop', { method: 'POST' })
  }

  // Screener
  async getScreenedStocks(): Promise<StockData[]> {
    return this.request<StockData[]>('/screener/stocks')
  }

  async getWatchlist(): Promise<StockData[]> {
    return this.request<StockData[]>('/screener/watchlist')
  }

  // Portfolio
  async getPortfolio(): Promise<Portfolio> {
    return this.request<Portfolio>('/portfolio')
  }

  async getPositions(): Promise<Position[]> {
    return this.request<Position[]>('/portfolio/positions')
  }

  // Trade Logs
  async getTradeLogs(limit?: number): Promise<TradeLog[]> {
    const query = limit ? `?limit=${limit}` : ''
    return this.request<TradeLog[]>(`/trades${query}`)
  }

  async getTradeHistory(days?: number): Promise<TradeLog[]> {
    const query = days ? `?days=${days}` : ''
    return this.request<TradeLog[]>(`/trades/history${query}`)
  }

  // News & Sentiment
  async getNews(params?: {
    page?: number
    limit?: number
    category?: string
    source?: string
    refresh?: boolean
  }): Promise<NewsResponse> {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append('page', params.page.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.category) queryParams.append('category', params.category)
    if (params?.source) queryParams.append('source', params.source)
    if (params?.refresh) queryParams.append('refresh', 'true')

    const query = queryParams.toString() ? `?${queryParams.toString()}` : ''
    return this.request<NewsResponse>(`/news${query}`)
  }

  async getNewsAnalysis(newsId: string): Promise<{
    newsId: string
    title: string
    summary: string
    source: string
    url: string
    publishedAt: string
    categories: string[]
    aiAnalysis: {
      impact: string
      sentiment: string
      relatedStocks: string[]
      analysis: string
      timeframe: string
      relevance?: number
    }
  }> {
    return this.request(`/news/${newsId}/analysis`)
  }

  async getLegacyNews(limit?: number): Promise<NewsItem[]> {
    const query = limit ? `?limit=${limit}` : ''
    return this.request<NewsItem[]>(`/sentiment/news${query}`)
  }

  async getSentimentAnalysis(symbol?: string): Promise<{
    overall: 'positive' | 'negative' | 'neutral'
    score: number
    confidence: number
    sources: number
  }> {
    const query = symbol ? `?symbol=${symbol}` : ''
    return this.request(`/sentiment/analysis${query}`)
  }

  // Risk Management
  async getRiskMetrics(): Promise<RiskMetrics> {
    return this.request<RiskMetrics>('/risk/metrics')
  }

  async updateRiskLimits(limits: {
    maxPositionSize?: number
    maxDailyLoss?: number
    maxDrawdown?: number
  }): Promise<{ message: string }> {
    return this.request<{ message: string }>('/risk/limits', {
      method: 'PUT',
      body: JSON.stringify(limits),
    })
  }

  // Trading Actions
  async executeTrade(trade: {
    symbol: string
    side: 'buy' | 'sell'
    quantity: number
    orderType?: 'market' | 'limit'
    price?: number
  }): Promise<{ orderId: string; message: string }> {
    return this.request<{ orderId: string; message: string }>('/trade/execute', {
      method: 'POST',
      body: JSON.stringify(trade),
    })
  }

  // AI Insights
  async getAIInsights(): Promise<{
    marketSentiment: string
    recommendations: Array<{
      symbol: string
      action: 'buy' | 'sell' | 'hold'
      confidence: number
      reasoning: string
    }>
    riskAssessment: string
  }> {
    return this.request('/ai/insights')
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health')
  }

  // Strategies
  async getStrategies(): Promise<{ strategies: Strategy[]; total: number }> {
    return this.request('/strategies')
  }

  async getStrategy(strategyId: string): Promise<{ strategy: Strategy }> {
    return this.request(`/strategies/${strategyId}`)
  }

  async toggleStrategy(strategyId: string): Promise<{ message: string; status: string }> {
    return this.request(`/strategies/${strategyId}/toggle`, { method: 'POST' })
  }

  async runStrategy(strategyId: string): Promise<{ message: string; signals: TradeSignal[] }> {
    return this.request(`/strategies/${strategyId}/run`, { method: 'POST' })
  }

  async generateSignal(symbol: string, strategyId?: string): Promise<{ signal: TradeSignal }> {
    return this.request('/signals/generate', {
      method: 'POST',
      body: JSON.stringify({ symbol, strategyId }),
    })
  }

  // Portfolio Summary (Phase 1)
  async getPortfolioSummary(): Promise<PortfolioSummary> {
    return this.request('/api/portfolio')
  }

  async getActivePositions(): Promise<ActivePosition[]> {
    return this.request('/api/portfolio/positions')
  }

  async getPerformanceMetrics(): Promise<{
    winRate: number
    totalPnl: number
    avgPnl: number
    profitFactor: number
    totalTrades: number
  }> {
    return this.request('/api/performance')
  }
}

export const apiService = new ApiService()

// WebSocket for real-time updates
export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private endpoint: string = '/ws'

  connect(onMessage: (data: any) => void, endpoint: string = '/ws') {
    this.endpoint = endpoint
    try {
      this.ws = new WebSocket(`ws://localhost:8001${endpoint}`)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.reconnect(onMessage)
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      this.reconnect(onMessage)
    }
  }

  private reconnect(onMessage: (data: any) => void) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

      console.log(`Attempting to reconnect WebSocket in ${delay}ms (attempt ${this.reconnectAttempts})`)

      setTimeout(() => {
        this.connect(onMessage, this.endpoint)
      }, delay)
    } else {
      console.error('Max WebSocket reconnection attempts reached')
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }
}

export const webSocketService = new WebSocketService()
