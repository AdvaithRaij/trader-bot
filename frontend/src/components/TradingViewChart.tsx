import { useEffect, useRef, useState, useCallback } from 'react'
import { createChart, ColorType, LineStyle, CandlestickSeries } from 'lightweight-charts'
import type { IChartApi, ISeriesApi } from 'lightweight-charts'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const RATE_LIMIT_MS = 5000 // 5 seconds between API calls

export interface ChartProps {
  symbol: string
  entryPrice?: number
  stopLoss?: number
  target1?: number
  target2?: number
  currentPrice?: number
  direction?: 'BUY' | 'SELL'
  height?: number
  timeframe?: string
  onTimeframeChange?: (change: number, changePercent: number) => void
}

interface CandleData {
  time: number
  open: number
  high: number
  low: number
  close: number
}

// Global rate limiter to prevent excessive API calls
let lastGlobalFetchTime = 0

export function TradingViewChart({
  symbol,
  entryPrice,
  stopLoss,
  target1,
  target2,
  direction = 'BUY',
  height = 400,
  timeframe = '5m',
  onTimeframeChange
}: ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const candlesRef = useRef<CandleData[]>([])
  const oldestTimeRef = useRef<number | null>(null)
  const isLoadingMoreRef = useRef(false)
  const scrollDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Days of data based on timeframe
  const getDaysForTimeframe = useCallback((tf: string): number => {
    const map: Record<string, number> = {
      '1m': 2, '5m': 5, '15m': 10, '30m': 15,
      '1H': 30, '4H': 60, '1D': 365, '1W': 730
    }
    return map[tf] || 5
  }, [])

  // Fetch candle data from API (with strict 5-second rate limiting)
  const fetchCandles = useCallback(async (
    endTime?: number,
    skipRateLimit = false
  ): Promise<{ candles: CandleData[], firstTime: number | null, change: number, changePercent: number }> => {
    // Global rate limit: max 1 request per 5 seconds
    const now = Date.now()
    if (!skipRateLimit && now - lastGlobalFetchTime < RATE_LIMIT_MS) {
      console.log(`Rate limited: wait ${Math.ceil((RATE_LIMIT_MS - (now - lastGlobalFetchTime)) / 1000)}s`)
      return { candles: [], firstTime: null, change: 0, changePercent: 0 }
    }
    lastGlobalFetchTime = now

    try {
      const days = getDaysForTimeframe(timeframe)
      let url = `${API_BASE}/api/stocks/${symbol}/candles?timeframe=${timeframe}&days=${days}`
      if (endTime) {
        url += `&end_time=${endTime}`
      }

      const response = await fetch(url)
      const data = await response.json()

      if (data.candles && data.candles.length > 0) {
        return {
          candles: data.candles,
          firstTime: data.firstCandleTime,
          change: data.change || 0,
          changePercent: data.changePercent || 0
        }
      }
      return { candles: [], firstTime: null, change: 0, changePercent: 0 }
    } catch (error) {
      console.error('Failed to fetch candles:', error)
      return { candles: [], firstTime: null, change: 0, changePercent: 0 }
    }
  }, [symbol, timeframe, getDaysForTimeframe])

  // Load more historical data when scrolling left
  const loadMoreData = useCallback(async () => {
    if (isLoadingMoreRef.current || !oldestTimeRef.current || !candleSeriesRef.current) return

    isLoadingMoreRef.current = true
    setIsLoadingMore(true)

    const result = await fetchCandles(oldestTimeRef.current - 1)

    if (result.candles.length > 0) {
      const newCandles = result.candles.filter(c => c.time < (oldestTimeRef.current || 0))
      if (newCandles.length > 0) {
        const allCandles = [...newCandles, ...candlesRef.current]
        candlesRef.current = allCandles
        candleSeriesRef.current.setData(allCandles as any)
        oldestTimeRef.current = newCandles[0].time
      }
    }

    setIsLoadingMore(false)
    // Cooldown before allowing next load (additional 5 seconds on top of rate limit)
    setTimeout(() => {
      isLoadingMoreRef.current = false
    }, 5000)
  }, [fetchCandles])

  // Initialize chart and fetch data
  useEffect(() => {
    if (!chartContainerRef.current) return

    // Reset refs for new symbol/timeframe
    candlesRef.current = []
    oldestTimeRef.current = null
    isLoadingMoreRef.current = false
    setIsLoading(true)
    setIsLoadingMore(false)

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#9ca3af'
      },
      grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.4)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.4)' }
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: 'rgba(197, 203, 206, 0.3)' },
      timeScale: {
        borderColor: 'rgba(197, 203, 206, 0.3)',
        timeVisible: true,
        secondsVisible: false
      }
    })

    chartRef.current = chart

    // Add candlestick series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderDownColor: '#ef4444',
      borderUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      wickUpColor: '#22c55e'
    })
    candleSeriesRef.current = candleSeries as any

    // Fetch initial data (skip rate limit for initial load)
    setError(null)
    fetchCandles(undefined, true).then(result => {
      if (result.candles.length > 0) {
        candlesRef.current = result.candles
        candleSeries.setData(result.candles as any)
        oldestTimeRef.current = result.firstTime
        setError(null)

        // Notify parent of timeframe change stats
        if (onTimeframeChange) {
          onTimeframeChange(result.change, result.changePercent)
        }

        // Add price lines
        if (entryPrice) {
          candleSeries.createPriceLine({
            price: entryPrice, color: '#3b82f6', lineWidth: 2,
            lineStyle: LineStyle.Solid, axisLabelVisible: true, title: 'Entry'
          })
        }
        if (stopLoss) {
          candleSeries.createPriceLine({
            price: stopLoss, color: '#ef4444', lineWidth: 2,
            lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: 'SL'
          })
        }
        if (target1) {
          candleSeries.createPriceLine({
            price: target1, color: '#22c55e', lineWidth: 2,
            lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: 'T1'
          })
        }
        if (target2) {
          candleSeries.createPriceLine({
            price: target2, color: '#eab308', lineWidth: 2,
            lineStyle: LineStyle.Dotted, axisLabelVisible: true, title: 'T2'
          })
        }

        chart.timeScale().fitContent()
      } else {
        // No data received - show error with retry option
        setError('Unable to load chart data. API rate limit may have been reached.')
      }
      setIsLoading(false)
    }).catch(err => {
      console.error('Chart fetch error:', err)
      setError('Failed to load chart data. Please try again.')
      setIsLoading(false)
    })

    // Handle scroll to load more data (heavily debounced - 1 second after scroll stops)
    const timeScale = chart.timeScale()
    const handleVisibleRangeChange = (range: { from: number; to: number } | null) => {
      // Clear any pending debounce
      if (scrollDebounceRef.current) {
        clearTimeout(scrollDebounceRef.current)
      }

      // Only trigger if scrolled to the left edge
      if (range && range.from < 5 && !isLoadingMoreRef.current) {
        scrollDebounceRef.current = setTimeout(() => {
          loadMoreData()
        }, 1000) // Wait 1 second after scroll stops
      }
    }
    timeScale.subscribeVisibleLogicalRangeChange(handleVisibleRangeChange)

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      if (scrollDebounceRef.current) {
        clearTimeout(scrollDebounceRef.current)
      }
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, entryPrice, stopLoss, target1, target2, height, timeframe, retryCount])

  return (
    <div className="relative rounded-lg overflow-hidden bg-gray-900/50 border border-gray-700">
      {/* Chart header */}
      <div className="absolute top-2 left-2 z-10 flex items-center gap-2">
        <span className="text-lg font-bold text-white">{symbol}</span>
        <span className="text-xs text-gray-400 px-1.5 py-0.5 bg-gray-800 rounded">{timeframe}</span>
        {direction && (
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
            direction === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}>
            {direction}
          </span>
        )}
      </div>

      {/* Initial loading spinner */}
      {isLoading && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 z-20">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="text-xs text-gray-400">Loading chart...</span>
          </div>
        </div>
      )}

      {/* Error state with retry button */}
      {error && !isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 z-20">
          <div className="flex flex-col items-center gap-3 text-center px-4">
            <svg className="w-10 h-10 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span className="text-sm text-gray-300">{error}</span>
            <button
              onClick={() => {
                setError(null)
                setIsLoading(true)
                setRetryCount(prev => prev + 1)
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Loading more indicator (top-right corner) */}
      {isLoadingMore && !isLoading && !error && (
        <div className="absolute top-2 right-2 z-10 flex items-center gap-2 bg-gray-800/90 px-2 py-1 rounded">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
          <span className="text-xs text-gray-300">Loading history...</span>
        </div>
      )}

      <div ref={chartContainerRef} className="w-full" style={{ height }} />
    </div>
  )
}

