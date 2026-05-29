import { useState, useEffect, useRef } from 'react'
import {
  Search,
  Activity,
  RefreshCw,
  Plus,
  Minus,
  Maximize2,
  ChevronDown,
  Star,
  X,
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle
} from 'lucide-react'
import { cn, formatCurrency } from '../lib/utils'
import { apiService, priceWebSocket } from '../lib/trading-api'
import type { TradeSignal, PriceUpdate } from '../lib/trading-api'
import { TradingViewChart } from '../components/TradingViewChart'

interface WatchlistItem {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
}

interface SearchResult {
  symbol: string
  name: string
  sector: string
}

interface AISuggestion {
  symbol: string
  action: string
  confidence: number
  entryPrice: number
  stopLoss: number
  target1: number
  target2?: number
  reasoning: string
  riskReward: number
}

export function TradeView() {
  const [symbol, setSymbol] = useState('RELIANCE')
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [signal, setSignal] = useState<TradeSignal | null>(null)
  const [executing, setExecuting] = useState(false)
  const [selectedTimeframe, setSelectedTimeframe] = useState('5m')
  const [showOrderPanel, setShowOrderPanel] = useState(false)
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market')
  const [orderSide, setOrderSide] = useState<'buy' | 'sell'>('buy')
  const [quantity, setQuantity] = useState(1)
  const [limitPrice, setLimitPrice] = useState(0)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [currentQuote, setCurrentQuote] = useState<{price: number, change: number, changePercent: number} | null>(null)
  const [aiSuggestions, setAiSuggestions] = useState<AISuggestion[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)
  const [showAIPanel, setShowAIPanel] = useState(true)
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [watchlistLoading, setWatchlistLoading] = useState(true)
  const [timeframeChange, setTimeframeChange] = useState<{change: number, changePercent: number} | null>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const searchDebounceRef = useRef<NodeJS.Timeout | null>(null)

  const timeframes = ['1m', '5m', '15m', '30m', '1H', '4H', '1D', '1W']

  // Load watchlist from API
  const loadWatchlist = async () => {
    try {
      setWatchlistLoading(true)
      const data = await apiService.getWatchlist()
      setWatchlist(data.watchlist || [])
    } catch (error) {
      console.error('Failed to load watchlist:', error)
      // Fallback to default watchlist
      setWatchlist([
        { symbol: 'RELIANCE', name: 'Reliance Industries', price: 0, change: 0, changePercent: 0 },
        { symbol: 'TCS', name: 'Tata Consultancy', price: 0, change: 0, changePercent: 0 },
        { symbol: 'HDFCBANK', name: 'HDFC Bank', price: 0, change: 0, changePercent: 0 },
        { symbol: 'INFY', name: 'Infosys', price: 0, change: 0, changePercent: 0 },
        { symbol: 'ICICIBANK', name: 'ICICI Bank', price: 0, change: 0, changePercent: 0 },
      ])
    } finally {
      setWatchlistLoading(false)
    }
  }

  // Add symbol to watchlist
  const handleAddToWatchlist = async (sym: string) => {
    try {
      const result = await apiService.addToWatchlist(sym)
      if (result.success) {
        await loadWatchlist()
      }
    } catch (error) {
      console.error('Failed to add to watchlist:', error)
    }
  }

  // Remove symbol from watchlist
  const handleRemoveFromWatchlist = async (sym: string) => {
    try {
      const result = await apiService.removeFromWatchlist(sym)
      if (result.success) {
        await loadWatchlist()
      }
    } catch (error) {
      console.error('Failed to remove from watchlist:', error)
    }
  }

  // Load watchlist on mount
  useEffect(() => {
    loadWatchlist()
  }, [])

  // WebSocket for real-time price updates
  const [wsConnected, setWsConnected] = useState(false)

  useEffect(() => {
    // Connect to price WebSocket
    priceWebSocket.connect(
      (prices: PriceUpdate[]) => {
        // Update watchlist prices
        setWatchlist(prev => prev.map(item => {
          const update = prices.find(p => p.symbol === item.symbol)
          if (update) {
            return {
              ...item,
              price: update.price,
              change: update.change,
              changePercent: update.changePercent
            }
          }
          return item
        }))

        // Update current quote if it matches selected symbol
        const currentUpdate = prices.find(p => p.symbol === symbol)
        if (currentUpdate) {
          setCurrentQuote({
            price: currentUpdate.price,
            change: currentUpdate.change,
            changePercent: currentUpdate.changePercent
          })
        }
      },
      (connected) => setWsConnected(connected)
    )

    return () => {
      priceWebSocket.disconnect()
    }
  }, [symbol])

  // Subscribe to watchlist symbols when watchlist changes
  useEffect(() => {
    if (watchlist.length > 0) {
      const symbols = watchlist.map(w => w.symbol)
      // Also include currently selected symbol
      if (!symbols.includes(symbol)) {
        symbols.push(symbol)
      }
      priceWebSocket.subscribe(symbols)
    }
  }, [watchlist, symbol])

  // Search stocks with debounce
  const handleSearchChange = (query: string) => {
    setSearchQuery(query)

    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current)
    }

    searchDebounceRef.current = setTimeout(async () => {
      if (query.length > 0) {
        setSearchLoading(true)
        try {
          const response = await apiService.searchStocks(query, 15)
          setSearchResults(response.stocks)
        } catch (err) {
          console.error('Search error:', err)
          setSearchResults([])
        } finally {
          setSearchLoading(false)
        }
      } else {
        // Show popular stocks when no query
        try {
          const response = await apiService.searchStocks('', 15)
          setSearchResults(response.stocks)
        } catch {
          setSearchResults([])
        }
      }
    }, 200)
  }

  // Fetch quote when symbol changes
  useEffect(() => {
    const fetchQuote = async () => {
      try {
        const quote = await apiService.getStockQuote(symbol)
        setCurrentQuote({ price: quote.price, change: quote.change, changePercent: quote.changePercent })
        setLimitPrice(quote.price)
      } catch (err) {
        console.error('Failed to fetch quote:', err)
      }
    }
    fetchQuote()
  }, [symbol])

  // Load initial search results
  useEffect(() => {
    if (showSearch && searchResults.length === 0) {
      handleSearchChange('')
    }
  }, [showSearch])

  useEffect(() => {
    if (showSearch && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [showSearch])

  // Fetch AI suggestions on mount
  useEffect(() => {
    const fetchAISuggestions = async () => {
      setLoadingSuggestions(true)
      try {
        const response = await fetch('http://localhost:8001/api/ai/suggestions?symbols=RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK')
        const data = await response.json()
        setAiSuggestions(data.suggestions || [])
      } catch (err) {
        console.error('Error fetching AI suggestions:', err)
      } finally {
        setLoadingSuggestions(false)
      }
    }
    fetchAISuggestions()
  }, [])

  const handleSymbolSelect = (sym: string) => {
    setSymbol(sym)
    setShowSearch(false)
    setSearchQuery('')
    setTimeframeChange(null) // Reset timeframe change on symbol change
    const selected = watchlist.find(w => w.symbol === sym)
    if (selected) {
      setLimitPrice(selected.price)
    }
  }

  const generateSignal = async (stockSymbol: string) => {
    try {
      setIsLoading(true)

      const response = await apiService.generateSignal(stockSymbol)
      setSignal(response.signal)
    } catch (err) {
      console.error('Error generating signal:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleExecuteTrade = async () => {
    try {
      setExecuting(true)

      await apiService.executeTrade({
        symbol: symbol,
        side: orderSide,
        quantity: quantity,
        orderType: orderType,
        price: orderType === 'limit' ? limitPrice : undefined
      })

      alert(`✅ Order placed: ${orderSide.toUpperCase()} ${quantity} ${symbol} @ ${orderType === 'market' ? 'Market' : formatCurrency(limitPrice)}`)
      setShowOrderPanel(false)
    } catch (err) {
      console.error('Error executing trade:', err)
      alert('❌ Failed to execute trade')
    } finally {
      setExecuting(false)
    }
  }

  const currentStock = watchlist.find(w => w.symbol === symbol) || watchlist[0] || {
    symbol: symbol,
    name: symbol,
    price: 0,
    change: 0,
    changePercent: 0
  }

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col bg-[#131722]">
      {/* Top Toolbar - TradingView Style */}
      <div className="flex items-center justify-between px-2 py-1 bg-[#1e222d] border-b border-[#2a2e39]">
        {/* Left Section - Symbol & Price */}
        <div className="flex items-center space-x-4">
          {/* Symbol Selector */}
          <div className="relative">
            <button
              onClick={() => setShowSearch(!showSearch)}
              className="flex items-center space-x-2 px-3 py-1.5 hover:bg-[#2a2e39] rounded transition-colors"
            >
              <span className="text-lg font-bold text-white">{symbol}</span>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>

            {/* Search Dropdown */}
            {showSearch && (
              <div className="absolute top-full left-0 mt-1 w-80 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-xl z-50">
                <div className="p-2 border-b border-[#2a2e39]">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      ref={searchInputRef}
                      type="text"
                      value={searchQuery}
                      onChange={(e) => handleSearchChange(e.target.value)}
                      placeholder="Search NSE stocks..."
                      className="w-full pl-9 pr-3 py-2 bg-[#2a2e39] rounded text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {searchLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <RefreshCw className="w-5 h-5 text-gray-400 animate-spin" />
                    </div>
                  ) : searchResults.length > 0 ? (
                    searchResults.map((item) => (
                      <div
                        key={item.symbol}
                        className="flex items-center justify-between px-3 py-2 hover:bg-[#2a2e39] transition-colors"
                      >
                        <button
                          onClick={() => handleSymbolSelect(item.symbol)}
                          className="flex-1 text-left"
                        >
                          <div className="text-white font-medium">{item.symbol}</div>
                          <div className="text-xs text-gray-400 truncate max-w-[200px]">{item.name}</div>
                        </button>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500 px-2 py-0.5 bg-gray-800 rounded">{item.sector}</span>
                          {!watchlist.find(w => w.symbol === item.symbol) && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleAddToWatchlist(item.symbol)
                              }}
                              className="p-1 hover:bg-green-500/20 rounded transition-colors"
                              title="Add to watchlist"
                            >
                              <Plus className="w-4 h-4 text-green-400" />
                            </button>
                          )}
                          {watchlist.find(w => w.symbol === item.symbol) && (
                            <Star className="w-4 h-4 text-yellow-400" />
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="px-3 py-4 text-center text-gray-500 text-sm">
                      No stocks found
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Current Price Display */}
          <div className="flex items-center space-x-3">
            <span className="text-2xl font-bold text-white">
              {currentQuote ? formatCurrency(currentQuote.price) : formatCurrency(currentStock.price)}
            </span>
            <span className={cn(
              "text-sm font-medium",
              (timeframeChange?.change ?? currentQuote?.change ?? currentStock.change) >= 0 ? "text-green-400" : "text-red-400"
            )}>
              {(timeframeChange?.change ?? currentQuote?.change ?? currentStock.change) >= 0 ? '+' : ''}
              {formatCurrency(timeframeChange?.change ?? currentQuote?.change ?? currentStock.change)}
              ({(timeframeChange?.changePercent ?? currentQuote?.changePercent ?? currentStock.changePercent).toFixed(2)}%)
            </span>
            <span className="text-xs text-gray-500">{selectedTimeframe}</span>
          </div>

          {/* Timeframe Selector */}
          <div className="flex items-center space-x-1 ml-4 border-l border-[#2a2e39] pl-4">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => setSelectedTimeframe(tf)}
                className={cn(
                  "px-2 py-1 text-xs font-medium rounded transition-colors",
                  selectedTimeframe === tf
                    ? "bg-blue-500 text-white"
                    : "text-gray-400 hover:text-white hover:bg-[#2a2e39]"
                )}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Right Section - Tools */}
        <div className="flex items-center space-x-2">
          {/* WebSocket Status Indicator */}
          <div className="flex items-center space-x-1 px-2 py-1 rounded" title={wsConnected ? 'Live prices connected' : 'Connecting to live prices...'}>
            <div className={cn(
              "w-2 h-2 rounded-full",
              wsConnected ? "bg-green-400 animate-pulse" : "bg-yellow-400"
            )} />
            <span className="text-xs text-gray-400">{wsConnected ? 'LIVE' : '...'}</span>
          </div>
          <button
            onClick={() => generateSignal(symbol)}
            disabled={isLoading}
            className="flex items-center space-x-1 px-3 py-1.5 bg-blue-500 hover:bg-blue-600 rounded text-sm font-medium transition-colors"
          >
            {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
            <span>AI Signal</span>
          </button>
          <button
            onClick={() => setShowOrderPanel(!showOrderPanel)}
            className="flex items-center space-x-1 px-3 py-1.5 bg-green-500 hover:bg-green-600 rounded text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Trade</span>
          </button>
          <button
            onClick={() => {
              const isInWatchlist = watchlist.some(w => w.symbol === symbol)
              if (isInWatchlist) {
                handleRemoveFromWatchlist(symbol)
              } else {
                handleAddToWatchlist(symbol)
              }
            }}
            className="p-1.5 hover:bg-[#2a2e39] rounded transition-colors"
            title={watchlist.some(w => w.symbol === symbol) ? 'Remove from watchlist' : 'Add to watchlist'}
          >
            <Star className={cn(
              "w-4 h-4",
              watchlist.some(w => w.symbol === symbol) ? "text-yellow-400 fill-yellow-400" : "text-gray-400"
            )} />
          </button>
          {!showAIPanel && (
            <button
              onClick={() => setShowAIPanel(true)}
              className="p-1.5 hover:bg-[#2a2e39] rounded transition-colors"
              title="Show AI Suggestions"
            >
              <Brain className="w-4 h-4 text-purple-400" />
            </button>
          )}
          <button className="p-1.5 hover:bg-[#2a2e39] rounded transition-colors">
            <Maximize2 className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Watchlist Sidebar */}
        <div className="w-56 bg-[#1e222d] border-r border-[#2a2e39] flex flex-col">
          <div className="px-3 py-2 border-b border-[#2a2e39] flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase">Watchlist</span>
            <button
              onClick={loadWatchlist}
              className="p-1 hover:bg-[#2a2e39] rounded transition-colors"
              title="Refresh watchlist"
            >
              <RefreshCw className={cn("w-3 h-3 text-gray-400", watchlistLoading && "animate-spin")} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {watchlistLoading && watchlist.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="w-5 h-5 text-gray-500 animate-spin" />
              </div>
            ) : watchlist.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-xs">
                <p>No stocks in watchlist</p>
                <p className="mt-1">Search and add stocks</p>
              </div>
            ) : (
              watchlist.map((item) => (
                <div
                  key={item.symbol}
                  className={cn(
                    "group flex items-center justify-between px-3 py-2 hover:bg-[#2a2e39] transition-colors border-l-2 cursor-pointer",
                    symbol === item.symbol ? "border-blue-500 bg-[#2a2e39]" : "border-transparent"
                  )}
                  onClick={() => handleSymbolSelect(item.symbol)}
                >
                  <div className="text-left flex-1 min-w-0">
                    <div className={cn("text-sm font-medium", symbol === item.symbol ? "text-white" : "text-gray-300")}>
                      {item.symbol}
                    </div>
                    <div className="text-xs text-gray-500 truncate max-w-[80px]">{item.name}</div>
                  </div>
                  <div className="text-right flex items-center gap-2">
                    <div>
                      <div className="text-sm text-white">{item.price > 0 ? formatCurrency(item.price) : '-'}</div>
                      <div className={cn("text-xs", item.change >= 0 ? "text-green-400" : "text-red-400")}>
                        {item.price > 0 ? `${item.change >= 0 ? '+' : ''}${item.changePercent.toFixed(2)}%` : '-'}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleRemoveFromWatchlist(item.symbol)
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all"
                      title="Remove from watchlist"
                    >
                      <X className="w-3 h-3 text-red-400" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
          {/* Add to watchlist from search */}
          {showSearch && searchResults.length > 0 && (
            <div className="border-t border-[#2a2e39] p-2">
              <p className="text-xs text-gray-500 mb-2">Click + to add to watchlist</p>
            </div>
          )}
        </div>

        {/* Chart Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Chart */}
          <div className="flex-1 p-2">
            <TradingViewChart
              symbol={symbol}
              entryPrice={signal?.entryPrice}
              stopLoss={signal?.stopLoss}
              target1={signal?.target1}
              target2={signal?.target2}
              direction={signal?.direction}
              currentPrice={currentStock.price}
              height={500}
              timeframe={selectedTimeframe}
              onTimeframeChange={(change, changePercent) => setTimeframeChange({ change, changePercent })}
            />
          </div>

          {/* Signal Panel (if signal exists) */}
          {signal && (
            <div className="bg-[#1e222d] border-t border-[#2a2e39] p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-6">
                  <div className="flex items-center space-x-2">
                    <span className={cn(
                      "px-2 py-0.5 rounded text-xs font-bold",
                      signal.direction === 'BUY' ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                    )}>
                      {signal.direction}
                    </span>
                    <span className="text-sm text-gray-400">Confidence: <span className="text-white font-medium">{signal.confidence}%</span></span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm">
                    <span className="text-gray-400">Entry: <span className="text-blue-400 font-medium">{formatCurrency(signal.entryPrice)}</span></span>
                    <span className="text-gray-400">SL: <span className="text-red-400 font-medium">{formatCurrency(signal.stopLoss)}</span></span>
                    <span className="text-gray-400">T1: <span className="text-green-400 font-medium">{formatCurrency(signal.target1)}</span></span>
                    {signal.target2 && (
                      <span className="text-gray-400">T2: <span className="text-green-400 font-medium">{formatCurrency(signal.target2)}</span></span>
                    )}
                  </div>
                </div>
                <div className="text-xs text-gray-400 max-w-md truncate">
                  {signal.reasoning}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* AI Suggestions Panel */}
        {showAIPanel && (
          <div className="w-72 bg-[#1e222d] border-l border-[#2a2e39] flex flex-col">
            <div className="flex items-center justify-between px-3 py-2 border-b border-[#2a2e39]">
              <div className="flex items-center space-x-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <span className="text-xs font-medium text-gray-400 uppercase">AI Suggestions</span>
              </div>
              <button
                onClick={() => setShowAIPanel(false)}
                className="p-1 hover:bg-[#2a2e39] rounded transition-colors"
              >
                <X className="w-3 h-3 text-gray-400" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {loadingSuggestions ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-5 h-5 text-gray-400 animate-spin" />
                </div>
              ) : aiSuggestions.length > 0 ? (
                aiSuggestions.map((suggestion, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSymbolSelect(suggestion.symbol)}
                    className={cn(
                      "p-3 rounded-lg cursor-pointer transition-all hover:scale-[1.02]",
                      suggestion.action === 'BUY'
                        ? "bg-green-500/10 border border-green-500/30 hover:border-green-500/50"
                        : suggestion.action === 'SELL'
                        ? "bg-red-500/10 border border-red-500/30 hover:border-red-500/50"
                        : "bg-yellow-500/10 border border-yellow-500/30 hover:border-yellow-500/50"
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-white">{suggestion.symbol}</span>
                      <span className={cn(
                        "px-2 py-0.5 rounded text-xs font-bold",
                        suggestion.action === 'BUY' ? "bg-green-500/20 text-green-400" :
                        suggestion.action === 'SELL' ? "bg-red-500/20 text-red-400" :
                        "bg-yellow-500/20 text-yellow-400"
                      )}>
                        {suggestion.action === 'BUY' && <TrendingUp className="w-3 h-3 inline mr-1" />}
                        {suggestion.action === 'SELL' && <TrendingDown className="w-3 h-3 inline mr-1" />}
                        {suggestion.action === 'HOLD' && <AlertTriangle className="w-3 h-3 inline mr-1" />}
                        {suggestion.action}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 space-y-1">
                      <div className="flex justify-between">
                        <span>Confidence:</span>
                        <span className="text-white">{suggestion.confidence}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Entry:</span>
                        <span className="text-blue-400">{formatCurrency(suggestion.entryPrice)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Stop Loss:</span>
                        <span className="text-red-400">{formatCurrency(suggestion.stopLoss)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Target:</span>
                        <span className="text-green-400">{formatCurrency(suggestion.target1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>R:R Ratio:</span>
                        <span className="text-purple-400">1:{suggestion.riskReward.toFixed(1)}</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-2 line-clamp-2">{suggestion.reasoning}</p>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500 text-sm">
                  <Brain className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No AI suggestions available</p>
                  <p className="text-xs mt-1">Click "AI Signal" to generate</p>
                </div>
              )}
            </div>
          </div>
        )}

      </div>

      {/* Order Panel Modal */}
      {showOrderPanel && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-50"
            onClick={() => setShowOrderPanel(false)}
          />
          {/* Modal */}
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 bg-[#1e222d] border border-[#2a2e39] rounded-lg shadow-2xl z-50">
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#2a2e39]">
              <div>
                <span className="text-lg font-semibold text-white">Place Order</span>
                <span className="ml-2 text-sm text-gray-400">{symbol}</span>
              </div>
              <button onClick={() => setShowOrderPanel(false)} className="p-1.5 hover:bg-[#2a2e39] rounded transition-colors">
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* Buy/Sell Toggle */}
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setOrderSide('buy')}
                  className={cn(
                    "py-3 text-sm font-semibold rounded-lg transition-colors",
                    orderSide === 'buy'
                      ? "bg-green-500 text-white shadow-lg shadow-green-500/30"
                      : "bg-[#2a2e39] text-gray-400 hover:text-white"
                  )}
                >
                  Buy
                </button>
                <button
                  onClick={() => setOrderSide('sell')}
                  className={cn(
                    "py-3 text-sm font-semibold rounded-lg transition-colors",
                    orderSide === 'sell'
                      ? "bg-red-500 text-white shadow-lg shadow-red-500/30"
                      : "bg-[#2a2e39] text-gray-400 hover:text-white"
                  )}
                >
                  Sell
                </button>
              </div>

              {/* Current Price */}
              <div className="p-3 bg-[#2a2e39] rounded-lg">
                <div className="text-xs text-gray-400 mb-1">Current Price</div>
                <div className="text-xl font-bold text-white">
                  {currentQuote ? formatCurrency(currentQuote.price) : formatCurrency(currentStock.price)}
                </div>
              </div>

              {/* Order Type */}
              <div>
                <label className="text-xs text-gray-400 mb-1.5 block">Order Type</label>
                <select
                  value={orderType}
                  onChange={(e) => setOrderType(e.target.value as 'market' | 'limit')}
                  className="w-full px-3 py-2.5 bg-[#2a2e39] border border-[#363a45] rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="market">Market Order</option>
                  <option value="limit">Limit Order</option>
                </select>
              </div>

              {/* Quantity */}
              <div>
                <label className="text-xs text-gray-400 mb-1.5 block">Quantity</label>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="p-2.5 bg-[#2a2e39] hover:bg-[#363a45] rounded-lg transition-colors"
                  >
                    <Minus className="w-4 h-4 text-gray-400" />
                  </button>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                    className="flex-1 px-3 py-2.5 bg-[#2a2e39] border border-[#363a45] rounded-lg text-white text-center font-medium focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={() => setQuantity(quantity + 1)}
                    className="p-2.5 bg-[#2a2e39] hover:bg-[#363a45] rounded-lg transition-colors"
                  >
                    <Plus className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>

              {/* Limit Price */}
              {orderType === 'limit' && (
                <div>
                  <label className="text-xs text-gray-400 mb-1.5 block">Limit Price</label>
                  <input
                    type="number"
                    value={limitPrice}
                    onChange={(e) => setLimitPrice(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2.5 bg-[#2a2e39] border border-[#363a45] rounded-lg text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              {/* Order Summary */}
              <div className="p-3 bg-[#2a2e39] rounded-lg space-y-2 border border-[#363a45]">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Est. Value</span>
                  <span className="text-white font-medium">
                    {formatCurrency(quantity * (orderType === 'limit' ? limitPrice : (currentQuote?.price ?? currentStock.price)))}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Brokerage</span>
                  <span className="text-white">₹20.00</span>
                </div>
                <div className="flex justify-between text-sm pt-2 border-t border-[#363a45]">
                  <span className="text-gray-400">Total</span>
                  <span className="text-white font-semibold">
                    {formatCurrency(quantity * (orderType === 'limit' ? limitPrice : (currentQuote?.price ?? currentStock.price)) + 20)}
                  </span>
                </div>
              </div>

              {/* Submit Button */}
              <button
                onClick={handleExecuteTrade}
                disabled={executing}
                className={cn(
                  "w-full py-3.5 rounded-lg font-semibold text-white transition-all",
                  orderSide === 'buy'
                    ? "bg-green-500 hover:bg-green-600 shadow-lg shadow-green-500/30"
                    : "bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/30",
                  executing && "opacity-50 cursor-not-allowed"
                )}
              >
                {executing ? 'Placing Order...' : `${orderSide === 'buy' ? 'Buy' : 'Sell'} ${quantity} ${symbol}`}
              </button>
            </div>
          </div>
        </>
      )}

      {/* Click outside to close search */}
      {showSearch && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowSearch(false)}
        />
      )}
    </div>
  )
}

