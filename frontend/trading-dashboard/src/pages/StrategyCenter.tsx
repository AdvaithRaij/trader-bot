import React, { useState } from 'react';
import { Play, Pause, Settings, BarChart3, TrendingUp, Brain, AlertCircle, CheckCircle, Clock, Edit3, Save, X } from 'lucide-react';
import type { Strategy } from '../data/mockData';
import { strategies } from '../data/mockData';

export function StrategyCenter() {
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(strategies[0]);
  const [editingParameters, setEditingParameters] = useState(false);
  const [editedParameters, setEditedParameters] = useState<{ [key: string]: any }>({});

  const getStatusColor = (status: Strategy['status']) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-400/10';
      case 'inactive': return 'text-gray-400 bg-gray-400/10';
      case 'backtest': return 'text-blue-400 bg-blue-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  const getStatusIcon = (status: Strategy['status']) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4" />;
      case 'inactive': return <Clock className="w-4 h-4" />;
      case 'backtest': return <Brain className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  const handleParameterEdit = (key: string, value: any) => {
    setEditedParameters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const saveParameters = () => {
    console.log('Saving parameters:', editedParameters);
    setEditingParameters(false);
    setEditedParameters({});
  };

  const cancelEdit = () => {
    setEditingParameters(false);
    setEditedParameters({});
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mobile-stack">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">Strategy Center</h1>
          <p className="text-gray-400 text-sm sm:text-base">Manage and optimize your trading strategies</p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 self-start sm:self-auto">
          <button className="glass-button px-3 sm:px-4 py-2 rounded-lg flex items-center gap-2 text-green-400 hover:bg-green-400/10 transition-colors touch-friendly">
            <Play className="w-4 h-4" />
            <span className="hidden sm:inline">Deploy Strategy</span>
          </button>
          <button className="glass-button px-3 sm:px-4 py-2 rounded-lg flex items-center gap-2 text-blue-400 hover:bg-blue-400/10 transition-colors touch-friendly">
            <Brain className="w-4 h-4" />
            <span className="hidden sm:inline">AI Optimize</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Strategy List */}
        <div className="space-y-4">
          <h2 className="text-lg sm:text-xl font-semibold text-white mb-4">Strategies</h2>
          {strategies.map((strategy) => (
            <div
              key={strategy.id}
              onClick={() => setSelectedStrategy(strategy)}
              className={`glass-card p-4 cursor-pointer transition-all hover:bg-white/10 touch-friendly ${
                selectedStrategy?.id === strategy.id ? 'ring-2 ring-blue-500/50' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-white text-sm sm:text-base">{strategy.name}</h3>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(strategy.status)}`}>
                  {getStatusIcon(strategy.status)}
                  <span className="hidden sm:inline">{strategy.status.toUpperCase()}</span>
                </div>
              </div>
              <p className="text-gray-400 text-xs sm:text-sm mb-3">{strategy.description}</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-400">Return:</span>
                  <span className="text-green-400 ml-1">+{strategy.performance.totalReturn}%</span>
                </div>
                <div>
                  <span className="text-gray-400">Win Rate:</span>
                  <span className="text-white ml-1">{strategy.performance.winRate}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Strategy Details */}
        <div className="lg:col-span-2">
          {selectedStrategy ? (
            <div className="space-y-6">
              {/* Strategy Header */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-3">
                  <div className="min-w-0 flex-1">
                    <h2 className="text-xl sm:text-2xl font-bold text-white">{selectedStrategy.name}</h2>
                    <p className="text-gray-400 mt-1 text-sm sm:text-base">{selectedStrategy.description}</p>
                  </div>
                  <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${getStatusColor(selectedStrategy.status)} self-start`}>
                    {getStatusIcon(selectedStrategy.status)}
                    <span className="text-sm">{selectedStrategy.status.toUpperCase()}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 text-xs sm:text-sm text-gray-400">
                  <span>Last modified: {new Date(selectedStrategy.lastModified).toLocaleDateString()}</span>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="glass-card p-4 sm:p-6">
                <h3 className="text-lg sm:text-xl font-semibold text-white mb-4">Performance Metrics</h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                  <div className="text-center">
                    <div className="text-lg sm:text-2xl font-bold text-green-400">+{selectedStrategy.performance.totalReturn}%</div>
                    <div className="text-gray-400 text-xs sm:text-sm">Total Return</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg sm:text-2xl font-bold text-white">{selectedStrategy.performance.sharpeRatio}</div>
                    <div className="text-gray-400 text-xs sm:text-sm">Sharpe Ratio</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg sm:text-2xl font-bold text-red-400">{selectedStrategy.performance.maxDrawdown}%</div>
                    <div className="text-gray-400 text-xs sm:text-sm">Max Drawdown</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg sm:text-2xl font-bold text-white">{selectedStrategy.performance.winRate}%</div>
                    <div className="text-gray-400 text-xs sm:text-sm">Win Rate</div>
                  </div>
                </div>
              </div>

              {/* Strategy Parameters */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-3">
                  <h3 className="text-lg sm:text-xl font-semibold text-white">Strategy Parameters</h3>
                  <div className="flex items-center gap-2 self-start">
                    {editingParameters ? (
                      <>
                        <button
                          onClick={saveParameters}
                          className="flex items-center gap-2 px-3 py-2 text-green-400 hover:bg-green-400/10 rounded-lg transition-colors touch-friendly"
                        >
                          <Save className="w-4 h-4" />
                          <span className="hidden sm:inline">Save</span>
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="flex items-center gap-2 px-3 py-2 text-red-400 hover:bg-red-400/10 rounded-lg transition-colors touch-friendly"
                        >
                          <X className="w-4 h-4" />
                          <span className="hidden sm:inline">Cancel</span>
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => setEditingParameters(true)}
                        className="flex items-center gap-2 px-3 py-2 text-blue-400 hover:bg-blue-400/10 rounded-lg transition-colors touch-friendly"
                      >
                        <Edit3 className="w-4 h-4" />
                        <span className="hidden sm:inline">Edit</span>
                      </button>
                    )}
                  </div>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {Object.entries(selectedStrategy.parameters).map(([key, value]) => (
                    <div key={key} className="space-y-2">
                      <label className="text-sm font-medium text-gray-300 capitalize">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </label>
                      {editingParameters ? (
                        <input
                          type={typeof value === 'number' ? 'number' : 'text'}
                          value={editedParameters[key] !== undefined ? editedParameters[key] : value}
                          onChange={(e) => handleParameterEdit(key, 
                            typeof value === 'number' ? parseFloat(e.target.value) : e.target.value
                          )}
                          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly"
                          step={typeof value === 'number' ? '0.01' : undefined}
                        />
                      ) : (
                        <div className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white">
                          {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value.toString()}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Backtest Results */}
              {selectedStrategy.backtestResults && (
                <div className="glass-card p-4 sm:p-6">
                  <h3 className="text-lg sm:text-xl font-semibold text-white mb-4">Backtest Results</h3>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                    <div>
                      <div className="text-gray-400 text-xs sm:text-sm">Period</div>
                      <div className="text-white font-medium text-sm sm:text-base">{selectedStrategy.backtestResults.period}</div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-xs sm:text-sm">Total Return</div>
                      <div className="text-green-400 font-medium text-sm sm:text-base">+{selectedStrategy.backtestResults.totalReturn}%</div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-xs sm:text-sm">Total Trades</div>
                      <div className="text-white font-medium text-sm sm:text-base">{selectedStrategy.backtestResults.trades}</div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-xs sm:text-sm">Avg Return/Trade</div>
                      <div className="text-green-400 font-medium text-sm sm:text-base">+{selectedStrategy.backtestResults.avgReturn}%</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-card p-12 text-center">
              <Brain className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Select a Strategy</h3>
              <p className="text-gray-400">Choose a strategy from the list to view details and configure parameters</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
