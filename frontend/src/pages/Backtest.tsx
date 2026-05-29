import React, { useState, useEffect } from 'react'
import { apiService } from '../lib/trading-api'

interface Strategy {
  id: string
  name: string
  description: string
  stockPickingType: string | null
  executionType: string | null
}

interface BacktestResult {
  strategyId: string
  strategyName: string
  startDate: string
  endDate: string
  initialCapital: number
  finalCapital: number
  totalPnl: number
  totalPnlPercent: number
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  avgWin: number
  avgLoss: number
  maxDrawdown: number
  maxDrawdownPercent: number
  sharpeRatio: number
  profitFactor: number
}

export function Backtest() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState<string>('')
  const [startDate, setStartDate] = useState<string>('2024-01-01')
  const [endDate, setEndDate] = useState<string>('2024-12-01')
  const [initialCapital, setInitialCapital] = useState<number>(100000)
  const [symbols, setSymbols] = useState<string>('RELIANCE,TCS,INFY,HDFCBANK')
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStrategies()
  }, [])

  const loadStrategies = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/backtest/strategies')
      const data = await response.json()
      setStrategies(data.strategies || [])
      if (data.strategies?.length > 0) {
        setSelectedStrategy(data.strategies[0].id)
      }
    } catch (e) {
      console.error('Error loading strategies:', e)
    }
  }

  const runBacktest = async () => {
    if (!selectedStrategy) return
    
    setIsRunning(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('http://localhost:8001/api/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategyId: selectedStrategy,
          startDate,
          endDate,
          initialCapital,
          symbols: symbols.split(',').map(s => s.trim())
        })
      })
      const data = await response.json()
      
      if (data.success) {
        setResult(data.result)
      } else {
        setError(data.error || 'Backtest failed')
      }
    } catch (e) {
      setError('Failed to run backtest')
    } finally {
      setIsRunning(false)
    }
  }

  const formatCurrency = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
  const formatPercent = (n: number) => `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">📊 Strategy Backtesting</h1>
        <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full text-sm">
          Historical Analysis
        </span>
      </div>

      {/* Configuration Panel */}
      <div className="bg-[#1e222d] rounded-xl p-6 border border-[#2a2e39]">
        <h2 className="text-lg font-semibold text-white mb-4">Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Strategy</label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full bg-[#131722] border border-[#2a2e39] rounded-lg px-3 py-2 text-white"
            >
              {strategies.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full bg-[#131722] border border-[#2a2e39] rounded-lg px-3 py-2 text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full bg-[#131722] border border-[#2a2e39] rounded-lg px-3 py-2 text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Initial Capital (₹)</label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              className="w-full bg-[#131722] border border-[#2a2e39] rounded-lg px-3 py-2 text-white"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-400 mb-1">Symbols (comma-separated)</label>
            <input
              type="text"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              className="w-full bg-[#131722] border border-[#2a2e39] rounded-lg px-3 py-2 text-white"
              placeholder="RELIANCE,TCS,INFY"
            />
          </div>
        </div>
        <button
          onClick={runBacktest}
          disabled={isRunning || !selectedStrategy}
          className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isRunning ? (
            <>
              <span className="animate-spin">⏳</span> Running...
            </>
          ) : (
            <>🚀 Run Backtest</>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-400">
          ❌ {error}
        </div>
      )}

      {/* Results Panel */}
      {result && (
        <div className="space-y-6">
          <div className="bg-[#1e222d] rounded-xl p-6 border border-[#2a2e39]">
            <h2 className="text-lg font-semibold text-white mb-4">Results: {result.strategyName}</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="Total P&L" value={formatCurrency(result.totalPnl)} 
                          color={result.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'} />
              <MetricCard label="Return" value={formatPercent(result.totalPnlPercent)} 
                          color={result.totalPnlPercent >= 0 ? 'text-green-400' : 'text-red-400'} />
              <MetricCard label="Win Rate" value={`${result.winRate.toFixed(1)}%`} 
                          color={result.winRate >= 50 ? 'text-green-400' : 'text-yellow-400'} />
              <MetricCard label="Total Trades" value={result.totalTrades.toString()} color="text-blue-400" />
              <MetricCard label="Winning Trades" value={result.winningTrades.toString()} color="text-green-400" />
              <MetricCard label="Losing Trades" value={result.losingTrades.toString()} color="text-red-400" />
              <MetricCard label="Avg Win" value={formatCurrency(result.avgWin)} color="text-green-400" />
              <MetricCard label="Avg Loss" value={formatCurrency(result.avgLoss)} color="text-red-400" />
              <MetricCard label="Max Drawdown" value={formatPercent(result.maxDrawdownPercent)} color="text-red-400" />
              <MetricCard label="Sharpe Ratio" value={result.sharpeRatio.toFixed(2)} 
                          color={result.sharpeRatio >= 1 ? 'text-green-400' : 'text-yellow-400'} />
              <MetricCard label="Profit Factor" value={result.profitFactor.toFixed(2)} 
                          color={result.profitFactor >= 1.5 ? 'text-green-400' : 'text-yellow-400'} />
              <MetricCard label="Final Capital" value={formatCurrency(result.finalCapital)} color="text-white" />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-[#131722] rounded-lg p-4">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className={`text-lg font-semibold ${color}`}>{value}</div>
    </div>
  )
}

