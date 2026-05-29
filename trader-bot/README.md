# 🤖 AI-Powered Intraday Trading Bot

A production-ready Python-based intraday stock trading bot that uses AI for decision-making, real-time market data, and automated risk management. Built specifically for the Indian stock market with Zerodha Kite Connect API integration.

## 🚀 Features

- **AI-Powered Decision Making**: Uses GPT-4/Claude for intelligent trade decisions
- **Real-Time Market Analysis**: Screens top stocks and analyzes sentiment
- **Risk Management**: Comprehensive position sizing and drawdown protection
- **Automated Execution**: Integrates with Fyers API for seamless trading
- **Telegram Notifications**: Daily reports and trade alerts
- **Complete Logging**: All trades and decisions logged to MongoDB
- **Web Dashboard**: FastAPI-based monitoring interface

## 🏗️ Architecture

The bot consists of several specialized modules:

- `screener.py` - Identifies top trading candidates
- `sentiment.py` - Analyzes market sentiment from news and social media
- `ai_decision_engine.py` - Makes AI-powered trading decisions
- `broker.py` - Handles trade execution via Fyers API
- `risk_manager.py` - Manages position sizing and risk controls
- `trade_logger.py` - Logs all activities to MongoDB
- `telegram_notifier.py` - Sends notifications via Telegram
- `poller.py` - Continuous monitoring and execution
- `main.py` - Orchestrates all components

## 📋 Prerequisites

- Python 3.11+
- MongoDB (for logging)
- Redis (for task queuing)
- Fyers API access (App ID, Secret Key, Access Token)
- OpenAI or Anthropic API key
- Telegram Bot Token (optional)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   cd /Users/advaithraij/Documents/projects/trader-bot/trader-bot
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

5. **Start MongoDB and Redis** (if not using cloud services)
   ```bash
   # MongoDB
   brew install mongodb-community
   brew services start mongodb-community

   # Redis
   brew install redis
   brew services start redis
   ```

## ⚙️ Configuration

Edit the `.env` file with your configuration:

### Required for Production
- `FYERS_APP_ID` - Your Fyers App ID (from Fyers Developer Portal)
- `FYERS_SECRET_KEY` - Your Fyers Secret Key
- `FYERS_ACCESS_TOKEN` - Your Fyers Access Token (generate using auth helper)
- `OPENAI_API_KEY` - OpenAI API key for AI decisions

### Fyers API Setup

1. **Create Fyers Account**
   - Sign up at [Fyers](https://fyers.in/)
   - Complete KYC verification

2. **Get API Credentials**
   - Visit [Fyers Developer Portal](https://myapi.fyers.in/)
   - Create a new app to get App ID and Secret Key
   - Add your App ID and Secret Key to `.env` file

3. **Generate Access Token**
   ```bash
   # Use the authentication helper
   python fyers_auth.py --auth
   ```
   
   This will:
   - Open authorization URL in browser
   - Guide you through OAuth2 flow
   - Generate and save access token to `.env`

4. **Test Connection**
   ```bash
   # Test your Fyers API connection
   python fyers_auth.py --test
   ```
- `TELEGRAM_BOT_TOKEN` - Telegram bot token for notifications
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID

### Optional
- `MONGODB_URL` - MongoDB connection string
- `REDIS_URL` - Redis connection string
- `ANTHROPIC_API_KEY` - Alternative to OpenAI

### Trading Parameters
- `INITIAL_CAPITAL` - Starting capital (default: ₹100,000)
- `MAX_ACTIVE_TRADES` - Maximum concurrent trades (default: 2)
- `MAX_CAPITAL_PER_TRADE` - Max capital per trade as percentage (default: 1%)
- `MAX_DAILY_LOSSES` - Stop trading after this many losses (default: 3)
- `AI_CONFIDENCE_THRESHOLD` - Minimum AI confidence for trades (default: 80%)

## 🚀 Usage

### Run Trading Bot
```bash
# Bot only
python src/main.py --mode bot

# Web interface only
python src/main.py --mode web

# Both bot and web interface
python src/main.py --mode both
```

### Run Individual Modules (for testing)
```bash
# Test stock screening
python src/screener.py

# Test sentiment analysis
python src/sentiment.py

# Test AI decision engine
python src/ai_decision_engine.py

# Test broker interface
python src/broker.py

# Test Telegram notifications
python src/telegram_notifier.py
```

### Web Dashboard
Access the monitoring dashboard at `http://localhost:8000`

Available endpoints:
- `/` - Status overview
- `/status` - Detailed bot status
- `/trades/today` - Today's trades
- `/report/today` - Daily report
- `/start` - Start the bot
- `/stop` - Stop the bot

## 📊 Trading Strategy

The bot follows this workflow:

1. **Daily Screening** (9:15 AM)
   - Screens top 50 stocks by volume
   - Filters based on technical indicators
   - Selects top 10 candidates

2. **Sentiment Analysis**
   - Scrapes news headlines and social media
   - Analyzes sentiment using NLP and AI
   - Scores stocks for intraday relevance

3. **Continuous Monitoring**
   - Polls inactive stocks every 10 minutes
   - Monitors active trades every 1 minute
   - Makes AI-informed decisions

4. **Trade Execution**
   - Places trades only with >80% AI confidence
   - Ensures minimum 1:1.5 risk-reward ratio
   - Sets stop loss and target automatically

5. **Risk Management**
   - Maximum 2 active trades
   - 1% capital risk per trade
   - Stops after 3 losses or 5% drawdown
   - Force exits all positions at 3:10 PM

## 🛡️ Risk Controls

- **Position Sizing**: Maximum 1% of capital per trade
- **Drawdown Limit**: Stops trading after 5% daily drawdown
- **Loss Limit**: Stops after 3 consecutive losses
- **Time Limit**: All positions closed by 3:10 PM IST
- **Confidence Threshold**: Only trades with >80% AI confidence
- **Risk-Reward**: Minimum 1:1.5 ratio required

## 📱 Telegram Integration

The bot sends:
- **Startup/Shutdown** notifications
- **Trade alerts** with entry/exit details
- **Risk alerts** for limit breaches
- **Daily reports** with P&L summary
- **Market close** summaries

## 📈 Monitoring & Logging

All activities are logged to:
- **MongoDB**: Complete trade history and decisions
- **Log files**: Detailed application logs
- **Telegram**: Real-time notifications
- **Web dashboard**: Live status monitoring

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Test specific module
python -m pytest tests/test_screener.py

# Run with coverage
python -m pytest --cov=src tests/
```

## 🔧 Development

### Mock Mode
Set `MOCK_MODE=true` in `.env` for testing without real API calls:
- Mock broker operations
- Mock AI decisions
- Mock market data
- Safe for development

### Adding New Features
1. Create new module in `src/`
2. Add configuration to `config.py`
3. Add tests in `tests/`
4. Update documentation

## 📊 Performance Tracking

The bot tracks:
- Win rate and profit factor
- Average trade duration
- Maximum drawdown
- Sharpe ratio (planned)
- All decisions for backtesting

## ⚠️ Important Notes

- **Paper Trading**: Test thoroughly before using real money
- **Market Hours**: Only operates during NSE trading hours (9:15 AM - 3:30 PM IST)
- **Internet Dependency**: Requires stable internet connection
- **API Limits**: Respect broker and data provider rate limits
- **Regulatory Compliance**: Ensure compliance with local trading regulations

## 🆘 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   ```bash
   # Check if MongoDB is running
   brew services list | grep mongodb
   
   # Start MongoDB if not running
   brew services start mongodb-community
   ```

2. **Redis Connection Failed**
   ```bash
   # Check Redis status
   brew services list | grep redis
   
   # Start Redis if not running
   brew services start redis
   ```

3. **API Key Errors**
   - Verify all API keys in `.env` file
   - Check Zerodha Kite Connect app permissions
   - Ensure OpenAI API key has sufficient credits

4. **Telegram Not Working**
   - Verify bot token and chat ID
   - Check if bot has permission to send messages
   - Test with `/telegram/test` endpoint

### Logs Location
- Application logs: `logs/trading_bot.log`
- Error logs: Check console output
- Trade logs: MongoDB `trades` collection

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review log files for errors
3. Test in mock mode first
4. Ensure all dependencies are installed

## ⚖️ Disclaimer

This trading bot is for educational and research purposes. Trading involves significant risk of financial loss. Always:
- Test thoroughly in paper trading mode
- Start with small capital
- Monitor performance regularly
- Understand the risks involved
- Comply with local regulations

The authors are not responsible for any financial losses incurred from using this software.

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for algorithmic trading enthusiasts**
