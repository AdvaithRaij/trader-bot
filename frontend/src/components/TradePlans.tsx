import React, { useState } from 'react'
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Zap,
  Info
} from 'lucide-react'
import { cn, formatCurrency } from '../lib/utils'
import type { TradePlan } from '../lib/trading-api'

interface TradePlansProps {
  plans: TradePlan[]
  onApprove?: (symbol: string) => void
  onReject?: (symbol: string) => void
  onExecute?: (symbol: string) => void
}

export function TradePlans({ plans, onApprove, onReject, onExecute }: TradePlansProps) {
  const [expandedPlan, setExpandedPlan] = useState<string | null>(null)

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return 'text-green-400 bg-green-500/20'
    if (confidence >= 75) return 'text-blue-400 bg-blue-500/20'
    if (confidence >= 60) return 'text-yellow-400 bg-yellow-500/20'
    return 'text-red-400 bg-red-500/20'
  }

  const getRRColor = (rr: number) => {
    if (rr >= 2.5) return 'text-green-400'
    if (rr >= 1.5) return 'text-blue-400'
    return 'text-yellow-400'
  }

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const isExpired = (validUntil: string) => {
    return new Date(validUntil) < new Date()
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-700/50 flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          AI Trade Plans
          <span className="text-sm text-gray-400">({plans.length})</span>
        </h3>
        <div className="text-xs text-gray-500">
          Min Confidence: 75% | Min R:R: 1.5
        </div>
      </div>

      <div className="divide-y divide-gray-700/30">
        {plans.map((plan) => {
          const expired = isExpired(plan.valid_until)
          const meetsThreshold = plan.confidence >= 75 && plan.levels.risk_reward_ratio >= 1.5

          return (
            <div
              key={plan.symbol}
              className={cn(
                "p-4 transition-colors",
                expired && "opacity-50",
                expandedPlan === plan.symbol && "bg-gray-800/20"
              )}
            >
              {/* Plan Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center",
                    plan.direction === 'BUY' ? 'bg-green-500/20' : 'bg-red-500/20'
                  )}>
                    {plan.direction === 'BUY' ? (
                      <TrendingUp className="w-5 h-5 text-green-400" />
                    ) : (
                      <TrendingDown className="w-5 h-5 text-red-400" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white">{plan.symbol}</span>
                      <span className={cn(
                        "text-xs px-2 py-0.5 rounded",
                        plan.direction === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                      )}>
                        {plan.direction}
                      </span>
                      {expired && (
                        <span className="text-xs px-2 py-0.5 rounded bg-gray-500/20 text-gray-400">
                          Expired
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500">{plan.rationale.setup_type}</p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {/* Confidence Badge */}
                  <div className="text-center">
                    <span className={cn(
                      "inline-flex items-center px-3 py-1 rounded-full text-sm font-bold",
                      getConfidenceColor(plan.confidence)
                    )}>
                      {plan.confidence}%
                    </span>
                    <p className="text-xs text-gray-500 mt-1">Confidence</p>
                  </div>

                  {/* R:R Badge */}
                  <div className="text-center">
                    <span className={cn("text-lg font-bold", getRRColor(plan.levels.risk_reward_ratio))}>
                      {plan.levels.risk_reward_ratio.toFixed(1)}
                    </span>
                    <p className="text-xs text-gray-500">R:R</p>
                  </div>

                  {/* Expand Button */}
                  <button
                    onClick={() => setExpandedPlan(expandedPlan === plan.symbol ? null : plan.symbol)}
                    className="p-2 hover:bg-gray-700 rounded transition-colors"
                  >
                    {expandedPlan === plan.symbol ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                </div>
              </div>

              {/* Price Levels */}
              <div className="mt-4 grid grid-cols-4 gap-4">
                <LevelCard label="Entry" value={plan.levels.entry} color="blue" />
                <LevelCard label="Stop Loss" value={plan.levels.stop_loss} color="red" />
                <LevelCard label="Target 1" value={plan.levels.target_1} color="green" />
                <LevelCard label="Target 2" value={plan.levels.target_2} color="cyan" />
              </div>

              {/* Expanded Details */}
              {expandedPlan === plan.symbol && (
                <div className="mt-4 space-y-4">
                  {/* Rationale */}
                  <div className="p-4 bg-gray-800/30 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-300 mb-2 flex items-center gap-2">
                      <Info className="w-4 h-4" />
                      Trade Rationale
                    </h4>
                    <p className="text-sm text-gray-400">{plan.rationale.summary}</p>
                  </div>

                  {/* Key Levels & Catalysts */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-gray-800/30 rounded-lg">
                      <h5 className="text-xs font-medium text-gray-400 mb-2">Key Levels</h5>
                      <div className="flex flex-wrap gap-2">
                        {plan.rationale.key_levels.map((level, i) => (
                          <span key={i} className="text-xs px-2 py-1 bg-blue-500/20 text-blue-400 rounded">
                            {level}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="p-3 bg-gray-800/30 rounded-lg">
                      <h5 className="text-xs font-medium text-gray-400 mb-2">Catalysts</h5>
                      <div className="flex flex-wrap gap-2">
                        {plan.rationale.catalysts.map((catalyst, i) => (
                          <span key={i} className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded">
                            {catalyst}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Risks */}
                  <div className="p-3 bg-red-500/10 rounded-lg">
                    <h5 className="text-xs font-medium text-red-400 mb-2 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      Risks
                    </h5>
                    <ul className="text-xs text-gray-400 space-y-1">
                      {plan.rationale.risks.map((risk, i) => (
                        <li key={i}>• {risk}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Timing */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Generated: {formatTime(plan.generated_at)}
                    </span>
                    <span className={cn(expired && "text-red-400")}>
                      Valid until: {formatTime(plan.valid_until)}
                    </span>
                  </div>

                  {/* Action Buttons */}
                  {!expired && meetsThreshold && (
                    <div className="flex items-center gap-3 pt-2">
                      <button
                        onClick={() => onExecute?.(plan.symbol)}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition-colors"
                      >
                        <Zap className="w-4 h-4" />
                        Execute Trade
                      </button>
                      <button
                        onClick={() => onApprove?.(plan.symbol)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Approve
                      </button>
                      <button
                        onClick={() => onReject?.(plan.symbol)}
                        className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                      >
                        <XCircle className="w-4 h-4" />
                        Reject
                      </button>
                    </div>
                  )}

                  {!meetsThreshold && !expired && (
                    <div className="flex items-center gap-2 p-3 bg-yellow-500/10 rounded-lg text-yellow-400 text-sm">
                      <AlertTriangle className="w-4 h-4" />
                      Does not meet minimum thresholds (75% confidence, 1.5 R:R)
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {plans.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-gray-400">
          <Brain className="w-12 h-12 mb-4 opacity-50" />
          <p>No trade plans available</p>
          <p className="text-sm">Select a screened candidate to generate a plan</p>
        </div>
      )}
    </div>
  )
}

function LevelCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colorClasses: Record<string, string> = {
    blue: 'text-blue-400',
    red: 'text-red-400',
    green: 'text-green-400',
    cyan: 'text-cyan-400'
  }
  return (
    <div className="p-2 rounded bg-gray-800/50 text-center">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={cn("font-bold", colorClasses[color] || 'text-white')}>{formatCurrency(value)}</p>
    </div>
  )
}

