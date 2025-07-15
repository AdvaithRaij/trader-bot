import React, { useState, useEffect, useRef } from 'react'
import { Search, ArrowRight, TrendingUp, BarChart3, Settings, Play, Square, RefreshCw, DollarSign } from 'lucide-react'
import { cn } from '../lib/utils'

interface Command {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  action: () => void
  keywords: string[]
  category: 'navigation' | 'trading' | 'data' | 'settings'
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  onNavigate: (path: string) => void
  onExecuteAction: (action: string) => void
}

export function CommandPalette({ isOpen, onClose, onNavigate, onExecuteAction }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const commands: Command[] = [
    // Navigation
    {
      id: 'nav-home',
      title: 'Go to Dashboard',
      description: 'View trading overview and portfolio summary',
      icon: <BarChart3 className="w-4 h-4" />,
      action: () => onNavigate('/'),
      keywords: ['dashboard', 'home', 'overview', 'portfolio'],
      category: 'navigation'
    },
    {
      id: 'nav-screener',
      title: 'Go to Stock Screener',
      description: 'Find and analyze potential trading opportunities',
      icon: <TrendingUp className="w-4 h-4" />,
      action: () => onNavigate('/screener'),
      keywords: ['screener', 'stocks', 'opportunities', 'filter'],
      category: 'navigation'
    },
    {
      id: 'nav-trades',
      title: 'Go to Trade Logs',
      description: 'View trading history and performance',
      icon: <DollarSign className="w-4 h-4" />,
      action: () => onNavigate('/trades'),
      keywords: ['trades', 'history', 'logs', 'performance'],
      category: 'navigation'
    },
    {
      id: 'nav-news',
      title: 'Go to Market News',
      description: 'Latest market news and sentiment analysis',
      icon: <RefreshCw className="w-4 h-4" />,
      action: () => onNavigate('/news'),
      keywords: ['news', 'sentiment', 'market', 'analysis'],
      category: 'navigation'
    },
    {
      id: 'nav-strategy',
      title: 'Go to Strategy Center',
      description: 'Manage trading strategies and AI settings',
      icon: <Settings className="w-4 h-4" />,
      action: () => onNavigate('/strategy'),
      keywords: ['strategy', 'ai', 'settings', 'configure'],
      category: 'navigation'
    },
    {
      id: 'nav-risk',
      title: 'Go to Risk Manager',
      description: 'Monitor and configure risk parameters',
      icon: <Settings className="w-4 h-4" />,
      action: () => onNavigate('/risk'),
      keywords: ['risk', 'limits', 'drawdown', 'safety'],
      category: 'navigation'
    },
    {
      id: 'nav-settings',
      title: 'Go to Settings',
      description: 'Configure application preferences',
      icon: <Settings className="w-4 h-4" />,
      action: () => onNavigate('/settings'),
      keywords: ['settings', 'preferences', 'configuration'],
      category: 'navigation'
    },
    // Trading Actions
    {
      id: 'action-start-bot',
      title: 'Start Trading Bot',
      description: 'Begin automated trading with current strategy',
      icon: <Play className="w-4 h-4" />,
      action: () => onExecuteAction('start-bot'),
      keywords: ['start', 'bot', 'trading', 'begin', 'run'],
      category: 'trading'
    },
    {
      id: 'action-stop-bot',
      title: 'Stop Trading Bot',
      description: 'Halt all automated trading activities',
      icon: <Square className="w-4 h-4" />,
      action: () => onExecuteAction('stop-bot'),
      keywords: ['stop', 'bot', 'trading', 'halt', 'pause'],
      category: 'trading'
    },
    // Data Actions
    {
      id: 'action-refresh-data',
      title: 'Refresh Market Data',
      description: 'Update all market data and portfolio information',
      icon: <RefreshCw className="w-4 h-4" />,
      action: () => onExecuteAction('refresh-data'),
      keywords: ['refresh', 'update', 'data', 'market', 'sync'],
      category: 'data'
    },
    {
      id: 'action-run-screener',
      title: 'Run Stock Screener',
      description: 'Execute screening to find new trading opportunities',
      icon: <TrendingUp className="w-4 h-4" />,
      action: () => onExecuteAction('run-screener'),
      keywords: ['screener', 'scan', 'opportunities', 'stocks'],
      category: 'data'
    }
  ]

  const filteredCommands = commands.filter(command => {
    if (!query) return true
    const searchTerms = query.toLowerCase().split(' ')
    return searchTerms.every(term => 
      command.title.toLowerCase().includes(term) ||
      command.description.toLowerCase().includes(term) ||
      command.keywords.some(keyword => keyword.toLowerCase().includes(term))
    )
  })

  const groupedCommands = filteredCommands.reduce((acc, command) => {
    if (!acc[command.category]) {
      acc[command.category] = []
    }
    acc[command.category].push(command)
    return acc
  }, {} as Record<string, Command[]>)

  const categoryLabels = {
    navigation: 'Navigation',
    trading: 'Trading Actions',
    data: 'Data & Analysis',
    settings: 'Configuration'
  }

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      if (e.key === 'Escape') {
        onClose()
      } else if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => Math.max(prev - 1, 0))
      } else if (e.key === 'Enter') {
        e.preventDefault()
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action()
          onClose()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, selectedIndex, filteredCommands, onClose])

  if (!isOpen) return null

  let currentIndex = 0

  return (
    <div className="cmd-palette-backdrop" onClick={onClose}>
      <div 
        className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="glass-card p-0 overflow-hidden">
          {/* Search Input */}
          <div className="flex items-center px-4 py-3 border-b border-white/10">
            <Search className="w-5 h-5 text-gray-400 mr-3" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Type a command or search..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 bg-transparent border-none outline-none text-white placeholder-gray-400 text-lg"
            />
            <div className="text-xs text-gray-400 hidden sm:block">
              ↑↓ Navigate • ↵ Select • ESC Close
            </div>
          </div>

          {/* Commands List */}
          <div className="max-h-96 overflow-y-auto">
            {Object.entries(groupedCommands).map(([category, commands]) => (
              <div key={category}>
                <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider bg-white/5">
                  {categoryLabels[category as keyof typeof categoryLabels]}
                </div>
                {commands.map((command) => {
                  const isSelected = currentIndex === selectedIndex
                  const itemIndex = currentIndex++
                  
                  return (
                    <div
                      key={command.id}
                      className={cn(
                        "flex items-center px-4 py-3 cursor-pointer transition-colors",
                        isSelected ? "bg-blue-500/20 border-l-2 border-blue-400" : "hover:bg-white/5"
                      )}
                      onClick={() => {
                        command.action()
                        onClose()
                      }}
                    >
                      <div className="flex items-center justify-center w-8 h-8 mr-3 rounded-md bg-white/10">
                        {command.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-white font-medium truncate">
                          {command.title}
                        </div>
                        <div className="text-gray-400 text-sm truncate">
                          {command.description}
                        </div>
                      </div>
                      {isSelected && (
                        <ArrowRight className="w-4 h-4 text-gray-400 ml-2" />
                      )}
                    </div>
                  )
                })}
              </div>
            ))}
            
            {filteredCommands.length === 0 && (
              <div className="px-4 py-8 text-center text-gray-400">
                No commands found for "{query}"
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
