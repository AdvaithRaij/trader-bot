import React, { useState } from 'react';
import { Shield, Settings, Bell, RefreshCw } from 'lucide-react';
import type { RiskMetric, RiskParameter, AlertRule } from '../data/mockData';
import { riskMetrics, riskParameters, alertRules } from '../data/mockData';

export function RiskManager() {
  const [activeTab, setActiveTab] = useState<'metrics' | 'parameters' | 'alerts'>('metrics');
  const [alertsEnabled, setAlertsEnabled] = useState(true);

  const getStatusColor = (status: RiskMetric['status']) => {
    switch (status) {
      case 'safe': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'danger': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusBg = (status: RiskMetric['status']) => {
    switch (status) {
      case 'safe': return 'bg-green-400/10';
      case 'warning': return 'bg-yellow-400/10';
      case 'danger': return 'bg-red-400/10';
      default: return 'bg-gray-400/10';
    }
  };

  const getUtilization = (current: number, limit: number) => {
    return Math.min((current / limit) * 100, 100);
  };

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
          <button className="glass-button px-3 sm:px-4 py-2 rounded-lg flex items-center gap-2 text-white hover:bg-white/10 transition-colors touch-friendly">
            <RefreshCw className="w-4 h-4" />
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
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {riskMetrics.map((metric) => (
              <div key={metric.id} className="glass-card p-4 sm:p-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-white text-sm sm:text-base">{metric.name}</h3>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBg(metric.status)} ${getStatusColor(metric.status)}`}>
                    {metric.status.toUpperCase()}
                  </div>
                </div>
                
                <div className="mb-3">
                  <div className="flex items-baseline gap-1">
                    <span className={`text-xl sm:text-2xl font-bold ${getStatusColor(metric.status)}`}>
                      {metric.current}
                    </span>
                    <span className="text-gray-400 text-xs sm:text-sm">
                      / {metric.limit}{metric.unit}
                    </span>
                  </div>
                </div>

                <div className="mb-3">
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        metric.status === 'safe' ? 'bg-green-400' :
                        metric.status === 'warning' ? 'bg-yellow-400' : 'bg-red-400'
                      }`}
                      style={{ width: `${getUtilization(metric.current, metric.limit)}%` }}
                    />
                  </div>
                </div>

                <p className="text-gray-400 text-xs">{metric.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'parameters' && (
        <div className="glass-card p-4 sm:p-6">
          <h3 className="text-lg sm:text-xl font-semibold text-white mb-4">Risk Parameters</h3>
          <p className="text-gray-400 text-sm sm:text-base">Configure risk management parameters here.</p>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="glass-card p-4 sm:p-6">
          <h3 className="text-lg sm:text-xl font-semibold text-white mb-4">Alert Rules</h3>
          <p className="text-gray-400 text-sm sm:text-base">Manage alert rules and notifications here.</p>
        </div>
      )}
    </div>
  );
}
