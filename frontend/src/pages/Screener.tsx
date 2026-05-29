import React, { useState, useEffect } from 'react'
import { Search, Filter, TrendingUp, TrendingDown, BarChart3, RefreshCw, ChevronDown, ChevronUp, Settings, Download, Columns, Star, ExternalLink, Save, X, Sliders } from 'lucide-react'
import { cn, formatCurrency, formatPercentage, getPercentageColor } from '../lib/utils'
import type { Stock } from '../data/mockData'
import { mockStocks } from '../data/mockData'
import { apiService } from '../lib/trading-api'

interface ScreenedStock extends Stock {
  relatedNews?: Array<{
    title: string
    sentiment: string
    impact: string
  }>
  screeningScore?: number
}

type SortField = 'symbol' | 'price' | 'changePercent' | 'volume' | 'marketCap' | 'rsi' | 'pe'
type SortDirection = 'asc' | 'desc'
type QuickFilter = 'none' | 'top_gainers' | 'top_losers' | 'most_active' | 'overbought' | 'oversold'

interface ScreenerPreset {
  id: string
  name: string
  filters: {
    rsiMin: number
    rsiMax: number
    changeMin: number
    changeMax: number
    volumeMin: number
    signal: string
  }
}

const DEFAULT_PRESETS: ScreenerPreset[] = [
  { id: 'momentum', name: 'Momentum Stocks', filters: { rsiMin: 50, rsiMax: 70, changeMin: 1, changeMax: 100, volumeMin: 100000, signal: 'buy' } },
  { id: 'oversold', name: 'Oversold Bounce', filters: { rsiMin: 0, rsiMax: 30, changeMin: -100, changeMax: 0, volumeMin: 50000, signal: 'all' } },
  { id: 'breakout', name: 'Breakout Candidates', filters: { rsiMin: 60, rsiMax: 80, changeMin: 2, changeMax: 100, volumeMin: 200000, signal: 'buy' } },
]

export function Screener() {
  const [stocks, setStocks] = useState<ScreenedStock[]>(mockStocks)
  const [filteredStocks, setFilteredStocks] = useState<ScreenedStock[]>(mockStocks)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSector, setSelectedSector] = useState('all')
  const [selectedSignal, setSelectedSignal] = useState('all')
  const [isLoading, setIsLoading] = useState(false)
  const [newsMap, setNewsMap] = useState<Record<string, any[]>>({})
  const [error, setError] = useState<string | null>(null)
  const [sortField, setSortField] = useState<SortField>('changePercent')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [selectedStock, setSelectedStock] = useState<string | null>(null)

  // Enhanced filters
  const [quickFilter, setQuickFilter] = useState<QuickFilter>('none')
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [rsiMin, setRsiMin] = useState(0)
  const [rsiMax, setRsiMax] = useState(100)
  const [changeMin, setChangeMin] = useState(-100)
  const [changeMax, setChangeMax] = useState(100)
  const [volumeMin, setVolumeMin] = useState(0)

  // Presets
  const [presets, setPresets] = useState<ScreenerPreset[]>(DEFAULT_PRESETS)
  const [showSavePreset, setShowSavePreset] = useState(false)
  const [newPresetName, setNewPresetName] = useState('')

  const sectors = ['all', ...Array.from(new Set(stocks.map(stock => stock.sector)))]
  const signals = ['all', 'buy', 'sell', 'neutral']

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDirection === 'asc'
      ? <ChevronUp className="w-3 h-3 ml-1" />
      : <ChevronDown className="w-3 h-3 ml-1" />
  }

  // Fetch screened stocks and news on mount
  useEffect(() => {
    fetchScreenedStocks()
  }, [])

  const fetchScreenedStocks = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Fetch screened stocks from API
      const response = await fetch('http://localhost:8001/screener/stocks')
      const data = await response.json()

      if (data.stocks && data.stocks.length > 0) {
        // Map API response to Stock format
        const apiStocks: ScreenedStock[] = data.stocks.map((s: any) => ({
          symbol: s.symbol,
          name: s.symbol, // API doesn't return name
          price: s.current_price || 0,
          change: s.price_change_pct || 0,
          changePercent: s.price_change_pct || 0,
          volume: s.current_volume || 0,
          marketCap: 0,
          pe: 0,
          sector: 'Unknown',
          rsi: s.rsi || 50,
          macdSignal: s.rsi > 70 ? 'sell' : s.rsi < 30 ? 'buy' : 'neutral',
          lastUpdated: new Date().toISOString(),
          screeningScore: s.screening_score
        }))
        setStocks(apiStocks)
        setFilteredStocks(apiStocks)
      }

      // Also fetch news to correlate with stocks
      await fetchNewsForStocks()

    } catch (err) {
      console.error('Error fetching screened stocks:', err)
      setError('Failed to fetch screened stocks. Using mock data.')
      // Fall back to mock data
      setStocks(mockStocks)
      setFilteredStocks(mockStocks)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchNewsForStocks = async () => {
    try {
      const newsResponse = await apiService.getNews({ page: 1, limit: 50 })
      if (newsResponse.articles) {
        // Group news by mentioned stocks
        const newsGrouped: Record<string, any[]> = {}
        newsResponse.articles.forEach((article: any) => {
          const symbols = article.aiAnalysis?.stocksAffected || []
          symbols.forEach((symbol: string) => {
            if (!newsGrouped[symbol]) newsGrouped[symbol] = []
            newsGrouped[symbol].push({
              title: article.title,
              sentiment: article.aiAnalysis?.sentiment || 'NEUTRAL',
              impact: article.aiAnalysis?.impact || 'LOW'
            })
          })
        })
        setNewsMap(newsGrouped)
      }
    } catch (err) {
      console.error('Error fetching news:', err)
    }
  }

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

    // Apply RSI filter
    filtered = filtered.filter(stock => stock.rsi >= rsiMin && stock.rsi <= rsiMax)

    // Apply change percent filter
    filtered = filtered.filter(stock => stock.changePercent >= changeMin && stock.changePercent <= changeMax)

    // Apply volume filter
    if (volumeMin > 0) {
      filtered = filtered.filter(stock => stock.volume >= volumeMin)
    }

    // Apply quick filters
    if (quickFilter !== 'none') {
      switch (quickFilter) {
        case 'top_gainers':
          filtered = filtered.filter(s => s.changePercent > 0).sort((a, b) => b.changePercent - a.changePercent).slice(0, 20)
          break
        case 'top_losers':
          filtered = filtered.filter(s => s.changePercent < 0).sort((a, b) => a.changePercent - b.changePercent).slice(0, 20)
          break
        case 'most_active':
          filtered = [...filtered].sort((a, b) => b.volume - a.volume).slice(0, 20)
          break
        case 'overbought':
          filtered = filtered.filter(s => s.rsi > 70)
          break
        case 'oversold':
          filtered = filtered.filter(s => s.rsi < 30)
          break
      }
    }

    // Sort (unless quick filter already sorted)
    if (quickFilter === 'none' || (quickFilter !== 'top_gainers' && quickFilter !== 'top_losers' && quickFilter !== 'most_active')) {
      filtered = [...filtered].sort((a, b) => {
        const aVal = a[sortField] as number
        const bVal = b[sortField] as number
        if (sortDirection === 'asc') {
          return aVal - bVal
        }
        return bVal - aVal
      })
    }

    setFilteredStocks(filtered)
  }, [stocks, searchTerm, selectedSector, selectedSignal, sortField, sortDirection, rsiMin, rsiMax, changeMin, changeMax, volumeMin, quickFilter])

  const handleRefresh = async () => {
    await fetchScreenedStocks()
  }

  const applyQuickFilter = (filter: QuickFilter) => {
    setQuickFilter(quickFilter === filter ? 'none' : filter)
  }

  const applyPreset = (preset: ScreenerPreset) => {
    setRsiMin(preset.filters.rsiMin)
    setRsiMax(preset.filters.rsiMax)
    setChangeMin(preset.filters.changeMin)
    setChangeMax(preset.filters.changeMax)
    setVolumeMin(preset.filters.volumeMin)
    setSelectedSignal(preset.filters.signal)
    setQuickFilter('none')
  }

  const savePreset = () => {
    if (!newPresetName.trim()) return
    const newPreset: ScreenerPreset = {
      id: `custom_${Date.now()}`,
      name: newPresetName,
      filters: {
        rsiMin,
        rsiMax,
        changeMin,
        changeMax,
        volumeMin,
        signal: selectedSignal
      }
    }
    setPresets([...presets, newPreset])
    setNewPresetName('')
    setShowSavePreset(false)
    // Save to localStorage
    localStorage.setItem('screener_presets', JSON.stringify([...presets, newPreset]))
  }

  const resetFilters = () => {
    setRsiMin(0)
    setRsiMax(100)
    setChangeMin(-100)
    setChangeMax(100)
    setVolumeMin(0)
    setSelectedSignal('all')
    setSelectedSector('all')
    setQuickFilter('none')
    setSearchTerm('')
  }

  // Load saved presets on mount
  useEffect(() => {
    const saved = localStorage.getItem('screener_presets')
    if (saved) {
      try {
        setPresets(JSON.parse(saved))
      } catch (e) {
        console.error('Failed to load presets:', e)
      }
    }
  }, [])

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
    <div className="h-[calc(100vh-120px)] flex flex-col bg-[#131722]">
      {/* Top Toolbar - TradingView Style */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#1e222d] border-b border-[#2a2e39]">
        <div className="flex items-center space-x-4">
          <h1 className="text-lg font-semibold text-white">Stock Screener</h1>
          <span className="text-sm text-gray-400">{filteredStocks.length} matches</span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="flex items-center space-x-1 px-3 py-1.5 hover:bg-[#2a2e39] rounded text-sm text-gray-300 transition-colors"
          >
            <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            <span>Refresh</span>
          </button>
          <button className="p-1.5 hover:bg-[#2a2e39] rounded transition-colors">
            <Download className="w-4 h-4 text-gray-400" />
          </button>
          <button className="p-1.5 hover:bg-[#2a2e39] rounded transition-colors">
            <Settings className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex items-center space-x-3 px-4 py-2 bg-[#1e222d] border-b border-[#2a2e39]">
        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search symbol or name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-[#2a2e39] rounded text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Filter Chips */}
        <div className="flex items-center space-x-2">
          <select
            value={selectedSector}
            onChange={(e) => setSelectedSector(e.target.value)}
            className="px-3 py-1.5 bg-[#2a2e39] border border-[#363a45] rounded text-white text-sm focus:outline-none focus:border-blue-500"
          >
            {sectors.map(sector => (
              <option key={sector} value={sector}>
                {sector === 'all' ? 'All Sectors' : sector}
              </option>
            ))}
          </select>

          <select
            value={selectedSignal}
            onChange={(e) => setSelectedSignal(e.target.value)}
            className="px-3 py-1.5 bg-[#2a2e39] border border-[#363a45] rounded text-white text-sm focus:outline-none focus:border-blue-500"
          >
            {signals.map(signal => (
              <option key={signal} value={signal}>
                {signal === 'all' ? 'All Signals' : signal.charAt(0).toUpperCase() + signal.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Quick Filters */}
        <div className="flex items-center space-x-1 border-l border-[#2a2e39] pl-3">
          <button
            onClick={() => applyQuickFilter('top_gainers')}
            className={cn("px-2 py-1 text-xs rounded transition-colors", quickFilter === 'top_gainers' ? 'text-green-400 bg-green-500/20' : 'text-gray-400 hover:text-white hover:bg-[#2a2e39]')}
          >
            Top Gainers
          </button>
          <button
            onClick={() => applyQuickFilter('top_losers')}
            className={cn("px-2 py-1 text-xs rounded transition-colors", quickFilter === 'top_losers' ? 'text-red-400 bg-red-500/20' : 'text-gray-400 hover:text-white hover:bg-[#2a2e39]')}
          >
            Top Losers
          </button>
          <button
            onClick={() => applyQuickFilter('most_active')}
            className={cn("px-2 py-1 text-xs rounded transition-colors", quickFilter === 'most_active' ? 'text-blue-400 bg-blue-500/20' : 'text-gray-400 hover:text-white hover:bg-[#2a2e39]')}
          >
            Most Active
          </button>
          <button
            onClick={() => applyQuickFilter('overbought')}
            className={cn("px-2 py-1 text-xs rounded transition-colors", quickFilter === 'overbought' ? 'text-orange-400 bg-orange-500/20' : 'text-gray-400 hover:text-white hover:bg-[#2a2e39]')}
          >
            Overbought
          </button>
          <button
            onClick={() => applyQuickFilter('oversold')}
            className={cn("px-2 py-1 text-xs rounded transition-colors", quickFilter === 'oversold' ? 'text-purple-400 bg-purple-500/20' : 'text-gray-400 hover:text-white hover:bg-[#2a2e39]')}
          >
            Oversold
          </button>
        </div>

        {/* Advanced Filters Toggle */}
        <button
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          className={cn("flex items-center space-x-1 px-3 py-1.5 rounded text-sm transition-colors border-l border-[#2a2e39] ml-2", showAdvancedFilters ? 'text-blue-400 bg-blue-500/20' : 'text-gray-400 hover:text-white hover:bg-[#2a2e39]')}
        >
          <Sliders className="w-4 h-4" />
          <span>Filters</span>
        </button>

        {/* Reset Filters */}
        {(rsiMin > 0 || rsiMax < 100 || changeMin > -100 || changeMax < 100 || volumeMin > 0 || selectedSignal !== 'all' || quickFilter !== 'none') && (
          <button
            onClick={resetFilters}
            className="flex items-center space-x-1 px-2 py-1 text-xs text-red-400 hover:bg-red-500/20 rounded transition-colors"
          >
            <X className="w-3 h-3" />
            <span>Reset</span>
          </button>
        )}
      </div>

      {/* Advanced Filters Panel */}
      {showAdvancedFilters && (
        <div className="px-4 py-3 bg-[#1e222d] border-b border-[#2a2e39]">
          <div className="flex flex-wrap items-center gap-4">
            {/* RSI Range */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-400">RSI:</span>
              <input
                type="number"
                value={rsiMin}
                onChange={(e) => setRsiMin(Number(e.target.value))}
                className="w-14 px-2 py-1 bg-[#2a2e39] rounded text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                min="0"
                max="100"
              />
              <span className="text-gray-500">-</span>
              <input
                type="number"
                value={rsiMax}
                onChange={(e) => setRsiMax(Number(e.target.value))}
                className="w-14 px-2 py-1 bg-[#2a2e39] rounded text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                min="0"
                max="100"
              />
            </div>

            {/* Change % Range */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-400">Change %:</span>
              <input
                type="number"
                value={changeMin}
                onChange={(e) => setChangeMin(Number(e.target.value))}
                className="w-16 px-2 py-1 bg-[#2a2e39] rounded text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <span className="text-gray-500">-</span>
              <input
                type="number"
                value={changeMax}
                onChange={(e) => setChangeMax(Number(e.target.value))}
                className="w-16 px-2 py-1 bg-[#2a2e39] rounded text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {/* Min Volume */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-400">Min Volume:</span>
              <select
                value={volumeMin}
                onChange={(e) => setVolumeMin(Number(e.target.value))}
                className="px-2 py-1 bg-[#2a2e39] rounded text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value={0}>Any</option>
                <option value={10000}>10K+</option>
                <option value={50000}>50K+</option>
                <option value={100000}>1L+</option>
                <option value={500000}>5L+</option>
                <option value={1000000}>10L+</option>
              </select>
            </div>

            {/* Presets */}
            <div className="flex items-center space-x-2 border-l border-[#2a2e39] pl-4">
              <span className="text-xs text-gray-400">Presets:</span>
              {presets.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => applyPreset(preset)}
                  className="px-2 py-1 text-xs text-gray-300 hover:text-white hover:bg-[#2a2e39] rounded transition-colors"
                >
                  {preset.name}
                </button>
              ))}
              <button
                onClick={() => setShowSavePreset(true)}
                className="flex items-center space-x-1 px-2 py-1 text-xs text-blue-400 hover:bg-blue-500/20 rounded transition-colors"
              >
                <Save className="w-3 h-3" />
                <span>Save</span>
              </button>
            </div>
          </div>

          {/* Save Preset Modal */}
          {showSavePreset && (
            <div className="mt-3 flex items-center space-x-2">
              <input
                type="text"
                value={newPresetName}
                onChange={(e) => setNewPresetName(e.target.value)}
                placeholder="Preset name..."
                className="px-3 py-1.5 bg-[#2a2e39] rounded text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <button
                onClick={savePreset}
                disabled={!newPresetName.trim()}
                className="px-3 py-1.5 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save
              </button>
              <button
                onClick={() => { setShowSavePreset(false); setNewPresetName('') }}
                className="px-3 py-1.5 text-gray-400 text-sm hover:text-white"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      )}

      {/* Main Table */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex items-center space-x-3">
              <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
              <span className="text-gray-300">Scanning market data...</span>
            </div>
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-[#1e222d] z-10">
              <tr className="border-b border-[#2a2e39]">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider w-8">
                  <Star className="w-3 h-3" />
                </th>
                <th
                  onClick={() => handleSort('symbol')}
                  className="text-left px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center">Symbol <SortIcon field="symbol" /></div>
                </th>
                <th
                  onClick={() => handleSort('price')}
                  className="text-right px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center justify-end">Last <SortIcon field="price" /></div>
                </th>
                <th
                  onClick={() => handleSort('changePercent')}
                  className="text-right px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center justify-end">Chg % <SortIcon field="changePercent" /></div>
                </th>
                <th
                  onClick={() => handleSort('volume')}
                  className="text-right px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center justify-end">Volume <SortIcon field="volume" /></div>
                </th>
                <th
                  onClick={() => handleSort('marketCap')}
                  className="text-right px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center justify-end">Mkt Cap <SortIcon field="marketCap" /></div>
                </th>
                <th
                  onClick={() => handleSort('pe')}
                  className="text-right px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center justify-end">P/E <SortIcon field="pe" /></div>
                </th>
                <th
                  onClick={() => handleSort('rsi')}
                  className="text-right px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
                >
                  <div className="flex items-center justify-end">RSI <SortIcon field="rsi" /></div>
                </th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Signal
                </th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider w-12">
                  Chart
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredStocks.map((stock) => (
                <tr
                  key={stock.symbol}
                  onClick={() => setSelectedStock(stock.symbol)}
                  className={cn(
                    "border-b border-[#2a2e39] hover:bg-[#2a2e39]/50 transition-colors cursor-pointer",
                    selectedStock === stock.symbol && "bg-[#2a2e39]"
                  )}
                >
                  <td className="px-4 py-3">
                    <button className="text-gray-500 hover:text-yellow-400 transition-colors">
                      <Star className="w-4 h-4" />
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white">
                        {stock.symbol.slice(0, 2)}
                      </div>
                      <div>
                        <div className="font-medium text-white">{stock.symbol}</div>
                        <div className="text-xs text-gray-400 truncate max-w-[150px]">{stock.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-medium text-white">{formatCurrency(stock.price)}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end space-x-1">
                      {stock.changePercent >= 0 ? (
                        <TrendingUp className="w-3 h-3 text-green-400" />
                      ) : (
                        <TrendingDown className="w-3 h-3 text-red-400" />
                      )}
                      <span className={cn(
                        "font-medium",
                        stock.changePercent >= 0 ? "text-green-400" : "text-red-400"
                      )}>
                        {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-gray-300">{formatVolume(stock.volume)}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-gray-300">{formatMarketCap(stock.marketCap)}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-gray-300">{stock.pe.toFixed(1)}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={cn(
                      "font-medium",
                      stock.rsi > 70 ? "text-red-400" : stock.rsi < 30 ? "text-green-400" : "text-gray-300"
                    )}>
                      {stock.rsi.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={cn(
                      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                      getSignalColor(stock.macdSignal)
                    )}>
                      {stock.macdSignal.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <a
                      href={`/trade-view?symbol=${stock.symbol}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-gray-400 hover:text-blue-400 transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!isLoading && filteredStocks.length === 0 && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 mx-auto mb-3 text-gray-500" />
              <p className="text-gray-400">No stocks found matching your criteria</p>
              <p className="text-sm text-gray-500 mt-1">Try adjusting your filters</p>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Status Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#1e222d] border-t border-[#2a2e39] text-xs text-gray-400">
        <div className="flex items-center space-x-4">
          <span>Showing {filteredStocks.length} of {stocks.length} stocks</span>
          <span>•</span>
          <span>Sorted by {sortField} ({sortDirection})</span>
        </div>
        <div className="flex items-center space-x-2">
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  )
}
