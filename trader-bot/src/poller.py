"""
Stock Poller Module for Trading Bot.
Polls stocks every 10 minutes (inactive) and active trades every 1 minute.
Handles continuous monitoring and decision making.
"""

import asyncio
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
from loguru import logger
import schedule
from dataclasses import dataclass

from config import get_config
from screener import screen_top_stocks
from sentiment import analyze_sentiment
from ai_decision_engine import make_trading_decision
from broker import broker, initialize_broker
from risk_manager import risk_manager, get_risk_manager
from trade_logger import trade_logger, initialize_trade_logger

config = get_config()


@dataclass
class MonitoredStock:
    """Represents a stock being monitored."""
    symbol: str
    added_time: datetime
    last_analysis_time: datetime
    sentiment_score: float
    technical_score: float
    is_active_trade: bool = False
    position_data: Dict = None


@dataclass
class ActiveTrade:
    """Represents an active trade being monitored."""
    trade_id: str
    symbol: str
    entry_time: datetime
    entry_price: float
    stop_loss: float
    target_price: float
    quantity: int
    transaction_type: str
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    last_check_time: datetime = None


class StockPoller:
    """
    Continuous monitoring system for stocks and active trades.
    Implements different polling frequencies based on activity level.
    """
    
    def __init__(self):
        self.config = config
        self.is_running = False
        self.risk_manager = get_risk_manager()
        
        # Monitoring data
        self.monitored_stocks: Dict[str, MonitoredStock] = {}
        self.active_trades: Dict[str, ActiveTrade] = {}
        self.watchlist: Set[str] = set()
        
        # Polling intervals
        self.inactive_poll_interval = config.INACTIVE_POLL_INTERVAL  # 10 minutes
        self.active_poll_interval = config.ACTIVE_POLL_INTERVAL      # 1 minute
        
        # Last execution times
        self.last_screening_time = None
        self.last_inactive_poll = None
        self.last_active_poll = None
        
        # Market hours
        self.market_open_hour = config.MARKET_OPEN_HOUR
        self.market_open_minute = config.MARKET_OPEN_MINUTE
        self.force_exit_hour = config.FORCE_EXIT_HOUR
        self.force_exit_minute = config.FORCE_EXIT_MINUTE
        
        # Daily state
        self.daily_screening_done = False
        self.force_exit_triggered = False
    
    def is_market_hours(self) -> bool:
        """Check if current time is within market hours."""
        now = datetime.now()
        
        # Simple check: 9:15 AM to 3:30 PM IST
        market_open = now.replace(
            hour=self.market_open_hour, 
            minute=self.market_open_minute, 
            second=0, 
            microsecond=0
        )
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def should_force_exit(self) -> bool:
        """Check if it's time to force exit all positions."""
        now = datetime.now()
        force_exit_time = now.replace(
            hour=self.force_exit_hour,
            minute=self.force_exit_minute,
            second=0,
            microsecond=0
        )
        
        return now >= force_exit_time and not self.force_exit_triggered
    
    async def initialize(self) -> bool:
        """Initialize the poller system."""
        try:
            logger.info("🚀 Initializing Stock Poller")
            
            # Initialize dependencies
            broker_success = await initialize_broker()
            logger_success = await initialize_trade_logger()
            
            if not broker_success:
                logger.error("Failed to initialize broker")
                return False
            
            if not logger_success:
                logger.warning("Trade logger initialization failed, continuing with mock logging")
            
            logger.info("✅ Stock Poller initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing poller: {e}")
            return False
    
    async def daily_market_screening(self) -> List[str]:
        """
        Perform daily market screening to identify trading candidates.
        
        Returns:
            List of selected stock symbols
        """
        try:
            logger.info("🔍 Starting daily market screening")
            
            # Screen top stocks
            screened_stocks = await screen_top_stocks(max_stocks=10)
            
            if not screened_stocks:
                logger.warning("No stocks found in screening")
                return []
            
            # Analyze sentiment for screened stocks
            symbols = [stock['symbol'] for stock in screened_stocks]
            sentiment_results = await analyze_sentiment(symbols)
            
            # Select final candidates
            selected_symbols = []
            
            for stock in screened_stocks:
                symbol = stock['symbol']
                sentiment_data = sentiment_results.get(symbol, {})
                
                # Create monitored stock entry
                monitored_stock = MonitoredStock(
                    symbol=symbol,
                    added_time=datetime.now(),
                    last_analysis_time=datetime.now(),
                    sentiment_score=sentiment_data.get('final_sentiment', 0),
                    technical_score=stock.get('screening_score', 0)
                )
                
                self.monitored_stocks[symbol] = monitored_stock
                self.watchlist.add(symbol)
                selected_symbols.append(symbol)
            
            self.daily_screening_done = True
            self.last_screening_time = datetime.now()
            
            logger.info(f"✅ Daily screening complete: {len(selected_symbols)} stocks selected")
            logger.info(f"Selected stocks: {', '.join(selected_symbols)}")
            
            return selected_symbols
            
        except Exception as e:
            logger.error(f"Error in daily market screening: {e}")
            return []
    
    async def poll_inactive_stocks(self):
        """Poll inactive stocks every 10 minutes for trading opportunities."""
        try:
            if not self.monitored_stocks:
                logger.debug("No stocks to poll")
                return
            
            logger.info(f"📊 Polling {len(self.monitored_stocks)} inactive stocks")
            
            # Check risk status
            account_risk = self.risk_manager.check_trading_allowed(broker.positions)
            
            if not account_risk.is_trading_allowed:
                logger.warning(f"Trading not allowed: {account_risk.risk_status}")
                return
            
            # Poll each monitored stock
            for symbol, monitored_stock in list(self.monitored_stocks.items()):
                if monitored_stock.is_active_trade:
                    continue  # Skip active trades (handled separately)
                
                try:
                    await self.analyze_and_decide(symbol, monitored_stock)
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error polling {symbol}: {e}")
            
            self.last_inactive_poll = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in inactive stock polling: {e}")
    
    async def analyze_and_decide(self, symbol: str, monitored_stock: MonitoredStock):
        """
        Analyze a stock and make trading decision.
        
        Args:
            symbol: Stock symbol
            monitored_stock: Monitored stock data
        """
        try:
            logger.debug(f"Analyzing {symbol}")
            
            # Get fresh market data (in production, this would be optimized)
            # For now, we'll use the existing screening data
            stock_data = {
                'symbol': symbol,
                'current_price': await broker.get_current_price(symbol),
                'timestamp': datetime.now()
            }
            
            # Get current sentiment (cached or fresh)
            sentiment_data = {
                'final_sentiment': monitored_stock.sentiment_score,
                'intraday_relevance': 0.6,  # Mock value
                'confidence': 0.7,           # Mock value
                'trade_signal': 'WATCH'
            }
            
            # Make AI decision
            decision_result = await make_trading_decision(stock_data, sentiment_data)
            
            # Log decision
            decision_id = await trade_logger.log_trade_decision(
                symbol, 
                decision_result.get('ai_decision', {}),
                decision_result.get('context', {}),
                decision_result.get('validation', {})
            )
            
            # Execute trade if decision is valid
            if decision_result.get('should_trade', False):
                await self.execute_trade_decision(symbol, decision_result, decision_id)
            
            # Update last analysis time
            monitored_stock.last_analysis_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
    
    async def execute_trade_decision(self, symbol: str, decision_result: Dict, decision_id: str):
        """
        Execute a validated trading decision.
        
        Args:
            symbol: Stock symbol
            decision_result: AI decision result
            decision_id: Decision ID for tracking
        """
        try:
            ai_decision = decision_result['ai_decision']
            
            logger.info(f"🎯 Executing trade: {symbol} - {ai_decision['decision']}")
            
            # Prepare order details
            order_details = {
                'transaction_type': ai_decision['decision'],
                'quantity': int(ai_decision.get('position_size', 0) * config.INITIAL_CAPITAL / ai_decision['entry_price']),
                'order_type': 'MARKET',
                'price': ai_decision['entry_price'],
                'stop_loss': ai_decision['stop_loss'],
                'target': ai_decision['target_price'],
                'tag': f"AI_TRADE_{decision_id}"
            }
            
            # Place bracket order
            order_result = await broker.place_bracket_order(
                symbol=symbol,
                transaction_type=ai_decision['decision'],
                quantity=order_details['quantity'],
                entry_price=ai_decision['entry_price'],
                stop_loss=ai_decision['stop_loss'],
                target=ai_decision['target_price'],
                tag=order_details['tag']
            )
            
            if order_result and order_result.get('entry_order_id'):
                # Log trade execution
                execution_result = {
                    'status': 'COMPLETE',
                    'executed_price': ai_decision['entry_price'],
                    'executed_quantity': order_details['quantity'],
                    'order_id': order_result['entry_order_id'],
                    'execution_time': datetime.now()
                }
                
                trade_id = await trade_logger.log_trade_execution(
                    symbol, order_details, execution_result, decision_id
                )
                
                # Create active trade entry
                active_trade = ActiveTrade(
                    trade_id=trade_id,
                    symbol=symbol,
                    entry_time=datetime.now(),
                    entry_price=ai_decision['entry_price'],
                    stop_loss=ai_decision['stop_loss'],
                    target_price=ai_decision['target_price'],
                    quantity=order_details['quantity'],
                    transaction_type=ai_decision['decision'],
                    current_price=ai_decision['entry_price']
                )
                
                self.active_trades[symbol] = active_trade
                
                # Mark as active in monitored stocks
                if symbol in self.monitored_stocks:
                    self.monitored_stocks[symbol].is_active_trade = True
                
                logger.info(f"✅ Trade executed successfully: {symbol} - {trade_id}")
                
            else:
                logger.error(f"❌ Failed to execute trade for {symbol}")
                
        except Exception as e:
            logger.error(f"Error executing trade for {symbol}: {e}")
    
    async def poll_active_trades(self):
        """Poll active trades every 1 minute for exit conditions."""
        try:
            if not self.active_trades:
                logger.debug("No active trades to monitor")
                return
            
            logger.info(f"📈 Monitoring {len(self.active_trades)} active trades")
            
            for symbol, active_trade in list(self.active_trades.items()):
                try:
                    await self.monitor_active_trade(symbol, active_trade)
                    await asyncio.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error monitoring active trade {symbol}: {e}")
            
            self.last_active_poll = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in active trade polling: {e}")
    
    async def monitor_active_trade(self, symbol: str, active_trade: ActiveTrade):
        """
        Monitor an active trade for exit conditions.
        
        Args:
            symbol: Stock symbol
            active_trade: Active trade data
        """
        try:
            # Get current price
            current_price = await broker.get_current_price(symbol)
            if not current_price:
                logger.warning(f"Could not get current price for {symbol}")
                return
            
            active_trade.current_price = current_price
            active_trade.last_check_time = datetime.now()
            
            # Calculate unrealized P&L
            if active_trade.transaction_type == 'BUY':
                active_trade.unrealized_pnl = ((current_price - active_trade.entry_price) 
                                             * active_trade.quantity)
            else:
                active_trade.unrealized_pnl = ((active_trade.entry_price - current_price) 
                                             * active_trade.quantity)
            
            # Check exit conditions
            should_exit = False
            exit_reason = None
            
            # Stop loss hit
            if active_trade.transaction_type == 'BUY' and current_price <= active_trade.stop_loss:
                should_exit = True
                exit_reason = "STOP_LOSS"
            elif active_trade.transaction_type == 'SELL' and current_price >= active_trade.stop_loss:
                should_exit = True
                exit_reason = "STOP_LOSS"
            
            # Target hit
            elif active_trade.transaction_type == 'BUY' and current_price >= active_trade.target_price:
                should_exit = True
                exit_reason = "TARGET"
            elif active_trade.transaction_type == 'SELL' and current_price <= active_trade.target_price:
                should_exit = True
                exit_reason = "TARGET"
            
            # Time-based exit (been in trade too long)
            elif (datetime.now() - active_trade.entry_time).total_seconds() > 14400:  # 4 hours
                should_exit = True
                exit_reason = "TIME_LIMIT"
            
            # Force exit check
            elif self.should_force_exit():
                should_exit = True
                exit_reason = "FORCE_EXIT"
            
            if should_exit:
                await self.exit_active_trade(symbol, active_trade, exit_reason)
            else:
                logger.debug(f"{symbol}: ₹{current_price:.2f} (P&L: ₹{active_trade.unrealized_pnl:.2f})")
            
        except Exception as e:
            logger.error(f"Error monitoring active trade {symbol}: {e}")
    
    async def exit_active_trade(self, symbol: str, active_trade: ActiveTrade, reason: str):
        """
        Exit an active trade.
        
        Args:
            symbol: Stock symbol
            active_trade: Active trade to exit
            reason: Reason for exit
        """
        try:
            logger.info(f"🚪 Exiting trade: {symbol} - Reason: {reason}")
            
            # Place exit order
            exit_success = await broker.exit_position(symbol)
            
            if exit_success:
                # Log trade exit
                exit_details = {
                    'entry_price': active_trade.entry_price,
                    'entry_time': active_trade.entry_time,
                    'original_transaction_type': active_trade.transaction_type
                }
                
                exit_result = {
                    'executed_price': active_trade.current_price,
                    'executed_quantity': active_trade.quantity,
                    'order_id': f"EXIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                }
                
                await trade_logger.log_trade_exit(
                    active_trade.trade_id,
                    exit_details,
                    exit_result,
                    reason
                )
                
                # Record trade outcome in risk manager
                self.risk_manager.record_trade_outcome(
                    symbol=symbol,
                    entry_price=active_trade.entry_price,
                    exit_price=active_trade.current_price,
                    quantity=active_trade.quantity,
                    transaction_type=active_trade.transaction_type
                )
                
                # Remove from active trades
                del self.active_trades[symbol]
                
                # Update monitored stock status
                if symbol in self.monitored_stocks:
                    self.monitored_stocks[symbol].is_active_trade = False
                
                logger.info(f"✅ Trade exited: {symbol} - P&L: ₹{active_trade.unrealized_pnl:.2f}")
                
            else:
                logger.error(f"❌ Failed to exit trade for {symbol}")
                
        except Exception as e:
            logger.error(f"Error exiting trade {symbol}: {e}")
    
    async def force_exit_all_trades(self):
        """Force exit all active trades at market close."""
        if self.force_exit_triggered:
            return
        
        try:
            logger.warning("🚨 FORCE EXIT: Closing all positions")
            
            # Exit all active trades
            for symbol in list(self.active_trades.keys()):
                active_trade = self.active_trades[symbol]
                await self.exit_active_trade(symbol, active_trade, "MARKET_CLOSE")
            
            # Also use broker's force exit
            await broker.force_exit_all_positions()
            
            self.force_exit_triggered = True
            logger.info("✅ All positions force-closed")
            
        except Exception as e:
            logger.error(f"Error in force exit: {e}")
    
    async def reset_daily_state(self):
        """Reset daily state for new trading day."""
        logger.info("🔄 Resetting daily state")
        
        self.daily_screening_done = False
        self.force_exit_triggered = False
        self.monitored_stocks.clear()
        self.active_trades.clear()
        self.watchlist.clear()
        
        # Reset risk manager
        self.risk_manager.reset_daily_metrics()
    
    async def run_continuous_polling(self):
        """Main continuous polling loop."""
        logger.info("🔄 Starting continuous polling loop")
        self.is_running = True
        
        while self.is_running:
            try:
                now = datetime.now()
                
                # Check if it's a new day
                if (self.last_screening_time and 
                    now.date() > self.last_screening_time.date()):
                    await self.reset_daily_state()
                
                # Only operate during market hours
                if not self.is_market_hours():
                    logger.debug("Outside market hours - sleeping")
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # Force exit check
                if self.should_force_exit():
                    await self.force_exit_all_trades()
                    await asyncio.sleep(60)
                    continue
                
                # Daily screening (once per day)
                if not self.daily_screening_done:
                    await self.daily_market_screening()
                
                # Active trades polling (every 1 minute)
                if (not self.last_active_poll or 
                    (now - self.last_active_poll).total_seconds() >= self.active_poll_interval):
                    await self.poll_active_trades()
                
                # Inactive stocks polling (every 10 minutes)
                if (not self.last_inactive_poll or 
                    (now - self.last_inactive_poll).total_seconds() >= self.inactive_poll_interval):
                    await self.poll_inactive_stocks()
                
                # Short sleep to prevent busy waiting
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def stop(self):
        """Stop the polling loop."""
        logger.info("🛑 Stopping poller")
        self.is_running = False
    
    async def get_status(self) -> Dict:
        """Get current poller status."""
        return {
            'is_running': self.is_running,
            'monitored_stocks': len(self.monitored_stocks),
            'active_trades': len(self.active_trades),
            'daily_screening_done': self.daily_screening_done,
            'force_exit_triggered': self.force_exit_triggered,
            'last_screening_time': self.last_screening_time,
            'last_inactive_poll': self.last_inactive_poll,
            'last_active_poll': self.last_active_poll,
            'is_market_hours': self.is_market_hours(),
            'watchlist': list(self.watchlist)
        }


# Global poller instance
poller = StockPoller()


async def start_poller():
    """Start the stock poller."""
    success = await poller.initialize()
    if success:
        await poller.run_continuous_polling()
    else:
        logger.error("Failed to start poller")


if __name__ == "__main__":
    # Test the poller
    async def test_poller():
        try:
            success = await poller.initialize()
            if not success:
                print("❌ Failed to initialize poller")
                return
            
            print("✅ Poller initialized")
            
            # Test daily screening
            stocks = await poller.daily_market_screening()
            print(f"Screened stocks: {stocks}")
            
            # Test status
            status = await poller.get_status()
            print(f"Status: {status}")
            
            # Don't run continuous loop in test
            print("Test completed successfully")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    asyncio.run(test_poller())
