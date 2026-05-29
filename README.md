# 🤖 AI-Powered Trading Bot

An intelligent, production-ready intraday trading bot for the Indian stock market with AI-driven decision making and a modern React dashboard.

## 🌟 Features

- **AI-Driven Trading Decisions** - Uses GPT-4/Claude for intelligent trade analysis
- **Real-Time Stock Screening** - Monitors top NSE stocks with technical indicators
- **Automated Execution** - Seamless integration with Fyers API
- **Comprehensive Risk Management** - Position sizing, drawdown protection, and loss limits
- **Modern Dashboard** - Real-time monitoring with responsive React UI
- **Mock Trading Mode** - Safe testing environment before going live
- **Telegram Notifications** - Real-time alerts and daily summaries
- **MongoDB Logging** - Complete trade history and analytics

## 📁 Project Structure

```
trading-bot/
├── backend/                    # Python trading engine
│   ├── src/                   # Core trading modules
│   │   ├── main.py           # Main application & FastAPI server
│   │   ├── screener.py       # Stock screening engine
│   │   ├── ai_decision_engine.py  # AI trading decisions
│   │   ├── broker.py         # Broker interface
│   │   ├── broker_fyers.py   # Fyers API integration
│   │   ├── risk_manager.py   # Risk management
│   │   ├── sentiment.py      # Sentiment analysis
│   │   ├── trade_logger.py   # MongoDB logging
│   │   ├── telegram_notifier.py  # Telegram notifications
│   │   ├── poller.py         # Continuous monitoring
│   │   └── config.py         # Configuration management
│   ├── config/               # Configuration files
│   ├── logs/                 # Application logs
│   ├── data/                 # Market data storage
│   └── requirements.txt      # Python dependencies
│
├── frontend/                  # React dashboard
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/           # Dashboard pages
│   │   ├── App.tsx          # Main React app
│   │   └── main.tsx         # Entry point
│   ├── public/              # Static assets
│   └── package.json         # Node dependencies
│
├── scripts/                   # Utility scripts
│   ├── quickstart.py        # Quick testing script
│   ├── run_bot.py           # Bot startup script
│   ├── fyers_auth.py        # Fyers authentication
│   ├── start.sh             # Setup & start script
│   └── test_commands.sh     # Test all commands
│
├── tests/                     # Unit tests
│   ├── test_screener.py
│   └── conftest.py
│
├── docs/                      # Documentation
│   ├── README.md            # Backend documentation
│   ├── SETUP.md             # Setup guide
│   └── *.md                 # Other docs
│
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **MongoDB** (for logging)
- **Redis** (optional, for task queuing)
- **Fyers API Account** (for live trading)
- **OpenAI or Anthropic API Key** (for AI decisions)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd trading-bot
```

2. **Run the setup script**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

Or manually:

3. **Setup Backend**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

4. **Setup Frontend**
```bash
cd frontend
npm install
```

5. **Configure Environment**
```bash
# Create .env file in project root
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### Configuration

Create a `.env` file in the project root:

```env
# Trading Parameters
INITIAL_CAPITAL=100000
MAX_ACTIVE_TRADES=2
MOCK_MODE=true

# Fyers API
FYERS_APP_ID=your_app_id
FYERS_SECRET_KEY=your_secret_key
FYERS_ACCESS_TOKEN=your_access_token

# AI API Keys (choose one)
OPENAI_API_KEY=your_openai_key
# OR
ANTHROPIC_API_KEY=your_anthropic_key

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database
MONGODB_URL=mongodb://localhost:27017/
DATABASE_NAME=trading_bot
```

## 🎮 Usage

### Run Trading Bot

```bash
# Activate virtual environment
source .venv/bin/activate

# Run bot only
python backend/src/main.py --mode bot

# Run web interface only
python backend/src/main.py --mode web

# Run both bot and web interface
python backend/src/main.py --mode both
```

### Run Frontend Dashboard

```bash
cd frontend
npm run dev
```

Access the dashboard at `http://localhost:3000`

### Quick Test

```bash
# Test all components
python scripts/quickstart.py

# Test Fyers integration
python scripts/test_fyers.py

# Run demo mode
python scripts/run_bot.py demo
```

## 📊 API Endpoints

The backend FastAPI server runs on `http://localhost:8000`

- `GET /` - API status
- `GET /status` - Bot status and statistics
- `POST /start` - Start the trading bot
- `POST /stop` - Stop the trading bot
- `GET /positions` - Current positions
- `GET /trades` - Trade history
- `GET /logs` - Recent logs
- `GET /docs` - Interactive API documentation

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_screener.py

# Run with coverage
python -m pytest --cov=backend/src tests/
```

## 🔒 Safety Features

- **Mock Mode** - Test without real money
- **Daily Loss Limits** - Automatic shutdown after max losses
- **Drawdown Protection** - Stops trading if daily drawdown exceeds limit
- **Position Sizing** - Risk only 1% capital per trade
- **AI Confidence Threshold** - Only trade when AI is confident (>80%)
- **Risk-Reward Ratio** - Minimum 1.5:1 ratio required

## 📈 Trading Strategy

1. **Screening** - Identifies top stocks based on volume and momentum
2. **Sentiment Analysis** - Analyzes news and social media
3. **AI Decision** - GPT-4/Claude evaluates entry, stop-loss, and targets
4. **Risk Check** - Validates against risk parameters
5. **Execution** - Places orders via Fyers API
6. **Monitoring** - Continuous tracking and exit management
7. **Logging** - Records all decisions and outcomes

## 🛠️ Development

### Project Commands

```bash
# Backend
python backend/src/screener.py      # Test screener
python backend/src/sentiment.py     # Test sentiment
python backend/src/broker.py        # Test broker

# Frontend
cd frontend
npm run dev                         # Development server
npm run build                       # Production build
npm run lint                        # Lint code

# Scripts
./scripts/start.sh                  # Full setup
./scripts/test_commands.sh          # Test all commands
```

## 📝 License

See LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the `docs/` directory for detailed documentation
- Review logs in `backend/logs/`
- See `docs/SETUP.md` for troubleshooting

## ⚠️ Disclaimer

This bot is for educational purposes. Trading involves risk. Always test thoroughly in mock mode before live trading. Past performance does not guarantee future results.

