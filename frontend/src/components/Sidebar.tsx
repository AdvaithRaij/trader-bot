import React, { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Newspaper,
  Brain,
  Shield,
  Settings,
  Activity,
  Bot,
  X,
  ChevronLeft,
  Target,
  FlaskConical,
  Play,
  Square,
  Loader2,
  Zap
} from 'lucide-react'
import { cn } from '../lib/utils'
import { apiService } from '../lib/trading-api'

interface SidebarProps {
  collapsed?: boolean
  onToggle?: () => void
  onClose?: () => void
  width?: number
  className?: string
}

const navigation = [
  { name: 'Trading Dashboard', href: '/', icon: Activity },
  { name: 'Trading Pipeline', href: '/pipeline', icon: Zap },  // Primary trading workflow
  { name: 'Trade View', href: '/trade', icon: Target },
  // REMOVED: Backtest page per user request
  // { name: 'Backtest', href: '/backtest', icon: FlaskConical },
  { name: 'Trade Logs', href: '/trades', icon: DollarSign },
  { name: 'Market News', href: '/news', icon: Newspaper },
  // REMOVED: Analytics page per user request
  // { name: 'Analytics', href: '/dashboard', icon: BarChart3 },
  { name: 'Risk Manager', href: '/risk', icon: Shield },
  { name: 'Settings', href: '/settings', icon: Settings },
  // REMOVED: Legacy pages per user request
  // { name: 'Strategy Manager', href: '/strategies', icon: Brain },
  // { name: 'Stock Screener', href: '/screener', icon: TrendingUp },
]

export function Sidebar({ collapsed = false, onToggle, onClose, width = 256, className }: SidebarProps) {
  const [botStatus, setBotStatus] = useState<{
    isRunning: boolean
    mode: string
    todayTrades: number
    todayPnl: number
  }>({
    isRunning: false,
    mode: 'paper',
    todayTrades: 0,
    todayPnl: 0
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isToggling, setIsToggling] = useState(false)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [health, mode, todayTradesData] = await Promise.all([
          apiService.getHealthStatus(),
          apiService.getTradingMode(),
          apiService.getTodayTrades()
        ])

        // Calculate today's P&L from trades
        const trades = todayTradesData?.trades || []
        const todayPnl = trades.reduce((sum, trade) => sum + (trade.pnl || 0), 0)

        setBotStatus({
          isRunning: health.components?.bot === 'running',
          mode: mode.mockMode ? 'paper' : 'live',
          todayTrades: trades.length,
          todayPnl: todayPnl
        })
      } catch (error) {
        console.error('Failed to fetch bot status:', error)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const handleToggleBot = async () => {
    setIsToggling(true)
    try {
      if (botStatus.isRunning) {
        await apiService.stopBot()
      } else {
        await apiService.startBot()
      }
      // Wait a moment then refresh status
      setTimeout(async () => {
        const health = await apiService.getHealthStatus()
        setBotStatus(prev => ({
          ...prev,
          isRunning: health.components?.bot === 'running'
        }))
        setIsToggling(false)
      }, 2000)
    } catch (error) {
      console.error('Failed to toggle bot:', error)
      setIsToggling(false)
    }
  }

  return (
    <div 
      className={cn(
        "glass-sidebar min-h-screen flex flex-col transition-all duration-300 relative",
        collapsed ? "w-16" : "w-full",
        className
      )}
      style={{ width: collapsed ? '64px' : `${width}px` }}
    >
      {/* Embedded Toggle Button */}
      {onToggle && (
        <button 
          onClick={onToggle}
          className="absolute -right-3 top-6 z-10 hidden md:flex items-center justify-center w-6 h-6 bg-gray-800 hover:bg-gray-700 border border-white/20 rounded-full transition-all duration-200 shadow-lg"
        >
          <ChevronLeft className={cn(
            "w-3 h-3 text-gray-400 transition-transform duration-200",
            collapsed && "rotate-180"
          )} />
        </button>
      )}

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-white/10">
        {!collapsed && (
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Bot className="w-8 h-8 text-blue-400" />
              <Activity className="w-3 h-3 text-green-400 absolute -top-1 -right-1 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">TradingBot</h1>
              <p className="text-xs text-gray-400">AI-Powered Trading</p>
            </div>
          </div>
        )}
        
        {collapsed && (
          <div className="flex items-center justify-center w-full">
            <div className="relative">
              <Bot className="w-8 h-8 text-blue-400" />
              <Activity className="w-3 h-3 text-green-400 absolute -top-1 -right-1 animate-pulse" />
            </div>
          </div>
        )}

        {/* Close button for mobile */}
        <button 
          onClick={onClose}
          className="md:hidden p-1 hover:bg-white/10 rounded transition-colors"
        >
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-6 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            onClick={onClose} // Close mobile sidebar on navigation
            className={({ isActive }) =>
              cn(
                "flex items-center text-sm font-medium rounded-lg transition-all duration-200 group",
                collapsed ? "px-3 py-3 justify-center" : "px-3 py-2.5",
                isActive
                  ? "bg-blue-500/20 text-blue-300 border border-blue-500/30 glow-blue"
                  : "text-gray-300 hover:text-white hover:bg-white/10 hover:border hover:border-white/20"
              )
            }
            title={collapsed ? item.name : undefined}
          >
            {({ isActive }) => (
              <>
                <item.icon className={cn(
                  "flex-shrink-0",
                  collapsed ? "w-6 h-6" : "w-5 h-5 mr-3",
                  isActive ? "text-blue-400" : "text-gray-400"
                )} />
                {!collapsed && (
                  <>
                    <span className="truncate">{item.name}</span>
                    {isActive && (
                      <div className="ml-auto w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                    )}
                  </>
                )}
                {collapsed && isActive && (
                  <div className="absolute right-1 w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bot Status & Controls */}
      {!collapsed && (
        <div className="px-4 py-4 border-t border-white/10">
          <div className="glass rounded-lg p-3">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-300">Bot Control</span>
              <div className="flex items-center space-x-1">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  botStatus.isRunning ? "bg-green-400 animate-pulse" : "bg-gray-500"
                )} />
                <span className={cn(
                  "text-xs font-medium",
                  botStatus.isRunning ? "text-green-400" : "text-gray-400"
                )}>
                  {botStatus.isRunning ? 'Running' : 'Stopped'}
                </span>
              </div>
            </div>

            {/* Start/Stop Button */}
            <button
              onClick={handleToggleBot}
              disabled={isToggling}
              className={cn(
                "w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-lg text-sm font-medium transition-all duration-200",
                botStatus.isRunning
                  ? "bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30"
                  : "bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30",
                isToggling && "opacity-50 cursor-not-allowed"
              )}
            >
              {isToggling ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{botStatus.isRunning ? 'Stopping...' : 'Starting...'}</span>
                </>
              ) : (
                <>
                  {botStatus.isRunning ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  <span>{botStatus.isRunning ? 'Stop Bot' : 'Start Bot'}</span>
                </>
              )}
            </button>

            {/* Status Info */}
            <div className="mt-3 space-y-1 text-xs text-gray-400">
              <div className="flex justify-between">
                <span>Mode:</span>
                <span className={cn(
                  botStatus.mode === 'live' ? "text-green-400" : "text-yellow-400"
                )}>
                  {botStatus.mode === 'live' ? 'LIVE' : 'Paper'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Trades Today:</span>
                <span className="text-white">{botStatus.todayTrades}</span>
              </div>
              <div className="flex justify-between">
                <span>P&L:</span>
                <span className={cn(
                  botStatus.todayPnl >= 0 ? "text-green-400" : "text-red-400"
                )}>
                  {botStatus.todayPnl >= 0 ? '+' : ''}₹{botStatus.todayPnl.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-white/10">
          <div className="text-xs text-gray-500 text-center">
            <div>Trading Bot v2.0</div>
            <div className="flex items-center justify-center space-x-2 mt-1">
              <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
              <span>Connected to NSE</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
