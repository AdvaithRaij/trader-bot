import React, { useState } from 'react';
import { User, Bell, Database, Shield, Palette, Key } from 'lucide-react';

interface SettingsSection {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
}

const settingsSections: SettingsSection[] = [
  { id: 'profile', name: 'Profile', icon: User, description: 'Personal information and preferences' },
  { id: 'notifications', name: 'Notifications', icon: Bell, description: 'Alert and notification settings' },
  { id: 'trading', name: 'Trading', icon: Database, description: 'Trading preferences and defaults' },
  { id: 'security', name: 'Security', icon: Shield, description: 'Authentication and security settings' },
  { id: 'appearance', name: 'Appearance', icon: Palette, description: 'Theme and display preferences' },
  { id: 'api', name: 'API Keys', icon: Key, description: 'Broker and data provider connections' }
];

export function Settings() {
  const [activeSection, setActiveSection] = useState('profile');

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mobile-stack">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">Settings</h1>
          <p className="text-gray-400 text-sm sm:text-base">Configure your trading dashboard preferences</p>
        </div>
        <button className="glass-button px-4 sm:px-6 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors touch-friendly self-start sm:self-auto">
          Save Changes
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
          <div className="glass-card p-4 sm:p-6">
            <h2 className="text-lg sm:text-xl font-semibold text-white mb-4 sm:mb-6">
              {settingsSections.find(s => s.id === activeSection)?.name}
            </h2>
            <div className="text-gray-400 text-sm sm:text-base">
              <p>Settings content will be displayed here.</p>
              <p>Current section: {activeSection}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
