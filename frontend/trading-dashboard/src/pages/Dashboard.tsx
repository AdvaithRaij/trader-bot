import React, { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  BarChart3, 
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw
} from 'lucide-react'
import { LineChart, Line, AreaChart, Area, PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { cn, formatCurrency, formatPercentage, getPercentageColor } from '../lib/utils'
import { portfolioData, sectorData, topPerformers, recentTrades, userProfile } from '../data/mockData'

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
  const [isLoading, setIsLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    // Simulate initial data loading
    const timer = setTimeout(() => setIsLoading(false), 1000)
    return () => clearTimeout(timer)
  }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setRefreshing(false)
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
          <p className="text-gray-400 mt-1 text-sm sm:text-base">Monitor your portfolio performance and market activity</p>
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
          value={formatCurrency(131247)}
          change="+₹6,247"
          changePercent={5.00}
          icon={<DollarSign className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend="up"
        />
        <StatsCard
          title="Day P&L"
          value={formatCurrency(6247)}
          change="+₹247"
          changePercent={4.12}
          icon={<TrendingUp className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend="up"
        />
        <StatsCard
          title="Active Positions"
          value="12"
          change="+2"
          icon={<BarChart3 className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend="up"
        />
        <StatsCard
          title="Win Rate"
          value="78.5%"
          change="+2.3%"
          icon={<Activity className="w-5 h-5 sm:w-6 sm:h-6" />}
          trend="up"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 sm:gap-6">
        {/* Portfolio Performance Chart */}
        <div className="xl:col-span-2 glass-card p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6 mobile-stack">
            <h3 className="text-lg font-semibold text-white">Portfolio Performance</h3>
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
              <span>Today</span>
            </div>
          </div>
          <div className="h-48 sm:h-64 lg:h-80 chart-container">
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

        {/* Sector Allocation */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Sector Allocation</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPieChart>
                <Pie
                  data={sectorData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
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
