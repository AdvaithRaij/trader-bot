"""
Main Trading Bot Application.
Orchestrates all modules and provides the main entry point for the trading system.
"""

import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import Optional, List, Dict
import uvicorn
from contextlib import asynccontextmanager
from pydantic import BaseModel

# Add src to path
sys.path.append(str(Path(__file__).parent))

from config import get_config, validate_config
from screener import StockScreener
from sentiment import SentimentAnalyzer
from ai_decision_engine import AIDecisionEngine
from broker import initialize_broker, broker
from risk_manager import get_risk_manager
from trade_logger import initialize_trade_logger, trade_logger
from telegram_notifier import notifier
from poller import poller
from news_aggregator import news_aggregator
from broker_resilient import ResilientBroker, trading_circuit_breaker
from fyers_auth import fyers_auth
from fyers_data_socket import fyers_data_socket
from pipeline_orchestrator import PipelineOrchestrator, PipelineState
from ai_insight_provider import AIInsightProvider
from trade_executor import TradeExecutor
from data_aggregator import DataAggregator
from multi_strategy_analyzer import MultiStrategyAnalyzer

config = get_config()


class TradingBot:
    """
    Main trading bot orchestrator.
    Manages the entire trading pipeline and coordinates all modules.
    """
    
    def __init__(self):
        self.config = config
        self.is_running = False
        self.startup_time = None
        
        # Components
        self.screener = None
        self.sentiment_analyzer = None
        self.ai_engine = None
        self.risk_manager = None
        
        # Setup logging
        self.setup_logging()
        
        # Signal handling for graceful shutdown
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Configure logging for the trading bot."""
        try:
            # Remove default logger
            logger.remove()
            
            # Add console logging
            logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                       "<level>{level: <8}</level> | "
                       "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                       "<level>{message}</level>",
                level=self.config.LOG_LEVEL,
                colorize=True
            )
            
            # Add file logging
            log_path = Path(self.config.LOG_FILE_PATH)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_path,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                level=self.config.LOG_LEVEL,
                rotation="1 day",
                retention="30 days",
                compression="zip"
            )
            
            logger.info("✅ Logging configured successfully")
            
        except Exception as e:
            print(f"Error setting up logging: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        import threading

        # When running under uvicorn, this module may be imported from a worker thread.
        # OS signal handlers can only be registered from the main thread, so skip
        # registration in other contexts to avoid ValueError.
        if threading.current_thread() is not threading.main_thread():
            logger.debug("Skipping signal handler setup (not running in main thread).")
            return

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize_components(self) -> bool:
        """Initialize all trading bot components.
        
        Returns:
            Success status
        """
        try:
            logger.info("🚀 Initializing Trading Bot components...")
	
            # Validate configuration
            try:
                validate_config()
                logger.info("✅ Configuration validated")
            except ValueError as e:
                logger.error(f"❌ Configuration validation failed: {e}")
                if not self.config.MOCK_MODE:
                    return False
                logger.warning("Continuing in mock mode...")
	
            # In LIVE mode, ensure Fyers token is valid (and refresh if needed)
            if not self.config.MOCK_MODE:
                logger.info("🔐 Checking Fyers token validity for trading bot startup...")
                try:
                    is_valid, reason = fyers_auth.is_token_valid()
                    if not is_valid:
                        logger.warning(f"⚠️ Token issue: {reason}")
                        if fyers_auth.totp_enabled:
                            logger.info("🔄 Attempting automatic token refresh for trading bot...")
                            new_token, error = await fyers_auth.auto_login()
                            if new_token:
                                # Update config with new token and reinitialize broker client
                                config.FYERS_ACCESS_TOKEN = new_token
                                broker.reinitialize_with_token(new_token)
                                logger.info("🎉 Fyers token automatically refreshed for trading bot startup!")
                            else:
                                logger.error(f"❌ Auto-login failed while starting bot: {error}")
                                return False
                        else:
                            logger.error(
                                "❌ Fyers token invalid and TOTP auto-login not configured; "
                                "cannot start bot in LIVE mode"
                            )
                            return False
                    else:
                        logger.info(f"✅ Fyers token valid: {reason}")
                except Exception as e:
                    logger.error(f"❌ Error while validating/refreshing Fyers token: {e}")
                    return False
	
            # Initialize broker
            logger.info("📊 Initializing broker interface...")
            broker_success = await initialize_broker()
            if not broker_success:
                logger.error("❌ Failed to initialize broker")
                return False
            logger.info("✅ Broker interface initialized")
            
            # Initialize trade logger
            logger.info("📝 Initializing trade logger...")
            logger_success = await initialize_trade_logger()
            if not logger_success:
                logger.warning("⚠️ Trade logger initialization failed, continuing with mock logging")
            else:
                logger.info("✅ Trade logger initialized")
            
            # Initialize components
            self.screener = StockScreener()
            self.sentiment_analyzer = SentimentAnalyzer()
            self.ai_engine = AIDecisionEngine()
            self.risk_manager = get_risk_manager()
            
            # Initialize poller
            logger.info("🔄 Initializing stock poller...")
            poller_success = await poller.initialize()
            if not poller_success:
                logger.error("❌ Failed to initialize poller")
                return False
            logger.info("✅ Stock poller initialized")
            
            # Test Telegram if configured
            if notifier.is_configured():
                logger.info("📱 Testing Telegram connection...")
                async with notifier:
                    telegram_success = await notifier.test_connection()
                    if telegram_success:
                        logger.info("✅ Telegram connection successful")
                    else:
                        logger.warning("⚠️ Telegram connection failed")
            else:
                logger.warning("⚠️ Telegram not configured")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
            return False
    
    async def start(self) -> bool:
        """
        Start the trading bot.
        
        Returns:
            Success status
        """
        try:
            self.startup_time = datetime.now()
            logger.info("🤖 Starting Trading Bot...")
            logger.info(f"Version: 1.0 | Mode: {'MOCK' if self.config.MOCK_MODE else 'LIVE'}")
            logger.info(f"Capital: ₹{self.config.INITIAL_CAPITAL:,.2f}")
            logger.info(f"Max trades: {self.config.MAX_ACTIVE_TRADES}")
            logger.info(f"Risk per trade: {self.config.MAX_CAPITAL_PER_TRADE:.1%}")
            
            # Initialize components
            success = await self.initialize_components()
            if not success:
                logger.error("❌ Failed to initialize components")
                return False
            
            # Send startup notification
            if notifier.is_configured():
                async with notifier:
                    await notifier.send_startup_notification()
            
            # Mark as running
            self.is_running = True
            
            # Start the main trading loop
            logger.info("🔄 Starting main trading loop...")
            await self.run_trading_loop()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting trading bot: {e}")
            return False
    
    async def run_trading_loop(self):
        """Run the main trading loop."""
        try:
            # Start the poller in background
            poller_task = asyncio.create_task(poller.run_continuous_polling())
            
            # Schedule daily report
            report_task = asyncio.create_task(self.schedule_daily_reports())
            
            # Wait for tasks to complete
            await asyncio.gather(poller_task, report_task, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
        finally:
            await self.shutdown()
    
    async def schedule_daily_reports(self):
        """Schedule and send daily reports."""
        try:
            while self.is_running:
                now = datetime.now()
                
                # Send daily report at market close (3:30 PM)
                if now.hour == 15 and now.minute == 30:
                    logger.info("📊 Sending daily report...")
                    
                    if notifier.is_configured():
                        async with notifier:
                            await notifier.send_market_close_summary()
                            await asyncio.sleep(300)  # Wait 5 minutes
                            await notifier.send_daily_report()
                    
                    # Generate and save report to database
                    await trade_logger.generate_daily_report()
                    
                    # Wait until next day
                    await asyncio.sleep(3600)  # 1 hour
                
                # Check every minute
                await asyncio.sleep(60)
                
        except Exception as e:
            logger.error(f"Error in daily report scheduling: {e}")
    
    async def shutdown(self):
        """Gracefully shutdown the trading bot."""
        if not self.is_running:
            return
        
        try:
            logger.info("🛑 Shutting down Trading Bot...")
            self.is_running = False
            
            # Stop poller
            poller.stop()
            
            # Force exit all positions
            if broker:
                logger.info("🚪 Force exiting all positions...")
                await broker.force_exit_all_positions()
            
            # Send shutdown notification
            if notifier.is_configured():
                async with notifier:
                    await notifier.send_shutdown_notification("Graceful shutdown")
                    
                    # Send final report if trading hours
                    now = datetime.now()
                    if 9 <= now.hour <= 15:
                        await notifier.send_daily_report()
            
            # Close trade logger connection
            if trade_logger.client:
                await trade_logger.close()
            
            # Calculate uptime
            if self.startup_time:
                uptime = datetime.now() - self.startup_time
                logger.info(f"📊 Bot uptime: {uptime}")
            
            logger.info("✅ Trading Bot shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def get_status(self) -> dict:
        """Get current bot status."""
        try:
            # Get component statuses
            poller_status = await poller.get_status()
            risk_summary = self.risk_manager.get_risk_summary()
            account_info = await broker.get_account_info()
            
            uptime = None
            if self.startup_time:
                uptime_delta = datetime.now() - self.startup_time
                uptime = str(uptime_delta)
            
            return {
                'is_running': self.is_running,
                'startup_time': self.startup_time.isoformat() if self.startup_time else None,
                'uptime': uptime,
                'mode': 'MOCK' if self.config.MOCK_MODE else 'LIVE',
                'poller_status': poller_status,
                'risk_summary': risk_summary,
                'account_info': account_info,
                'config': {
                    'initial_capital': self.config.INITIAL_CAPITAL,
                    'max_active_trades': self.config.MAX_ACTIVE_TRADES,
                    'max_capital_per_trade': self.config.MAX_CAPITAL_PER_TRADE,
                    'ai_confidence_threshold': self.config.AI_CONFIDENCE_THRESHOLD
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {'error': str(e)}


# Global bot instance
trading_bot = TradingBot()


# FastAPI application for monitoring and control
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Set
import json

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

ws_manager = ConnectionManager()


def is_market_open() -> bool:
    """
    Check if Indian stock market is open.
    NSE/BSE trading hours: 9:15 AM - 3:30 PM IST, Monday to Friday.
    """
    import pytz

    # Get current time in IST
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)

    # Check if it's a weekday (Monday=0 to Friday=4)
    if now.weekday() > 4:  # Saturday or Sunday
        return False

    # Parse market hours from config
    try:
        start_parts = config.TRADING_HOURS_START.split(':')
        end_parts = config.TRADING_HOURS_END.split(':')

        market_open = now.replace(
            hour=int(start_parts[0]),
            minute=int(start_parts[1]),
            second=0,
            microsecond=0
        )
        market_close = now.replace(
            hour=int(end_parts[0]),
            minute=int(end_parts[1]),
            second=0,
            microsecond=0
        )

        return market_open <= now <= market_close
    except Exception as e:
        logger.error(f"Error checking market hours: {e}")
        # Default to market hours check (9:15 AM - 3:30 PM)
        current_time = now.hour * 60 + now.minute
        market_open_time = 9 * 60 + 15  # 9:15 AM
        market_close_time = 15 * 60 + 30  # 3:30 PM
        return market_open_time <= current_time <= market_close_time


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan management."""
    # Startup
    logger.info("🌐 Starting FastAPI server...")

    # Check and auto-refresh Fyers token if needed
    logger.info("🔐 Checking Fyers token validity...")
    try:
        from fyers_auth import fyers_auth
        is_valid, reason = fyers_auth.is_token_valid()
        if not is_valid:
            logger.warning(f"⚠️ Token issue: {reason}")
            if fyers_auth.totp_enabled:
                logger.info("🔄 Attempting automatic token refresh...")
                new_token, error = await fyers_auth.auto_login()
                if new_token:
                    # Update config with new token
                    config.FYERS_ACCESS_TOKEN = new_token
                    # Reinitialize broker with new token
                    broker.reinitialize_with_token(new_token)
                    logger.info("🎉 Token automatically refreshed!")
                else:
                    logger.error(f"❌ Auto-login failed: {error}")
            else:
                logger.warning("⚠️ TOTP not configured. Set FYERS_TOTP_SECRET and FYERS_PIN in .env for auto-renewal")
        else:
            logger.info(f"✅ Fyers token valid: {reason}")
    except Exception as e:
        logger.warning(f"⚠️ Token check error: {e}")

    # Initialize core components (broker, database)
    logger.info("🔌 Initializing core components...")

    # Initialize broker (works in mock mode even without API credentials)
    try:
        broker_success = await initialize_broker()
        if broker_success:
            logger.info("✅ Broker initialized")
        else:
            logger.warning("⚠️ Broker initialization failed, running in mock mode")
    except Exception as e:
        logger.warning(f"⚠️ Broker initialization error: {e}")

    # Initialize trade logger (database)
    try:
        logger_success = await initialize_trade_logger()
        if logger_success:
            logger.info("✅ Database connected")
        else:
            logger.warning("⚠️ Database connection failed")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization error: {e}")

    # Initialize base trading bot components (these don't require bot to be running)
    try:
        trading_bot.screener = StockScreener()
        trading_bot.sentiment_analyzer = SentimentAnalyzer()
        trading_bot.ai_engine = AIDecisionEngine()
        trading_bot.risk_manager = get_risk_manager()
        logger.info("✅ Trading components initialized")
    except Exception as e:
        logger.warning(f"⚠️ Trading components initialization error: {e}")

    # Initialize Fyers data socket for real-time prices
    try:
        if not config.MOCK_MODE:
            await fyers_data_socket.connect()
            logger.info("✅ Fyers data socket initialized")
        else:
            logger.info("🤖 Mock mode - data socket not connected")
    except Exception as e:
        logger.warning(f"⚠️ Data socket initialization error: {e}")

    yield

    # Shutdown
    logger.info("🌐 Shutting down FastAPI server...")
    if trading_bot.is_running:
        await trading_bot.shutdown()


app = FastAPI(
    title="Trading Bot API",
    description="AI-powered intraday trading bot",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Trading Bot API",
        "version": "1.0.0",
        "status": "running" if trading_bot.is_running else "stopped"
    }


@app.get("/status")
async def get_status():
    """Get bot status."""
    return await trading_bot.get_status()


@app.post("/start")
async def start_bot():
    """Start the trading bot."""
    if trading_bot.is_running:
        return {"message": "Bot is already running"}
    
    # Start bot in background
    asyncio.create_task(trading_bot.start())
    return {"message": "Bot starting..."}


@app.post("/stop")
async def stop_bot():
    """Stop the trading bot."""
    if not trading_bot.is_running:
        return {"message": "Bot is not running"}
    
    await trading_bot.shutdown()
    return {"message": "Bot stopped"}


@app.get("/trades/today")
async def get_today_trades():
    """Get today's trades."""
    try:
        trades = await trade_logger.get_daily_trades()
        # Convert ObjectId to string for JSON serialization
        serialized_trades = []
        for trade in trades:
            trade_dict = dict(trade)
            if '_id' in trade_dict:
                trade_dict['_id'] = str(trade_dict['_id'])
            serialized_trades.append(trade_dict)
        return {"trades": serialized_trades}
    except Exception as e:
        return {"error": str(e)}


@app.get("/decisions/today")
async def get_today_decisions():
    """Get today's decisions."""
    try:
        decisions = await trade_logger.get_daily_decisions()
        return {"decisions": decisions}
    except Exception as e:
        return {"error": str(e)}


@app.get("/report/today")
async def get_today_report():
    """Get today's trading report."""
    try:
        report = await trade_logger.generate_daily_report()
        return report
    except Exception as e:
        return {"error": str(e)}


@app.post("/telegram/test")
async def test_telegram():
    """Test Telegram connection."""
    try:
        async with notifier:
            success = await notifier.test_connection()
            return {"success": success}
    except Exception as e:
        return {"error": str(e)}


# ============================================
# SCREENER ENDPOINTS
# ============================================

@app.get("/screener/stocks")
async def get_screened_stocks():
    """Get list of screened stocks based on technical criteria."""
    try:
        if not trading_bot.screener:
            return {"error": "Screener not initialized"}

        stocks = await trading_bot.screener.screen_stocks()

        # Format for frontend
        formatted_stocks = []
        for stock in stocks:
            formatted_stocks.append({
                "symbol": stock.get("symbol"),
                "price": stock.get("current_price", 0),
                "change": stock.get("price_change", 0),
                "changePercent": stock.get("price_change_pct", 0),
                "volume": stock.get("current_volume", 0),
                "marketCap": stock.get("market_cap"),
                "pe": stock.get("pe_ratio"),
                "sector": stock.get("sector"),
                "lastUpdated": datetime.now().isoformat(),
                "rsi": stock.get("rsi"),
                "vwap": stock.get("vwap"),
                "aboveVwap": stock.get("above_vwap"),
                "volumeRatio": stock.get("volume_ratio")
            })

        return {"stocks": formatted_stocks, "count": len(formatted_stocks)}
    except Exception as e:
        logger.error(f"Error getting screened stocks: {e}")
        return {"error": str(e), "stocks": []}


@app.get("/screener/watchlist")
async def get_watchlist():
    """Get current watchlist."""
    try:
        # Get watchlist from config or screener
        watchlist = config.WATCHLIST if hasattr(config, 'WATCHLIST') else []

        if not watchlist:
            return {"watchlist": [], "count": 0}

        # Get current prices for watchlist in a single batch call
        prices = await broker.get_batch_ltp(watchlist)

        watchlist_data = []
        for symbol in watchlist:
            ltp = prices.get(symbol, 0.0)
            watchlist_data.append({
                "symbol": symbol,
                "price": ltp,
                "lastUpdated": datetime.now().isoformat()
            })

        return {"watchlist": watchlist_data, "count": len(watchlist_data)}
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        return {"error": str(e), "watchlist": []}


# ============================================
# WATCHLIST ENDPOINTS (with persistence)
# ============================================

@app.get("/api/watchlist")
async def get_user_watchlist():
    """Get user's watchlist with current prices (batch API call)."""
    try:
        # Get watchlist from database
        if trade_logger.db is not None:
            watchlist_doc = await trade_logger.db.watchlist.find_one({"_id": "default"})
            symbols = watchlist_doc.get("symbols", []) if watchlist_doc else []
        else:
            # Fallback to default watchlist
            symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

        if not symbols:
            return {"watchlist": [], "count": 0}

        # Get current prices in a single batch API call
        prices = await broker.get_batch_ltp(symbols)

        watchlist_data = []
        for symbol in symbols:
            ltp = prices.get(symbol, 0.0)
            # Get previous close for change calculation
            prev_close = ltp * 0.99  # Mock previous close
            change = ltp - prev_close
            change_percent = (change / prev_close) * 100 if prev_close > 0 else 0

            watchlist_data.append({
                "symbol": symbol,
                "name": symbol,  # Could be enhanced with company name lookup
                "price": ltp,
                "change": round(change, 2),
                "changePercent": round(change_percent, 2),
                "lastUpdated": datetime.now().isoformat()
            })

        return {"watchlist": watchlist_data, "count": len(watchlist_data)}
    except Exception as e:
        logger.error(f"Error getting user watchlist: {e}")
        return {"error": str(e), "watchlist": []}


@app.post("/api/watchlist/add")
async def add_to_watchlist(request: dict):
    """Add a symbol to the watchlist."""
    try:
        symbol = request.get("symbol", "").upper().strip()
        if not symbol:
            return {"success": False, "error": "Symbol is required"}

        if trade_logger.db is not None:
            # Get current watchlist
            watchlist_doc = await trade_logger.db.watchlist.find_one({"_id": "default"})
            symbols = watchlist_doc.get("symbols", []) if watchlist_doc else []

            # Check if already exists
            if symbol in symbols:
                return {"success": False, "error": f"{symbol} is already in watchlist"}

            # Add symbol
            symbols.append(symbol)

            # Update database
            await trade_logger.db.watchlist.update_one(
                {"_id": "default"},
                {"$set": {"symbols": symbols, "updatedAt": datetime.now()}},
                upsert=True
            )

            return {"success": True, "message": f"{symbol} added to watchlist", "symbols": symbols}
        else:
            return {"success": False, "error": "Database not connected"}
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/watchlist/remove")
async def remove_from_watchlist(request: dict):
    """Remove a symbol from the watchlist."""
    try:
        symbol = request.get("symbol", "").upper().strip()
        if not symbol:
            return {"success": False, "error": "Symbol is required"}

        if trade_logger.db is not None:
            # Get current watchlist
            watchlist_doc = await trade_logger.db.watchlist.find_one({"_id": "default"})
            symbols = watchlist_doc.get("symbols", []) if watchlist_doc else []

            # Check if exists
            if symbol not in symbols:
                return {"success": False, "error": f"{symbol} is not in watchlist"}

            # Remove symbol
            symbols.remove(symbol)

            # Update database
            await trade_logger.db.watchlist.update_one(
                {"_id": "default"},
                {"$set": {"symbols": symbols, "updatedAt": datetime.now()}},
                upsert=True
            )

            return {"success": True, "message": f"{symbol} removed from watchlist", "symbols": symbols}
        else:
            return {"success": False, "error": "Database not connected"}
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/screener/stocks")
async def get_api_screened_stocks():
    """Get screened stocks with news correlation (API version)."""
    return await get_screened_stocks()


# Get NSE stocks from the actual NIFTY 200 data
def get_nse_stocks_list():
    """Get list of NSE stocks with metadata from NIFTY 200 universe."""
    from data.nifty_stocks import get_all_symbols, get_stock_metadata

    stocks_list = []
    for symbol in get_all_symbols():
        metadata = get_stock_metadata(symbol)
        stocks_list.append({
            "symbol": symbol,
            "name": metadata.get("name", symbol),
            "sector": metadata.get("sector", "Unknown")
        })
    return stocks_list

# Initialize with basic list (metadata will be fetched on demand)
NSE_STOCKS = None

def get_nse_stocks():
    """Get NSE stocks list, initializing if needed."""
    global NSE_STOCKS
    if NSE_STOCKS is None:
        from data.nifty_stocks import get_all_symbols
        # Start with basic list, metadata fetched on search
        NSE_STOCKS = [{"symbol": s, "name": s, "sector": "Unknown"} for s in get_all_symbols()]
    return NSE_STOCKS


@app.get("/api/stocks/search")
async def search_stocks(query: str = "", limit: int = 20):
    """Search for stocks by symbol or name from NIFTY 200 universe."""
    try:
        stocks_list = get_nse_stocks()

        if not query:
            # Return popular stocks (NIFTY 50 first)
            from data.nifty_stocks import NIFTY_50
            popular = [s for s in stocks_list if s["symbol"] in NIFTY_50]
            return {"stocks": popular[:limit], "count": min(limit, len(popular))}

        query_lower = query.lower()

        # Search by symbol or name
        results = [
            stock for stock in stocks_list
            if query_lower in stock["symbol"].lower() or query_lower in stock["name"].lower()
        ]

        # Sort by relevance (exact match first, then starts with, then contains)
        def sort_key(stock):
            symbol_lower = stock["symbol"].lower()
            if symbol_lower == query_lower:
                return 0
            if symbol_lower.startswith(query_lower):
                return 1
            return 2

        results.sort(key=sort_key)

        return {"stocks": results[:limit], "count": len(results[:limit])}
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        return {"error": str(e), "stocks": []}


@app.get("/api/stocks/{symbol}/quote")
async def get_stock_quote(symbol: str):
    """Get current quote for a stock using real data sources."""
    import yfinance as yf

    try:
        # Convert symbol to yfinance format
        def get_yf_symbol(sym: str) -> str:
            """Convert symbol to yfinance format."""
            # Handle indices
            if 'NIFTY50' in sym or 'NIFTY 50' in sym:
                return '^NSEI'  # NIFTY 50 index
            elif 'NIFTYBANK' in sym or 'BANKNIFTY' in sym or 'BANK NIFTY' in sym:
                return '^NSEBANK'  # Bank Nifty index
            elif 'SENSEX' in sym:
                return '^BSESN'  # Sensex index

            # Handle stocks - remove NSE: prefix if present
            clean_symbol = sym.replace('NSE:', '').replace('-INDEX', '')

            # Special cases for stocks with different yfinance symbols
            symbol_map = {
                'TATAMOTORS': 'TATAMOTORS.NS',
                'TATAMOTOR': 'TATAMOTORS.NS',
            }

            if clean_symbol in symbol_map:
                return symbol_map[clean_symbol]

            # Default: add .NS suffix for NSE stocks
            return f"{clean_symbol}.NS"

        yf_symbol = get_yf_symbol(symbol)
        logger.debug(f"Fetching quote for {symbol} using yfinance symbol: {yf_symbol}")

        # Use yfinance for all quotes (more reliable than broker for ticker)
        ticker = yf.Ticker(yf_symbol)

        # Get intraday data if market is open, otherwise daily data
        from datetime import datetime, time
        now = datetime.now()
        market_open = time(9, 15) <= now.time() <= time(15, 30)

        if market_open:
            # Try to get intraday data
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                # Fallback to daily data
                hist = ticker.history(period="5d", interval="1d")
        else:
            # Use daily data outside market hours
            hist = ticker.history(period="5d", interval="1d")

        if hist.empty or len(hist) < 1:
            raise ValueError(f"No data available for {symbol}")

        # Get current and previous close
        today = hist.iloc[-1]

        # For intraday data, use today's open as reference
        # For daily data, use previous day's close
        if len(hist) >= 2:
            prev_close = hist.iloc[-2]['Close']
        else:
            prev_close = today['Open']

        current_price = float(today['Close'])
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close > 0 else 0

        return {
            "symbol": symbol,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "changePercent": round(change_pct, 2),
            "high": round(float(today['High']), 2),
            "low": round(float(today['Low']), 2),
            "open": round(float(today['Open']), 2),
            "volume": int(today['Volume']),
        }

    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {e}")
        return {
            "error": f"Unable to fetch quote for {symbol}",
            "symbol": symbol,
            "price": 0,
            "change": 0,
            "changePercent": 0,
            "high": 0,
            "low": 0,
            "open": 0,
            "volume": 0,
        }


@app.post("/api/stocks/quotes/batch")
async def get_batch_quotes(request: dict):
    """Get quotes for multiple symbols in a single request to avoid rate limiting."""
    import yfinance as yf
    from datetime import datetime, time

    symbols = request.get("symbols", [])
    if not symbols:
        return {"quotes": []}

    try:
        # Symbol mapping function
        def get_yf_symbol(sym: str) -> str:
            """Convert symbol to yfinance format."""
            if 'NIFTY50' in sym or 'NIFTY 50' in sym:
                return '^NSEI'
            elif 'NIFTYBANK' in sym or 'BANKNIFTY' in sym or 'BANK NIFTY' in sym:
                return '^NSEBANK'
            elif 'SENSEX' in sym:
                return '^BSESN'

            clean_symbol = sym.replace('NSE:', '').replace('-INDEX', '')

            symbol_map = {
                'TATAMOTORS': 'TATAMOTORS.NS',
                'TATAMOTOR': 'TATAMOTORS.NS',
            }

            if clean_symbol in symbol_map:
                return symbol_map[clean_symbol]

            return f"{clean_symbol}.NS"

        # Convert all symbols to yfinance format
        yf_symbols = [get_yf_symbol(sym) for sym in symbols]

        # Fetch all quotes in a single batch call
        tickers = yf.Tickers(' '.join(yf_symbols))

        # Determine if market is open
        now = datetime.now()
        market_open = time(9, 15) <= now.time() <= time(15, 30)

        quotes = []
        for i, symbol in enumerate(symbols):
            try:
                yf_symbol = yf_symbols[i]
                ticker = tickers.tickers[yf_symbol]

                # Get historical data
                if market_open:
                    hist = ticker.history(period="1d", interval="1m")
                    if hist.empty:
                        hist = ticker.history(period="5d", interval="1d")
                else:
                    hist = ticker.history(period="5d", interval="1d")

                if hist.empty or len(hist) < 1:
                    continue

                today = hist.iloc[-1]
                prev_close = hist.iloc[-2]['Close'] if len(hist) >= 2 else today['Open']

                current_price = float(today['Close'])
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100 if prev_close > 0 else 0

                quotes.append({
                    "symbol": symbol,
                    "price": round(current_price, 2),
                    "change": round(change, 2),
                    "changePercent": round(change_pct, 2),
                    "high": round(float(today['High']), 2),
                    "low": round(float(today['Low']), 2),
                    "open": round(float(today['Open']), 2),
                    "volume": int(today['Volume']),
                })
            except Exception as e:
                logger.debug(f"Error getting quote for {symbol}: {e}")
                continue

        return {"quotes": quotes, "count": len(quotes)}

    except Exception as e:
        logger.error(f"Error getting batch quotes: {e}")
        return {"quotes": [], "error": str(e)}


# Cache for candle data to prevent excessive Fyers API calls
_candles_cache: Dict[str, Dict] = {}
_candles_cache_expiry: Dict[str, float] = {}
CANDLES_CACHE_TTL = 60  # 60 seconds cache for candles


@app.get("/api/stocks/{symbol}/candles")
async def get_stock_candles(
    symbol: str,
    timeframe: str = "5m",
    days: int = 5,
    end_time: int = None
):
    """
    Get candlestick data for charting with 60-second caching.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE')
        timeframe: '1m', '5m', '15m', '30m', '1H', '4H', '1D', '1W'
        days: Number of days of data
        end_time: Unix timestamp for end time (for pagination/scroll loading)

    Returns:
        candles: List of {time, open, high, low, close, volume}
        firstCandleTime: Timestamp of first candle (for scroll loading)
        symbol: Symbol name
        timeframe: Timeframe used
    """
    import time as time_module

    # Create cache key
    cache_key = f"{symbol}:{timeframe}:{days}:{end_time or 'latest'}"
    now = time_module.time()

    # Check cache
    if cache_key in _candles_cache and cache_key in _candles_cache_expiry:
        if now < _candles_cache_expiry[cache_key]:
            logger.debug(f"📦 Using cached candles for {cache_key}")
            return _candles_cache[cache_key]

    # Map frontend timeframe to Fyers resolution
    resolution_map = {
        '1m': '1', '5m': '5', '15m': '15', '30m': '30',
        '1H': '60', '4H': '240', '1D': 'D', '1W': 'W'
    }
    resolution = resolution_map.get(timeframe, '5')

    try:
        candles = await broker.get_candles(symbol, resolution, days, end_time)

        # Calculate change from first candle for this timeframe
        change = 0
        changePercent = 0
        if candles and len(candles) >= 2:
            first_close = candles[0]['close']
            last_close = candles[-1]['close']
            change = round(last_close - first_close, 2)
            changePercent = round((change / first_close) * 100, 2) if first_close > 0 else 0

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": candles,
            "count": len(candles),
            "firstCandleTime": candles[0]['time'] if candles else None,
            "lastCandleTime": candles[-1]['time'] if candles else None,
            "change": change,
            "changePercent": changePercent
        }

        # Cache the result
        _candles_cache[cache_key] = result
        _candles_cache_expiry[cache_key] = now + CANDLES_CACHE_TTL

        return result
    except Exception as e:
        logger.error(f"Error getting candles for {symbol}: {e}")
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": [],
            "count": 0,
            "error": str(e)
        }


@app.get("/api/screener/stocks-with-news")
async def get_screened_stocks_with_news():
    """Get screened stocks with related news articles."""
    try:
        # Get screened stocks
        stocks_response = await get_screened_stocks()
        stocks = stocks_response.get("stocks", [])

        # Get news
        news_response = await news_aggregator.get_news_with_analysis(limit=100)
        articles = news_response.get("articles", [])

        # Correlate news with stocks
        for stock in stocks:
            symbol = stock.get("symbol", "")
            related_news = []

            for article in articles:
                ai_analysis = article.get("aiAnalysis", {})
                affected_stocks = ai_analysis.get("stocksAffected", [])

                if symbol in affected_stocks:
                    related_news.append({
                        "id": article.get("id"),
                        "title": article.get("title"),
                        "sentiment": ai_analysis.get("sentiment"),
                        "impact": ai_analysis.get("impact"),
                        "relevance": ai_analysis.get("relevance", 0)
                    })

            stock["relatedNews"] = related_news[:5]  # Top 5 related news
            stock["newsCount"] = len(related_news)

        return {
            "stocks": stocks,
            "count": len(stocks),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting stocks with news: {e}")
        return {"error": str(e), "stocks": []}


# ============================================
# PORTFOLIO ENDPOINTS
# ============================================

@app.get("/portfolio")
async def get_portfolio():
    """Get portfolio summary with positions."""
    try:
        # Get account info
        account = await broker.get_account_info()

        # Get positions
        positions = await broker.get_positions()

        # Calculate portfolio metrics
        total_value = account.get('available_balance', 0)
        day_pnl = 0
        position_list = []

        # Get all prices in a single batch call
        if positions:
            symbols = [pos.symbol for pos in positions]
            prices = await broker.get_batch_ltp(symbols)
        else:
            prices = {}

        for pos in positions:
            current_price = prices.get(pos.symbol, 0.0)
            market_value = pos.quantity * current_price
            pnl = (current_price - pos.average_price) * pos.quantity
            pnl_percent = ((current_price - pos.average_price) / pos.average_price * 100) if pos.average_price > 0 else 0

            day_pnl += pnl
            total_value += market_value

            position_list.append({
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "avgPrice": pos.average_price,
                "currentPrice": current_price,
                "pnl": pnl,
                "pnlPercent": pnl_percent,
                "marketValue": market_value
            })

        day_pnl_percent = (day_pnl / total_value * 100) if total_value > 0 else 0

        return {
            "totalValue": total_value,
            "dayPnl": day_pnl,
            "dayPnlPercent": day_pnl_percent,
            "positions": position_list,
            "cash": account.get('available_balance', 0)
        }
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return {"error": str(e)}


@app.get("/portfolio/positions")
async def get_positions():
    """Get current positions (batch LTP call)."""
    try:
        positions = await broker.get_positions()

        if not positions:
            return {"positions": [], "count": 0}

        # Get all prices in a single batch call
        symbols = [pos.symbol for pos in positions]
        prices = await broker.get_batch_ltp(symbols)

        position_list = []
        for pos in positions:
            current_price = prices.get(pos.symbol, 0.0)
            pnl = (current_price - pos.average_price) * pos.quantity
            pnl_percent = ((current_price - pos.average_price) / pos.average_price * 100) if pos.average_price > 0 else 0

            position_list.append({
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "avgPrice": pos.average_price,
                "currentPrice": current_price,
                "pnl": pnl,
                "pnlPercent": pnl_percent,
                "marketValue": pos.quantity * current_price
            })

        return {"positions": position_list, "count": len(position_list)}
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return {"error": str(e), "positions": []}


@app.get("/api/portfolio/summary")
async def get_portfolio_summary():
    """Get portfolio summary with real account data from Fyers."""
    try:
        # Get real account balance from Fyers API
        account_info = await broker.get_account_info()
        available_balance = account_info.get('available_balance', 0.0)
        used_margin = account_info.get('used_margin', 0.0)
        total_capital = available_balance + used_margin

        # Get open positions
        positions = await broker.get_positions()
        open_positions_count = len(positions) if positions else 0

        # Calculate unrealized P&L from positions
        unrealized_pnl = 0.0
        allocated_capital = 0.0
        if positions:
            symbols = [pos.symbol for pos in positions]
            prices = await broker.get_batch_ltp(symbols)
            for pos in positions:
                current_price = prices.get(pos.symbol, pos.entry_price)
                pos_value = current_price * pos.quantity
                allocated_capital += pos_value
                unrealized_pnl += (current_price - pos.entry_price) * pos.quantity

        # Get today's realized P&L from trade logs
        today_pnl = 0.0
        try:
            trades_today = await get_today_trades()
            if trades_today and isinstance(trades_today, list):
                today_pnl = sum(t.get('pnl', 0) for t in trades_today if t.get('pnl'))
        except Exception:
            pass

        total_pnl = unrealized_pnl + today_pnl

        return {
            "totalCapital": total_capital,
            "availableCash": available_balance,
            "allocatedCapital": allocated_capital,
            "totalPnl": total_pnl,
            "totalPnlPercent": (total_pnl / total_capital * 100) if total_capital > 0 else 0,
            "todayPnl": today_pnl,
            "todayPnlPercent": (today_pnl / total_capital * 100) if total_capital > 0 else 0,
            "openPositions": open_positions_count,
            "maxPositions": 5,
            "currentDrawdown": 0,  # Would need historical tracking for accurate value
            "maxDrawdown": 10.0,
            "winRate": 0,  # Would need trade history analysis
            "totalTrades": 0  # Would need trade count from DB
        }
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        # Return zeros if unable to fetch real data
        return {
            "totalCapital": 0,
            "availableCash": 0,
            "allocatedCapital": 0,
            "totalPnl": 0,
            "totalPnlPercent": 0,
            "todayPnl": 0,
            "todayPnlPercent": 0,
            "openPositions": 0,
            "maxPositions": 5,
            "currentDrawdown": 0,
            "maxDrawdown": 10.0,
            "winRate": 0,
            "totalTrades": 0
        }


@app.get("/api/portfolio/positions")
async def get_api_positions():
    """Get active positions from PortfolioManager."""
    try:
        from portfolio_manager import PortfolioManager
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.DATABASE_NAME]

        portfolio_manager = PortfolioManager(
            initial_capital=config.INITIAL_CAPITAL,
            max_position_size_percent=20.0,
            max_daily_loss_percent=5.0,
            max_drawdown_percent=10.0,
            max_open_positions=5,
            db_collection=db.portfolio
        )

        await portfolio_manager.load_from_db()

        positions = []
        for symbol, pos in portfolio_manager.portfolio.openPositions.items():
            positions.append({
                "symbol": pos.symbol,
                "direction": "BUY",  # Assuming all are BUY for now
                "quantity": pos.quantity,
                "entryPrice": pos.entryPrice,
                "currentPrice": pos.currentPrice,
                "stopLoss": pos.stopLoss,
                "target1": pos.target1,
                "target2": pos.target2,
                "pnl": pos.unrealizedPnl,
                "pnlPercent": pos.unrealizedPnlPercent,
                "status": "OPEN",
                "strategyId": pos.strategyId,
                "strategyName": pos.strategyId,  # TODO: Get actual strategy name
                "entryTime": pos.entryTime.isoformat()
            })

        client.close()

        return positions
    except Exception as e:
        logger.error(f"Error getting active positions: {e}")
        return []


# ============================================
# WEBSOCKET ENDPOINTS
# ============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates."""
    await ws_manager.connect(websocket)
    try:
        # Send initial state
        await ws_manager.send_personal_message({
            "type": "connected",
            "message": "Connected to Trading Bot WebSocket"
        }, websocket)

        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type", "")

                if msg_type == "subscribe":
                    # Handle subscription requests
                    channel = message.get("channel", "")
                    await ws_manager.send_personal_message({
                        "type": "subscribed",
                        "channel": channel
                    }, websocket)

                elif msg_type == "ping":
                    await ws_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)

                elif msg_type == "get_positions":
                    # Send current positions
                    positions = await get_api_positions()
                    await ws_manager.send_personal_message({
                        "type": "positions",
                        "data": positions
                    }, websocket)

                elif msg_type == "get_portfolio":
                    # Send portfolio summary
                    summary = await get_portfolio_summary()
                    await ws_manager.send_personal_message({
                        "type": "portfolio",
                        "data": summary
                    }, websocket)

            except json.JSONDecodeError:
                await ws_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON"
                }, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@app.websocket("/ws/portfolio")
async def websocket_portfolio(websocket: WebSocket):
    """WebSocket endpoint for portfolio updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Send portfolio updates every 5 seconds
            summary = await get_portfolio_summary()
            positions = await get_api_positions()

            await ws_manager.send_personal_message({
                "type": "portfolio_update",
                "summary": summary,
                "positions": positions,
                "timestamp": datetime.now().isoformat()
            }, websocket)

            await asyncio.sleep(5)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Portfolio WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@app.websocket("/ws/trades")
async def websocket_trades(websocket: WebSocket):
    """WebSocket endpoint for trade updates."""
    await ws_manager.connect(websocket)
    try:
        last_trade_count = 0

        while True:
            # Check for new trades
            trades = await trade_logger.get_daily_trades()
            current_count = len(trades) if trades else 0

            if current_count != last_trade_count:
                await ws_manager.send_personal_message({
                    "type": "trades_update",
                    "trades": trades[-10:] if trades else [],  # Last 10 trades
                    "totalTrades": current_count,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                last_trade_count = current_count

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Trades WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """WebSocket endpoint for real-time price updates."""
    await ws_manager.connect(websocket)
    subscribed_symbols: set = set()

    try:
        # Send initial connection message
        await ws_manager.send_personal_message({
            "type": "connected",
            "message": "Connected to price stream"
        }, websocket)

        while True:
            try:
                # Check for subscription messages (non-blocking with timeout)
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
                    message = json.loads(data)

                    if message.get("type") == "subscribe":
                        symbols = message.get("symbols", [])
                        # Only subscribe to NEW symbols (not already subscribed)
                        new_symbols = [s for s in symbols if s not in subscribed_symbols]

                        if new_symbols:
                            subscribed_symbols.update(new_symbols)
                            # Only subscribe to Fyers data socket during market hours
                            if is_market_open():
                                fyers_data_socket.subscribe(new_symbols)
                                logger.debug(f"📊 Subscribed to live prices for: {new_symbols}")
                            else:
                                logger.debug(f"⏸️ Market closed - skipping live subscription for: {new_symbols}")

                        await ws_manager.send_personal_message({
                            "type": "subscribed",
                            "symbols": list(subscribed_symbols),
                            "market_open": is_market_open()
                        }, websocket)

                    elif message.get("type") == "unsubscribe":
                        symbols = message.get("symbols", [])
                        subscribed_symbols.difference_update(symbols)
                        fyers_data_socket.unsubscribe(symbols)
                        await ws_manager.send_personal_message({
                            "type": "unsubscribed",
                            "symbols": list(subscribed_symbols)
                        }, websocket)

                except asyncio.TimeoutError:
                    pass  # No message received, continue to send prices

                # Send price updates for subscribed symbols
                if subscribed_symbols:
                    market_is_open = is_market_open()
                    prices = []

                    for symbol in subscribed_symbols:
                        try:
                            # Try to get from data socket cache first (real-time)
                            cached_price = fyers_data_socket.get_latest_price(symbol)
                            if cached_price:
                                prices.append({
                                    "symbol": symbol,
                                    "price": cached_price.get("ltp", 0),
                                    "change": cached_price.get("change", 0),
                                    "changePercent": cached_price.get("changePercent", 0),
                                    "high": cached_price.get("high", 0),
                                    "low": cached_price.get("low", 0),
                                    "volume": cached_price.get("volume", 0)
                                })
                            elif market_is_open:
                                # Only poll broker during market hours
                                quote = broker.get_quote(symbol)
                                if quote:
                                    prices.append({
                                        "symbol": symbol,
                                        "price": quote.get("ltp", 0),
                                        "change": quote.get("change", 0),
                                        "changePercent": quote.get("changePercent", 0),
                                        "high": quote.get("high", 0),
                                        "low": quote.get("low", 0),
                                        "volume": quote.get("volume", 0)
                                    })
                        except Exception as e:
                            logger.debug(f"Error getting quote for {symbol}: {e}")

                    if prices:
                        await ws_manager.send_personal_message({
                            "type": "prices",
                            "data": prices,
                            "market_open": market_is_open,
                            "timestamp": datetime.now().isoformat()
                        }, websocket)

                    # Slower polling outside market hours (10 sec vs 2 sec)
                    if not market_is_open:
                        await asyncio.sleep(8)  # Extra sleep for total ~10 sec

            except WebSocketDisconnect:
                break
            except Exception as e:
                # Check if it's a connection closed error
                if "not connected" in str(e).lower() or "closed" in str(e).lower():
                    break
                logger.error(f"Price WebSocket error: {e}")
                await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        if "not connected" not in str(e).lower():
            logger.error(f"Price WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket)


@app.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    """WebSocket endpoint for pipeline status updates."""
    await ws_manager.connect(websocket)
    try:
        # Send initial connection message
        await ws_manager.send_personal_message({
            "type": "connected",
            "message": "Connected to pipeline stream"
        }, websocket)

        while True:
            try:
                # Check for messages from client (non-blocking with timeout)
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                    message = json.loads(data)

                    if message.get("type") == "ping":
                        await ws_manager.send_personal_message({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }, websocket)

                except asyncio.TimeoutError:
                    pass  # No message received, continue to send status

                # Send pipeline status update
                if pipeline_orchestrator:
                    status = pipeline_orchestrator.get_status()
                    await ws_manager.send_personal_message({
                        "type": "pipeline_status",
                        "data": status,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                else:
                    await ws_manager.send_personal_message({
                        "type": "pipeline_status",
                        "data": {
                            "state": "STOPPED",
                            "is_running": False,
                            "message": "Pipeline not initialized"
                        },
                        "timestamp": datetime.now().isoformat()
                    }, websocket)

                await asyncio.sleep(5)  # Update every 5 seconds

            except WebSocketDisconnect:
                break
            except Exception as e:
                if "not connected" in str(e).lower() or "closed" in str(e).lower():
                    break
                logger.error(f"Pipeline WebSocket error: {e}")
                await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        if "not connected" not in str(e).lower():
            logger.error(f"Pipeline WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket)


# Helper function to broadcast position updates
async def broadcast_position_update(position_data: dict):
    """Broadcast position update to all connected clients."""
    await ws_manager.broadcast({
        "type": "position_update",
        "data": position_data,
        "timestamp": datetime.now().isoformat()
    })


# Helper function to broadcast trade execution
async def broadcast_trade_execution(trade_data: dict):
    """Broadcast trade execution to all connected clients."""
    await ws_manager.broadcast({
        "type": "trade_executed",
        "data": trade_data,
        "timestamp": datetime.now().isoformat()
    })


# ============================================
# TRADE ENDPOINTS
# ============================================

@app.get("/trades")
async def get_trades(limit: int = 50):
    """Get recent trades with optional limit."""
    try:
        trades = await trade_logger.get_recent_trades(limit=limit)

        # Format for frontend
        formatted_trades = []
        for trade in trades:
            formatted_trades.append({
                "id": str(trade.get("_id", "")),
                "symbol": trade.get("symbol"),
                "side": trade.get("transaction_type", "").lower(),
                "quantity": trade.get("quantity", 0),
                "price": trade.get("price", 0),
                "timestamp": trade.get("timestamp", datetime.now()).isoformat(),
                "status": trade.get("status", "unknown"),
                "pnl": trade.get("pnl", 0),
                "reason": trade.get("reason", "")
            })

        return {"trades": formatted_trades, "count": len(formatted_trades)}
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return {"error": str(e), "trades": []}


@app.get("/trades/history")
async def get_trade_history(days: int = 7):
    """Get trade history for specified number of days."""
    try:
        trades = await trade_logger.get_trade_history(days=days)

        formatted_trades = []
        for trade in trades:
            formatted_trades.append({
                "id": str(trade.get("_id", "")),
                "symbol": trade.get("symbol"),
                "side": trade.get("transaction_type", "").lower(),
                "quantity": trade.get("quantity", 0),
                "price": trade.get("price", 0),
                "timestamp": trade.get("timestamp", datetime.now()).isoformat(),
                "status": trade.get("status", "unknown"),
                "pnl": trade.get("pnl", 0),
                "reason": trade.get("reason", "")
            })

        return {"trades": formatted_trades, "count": len(formatted_trades), "days": days}
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        return {"error": str(e), "trades": []}


@app.post("/trade/execute")
@app.post("/api/trades/execute")
async def execute_trade(trade_request: dict):
    """Execute a manual trade."""
    try:
        symbol = trade_request.get("symbol")
        side = trade_request.get("side")  # "buy" or "sell"
        quantity = trade_request.get("quantity")
        order_type = trade_request.get("orderType", "market")
        price = trade_request.get("price", 0)

        if not symbol or not side or not quantity:
            return {"error": "Missing required fields: symbol, side, quantity"}

        # Convert side to transaction type
        transaction_type = "1" if side.lower() == "buy" else "-1"

        # Place order
        order_id = await broker.place_order(
            symbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=order_type.upper(),
            price=price
        )

        if order_id:
            # Log the trade execution
            order_details = {
                "transaction_type": side.upper(),
                "quantity": quantity,
                "order_type": order_type.upper(),
                "price": price
            }
            execution_result = {
                "status": "COMPLETE",
                "executed_price": price,
                "executed_quantity": quantity,
                "order_id": order_id
            }
            await trade_logger.log_trade_execution(
                symbol=symbol,
                order_details=order_details,
                execution_result=execution_result
            )

            return {"success": True, "orderId": order_id, "message": "Trade executed successfully"}
        else:
            return {"success": False, "error": "Failed to place order"}

    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return {"success": False, "error": str(e)}


# ============================================
# NEWS & SENTIMENT ENDPOINTS
# ============================================

@app.get("/news")
async def get_news(
    page: int = 1,
    limit: int = 10,
    category: str = "all",
    source: str = "all",
    refresh: bool = False
):
    """
    Get market news with AI-powered impact analysis.

    Args:
        page: Page number (1-indexed)
        limit: Items per page (default: 10)
        category: Filter by category (all, market, finance, economy, corporate, policy)
        source: Filter by source (all, Economic Times, Google News, MoneyControl)
        refresh: Force refresh cache
    """
    try:
        # Fetch news with analysis
        all_news = await news_aggregator.get_news_with_analysis(
            limit=100,  # Fetch more for pagination
            category=category if category != "all" else None,
            source=source if source != "all" else None,
            refresh=refresh
        )

        # Calculate pagination
        total_items = len(all_news)
        total_pages = (total_items + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit

        # Get page items
        page_items = all_news[start_idx:end_idx]

        # Always return all configured options (not dynamic based on data)
        # This ensures dropdowns always show all available options
        all_sources = ["Economic Times", "Google News", "MoneyControl"]
        all_categories = ["market", "finance", "economy", "corporate", "policy"]
        all_sentiments = ["positive", "negative", "neutral"]

        return {
            "news": page_items,
            "pagination": {
                "currentPage": page,
                "totalPages": total_pages,
                "totalItems": total_items,
                "itemsPerPage": limit,
                "hasNext": page < total_pages,
                "hasPrevious": page > 1
            },
            "filters": {
                "category": category,
                "availableCategories": all_categories,
                "availableSources": all_sources,
                "availableSentiments": all_sentiments
            }
        }
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        return {"error": str(e), "news": [], "pagination": {}}


@app.get("/news/{news_id}/analysis")
async def get_news_analysis(news_id: str):
    """Get detailed AI analysis for a specific news article."""
    try:
        # Get all news from cache
        all_news = await news_aggregator.get_news_with_analysis(limit=100)

        # Find the specific news item
        news_item = next((n for n in all_news if n['id'] == news_id), None)

        if not news_item:
            return {"error": "News article not found"}

        return {
            "newsId": news_id,
            "title": news_item['title'],
            "summary": news_item['summary'],
            "source": news_item['source'],
            "url": news_item['url'],
            "publishedAt": news_item['publishedAt'],
            "categories": news_item.get('categories', []),
            "aiAnalysis": news_item.get('aiAnalysis', {})
        }
    except Exception as e:
        logger.error(f"Error getting news analysis: {e}")
        return {"error": str(e)}


@app.get("/api/news")
async def get_api_news(
    page: int = 1,
    limit: int = 10,
    category: str = "all",
    source: str = "all",
    refresh: bool = False
):
    """Get news with AI analysis (API version)."""
    return await get_news(page, limit, category, source, refresh)


@app.get("/sentiment/news")
async def get_sentiment_news(limit: int = 20):
    """Get recent news with sentiment analysis (legacy endpoint)."""
    try:
        # Use new news aggregator
        news_items = await news_aggregator.get_news_with_analysis(limit=limit)

        # Format for legacy compatibility
        formatted_news = []
        for item in news_items:
            ai_analysis = item.get('aiAnalysis', {})
            formatted_news.append({
                "id": item['id'],
                "title": item['title'],
                "summary": item['summary'],
                "sentiment": ai_analysis.get('sentiment', 'neutral').lower(),
                "sentimentScore": 0.5,  # Placeholder
                "source": item['source'],
                "publishedAt": item['publishedAt'],
                "url": item['url'],
                "symbols": ai_analysis.get('relatedStocks', [])
            })

        return {"news": formatted_news, "count": len(formatted_news)}
    except Exception as e:
        logger.error(f"Error getting sentiment news: {e}")
        return {"error": str(e), "news": []}


@app.get("/sentiment/analysis")
async def get_sentiment_analysis(symbol: str):
    """Get sentiment analysis for a specific symbol."""
    try:
        if not trading_bot.sentiment_analyzer:
            return {"error": "Sentiment analyzer not initialized"}

        analysis = await trading_bot.sentiment_analyzer.analyze_sentiment(symbol)

        return {
            "symbol": symbol,
            "sentiment": analysis.get("final_sentiment", 0),
            "signal": analysis.get("trade_signal", "NEUTRAL"),
            "newsCount": analysis.get("news_count", 0),
            "intradayRelevance": analysis.get("intraday_relevance", 0),
            "lastUpdated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting sentiment analysis for {symbol}: {e}")
        return {"error": str(e)}


# ============================================
# STRATEGY MANAGEMENT ENDPOINTS
# ============================================

@app.get("/strategies")
async def get_strategies():
    """Get all trading strategies."""
    try:
        from strategy_manager import StrategyManager
        from motor.motor_asyncio import AsyncIOMotorClient

        # Connect to MongoDB
        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.DATABASE_NAME]

        strategy_manager = StrategyManager(db_collection=db.strategies)
        await strategy_manager.load_strategies()

        # Return full strategy objects
        strategies_list = []
        for strategy_id, strategy in strategy_manager.strategies.items():
            strategy_dict = strategy.model_dump()
            # Convert enums to strings
            strategy_dict['status'] = strategy.status.value
            strategy_dict['stockPicking']['type'] = strategy.stockPicking.type.value
            strategy_dict['execution']['type'] = strategy.execution.type.value
            if strategy.createdAt:
                strategy_dict['createdAt'] = strategy.createdAt.isoformat()
            if strategy.updatedAt:
                strategy_dict['updatedAt'] = strategy.updatedAt.isoformat()
            strategies_list.append(strategy_dict)

        client.close()

        return strategies_list
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return []


@app.get("/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get a specific strategy by ID."""
    try:
        from strategy_manager import StrategyManager
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.DATABASE_NAME]

        strategy_manager = StrategyManager(db_collection=db.strategies)
        strategy = await strategy_manager.get_strategy(strategy_id)

        client.close()

        if not strategy:
            return {"error": "Strategy not found"}

        return {"strategy": strategy.model_dump()}
    except Exception as e:
        logger.error(f"Error getting strategy: {e}")
        return {"error": str(e)}


@app.post("/strategies/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: str):
    """Toggle strategy status (ACTIVE <-> PAUSED)."""
    try:
        from strategy_manager import StrategyManager
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.DATABASE_NAME]

        strategy_manager = StrategyManager(db_collection=db.strategies)
        new_status = await strategy_manager.toggle_strategy(strategy_id)

        client.close()

        if not new_status:
            return {"error": "Strategy not found"}

        return {
            "message": f"Strategy status updated to {new_status.value}",
            "status": new_status.value
        }
    except Exception as e:
        logger.error(f"Error toggling strategy: {e}")
        return {"error": str(e)}


@app.post("/strategies/{strategy_id}/run")
async def run_strategy(strategy_id: str):
    """Manually run a specific strategy and generate signals."""
    try:
        from strategy_engine import StrategyEngine
        from strategy_manager import StrategyManager
        from ai_trade_assistant import AITradeAssistant
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.DATABASE_NAME]

        strategy_manager = StrategyManager(db_collection=db.strategies)
        await strategy_manager.load_strategies()

        ai_assistant = AITradeAssistant()

        strategy_engine = StrategyEngine(
            strategy_manager=strategy_manager,
            news_aggregator=news_aggregator,
            broker=broker,
            ai_assistant=ai_assistant
        )

        signals = await strategy_engine.run_strategy(strategy_id)

        client.close()

        return {
            "message": f"Generated {len(signals)} signals",
            "signals": [
                {
                    "symbol": s.symbol,
                    "direction": s.direction.value,
                    "entryPrice": s.entryPrice,
                    "stopLoss": s.stopLoss,
                    "target1": s.target1,
                    "target2": s.target2,
                    "confidence": s.confidence,
                    "reasoning": s.reasoning
                }
                for s in signals
            ]
        }
    except Exception as e:
        logger.error(f"Error running strategy: {e}")
        return {"error": str(e), "signals": []}


# API versions with /api prefix
@app.get("/api/strategies")
async def get_api_strategies():
    """Get all trading strategies (API version)."""
    return await get_strategies()


@app.get("/api/strategies/{strategy_id}")
async def get_api_strategy(strategy_id: str):
    """Get a specific strategy by ID (API version)."""
    return await get_strategy(strategy_id)


@app.post("/api/strategies/{strategy_id}/toggle")
async def toggle_api_strategy(strategy_id: str):
    """Toggle strategy status (API version)."""
    return await toggle_strategy(strategy_id)


@app.post("/api/strategies/{strategy_id}/run")
async def run_api_strategy(strategy_id: str):
    """Manually run a specific strategy (API version)."""
    return await run_strategy(strategy_id)


# ============================================
# LLM STRATEGY CREATION ENDPOINTS
# ============================================

@app.post("/api/strategies/create-from-description")
async def create_strategy_from_description(request: dict):
    """
    Create a new strategy from natural language description.

    Request body:
    {
        "description": "I want to buy stocks when there's positive news with high impact...",
        "strategyId": "my_custom_strategy"  // optional
    }
    """
    try:
        from strategy_creator import strategy_creator
        from strategy_manager import StrategyManager

        description = request.get("description")
        strategy_id = request.get("strategyId")
        save_to_db = request.get("saveToDatabase", True)

        if not description:
            return {"error": "Missing required field: description"}

        # Create strategy from description
        result = await strategy_creator.create_strategy_from_description(
            description=description,
            strategy_id=strategy_id
        )

        if "error" in result:
            return result

        # Optionally save to database
        if save_to_db and result.get("success"):
            manager = StrategyManager()
            strategy_data = result["strategy"]

            # Convert to StrategyModel and save
            from models.strategy import (
                StrategyModel, StockPickingConfig, ExecutionConfig,
                RiskManagementConfig, StockPickingType, ExecutionType, StrategyStatus
            )

            stock_picking = StockPickingConfig(
                type=StockPickingType(strategy_data["stockPicking"]["type"]),
                newsFilters=strategy_data["stockPicking"].get("newsFilters"),
                technicalFilters=strategy_data["stockPicking"].get("technicalFilters"),
                allowedSymbols=strategy_data["stockPicking"].get("allowedSymbols"),
                excludedSymbols=strategy_data["stockPicking"].get("excludedSymbols", []),
                maxStocks=strategy_data["stockPicking"].get("maxStocks", 5)
            )

            execution = ExecutionConfig(
                type=ExecutionType(strategy_data["execution"]["type"]),
                entryCondition=strategy_data["execution"].get("entryCondition", "AI determined"),
                stopLossPercent=strategy_data["execution"].get("stopLossPercent", 2.0),
                takeProfitPercent=strategy_data["execution"].get("takeProfitPercent", 5.0),
                useTrailingStop=strategy_data["execution"].get("useTrailingStop", False),
                trailingStopPercent=strategy_data["execution"].get("trailingStopPercent", 1.5),
                useMultipleTargets=strategy_data["execution"].get("useMultipleTargets", True),
                target1Percent=strategy_data["execution"].get("target1Percent", 3.0),
                target2Percent=strategy_data["execution"].get("target2Percent", 5.0),
                exitAtEOD=strategy_data["execution"].get("exitAtEOD", True),
                eodExitTime=strategy_data["execution"].get("eodExitTime", "15:15"),
                useAILevels=strategy_data["execution"].get("useAILevels", True)
            )

            risk = RiskManagementConfig(
                maxPositionPercent=strategy_data["riskManagement"].get("maxPositionPercent", 20),
                maxDailyLoss=strategy_data["riskManagement"].get("maxDailyLoss", 5),
                maxDrawdown=strategy_data["riskManagement"].get("maxDrawdown", 10)
            )

            strategy_model = StrategyModel(
                strategyId=strategy_data["strategyId"],
                name=strategy_data["name"],
                description=strategy_data["description"],
                version="1.0",
                status=StrategyStatus.PAUSED,
                stockPicking=stock_picking,
                execution=execution,
                riskManagement=risk,
                createdBy="ai_creator"
            )

            saved = await manager.create_strategy(strategy_model)
            result["savedToDatabase"] = saved is not None

        return result

    except Exception as e:
        logger.error(f"Error creating strategy from description: {e}")
        return {"error": str(e)}


@app.post("/api/strategies/{strategy_id}/refine")
async def refine_strategy(strategy_id: str, request: dict):
    """
    Refine an existing strategy based on user feedback.

    Request body:
    {
        "refinement": "Make the stop loss tighter at 1.5% and add a trailing stop"
    }
    """
    try:
        from strategy_creator import strategy_creator

        refinement = request.get("refinement")

        if not refinement:
            return {"error": "Missing required field: refinement"}

        result = await strategy_creator.refine_strategy(
            strategy_id=strategy_id,
            refinement_request=refinement
        )

        return result

    except Exception as e:
        logger.error(f"Error refining strategy: {e}")
        return {"error": str(e)}


@app.post("/signals/generate")
async def generate_signal(request: dict):
    """Manually generate a trade signal for a specific symbol."""
    try:
        symbol = request.get("symbol")
        strategy_id = request.get("strategyId")

        if not symbol:
            return {"error": "Symbol is required"}

        from strategy_engine import StrategyEngine
        from strategy_manager import StrategyManager
        from ai_trade_assistant import AITradeAssistant
        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.DATABASE_NAME]

        strategy_manager = StrategyManager(db_collection=db.strategies)
        await strategy_manager.load_strategies()

        ai_assistant = AITradeAssistant()

        strategy_engine = StrategyEngine(
            strategy_manager=strategy_manager,
            news_aggregator=news_aggregator,
            broker=broker,
            ai_assistant=ai_assistant
        )

        signal = await strategy_engine.generate_manual_signal(symbol, strategy_id)

        if not signal:
            client.close()
            return {"error": "Failed to generate signal"}

        # Fetch full news articles if we have article IDs
        news_context = []
        if signal.newsArticles:
            all_news = await news_aggregator.get_news_with_analysis()
            # all_news is a List[Dict], not a dict with 'articles' key
            news_dict = {article['id']: article for article in all_news}
            news_context = [news_dict[article_id] for article_id in signal.newsArticles if article_id in news_dict]

        client.close()

        return {
            "signal": {
                "symbol": signal.symbol,
                "direction": signal.direction.value,
                "strategyId": signal.strategyId,
                "strategyName": signal.strategyName,
                "entryPrice": signal.entryPrice,
                "stopLoss": signal.stopLoss,
                "target1": signal.target1,
                "target2": signal.target2,
                "confidence": signal.confidence,
                "reasoning": signal.reasoning,
                "newsContext": news_context,
                "aiAnalysis": signal.aiAnalysis
            }
        }
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        return {"error": str(e)}


@app.post("/api/signals/generate")
async def generate_api_signal(request: dict):
    """Manually generate a trade signal (API version)."""
    return await generate_signal(request)


# ============================================
# RISK MANAGEMENT ENDPOINTS
# ============================================

@app.get("/risk/metrics")
async def get_risk_metrics():
    """Get current risk metrics."""
    try:
        if not trading_bot.risk_manager:
            return {"error": "Risk manager not initialized"}

        # Get trades for metrics calculation
        trades = await trade_logger.get_recent_trades(limit=100)

        # Calculate metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) < 0]

        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        avg_win = sum(t.get("pnl", 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.get("pnl", 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0

        # Get drawdown from risk manager
        current_drawdown = trading_bot.risk_manager.current_drawdown if hasattr(trading_bot.risk_manager, 'current_drawdown') else 0
        max_drawdown = trading_bot.risk_manager.max_drawdown if hasattr(trading_bot.risk_manager, 'max_drawdown') else 0

        # Calculate Sharpe ratio (simplified)
        returns = [t.get("pnl", 0) for t in trades]
        avg_return = sum(returns) / len(returns) if returns else 0
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 1
        sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0

        return {
            "maxDrawdown": max_drawdown,
            "currentDrawdown": current_drawdown,
            "sharpeRatio": sharpe_ratio,
            "winRate": win_rate,
            "avgWin": avg_win,
            "avgLoss": avg_loss,
            "totalTrades": total_trades
        }
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        return {"error": str(e)}


@app.put("/risk/limits")
async def update_risk_limits(limits: dict):
    """Update risk management limits."""
    try:
        if not trading_bot.risk_manager:
            return {"error": "Risk manager not initialized"}

        # Update limits
        if "maxDrawdown" in limits:
            trading_bot.risk_manager.max_drawdown_limit = limits["maxDrawdown"]

        if "maxDailyLoss" in limits:
            trading_bot.risk_manager.max_daily_loss = limits["maxDailyLoss"]

        if "maxPositionSize" in limits:
            trading_bot.risk_manager.max_position_size = limits["maxPositionSize"]

        return {"success": True, "message": "Risk limits updated successfully"}
    except Exception as e:
        logger.error(f"Error updating risk limits: {e}")
        return {"error": str(e)}


# ============================================
# AI INSIGHTS ENDPOINT
# ============================================

@app.get("/ai/insights")
async def get_ai_insights():
    """Get AI-generated trading insights and recommendations."""
    try:
        if not trading_bot.ai_engine:
            return {"error": "AI engine not initialized", "insights": []}

        insights = []

        # Get screened stocks
        if trading_bot.screener:
            stocks = await trading_bot.screener.screen_stocks()

            # Get AI analysis for top 3 stocks
            for stock in stocks[:3]:
                try:
                    # Get sentiment data
                    sentiment_data = {}
                    if trading_bot.sentiment_analyzer:
                        sentiment_data = await trading_bot.sentiment_analyzer.analyze_sentiment(stock["symbol"])

                    # Get AI decision
                    decision = await trading_bot.ai_engine.make_trading_decision(stock, sentiment_data)

                    insights.append({
                        "symbol": stock["symbol"],
                        "recommendation": decision.get("decision", "HOLD"),
                        "confidence": decision.get("confidence", 0),
                        "reasoning": decision.get("reasoning", ""),
                        "entryPrice": decision.get("entry_price", 0),
                        "targetPrice": decision.get("target_price", 0),
                        "stopLoss": decision.get("stop_loss", 0),
                        "riskRewardRatio": decision.get("risk_reward_ratio", 0),
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Error getting AI insight for {stock['symbol']}: {e}")

        return {"insights": insights, "count": len(insights)}
    except Exception as e:
        logger.error(f"Error getting AI insights: {e}")
        return {"error": str(e), "insights": []}


# ============================================
# BACKTESTING ENDPOINTS
# ============================================

@app.post("/api/backtest/run")
async def run_backtest(request: dict):
    """
    Run a backtest for a strategy.

    Request body:
    {
        "strategyId": "news_momentum_v1",
        "startDate": "2024-01-01",
        "endDate": "2024-11-01",
        "initialCapital": 100000,
        "symbols": ["RELIANCE", "TCS", "INFY"]  // optional
    }
    """
    try:
        from backtester import Backtester
        from motor.motor_asyncio import AsyncIOMotorClient

        strategy_id = request.get("strategyId")
        start_date = request.get("startDate")
        end_date = request.get("endDate")
        initial_capital = request.get("initialCapital", 100000)
        symbols = request.get("symbols")

        if not strategy_id or not start_date or not end_date:
            return {"error": "Missing required fields: strategyId, startDate, endDate"}

        # Connect to MongoDB for strategy loading
        mongo_client = AsyncIOMotorClient(config.MONGODB_URL)
        db = mongo_client[config.DATABASE_NAME]

        backtester = Backtester(
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            db_collection=db.strategies
        )

        result = await backtester.run(symbols=symbols)

        # Close MongoDB connection
        mongo_client.close()

        return {
            "success": True,
            "result": {
                "strategyId": result.strategyId,
                "strategyName": result.strategyName,
                "startDate": result.startDate,
                "endDate": result.endDate,
                "initialCapital": result.initialCapital,
                "finalCapital": result.finalCapital,
                "totalPnl": result.totalPnl,
                "totalPnlPercent": result.totalPnlPercent,
                "totalTrades": result.totalTrades,
                "winningTrades": result.winningTrades,
                "losingTrades": result.losingTrades,
                "winRate": result.winRate,
                "avgWin": result.avgWin,
                "avgLoss": result.avgLoss,
                "maxDrawdown": result.maxDrawdown,
                "maxDrawdownPercent": result.maxDrawdownPercent,
                "sharpeRatio": result.sharpeRatio,
                "profitFactor": result.profitFactor,
                "trades": [
                    {
                        "symbol": t.symbol,
                        "direction": t.direction.value,
                        "entryDate": t.entryDate,
                        "entryPrice": t.entryPrice,
                        "exitDate": t.exitDate,
                        "exitPrice": t.exitPrice,
                        "quantity": t.quantity,
                        "pnl": t.pnl,
                        "pnlPercent": t.pnlPercent,
                        "exitReason": t.exitReason
                    }
                    for t in result.trades[:50]  # Limit to 50 trades in response
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        return {"error": str(e)}


# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@app.get("/health")
async def health_check():
    """System health check endpoint."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }

        # Check broker connection
        try:
            if broker.is_connected:
                health_status["components"]["broker"] = "healthy"
            else:
                health_status["components"]["broker"] = "disconnected"
                health_status["status"] = "warning"
        except:
            health_status["components"]["broker"] = "error"
            health_status["status"] = "error"

        # Check database connection
        try:
            if trade_logger.db is not None:
                health_status["components"]["database"] = "healthy"
            else:
                health_status["components"]["database"] = "disconnected"
                health_status["status"] = "warning"
        except Exception as db_error:
            logger.error(f"Database health check error: {db_error}")
            health_status["components"]["database"] = "error"
            health_status["status"] = "error"

        # Check AI engine
        try:
            if trading_bot.ai_engine:
                health_status["components"]["ai_engine"] = "healthy"
            else:
                health_status["components"]["ai_engine"] = "not_initialized"
                health_status["status"] = "warning"
        except:
            health_status["components"]["ai_engine"] = "error"
            health_status["status"] = "warning"

        # Check screener
        try:
            if trading_bot.screener:
                health_status["components"]["screener"] = "healthy"
            else:
                health_status["components"]["screener"] = "not_initialized"
        except:
            health_status["components"]["screener"] = "error"

        # Check sentiment analyzer
        try:
            if trading_bot.sentiment_analyzer:
                health_status["components"]["sentiment"] = "healthy"
            else:
                health_status["components"]["sentiment"] = "not_initialized"
        except:
            health_status["components"]["sentiment"] = "error"

        # Bot status
        health_status["components"]["bot"] = "running" if trading_bot.is_running else "stopped"

        return health_status
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================
# EMERGENCY & CIRCUIT BREAKER ENDPOINTS
# ============================================

@app.post("/api/emergency/kill-switch")
async def emergency_kill_switch():
    """
    EMERGENCY KILL SWITCH - Immediately closes all positions and halts trading.
    Use this if something goes wrong!
    """
    logger.error("🚨 EMERGENCY KILL SWITCH ACTIVATED!")

    try:
        # Halt trading immediately
        trading_circuit_breaker.halt_trading("Emergency kill switch activated by user")

        # Close all positions
        closed_count = 0
        failed_count = 0

        try:
            positions = await broker.get_positions()
            for position in positions:
                try:
                    success = await broker.close_position(position.symbol)
                    if success:
                        closed_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to close {position.symbol}: {e}")
                    failed_count += 1
        except Exception as e:
            logger.error(f"Error getting positions: {e}")

        # Stop the trading bot
        if trading_bot.is_running:
            await trading_bot.shutdown()

        return {
            "success": True,
            "message": "Emergency kill switch activated",
            "positions_closed": closed_count,
            "positions_failed": failed_count,
            "trading_halted": True,
            "bot_stopped": True
        }
    except Exception as e:
        logger.error(f"Error in kill switch: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/circuit-breaker/status")
async def get_circuit_breaker_status():
    """Get the current trading circuit breaker status."""
    return trading_circuit_breaker.get_status()


@app.post("/api/circuit-breaker/reset")
async def reset_circuit_breaker():
    """Reset the trading circuit breaker. Use with caution!"""
    trading_circuit_breaker.force_resume()
    return {
        "success": True,
        "message": "Circuit breaker reset",
        "status": trading_circuit_breaker.get_status()
    }


# ============================================
# FYERS AUTH ENDPOINTS
# ============================================

@app.get("/api/auth/token-status")
async def get_token_status():
    """Get Fyers access token status."""
    return fyers_auth.get_token_info()


@app.get("/api/auth/login-url")
async def get_fyers_login_url():
    """Get the Fyers OAuth login URL."""
    auth_url = fyers_auth.get_auth_url()
    return {
        "auth_url": auth_url,
        "instructions": "Visit this URL to login to Fyers. After login, copy the auth_code from the redirect URL and use /api/auth/set-token endpoint."
    }


@app.post("/api/auth/set-token")
async def set_fyers_token(data: dict):
    """
    Exchange auth_code for access_token.

    Body: {"auth_code": "your_auth_code_here"}
    """
    auth_code = data.get("auth_code")
    if not auth_code:
        return {"success": False, "error": "auth_code is required"}

    token, error = await fyers_auth.exchange_auth_code(auth_code)

    if token:
        return {
            "success": True,
            "message": "Token generated successfully",
            "token_info": fyers_auth.get_token_info(token),
            "note": "Update FYERS_ACCESS_TOKEN in .env file with the new token and restart the server"
        }
    else:
        return {
            "success": False,
            "error": error
        }


@app.post("/api/auth/refresh")
async def refresh_fyers_token():
    """
    Attempt to refresh the Fyers access token.
    Uses TOTP auto-login if configured, otherwise returns instructions.
    """
    # Check current status
    is_valid, reason = fyers_auth.is_token_valid()

    if is_valid and "expiring soon" not in reason.lower():
        return {
            "success": True,
            "message": "Token is still valid, no refresh needed",
            "token_info": fyers_auth.get_token_info()
        }

    # Try to refresh
    if fyers_auth.totp_enabled:
        access_token, error = await fyers_auth.auto_login()
        if access_token:
            # Update config and reinitialize broker
            config.FYERS_ACCESS_TOKEN = access_token
            try:
                await broker.initialize()
                logger.info("✅ Broker reinitialized with new token")
            except Exception as e:
                logger.warning(f"⚠️ Broker reinit warning: {e}")

            return {
                "success": True,
                "message": "Token refreshed successfully via TOTP auto-login. Broker reinitialized.",
                "token_info": fyers_auth.get_token_info(access_token)
            }
        else:
            return {
                "success": False,
                "error": error,
                "fallback": "Use /api/auth/login-url to login manually"
            }
    else:
        auth_url = fyers_auth.get_auth_url()
        return {
            "success": False,
            "error": "TOTP auto-login not configured",
            "instructions": "Either configure FYERS_TOTP_SECRET and FYERS_PIN in .env, or login manually",
            "auth_url": auth_url
        }


@app.get("/api/auth/auto-login-status")
async def get_auto_login_status():
    """Check if TOTP auto-login is configured."""
    return {
        "totp_enabled": fyers_auth.totp_enabled,
        "pyotp_available": True,  # We added pyotp
        "totp_secret_configured": bool(fyers_auth.totp_secret),
        "pin_configured": bool(fyers_auth.pin),
        "instructions": "To enable auto-login, set FYERS_TOTP_SECRET and FYERS_PIN in .env file"
    }


async def main():
    """Main entry point for the trading bot."""
    try:
        # Start the trading bot
        await trading_bot.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await trading_bot.shutdown()


def run_web_server():
    """Run the FastAPI web server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )


# ============================================
# BACKTESTING ENDPOINTS
@app.get("/api/backtest/strategies")
async def get_backtest_strategies():
    """Get available strategies for backtesting."""
    try:
        from strategy_manager import StrategyManager
        from motor.motor_asyncio import AsyncIOMotorClient

        # Connect to MongoDB
        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.DATABASE_NAME]

        manager = StrategyManager(db_collection=db.strategies)
        await manager.load_strategies()

        # Get all strategies from the manager's cache
        strategies = list(manager.strategies.values())

        client.close()

        return {
            "strategies": [
                {
                    "id": s.strategyId,
                    "name": s.name,
                    "description": s.description,
                    "stockPickingType": s.stockPicking.type.value if s.stockPicking else None,
                    "executionType": s.execution.type if s.execution else None,
                }
                for s in strategies
            ]
        }
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return {"strategies": [], "error": str(e)}


# ============================================
# AI SUGGESTIONS ENDPOINTS
# ============================================

# Cache for AI suggestions to prevent repeated API calls
_suggestions_cache: Dict[str, Dict] = {}
_suggestions_cache_expiry: Dict[str, float] = {}
SUGGESTIONS_CACHE_TTL = 300  # 5 minutes cache


@app.get("/api/ai/suggestions")
async def get_ai_suggestions(symbols: str = "RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK"):
    """Get AI-generated trading suggestions for multiple symbols (cached 5 min)."""
    import time as time_module

    # Check cache first
    cache_key = symbols
    now = time_module.time()

    if cache_key in _suggestions_cache and cache_key in _suggestions_cache_expiry:
        if now < _suggestions_cache_expiry[cache_key]:
            logger.debug(f"📦 Using cached AI suggestions")
            return _suggestions_cache[cache_key]

    try:
        from ai_trade_assistant import AITradeAssistant
        from news_aggregator import NewsAggregator
        from models import TradeDirection, ExecutionConfig

        symbol_list = [s.strip() for s in symbols.split(",")]
        suggestions = []

        # Initialize AI assistant and news aggregator
        ai_assistant = AITradeAssistant()
        news_aggregator = NewsAggregator()

        # Get news context (await the async function)
        all_news = await news_aggregator.get_news_with_analysis()

        # Default execution config for AI suggestions
        default_execution = ExecutionConfig(
            type="AI_ASSISTED",
            entryCondition="AI-suggested entry price",
            stopLossPercent=2.0,
            takeProfitPercent=5.0,
            useTrailingStop=False,
            useMultipleTargets=True,
            target1Percent=3.0,
            target2Percent=5.0,
            exitAtEOD=True,
            eodExitTime="15:15",
            useAILevels=True
        )

        for symbol in symbol_list[:5]:  # Limit to 5 symbols
            try:
                # Get current price for the symbol
                quote = await get_stock_quote(symbol)
                current_price = quote.get('price', 1000)

                # Filter news for this symbol
                symbol_news = [n for n in all_news if symbol.lower() in n.get('title', '').lower()
                              or symbol.lower() in n.get('summary', '').lower()][:3]

                # Generate AI levels directly (default to BUY direction)
                levels = await ai_assistant.suggest_levels(
                    symbol=symbol,
                    current_price=current_price,
                    direction=TradeDirection.BUY,
                    news_context=symbol_news,
                    execution_config=default_execution
                )

                if levels:
                    # Calculate risk-reward ratio
                    entry = levels.get('entryPrice', current_price)
                    sl = levels.get('stopLoss', entry * 0.98)
                    t1 = levels.get('target1', entry * 1.03)
                    risk = abs(entry - sl)
                    reward = abs(t1 - entry)
                    rr_ratio = reward / risk if risk > 0 else 0

                    suggestions.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "confidence": levels.get('confidence', 70),
                        "entryPrice": entry,
                        "stopLoss": sl,
                        "target1": t1,
                        "target2": levels.get('target2'),
                        "reasoning": levels.get('reasoning', f"AI analysis for {symbol}"),
                        "riskReward": round(rr_ratio, 2),
                    })
            except Exception as e:
                logger.warning(f"Error generating suggestion for {symbol}: {e}")
                continue

        result = {"suggestions": suggestions, "generatedAt": datetime.now().isoformat()}

        # Cache the result
        _suggestions_cache[cache_key] = result
        _suggestions_cache_expiry[cache_key] = now + SUGGESTIONS_CACHE_TTL

        return result

    except Exception as e:
        logger.error(f"Error getting AI suggestions: {e}")
        return {"suggestions": [], "error": str(e)}


@app.post("/api/ai/analyze")
async def analyze_stock(request: dict):
    """Get detailed AI analysis for a specific stock."""
    try:
        symbol = request.get("symbol", "RELIANCE")

        # Generate full signal with analysis
        result = await generate_signal({"symbol": symbol})

        if "error" in result:
            return result

        signal = result.get("signal", {})

        return {
            "symbol": symbol,
            "analysis": {
                "recommendation": signal.get("direction", "HOLD"),
                "confidence": signal.get("confidence", 0),
                "entryPrice": signal.get("entryPrice", 0),
                "stopLoss": signal.get("stopLoss", 0),
                "targets": [signal.get("target1"), signal.get("target2")],
                "reasoning": signal.get("reasoning", ""),
                "newsContext": signal.get("newsContext", []),
                "riskReward": signal.get("aiAnalysis", {}).get("riskRewardRatio", 0),
                "expectedMove": signal.get("aiAnalysis", {}).get("expectedMove", "0%"),
            },
            "generatedAt": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error analyzing stock: {e}")
        return {"error": str(e)}


# ============================================
# PAPER TRADING ENDPOINTS
# ============================================

@app.get("/api/trading/mode")
async def get_trading_mode():
    """Get current trading mode (paper/live)."""
    return {
        "mode": "paper" if config.MOCK_MODE else "live",
        "mockMode": config.MOCK_MODE,
        "mockBroker": config.MOCK_BROKER,
        "brokerConnected": broker.is_connected if broker else False,
    }


@app.post("/api/trading/mode")
async def set_trading_mode(request: dict):
    """Switch between paper and live trading mode."""
    mode = request.get("mode", "paper")

    if mode == "live" and config.MOCK_MODE:
        return {
            "success": False,
            "error": "Cannot switch to live mode. Set MOCK_MODE=false in .env and restart.",
            "currentMode": "paper"
        }

    return {
        "success": True,
        "mode": "paper" if config.MOCK_MODE else "live",
        "message": f"Trading in {'paper' if config.MOCK_MODE else 'live'} mode"
    }


# ============================================
# SETTINGS ENDPOINTS
# ============================================

@app.get("/api/settings")
async def get_settings():
    """Get current application settings."""
    return {
        "trading": {
            "initialCapital": config.INITIAL_CAPITAL,
            "maxCapitalPerTrade": config.MAX_CAPITAL_PER_TRADE * 100,  # Convert to percentage
            "maxActiveTrades": config.MAX_ACTIVE_TRADES,
            "maxDailyLosses": config.MAX_DAILY_LOSSES,
            "maxDailyDrawdown": config.MAX_DAILY_DRAWDOWN * 100,  # Convert to percentage
            "minRiskRewardRatio": config.MIN_RISK_REWARD_RATIO,
            "aiConfidenceThreshold": config.AI_CONFIDENCE_THRESHOLD * 100,  # Convert to percentage
        },
        "marketHours": {
            "tradingStart": config.TRADING_HOURS_START,
            "tradingEnd": config.TRADING_HOURS_END,
            "forceExitTime": config.FORCE_EXIT_TIME,
        },
        "broker": {
            "connected": broker.is_connected if broker else False,
            "mode": "paper" if config.MOCK_MODE else "live",
            "provider": "Fyers",
            "hasApiKey": bool(config.FYERS_APP_ID),
        },
        "ai": {
            "provider": config.AI_PROVIDER,
            "model": config.GROQ_MODEL if config.AI_PROVIDER == "groq" else config.GEMINI_MODEL,
            "hasApiKey": bool(config.GROQ_API_KEY) if config.AI_PROVIDER == "groq" else bool(config.GEMINI_API_KEY),
        },
        "notifications": {
            "telegramEnabled": bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID),
            "hasTelegramToken": bool(config.TELEGRAM_BOT_TOKEN),
        },
        "database": {
            "connected": trade_logger.db is not None if trade_logger else False,
            "url": config.MONGODB_URL.split("@")[-1] if "@" in config.MONGODB_URL else config.MONGODB_URL,  # Hide credentials
        }
    }


@app.get("/api/settings/api-status")
async def get_api_status():
    """Get status of all API connections."""
    return {
        "broker": {
            "name": "Fyers",
            "connected": broker.is_connected if broker else False,
            "mode": "paper" if config.MOCK_MODE else "live",
        },
        "ai": {
            "name": config.AI_PROVIDER.upper(),
            "connected": bool(config.GROQ_API_KEY) if config.AI_PROVIDER == "groq" else bool(config.GEMINI_API_KEY),
            "model": config.GROQ_MODEL if config.AI_PROVIDER == "groq" else config.GEMINI_MODEL,
        },
        "database": {
            "name": "MongoDB",
            "connected": trade_logger.db is not None if trade_logger else False,
        },
        "telegram": {
            "name": "Telegram",
            "connected": bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID),
        },
        "news": {
            "name": "News Aggregator",
            "connected": True,  # Always available
            "sources": config.NEWS_SOURCES.split(","),
        }
    }


# ============================================
# ALERTS ENDPOINTS
# ============================================

# In-memory alerts store (would be MongoDB in production)
alerts_store: List[Dict] = []


@app.get("/api/alerts")
async def get_alerts():
    """Get all alerts for the user."""
    try:
        if trade_logger is not None and trade_logger.db is not None:
            alerts_collection = trade_logger.db["alerts"]
            cursor = alerts_collection.find({}).sort("created_at", -1)
            alerts = await cursor.to_list(length=100)
            # Convert ObjectId to string
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
            return {"alerts": alerts}
        return {"alerts": alerts_store}
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return {"error": str(e), "alerts": []}


@app.post("/api/alerts")
async def create_alert(request: dict):
    """
    Create a new price/condition alert.

    Request body:
    {
        "symbol": "RELIANCE",
        "type": "price_above" | "price_below" | "percent_change" | "volume_spike",
        "condition": {
            "value": 2500,  # Price level or percentage
            "comparison": "above" | "below" | "crosses"
        },
        "enabled": true,
        "notification": {
            "push": true,
            "telegram": false,
            "sound": true
        }
    }
    """
    try:
        alert = {
            "id": f"ALT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(alerts_store)}",
            "symbol": request.get("symbol", ""),
            "type": request.get("type", "price_above"),
            "condition": request.get("condition", {}),
            "enabled": request.get("enabled", True),
            "notification": request.get("notification", {"push": True, "telegram": False, "sound": True}),
            "triggered": False,
            "triggered_at": None,
            "created_at": datetime.now().isoformat(),
        }

        if trade_logger is not None and trade_logger.db is not None:
            alerts_collection = trade_logger.db["alerts"]
            result = await alerts_collection.insert_one(alert)
            alert["_id"] = str(result.inserted_id)
        else:
            alerts_store.append(alert)

        return {"success": True, "alert": alert}
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return {"error": str(e), "success": False}


@app.put("/api/alerts/{alert_id}")
async def update_alert(alert_id: str, request: dict):
    """Update an existing alert."""
    try:
        if trade_logger is not None and trade_logger.db is not None:
            from bson import ObjectId
            alerts_collection = trade_logger.db["alerts"]
            update_data = {k: v for k, v in request.items() if k != "_id"}
            result = await alerts_collection.update_one(
                {"_id": ObjectId(alert_id)},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                return {"success": True, "message": "Alert updated"}
            return {"success": False, "message": "Alert not found"}
        else:
            for alert in alerts_store:
                if alert["id"] == alert_id:
                    alert.update(request)
                    return {"success": True, "alert": alert}
            return {"success": False, "message": "Alert not found"}
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        return {"error": str(e), "success": False}


@app.delete("/api/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert."""
    try:
        if trade_logger is not None and trade_logger.db is not None:
            from bson import ObjectId
            alerts_collection = trade_logger.db["alerts"]
            result = await alerts_collection.delete_one({"_id": ObjectId(alert_id)})
            if result.deleted_count > 0:
                return {"success": True, "message": "Alert deleted"}
            return {"success": False, "message": "Alert not found"}
        else:
            global alerts_store
            alerts_store = [a for a in alerts_store if a["id"] != alert_id]
            return {"success": True, "message": "Alert deleted"}
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        return {"error": str(e), "success": False}


@app.post("/api/alerts/{alert_id}/toggle")
async def toggle_alert(alert_id: str):
    """Toggle an alert on/off."""
    try:
        if trade_logger is not None and trade_logger.db is not None:
            from bson import ObjectId
            alerts_collection = trade_logger.db["alerts"]
            alert = await alerts_collection.find_one({"_id": ObjectId(alert_id)})
            if alert:
                new_enabled = not alert.get("enabled", True)
                await alerts_collection.update_one(
                    {"_id": ObjectId(alert_id)},
                    {"$set": {"enabled": new_enabled}}
                )
                return {"success": True, "enabled": new_enabled}
            return {"success": False, "message": "Alert not found"}
        else:
            for alert in alerts_store:
                if alert["id"] == alert_id:
                    alert["enabled"] = not alert.get("enabled", True)
                    return {"success": True, "enabled": alert["enabled"]}
            return {"success": False, "message": "Alert not found"}
    except Exception as e:
        logger.error(f"Error toggling alert: {e}")
        return {"error": str(e), "success": False}


@app.get("/api/alerts/check")
async def check_alerts():
    """Check all alerts against current prices and trigger if conditions met."""
    try:
        triggered_alerts = []
        alerts = []

        if trade_logger is not None and trade_logger.db is not None:
            alerts_collection = trade_logger.db["alerts"]
            cursor = alerts_collection.find({"enabled": True, "triggered": False})
            alerts = await cursor.to_list(length=100)
        else:
            alerts = [a for a in alerts_store if a.get("enabled") and not a.get("triggered")]

        for alert in alerts:
            symbol = alert.get("symbol")
            alert_type = alert.get("type")
            condition = alert.get("condition", {})

            # Get current price
            try:
                quote = broker.get_quote(symbol)
                current_price = quote.get("ltp", 0)

                should_trigger = False

                if alert_type == "price_above":
                    should_trigger = current_price >= condition.get("value", 0)
                elif alert_type == "price_below":
                    should_trigger = current_price <= condition.get("value", 0)
                elif alert_type == "percent_change":
                    change_pct = quote.get("change_pct", 0)
                    threshold = condition.get("value", 0)
                    if condition.get("comparison") == "above":
                        should_trigger = change_pct >= threshold
                    else:
                        should_trigger = change_pct <= -threshold

                if should_trigger:
                    alert["triggered"] = True
                    alert["triggered_at"] = datetime.now().isoformat()
                    alert["trigger_price"] = current_price

                    if trade_logger is not None and trade_logger.db is not None:
                        from bson import ObjectId
                        alerts_collection = trade_logger.db["alerts"]
                        await alerts_collection.update_one(
                            {"_id": alert["_id"]},
                            {"$set": {"triggered": True, "triggered_at": alert["triggered_at"], "trigger_price": current_price}}
                        )

                    triggered_alerts.append({
                        "symbol": symbol,
                        "type": alert_type,
                        "price": current_price,
                        "condition": condition,
                        "message": f"{symbol} alert triggered: {alert_type} at ₹{current_price:.2f}"
                    })

                    # Send Telegram notification if enabled
                    if alert.get("notification", {}).get("telegram"):
                        try:
                            async with notifier:
                                await notifier.send_message(
                                    f"🔔 **Price Alert**\n\n"
                                    f"Symbol: {symbol}\n"
                                    f"Type: {alert_type}\n"
                                    f"Price: ₹{current_price:.2f}\n"
                                    f"Condition: {condition}"
                                )
                        except Exception as e:
                            logger.error(f"Error sending Telegram alert: {e}")

            except Exception as e:
                logger.error(f"Error checking alert for {symbol}: {e}")

        return {"triggered": triggered_alerts, "count": len(triggered_alerts)}
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        return {"error": str(e), "triggered": []}


# ============================================
# PIPELINE API ENDPOINTS (3-Stage Architecture)
# ============================================

# Global pipeline orchestrator instance
pipeline_orchestrator: Optional[PipelineOrchestrator] = None


@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """Get current pipeline status and metrics."""
    global pipeline_orchestrator

    if not pipeline_orchestrator:
        return {
            "state": "STOPPED",
            "is_running": False,
            "current_cycle": 0,
            "last_screening_time": None,
            "last_execution_time": None,
            "next_screening_time": None,
            "market_status": "CLOSED",
            "metrics": {
                "total_screenings": 0,
                "total_analyses": 0,
                "total_executions": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "total_pnl": 0,
                "open_positions": 0,
                "open_risk_percent": 0,
                "daily_loss_percent": 0,
                "trades_today": 0
            }
        }

    return pipeline_orchestrator.get_status()


@app.post("/api/pipeline/start")
async def start_pipeline():
    """Start the trading pipeline."""
    global pipeline_orchestrator

    try:
        if not pipeline_orchestrator:
            pipeline_orchestrator = PipelineOrchestrator()

        await pipeline_orchestrator.start()
        return {"success": True, "message": "Pipeline started successfully"}
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        return {"success": False, "message": str(e)}


@app.post("/api/pipeline/stop")
async def stop_pipeline():
    """Stop the trading pipeline."""
    global pipeline_orchestrator

    try:
        if pipeline_orchestrator:
            await pipeline_orchestrator.stop()
        return {"success": True, "message": "Pipeline stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop pipeline: {e}")
        return {"success": False, "message": str(e)}


@app.post("/api/pipeline/screen")
async def trigger_screening():
    """Manually trigger a screening cycle."""
    global pipeline_orchestrator

    try:
        # Auto-initialize pipeline if not already done
        if not pipeline_orchestrator:
            logger.info("Auto-initializing pipeline orchestrator for manual screening...")
            pipeline_orchestrator = PipelineOrchestrator()

        # Run screening cycle and return results
        result = await pipeline_orchestrator.run_screening_cycle()
        if result:
            return {
                "success": True,
                "message": "Screening completed",
                "candidates_count": len(result.candidates) if result.candidates else 0
            }
        return {"success": True, "message": "Screening completed, no candidates found"}
    except Exception as e:
        logger.error(f"Failed to trigger screening: {e}")
        return {"success": False, "message": str(e)}


@app.get("/api/screener/results")
async def get_screener_results():
    """Get the latest screener results."""
    global pipeline_orchestrator

    try:
        if pipeline_orchestrator and pipeline_orchestrator.latest_screener_output:
            output = pipeline_orchestrator.latest_screener_output
            # Get VIX level from MarketContext (attribute is 'vix' not 'vix_level')
            vix_value = output.market_context.vix if output.market_context else 15.0
            # Determine VIX status based on value
            vix_status = "LOW" if vix_value < 15 else ("HIGH" if vix_value > 25 else "NORMAL")
            return {
                "timestamp": output.timestamp.isoformat() if output.timestamp else None,
                "market_context": {
                    "nifty_trend": output.market_context.nifty_trend if output.market_context else "SIDEWAYS",
                    "nifty_change_pct": output.market_context.nifty_change_pct if output.market_context else 0.0,
                    "market_breadth": output.market_context.market_breadth if output.market_context else "neutral",
                    "vix_level": vix_value,
                    "vix_status": vix_status,
                    "market_status": "OPEN" if output.market_context else "CLOSED"
                },
                "candidates": [
                    {
                        "symbol": c.symbol,
                        "name": c.name,
                        "current_price": c.price_action.last_price if c.price_action else 0,
                        "change_percent": c.price_action.today_pct_change if c.price_action else 0,
                        "screening_score": c.score,
                        "relative_volume": c.liquidity.rvol if c.liquidity else 1.0,
                        "turnover_cr": c.liquidity.today_turnover_cr if c.liquidity else 0,
                        "atr_percent": c.technicals.atr_pct if c.technicals else 0,
                        "rsi": c.technicals.rsi if c.technicals else 50,
                        "gap_percent": c.price_action.gap_pct if c.price_action else 0,
                        "vwap_distance_percent": c.price_action.vwap_distance_pct if c.price_action else 0,
                        "market_cap_cr": c.market_cap_cr,
                        "trend": c.technicals.trend_label if c.technicals else "sideways",
                        "news_context": {
                            "has_news": c.news.has_fresh_news if c.news else False,
                            "sentiment": c.news.sentiment if c.news else "neutral",
                            "summary": c.news.summary if c.news else None
                        }
                    }
                    for c in output.candidates
                ],
                "total_scanned": output.total_scanned,
                "passed_filters": output.passed_filters
            }

        # Return empty results if no screening has been done
        return {
            "timestamp": None,
            "market_context": {
                "nifty_trend": "SIDEWAYS",
                "vix_level": 15,
                "vix_status": "NORMAL",
                "market_status": "CLOSED"
            },
            "candidates": [],
            "total_scanned": 0,
            "filters_applied": []
        }
    except Exception as e:
        logger.error(f"Error getting screener results: {e}")
        return {"error": str(e), "candidates": []}


@app.get("/api/trade-plans")
async def get_trade_plans():
    """Get current trade plans."""
    global pipeline_orchestrator

    try:
        if pipeline_orchestrator and pipeline_orchestrator.latest_trade_plans and pipeline_orchestrator.latest_trade_plans.plans:
            plans = []
            for plan in pipeline_orchestrator.latest_trade_plans.plans:
                plans.append({
                    "symbol": plan.symbol,
                    "direction": plan.direction,
                    "confidence": plan.confidence,
                    "levels": {
                        "entry": plan.levels.entry,
                        "stop_loss": plan.levels.stop_loss,
                        "target_1": plan.levels.target_1,
                        "target_2": plan.levels.target_2,
                        "risk_reward_ratio": plan.levels.risk_reward_ratio
                    },
                    "rationale": {
                        "setup_type": plan.rationale.setup_type if plan.rationale else "",
                        "key_levels": plan.rationale.key_levels if plan.rationale else [],
                        "catalysts": plan.rationale.catalysts if plan.rationale else [],
                        "risks": plan.rationale.risks if plan.rationale else [],
                        "summary": plan.rationale.summary if plan.rationale else ""
                    },
                    "generated_at": plan.timestamp.isoformat() if plan.timestamp else None,
                    "is_executable": plan.is_executable
                })
            return {"plans": plans, "count": len(plans)}

        return {"plans": [], "count": 0}
    except Exception as e:
        logger.error(f"Error getting trade plans: {e}")
        return {"error": str(e), "plans": [], "count": 0}


@app.post("/api/trade-plans/generate")
async def generate_trade_plan(request: dict):
    """Generate a trade plan for a specific symbol."""
    global pipeline_orchestrator

    try:
        symbol = request.get("symbol")
        if not symbol:
            return {"error": "Symbol is required"}

        # Auto-initialize pipeline if not already done
        if not pipeline_orchestrator:
            logger.info("Auto-initializing pipeline orchestrator for trade plan generation...")
            pipeline_orchestrator = PipelineOrchestrator()

        plan = await pipeline_orchestrator.generate_plan_for_symbol(symbol)
        if plan:
            return {
                "plan": {
                    "symbol": plan.symbol,
                    "direction": plan.direction,
                    "confidence": plan.confidence,
                    "levels": {
                        "entry": plan.levels.entry,
                        "stop_loss": plan.levels.stop_loss,
                        "target_1": plan.levels.target_1,
                        "target_2": plan.levels.target_2,
                        "risk_reward_ratio": plan.levels.risk_reward_ratio
                    },
                    "rationale": {
                        "setup_type": plan.rationale.setup_type if plan.rationale else "",
                        "key_levels": plan.rationale.key_levels if plan.rationale else [],
                        "catalysts": plan.rationale.catalysts if plan.rationale else [],
                        "risks": plan.rationale.risks if plan.rationale else [],
                        "summary": plan.rationale.summary if plan.rationale else ""
                    },
                    "generated_at": plan.timestamp.isoformat() if plan.timestamp else None,
                    "is_executable": plan.is_executable
                }
            }
        return {"error": "Failed to generate trade plan"}
    except Exception as e:
        logger.error(f"Error generating trade plan: {e}")
        return {"error": str(e)}


@app.get("/api/executor/status")
async def get_executor_status():
    """Get trade executor status."""
    global pipeline_orchestrator

    try:
        if pipeline_orchestrator and pipeline_orchestrator.executor:
            executor = pipeline_orchestrator.executor
            # Use actual attributes from TradeExecutor class
            pending_orders = getattr(executor, 'pending_orders', {})
            return {
                "is_active": pipeline_orchestrator.state.value in ['EXECUTING', 'MONITORING'],
                "open_positions": len(pending_orders),
                "pending_orders": len(pending_orders),
                "trades_today": getattr(executor, 'daily_trades_count', 0),
                "max_trades_per_day": getattr(executor, 'MAX_TRADES_PER_DAY', 10),
                "daily_pnl": -getattr(executor, 'daily_loss', 0.0),  # daily_loss is positive for losses
                "daily_pnl_percent": 0.0,  # Not tracked in current implementation
                "open_risk_percent": getattr(executor, 'open_risk', 0.0),
                "max_open_risk_percent": getattr(executor, 'MAX_OPEN_RISK_PCT', 5.0),
                "last_trade_time": None,  # Not tracked in current implementation
                "positions": []  # Would need to get from portfolio manager
            }

        return {
            "is_active": False,
            "open_positions": 0,
            "pending_orders": 0,
            "trades_today": 0,
            "max_trades_per_day": 10,
            "daily_pnl": 0,
            "daily_pnl_percent": 0,
            "open_risk_percent": 0,
            "max_open_risk_percent": 5,
            "last_trade_time": None,
            "positions": []
        }
    except Exception as e:
        logger.error(f"Error getting executor status: {e}")
        return {"error": str(e)}


@app.post("/api/executor/execute")
async def execute_trade_plan(request: dict):
    """Execute a trade plan."""
    global pipeline_orchestrator

    try:
        symbol = request.get("symbol")
        if not symbol:
            return {"success": False, "message": "Symbol is required"}

        if not pipeline_orchestrator:
            return {"success": False, "message": "Pipeline not initialized"}

        result = await pipeline_orchestrator.execute_plan(symbol)
        return result
    except Exception as e:
        logger.error(f"Error executing trade plan: {e}")
        return {"success": False, "message": str(e)}


@app.post("/api/executor/square-off")
async def square_off_position(request: dict):
    """Square off a specific position."""
    global pipeline_orchestrator

    try:
        symbol = request.get("symbol")
        if not symbol:
            return {"success": False, "message": "Symbol is required"}

        if not pipeline_orchestrator or not pipeline_orchestrator.executor:
            return {"success": False, "message": "Executor not initialized"}

        result = await pipeline_orchestrator.executor.square_off_position(symbol)
        return {"success": result, "message": f"Position {symbol} squared off" if result else "Failed to square off"}
    except Exception as e:
        logger.error(f"Error squaring off position: {e}")
        return {"success": False, "message": str(e)}


@app.post("/api/executor/square-off-all")
async def square_off_all_positions():
    """Square off all open positions."""
    global pipeline_orchestrator

    try:
        if not pipeline_orchestrator or not pipeline_orchestrator.executor:
            return {"success": False, "message": "Executor not initialized", "closed_count": 0}

        closed_count = await pipeline_orchestrator.executor.square_off_all()
        return {"success": True, "message": f"Squared off {closed_count} positions", "closed_count": closed_count}
    except Exception as e:
        logger.error(f"Error squaring off all positions: {e}")
        return {"success": False, "message": str(e), "closed_count": 0}


@app.get("/api/pipeline/metrics")
async def get_pipeline_metrics():
    """Get pipeline performance metrics."""
    global pipeline_orchestrator

    try:
        if pipeline_orchestrator:
            return pipeline_orchestrator.get_metrics()

        return {
            "total_screenings": 0,
            "total_analyses": 0,
            "total_executions": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_pnl": 0,
            "open_positions": 0,
            "open_risk_percent": 0,
            "daily_loss_percent": 0,
            "trades_today": 0
        }
    except Exception as e:
        logger.error(f"Error getting pipeline metrics: {e}")
        return {"error": str(e)}


# ============================================
# MULTI-STRATEGY ANALYSIS ENDPOINTS
# ============================================

# Global instances for multi-strategy analysis
data_aggregator: Optional[DataAggregator] = None
multi_strategy_analyzer: Optional[MultiStrategyAnalyzer] = None


class MultiStrategyRequest(BaseModel):
    """Request body for multi-strategy analysis."""
    symbols: Optional[List[str]] = None  # If None, analyze all screened candidates


@app.post("/api/pipeline/analyze-multi")
async def analyze_multi_strategy(request: Optional[MultiStrategyRequest] = None):
    """
    Run multi-strategy analysis on selected or all screened candidates.

    This endpoint:
    1. Gets latest screener candidates (filtered by request.symbols if provided)
    2. Aggregates complete data (fundamentals, news, technicals)
    3. Runs 3-strategy AI analysis (fundamental, news-based, combined)
    4. Returns recommendations for each stock
    """
    global pipeline_orchestrator, data_aggregator, multi_strategy_analyzer

    try:
        # Initialize components if needed
        if not data_aggregator:
            data_aggregator = DataAggregator(
                broker=broker,
                news_aggregator=news_aggregator
            )

        if not multi_strategy_analyzer:
            multi_strategy_analyzer = MultiStrategyAnalyzer(news_aggregator=news_aggregator)

        # Get screener candidates
        if not pipeline_orchestrator:
            pipeline_orchestrator = PipelineOrchestrator()

        if not pipeline_orchestrator.latest_screener_output:
            # Run screening first
            await pipeline_orchestrator.run_screening_cycle()

        screener_output = pipeline_orchestrator.latest_screener_output
        if not screener_output or not screener_output.candidates:
            return {
                "success": False,
                "message": "No screener candidates available",
                "analyses": []
            }

        # Get symbols - use requested symbols or all candidates
        requested_symbols = request.symbols if request and request.symbols else None

        if requested_symbols:
            # Filter candidates to only include requested symbols
            filtered_candidates = [c for c in screener_output.candidates if c.symbol in requested_symbols]
            symbols = [c.symbol for c in filtered_candidates]
            logger.info(f"Analyzing {len(symbols)} selected stocks: {symbols}")
        else:
            # Use all candidates (up to 10)
            filtered_candidates = screener_output.candidates[:10]
            symbols = [c.symbol for c in filtered_candidates]
            logger.info(f"Analyzing all {len(symbols)} screened stocks: {symbols}")

        if not symbols:
            return {
                "success": False,
                "message": "No valid symbols to analyze",
                "analyses": []
            }

        # Aggregate complete data
        stock_data = await data_aggregator.get_batch_stock_data(
            symbols=symbols,
            screener_candidates=filtered_candidates
        )

        # Run multi-strategy analysis
        analysis_output = await multi_strategy_analyzer.analyze_batch(stock_data)

        # Format response
        analyses = []
        for result in analysis_output.analyses:
            analyses.append({
                "symbol": result.symbol,
                "name": result.name,
                "current_price": result.current_price,
                "day_change_pct": result.day_change_pct,
                "screener_score": result.screener_score,
                "strategies": {
                    "fundamental": {
                        "direction": result.fundamental.direction,
                        "confidence": result.fundamental.confidence,
                        "entry": result.fundamental.entry,
                        "stop_loss": result.fundamental.stop_loss,
                        "target_1": result.fundamental.target_1,
                        "risk_reward": result.fundamental.risk_reward_ratio,
                        "reasoning": result.fundamental.reasoning
                    },
                    "news_based": {
                        "direction": result.news_based.direction,
                        "confidence": result.news_based.confidence,
                        "entry": result.news_based.entry,
                        "stop_loss": result.news_based.stop_loss,
                        "target_1": result.news_based.target_1,
                        "risk_reward": result.news_based.risk_reward_ratio,
                        "reasoning": result.news_based.reasoning
                    },
                    "combined": {
                        "direction": result.combined.direction,
                        "confidence": result.combined.confidence,
                        "entry": result.combined.entry,
                        "stop_loss": result.combined.stop_loss,
                        "target_1": result.combined.target_1,
                        "risk_reward": result.combined.risk_reward_ratio,
                        "reasoning": result.combined.reasoning
                    }
                },
                "recommendation": {
                    "best_strategy": result.recommendation.best_strategy,
                    "confidence": result.recommendation.confidence,
                    "reasoning": result.recommendation.reasoning,
                    "overall_sentiment": result.recommendation.overall_sentiment,
                    "trade_quality": result.recommendation.trade_quality
                }
            })

        return {
            "success": True,
            "timestamp": analysis_output.timestamp.isoformat(),
            "total_analyzed": analysis_output.total_analyzed,
            "duration_ms": analysis_output.analysis_duration_ms,
            "analyses": analyses
        }

    except Exception as e:
        logger.error(f"Error in multi-strategy analysis: {e}")
        return {"success": False, "message": str(e), "analyses": []}


@app.get("/api/pipeline/multi-strategy-results")
async def get_multi_strategy_results():
    """Get the latest multi-strategy analysis results."""
    global multi_strategy_analyzer

    if not multi_strategy_analyzer:
        return {
            "success": False,
            "message": "Multi-strategy analyzer not initialized. Run /api/pipeline/analyze-multi first.",
            "analyses": []
        }

    # For now, return a message to run the analysis
    return {
        "success": True,
        "message": "Use POST /api/pipeline/analyze-multi to run analysis",
        "analyses": []
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Trading Bot")
    parser.add_argument("--mode", choices=["bot", "web", "both"], default="bot",
                       help="Run mode: bot only, web server only, or both")

    args = parser.parse_args()

    if args.mode == "bot":
        # Run trading bot only
        asyncio.run(main())
    elif args.mode == "web":
        # Run web server only
        run_web_server()
    elif args.mode == "both":
        # Run both bot and web server
        import threading

        # Start web server in thread
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()

        # Run bot in main thread
        asyncio.run(main())
