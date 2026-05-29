import React, { useState, useEffect } from 'react';
import { User, Bell, Database, Shield, Palette, Key, RefreshCw, CheckCircle, XCircle, AlertTriangle, TrendingUp, Clock, DollarSign, Activity, Zap } from 'lucide-react';
import { apiService } from '../lib/trading-api';

interface SettingsSection {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
}

interface Settings {
  trading: {
    initialCapital: number;
    maxCapitalPerTrade: number;
    maxActiveTrades: number;
    maxDailyLosses: number;
    maxDailyDrawdown: number;
    minRiskRewardRatio: number;
    aiConfidenceThreshold: number;
  };
  marketHours: {
    tradingStart: string;
    tradingEnd: string;
    forceExitTime: string;
  };
  broker: {
    connected: boolean;
    mode: string;
    provider: string;
    hasApiKey: boolean;
  };
  ai: {
    provider: string;
    model: string;
    hasApiKey: boolean;
  };
  notifications: {
    telegramEnabled: boolean;
    hasTelegramToken: boolean;
  };
  database: {
    connected: boolean;
    url: string;
  };
}

interface ApiStatus {
  broker: { name: string; connected: boolean; mode: string };
  ai: { name: string; connected: boolean; model: string };
  database: { name: string; connected: boolean };
  telegram: { name: string; connected: boolean };
  news: { name: string; connected: boolean; sources: string[] };
}

const settingsSections: SettingsSection[] = [
  { id: 'trading', name: 'Trading', icon: TrendingUp, description: 'Trading preferences and defaults' },
  { id: 'api', name: 'API Connections', icon: Key, description: 'Broker and data provider connections' },
  { id: 'notifications', name: 'Notifications', icon: Bell, description: 'Alert and notification settings' },
  { id: 'market', name: 'Market Hours', icon: Clock, description: 'Trading hours configuration' },
];

export function Settings() {
  const [activeSection, setActiveSection] = useState('trading');
  const [settings, setSettings] = useState<Settings | null>(null);
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSettings = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [settingsData, statusData] = await Promise.all([
        apiService.getSettings(),
        apiService.getApiStatus()
      ]);
      setSettings(settingsData);
      setApiStatus(statusData);
    } catch (err) {
      console.error('Failed to load settings:', err);
      setError('Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const formatCurrency = (value: number) => `₹${value.toLocaleString('en-IN')}`;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mobile-stack">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">Settings</h1>
          <p className="text-gray-400 text-sm sm:text-base">Configure your trading dashboard preferences</p>
        </div>
        <button
          onClick={loadSettings}
          disabled={isLoading}
          className="glass-button px-4 sm:px-6 py-2 rounded-lg flex items-center gap-2 text-white hover:bg-white/10 transition-colors touch-friendly self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 sm:gap-6">
        {/* Mobile Settings Navigation */}
        <div className="lg:hidden">
          <div className="glass-card p-3">
            <select
              value={activeSection}
              onChange={(e) => setActiveSection(e.target.value)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly"
            >
              {settingsSections.map((section) => (
                <option key={section.id} value={section.id} className="bg-gray-800">
                  {section.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Desktop Settings Navigation */}
        <div className="hidden lg:block lg:col-span-1">
          <div className="glass-card p-4 space-y-2">
            {settingsSections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors flex items-center gap-3 touch-friendly ${
                  activeSection === section.id
                    ? 'bg-blue-500/20 text-blue-400'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <section.icon className="w-4 h-4 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="font-medium">{section.name}</div>
                  <div className="text-xs opacity-75 truncate">{section.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3">
          {isLoading && !settings ? (
            <div className="glass-card p-8 text-center">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-400 mx-auto mb-4" />
              <p className="text-gray-400">Loading settings...</p>
            </div>
          ) : error ? (
            <div className="glass-card p-8 text-center">
              <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-4" />
              <p className="text-red-400">{error}</p>
            </div>
          ) : (
            <>
              {/* Trading Settings */}
              {activeSection === 'trading' && settings && (
                <div className="glass-card p-4 sm:p-6">
                  <h2 className="text-lg sm:text-xl font-semibold text-white mb-6">Trading Configuration</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="p-4 bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <DollarSign className="w-5 h-5 text-green-400" />
                          <span className="text-gray-400">Initial Capital</span>
                        </div>
                        <div className="text-2xl font-bold text-white">{formatCurrency(settings.trading.initialCapital)}</div>
                      </div>

                      <div className="p-4 bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <Activity className="w-5 h-5 text-blue-400" />
                          <span className="text-gray-400">Max Active Trades</span>
                        </div>
                        <div className="text-2xl font-bold text-white">{settings.trading.maxActiveTrades}</div>
                      </div>

                      <div className="p-4 bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <TrendingUp className="w-5 h-5 text-purple-400" />
                          <span className="text-gray-400">Min Risk/Reward Ratio</span>
                        </div>
                        <div className="text-2xl font-bold text-white">{settings.trading.minRiskRewardRatio}:1</div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="p-4 bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <AlertTriangle className="w-5 h-5 text-yellow-400" />
                          <span className="text-gray-400">Max Capital Per Trade</span>
                        </div>
                        <div className="text-2xl font-bold text-white">{settings.trading.maxCapitalPerTrade}%</div>
                      </div>

                      <div className="p-4 bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <XCircle className="w-5 h-5 text-red-400" />
                          <span className="text-gray-400">Max Daily Losses</span>
                        </div>
                        <div className="text-2xl font-bold text-white">{settings.trading.maxDailyLosses}</div>
                      </div>

                      <div className="p-4 bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <Zap className="w-5 h-5 text-cyan-400" />
                          <span className="text-gray-400">AI Confidence Threshold</span>
                        </div>
                        <div className="text-2xl font-bold text-white">{settings.trading.aiConfidenceThreshold}%</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* API Connections */}
              {activeSection === 'api' && apiStatus && (
                <div className="glass-card p-4 sm:p-6">
                  <h2 className="text-lg sm:text-xl font-semibold text-white mb-6">API Connections</h2>
                  <div className="space-y-4">
                    {Object.entries(apiStatus).map(([key, status]) => (
                      <div key={key} className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-4">
                          <div className={`p-2 rounded-lg ${status.connected ? 'bg-green-400/10' : 'bg-red-400/10'}`}>
                            {status.connected ? (
                              <CheckCircle className="w-5 h-5 text-green-400" />
                            ) : (
                              <XCircle className="w-5 h-5 text-red-400" />
                            )}
                          </div>
                          <div>
                            <h4 className="text-white font-medium">{status.name}</h4>
                            <p className="text-gray-400 text-sm">
                              {'mode' in status && `Mode: ${status.mode}`}
                              {'model' in status && `Model: ${status.model}`}
                              {'sources' in status && `Sources: ${status.sources.join(', ')}`}
                            </p>
                          </div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          status.connected
                            ? 'bg-green-400/10 text-green-400'
                            : 'bg-red-400/10 text-red-400'
                        }`}>
                          {status.connected ? 'Connected' : 'Disconnected'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Notifications */}
              {activeSection === 'notifications' && settings && (
                <div className="glass-card p-4 sm:p-6">
                  <h2 className="text-lg sm:text-xl font-semibold text-white mb-6">Notification Settings</h2>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className={`p-2 rounded-lg ${settings.notifications.telegramEnabled ? 'bg-green-400/10' : 'bg-gray-400/10'}`}>
                          <Bell className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                          <h4 className="text-white font-medium">Telegram Notifications</h4>
                          <p className="text-gray-400 text-sm">Receive trade alerts via Telegram</p>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        settings.notifications.telegramEnabled
                          ? 'bg-green-400/10 text-green-400'
                          : 'bg-gray-400/10 text-gray-400'
                      }`}>
                        {settings.notifications.telegramEnabled ? 'Enabled' : 'Not Configured'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="p-2 rounded-lg bg-blue-400/10">
                          <Bell className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                          <h4 className="text-white font-medium">Trade Execution Alerts</h4>
                          <p className="text-gray-400 text-sm">Get notified when trades are executed</p>
                        </div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" defaultChecked className="sr-only peer" />
                        <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                      </label>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="p-2 rounded-lg bg-yellow-400/10">
                          <AlertTriangle className="w-5 h-5 text-yellow-400" />
                        </div>
                        <div>
                          <h4 className="text-white font-medium">Risk Alerts</h4>
                          <p className="text-gray-400 text-sm">Get notified when risk limits are approached</p>
                        </div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" defaultChecked className="sr-only peer" />
                        <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {/* Market Hours */}
              {activeSection === 'market' && settings && (
                <div className="glass-card p-4 sm:p-6">
                  <h2 className="text-lg sm:text-xl font-semibold text-white mb-6">Market Hours Configuration</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-4 bg-gray-800/50 rounded-lg">
                      <div className="flex items-center gap-3 mb-2">
                        <Clock className="w-5 h-5 text-green-400" />
                        <span className="text-gray-400">Trading Start</span>
                      </div>
                      <div className="text-2xl font-bold text-white">{settings.marketHours.tradingStart}</div>
                      <p className="text-xs text-gray-500 mt-1">Market opens for trading</p>
                    </div>

                    <div className="p-4 bg-gray-800/50 rounded-lg">
                      <div className="flex items-center gap-3 mb-2">
                        <Clock className="w-5 h-5 text-red-400" />
                        <span className="text-gray-400">Trading End</span>
                      </div>
                      <div className="text-2xl font-bold text-white">{settings.marketHours.tradingEnd}</div>
                      <p className="text-xs text-gray-500 mt-1">Market closes for trading</p>
                    </div>

                    <div className="p-4 bg-gray-800/50 rounded-lg">
                      <div className="flex items-center gap-3 mb-2">
                        <AlertTriangle className="w-5 h-5 text-yellow-400" />
                        <span className="text-gray-400">Force Exit Time</span>
                      </div>
                      <div className="text-2xl font-bold text-white">{settings.marketHours.forceExitTime}</div>
                      <p className="text-xs text-gray-500 mt-1">All positions closed automatically</p>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 text-blue-400 mt-0.5" />
                      <div>
                        <h4 className="text-blue-400 font-medium">NSE Market Hours</h4>
                        <p className="text-gray-400 text-sm mt-1">
                          The Indian stock market (NSE) operates from 9:15 AM to 3:30 PM IST on weekdays.
                          The bot will automatically exit all positions before market close to avoid overnight risk.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
