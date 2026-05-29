// Test file to verify imports work
import { apiService, PortfolioSummary, ActivePosition, TradeSignal } from './lib/api'

console.log('Imports successful!')
console.log('apiService:', typeof apiService)
console.log('PortfolioSummary:', typeof ({} as PortfolioSummary))
console.log('ActivePosition:', typeof ({} as ActivePosition))
console.log('TradeSignal:', typeof ({} as TradeSignal))

