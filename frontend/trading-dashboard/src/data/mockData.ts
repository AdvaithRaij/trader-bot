// Mock data for the Trading Dashboard
// This file centralizes all mock data used across the application

// ========================
// PORTFOLIO DATA
// ========================
export const portfolioData = [
  { time: '09:30', value: 125000, pnl: 0 },
  { time: '10:00', value: 126200, pnl: 1200 },
  { time: '10:30', value: 125800, pnl: 800 },
  { time: '11:00', value: 127100, pnl: 2100 },
  { time: '11:30', value: 126900, pnl: 1900 },
  { time: '12:00', value: 128200, pnl: 3200 },
  { time: '12:30', value: 127800, pnl: 2800 },
  { time: '13:00', value: 129100, pnl: 4100 },
  { time: '13:30', value: 128700, pnl: 3700 },
  { time: '14:00', value: 130200, pnl: 5200 },
  { time: '14:30', value: 129800, pnl: 4800 },
  { time: '15:00', value: 131247, pnl: 6247 },
];

// ========================
// SECTOR DATA
// ========================
export const sectorData = [
  { name: 'Technology', value: 35, color: '#3B82F6' },
  { name: 'Finance', value: 25, color: '#10B981' },
  { name: 'Healthcare', value: 20, color: '#F59E0B' },
  { name: 'Energy', value: 12, color: '#EF4444' },
  { name: 'Consumer', value: 8, color: '#8B5CF6' },
];

// ========================
// TOP PERFORMERS
// ========================
export const topPerformers = [
  { symbol: 'RELIANCE', price: 2847.50, change: 2.34, changePercent: 0.82 },
  { symbol: 'TCS', price: 3891.20, change: 45.80, changePercent: 1.19 },
  { symbol: 'HDFCBANK', price: 1678.90, change: 23.45, changePercent: 1.42 },
  { symbol: 'INFY', price: 1456.30, change: 18.90, changePercent: 1.31 },
  { symbol: 'ICICIBANK', price: 1089.60, change: 15.40, changePercent: 1.43 },
];

// ========================
// RECENT TRADES
// ========================
export const recentTrades = [
  { id: '1', symbol: 'RELIANCE', side: 'buy', quantity: 10, price: 2845.50, time: '14:23', status: 'executed' },
  { id: '2', symbol: 'TCS', side: 'sell', quantity: 5, price: 3885.20, time: '13:56', status: 'executed' },
  { id: '3', symbol: 'HDFCBANK', side: 'buy', quantity: 15, price: 1675.90, time: '12:34', status: 'executed' },
  { id: '4', symbol: 'INFY', side: 'sell', quantity: 8, price: 1452.30, time: '11:45', status: 'pending' },
];

// ========================
// TRADE LOGS DATA
// ========================
export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  timestamp: string;
  status: 'pending' | 'executed' | 'failed' | 'cancelled';
  pnl?: number;
  fees: number;
  strategy: string;
  confidence: number;
  executionTime: number;
  orderId?: string;
}

export const mockTrades: Trade[] = [
  {
    id: '1',
    symbol: 'RELIANCE',
    side: 'buy',
    quantity: 10,
    price: 2845.50,
    timestamp: '2025-06-25T14:23:15Z',
    status: 'executed',
    pnl: 247.50,
    fees: 15.20,
    strategy: 'AI Momentum',
    confidence: 85,
    executionTime: 1250,
    orderId: 'ORD001234'
  },
  {
    id: '2',
    symbol: 'TCS',
    side: 'sell',
    quantity: 5,
    price: 3885.20,
    timestamp: '2025-06-25T13:56:42Z',
    status: 'executed',
    pnl: 1125.30,
    fees: 9.75,
    strategy: 'Mean Reversion',
    confidence: 78,
    executionTime: 890,
    orderId: 'ORD001235'
  },
  {
    id: '3',
    symbol: 'HDFCBANK',
    side: 'buy',
    quantity: 15,
    price: 1675.90,
    timestamp: '2025-06-25T12:34:28Z',
    status: 'executed',
    pnl: -125.40,
    fees: 12.55,
    strategy: 'Breakout',
    confidence: 72,
    executionTime: 1450,
    orderId: 'ORD001236'
  },
  {
    id: '4',
    symbol: 'INFY',
    side: 'sell',
    quantity: 8,
    price: 1452.30,
    timestamp: '2025-06-25T11:45:18Z',
    status: 'pending',
    fees: 8.50,
    strategy: 'AI Momentum',
    confidence: 81,
    executionTime: 0
  },
  {
    id: '5',
    symbol: 'ICICIBANK',
    side: 'buy',
    quantity: 20,
    price: 1089.60,
    timestamp: '2025-06-25T10:15:33Z',
    status: 'failed',
    fees: 0,
    strategy: 'Support/Resistance',
    confidence: 65,
    executionTime: 0
  }
];

// ========================
// STOCK SCREENER DATA
// ========================
export interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  pe: number;
  sector: string;
  rsi: number;
  macdSignal: 'buy' | 'sell' | 'hold';
  lastUpdated: string;
}

export const mockStocks: Stock[] = [
  {
    symbol: 'RELIANCE',
    name: 'Reliance Industries Ltd',
    price: 2847.50,
    change: 23.45,
    changePercent: 0.83,
    volume: 2847391,
    marketCap: 19234000000,
    pe: 15.4,
    sector: 'Energy',
    rsi: 68.5,
    macdSignal: 'buy',
    lastUpdated: '2025-06-25T15:00:00Z'
  },
  {
    symbol: 'TCS',
    name: 'Tata Consultancy Services',
    price: 3891.20,
    change: 45.80,
    changePercent: 1.19,
    volume: 1456789,
    marketCap: 14234000000,
    pe: 28.9,
    sector: 'Technology',
    rsi: 72.1,
    macdSignal: 'buy',
    lastUpdated: '2025-06-25T15:00:00Z'
  },
  {
    symbol: 'HDFCBANK',
    name: 'HDFC Bank Limited',
    price: 1678.90,
    change: -12.45,
    changePercent: -0.74,
    volume: 3245678,
    marketCap: 9234000000,
    pe: 18.7,
    sector: 'Finance',
    rsi: 45.3,
    macdSignal: 'sell',
    lastUpdated: '2025-06-25T15:00:00Z'
  },
  {
    symbol: 'INFY',
    name: 'Infosys Limited',
    price: 1456.30,
    change: 18.90,
    changePercent: 1.31,
    volume: 987654,
    marketCap: 6123000000,
    pe: 22.1,
    sector: 'Technology',
    rsi: 58.7,
    macdSignal: 'hold',
    lastUpdated: '2025-06-25T15:00:00Z'
  },
  {
    symbol: 'ICICIBANK',
    name: 'ICICI Bank Limited',
    price: 1089.60,
    change: 15.40,
    changePercent: 1.43,
    volume: 1876543,
    marketCap: 7654000000,
    pe: 16.8,
    sector: 'Finance',
    rsi: 62.4,
    macdSignal: 'buy',
    lastUpdated: '2025-06-25T15:00:00Z'
  },
  {
    symbol: 'ITC',
    name: 'ITC Limited',
    price: 456.80,
    change: -8.20,
    changePercent: -1.76,
    volume: 2345678,
    marketCap: 5678000000,
    pe: 28.5,
    sector: 'Consumer',
    rsi: 42.1,
    macdSignal: 'sell',
    lastUpdated: '2025-06-25T15:00:00Z'
  }
];

// ========================
// STRATEGIES DATA
// ========================
export interface Strategy {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'backtest';
  performance: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
  };
  parameters: {
    [key: string]: string | number | boolean;
  };
  lastModified: string;
  backtestResults?: {
    period: string;
    totalReturn: number;
    trades: number;
    avgReturn: number;
  };
}

export const strategies: Strategy[] = [
  {
    id: '1',
    name: 'Momentum Breakout',
    description: 'Identifies stocks breaking above resistance with high volume',
    status: 'active',
    performance: {
      totalReturn: 23.5,
      sharpeRatio: 1.4,
      maxDrawdown: -8.2,
      winRate: 68
    },
    parameters: {
      volumeThreshold: 1.5,
      priceBreakout: 0.02,
      rsiMin: 30,
      rsiMax: 70,
      stopLoss: 0.05,
      takeProfit: 0.15
    },
    lastModified: '2024-01-15T10:30:00Z'
  },
  {
    id: '2',
    name: 'Mean Reversion',
    description: 'Trades oversold stocks with strong fundamentals',
    status: 'inactive',
    performance: {
      totalReturn: 15.8,
      sharpeRatio: 1.1,
      maxDrawdown: -12.1,
      winRate: 72
    },
    parameters: {
      rsiThreshold: 25,
      peRatio: 15,
      debtToEquity: 0.5,
      holdingPeriod: 14,
      stopLoss: 0.08,
      takeProfit: 0.12
    },
    lastModified: '2024-01-14T15:45:00Z'
  },
  {
    id: '3',
    name: 'AI Sentiment Analysis',
    description: 'Uses news sentiment and social media data for trading decisions',
    status: 'backtest',
    performance: {
      totalReturn: 31.2,
      sharpeRatio: 1.8,
      maxDrawdown: -6.5,
      winRate: 74
    },
    parameters: {
      sentimentThreshold: 0.7,
      newsWeight: 0.6,
      socialWeight: 0.4,
      confidenceMin: 0.8,
      positionSize: 0.05,
      rebalanceFreq: 'daily'
    },
    lastModified: '2024-01-16T09:15:00Z',
    backtestResults: {
      period: '6 months',
      totalReturn: 31.2,
      trades: 147,
      avgReturn: 2.1
    }
  }
];

// ========================
// RISK MANAGEMENT DATA
// ========================
export interface RiskMetric {
  id: string;
  name: string;
  current: number;
  limit: number;
  unit: string;
  status: 'safe' | 'warning' | 'danger';
  description: string;
}

export const riskMetrics: RiskMetric[] = [
  {
    id: '1',
    name: 'Portfolio Drawdown',
    current: 3.2,
    limit: 10.0,
    unit: '%',
    status: 'safe',
    description: 'Maximum loss from portfolio peak'
  },
  {
    id: '2',
    name: 'Daily VaR (95%)',
    current: 2.1,
    limit: 3.0,
    unit: '%',
    status: 'safe',
    description: 'Value at Risk for single day'
  },
  {
    id: '3',
    name: 'Position Concentration',
    current: 8.5,
    limit: 10.0,
    unit: '%',
    status: 'warning',
    description: 'Largest single position size'
  },
  {
    id: '4',
    name: 'Leverage Ratio',
    current: 1.2,
    limit: 2.0,
    unit: 'x',
    status: 'safe',
    description: 'Total exposure to equity ratio'
  },
  {
    id: '5',
    name: 'Sector Concentration',
    current: 35,
    limit: 40,
    unit: '%',
    status: 'warning',
    description: 'Maximum allocation to single sector'
  },
  {
    id: '6',
    name: 'Beta to Market',
    current: 1.1,
    limit: 1.5,
    unit: '',
    status: 'safe',
    description: 'Portfolio sensitivity to market movements'
  }
];

// ========================
// USER PROFILE DATA
// ========================
export const userProfile = {
  name: 'Advaith',
  role: 'Trader',
  totalValue: 1312470,
  dayPnL: 6247,
  dayPnLPercent: 4.12,
  activePositions: 12,
  winRate: 78.5
};

// ========================
// NEWS & SENTIMENT DATA
// ========================
export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  content: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentimentScore: number;
  confidence: number;
  source: string;
  author?: string;
  publishedAt: string;
  url?: string;
  symbols?: string[];
  category: 'market' | 'company' | 'economy' | 'technology' | 'policy';
  readTime: number;
}

export const mockNews: NewsItem[] = [
  {
    id: '1',
    title: 'Indian Markets Rally on Strong Q4 Results and Fed Rate Cut Hopes',
    summary: 'Nifty 50 surged 1.2% as banking and IT stocks led the rally following better-than-expected quarterly earnings.',
    content: 'The Indian stock market witnessed a significant rally today with the Nifty 50 index gaining 1.2% to close at 19,847.9 points. Banking and IT stocks led the surge following better-than-expected quarterly earnings from major companies. The rally was further fueled by hopes of potential rate cuts by the Federal Reserve in the coming months.',
    sentiment: 'positive',
    sentimentScore: 0.78,
    confidence: 85,
    source: 'Economic Times',
    author: 'Market Reporter',
    publishedAt: '2025-06-25T14:30:00Z',
    url: 'https://economictimes.com/markets/rally',
    symbols: ['NIFTY', 'BANKNIFTY', 'TCS', 'RELIANCE'],
    category: 'market',
    readTime: 3
  },
  {
    id: '2',
    title: 'RBI Maintains Repo Rate at 6.5%, Focuses on Inflation Control',
    summary: 'Reserve Bank of India keeps key interest rates unchanged, citing need to balance growth and inflation concerns.',
    content: 'The Reserve Bank of India\'s Monetary Policy Committee decided to maintain the repo rate at 6.5% for the third consecutive meeting. The central bank emphasized its focus on controlling inflation while supporting economic growth. Governor Shaktikanta Das highlighted the need for a balanced approach given global economic uncertainties.',
    sentiment: 'neutral',
    sentimentScore: 0.12,
    confidence: 92,
    source: 'Business Standard',
    author: 'Policy Desk',
    publishedAt: '2025-06-25T13:15:00Z',
    url: 'https://business-standard.com/rbi-policy',
    symbols: ['BANKNIFTY', 'HDFCBANK', 'ICICIBANK'],
    category: 'policy',
    readTime: 4
  },
  {
    id: '3',
    title: 'TCS Reports Strong Q4 Numbers, Beats Revenue Estimates',
    summary: 'Tata Consultancy Services posts 12% YoY revenue growth with improved margins and strong deal pipeline.',
    content: 'India\'s largest IT services company TCS reported better-than-expected quarterly results with revenue growing 12% year-on-year to ₹61,327 crores. The company also announced a strong deal pipeline and improved operating margins, signaling robust demand for digital transformation services.',
    sentiment: 'positive',
    sentimentScore: 0.82,
    confidence: 88,
    source: 'Mint',
    author: 'Corporate Reporter',
    publishedAt: '2025-06-25T12:45:00Z',
    url: 'https://mint.com/tcs-results',
    symbols: ['TCS', 'INFY', 'WIPRO'],
    category: 'company',
    readTime: 5
  },
  {
    id: '4',
    title: 'Oil Prices Surge on Middle East Tensions, Energy Stocks Gain',
    summary: 'Crude oil prices jump 3% amid geopolitical concerns, benefiting Indian energy companies.',
    content: 'Global crude oil prices surged on renewed tensions in the Middle East, with Brent crude touching $78 per barrel. Indian energy companies including Reliance Industries and ONGC saw significant gains as investors anticipated higher refining margins and upstream profitability.',
    sentiment: 'positive',
    sentimentScore: 0.65,
    confidence: 75,
    source: 'Reuters',
    author: 'Energy Correspondent',
    publishedAt: '2025-06-25T11:20:00Z',
    url: 'https://reuters.com/oil-surge',
    symbols: ['RELIANCE', 'ONGC', 'BPCL'],
    category: 'economy',
    readTime: 3
  },
  {
    id: '5',
    title: 'Banking Sector Faces NPA Concerns Despite Strong Performance',
    summary: 'While banks report healthy profits, analysts warn of potential asset quality issues in the coming quarters.',
    content: 'The banking sector\'s strong performance in recent quarters may face headwinds as concerns over non-performing assets resurface. Despite healthy profit margins and improved provisioning, analysts are cautioning about potential stress in certain sectors that could impact asset quality.',
    sentiment: 'negative',
    sentimentScore: -0.45,
    confidence: 79,
    source: 'Financial Express',
    author: 'Banking Analyst',
    publishedAt: '2025-06-25T10:30:00Z',
    url: 'https://financialexpress.com/banking-npa',
    symbols: ['BANKNIFTY', 'HDFCBANK', 'ICICIBANK', 'SBIN'],
    category: 'market',
    readTime: 6
  }
];

// ========================
// ALERT RULES DATA
// ========================
export interface AlertRule {
  id: string;
  name: string;
  condition: string;
  value: number;
  isEnabled: boolean;
  type: 'risk' | 'performance' | 'position';
}

export const alertRules: AlertRule[] = [
  {
    id: '1',
    name: 'Portfolio Drawdown Alert',
    condition: 'Portfolio drawdown exceeds',
    value: 5,
    isEnabled: true,
    type: 'risk'
  },
  {
    id: '2',
    name: 'Position Size Alert',
    condition: 'Single position exceeds',
    value: 10,
    isEnabled: true,
    type: 'position'
  },
  {
    id: '3',
    name: 'Daily Loss Alert',
    condition: 'Daily loss exceeds',
    value: 2,
    isEnabled: false,
    type: 'performance'
  },
  {
    id: '4',
    name: 'Margin Call Alert',
    condition: 'Available margin below',
    value: 20,
    isEnabled: true,
    type: 'risk'
  }
];

// ========================
// RISK PARAMETERS DATA
// ========================
export interface RiskParameter {
  id: string;
  name: string;
  currentValue: number;
  maxValue: number;
  unit: string;
  description: string;
}

export const riskParameters: RiskParameter[] = [
  {
    id: '1',
    name: 'Maximum Position Size',
    currentValue: 10,
    maxValue: 15,
    unit: '%',
    description: 'Maximum percentage of portfolio in single position'
  },
  {
    id: '2',
    name: 'Daily Loss Limit',
    currentValue: 3,
    maxValue: 5,
    unit: '%',
    description: 'Maximum daily loss as percentage of portfolio'
  },
  {
    id: '3',
    name: 'Maximum Leverage',
    currentValue: 2,
    maxValue: 3,
    unit: 'x',
    description: 'Maximum leverage allowed for trading'
  },
  {
    id: '4',
    name: 'Stop Loss Percentage',
    currentValue: 5,
    maxValue: 10,
    unit: '%',
    description: 'Default stop loss percentage for new positions'
  }
];
