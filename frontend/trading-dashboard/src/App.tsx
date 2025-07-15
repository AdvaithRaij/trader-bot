import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Screener } from './pages/Screener'
import { TradeLogs } from './pages/TradeLogs'
import { MarketNews } from './pages/MarketNews'
import { StrategyCenter } from './pages/StrategyCenter'
import { RiskManager } from './pages/RiskManager'
import { Settings } from './pages/Settings'

function App() {
  return (
    <Router>
      <div className="min-h-screen" style={{
        background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 25%, #16213e 50%, #0f0f23 100%)',
        backgroundAttachment: 'fixed'
      }}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="screener" element={<Screener />} />
            <Route path="trades" element={<TradeLogs />} />
            <Route path="news" element={<MarketNews />} />
            <Route path="strategy" element={<StrategyCenter />} />
            <Route path="risk" element={<RiskManager />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </div>
    </Router>
  )
}

export default App
