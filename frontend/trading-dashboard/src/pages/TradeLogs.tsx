import React, { useState, useEffect } from 'react'
import { 
  Calendar, 
  Filter, 
  Download, 
  TrendingUp, 
  TrendingDown, 
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw
} from 'lucide-react'
import { cn, formatCurrency, formatPercentage, formatDateTime, getPercentageColor } from '../lib/utils'
import type { Trade } from '../data/mockData'
import { mockTrades } from '../data/mockData'

export function TradeLogs() {
  const [trades, setTrades] = useState<Trade[]>(mockTrades)
  const [filteredTrades, setFilteredTrades] = useState<Trade[]>(mockTrades)
  const [statusFilter, setStatusFilter] = useState('all')
  const [sideFilter, setSideFilter] = useState('all')
  const [strategyFilter, setStrategyFilter] = useState('all')
  const [dateRange, setDateRange] = useState('today')
  const [isLoading, setIsLoading] = useState(false)

  const statuses = ['all', 'executed', 'pending', 'failed', 'cancelled']
  const sides = ['all', 'buy', 'sell']
  const strategies = ['all', ...Array.from(new Set(trades.map(trade => trade.strategy)))]

  useEffect(() => {
    let filtered = trades

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(trade => trade.status === statusFilter)
    }

    // Filter by side
    if (sideFilter !== 'all') {
      filtered = filtered.filter(trade => trade.side === sideFilter)
    }

    // Filter by strategy
    if (strategyFilter !== 'all') {
      filtered = filtered.filter(trade => trade.strategy === strategyFilter)
    }

    // Filter by date range
    const now = new Date()
    const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    
    if (dateRange === 'today') {
      filtered = filtered.filter(trade => new Date(trade.timestamp) >= startOfDay)
    } else if (dateRange === 'week') {
      const weekAgo = new Date(startOfDay.getTime() - 7 * 24 * 60 * 60 * 1000)
      filtered = filtered.filter(trade => new Date(trade.timestamp) >= weekAgo)
    }

    setFilteredTrades(filtered)
  }, [trades, statusFilter, sideFilter, strategyFilter, dateRange])

  const handleRefresh = async () => {
    setIsLoading(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsLoading(false)
  }

  const handleExport = () => {
    // Export trades to CSV
    const csv = [
      ['ID', 'Symbol', 'Side', 'Quantity', 'Price', 'Timestamp', 'Status', 'P&L', 'Fees', 'Strategy'].join(','),
      ...filteredTrades.map(trade => [
        trade.id,
        trade.symbol,
        trade.side,
        trade.quantity,
        trade.price,
        trade.timestamp,
        trade.status,
        trade.pnl || 0,
        trade.fees,
        trade.strategy
      ].join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `trades_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'executed':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-400" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />
      case 'cancelled':
        return <AlertCircle className="w-4 h-4 text-gray-400" />
      default:
        return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'executed': return 'text-green-400 bg-green-500/20'
      case 'pending': return 'text-yellow-400 bg-yellow-500/20'
      case 'failed': return 'text-red-400 bg-red-500/20'
      case 'cancelled': return 'text-gray-400 bg-gray-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  // Calculate summary stats
  const executedTrades = filteredTrades.filter(t => t.status === 'executed')
  const totalPnL = executedTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0)
  const totalFees = executedTrades.reduce((sum, trade) => sum + trade.fees, 0)
  const winningTrades = executedTrades.filter(t => (t.pnl || 0) > 0).length
  const winRate = executedTrades.length > 0 ? (winningTrades / executedTrades.length) * 100 : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mobile-stack">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl sm:text-3xl font-bold gradient-text">Trade Logs</h1>
          <p className="text-gray-400 mt-1 text-sm sm:text-base">Track your trading performance and history</p>
        </div>
        <div className="flex items-center space-x-2 sm:space-x-3 self-start sm:self-auto">
          <button
            onClick={handleExport}
            className="flex items-center space-x-2 px-3 sm:px-4 py-2 glass rounded-lg hover:bg-white/10 transition-colors touch-friendly"
          >
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export</span>
          </button>
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3 sm:px-4 py-2 glass rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50 touch-friendly"
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="glass-card p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-400">Total P&L</p>
              <p className={cn("text-lg sm:text-2xl font-bold mt-1", getPercentageColor(totalPnL))}>
                {formatCurrency(totalPnL)}
              </p>
            </div>
            <div className={cn(
              "p-2 sm:p-3 rounded-lg flex-shrink-0",
              totalPnL >= 0 ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
            )}>
              {totalPnL >= 0 ? <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6" /> : <TrendingDown className="w-5 h-5 sm:w-6 sm:h-6" />}
            </div>
          </div>
        </div>

        <div className="glass-card p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-400">Win Rate</p>
              <p className="text-lg sm:text-2xl font-bold text-white mt-1">{winRate.toFixed(1)}%</p>
              <p className="text-xs sm:text-sm text-gray-400">{winningTrades}/{executedTrades.length} trades</p>
            </div>
            <div className="p-2 sm:p-3 rounded-lg bg-blue-500/20 text-blue-400 flex-shrink-0">
              <CheckCircle className="w-5 h-5 sm:w-6 sm:h-6" />
            </div>
          </div>
        </div>

        <div className="glass-card p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-400">Total Trades</p>
              <p className="text-lg sm:text-2xl font-bold text-white mt-1">{filteredTrades.length}</p>
              <p className="text-xs sm:text-sm text-gray-400">Executed: {executedTrades.length}</p>
            </div>
            <div className="p-2 sm:p-3 rounded-lg bg-purple-500/20 text-purple-400 flex-shrink-0">
              <Calendar className="w-5 h-5 sm:w-6 sm:h-6" />
            </div>
          </div>
        </div>

        <div className="glass-card p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-400">Total Fees</p>
              <p className="text-lg sm:text-2xl font-bold text-red-400 mt-1">{formatCurrency(totalFees)}</p>
            </div>
            <div className="p-2 sm:p-3 rounded-lg bg-red-500/20 text-red-400 flex-shrink-0">
              <TrendingDown className="w-5 h-5 sm:w-6 sm:h-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row flex-wrap items-start sm:items-center gap-3 sm:gap-4">
          {/* Date Range */}
          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <Calendar className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="flex-1 sm:flex-none px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly"
            >
              <option value="today" className="bg-gray-800">Today</option>
              <option value="week" className="bg-gray-800">This Week</option>
              <option value="month" className="bg-gray-800">This Month</option>
              <option value="all" className="bg-gray-800">All Time</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="flex-1 sm:flex-none px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly"
            >
              {statuses.map(status => (
                <option key={status} value={status} className="bg-gray-800">
                  {status === 'all' ? 'All Status' : status.charAt(0).toUpperCase() + status.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Side Filter */}
          <select
            value={sideFilter}
            onChange={(e) => setSideFilter(e.target.value)}
            className="w-full sm:w-auto px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly"
          >
            {sides.map(side => (
              <option key={side} value={side} className="bg-gray-800">
                {side === 'all' ? 'Buy & Sell' : side.charAt(0).toUpperCase() + side.slice(1)}
              </option>
            ))}
          </select>

          {/* Strategy Filter */}
          <select
            value={strategyFilter}
            onChange={(e) => setStrategyFilter(e.target.value)}
            className="w-full sm:w-auto px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly"
          >
            {strategies.map(strategy => (
              <option key={strategy} value={strategy} className="bg-gray-800">
                {strategy === 'all' ? 'All Strategies' : strategy}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Trade Table */}
      <div className="glass-card overflow-hidden">
        <div className="px-4 sm:px-6 py-4 border-b border-white/10">
          <h3 className="text-lg font-semibold text-white">
            {filteredTrades.length} trades found
          </h3>
        </div>

        {/* Mobile Card View */}
        <div className="block sm:hidden">
          {filteredTrades.map((trade) => (
            <div key={trade.id} className="p-4 border-b border-white/5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-white">{trade.symbol}</span>
                  <span className={cn(
                    "px-2 py-1 text-xs font-medium rounded-full",
                    trade.side === 'buy' 
                      ? "bg-green-500/20 text-green-400" 
                      : "bg-red-500/20 text-red-400"
                  )}>
                    {trade.side.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(trade.status)}
                  <span className={cn(
                    "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                    getStatusColor(trade.status)
                  )}>
                    {trade.status.toUpperCase()}
                  </span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-gray-400">Quantity</p>
                  <p className="text-white font-medium">{trade.quantity} shares</p>
                </div>
                <div>
                  <p className="text-gray-400">Price</p>
                  <p className="text-white font-medium">{formatCurrency(trade.price)}</p>
                </div>
                <div>
                  <p className="text-gray-400">Total Value</p>
                  <p className="text-white font-medium">{formatCurrency(trade.price * trade.quantity)}</p>
                </div>
                <div>
                  <p className="text-gray-400">P&L</p>
                  {trade.pnl !== undefined ? (
                    <p className={cn("font-medium", getPercentageColor(trade.pnl))}>
                      {trade.pnl > 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                    </p>
                  ) : (
                    <p className="text-gray-400">-</p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center justify-between text-xs">
                <div>
                  <span className="text-gray-400">Strategy: </span>
                  <span className="text-white">{trade.strategy}</span>
                </div>
                <div className="text-gray-400">
                  {formatDateTime(new Date(trade.timestamp))}
                </div>
              </div>
            </div>
          ))}
          
          {filteredTrades.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-400">No trades found matching your criteria</p>
            </div>
          )}
        </div>

        {/* Desktop Table View */}
        <div className="hidden sm:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">Trade</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">Price</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">P&L</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">Fees</th>
                <th className="text-center px-6 py-4 text-sm font-medium text-gray-400">Status</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">Strategy</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">Time</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.map((trade) => (
                <tr 
                  key={trade.id} 
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="px-6 py-4">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-white">{trade.symbol}</span>
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
                        {trade.quantity} shares @ {formatCurrency(trade.price)}
                      </div>
                      {trade.orderId && (
                        <div className="text-xs text-gray-500">ID: {trade.orderId}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="font-medium text-white">
                      {formatCurrency(trade.price * trade.quantity)}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {trade.pnl !== undefined ? (
                      <div className={cn("font-medium", getPercentageColor(trade.pnl))}>
                        {trade.pnl > 0 ? '+' : ''}{formatCurrency(trade.pnl)}
                      </div>
                    ) : (
                      <div className="text-gray-400">-</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="text-red-400">{formatCurrency(trade.fees)}</div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center space-x-2">
                      {getStatusIcon(trade.status)}
                      <span className={cn(
                        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                        getStatusColor(trade.status)
                      )}>
                        {trade.status.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-white">{trade.strategy}</div>
                    <div className="text-xs text-gray-400">
                      Confidence: {trade.confidence}%
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="text-white text-sm">
                      {formatDateTime(new Date(trade.timestamp))}
                    </div>
                    {trade.executionTime > 0 && (
                      <div className="text-xs text-gray-400">
                        {trade.executionTime}ms
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredTrades.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-400">No trades found matching your criteria</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
