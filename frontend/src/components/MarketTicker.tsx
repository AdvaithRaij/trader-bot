import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { cn, formatCurrency, formatPercentage, getPercentageColor } from '../lib/utils'
import { apiService } from '../lib/trading-api'

interface TickerItem {
  symbol: string
  name?: string
  price: number
  change: number
  changePercent: number
  type: 'index' | 'stock'
}

export function MarketTicker() {
  const [tickerItems, setTickerItems] = useState<TickerItem[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTickerData = async () => {
      try {
        // Fetch live quotes for indices and popular stocks using batch API
        const symbols = [
          'NSE:NIFTY50-INDEX',
          'NSE:NIFTYBANK-INDEX',
          'SBIN',
          'RELIANCE',
          'TCS',
          'INFY',
          'HDFCBANK',
          'ICICIBANK',
          'MARUTI',
          'TITAN',
          'TATAMOTORS',
          'SUNPHARMA',
          'BAJFINANCE',
          'ADANIGREEN',
          'LTIM'
        ]

        // Use batch API to get all quotes in a single request
        const response = await apiService.getBatchQuotes(symbols)
        const quotes = response.quotes || []

        const tickerData: TickerItem[] = []

        quotes.forEach((quote) => {
          // Skip quotes with zero price (failed to fetch)
          if (!quote.price || quote.price === 0) {
            return
          }

          // Determine if it's an index or stock
          const isIndex = quote.symbol.includes('INDEX') || quote.symbol.includes('NIFTY') || quote.symbol.includes('BANK')

          // Format display symbol
          let displaySymbol = quote.symbol
          if (quote.symbol.includes('NIFTY50')) {
            displaySymbol = 'NIFTY 50'
          } else if (quote.symbol.includes('NIFTYBANK')) {
            displaySymbol = 'BANKNIFTY'
          } else {
            displaySymbol = quote.symbol.replace('NSE:', '').replace('-INDEX', '')
          }

          tickerData.push({
            symbol: displaySymbol,
            price: quote.price,
            change: quote.change,
            changePercent: quote.changePercent,
            type: isIndex ? 'index' : 'stock'
          })
        })

        if (tickerData.length === 0) {
          setError('No market data available')
          setIsLoading(false)
          return
        }

        // Duplicate for seamless scrolling
        setTickerItems([...tickerData, ...tickerData])
        setError(null)
        setIsLoading(false)
      } catch (error) {
        console.error('Failed to fetch ticker data:', error)
        setError('Failed to load market data')
        setIsLoading(false)
      }
    }

    fetchTickerData()

    // Refresh ticker data every 5 minutes
    const interval = setInterval(fetchTickerData, 300000)

    return () => clearInterval(interval)
  }, [])

  const handleMouseEnter = () => setIsPaused(true)
  const handleMouseLeave = () => setIsPaused(false)

  // Function to get TradingView URL for a symbol
  const getTradingViewUrl = (symbol: string, type: 'index' | 'stock') => {
    if (type === 'index') {
      // For indices, use NSE index format
      if (symbol === 'NIFTY 50') return 'https://www.tradingview.com/chart/?symbol=NSE%3ANIFTY'
      if (symbol === 'BANKNIFTY') return 'https://www.tradingview.com/chart/?symbol=NSE%3ABANKNIFTY'
      return `https://www.tradingview.com/chart/?symbol=NSE%3A${symbol}`
    }
    // For stocks, use NSE stock format
    return `https://www.tradingview.com/chart/?symbol=NSE%3A${symbol}`
  }

  const handleTickerClick = (symbol: string, type: 'index' | 'stock') => {
    const url = getTradingViewUrl(symbol, type)
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  // Show loading state
  if (isLoading) {
    return (
      <div className="relative bg-gray-900/90 backdrop-blur-sm border-b border-white/10 overflow-hidden">
        <div className="flex items-center justify-center py-2 text-gray-400 text-sm">
          <span className="animate-pulse">Loading market data...</span>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="relative bg-gray-900/90 backdrop-blur-sm border-b border-white/10 overflow-hidden">
        <div className="flex items-center justify-center py-2 text-red-400 text-sm">
          <span>{error}</span>
        </div>
      </div>
    )
  }

  // Show empty state
  if (tickerItems.length === 0) {
    return (
      <div className="relative bg-gray-900/90 backdrop-blur-sm border-b border-white/10 overflow-hidden">
        <div className="flex items-center justify-center py-2 text-gray-400 text-sm">
          <span>No market data available</span>
        </div>
      </div>
    )
  }

  return (
    <div className="relative bg-gray-900/90 backdrop-blur-sm border-b border-white/10 overflow-hidden">
      <div
        className={cn(
          "flex items-center py-2 gap-6 sm:gap-8 animate-scroll",
          isPaused && "animation-paused"
        )}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{
          width: 'fit-content',
          minWidth: '100%'
        }}
      >
        {tickerItems.map((item, index) => (
          <button
            key={`${item.symbol}-${index}`}
            onClick={() => handleTickerClick(item.symbol, item.type)}
            className="flex items-center space-x-1.5 sm:space-x-2 px-2 sm:px-4 py-1 whitespace-nowrap flex-shrink-0 hover:bg-white/5 rounded transition-colors duration-200 cursor-pointer"
          >
            {/* Symbol */}
            <span className={cn(
              "font-semibold text-xs sm:text-sm",
              item.type === 'index' ? "text-blue-300" : "text-white"
            )}>
              {item.symbol}
            </span>

            {/* Price */}
            <span className="text-white font-medium text-xs sm:text-sm">
              {item.type === 'index' ? item.price.toLocaleString() : formatCurrency(item.price)}
            </span>

            {/* Change and Icon */}
            <div className={cn(
              "flex items-center space-x-0.5 sm:space-x-1 text-xs font-medium",
              getPercentageColor(item.changePercent)
            )}>
              {item.changePercent >= 0 ? (
                <TrendingUp className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
              ) : (
                <TrendingDown className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
              )}
              <span className="text-xs">
                {formatPercentage(item.changePercent)}
              </span>
              <span className="text-gray-400 hidden sm:inline text-xs">
                ({item.change >= 0 ? '+' : ''}{item.type === 'index' ? item.change.toFixed(1) : formatCurrency(item.change)})
              </span>
            </div>

            {/* Separator */}
            <div className="w-px h-3 sm:h-4 bg-white/20" />
          </button>
        ))}
      </div>

      {/* Gradient overlays for smooth edges */}
      <div className="absolute top-0 left-0 w-8 sm:w-16 h-full bg-gradient-to-r from-gray-900/90 to-transparent pointer-events-none" />
      <div className="absolute top-0 right-0 w-8 sm:w-16 h-full bg-gradient-to-l from-gray-900/90 to-transparent pointer-events-none" />
      
    </div>
  )
}
