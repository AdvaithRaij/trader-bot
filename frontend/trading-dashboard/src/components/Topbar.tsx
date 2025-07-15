import React, { useState } from 'react'
import { Search, Command, Bell, User, RefreshCw, Play, Square, Menu, X, ChevronLeft, ChevronRight } from 'lucide-react'
import { cn, formatCurrency, formatTime } from '../lib/utils'

interface TopbarProps {
  onCommandPaletteOpen: () => void
  onSidebarToggle?: () => void
  sidebarCollapsed?: boolean
  showMobileMenu?: boolean
  className?: string
}

export function Topbar({ 
  onCommandPaletteOpen, 
  onSidebarToggle, 
  sidebarCollapsed = false, 
  showMobileMenu = false, 
  className 
}: TopbarProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [botRunning, setBotRunning] = useState(true)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsRefreshing(false)
  }

  const toggleBot = () => {
    setBotRunning(!botRunning)
  }

  return (
    <header className={cn("glass border-b border-white/10 px-3 sm:px-4 md:px-6 py-3 md:py-4", className)}>
      <div className="flex items-center justify-between min-w-0 gap-2 sm:gap-4">
        {/* Left Side */}
        <div className="flex items-center space-x-2 sm:space-x-4 min-w-0 flex-shrink-0">
          {/* Mobile Menu Toggle */}
          {showMobileMenu && (
            <button
              onClick={onSidebarToggle}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors md:hidden"
            >
              <Menu className="w-5 h-5 text-gray-400" />
            </button>
          )}

          {/* Search and Command Palette */}
          <button
            onClick={onCommandPaletteOpen}
            className="flex items-center space-x-2 px-2 sm:px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg border border-white/10 transition-colors group min-w-0 max-w-xs"
          >
            <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <span className="text-gray-400 text-sm hidden sm:inline truncate">
              Search or run command...
            </span>
            <div className="hidden lg:flex items-center space-x-1 ml-4 flex-shrink-0">
              <kbd className="px-1.5 py-0.5 text-xs font-semibold text-gray-400 bg-white/10 border border-white/20 rounded">
                ⌘
              </kbd>
              <kbd className="px-1.5 py-0.5 text-xs font-semibold text-gray-400 bg-white/10 border border-white/20 rounded">
                K
              </kbd>
            </div>
          </button>
        </div>

        {/* Center - Spacer */}
        <div className="flex-1" />

        {/* Right Side Actions */}
        <div className="flex items-center space-x-1 sm:space-x-2 md:space-x-3 flex-shrink-0">
            {/* Bot Control */}
            <button
                onClick={toggleBot}
                className={cn(
                "flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-2 rounded-lg transition-all duration-200",
                botRunning 
                    ? "bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/30" 
                    : "bg-green-500/20 hover:bg-green-500/30 text-green-300 border border-green-500/30"
                )}
            >
                {botRunning ? (
                <>
                    <Square className="w-4 h-4" />
                    <span className="text-sm font-medium hidden sm:inline">Stop</span>
                </>
                ) : (
                <>
                    <Play className="w-4 h-4" />
                    <span className="text-sm font-medium hidden sm:inline">Start</span>
                </>
                )}
            </button>
          {/* Market Status & Time Combined - Desktop only */}
          <div className="hidden lg:flex items-center space-x-2 px-3 py-2 glass rounded-lg">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-sm text-gray-400 font-medium">LIVE</span>
            </div>
            <div className="w-px h-4 bg-white/20" />
            <div className="text-sm text-gray-300">
              <span className="text-white font-medium">2:47 PM</span>
              <span className="ml-1 text-gray-400">22m left</span>
            </div>
          </div>

          {/* Win Rate - Desktop only */}
          <div className="hidden lg:flex xl:hidden items-center px-3 py-2 glass rounded-lg portfolio-stats">
            <div className="text-sm min-w-0">
              <div className="text-gray-400 text-nowrap-responsive">Win Rate</div>
              <div className="font-medium text-blue-400 text-nowrap-responsive">78.5%</div>
            </div>
          </div>

          {/* Portfolio Summary - Desktop only */}
          <div className="hidden xl:flex items-center space-x-4 px-3 py-2 glass rounded-lg portfolio-stats">
            <div className="text-sm min-w-0">
              <div className="text-gray-400 text-nowrap-responsive">Portfolio</div>
              <div className="font-medium text-white text-nowrap-responsive">{formatCurrency(125000)}</div>
            </div>
            <div className="text-sm min-w-0">
              <div className="text-gray-400 text-nowrap-responsive">Day P&L</div>
              <div className="font-medium text-green-400 text-nowrap-responsive">+{formatCurrency(1247)}</div>
            </div>
            <div className="text-sm min-w-0">
              <div className="text-gray-400 text-nowrap-responsive">Win Rate</div>
              <div className="font-medium text-blue-400 text-nowrap-responsive">78.5%</div>
            </div>
          </div>

          {/* Compact Portfolio - Tablet */}
          <div className="hidden lg:flex xl:hidden items-center px-3 py-2 glass rounded-lg portfolio-stats">
            <div className="text-sm min-w-0">
              <div className="text-gray-400 text-nowrap-responsive">P&L</div>
              <div className="font-medium text-green-400 text-nowrap-responsive">+{formatCurrency(1247)}</div>
            </div>
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={cn("w-4 h-4 sm:w-5 sm:h-5 text-gray-400", isRefreshing && "animate-spin")} />
          </button>

          {/* Notifications */}
          <button className="relative p-2 hover:bg-white/10 rounded-lg transition-colors">
            <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
            <div className="absolute -top-1 -right-1 w-2 h-2 sm:w-3 sm:h-3 bg-red-500 rounded-full flex items-center justify-center">
              <span className="text-xs text-white font-bold hidden sm:inline">3</span>
            </div>
          </button>

          {/* User Menu */}
          <button className="flex items-center space-x-2 p-1 sm:p-2 hover:bg-white/10 rounded-lg transition-colors">
            <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center">
              <User className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
            </div>
            <div className="hidden md:block text-left">
              <div className="text-sm font-medium text-white">Advaith</div>
              <div className="text-xs text-gray-400">Trader</div>
            </div>
          </button>
        </div>
      </div>

      {/* Mobile Stats Bar */}
      <div className="lg:hidden mt-3 pt-3 border-t border-white/10">
        <div className="flex items-center justify-between text-xs sm:text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
            <span className="text-gray-300">LIVE <span className="text-white">2:47 PM</span></span>
          </div>
          <div className="text-gray-300">
            Portfolio: <span className="text-white font-medium">{formatCurrency(131247)}</span>
          </div>
          <div className="text-gray-300">
            P&L: <span className="text-green-400 font-medium">+{formatCurrency(6247)}</span>
          </div>
          <div className="text-gray-300">
            Win: <span className="text-blue-400 font-medium">78.5%</span>
          </div>
        </div>
      </div>
    </header>
  )
}
