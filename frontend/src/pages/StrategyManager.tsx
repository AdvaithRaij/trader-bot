import React, { useState, useEffect } from 'react'
import {
  Play,
  Pause,
  RefreshCw,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  XCircle,
  Activity,
  Target,
  Shield,
  Sparkles
} from 'lucide-react'
import { cn, formatCurrency, formatPercentage, getPercentageColor } from '../lib/utils'
import { apiService } from '../lib/trading-api'
import type { Strategy, TradeSignal } from '../lib/trading-api'
import { AIStrategyCreator } from '../components/AIStrategyCreator'

interface StrategyCardProps {
  strategy: Strategy
  onToggle: (strategyId: string) => void
  onRun: (strategyId: string) => void
  isRunning: boolean
}

function StrategyCard({ strategy, onToggle, onRun, isRunning }: StrategyCardProps) {
  const isActive = strategy.status === 'ACTIVE'
  const isPaused = strategy.status === 'PAUSED'
  
  return (
    <div className="glass-card p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h3 className="text-lg font-semibold text-white">{strategy.name}</h3>
            <span className={cn(
              "px-2 py-1 text-xs font-medium rounded-full",
              isActive && "bg-green-500/20 text-green-400",
              isPaused && "bg-yellow-500/20 text-yellow-400",
              strategy.status === 'DISABLED' && "bg-red-500/20 text-red-400"
            )}>
              {strategy.status}
            </span>
          </div>
          <p className="text-sm text-gray-400">{strategy.description}</p>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-400 mb-1">Total Trades</p>
          <p className="text-lg font-bold text-white">{strategy.performance.totalTrades}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">Win Rate</p>
          <p className={cn("text-lg font-bold", getPercentageColor(strategy.performance.winRate - 50))}>
            {strategy.performance.winRate.toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">Total P&L</p>
          <p className={cn("text-lg font-bold", getPercentageColor(strategy.performance.totalPnl))}>
            {formatCurrency(strategy.performance.totalPnl)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">Avg P&L</p>
          <p className={cn("text-lg font-bold", getPercentageColor(strategy.performance.avgPnl))}>
            {formatCurrency(strategy.performance.avgPnl)}
          </p>
        </div>
      </div>

      {/* Configuration */}
      <div className="space-y-3 mb-4 p-4 bg-white/5 rounded-lg">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Stock Picking:</span>
          <span className="text-white font-medium">{strategy.stockPicking.type.replace('_', ' ')}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Execution:</span>
          <span className="text-white font-medium">{strategy.execution.type.replace('_', ' ')}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Stop Loss / Target:</span>
          <span className="text-white font-medium">
            {strategy.execution.stopLossPercent}% / {strategy.execution.takeProfitPercent}%
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Max Positions:</span>
          <span className="text-white font-medium">{strategy.riskManagement.maxOpenPositions}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Position Size:</span>
          <span className="text-white font-medium">{strategy.riskManagement.maxPositionSize}%</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center space-x-3">
        <button
          onClick={() => onToggle(strategy.strategyId)}
          className={cn(
            "flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-lg transition-colors",
            isActive 
              ? "bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30" 
              : "bg-green-500/20 text-green-400 hover:bg-green-500/30"
          )}
        >
          {isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          <span>{isActive ? 'Pause' : 'Activate'}</span>
        </button>
        <button
          onClick={() => onRun(strategy.strategyId)}
          disabled={isRunning}
          className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded-lg transition-colors disabled:opacity-50"
        >
          <Activity className={cn("w-4 h-4", isRunning && "animate-pulse")} />
          <span>{isRunning ? 'Running...' : 'Run Now'}</span>
        </button>
      </div>
    </div>
  )
}

export function StrategyManager() {
  const [isLoading, setIsLoading] = useState(true)
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [runningStrategy, setRunningStrategy] = useState<string | null>(null)
  const [generatedSignals, setGeneratedSignals] = useState<TradeSignal[]>([])
  const [error, setError] = useState<string | null>(null)

  const loadStrategies = async () => {
    try {
      setError(null)
      const response = await apiService.getStrategies()
      // Backend returns array directly, not wrapped in object
      setStrategies(Array.isArray(response) ? response : [])
    } catch (err) {
      console.error('Error loading strategies:', err)
      setError('Failed to load strategies. Make sure the backend is running and strategies are seeded.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadStrategies()
  }, [])

  const handleToggle = async (strategyId: string) => {
    try {
      await apiService.toggleStrategy(strategyId)
      await loadStrategies()
    } catch (err) {
      console.error('Error toggling strategy:', err)
      alert('Failed to toggle strategy')
    }
  }

  const handleRun = async (strategyId: string) => {
    try {
      setRunningStrategy(strategyId)
      setGeneratedSignals([])
      
      const response = await apiService.runStrategy(strategyId)
      setGeneratedSignals(response.signals)
      
      if (response.signals.length === 0) {
        alert('No signals generated. Try refreshing news or adjusting strategy filters.')
      }
    } catch (err) {
      console.error('Error running strategy:', err)
      alert('Failed to run strategy')
    } finally {
      setRunningStrategy(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="flex items-center space-x-3">
          <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
          <span className="text-lg text-gray-300">Loading strategies...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="glass-card p-6 max-w-md">
          <div className="flex items-center space-x-3 text-red-400 mb-4">
            <AlertCircle className="w-6 h-6" />
            <span className="text-lg font-semibold">Error</span>
          </div>
          <p className="text-gray-300 mb-4">{error}</p>
          <p className="text-sm text-gray-400 mb-4">
            Run: <code className="bg-white/10 px-2 py-1 rounded">python backend/src/seed_strategies.py</code>
          </p>
          <button
            onClick={loadStrategies}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const activeStrategies = strategies.filter(s => s.status === 'ACTIVE')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold gradient-text">Strategy Manager</h1>
          <p className="text-gray-400 mt-1 text-sm sm:text-base">
            Manage and monitor your trading strategies
          </p>
        </div>
        <button
          onClick={loadStrategies}
          className="flex items-center space-x-2 px-4 py-2 glass rounded-lg hover:bg-white/10 transition-colors mt-4 sm:mt-0"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Active Strategies</p>
              <p className="text-2xl font-bold text-white">{activeStrategies.length}/{strategies.length}</p>
            </div>
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Activity className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total Trades</p>
              <p className="text-2xl font-bold text-white">
                {strategies.reduce((sum, s) => sum + s.performance.totalTrades, 0)}
              </p>
            </div>
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <TrendingUp className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total P&L</p>
              <p className={cn(
                "text-2xl font-bold",
                getPercentageColor(strategies.reduce((sum, s) => sum + s.performance.totalPnl, 0))
              )}>
                {formatCurrency(strategies.reduce((sum, s) => sum + s.performance.totalPnl, 0))}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* AI Strategy Creator */}
      <AIStrategyCreator onStrategyCreated={loadStrategies} />

      {/* Strategy Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {strategies.map((strategy) => (
          <StrategyCard
            key={strategy.strategyId}
            strategy={strategy}
            onToggle={handleToggle}
            onRun={handleRun}
            isRunning={runningStrategy === strategy.strategyId}
          />
        ))}
      </div>

      {/* Generated Signals */}
      {generatedSignals.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Generated Signals ({generatedSignals.length})
          </h3>
          <div className="space-y-3">
            {generatedSignals.map((signal, index) => (
              <div key={index} className="p-4 bg-white/5 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg font-bold text-white">{signal.symbol}</span>
                    <span className={cn(
                      "px-2 py-1 text-xs font-medium rounded-full",
                      signal.direction === 'BUY' 
                        ? "bg-green-500/20 text-green-400" 
                        : "bg-red-500/20 text-red-400"
                    )}>
                      {signal.direction}
                    </span>
                  </div>
                  <span className={cn(
                    "text-sm font-medium",
                    signal.confidence >= 80 ? "text-green-400" :
                    signal.confidence >= 60 ? "text-yellow-400" : "text-red-400"
                  )}>
                    {signal.confidence}% confidence
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-4 text-sm mb-2">
                  <div>
                    <span className="text-gray-400">Entry: </span>
                    <span className="text-white font-medium">{formatCurrency(signal.entryPrice)}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">SL: </span>
                    <span className="text-red-400 font-medium">{formatCurrency(signal.stopLoss)}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">T1: </span>
                    <span className="text-green-400 font-medium">{formatCurrency(signal.target1)}</span>
                  </div>
                  {signal.target2 && (
                    <div>
                      <span className="text-gray-400">T2: </span>
                      <span className="text-green-400 font-medium">{formatCurrency(signal.target2)}</span>
                    </div>
                  )}
                </div>
                <p className="text-sm text-gray-300 mb-2">{signal.reasoning}</p>
                {signal.aiAnalysis && (
                  <div className="flex items-center space-x-4 text-xs text-gray-400">
                    {signal.aiAnalysis.expectedMove && (
                      <span>Expected: {signal.aiAnalysis.expectedMove}</span>
                    )}
                    {signal.aiAnalysis.riskRewardRatio && (
                      <span>R:R = {signal.aiAnalysis.riskRewardRatio.toFixed(2)}</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

