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
from typing import Optional
import uvicorn
from contextlib import asynccontextmanager

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
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize_components(self) -> bool:
        """
        Initialize all trading bot components.
        
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
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan management."""
    # Startup
    logger.info("🌐 Starting FastAPI server...")
    yield
    # Shutdown
    logger.info("🌐 Shutting down FastAPI server...")


app = FastAPI(
    title="Trading Bot API",
    description="AI-powered intraday trading bot",
    version="1.0.0",
    lifespan=lifespan
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
        return {"trades": trades}
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
