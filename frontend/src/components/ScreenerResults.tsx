import React, { useState } from 'react'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  BarChart3,
  Brain,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Star,
  AlertCircle
} from 'lucide-react'
import { cn, formatCurrency } from '../lib/utils'
import type { ScreenerCandidate } from '../lib/trading-api'

interface ScreenerResultsProps {
  candidates: ScreenerCandidate[]
  onSelect?: (symbol: string) => void
  onGeneratePlan?: (symbol: string) => void
  selectedSymbol?: string
}

type SortField = 'screening_score' | 'relative_volume' | 'atr_percent' | 'rsi' | 'current_price'
type SortDirection = 'asc' | 'desc'

export function ScreenerResults({ 
  candidates, 
  onSelect, 
  onGeneratePlan,
  selectedSymbol 
}: ScreenerResultsProps) {
  const [sortField, setSortField] = useState<SortField>('screening_score')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [expandedSymbol, setExpandedSymbol] = useState<string | null>(null)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const sortedCandidates = [...candidates].sort((a, b) => {
    const aVal = a[sortField] as number
    const bVal = b[sortField] as number
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
  })

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400 bg-green-500/20'
    if (score >= 60) return 'text-blue-400 bg-blue-500/20'
    if (score >= 40) return 'text-yellow-400 bg-yellow-500/20'
    return 'text-gray-400 bg-gray-500/20'
  }

  const getRsiColor = (rsi: number) => {
    if (rsi > 70) return 'text-red-400'
    if (rsi < 30) return 'text-green-400'
    return 'text-gray-300'
  }

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'POSITIVE': return <TrendingUp className="w-4 h-4 text-green-400" />
      case 'NEGATIVE': return <TrendingDown className="w-4 h-4 text-red-400" />
      default: return <Activity className="w-4 h-4 text-gray-400" />
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDirection === 'asc' 
      ? <ChevronUp className="w-3 h-3 ml-1" />
      : <ChevronDown className="w-3 h-3 ml-1" />
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-700/50 flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          Screened Candidates
          <span className="text-sm text-gray-400">({candidates.length})</span>
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                Symbol
              </th>
              <th 
                onClick={() => handleSort('current_price')}
                className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end">
                  Price <SortIcon field="current_price" />
                </div>
              </th>
              <th 
                onClick={() => handleSort('screening_score')}
                className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-center">
                  Score <SortIcon field="screening_score" />
                </div>
              </th>
              <th 
                onClick={() => handleSort('relative_volume')}
                className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end">
                  RVOL <SortIcon field="relative_volume" />
                </div>
              </th>
              <th 
                onClick={() => handleSort('atr_percent')}
                className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end">
                  ATR% <SortIcon field="atr_percent" />
                </div>
              </th>
              <th 
                onClick={() => handleSort('rsi')}
                className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end">
                  RSI <SortIcon field="rsi" />
                </div>
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase">
                News
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/30">
            {sortedCandidates.map((candidate) => (
              <React.Fragment key={candidate.symbol}>
                <tr
                  className={cn(
                    "hover:bg-gray-800/30 cursor-pointer transition-colors",
                    selectedSymbol === candidate.symbol && "bg-blue-500/10",
                    expandedSymbol === candidate.symbol && "bg-gray-800/20"
                  )}
                  onClick={() => onSelect?.(candidate.symbol)}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs font-bold">
                        {candidate.symbol.slice(0, 2)}
                      </div>
                      <div>
                        <span className="font-medium text-white">{candidate.symbol}</span>
                        <p className="text-xs text-gray-500">
                          {candidate.nearest_pivot} ({candidate.pivot_distance_percent.toFixed(1)}%)
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-medium text-white">{formatCurrency(candidate.current_price)}</span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={cn(
                      "inline-flex items-center px-2 py-1 rounded text-xs font-bold",
                      getScoreColor(candidate.screening_score)
                    )}>
                      {candidate.screening_score.toFixed(0)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={cn(
                      "font-medium",
                      candidate.relative_volume >= 2 ? 'text-green-400' :
                      candidate.relative_volume >= 1.5 ? 'text-blue-400' : 'text-gray-400'
                    )}>
                      {candidate.relative_volume.toFixed(1)}x
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="text-gray-300">{candidate.atr_percent.toFixed(1)}%</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={getRsiColor(candidate.rsi)}>
                      {candidate.rsi.toFixed(0)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {getSentimentIcon(candidate.news_context.sentiment)}
                      {candidate.news_context.news_count > 0 && (
                        <span className="text-xs text-gray-400">{candidate.news_context.news_count}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setExpandedSymbol(expandedSymbol === candidate.symbol ? null : candidate.symbol)
                        }}
                        className="p-1.5 hover:bg-gray-700 rounded transition-colors"
                      >
                        {expandedSymbol === candidate.symbol ? (
                          <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onGeneratePlan?.(candidate.symbol)
                        }}
                        className="p-1.5 hover:bg-purple-500/20 rounded transition-colors"
                        title="Generate AI Trade Plan"
                      >
                        <Brain className="w-4 h-4 text-purple-400" />
                      </button>
                    </div>
                  </td>
                </tr>
                {/* Expanded Details Row */}
                {expandedSymbol === candidate.symbol && (
                  <tr className="bg-gray-800/30">
                    <td colSpan={8} className="px-4 py-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Turnover</span>
                          <p className="text-white font-medium">₹{candidate.turnover_cr.toFixed(1)} Cr</p>
                        </div>
                        <div>
                          <span className="text-gray-500">Market Cap</span>
                          <p className="text-white font-medium">₹{candidate.market_cap_cr.toFixed(0)} Cr</p>
                        </div>
                        <div>
                          <span className="text-gray-500">Gap</span>
                          <p className={cn("font-medium", candidate.gap_percent >= 0 ? 'text-green-400' : 'text-red-400')}>
                            {candidate.gap_percent >= 0 ? '+' : ''}{candidate.gap_percent.toFixed(2)}%
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-500">VWAP Distance</span>
                          <p className={cn("font-medium", candidate.distance_from_vwap_percent >= 0 ? 'text-green-400' : 'text-red-400')}>
                            {candidate.distance_from_vwap_percent >= 0 ? '+' : ''}{candidate.distance_from_vwap_percent.toFixed(2)}%
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-500">Liquidity Score</span>
                          <p className="text-blue-400 font-medium">{candidate.liquidity_score.toFixed(0)}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">Volatility Score</span>
                          <p className="text-purple-400 font-medium">{candidate.volatility_score.toFixed(0)}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">Trend Score</span>
                          <p className="text-cyan-400 font-medium">{candidate.trend_score.toFixed(0)}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">News Score</span>
                          <p className="text-yellow-400 font-medium">{candidate.news_score.toFixed(0)}</p>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {candidates.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-gray-400">
          <AlertCircle className="w-12 h-12 mb-4 opacity-50" />
          <p>No screened candidates available</p>
          <p className="text-sm">Run the screener to find trading opportunities</p>
        </div>
      )}
    </div>
  )
}

