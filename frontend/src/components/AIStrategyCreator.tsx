import React, { useState } from 'react'
import { 
  Sparkles, 
  Send, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import { apiService } from '../lib/trading-api'

interface CreatedStrategy {
  strategyId: string
  name: string
  description: string
  stockPicking: any
  execution: any
  riskManagement: any
}

export function AIStrategyCreator({ onStrategyCreated }: { onStrategyCreated?: () => void }) {
  const [description, setDescription] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [createdStrategy, setCreatedStrategy] = useState<CreatedStrategy | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  const examplePrompts = [
    "Buy stocks with high-impact positive news and 3% target, 1.5% stop loss",
    "Conservative strategy: only trade blue-chip stocks with very high confidence news",
    "Aggressive scalping on immediate news with 5% target and trailing stop",
    "Trade only IT sector stocks when there's positive earnings news"
  ]

  const handleCreate = async () => {
    if (!description.trim()) return

    try {
      setIsCreating(true)
      setError(null)
      setCreatedStrategy(null)

      const response = await fetch('http://localhost:8001/api/strategies/create-from-description', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, saveToDatabase: true })
      })

      const data = await response.json()

      if (data.error) {
        setError(data.error)
      } else if (data.success) {
        setCreatedStrategy(data.strategy)
        setDescription('')
        onStrategyCreated?.()
      }
    } catch (err) {
      console.error('Error creating strategy:', err)
      setError('Failed to create strategy. Make sure the backend is running.')
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <div className="glass-card p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="p-2 bg-purple-500/20 rounded-lg">
          <Sparkles className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">AI Strategy Creator</h3>
          <p className="text-sm text-gray-400">Describe your strategy in plain English</p>
        </div>
      </div>

      {/* Input Area */}
      <div className="mb-4">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe your trading strategy... e.g., 'I want to buy stocks when there's high-impact positive news with at least 80% relevance. Set stop loss at 2% and take profit at 5%.'"
          className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-400 transition-colors resize-none"
        />
      </div>

      {/* Example Prompts */}
      <div className="mb-4">
        <p className="text-xs text-gray-400 mb-2">Try these examples:</p>
        <div className="flex flex-wrap gap-2">
          {examplePrompts.map((prompt, i) => (
            <button
              key={i}
              onClick={() => setDescription(prompt)}
              className="px-3 py-1 text-xs bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-gray-300 transition-colors"
            >
              {prompt.slice(0, 40)}...
            </button>
          ))}
        </div>
      </div>

      {/* Create Button */}
      <button
        onClick={handleCreate}
        disabled={isCreating || !description.trim()}
        className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-gray-500 disabled:to-gray-600 rounded-lg font-medium transition-all flex items-center justify-center space-x-2"
      >
        {isCreating ? (
          <>
            <RefreshCw className="w-5 h-5 animate-spin" />
            <span>Creating Strategy...</span>
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
            <span>Create Strategy with AI</span>
          </>
        )}
      </button>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
          <div className="flex items-center space-x-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Success Display */}
      {createdStrategy && (
        <div className="mt-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2 text-green-400">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">Strategy Created!</span>
            </div>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-gray-400 hover:text-white"
            >
              {showDetails ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
          </div>
          <p className="text-white font-medium">{createdStrategy.name}</p>
          <p className="text-sm text-gray-300">{createdStrategy.description}</p>
          
          {showDetails && (
            <div className="mt-4 space-y-3 text-sm">
              <div className="p-3 bg-white/5 rounded-lg">
                <p className="text-gray-400 mb-1">Stock Picking</p>
                <p className="text-white">Type: {createdStrategy.stockPicking?.type}</p>
              </div>
              <div className="p-3 bg-white/5 rounded-lg">
                <p className="text-gray-400 mb-1">Execution</p>
                <p className="text-white">SL: {createdStrategy.execution?.stopLossPercent}% | TP: {createdStrategy.execution?.takeProfitPercent}%</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

