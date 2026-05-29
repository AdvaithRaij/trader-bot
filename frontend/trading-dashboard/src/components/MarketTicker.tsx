import React, { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { cn, formatCurrency, formatPercentage, getPercentageColor } from '../lib/utils'
import { mockStocks } from '../data/mockData'

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

  useEffect(() => {
    // Combine market indices and top stocks for the ticker
    const marketIndices: TickerItem[] = [
      {
        symbol: 'NIFTY 50',
        name: 'NIFTY',
        price: 19847.9,
        change: 101.2,
        changePercent: 0.52,
        type: 'index'
      },
      {
        symbol: 'SENSEX',
        name: 'BSE SENSEX',
        price: 66901.7,
        change: 274.8,
        changePercent: 0.41,
        type: 'index'
      },
      {
        symbol: 'BANKNIFTY',
        name: 'BANK NIFTY',
        price: 45234.6,
        change: 298.5,
        changePercent: 0.66,
        type: 'index'
      },
      {
        symbol: 'NIFTY IT',
        name: 'NIFTY IT',
        price: 34567.8,
        change: 456.7,
        changePercent: 1.34,
        type: 'index'
      },
      {
        symbol: 'NIFTY AUTO',
        name: 'NIFTY AUTO',
        price: 15432.1,
        change: -123.4,
        changePercent: -0.79,
        type: 'index'
      },
      {
        symbol: 'NIFTY PHARMA',
        name: 'NIFTY PHARMA',
        price: 12345.6,
        change: 89.2,
        changePercent: 0.73,
        type: 'index'
      }
    ]

    // Convert stock data to ticker format and select top 20 by volume
    const topStocks: TickerItem[] = mockStocks
      .sort((a, b) => b.volume - a.volume)
      .slice(0, 20)
      .map(stock => ({
        symbol: stock.symbol,
        price: stock.price,
        change: stock.change,
        changePercent: stock.changePercent,
        type: 'stock' as const
      }))

    // Add some additional popular stocks for demo
    const additionalStocks: TickerItem[] = [
      { symbol: 'ADANIGREEN', price: 987.65, change: 45.30, changePercent: 4.82, type: 'stock' },
      { symbol: 'BAJFINANCE', price: 6234.50, change: -67.80, changePercent: -1.08, type: 'stock' },
      { symbol: 'LTIM', price: 4567.90, change: 123.45, changePercent: 2.78, type: 'stock' },
      { symbol: 'TATAMOTORS', price: 567.80, change: 12.30, changePercent: 2.21, type: 'stock' },
      { symbol: 'SUNPHARMA', price: 1089.50, change: -15.60, changePercent: -1.41, type: 'stock' },
      { symbol: 'SBIN', price: 543.20, change: 8.90, changePercent: 1.67, type: 'stock' },
      { symbol: 'MARUTI', price: 9876.40, change: 234.50, changePercent: 2.43, type: 'stock' },
      { symbol: 'TITAN', price: 3210.80, change: -45.70, changePercent: -1.40, type: 'stock' }
    ]

    // Combine and duplicate for seamless scrolling
    const allItems = [...marketIndices, ...topStocks, ...additionalStocks]
    setTickerItems([...allItems, ...allItems]) // Duplicate for continuous scroll
  }, [])

  const handleMouseEnter = () => setIsPaused(true)
  const handleMouseLeave = () => setIsPaused(false)

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
          <div 
            key={`${item.symbol}-${index}`}
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
          </div>
        ))}
      </div>

      {/* Gradient overlays for smooth edges */}
      <div className="absolute top-0 left-0 w-8 sm:w-16 h-full bg-gradient-to-r from-gray-900/90 to-transparent pointer-events-none" />
      <div className="absolute top-0 right-0 w-8 sm:w-16 h-full bg-gradient-to-l from-gray-900/90 to-transparent pointer-events-none" />
      
    </div>
  )
}
