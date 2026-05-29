import React, { useState, useEffect, useCallback } from 'react'
import {
  RefreshCw, AlertCircle, Search, Brain, Zap,
  ChevronRight, Play, Square,
  TrendingUp, TrendingDown,
  ArrowRight, XCircle, Loader2
} from 'lucide-react'
import {
  apiService,
  pipelineWebSocket,
  type ScreenerCandidate,
  type TradePlan,
  type ExecutorStatus,
  type PipelineEvent,
  type PipelineStatus,
  type MultiStrategyAnalysis
} from '../lib/trading-api'

type PipelineStage = 'screening' | 'analysis' | 'execution'

export default function Pipeline() {
  const [currentStage, setCurrentStage] = useState<PipelineStage>('screening')
  const [candidates, setCandidates] = useState<ScreenerCandidate[]>([])
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set())
  const [tradePlans, setTradePlans] = useState<TradePlan[]>([])
  const [, setApprovedPlans] = useState<Set<string>>(new Set())
  const [executorStatus, setExecutorStatus] = useState<ExecutorStatus | null>(null)
  const [, setPipelineStatus] = useState<PipelineStatus | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isScreening, setIsScreening] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Multi-strategy analysis state
  const [multiStrategyAnalyses, setMultiStrategyAnalyses] = useState<MultiStrategyAnalysis[]>([])
  const [isMultiAnalyzing, setIsMultiAnalyzing] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<'fundamental' | 'news_based' | 'combined'>('combined')

  const loadData = useCallback(async () => {
    try {
      setError(null)
      const [screenerData, plansData, executorData, statusData] = await Promise.all([
        apiService.getScreenerResults().catch(() => ({ candidates: [], timestamp: '', market_context: null, total_scanned: 0, filters_applied: [] })),
        apiService.getTradePlans().catch(() => ({ plans: [], count: 0 })),
        apiService.getExecutorStatus().catch(() => null),
        apiService.getPipelineStatus().catch(() => null)
      ])

      setCandidates(screenerData.candidates || [])
      setTradePlans(plansData.plans || [])
      setExecutorStatus(executorData)
      setPipelineStatus(statusData)
    } catch (err) {
      console.error('Error loading pipeline data:', err)
      setError('Failed to load pipeline data')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleRunScreening = async () => {
    try {
      setIsScreening(true)
      setError(null)
      // Clear previous results when starting new screening
      setMultiStrategyAnalyses([])
      setTradePlans([])
      setApprovedPlans(new Set())
      setSelectedCandidates(new Set())

      const result = await apiService.triggerScreening()
      if (result.success) {
        await loadData()
      } else {
        setError(result.message || 'Screening failed')
      }
    } catch (err) {
      console.error('Screening error:', err)
      setError('Failed to run screening')
    } finally {
      setIsScreening(false)
    }
  }

  const handleSelectCandidate = (symbol: string) => {
    setSelectedCandidates(prev => {
      const next = new Set(prev)
      if (next.has(symbol)) {
        next.delete(symbol)
      } else {
        next.add(symbol)
      }
      return next
    })
  }

  const handleSelectAllCandidates = () => {
    if (selectedCandidates.size === candidates.length) {
      setSelectedCandidates(new Set())
    } else {
      setSelectedCandidates(new Set(candidates.map(c => c.symbol)))
    }
  }

  const handleMultiStrategyAnalysis = async () => {
    // Use selected candidates, or all candidates if none selected
    const symbolsToAnalyze = selectedCandidates.size > 0
      ? Array.from(selectedCandidates)
      : candidates.map(c => c.symbol)

    if (symbolsToAnalyze.length === 0) {
      setError('No stocks selected for analysis')
      return
    }

    setIsMultiAnalyzing(true)
    setError(null)

    try {
      const result = await apiService.runMultiStrategyAnalysis(symbolsToAnalyze)
      if (result.success && result.analyses) {
        setMultiStrategyAnalyses(result.analyses)
        setCurrentStage('analysis')
      } else {
        setError(result.message || 'Multi-strategy analysis failed')
      }
    } catch (err) {
      console.error('Multi-strategy analysis error:', err)
      setError('Failed to run multi-strategy analysis')
    } finally {
      setIsMultiAnalyzing(false)
    }
  }

  const handlePipelineEvent = useCallback((event: PipelineEvent) => {
    switch (event.type) {
      case 'screening_complete':
        setCandidates(event.data.candidates || [])
        break
      case 'analysis_complete':
        setTradePlans(prev => {
          const existing = prev.findIndex(p => p.symbol === event.data.plan.symbol)
          if (existing >= 0) {
            const updated = [...prev]
            updated[existing] = event.data.plan
            return updated
          }
          return [...prev, event.data.plan]
        })
        break
      case 'trade_executed':
      case 'position_update':
        loadData()
        break
    }
  }, [loadData])

  // Initial data load
  useEffect(() => {
    loadData()
  }, [loadData])

  // WebSocket connection - separate effect to prevent reconnection loops
  useEffect(() => {
    pipelineWebSocket.connect(handlePipelineEvent, () => {})

    return () => {
      pipelineWebSocket.disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Only connect once on mount

  // Periodic refresh
  useEffect(() => {
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [loadData])

  const handleSquareOff = async (symbol: string) => {
    try {
      await apiService.squareOffPosition(symbol)
      loadData()
    } catch (err) {
      console.error('Failed to square off:', err)
    }
  }

  const handleSquareOffAll = async () => {
    if (!confirm('Are you sure you want to square off all positions?')) return
    try {
      await apiService.squareOffAll()
      loadData()
    } catch (err) {
      console.error('Failed to square off all:', err)
    }
  }

  const stages: { id: PipelineStage; label: string; icon: React.ReactNode }[] = [
    { id: 'screening', label: 'Stock Screening', icon: <Search className="w-5 h-5" /> },
    { id: 'analysis', label: 'Multi-Strategy Analysis', icon: <Brain className="w-5 h-5" /> },
    { id: 'execution', label: 'Trade Execution', icon: <Zap className="w-5 h-5" /> }
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-400" />
      </div>
    )
  }

  return (
    <div className="w-full pb-6">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Trading Pipeline</h1>
          <p className="text-gray-400">3-Stage Approval-Based Trading Workflow</p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700/50 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 mb-6">
          <AlertCircle className="w-5 h-5" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-300 hover:text-white">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Layout: Vertical Stepper + Content */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Left Sidebar - Vertical Stage Stepper */}
        <div className="xl:col-span-1">
          <div className="glass-card p-4 xl:sticky xl:top-6">
            <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wider">Pipeline Stages</h3>
            <div className="space-y-3">
              {stages.map((stage, index) => {
                const isActive = currentStage === stage.id
                const isCompleted =
                  (stage.id === 'screening' && candidates.length > 0) ||
                  (stage.id === 'analysis' && multiStrategyAnalyses.length > 0) ||
                  (stage.id === 'execution' && (executorStatus?.open_positions || 0) > 0)

                return (
                  <div key={stage.id} className="relative">
                    {/* Connector Line */}
                    {index < stages.length - 1 && (
                      <div className="absolute left-6 top-12 w-0.5 h-8 bg-gray-700/50" />
                    )}

                    <button
                      onClick={() => setCurrentStage(stage.id)}
                      className={`w-full flex items-start gap-3 p-3 rounded-lg transition-all text-left ${
                        isActive
                          ? 'bg-blue-500/20 border border-blue-500/50'
                          : 'bg-gray-800/30 border border-gray-700/30 hover:bg-gray-800/50 hover:border-gray-600/50'
                      }`}
                    >
                      <div className={`p-2 rounded-lg flex-shrink-0 ${
                        isActive ? 'bg-blue-500/30 text-blue-400' :
                        isCompleted ? 'bg-green-500/20 text-green-400' :
                        'bg-gray-700/50 text-gray-500'
                      }`}>
                        {stage.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-gray-500">Stage {index + 1}</span>
                          {isCompleted && !isActive && (
                            <div className="w-2 h-2 bg-green-400 rounded-full" />
                          )}
                        </div>
                        <div className={`font-medium text-sm ${isActive ? 'text-blue-400' : 'text-white'}`}>
                          {stage.label}
                        </div>
                        {stage.id === 'screening' && candidates.length > 0 && (
                          <div className="text-xs text-gray-400 mt-1">{candidates.length} candidates</div>
                        )}
                        {stage.id === 'analysis' && multiStrategyAnalyses.length > 0 && (
                          <div className="text-xs text-gray-400 mt-1">{multiStrategyAnalyses.length} analyses</div>
                        )}
                        {stage.id === 'execution' && (executorStatus?.open_positions || 0) > 0 && (
                          <div className="text-xs text-gray-400 mt-1">{executorStatus?.open_positions} positions</div>
                        )}
                      </div>
                    </button>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Right Content Area */}
        <div className="xl:col-span-3">
          <div className="glass-card p-6">
        {/* STAGE 1: SCREENING */}
        {currentStage === 'screening' && (
          <div className="space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                  <Search className="w-5 h-5 text-blue-400" />
                  Stock Screening
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Scan NIFTY 200 universe for high-probability setups
                </p>
                <details className="mt-3 max-w-2xl">
                  <summary className="text-xs text-blue-400 cursor-pointer hover:text-blue-300 select-none">
                    View Screening Criteria
                  </summary>
                  <div className="mt-2 p-4 bg-gray-800/50 border border-gray-700/50 rounded-lg text-xs text-gray-300 space-y-1">
                    <div className="font-semibold text-blue-400 mb-2">Filtering Criteria:</div>
                    <div>• Turnover ≥ ₹10 Cr/day (liquidity)</div>
                    <div>• RVOL ≥ 1.5x (vs 10-day avg)</div>
                    <div>• ATR% between 1.5% - 5.0% (volatility)</div>
                    <div>• Market Cap ≥ ₹5,000 Cr</div>
                    <div>• RSI between 30 - 70 (not overbought/oversold)</div>
                    <div>• Gap &lt; 3% (avoid large gaps)</div>
                    <div className="font-semibold text-blue-400 mt-3 mb-2">Scoring Weights:</div>
                    <div>• Liquidity: 30% | Volatility: 25% | Trend: 25% | News: 20%</div>
                  </div>
                </details>
              </div>
              <button
                onClick={handleRunScreening}
                disabled={isScreening}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 flex-shrink-0"
              >
                {isScreening ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {isScreening ? 'Scanning...' : 'Run Screener'}
              </button>
            </div>

            {candidates.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No screened candidates yet</p>
                <p className="text-sm mt-1">Click "Run Screener" to find trading opportunities</p>
              </div>
            ) : (
              <>
                {/* Candidates Table */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-700/50">
                        <th className="text-left py-3 px-2 text-xs font-medium text-gray-400 uppercase tracking-wider">
                          <input
                            type="checkbox"
                            checked={selectedCandidates.size === candidates.length}
                            onChange={handleSelectAllCandidates}
                            className="rounded border-gray-600 bg-gray-700 text-blue-500"
                          />
                        </th>
                        <th className="text-left py-3 px-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Symbol</th>
                        <th className="text-right py-3 px-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Price</th>
                        <th className="text-center py-3 px-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Change</th>
                        <th className="text-center py-3 px-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Score</th>
                        <th className="text-center py-3 px-3 text-xs font-medium text-gray-400 uppercase tracking-wider">RSI</th>
                        <th className="text-center py-3 px-3 text-xs font-medium text-gray-400 uppercase tracking-wider">RVOL</th>
                        <th className="text-center py-3 px-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Trend</th>
                      </tr>
                    </thead>
                    <tbody>
                      {candidates.map(candidate => (
                        <tr
                          key={candidate.symbol}
                          className={`border-b border-gray-700/30 cursor-pointer transition-colors ${
                            selectedCandidates.has(candidate.symbol)
                              ? 'bg-blue-500/10'
                              : 'hover:bg-gray-800/30'
                          }`}
                          onClick={() => handleSelectCandidate(candidate.symbol)}
                        >
                          <td className="py-3 px-2">
                            <input
                              type="checkbox"
                              checked={selectedCandidates.has(candidate.symbol)}
                              onChange={() => {}}
                              className="rounded border-gray-600 bg-gray-700 text-blue-500"
                            />
                          </td>
                          <td className="py-3 px-3">
                            <div className="font-medium text-white">{candidate.symbol}</div>
                            <div className="text-xs text-gray-500">{candidate.name || 'Stock'}</div>
                          </td>
                          <td className="py-3 px-3 text-right">
                            <div className="text-white">₹{candidate.current_price?.toFixed(2)}</div>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <div className={`inline-flex items-center px-2 py-1 rounded text-sm font-medium ${
                              (candidate.change_percent || 0) >= 0
                                ? 'bg-green-500/20 text-green-400'
                                : 'bg-red-500/20 text-red-400'
                            }`}>
                              {(candidate.change_percent || 0) >= 0 ? '+' : ''}{candidate.change_percent?.toFixed(2)}%
                            </div>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <div className="text-lg font-bold text-blue-400">{candidate.screening_score?.toFixed(0) || 0}</div>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <div className={`text-base font-bold ${
                              (candidate.rsi || 50) < 30 ? 'text-green-400' :
                              (candidate.rsi || 50) > 70 ? 'text-red-400' : 'text-gray-300'
                            }`}>{candidate.rsi?.toFixed(0) || 'N/A'}</div>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <div className={`text-base font-bold ${
                              (candidate.relative_volume || 1) > 1.5 ? 'text-green-400' :
                              (candidate.relative_volume || 1) < 0.8 ? 'text-red-400' : 'text-gray-300'
                            }`}>{candidate.relative_volume?.toFixed(1) || 'N/A'}x</div>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <div className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              candidate.trend === 'uptrend' ? 'bg-green-500/20 text-green-400' :
                              candidate.trend === 'downtrend' ? 'bg-red-500/20 text-red-400' :
                              'bg-gray-500/20 text-gray-300'
                            }`}>
                              {candidate.trend === 'uptrend' ? <TrendingUp className="w-3 h-3 mr-1" /> :
                               candidate.trend === 'downtrend' ? <TrendingDown className="w-3 h-3 mr-1" /> : null}
                              {candidate.trend || 'N/A'}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="flex justify-end pt-4 border-t border-gray-700/50">
                  <button
                    onClick={handleMultiStrategyAnalysis}
                    disabled={candidates.length === 0 || isMultiAnalyzing}
                    className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:from-blue-600 hover:to-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {isMultiAnalyzing ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Brain className="w-4 h-4" />
                    )}
                    {selectedCandidates.size > 0
                      ? `Analyze Selected (${selectedCandidates.size})`
                      : `Analyze All Stocks (${candidates.length})`
                    }
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* STAGE 2: MULTI-STRATEGY ANALYSIS */}
        {currentStage === 'analysis' && (
          <div className="space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                  <Brain className="w-5 h-5 text-purple-400" />
                  Multi-Strategy Analysis
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Compare 3 AI strategies: Fundamental, News-Based, and Combined
                </p>
                <details className="mt-3 max-w-2xl">
                  <summary className="text-xs text-purple-400 cursor-pointer hover:text-purple-300 select-none">
                    View Strategy Details
                  </summary>
                  <div className="mt-2 p-4 bg-gray-800/50 border border-gray-700/50 rounded-lg text-xs text-gray-300 space-y-2">
                    <div>
                      <span className="font-semibold text-green-400">1. Fundamental Strategy:</span>
                      <div className="ml-4 mt-1 space-y-0.5">
                        <div>• Focus: P/E, EPS, Market Cap, D/E, ROE, Book Value</div>
                        <div>• Style: Conservative, value-based</div>
                        <div>• Stop-Loss: 1-2% | Targets: 3-5%</div>
                        <div>• Timeframe: 2-5 days</div>
                      </div>
                    </div>
                    <div>
                      <span className="font-semibold text-blue-400">2. News-Based Strategy:</span>
                      <div className="ml-4 mt-1 space-y-0.5">
                        <div>• Focus: Sentiment, news impact, timing, momentum</div>
                        <div>• Style: Event-driven, momentum</div>
                        <div>• Stop-Loss: 2-3% | Targets: 4-8%</div>
                        <div>• Timeframe: Intraday to 1 day</div>
                      </div>
                    </div>
                    <div>
                      <span className="font-semibold text-purple-400">3. Combined Strategy:</span>
                      <div className="ml-4 mt-1 space-y-0.5">
                        <div>• Focus: Holistic analysis of all factors</div>
                        <div>• Weights: Technical 35%, Fundamental 30%, News 25%, Market 10%</div>
                        <div>• Style: Balanced, confluence-based</div>
                        <div>• Stop-Loss: 1.5-2.5% | Targets: 3-6%</div>
                        <div>• Timeframe: 1-3 days</div>
                      </div>
                    </div>
                  </div>
                </details>
              </div>
              <div className="flex items-center gap-4 flex-shrink-0">
                <select
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value as any)}
                  className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
                >
                  <option value="combined">Combined Strategy</option>
                  <option value="fundamental">Fundamental Strategy</option>
                  <option value="news_based">News-Based Strategy</option>
                </select>
              </div>
            </div>

            {multiStrategyAnalyses.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No analyses available</p>
                <p className="text-sm mt-1">
                  <button
                    onClick={() => setCurrentStage('screening')}
                    className="text-blue-400 hover:underline"
                  >
                    Go back to screening
                  </button>
                  {' '}and run analysis
                </p>
              </div>
            ) : (
              <>
                <div className="grid gap-4">
                  {multiStrategyAnalyses.map(analysis => {
                    const strategy = analysis.strategies[selectedStrategy]
                    const rec = analysis.recommendation

                    return (
                      <div
                        key={analysis.symbol}
                        className="p-4 rounded-lg border bg-gray-800/50 border-gray-700/50"
                      >
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div>
                              <div className="font-medium text-white text-lg">{analysis.symbol}</div>
                              <div className="text-sm text-gray-500">{analysis.name}</div>
                            </div>
                            <div className={`px-2 py-1 rounded text-xs font-medium ${
                              rec.trade_quality === 'excellent' ? 'bg-green-500/20 text-green-400' :
                              rec.trade_quality === 'good' ? 'bg-blue-500/20 text-blue-400' :
                              rec.trade_quality === 'fair' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-gray-500/20 text-gray-400'
                            }`}>
                              {rec.trade_quality.toUpperCase()}
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <div className="text-white">₹{analysis.current_price?.toFixed(2)}</div>
                              <div className={`text-sm ${(analysis.day_change_pct || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {(analysis.day_change_pct || 0) >= 0 ? '+' : ''}{analysis.day_change_pct?.toFixed(2)}%
                              </div>
                            </div>
                            <div className="text-center px-3 py-1 bg-gray-700/50 rounded">
                              <div className="text-xs text-gray-500">Score</div>
                              <div className="text-lg font-bold text-blue-400">{analysis.screener_score?.toFixed(0) || 0}</div>
                            </div>
                          </div>
                        </div>

                        {/* Strategy Comparison */}
                        <div className="grid grid-cols-3 gap-3 mb-4">
                          {(['fundamental', 'news_based', 'combined'] as const).map(stratId => {
                            const strat = analysis.strategies[stratId]
                            const isSelected = stratId === selectedStrategy
                            const isBest = stratId === rec.best_strategy

                            return (
                              <div
                                key={stratId}
                                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                                  isSelected ? 'bg-blue-500/20 border-blue-500/50' :
                                  isBest ? 'bg-green-500/10 border-green-500/30' :
                                  'bg-gray-700/30 border-gray-600/30 hover:border-gray-500'
                                }`}
                                onClick={() => setSelectedStrategy(stratId)}
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-xs text-gray-400 capitalize">
                                    {stratId.replace('_', '-')}
                                  </span>
                                  {isBest && (
                                    <span className="text-xs bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">
                                      BEST
                                    </span>
                                  )}
                                </div>
                                <div className={`text-lg font-bold ${
                                  strat.direction === 'BUY' ? 'text-green-400' :
                                  strat.direction === 'SELL' ? 'text-red-400' :
                                  'text-gray-400'
                                }`}>
                                  {strat.direction}
                                </div>
                                <div className="text-sm text-gray-400">
                                  {strat.confidence}% conf • R:R {strat.risk_reward?.toFixed(1)}
                                </div>
                              </div>
                            )
                          })}
                        </div>

                        {/* Selected Strategy Details */}
                        <div className="bg-gray-900/50 rounded-lg p-4">
                          <div className="grid grid-cols-4 gap-4 mb-3">
                            <div>
                              <div className="text-xs text-gray-500">Entry</div>
                              <div className="text-white font-medium">₹{strategy.entry?.toFixed(2)}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Stop Loss</div>
                              <div className="text-red-400 font-medium">₹{strategy.stop_loss?.toFixed(2)}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Target 1</div>
                              <div className="text-green-400 font-medium">₹{strategy.target_1?.toFixed(2)}</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500">Risk:Reward</div>
                              <div className={`font-medium ${
                                (strategy.risk_reward || 0) >= 2 ? 'text-green-400' :
                                (strategy.risk_reward || 0) >= 1.5 ? 'text-yellow-400' :
                                'text-red-400'
                              }`}>
                                1:{strategy.risk_reward?.toFixed(1)}
                              </div>
                            </div>
                          </div>
                          <div className="text-sm text-gray-400">
                            <strong className="text-gray-300">Reasoning:</strong> {strategy.reasoning}
                          </div>
                        </div>

                        {/* Recommendation */}
                        <div className="mt-3 p-3 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg border border-blue-500/20">
                          <div className="flex items-center gap-2 mb-1">
                            <Brain className="w-4 h-4 text-purple-400" />
                            <span className="text-sm font-medium text-white">AI Recommendation</span>
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              rec.overall_sentiment === 'bullish' ? 'bg-green-500/20 text-green-400' :
                              rec.overall_sentiment === 'bearish' ? 'bg-red-500/20 text-red-400' :
                              'bg-gray-500/20 text-gray-400'
                            }`}>
                              {rec.overall_sentiment.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-400">{rec.reasoning}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>

                <div className="flex justify-between pt-4 border-t border-gray-700/50">
                  <button
                    onClick={() => setCurrentStage('screening')}
                    className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white transition-colors"
                  >
                    <ChevronRight className="w-4 h-4 rotate-180" />
                    Back to Screening
                  </button>
                  <button
                    onClick={() => setCurrentStage('execution')}
                    className="flex items-center gap-2 px-6 py-3 bg-yellow-500 text-black font-medium rounded-lg hover:bg-yellow-400 transition-colors"
                  >
                    <Zap className="w-4 h-4" />
                    Proceed to Execution
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* STAGE 3: EXECUTION */}
        {currentStage === 'execution' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-400" />
                  Trade Execution & Monitoring
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Monitor active positions and manage exits
                </p>
              </div>
              {(executorStatus?.open_positions || 0) > 0 && (
                <button
                  onClick={handleSquareOffAll}
                  className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                >
                  <Square className="w-4 h-4" />
                  Square Off All
                </button>
              )}
            </div>

            {/* Executor Stats */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700/50">
                <div className="text-gray-500 text-sm">Open Positions</div>
                <div className="text-2xl font-bold text-white">{executorStatus?.open_positions || 0}</div>
              </div>
              <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700/50">
                <div className="text-gray-500 text-sm">Trades Today</div>
                <div className="text-2xl font-bold text-white">
                  {executorStatus?.trades_today || 0}/{executorStatus?.max_trades_per_day || 10}
                </div>
              </div>
              <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700/50">
                <div className="text-gray-500 text-sm">Daily P&L</div>
                <div className={`text-2xl font-bold ${
                  (executorStatus?.daily_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {(executorStatus?.daily_pnl || 0) >= 0 ? '+' : ''}₹{executorStatus?.daily_pnl?.toFixed(2) || '0.00'}
                </div>
              </div>
              <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700/50">
                <div className="text-gray-500 text-sm">Open Risk</div>
                <div className={`text-2xl font-bold ${
                  (executorStatus?.open_risk_percent || 0) > 4 ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {executorStatus?.open_risk_percent?.toFixed(1) || '0.0'}%
                </div>
              </div>
            </div>

            {/* Positions */}
            {(executorStatus?.positions || []).length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Zap className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No active positions</p>
                <p className="text-sm mt-1">
                  Approved trades will appear here once executed
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {executorStatus?.positions?.map((pos: any) => (
                  <div
                    key={pos.symbol}
                    className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          pos.direction === 'LONG' ? 'bg-green-500/20' : 'bg-red-500/20'
                        }`}>
                          {pos.direction === 'LONG' ? (
                            <TrendingUp className="w-5 h-5 text-green-400" />
                          ) : (
                            <TrendingDown className="w-5 h-5 text-red-400" />
                          )}
                        </div>
                        <div>
                          <div className="font-medium text-white">{pos.symbol}</div>
                          <div className="text-sm text-gray-500">
                            {pos.quantity} @ ₹{pos.entry_price?.toFixed(2)}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="text-gray-500 text-xs">Unrealized P&L</div>
                          <div className={`font-medium ${
                            (pos.unrealized_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {(pos.unrealized_pnl || 0) >= 0 ? '+' : ''}₹{pos.unrealized_pnl?.toFixed(2) || '0.00'}
                          </div>
                        </div>
                        <button
                          onClick={() => handleSquareOff(pos.symbol)}
                          className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors text-sm"
                        >
                          Square Off
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-start pt-4 border-t border-gray-700/50">
              <button
                onClick={() => setCurrentStage('analysis')}
                className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                <ChevronRight className="w-4 h-4 rotate-180" />
                Back to Analysis
              </button>
            </div>
          </div>
        )}
          </div>
        </div>
      </div>

      {/* Multi-Strategy Analysis Overlay */}
      {isMultiAnalyzing && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="glass-card p-6 flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
            <p className="text-white">Running Multi-Strategy Analysis...</p>
            <p className="text-gray-400 text-sm">Analyzing with Fundamental, News-Based, and Combined strategies</p>
          </div>
        </div>
      )}
    </div>
  )
}

