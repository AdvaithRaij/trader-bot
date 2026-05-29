import React, { useState, useEffect } from 'react'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw
} from 'lucide-react'
import { AreaChart, Area, PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { cn, formatCurrency, formatPercentage, getPercentageColor } from '../lib/utils'
import { portfolioData, sectorData, topPerformers, recentTrades } from '../data/mockData'

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

export function Dashboard() {
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    // Simulate loading
    setTimeout(() => {}, 500)
  }, [])

  const handleRefresh = () => {
    setRefreshing(true)
    setTimeout(() => setRefreshing(false), 1000)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="flex items-center space-x-3">
          <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
          <span className="text-lg text-gray-300">Loading dashboard...</span>
        </div>
      </div>
    )
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
          title="Portfolio Value"
          value={formatCurrency(portfolioValue)}
          change={dayPnL > 0 ? `+${formatCurrency(dayPnL)}` : formatCurrency(dayPnL)}
          changePercent={portfolioValue > 0 ? (dayPnL / portfolioValue) * 100 : 0}
          icon={<DollarSign className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend={dayPnL > 0 ? "up" : dayPnL < 0 ? "down" : "neutral"}
        />
        <StatsCard
          title="Day P&L"
          value={formatCurrency(Math.abs(dayPnL))}
          change={`${todayTrades.length} trades`}
          changePercent={portfolioValue > 0 ? (dayPnL / portfolioValue) * 100 : 0}
          icon={<TrendingUp className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend={dayPnL > 0 ? "up" : dayPnL < 0 ? "down" : "neutral"}
        />
        <StatsCard
          title="Active Positions"
          value={activePositions.toString()}
          change={`${todayTrades.length} total today`}
          icon={<BarChart3 className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend="neutral"
        />
        <StatsCard
          title="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          change={winRate > 50 ? "Above target" : "Below target"}
          icon={<Activity className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend={winRate > 50 ? "up" : "down"}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 sm:gap-6">
        {/* Left Column - Portfolio Performance & Active Positions */}
        <div className="xl:col-span-2 space-y-6">
          {/* Portfolio Performance Chart */}
          <div className="glass-card p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6 mobile-stack">
              <h3 className="text-lg font-semibold text-white">Portfolio Performance</h3>
              <div className="flex items-center space-x-2 text-sm text-gray-400">
                <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
                <span>Today</span>
              </div>
            </div>
            <div className="h-48 sm:h-64 chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={portfolioData}>
                  <defs>
                    <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis
                    dataKey="time"
                    stroke="#6B7280"
                    fontSize={12}
                  />
                  <YAxis
                    stroke="#6B7280"
                    fontSize={12}
                    tickFormatter={(value) => formatCurrency(value, 'INR').replace('₹', '₹')}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 15, 35, 0.95)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '8px',
                      color: 'white'
                    }}
                    formatter={(value: number, name: string) => [
                      formatCurrency(value),
                      name === 'value' ? 'Portfolio Value' : 'P&L'
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    fill="url(#portfolioGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Active Positions Section */}
          <div className="glass-card p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Active Positions ({activePositions})</h3>
              <span className="text-sm text-gray-400">Live</span>
            </div>
            {activeTrades.length > 0 ? (
              <div className="space-y-3">
                {activeTrades.map((trade) => (
                  <div key={trade.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-lg transition-colors border border-white/10">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-white">{trade.symbol}</span>
                        <span className={cn(
                          "px-2 py-0.5 text-xs font-medium rounded-full",
                          trade.side === 'buy'
                            ? "bg-green-500/20 text-green-400"
                            : "bg-red-500/20 text-red-400"
                        )}>
                          {trade.side.toUpperCase()}
                        </span>
                        {trade.status === 'executed' && (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        )}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        {trade.quantity} @ {formatCurrency(trade.price)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={cn(
                        "font-medium",
                        getPercentageColor(trade.pnl || 0)
                      )}>
                        {trade.pnl ? formatCurrency(trade.pnl) : '—'}
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(trade.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No active positions</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Hot News & Sector Allocation */}
        <div className="space-y-6">
          {/* Hot News Section */}
          <div className="glass-card p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
                <Newspaper className="w-5 h-5 text-blue-400" />
                <span>Hot News</span>
              </h3>
              <span className="text-xs text-gray-400">Updates hourly</span>
            </div>
            {hotNews.length > 0 ? (
              <div className="space-y-4">
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
              <div className="text-center py-8 text-gray-400">
                <Newspaper className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No news available</p>
              </div>
            )}
          </div>

          {/* Sector Allocation */}
          <div className="glass-card p-6">
            <h3 className="text-lg font-semibold text-white mb-6">Sector Allocation</h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart>
                  <Pie
                    data={sectorData}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={60}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {sectorData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(15, 15, 35, 0.95)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '8px',
                      color: 'white'
                    }}
                    formatter={(value: number) => [`${value}%`, 'Allocation']}
                  />
                </RechartsPieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2 mt-4">
              {sectorData.map((sector, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: sector.color }}
                    />
                    <span className="text-gray-300">{sector.name}</span>
                  </div>
                  <span className="text-white font-medium">{sector.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tables Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Performers */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Top Performers</h3>
          <div className="space-y-3">
            {topPerformers.map((stock, index) => (
              <div key={index} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-lg transition-colors">
                <div>
                  <div className="font-medium text-white">{stock.symbol}</div>
                  <div className="text-sm text-gray-400">{formatCurrency(stock.price)}</div>
                </div>
                <div className="text-right">
                  <div className={cn("font-medium", getPercentageColor(stock.changePercent))}>
                    {formatPercentage(stock.changePercent)}
                  </div>
                  <div className={cn("text-sm", getPercentageColor(stock.change))}>
                    {stock.change > 0 ? '+' : ''}{formatCurrency(stock.change)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Trades */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Recent Trades</h3>
          <div className="space-y-3">
            {recentTrades.map((trade) => (
              <div key={trade.id} className="flex items-center justify-between p-3 hover:bg-white/5 rounded-lg transition-colors">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-white">{trade.symbol}</span>
                    <span className={cn(
                      "px-2 py-1 text-xs font-medium rounded-full",
                      trade.side === 'buy' 
                        ? "bg-green-500/20 text-green-400" 
                        : "bg-red-500/20 text-red-400"
                    )}>
                      {trade.side.toUpperCase()}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">
                    {trade.quantity} @ {formatCurrency(trade.price)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-300">{trade.time}</div>
                  <div className={cn(
                    "text-xs font-medium",
                    trade.status === 'executed' ? "text-green-400" : "text-yellow-400"
                  )}>
                    {trade.status.toUpperCase()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
