import React, { useState, useEffect } from 'react'
import { Search, Filter, TrendingUp, TrendingDown, BarChart3, RefreshCw } from 'lucide-react'
import { cn, formatCurrency, formatPercentage, getPercentageColor } from '../lib/utils'
import type { Stock } from '../data/mockData'
import { mockStocks } from '../data/mockData'

export function Screener() {
  const [stocks, setStocks] = useState<Stock[]>(mockStocks)
  const [filteredStocks, setFilteredStocks] = useState<Stock[]>(mockStocks)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSector, setSelectedSector] = useState('all')
  const [selectedSignal, setSelectedSignal] = useState('all')
  const [isLoading, setIsLoading] = useState(false)

  const sectors = ['all', ...Array.from(new Set(stocks.map(stock => stock.sector)))]
  const signals = ['all', 'buy', 'sell', 'neutral']

  useEffect(() => {
    let filtered = stocks

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(stock => 
        stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
        stock.name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Filter by sector
    if (selectedSector !== 'all') {
      filtered = filtered.filter(stock => stock.sector === selectedSector)
    }

    // Filter by signal
    if (selectedSignal !== 'all') {
      filtered = filtered.filter(stock => stock.macdSignal === selectedSignal)
    }

    setFilteredStocks(filtered)
  }, [stocks, searchTerm, selectedSector, selectedSignal])

  const handleRefresh = async () => {
    setIsLoading(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsLoading(false)
  }

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'buy': return 'text-green-400 bg-green-500/20'
      case 'sell': return 'text-red-400 bg-red-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  const formatVolume = (volume: number) => {
    if (volume >= 10000000) return `${(volume / 10000000).toFixed(1)}Cr`
    if (volume >= 100000) return `${(volume / 100000).toFixed(1)}L`
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`
    return volume.toString()
  }

  const formatMarketCap = (marketCap: number) => {
    if (marketCap >= 1000000000000) return `₹${(marketCap / 1000000000000).toFixed(1)}T`
    if (marketCap >= 10000000000) return `₹${(marketCap / 10000000000).toFixed(1)}B`
    if (marketCap >= 10000000) return `₹${(marketCap / 10000000).toFixed(1)}Cr`
    return formatCurrency(marketCap)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mobile-stack">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl sm:text-3xl font-bold gradient-text">Stock Screener</h1>
          <p className="text-gray-400 mt-1 text-sm sm:text-base">Discover and analyze trading opportunities</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="flex items-center space-x-2 px-3 sm:px-4 py-2 glass rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50 touch-friendly self-start sm:self-auto"
        >
          <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
          <span className="hidden sm:inline">Refresh Data</span>
        </button>
      </div>

      {/* Filters */}
      <div className="glass-card p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row flex-wrap items-start sm:items-center gap-3 sm:gap-4">
          {/* Search */}
          <div className="flex-1 min-w-0 w-full sm:min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search stocks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 touch-friendly"
              />
            </div>
          </div>

          {/* Sector Filter */}
          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="flex-1 sm:flex-none px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly"
            >
              {sectors.map(sector => (
                <option key={sector} value={sector} className="bg-gray-800">
                  {sector === 'all' ? 'All Sectors' : sector}
                </option>
              ))}
            </select>
          </div>

          {/* Signal Filter */}
          <div className="flex items-center space-x-2 w-full sm:w-auto">
            <BarChart3 className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <select
              value={selectedSignal}
              onChange={(e) => setSelectedSignal(e.target.value)}
              className="flex-1 sm:flex-none px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly"
            >
              {signals.map(signal => (
                <option key={signal} value={signal} className="bg-gray-800">
                  {signal === 'all' ? 'All Signals' : signal.charAt(0).toUpperCase() + signal.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="glass-card overflow-hidden">
        <div className="px-4 sm:px-6 py-4 border-b border-white/10">
          <h3 className="text-lg font-semibold text-white">
            Found {filteredStocks.length} stocks
          </h3>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center space-x-3">
              <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
              <span className="text-lg text-gray-300">Scanning market data...</span>
            </div>
          </div>
        ) : (
          <>
            {/* Mobile Card View */}
            <div className="block sm:hidden">
              {filteredStocks.map((stock) => (
                <div key={stock.symbol} className="p-4 border-b border-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="font-semibold text-white">{stock.symbol}</div>
                      <div className="text-sm text-gray-400 truncate">{stock.name}</div>
                      <div className="text-xs text-gray-500">{stock.sector}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium text-white">{formatCurrency(stock.price)}</div>
                      <div className={cn("text-sm font-medium", getPercentageColor(stock.changePercent))}>
                        {formatPercentage(stock.changePercent)}
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-gray-400">Volume</p>
                      <p className="text-white font-medium">{formatVolume(stock.volume)}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Market Cap</p>
                      <p className="text-white font-medium">{formatMarketCap(stock.marketCap)}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">P/E Ratio</p>
                      <p className="text-white font-medium">{stock.pe.toFixed(1)}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">RSI</p>
                      <p className={cn(
                        "font-medium",
                        stock.rsi > 70 ? "text-red-400" : stock.rsi < 30 ? "text-green-400" : "text-white"
                      )}>
                        {stock.rsi.toFixed(1)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className={cn(
                      "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium",
                      getSignalColor(stock.macdSignal)
                    )}>
                      {stock.macdSignal.toUpperCase()}
                    </span>
                    <div className={cn("text-sm", getPercentageColor(stock.change))}>
                      {stock.change > 0 ? '+' : ''}{formatCurrency(stock.change)}
                    </div>
                  </div>
                </div>
              ))}
              
              {filteredStocks.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-400">No stocks found matching your criteria</p>
                </div>
              )}
            </div>

            {/* Desktop Table View */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left px-6 py-4 text-sm font-medium text-gray-400">Stock</th>
                    <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">Price</th>
                    <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">Change</th>
                    <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">Volume</th>
                    <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">Market Cap</th>
                    <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">P/E</th>
                    <th className="text-right px-6 py-4 text-sm font-medium text-gray-400">RSI</th>
                    <th className="text-center px-6 py-4 text-sm font-medium text-gray-400">Signal</th>
                  </tr>
                </thead>
              <tbody>
                {filteredStocks.map((stock, index) => (
                  <tr 
                    key={stock.symbol} 
                    className="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
                  >
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-semibold text-white">{stock.symbol}</div>
                        <div className="text-sm text-gray-400 truncate max-w-48">{stock.name}</div>
                        <div className="text-xs text-gray-500">{stock.sector}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="font-medium text-white">{formatCurrency(stock.price)}</div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className={cn("font-medium", getPercentageColor(stock.changePercent))}>
                        {formatPercentage(stock.changePercent)}
                      </div>
                      <div className={cn("text-sm", getPercentageColor(stock.change))}>
                        {stock.change > 0 ? '+' : ''}{formatCurrency(stock.change)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="text-white">{formatVolume(stock.volume)}</div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="text-white">{formatMarketCap(stock.marketCap)}</div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="text-white">{stock.pe.toFixed(1)}</div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className={cn(
                        "text-white",
                        stock.rsi > 70 ? "text-red-400" : stock.rsi < 30 ? "text-green-400" : ""
                      )}>
                        {stock.rsi.toFixed(1)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={cn(
                        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                        getSignalColor(stock.macdSignal)
                      )}>
                        {stock.macdSignal.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

              {filteredStocks.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-400">No stocks found matching your criteria</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
