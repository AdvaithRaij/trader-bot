const API_BASE_URL = 'http://localhost:8000'

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
  async getNews(limit?: number): Promise<NewsItem[]> {
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
}

export const apiService = new ApiService()

// WebSocket for real-time updates
export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(onMessage: (data: any) => void) {
    try {
      this.ws = new WebSocket('ws://localhost:8000/ws')

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
        this.connect(onMessage)
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
