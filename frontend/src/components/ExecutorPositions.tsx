import React from 'react'
import {
  Zap,
  TrendingUp,
  TrendingDown,
  Target,
  Shield,
  XCircle,
  Clock,
  AlertTriangle
} from 'lucide-react'
import { cn, formatCurrency } from '../lib/utils'
import type { ExecutorPosition, ExecutorStatus } from '../lib/trading-api'

interface ExecutorPositionsProps {
  status: ExecutorStatus | null
  onSquareOff?: (symbol: string) => void
  onSquareOffAll?: () => void
}

export function ExecutorPositions({ status, onSquareOff, onSquareOffAll }: ExecutorPositionsProps) {
  // Default values for when status is null or partially undefined
  const safeStatus: ExecutorStatus = status ? {
    is_active: status.is_active ?? false,
    open_positions: status.open_positions ?? 0,
    pending_orders: status.pending_orders ?? 0,
    trades_today: status.trades_today ?? 0,
    max_trades_per_day: status.max_trades_per_day ?? 10,
    daily_pnl: status.daily_pnl ?? 0,
    daily_pnl_percent: status.daily_pnl_percent ?? 0,
    open_risk_percent: status.open_risk_percent ?? 0,
    max_open_risk_percent: status.max_open_risk_percent ?? 5,
    last_trade_time: status.last_trade_time ?? null,
    positions: status.positions ?? []
  } : {
    is_active: false,
    open_positions: 0,
    pending_orders: 0,
    trades_today: 0,
    max_trades_per_day: 10,
    daily_pnl: 0,
    daily_pnl_percent: 0,
    open_risk_percent: 0,
    max_open_risk_percent: 5,
    last_trade_time: null,
    positions: []
  }

  if (!status) {
    return (
      <div className="glass-card p-8 text-center text-gray-400">
        <Zap className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>Executor status unavailable</p>
      </div>
    )
  }

  const formatTime = (isoString: string | null) => {
    if (!isoString) return '--:--'
    return new Date(isoString).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700/50 flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Zap className="w-5 h-5 text-green-400" />
          Trade Executor
          <span className={cn(
            "text-xs px-2 py-0.5 rounded",
            safeStatus.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
          )}>
            {safeStatus.is_active ? 'Active' : 'Inactive'}
          </span>
        </h3>
        {safeStatus.positions.length > 0 && (
          <button
            onClick={onSquareOffAll}
            className="flex items-center gap-2 px-3 py-1.5 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors text-sm"
          >
            <XCircle className="w-4 h-4" />
            Square Off All
          </button>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 border-b border-gray-700/30">
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{safeStatus.open_positions}</p>
          <p className="text-xs text-gray-500">Open Positions</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-white">{safeStatus.trades_today}/{safeStatus.max_trades_per_day}</p>
          <p className="text-xs text-gray-500">Trades Today</p>
        </div>
        <div className="text-center">
          <p className={cn(
            "text-2xl font-bold",
            safeStatus.daily_pnl >= 0 ? 'text-green-400' : 'text-red-400'
          )}>
            {safeStatus.daily_pnl >= 0 ? '+' : ''}{formatCurrency(safeStatus.daily_pnl)}
          </p>
          <p className="text-xs text-gray-500">Daily P&L</p>
        </div>
        <div className="text-center">
          <p className={cn(
            "text-2xl font-bold",
            safeStatus.open_risk_percent > 4 ? 'text-red-400' :
            safeStatus.open_risk_percent > 3 ? 'text-yellow-400' : 'text-green-400'
          )}>
            {safeStatus.open_risk_percent.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500">Open Risk (Max {safeStatus.max_open_risk_percent}%)</p>
        </div>
      </div>

      {/* Positions Table */}
      {safeStatus.positions.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Symbol</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Entry</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Current</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">SL</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Target</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">P&L</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Risk</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/30">
              {safeStatus.positions.map((position) => (
                <PositionRow
                  key={position.symbol}
                  position={position}
                  onSquareOff={onSquareOff}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-gray-400">
          <Target className="w-12 h-12 mb-4 opacity-50" />
          <p>No open positions</p>
          <p className="text-sm">Positions will appear here when trades are executed</p>
        </div>
      )}

      {/* Last Trade Time */}
      {safeStatus.last_trade_time && (
        <div className="px-4 py-2 border-t border-gray-700/30 text-xs text-gray-500 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Last trade: {formatTime(safeStatus.last_trade_time)}
        </div>
      )}
    </div>
  )
}

interface PositionRowProps {
  position: ExecutorPosition
  onSquareOff?: (symbol: string) => void
}

function PositionRow({ position, onSquareOff }: PositionRowProps) {
  const isProfitable = position.unrealized_pnl >= 0
  const isNearSL = position.direction === 'BUY'
    ? position.current_price <= position.stop_loss * 1.02
    : position.current_price >= position.stop_loss * 0.98

  return (
    <tr className={cn("hover:bg-gray-800/30", isNearSL && "bg-red-500/5")}>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {position.direction === 'BUY' ? (
            <TrendingUp className="w-4 h-4 text-green-400" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-400" />
          )}
          <span className="font-medium text-white">{position.symbol}</span>
          <span className="text-xs text-gray-500">x{position.quantity}</span>
        </div>
      </td>
      <td className="px-4 py-3 text-right text-gray-300">
        {formatCurrency(position.entry_price)}
      </td>
      <td className="px-4 py-3 text-right">
        <span className={cn(
          "font-medium",
          isProfitable ? 'text-green-400' : 'text-red-400'
        )}>
          {formatCurrency(position.current_price)}
        </span>
      </td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-1">
          {isNearSL && <AlertTriangle className="w-3 h-3 text-red-400" />}
          <span className="text-red-400">{formatCurrency(position.stop_loss)}</span>
        </div>
      </td>
      <td className="px-4 py-3 text-right text-green-400">
        {formatCurrency(position.target_1)}
      </td>
      <td className="px-4 py-3 text-right">
        <div>
          <span className={cn(
            "font-medium",
            isProfitable ? 'text-green-400' : 'text-red-400'
          )}>
            {isProfitable ? '+' : ''}{formatCurrency(position.unrealized_pnl)}
          </span>
          <p className={cn(
            "text-xs",
            isProfitable ? 'text-green-400/70' : 'text-red-400/70'
          )}>
            {isProfitable ? '+' : ''}{position.unrealized_pnl_percent.toFixed(2)}%
          </p>
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        <span className={cn(
          "text-sm",
          position.risk_percent > 1.5 ? 'text-red-400' : 'text-gray-400'
        )}>
          {position.risk_percent.toFixed(2)}%
        </span>
      </td>
      <td className="px-4 py-3 text-center">
        <button
          onClick={() => onSquareOff?.(position.symbol)}
          className="p-1.5 hover:bg-red-500/20 rounded transition-colors"
          title="Square Off Position"
        >
          <XCircle className="w-4 h-4 text-red-400" />
        </button>
      </td>
    </tr>
  )
}

