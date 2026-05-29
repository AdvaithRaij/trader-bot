"""
You are an advanced AI code assistant helping me build a production-ready **Python-based intraday stock trading bot** using AI, real-time data, and broker APIs. Follow these requirements strictly:

🔹 SYSTEM OVERVIEW:
The bot should:
1. Start each day by screening the **top 5-10 stocks** with high intraday trading potential using APIs from Screener.in, Chartink, or TradingView.
2. Run **sentiment analysis and news aggregation** on shortlisted stocks using web scraping (Google News, Moneycontrol), Twitter API, and LLM (Claude or GPT-4) to score them based on intraday relevance.
3. Poll the selected stocks every **10 minutes**, and active trades every **1 minute**, to make **AI-informed trade decisions** using indicators like VWAP, RSI, MACD, and candlestick patterns.
4. When a trade is triggered, use the **Zerodha Kite Connect API** (or mock it) to place trades with proper **stop loss and target** using a fixed risk-to-reward ratio.
5. Log every trade with its reasoning, entry/exit, and decision confidence.
6. Build a **risk management engine**: Max 2 active trades at a time, 1% capital per trade, stop trading after 3 losses in a day or 5% drawdown.
7. Generate a daily report of P&L and trade reasons via Telegram Bot API.
8. Ensure all trades are closed before **3:10 PM IST**.

🔹 TECH STACK:
- Language: Python 3.11+
- Frameworks: FastAPI (for REST interface), Celery + Redis (for polling), MongoDB (for logs), WebSocket (for real-time price), pandas
- Brokers: Zerodha Kite Connect (placeholders acceptable)
- AI: Use GPT-4 or Claude via API call wrapper (mockable for now)
- Telegram integration: Telegram Bot API for end-of-day summary

🔹 MODULES TO IMPLEMENT (Break into files or classes):
1. `screener.py` – pulls and filters top 10 stocks based on premarket and volume
2. `sentiment.py` – scrapes headlines and tweets, runs NER and LLM scoring
3. `poller.py` – polls stocks in 10-min cycles (inactive) and 1-min cycles (active trades)
4. `ai_decision_engine.py` – integrates OpenAI/Claude to decide entry/SL/target
5. `broker.py` – wrapper around Zerodha Kite API with mocked order placement
6. `risk_manager.py` – handles drawdown limits, position sizing, max trades logic
7. `trade_logger.py` – stores all trades, reasoning, and outcome to MongoDB
8. `telegram_notifier.py` – sends summary of the day with total P&L and logs
9. `config.py` – environment settings, API keys, capital allocation
10. `main.py` – bootstraps all modules, schedules polling jobs via Celery

🔹 FUNCTIONAL GUARDRAILS:
- All trades must pass a confidence threshold > 80% from the AI before placing.
- Must reject trades with Risk:Reward ratio < 1:1.5.
- Place SL and target immediately after buy/sell.
- Close open trades at 3:10 PM using force-exit.
- Log why a trade was skipped (e.g., weak sentiment, bad R:R).
- Store decisions in MongoDB for backtesting later.

🔹 OTHER REQUIREMENTS:
- Use async tasks for polling.
- Modular code structure, well-commented and production-ready.
- Write one testable function at a time.
- Add docstrings for all classes and methods.
- Use environment variables for API keys and sensitive data.
- Mock external APIs initially if real keys are not available.

Start by generating `screener.py` with a function that pulls the top 50 stocks based on volume and filters to top 10 based on predefined rules. Then, proceed module by module in order.

Write clean, modular, maintainable code. Ask for clarification only if any major decision is ambiguous. Assume that later, I will deploy this bot to a cloud server.

"""
