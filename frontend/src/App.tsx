import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
// REMOVED: Analytics page per user request
// import { Dashboard } from './pages/Dashboard'
import { TradingDashboard } from './pages/TradingDashboard'
// REMOVED: Strategy Manager page per user request
// import { StrategyManager } from './pages/StrategyManager'
import { TradeView } from './pages/TradeView'
// REMOVED: Backtest page per user request
// import { Backtest } from './pages/Backtest'
// REMOVED: Stock Screener page per user request
// import { Screener } from './pages/Screener'
import { TradeLogs } from './pages/TradeLogs'
import { MarketNews } from './pages/MarketNews'
import { StrategyCenter } from './pages/StrategyCenter'
import { RiskManager } from './pages/RiskManager'
import { Settings } from './pages/Settings'
import Pipeline from './pages/Pipeline'

function App() {
  return (
    <Router>
      <div className="min-h-screen" style={{
        background: 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 25%, #16213e 50%, #0f0f23 100%)',
        backgroundAttachment: 'fixed'
      }}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<TradingDashboard />} />
            <Route path="pipeline" element={<Pipeline />} />
            {/* REMOVED: Strategy Manager route per user request */}
            {/* <Route path="strategies" element={<StrategyManager />} /> */}
            <Route path="trade" element={<TradeView />} />
            {/* REMOVED: Analytics route per user request */}
            {/* <Route path="dashboard" element={<Dashboard />} /> */}
            {/* REMOVED: Stock Screener route per user request */}
            {/* <Route path="screener" element={<Screener />} /> */}
            <Route path="trades" element={<TradeLogs />} />
            <Route path="news" element={<MarketNews />} />
            <Route path="strategy" element={<StrategyCenter />} />
            <Route path="risk" element={<RiskManager />} />
            {/* REMOVED: Backtest route per user request */}
            {/* <Route path="backtest" element={<Backtest />} /> */}
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </div>
    </Router>
  )
}

export default App
