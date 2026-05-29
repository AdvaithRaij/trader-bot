import React, { useState, useEffect } from 'react';
import { Shield, Settings, Bell, RefreshCw, AlertTriangle, TrendingUp, TrendingDown, DollarSign, Activity, Target, Percent, Save, Plus, Trash2, X } from 'lucide-react';
import { apiService, getAlerts, createAlert, deleteAlert, toggleAlert } from '../lib/trading-api';
import type { Alert } from '../lib/trading-api';


interface RiskMetrics {
  maxDrawdown: number;
  currentDrawdown: number;
  sharpeRatio: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  totalTrades: number;
}

interface RiskLimits {
  maxRiskPerTrade: number;      // Max 1.5% per trade (PLAN_OF_ACTION.md)
  maxOpenRisk: number;          // Max 5% total open risk
  maxDailyLoss: number;         // Max 3% daily loss
  maxTradesPerDay: number;      // Max 10 trades per day
  aiConfidenceThreshold: number; // Min 75% AI confidence
  minRiskReward: number;        // Min 1.5 R:R ratio
  maxPositionSize: number;      // Max position size %
  maxActivePositions: number;   // Max concurrent positions
}

export function RiskManager() {
  const [activeTab, setActiveTab] = useState<'metrics' | 'parameters' | 'alerts'>('metrics');
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [metrics, setMetrics] = useState<RiskMetrics | null>(null);
  // Default values from PLAN_OF_ACTION.md
  const [limits, setLimits] = useState<RiskLimits>({
    maxRiskPerTrade: 1.5,       // 1.5% max risk per trade
    maxOpenRisk: 5,             // 5% max open risk
    maxDailyLoss: 3,            // 3% max daily loss
    maxTradesPerDay: 10,        // 10 trades per day
    aiConfidenceThreshold: 75,  // 75% AI confidence threshold
    minRiskReward: 1.5,         // 1.5 minimum R:R
    maxPositionSize: 10,        // 10% max position size
    maxActivePositions: 5       // 5 max active positions
  });
  const [error, setError] = useState<string | null>(null);

  // Alerts state
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [showAddAlert, setShowAddAlert] = useState(false);
  const [newAlert, setNewAlert] = useState({
    symbol: '',
    type: 'price_above' as 'price_above' | 'price_below' | 'percent_change' | 'volume_spike',
    value: 0,
    telegram: false
  });

  const loadRiskMetrics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.getRiskMetrics();
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load risk metrics:', err);
      setError('Failed to load risk metrics');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAlerts = async () => {
    try {
      const alertsData = await getAlerts();
      setAlerts(alertsData);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    }
  };

  const handleAddAlert = async () => {
    if (!newAlert.symbol || !newAlert.value) return;

    try {
      const result = await createAlert({
        symbol: newAlert.symbol.toUpperCase(),
        type: newAlert.type,
        condition: { value: newAlert.value },
        enabled: true,
        notification: { push: true, telegram: newAlert.telegram, sound: true }
      });

      if (result.success && result.alert) {
        setAlerts(prev => [result.alert!, ...prev]);
        setShowAddAlert(false);
        setNewAlert({ symbol: '', type: 'price_above', value: 0, telegram: false });
      }
    } catch (err) {
      console.error('Failed to create alert:', err);
    }
  };

  const handleDeleteAlert = async (alertId: string) => {
    try {
      const result = await deleteAlert(alertId);
      if (result.success) {
        setAlerts(prev => prev.filter(a => (a._id || a.id) !== alertId));
      }
    } catch (err) {
      console.error('Failed to delete alert:', err);
    }
  };

  const handleToggleAlert = async (alertId: string) => {
    try {
      const result = await toggleAlert(alertId);
      if (result.success) {
        setAlerts(prev => prev.map(a =>
          (a._id || a.id) === alertId ? { ...a, enabled: result.enabled! } : a
        ));
      }
    } catch (err) {
      console.error('Failed to toggle alert:', err);
    }
  };

  useEffect(() => {
    loadRiskMetrics();
    loadAlerts();
    const interval = setInterval(loadRiskMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusFromValue = (value: number, warningThreshold: number, dangerThreshold: number): 'safe' | 'warning' | 'danger' => {
    if (value >= dangerThreshold) return 'danger';
    if (value >= warningThreshold) return 'warning';
    return 'safe';
  };

  const getStatusColor = (status: 'safe' | 'warning' | 'danger') => {
    switch (status) {
      case 'safe': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'danger': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusBg = (status: 'safe' | 'warning' | 'danger') => {
    switch (status) {
      case 'safe': return 'bg-green-400/10';
      case 'warning': return 'bg-yellow-400/10';
      case 'danger': return 'bg-red-400/10';
      default: return 'bg-gray-400/10';
    }
  };

  const handleSaveLimits = async () => {
    setIsSaving(true);
    try {
      await apiService.updateRiskLimits({
        maxDrawdown: limits.maxOpenRisk,
        maxDailyLoss: limits.maxDailyLoss,
        maxPositionSize: limits.maxPositionSize
      });
    } catch (err) {
      console.error('Failed to save limits:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const formatPercent = (value: number) => `${value.toFixed(2)}%`;
  const formatCurrency = (value: number) => `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mobile-stack">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">Risk Manager</h1>
          <p className="text-gray-400 text-sm sm:text-base">Monitor and configure risk management parameters</p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 self-start sm:self-auto">
          <button
            onClick={() => setAlertsEnabled(!alertsEnabled)}
            className={`glass-button px-3 sm:px-4 py-2 rounded-lg flex items-center gap-2 transition-colors touch-friendly ${
              alertsEnabled ? 'text-green-400 hover:bg-green-400/10' : 'text-gray-400 hover:bg-gray-400/10'
            }`}
          >
            <Bell className="w-4 h-4" />
            <span className="hidden sm:inline">{alertsEnabled ? 'Alerts On' : 'Alerts Off'}</span>
          </button>
          <button
            onClick={loadRiskMetrics}
            disabled={isLoading}
            className="glass-button px-3 sm:px-4 py-2 rounded-lg flex items-center gap-2 text-white hover:bg-white/10 transition-colors touch-friendly disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      <div className="flex space-x-1 glass-card p-1 w-full sm:w-fit overflow-x-auto">
        {[
          { key: 'metrics', label: 'Risk Metrics', icon: Shield },
          { key: 'parameters', label: 'Parameters', icon: Settings },
          { key: 'alerts', label: 'Alert Rules', icon: Bell }
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-3 sm:px-4 py-2 rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap touch-friendly ${
              activeTab === tab.key 
                ? 'bg-blue-500/20 text-blue-400' 
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span className="text-sm sm:text-base">{tab.label}</span>
          </button>
        ))}
      </div>

      {activeTab === 'metrics' && (
        <div className="space-y-6">
          {isLoading && !metrics ? (
            <div className="glass-card p-8 text-center">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-400 mx-auto mb-4" />
              <p className="text-gray-400">Loading risk metrics...</p>
            </div>
          ) : error ? (
            <div className="glass-card p-8 text-center">
              <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-4" />
              <p className="text-red-400">{error}</p>
            </div>
          ) : metrics ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
              {/* Max Drawdown */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-red-400/10">
                    <TrendingDown className="w-5 h-5 text-red-400" />
                  </div>
                  <h3 className="font-medium text-white">Max Drawdown</h3>
                </div>
                <div className="text-2xl font-bold text-red-400 mb-1">
                  {formatPercent(metrics.maxDrawdown)}
                </div>
                <p className="text-gray-400 text-xs">Maximum portfolio decline from peak</p>
              </div>

              {/* Current Drawdown */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-yellow-400/10">
                    <Activity className="w-5 h-5 text-yellow-400" />
                  </div>
                  <h3 className="font-medium text-white">Current Drawdown</h3>
                </div>
                <div className={`text-2xl font-bold mb-1 ${metrics.currentDrawdown > 3 ? 'text-red-400' : metrics.currentDrawdown > 1 ? 'text-yellow-400' : 'text-green-400'}`}>
                  {formatPercent(metrics.currentDrawdown)}
                </div>
                <p className="text-gray-400 text-xs">Current decline from peak</p>
              </div>

              {/* Win Rate */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-green-400/10">
                    <Target className="w-5 h-5 text-green-400" />
                  </div>
                  <h3 className="font-medium text-white">Win Rate</h3>
                </div>
                <div className={`text-2xl font-bold mb-1 ${metrics.winRate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                  {formatPercent(metrics.winRate)}
                </div>
                <p className="text-gray-400 text-xs">Percentage of winning trades</p>
              </div>

              {/* Sharpe Ratio */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-blue-400/10">
                    <TrendingUp className="w-5 h-5 text-blue-400" />
                  </div>
                  <h3 className="font-medium text-white">Sharpe Ratio</h3>
                </div>
                <div className={`text-2xl font-bold mb-1 ${metrics.sharpeRatio >= 1 ? 'text-green-400' : metrics.sharpeRatio >= 0 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {metrics.sharpeRatio.toFixed(2)}
                </div>
                <p className="text-gray-400 text-xs">Risk-adjusted return measure</p>
              </div>

              {/* Average Win */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-green-400/10">
                    <DollarSign className="w-5 h-5 text-green-400" />
                  </div>
                  <h3 className="font-medium text-white">Average Win</h3>
                </div>
                <div className="text-2xl font-bold text-green-400 mb-1">
                  {formatCurrency(metrics.avgWin)}
                </div>
                <p className="text-gray-400 text-xs">Average profit per winning trade</p>
              </div>

              {/* Average Loss */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-red-400/10">
                    <DollarSign className="w-5 h-5 text-red-400" />
                  </div>
                  <h3 className="font-medium text-white">Average Loss</h3>
                </div>
                <div className="text-2xl font-bold text-red-400 mb-1">
                  {formatCurrency(Math.abs(metrics.avgLoss))}
                </div>
                <p className="text-gray-400 text-xs">Average loss per losing trade</p>
              </div>

              {/* Total Trades */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-purple-400/10">
                    <Activity className="w-5 h-5 text-purple-400" />
                  </div>
                  <h3 className="font-medium text-white">Total Trades</h3>
                </div>
                <div className="text-2xl font-bold text-purple-400 mb-1">
                  {metrics.totalTrades}
                </div>
                <p className="text-gray-400 text-xs">Number of trades executed</p>
              </div>

              {/* Risk/Reward Ratio */}
              <div className="glass-card p-4 sm:p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-cyan-400/10">
                    <Percent className="w-5 h-5 text-cyan-400" />
                  </div>
                  <h3 className="font-medium text-white">Risk/Reward</h3>
                </div>
                <div className={`text-2xl font-bold mb-1 ${metrics.avgLoss !== 0 && Math.abs(metrics.avgWin / metrics.avgLoss) >= 1.5 ? 'text-green-400' : 'text-yellow-400'}`}>
                  {metrics.avgLoss !== 0 ? Math.abs(metrics.avgWin / metrics.avgLoss).toFixed(2) : 'N/A'}
                </div>
                <p className="text-gray-400 text-xs">Average win to loss ratio</p>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {activeTab === 'parameters' && (
        <div className="glass-card p-4 sm:p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg sm:text-xl font-semibold text-white">Risk Parameters</h3>
            <button
              onClick={handleSaveLimits}
              disabled={isSaving}
              className="glass-button px-4 py-2 rounded-lg flex items-center gap-2 text-green-400 hover:bg-green-400/10 transition-colors disabled:opacity-50"
            >
              <Save className={`w-4 h-4 ${isSaving ? 'animate-spin' : ''}`} />
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>

          {/* PLAN_OF_ACTION.md Risk Parameters */}
          <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <h4 className="text-sm font-medium text-blue-400 mb-2">📋 PLAN_OF_ACTION.md Risk Rules</h4>
            <p className="text-xs text-gray-400">These parameters are configured according to the trading plan specifications.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Risk Per Trade */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Max Risk Per Trade (%)</label>
              <input
                type="number"
                value={limits.maxRiskPerTrade}
                onChange={(e) => setLimits({ ...limits, maxRiskPerTrade: parseFloat(e.target.value) || 0 })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                min="0.1"
                max="5"
                step="0.1"
              />
              <p className="text-xs text-gray-500 mt-1">Max 1.5% per trade (recommended)</p>
            </div>

            {/* Max Open Risk */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Max Open Risk (%)</label>
              <input
                type="number"
                value={limits.maxOpenRisk}
                onChange={(e) => setLimits({ ...limits, maxOpenRisk: parseFloat(e.target.value) || 0 })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                min="0"
                max="20"
                step="0.5"
              />
              <p className="text-xs text-gray-500 mt-1">Max 5% total open risk (recommended)</p>
            </div>

            {/* Max Daily Loss */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Max Daily Loss (%)</label>
              <input
                type="number"
                value={limits.maxDailyLoss}
                onChange={(e) => setLimits({ ...limits, maxDailyLoss: parseFloat(e.target.value) || 0 })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                min="0"
                max="10"
                step="0.5"
              />
              <p className="text-xs text-gray-500 mt-1">Max 3% daily loss (recommended)</p>
            </div>

            {/* Max Trades Per Day */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Max Trades Per Day</label>
              <input
                type="number"
                value={limits.maxTradesPerDay}
                onChange={(e) => setLimits({ ...limits, maxTradesPerDay: parseInt(e.target.value) || 0 })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                min="1"
                max="50"
                step="1"
              />
              <p className="text-xs text-gray-500 mt-1">Max 10 trades/day (recommended)</p>
            </div>

            {/* AI Confidence Threshold */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">AI Confidence Threshold (%)</label>
              <input
                type="number"
                value={limits.aiConfidenceThreshold}
                onChange={(e) => setLimits({ ...limits, aiConfidenceThreshold: parseFloat(e.target.value) || 0 })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                min="50"
                max="100"
                step="5"
              />
              <p className="text-xs text-gray-500 mt-1">Min 75% confidence (recommended)</p>
            </div>

            {/* Min Risk:Reward */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Min Risk:Reward Ratio</label>
              <input
                type="number"
                value={limits.minRiskReward}
                onChange={(e) => setLimits({ ...limits, minRiskReward: parseFloat(e.target.value) || 0 })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                min="1"
                max="5"
                step="0.1"
              />
              <p className="text-xs text-gray-500 mt-1">Min 1.5 R:R (recommended)</p>
            </div>

            {/* Max Position Size */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Max Position Size (%)</label>
              <input
                type="number"
                value={limits.maxPositionSize}
                onChange={(e) => setLimits({ ...limits, maxPositionSize: parseFloat(e.target.value) || 0 })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                min="1"
                max="50"
                step="1"
              />
              <p className="text-xs text-gray-500 mt-1">Max capital per position</p>
            </div>

            {/* Max Active Positions */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Max Active Positions</label>
              <input
                type="number"
                value={limits.maxActivePositions}
                onChange={(e) => setLimits({ ...limits, maxActivePositions: parseInt(e.target.value) || 0 })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                min="1"
                max="20"
                step="1"
              />
              <p className="text-xs text-gray-500 mt-1">Max concurrent positions</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="glass-card p-4 sm:p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg sm:text-xl font-semibold text-white">Price Alerts</h3>
            <button
              onClick={() => setShowAddAlert(true)}
              className="glass-button px-4 py-2 rounded-lg flex items-center gap-2 text-blue-400 hover:bg-blue-400/10 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Alert
            </button>
          </div>

          {/* Add Alert Modal */}
          {showAddAlert && (
            <div className="mb-6 p-4 bg-gray-800/80 rounded-lg border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-white font-medium">Create New Alert</h4>
                <button onClick={() => setShowAddAlert(false)} className="text-gray-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Symbol</label>
                  <input
                    type="text"
                    value={newAlert.symbol}
                    onChange={(e) => setNewAlert({ ...newAlert, symbol: e.target.value.toUpperCase() })}
                    placeholder="e.g., RELIANCE"
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Alert Type</label>
                  <select
                    value={newAlert.type}
                    onChange={(e) => setNewAlert({ ...newAlert, type: e.target.value as typeof newAlert.type })}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="price_above">Price Goes Above</option>
                    <option value="price_below">Price Goes Below</option>
                    <option value="percent_change">Percent Change</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">
                    {newAlert.type === 'percent_change' ? 'Percentage (%)' : 'Price (₹)'}
                  </label>
                  <input
                    type="number"
                    value={newAlert.value || ''}
                    onChange={(e) => setNewAlert({ ...newAlert, value: parseFloat(e.target.value) || 0 })}
                    placeholder={newAlert.type === 'percent_change' ? '5' : '2500'}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    id="telegram-notify"
                    checked={newAlert.telegram}
                    onChange={(e) => setNewAlert({ ...newAlert, telegram: e.target.checked })}
                    className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
                  />
                  <label htmlFor="telegram-notify" className="text-sm text-gray-400">Send Telegram notification</label>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowAddAlert(false)}
                  className="px-4 py-2 rounded-lg text-gray-400 hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddAlert}
                  disabled={!newAlert.symbol || !newAlert.value}
                  className="px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Alert
                </button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Bell className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No alerts configured</p>
                <p className="text-sm">Click "Add Alert" to create your first price alert</p>
              </div>
            ) : (
              alerts.map((alert) => {
                const alertId = alert._id || alert.id || '';
                const icon = alert.type === 'price_above' ? TrendingUp :
                            alert.type === 'price_below' ? TrendingDown :
                            Percent;
                const iconColor = alert.type === 'price_above' ? 'text-green-400' :
                                 alert.type === 'price_below' ? 'text-red-400' :
                                 'text-yellow-400';
                const bgColor = alert.type === 'price_above' ? 'bg-green-400/10' :
                               alert.type === 'price_below' ? 'bg-red-400/10' :
                               'bg-yellow-400/10';
                const Icon = icon;

                return (
                  <div key={alertId} className={`flex items-center justify-between p-4 rounded-lg ${alert.triggered ? 'bg-orange-500/20 border border-orange-500/30' : 'bg-gray-800/50'}`}>
                    <div className="flex items-center gap-4">
                      <div className={`p-2 rounded-lg ${bgColor}`}>
                        <Icon className={`w-5 h-5 ${iconColor}`} />
                      </div>
                      <div>
                        <h4 className="text-white font-medium">{alert.symbol}</h4>
                        <p className="text-gray-400 text-sm">
                          {alert.type === 'price_above' && `Price goes above ₹${alert.condition.value}`}
                          {alert.type === 'price_below' && `Price goes below ₹${alert.condition.value}`}
                          {alert.type === 'percent_change' && `Change exceeds ${alert.condition.value}%`}
                          {alert.triggered && (
                            <span className="ml-2 text-orange-400">
                              • Triggered at ₹{alert.trigger_price?.toFixed(2)}
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={alert.enabled}
                          onChange={() => handleToggleAlert(alertId)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                      </label>
                      <button
                        onClick={() => handleDeleteAlert(alertId)}
                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
