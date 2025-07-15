# 🤖 Advanced Trading Bot

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.0+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-4.9+-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An advanced, AI-powered trading bot with real-time stock screening, automated decision-making, and a modern React dashboard for intraday trading in the Indian stock market.

## ✨ Features

### 🎯 Core Trading Engine
- **AI-Powered Decision Engine**: Uses machine learning for trade decisions
- **Real-time Stock Screening**: Filters top stocks based on volume, volatility, and technical indicators
- **Multi-Broker Support**: Integrated with Fyers API and Zerodha (KiteConnect)
- **Risk Management**: Comprehensive risk assessment and position management
- **Automated Trading**: Fully automated buy/sell execution with stop-loss and take-profit

### 📊 Advanced Analytics
- **Technical Indicators**: RSI, VWAP, Moving Averages, Volume Analysis
- **Sentiment Analysis**: News and social media sentiment integration
- **Performance Tracking**: Detailed trade logging and performance metrics
- **Real-time Monitoring**: Live market data and position tracking

### 🎨 Modern Dashboard
- **React + TypeScript**: Modern, responsive web interface
- **Real-time Updates**: Live market data and trading status
- **Interactive Charts**: TradingView-style charts and visualizations
- **Mobile Responsive**: Works seamlessly on all devices
- **Dark/Light Theme**: Customizable UI themes

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Fyers API credentials
- Telegram Bot Token (for notifications)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AdvaithRaij/trader-bot.git
   cd trader-bot
   ```

2. **Set up Python environment**
   ```bash
   cd trader-bot
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up React frontend**
   ```bash
   cd ../frontend/trading-dashboard
   npm install
   ```

4. **Configure environment variables**
   ```bash
   # Copy example config
   cp trader-bot/.env.example trader-bot/.env
   
   # Edit with your credentials
   nano trader-bot/.env
   ```

5. **Run the application**
   ```bash
   # Start the trading bot
   cd trader-bot
   python run_bot.py
   
   # Start the frontend (in another terminal)
   cd frontend/trading-dashboard
   npm run dev
   ```

## 📁 Project Structure

```
trader-bot/
├── trader-bot/                 # Main trading engine
│   ├── src/
│   │   ├── main.py            # Main trading loop
│   │   ├── screener.py        # Stock screening engine
│   │   ├── ai_decision_engine.py # AI trading decisions
│   │   ├── broker_fyers.py    # Fyers API integration
│   │   ├── risk_manager.py    # Risk management
│   │   └── ...
│   ├── config/                # Configuration files
│   ├── data/                  # Market data storage
│   ├── logs/                  # Trading logs
│   └── tests/                 # Unit tests
├── frontend/
│   └── trading-dashboard/     # React dashboard
│       ├── src/
│       │   ├── components/    # UI components
│       │   ├── pages/         # Dashboard pages
│       │   ├── lib/           # Utilities
│       │   └── ...
│       └── ...
└── README.md
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the `trader-bot` directory:

```env
# Fyers API
FYERS_APP_ID=your_app_id
FYERS_SECRET_KEY=your_secret_key
FYERS_CLIENT_ID=your_client_id
FYERS_REDIRECT_URI=http://localhost:8080/callback

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Configuration
MAX_POSITIONS=5
MAX_INVESTMENT_PER_TRADE=10000
RISK_TOLERANCE=0.02
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=3.0
```

### Trading Parameters
Modify `trader-bot/src/config.py` to adjust:
- Screening criteria
- Risk parameters
- Technical indicator settings
- Trading timeframes

## 🎯 How It Works

### 1. Stock Screening
The bot continuously screens stocks based on:
- Volume spikes (>20% above average)
- Price volatility (0.5-5% range)
- Technical indicators (RSI, VWAP)
- Market liquidity requirements

### 2. AI Decision Engine
Uses machine learning to analyze:
- Historical price patterns
- Technical indicator signals
- Market sentiment
- Risk-reward ratios

### 3. Risk Management
Implements comprehensive risk controls:
- Position sizing based on volatility
- Stop-loss and take-profit levels
- Maximum drawdown limits
- Portfolio diversification

### 4. Trade Execution
Automated execution with:
- Market/limit order placement
- Order status monitoring
- Position management
- Real-time notifications

## 📊 Performance Metrics

The bot tracks and displays:
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Daily/Monthly PnL**: Profit and loss tracking

## 🔒 Security Features

- **API Key Encryption**: Secure credential storage
- **Rate Limiting**: Prevents API abuse
- **Error Handling**: Robust error recovery
- **Logging**: Comprehensive audit trail
- **Backup Systems**: Automatic data backup

## 🛠️ Development

### Running Tests
```bash
cd trader-bot
python -m pytest tests/
```

### Code Quality
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/
```

### Frontend Development
```bash
cd frontend/trading-dashboard
npm run dev      # Development server
npm run build    # Production build
npm run lint     # Code linting
```

## 📈 Trading Strategies

### Current Implementation
- **Momentum Trading**: Identifies stocks with strong momentum
- **Mean Reversion**: Trades oversold/overbought conditions
- **Volume Breakout**: Trades on volume-based breakouts
- **VWAP Strategy**: Trades around VWAP levels

### Customization
Add custom strategies in `trader-bot/src/strategies/`:
```python
class CustomStrategy:
    def analyze(self, data):
        # Your strategy logic
        return signal
    
    def generate_signal(self, analysis):
        # Generate buy/sell signals
        return trade_signal
```

## 🚨 Risk Disclaimer

**Important**: This trading bot is for educational and research purposes. Trading involves substantial risk and may not be suitable for all investors. Past performance does not guarantee future results. Always:

- Test thoroughly with paper trading
- Start with small amounts
- Monitor performance closely
- Understand the risks involved
- Consider consulting financial advisors

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/AdvaithRaij/trader-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AdvaithRaij/trader-bot/discussions)
- **Email**: advaithoffl@gmail.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) for market data
- [Fyers API](https://fyers.in/) for broker integration
- [React](https://reactjs.org/) for the frontend framework
- [TradingView](https://www.tradingview.com/) for chart inspiration

---

**⭐ Star this repository if you find it helpful!**
