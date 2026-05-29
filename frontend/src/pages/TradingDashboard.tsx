import React, { useState, useEffect } from 'react'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  AlertCircle,
  Play,
  Pause,
  Newspaper,
  Clock,
  ExternalLink,
  CheckCircle
} from 'lucide-react'
import { cn, formatCurrency, formatPercentage, getPercentageColor, formatDateTime } from '../lib/utils'
import { apiService } from '../lib/trading-api'
import type { PortfolioSummary, ActivePosition, TradeSignal, NewsItem } from '../lib/trading-api'

interface StatsCardProps {
  title: string
  value: string
  change?: string
  changePercent?: number
  icon: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  className?: string
}

function StatsCard({ title, value, change, changePercent, icon, trend = 'neutral', className }: StatsCardProps) {
  return (
    <div className={cn("glass-card p-4 sm:p-6", className)}>
      <div className="flex items-center justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-xs sm:text-sm font-medium text-gray-400 truncate">{title}</p>
          <p className="text-lg sm:text-2xl font-bold text-white mt-1 break-all">{value}</p>
          {change && (
            <div className="flex items-center mt-2 space-x-1">
              {trend === 'up' && <ArrowUpRight className="w-3 h-3 sm:w-4 sm:h-4 text-green-400 flex-shrink-0" />}
              {trend === 'down' && <ArrowDownRight className="w-3 h-3 sm:w-4 sm:h-4 text-red-400 flex-shrink-0" />}
              <span className={cn("text-xs sm:text-sm font-medium", getPercentageColor(changePercent || 0))}>
                {change}
              </span>
              {changePercent !== undefined && (
                <span className={cn("text-xs sm:text-sm", getPercentageColor(changePercent))}>
                  ({formatPercentage(changePercent)})
                </span>
              )}
            </div>
          )}
        </div>
        <div className={cn(
          "p-2 sm:p-3 rounded-lg flex-shrink-0 ml-2",
          trend === 'up' && "bg-green-500/20 text-green-400",
          trend === 'down' && "bg-red-500/20 text-red-400",
          trend === 'neutral' && "bg-blue-500/20 text-blue-400"
        )}>
          {icon}
        </div>
      </div>
    </div>
  )
}

export function TradingDashboard() {
  const [isLoading, setIsLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null)
  const [positions, setPositions] = useState<ActivePosition[]>([])
  const [recentSignals, setRecentSignals] = useState<TradeSignal[]>([])
  const [error, setError] = useState<string | null>(null)
  const [hotNews, setHotNews] = useState<NewsItem[]>([])
  const [todayTrades, setTodayTrades] = useState<any[]>([])

  const loadData = async () => {
    try {
      setError(null)

      // Load portfolio summary
      const portfolioData = await apiService.getPortfolioSummary()
      setPortfolio(portfolioData)

      // Load active positions
      const positionsData = await apiService.getActivePositions()
      setPositions(positionsData)

      // Load hot news
      await fetchHotNews()

      // Load today's trades
      await fetchTodayTrades()

      // Load recent signals (run all strategies)
      // For now, we'll just show empty - will be populated when strategies run

    } catch (err) {
      console.error('Error loading dashboard data:', err)
      setError('Failed to load dashboard data. Make sure the backend is running.')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchHotNews = async () => {
    try {
      const response = await apiService.getNews({
        page: 1,
        limit: 5, // Only fetch 5 latest news items
        refresh: false
      })

      const transformedNews = response.news.map(item => ({
        ...item,
        sentiment: (item.aiAnalysis?.sentiment.toLowerCase() || 'neutral') as 'positive' | 'negative' | 'neutral',
        sentimentScore: item.aiAnalysis?.sentiment === 'POSITIVE' ? 0.7 :
                       item.aiAnalysis?.sentiment === 'NEGATIVE' ? -0.7 : 0,
        symbols: item.aiAnalysis?.relatedStocks || [],
        category: (item.categories?.[0] || 'market') as any,
        content: item.summary,
        confidence: item.aiAnalysis?.relevance || 50,
        readTime: 3
      }))

      setHotNews(transformedNews)
    } catch (error) {
      console.error('Error fetching news:', error)
    }
  }

  const fetchTodayTrades = async () => {
    try {
      const response = await apiService.getTodayTrades()
      setTodayTrades(response.trades || [])
    } catch (error) {
      console.error('Error fetching trades:', error)
    }
  }

  useEffect(() => {
    loadData()

    // Refresh news every 1 hour
    const newsInterval = setInterval(() => {
      fetchHotNews()
    }, 3600000) // 1 hour in milliseconds

    return () => clearInterval(newsInterval)
  }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    await loadData()
    setRefreshing(false)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="flex items-center space-x-3">
          <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
          <span className="text-lg text-gray-300">Loading trading dashboard...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="glass-card p-6 max-w-md">
          <div className="flex items-center space-x-3 text-red-400 mb-4">
            <AlertCircle className="w-6 h-6" />
            <span className="text-lg font-semibold">Error</span>
          </div>
          <p className="text-gray-300 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const getTrend = (value: number): 'up' | 'down' | 'neutral' => {
    if (value > 0) return 'up'
    if (value < 0) return 'down'
    return 'neutral'
  }

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return <TrendingUp className="w-4 h-4 text-green-400" />
      case 'negative':
        return <TrendingDown className="w-4 h-4 text-red-400" />
      default:
        return <div className="w-4 h-4 rounded-full bg-gray-400" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mobile-stack">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl sm:text-3xl font-bold gradient-text">Trading Dashboard</h1>
          <p className="text-gray-400 mt-1 text-sm sm:text-base">Monitor your autonomous trading bot performance</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center space-x-2 px-3 sm:px-4 py-2 glass rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50 touch-friendly self-start sm:self-auto"
        >
          <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatsCard
          title="Total Capital"
          value={formatCurrency(portfolio?.totalCapital || 0)}
          change={formatCurrency(portfolio?.totalPnl || 0)}
          changePercent={portfolio?.totalPnlPercent || 0}
          icon={<DollarSign className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend={getTrend(portfolio?.totalPnl || 0)}
        />
        <StatsCard
          title="Today's P&L"
          value={formatCurrency(portfolio?.todayPnl || 0)}
          changePercent={portfolio?.todayPnlPercent || 0}
          icon={<TrendingUp className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend={getTrend(portfolio?.todayPnl || 0)}
        />
        <StatsCard
          title="Active Positions"
          value={`${portfolio?.openPositions || 0}/${portfolio?.maxPositions || 5}`}
          icon={<BarChart3 className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend="neutral"
        />
        <StatsCard
          title="Win Rate"
          value={`${portfolio?.winRate || 0}%`}
          change={`${portfolio?.totalTrades || 0} trades`}
          icon={<Activity className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend={getTrend((portfolio?.winRate || 0) - 50)}
        />
      </div>

      {/* Portfolio Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Available Cash</h3>
          <p className="text-2xl font-bold text-white">{formatCurrency(portfolio?.availableCash || 0)}</p>
        </div>
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Allocated Capital</h3>
          <p className="text-2xl font-bold text-white">{formatCurrency(portfolio?.allocatedCapital || 0)}</p>
        </div>
        <div className="glass-card p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Current Drawdown</h3>
          <p className={cn("text-2xl font-bold", getPercentageColor(-(portfolio?.currentDrawdown || 0)))}>
            {formatPercentage(portfolio?.currentDrawdown || 0)}
          </p>
          <p className="text-xs text-gray-400 mt-1">Max: {formatPercentage(portfolio?.maxDrawdown || 0)}</p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 sm:gap-6 items-start">
        {/* Left Column - Active Positions & Recent Signals */}
        <div className="xl:col-span-2 space-y-6 flex flex-col">

          {/* Active Positions */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-white mb-6">
              Active Positions ({positions.length}/{portfolio?.maxPositions || 5})
            </h3>
            {positions.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No active positions</p>
                <p className="text-sm mt-1">Strategies will generate signals automatically</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-400 border-b border-white/10">
                      <th className="pb-3">Symbol</th>
                      <th className="pb-3">Direction</th>
                      <th className="pb-3">Entry</th>
                      <th className="pb-3">Current</th>
                      <th className="pb-3">Qty</th>
                      <th className="pb-3">P&L</th>
                      <th className="pb-3">SL / TP</th>
                      <th className="pb-3">Strategy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((position, index) => (
                      <tr key={index} className="border-b border-white/5 hover:bg-white/5">
                        <td className="py-3 font-medium text-white">{position.symbol}</td>
                        <td className="py-3">
                          <span className={cn(
                            "px-2 py-1 text-xs font-medium rounded-full",
                            position.direction === 'BUY'
                              ? "bg-green-500/20 text-green-400"
                              : "bg-red-500/20 text-red-400"
                          )}>
                            {position.direction}
                          </span>
                        </td>
                        <td className="py-3 text-gray-300">{formatCurrency(position.entryPrice)}</td>
                        <td className="py-3 text-gray-300">{formatCurrency(position.currentPrice)}</td>
                        <td className="py-3 text-gray-300">{position.quantity}</td>
                        <td className="py-3">
                          <div className={cn("font-medium", getPercentageColor(position.pnl))}>
                            {formatCurrency(position.pnl)}
                          </div>
                          <div className={cn("text-xs", getPercentageColor(position.pnlPercent))}>
                            {formatPercentage(position.pnlPercent)}
                          </div>
                        </td>
                        <td className="py-3 text-sm text-gray-300">
                          <div>{formatCurrency(position.stopLoss)}</div>
                          <div>{formatCurrency(position.target1)}</div>
                        </td>
                        <td className="py-3 text-sm text-gray-400">{position.strategyName}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Recent Signals - Shortened */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Signals</h3>
            {recentSignals.length === 0 ? (
              <div className="text-center py-6 text-gray-400">
                <Activity className="w-10 h-10 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No recent signals</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentSignals.slice(0, 3).map((signal, index) => (
                  <div key={index} className="p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-base font-bold text-white">{signal.symbol}</span>
                        <span className={cn(
                          "px-2 py-0.5 text-xs font-medium rounded-full",
                          signal.direction === 'BUY'
                            ? "bg-green-500/20 text-green-400"
                            : "bg-red-500/20 text-red-400"
                        )}>
                          {signal.direction}
                        </span>
                      </div>
                      <span className={cn(
                        "text-xs font-medium",
                        signal.confidence >= 80 ? "text-green-400" :
                        signal.confidence >= 60 ? "text-yellow-400" : "text-red-400"
                      )}>
                        {signal.confidence}%
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-xs">
                      <div>
                        <span className="text-gray-400">Entry: </span>
                        <span className="text-white font-medium">{formatCurrency(signal.entryPrice)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">SL: </span>
                        <span className="text-red-400 font-medium">{formatCurrency(signal.stopLoss)}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Target: </span>
                        <span className="text-green-400 font-medium">{formatCurrency(signal.target1)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Hot News */}
        <div className="xl:sticky xl:top-6">
          {/* Hot News Section */}
          <div className="glass-card p-4 sm:p-6 flex flex-col h-[calc(100vh-200px)] max-h-[800px]">
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                <Newspaper className="w-5 h-5 text-blue-400" />
                <span>Hot News</span>
              </h3>
              <span className="text-xs text-gray-400">Updates hourly</span>
            </div>
            {hotNews.length > 0 ? (
              <div className="space-y-4 overflow-y-auto pr-2 flex-1 scrollbar-thin scrollbar-thumb-blue-500/50 scrollbar-track-white/5">
                {hotNews.map((item) => (
                  <div key={item.id} className="border-b border-white/10 pb-4 last:border-0 last:pb-0">
                    <div className="flex items-start space-x-2 mb-2">
                      {getSentimentIcon(item.sentiment)}
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-white line-clamp-2 leading-tight">
                          {item.title}
                        </h4>
                      </div>
                    </div>
                    <p className="text-xs text-gray-400 line-clamp-2 mb-2">
                      {item.summary}
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <Clock className="w-3 h-3" />
                        <span>{formatDateTime(new Date(item.publishedAt))}</span>
                      </div>
                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-400 hover:text-blue-300 flex items-center space-x-1"
                        >
                          <span>Read</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                    {item.symbols && item.symbols.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {item.symbols.slice(0, 3).map((symbol, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-500/20 text-blue-400"
                          >
                            {symbol}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400 flex-1 flex flex-col items-center justify-center">
                <Newspaper className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No news available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

