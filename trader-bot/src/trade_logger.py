"""
Trade Logger Module for Trading Bot.
Logs all trades, decisions, and outcomes to MongoDB for analysis and backtesting.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from loguru import logger
import json

from config import get_config

config = get_config()


class TradeLogger:
    """
    Comprehensive logging system for trading activities.
    Stores all trades, decisions, and analysis in MongoDB.
    """
    
    def __init__(self):
        self.config = config
        self.client = None
        self.db = None
        
        # Collections
        self.trades_collection = None
        self.decisions_collection = None
        self.daily_reports_collection = None
        self.risk_events_collection = None
        self.market_data_collection = None
    
    async def initialize(self) -> bool:
        """
        Initialize MongoDB connection and collections.
        
        Returns:
            Success status
        """
        try:
            # Connect to MongoDB
            self.client = AsyncIOMotorClient(self.config.MONGODB_URL)
            self.db = self.client[self.config.DATABASE_NAME]
            
            # Initialize collections
            self.trades_collection = self.db.trades
            self.decisions_collection = self.db.decisions
            self.daily_reports_collection = self.db.daily_reports
            self.risk_events_collection = self.db.risk_events
            self.market_data_collection = self.db.market_data
            
            # Create indexes for better performance
            await self.create_indexes()
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("✅ MongoDB connection established")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {e}")
            logger.warning("Continuing with mock logging...")
            return False
    
    async def create_indexes(self):
        """Create database indexes for optimal performance."""
        try:
            # Trades collection indexes
            await self.trades_collection.create_index([
                ("symbol", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            await self.trades_collection.create_index([("trade_id", ASCENDING)])
            await self.trades_collection.create_index([("date", DESCENDING)])
            
            # Decisions collection indexes
            await self.decisions_collection.create_index([
                ("symbol", ASCENDING),
                ("timestamp", DESCENDING)
            ])
            await self.decisions_collection.create_index([("decision_id", ASCENDING)])
            
            # Daily reports indexes
            await self.daily_reports_collection.create_index([("date", DESCENDING)])
            
            # Risk events indexes
            await self.risk_events_collection.create_index([("timestamp", DESCENDING)])
            await self.risk_events_collection.create_index([("event_type", ASCENDING)])
            
            logger.info("✅ Database indexes created")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def generate_trade_id(self) -> str:
        """Generate unique trade ID."""
        return f"TRD_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def generate_decision_id(self) -> str:
        """Generate unique decision ID."""
        return f"DEC_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    async def log_trade_decision(self, symbol: str, ai_decision: Dict,
                               market_context: Dict, validation_result: Dict) -> str:
        """
        Log AI trading decision with full context.
        
        Args:
            symbol: Stock symbol
            ai_decision: AI decision output
            market_context: Market context used for decision
            validation_result: Risk validation results
            
        Returns:
            Decision ID
        """
        try:
            decision_id = self.generate_decision_id()
            
            decision_record = {
                'decision_id': decision_id,
                'symbol': symbol,
                'timestamp': datetime.now(),
                'date': datetime.now().date().isoformat(),
                
                # AI Decision
                'ai_decision': {
                    'decision': ai_decision.get('decision', 'HOLD'),
                    'confidence': ai_decision.get('confidence', 0),
                    'reasoning': ai_decision.get('reasoning', ''),
                    'entry_price': ai_decision.get('entry_price', 0),
                    'stop_loss': ai_decision.get('stop_loss', 0),
                    'target_price': ai_decision.get('target_price', 0),
                    'risk_reward_ratio': ai_decision.get('risk_reward_ratio', 0),
                    'position_size': ai_decision.get('position_size', 0)
                },
                
                # Market Context
                'market_context': market_context,
                
                # Validation
                'validation': validation_result,
                
                # Outcome
                'final_action': validation_result.get('final_action', 'HOLD'),
                'should_trade': validation_result.get('should_trade', False),
                
                # Metadata
                'bot_version': '1.0',
                'config_snapshot': {
                    'min_confidence': self.config.AI_CONFIDENCE_THRESHOLD,
                    'min_risk_reward': self.config.MIN_RISK_REWARD_RATIO,
                    'max_capital_per_trade': self.config.MAX_CAPITAL_PER_TRADE
                }
            }
            
            if self.decisions_collection:
                await self.decisions_collection.insert_one(decision_record)
                logger.info(f"✅ Decision logged: {decision_id} - {symbol}")
            else:
                # Mock logging
                logger.info(f"📝 [MOCK] Decision logged: {decision_id} - {symbol} - {ai_decision.get('decision')}")
            
            return decision_id
            
        except Exception as e:
            logger.error(f"Error logging trade decision: {e}")
            return f"ERROR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def log_trade_execution(self, symbol: str, order_details: Dict,
                                execution_result: Dict, decision_id: str = None) -> str:
        """
        Log trade execution details.
        
        Args:
            symbol: Stock symbol
            order_details: Order placement details
            execution_result: Execution results from broker
            decision_id: Related decision ID
            
        Returns:
            Trade ID
        """
        try:
            trade_id = self.generate_trade_id()
            
            trade_record = {
                'trade_id': trade_id,
                'decision_id': decision_id,
                'symbol': symbol,
                'timestamp': datetime.now(),
                'date': datetime.now().date().isoformat(),
                
                # Order Details
                'order_type': order_details.get('order_type', 'MARKET'),
                'transaction_type': order_details.get('transaction_type'),
                'quantity': order_details.get('quantity', 0),
                'requested_price': order_details.get('price', 0),
                
                # Execution Details
                'execution_status': execution_result.get('status', 'UNKNOWN'),
                'executed_price': execution_result.get('executed_price', 0),
                'executed_quantity': execution_result.get('executed_quantity', 0),
                'execution_time': execution_result.get('execution_time'),
                'broker_order_id': execution_result.get('order_id'),
                
                # Risk Management
                'stop_loss_price': order_details.get('stop_loss'),
                'target_price': order_details.get('target'),
                'position_size_pct': order_details.get('position_size_pct', 0),
                
                # Status
                'is_entry': True,
                'is_closed': False,
                'pnl': 0.0,
                'pnl_pct': 0.0,
                
                # Metadata
                'broker_used': 'MOCK' if self.config.MOCK_BROKER else 'ZERODHA',
                'trading_session': self.get_trading_session()
            }
            
            if self.trades_collection:
                await self.trades_collection.insert_one(trade_record)
                logger.info(f"✅ Trade execution logged: {trade_id} - {symbol}")
            else:
                # Mock logging
                logger.info(f"📝 [MOCK] Trade logged: {trade_id} - {symbol} - "
                           f"{order_details.get('transaction_type')} {order_details.get('quantity')}")
            
            return trade_id
            
        except Exception as e:
            logger.error(f"Error logging trade execution: {e}")
            return f"ERROR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def log_trade_exit(self, trade_id: str, exit_details: Dict,
                           exit_result: Dict, exit_reason: str) -> bool:
        """
        Log trade exit and calculate final P&L.
        
        Args:
            trade_id: Original trade ID
            exit_details: Exit order details
            exit_result: Exit execution results
            exit_reason: Reason for exit (SL/TARGET/FORCE/TIME)
            
        Returns:
            Success status
        """
        try:
            # Calculate P&L
            entry_price = exit_details.get('entry_price', 0)
            exit_price = exit_result.get('executed_price', 0)
            quantity = exit_result.get('executed_quantity', 0)
            transaction_type = exit_details.get('original_transaction_type', 'BUY')
            
            if transaction_type == 'BUY':
                pnl = (exit_price - entry_price) * quantity
            else:
                pnl = (entry_price - exit_price) * quantity
            
            pnl_pct = (pnl / (entry_price * quantity)) * 100 if entry_price > 0 else 0
            
            # Update trade record
            update_data = {
                'exit_timestamp': datetime.now(),
                'exit_price': exit_price,
                'exit_quantity': quantity,
                'exit_reason': exit_reason,
                'is_closed': True,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'exit_order_id': exit_result.get('order_id'),
                'trade_duration_minutes': self.calculate_trade_duration(exit_details.get('entry_time'))
            }
            
            if self.trades_collection:
                result = await self.trades_collection.update_one(
                    {'trade_id': trade_id},
                    {'$set': update_data}
                )
                
                if result.modified_count > 0:
                    logger.info(f"✅ Trade exit logged: {trade_id} - P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%)")
                    return True
                else:
                    logger.warning(f"Trade {trade_id} not found for exit update")
                    return False
            else:
                # Mock logging
                logger.info(f"📝 [MOCK] Trade exit: {trade_id} - P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%) - {exit_reason}")
                return True
                
        except Exception as e:
            logger.error(f"Error logging trade exit: {e}")
            return False
    
    async def log_risk_event(self, event_type: str, description: str,
                           severity: str = "INFO", additional_data: Dict = None):
        """
        Log risk management events.
        
        Args:
            event_type: Type of risk event
            description: Event description
            severity: Severity level (INFO/WARNING/ERROR)
            additional_data: Additional event data
        """
        try:
            risk_event = {
                'timestamp': datetime.now(),
                'date': datetime.now().date().isoformat(),
                'event_type': event_type,
                'description': description,
                'severity': severity,
                'additional_data': additional_data or {}
            }
            
            if self.risk_events_collection:
                await self.risk_events_collection.insert_one(risk_event)
            
            logger.info(f"🛡️ Risk event logged: {event_type} - {description}")
            
        except Exception as e:
            logger.error(f"Error logging risk event: {e}")
    
    def calculate_trade_duration(self, entry_time: datetime) -> Optional[int]:
        """Calculate trade duration in minutes."""
        if entry_time:
            duration = datetime.now() - entry_time
            return int(duration.total_seconds() / 60)
        return None
    
    def get_trading_session(self) -> str:
        """Get current trading session."""
        now = datetime.now()
        hour = now.hour
        
        if 9 <= hour < 11:
            return "OPENING"
        elif 11 <= hour < 14:
            return "MID_SESSION"
        elif 14 <= hour < 15:
            return "CLOSING"
        else:
            return "POST_MARKET"
    
    async def get_daily_trades(self, date: datetime = None) -> List[Dict]:
        """
        Get all trades for a specific date.
        
        Args:
            date: Date to query (defaults to today)
            
        Returns:
            List of trades for the date
        """
        try:
            if date is None:
                date = datetime.now().date()
            
            date_str = date.isoformat()
            
            if self.trades_collection:
                cursor = self.trades_collection.find({'date': date_str}).sort('timestamp', ASCENDING)
                trades = await cursor.to_list(length=None)
                return trades
            else:
                # Mock data
                return []
                
        except Exception as e:
            logger.error(f"Error getting daily trades: {e}")
            return []
    
    async def get_daily_decisions(self, date: datetime = None) -> List[Dict]:
        """
        Get all decisions for a specific date.
        
        Args:
            date: Date to query (defaults to today)
            
        Returns:
            List of decisions for the date
        """
        try:
            if date is None:
                date = datetime.now().date()
            
            date_str = date.isoformat()
            
            if self.decisions_collection:
                cursor = self.decisions_collection.find({'date': date_str}).sort('timestamp', ASCENDING)
                decisions = await cursor.to_list(length=None)
                return decisions
            else:
                # Mock data
                return []
                
        except Exception as e:
            logger.error(f"Error getting daily decisions: {e}")
            return []
    
    async def generate_daily_report(self, date: datetime = None) -> Dict:
        """
        Generate comprehensive daily trading report.
        
        Args:
            date: Date for report (defaults to today)
            
        Returns:
            Daily report dictionary
        """
        try:
            if date is None:
                date = datetime.now().date()
            
            # Get trades and decisions
            trades = await self.get_daily_trades(date)
            decisions = await self.get_daily_decisions(date)
            
            # Calculate trade statistics
            total_trades = len(trades)
            completed_trades = [t for t in trades if t.get('is_closed', False)]
            winning_trades = [t for t in completed_trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in completed_trades if t.get('pnl', 0) < 0]
            
            total_pnl = sum(t.get('pnl', 0) for t in completed_trades)
            total_pnl_pct = sum(t.get('pnl_pct', 0) for t in completed_trades)
            
            win_rate = (len(winning_trades) / len(completed_trades) * 100) if completed_trades else 0
            avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            # Decision statistics
            total_decisions = len(decisions)
            buy_decisions = len([d for d in decisions if d.get('ai_decision', {}).get('decision') == 'BUY'])
            sell_decisions = len([d for d in decisions if d.get('ai_decision', {}).get('decision') == 'SELL'])
            hold_decisions = len([d for d in decisions if d.get('ai_decision', {}).get('decision') == 'HOLD'])
            
            executed_decisions = len([d for d in decisions if d.get('should_trade', False)])
            decision_execution_rate = (executed_decisions / total_decisions * 100) if total_decisions else 0
            
            # Create report
            report = {
                'date': date.isoformat(),
                'generated_at': datetime.now(),
                
                # Trade Statistics
                'trade_summary': {
                    'total_trades': total_trades,
                    'completed_trades': len(completed_trades),
                    'winning_trades': len(winning_trades),
                    'losing_trades': len(losing_trades),
                    'win_rate_pct': win_rate,
                    'total_pnl': total_pnl,
                    'total_pnl_pct': total_pnl_pct,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0
                },
                
                # Decision Statistics
                'decision_summary': {
                    'total_decisions': total_decisions,
                    'buy_decisions': buy_decisions,
                    'sell_decisions': sell_decisions,
                    'hold_decisions': hold_decisions,
                    'executed_decisions': executed_decisions,
                    'execution_rate_pct': decision_execution_rate
                },
                
                # Detailed trades
                'trades': completed_trades,
                
                # Top performers
                'best_trade': max(completed_trades, key=lambda x: x.get('pnl', 0)) if completed_trades else None,
                'worst_trade': min(completed_trades, key=lambda x: x.get('pnl', 0)) if completed_trades else None,
                
                # Risk metrics
                'risk_metrics': {
                    'max_single_loss': min(t.get('pnl', 0) for t in completed_trades) if completed_trades else 0,
                    'max_single_gain': max(t.get('pnl', 0) for t in completed_trades) if completed_trades else 0,
                    'avg_trade_duration_min': sum(t.get('trade_duration_minutes', 0) for t in completed_trades) / len(completed_trades) if completed_trades else 0
                }
            }
            
            # Save report to database
            if self.daily_reports_collection:
                await self.daily_reports_collection.replace_one(
                    {'date': date.isoformat()},
                    report,
                    upsert=True
                )
            
            logger.info(f"📊 Daily report generated for {date}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {}
    
    async def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Global trade logger instance
trade_logger = TradeLogger()


async def initialize_trade_logger() -> bool:
    """Initialize the global trade logger."""
    return await trade_logger.initialize()


if __name__ == "__main__":
    # Test the trade logger
    async def test_trade_logger():
        try:
            # Initialize
            success = await initialize_trade_logger()
            print(f"Logger initialized: {success}")
            
            # Log a decision
            ai_decision = {
                'decision': 'BUY',
                'confidence': 0.8,
                'reasoning': 'Strong bullish signals detected',
                'entry_price': 2500.0,
                'stop_loss': 2450.0,
                'target_price': 2600.0,
                'risk_reward_ratio': 2.0
            }
            
            market_context = {
                'symbol': 'RELIANCE',
                'technical': {'rsi': 35, 'volume_ratio': 2.1},
                'sentiment': {'final_sentiment': 0.6}
            }
            
            validation_result = {
                'final_action': 'BUY',
                'should_trade': True
            }
            
            decision_id = await trade_logger.log_trade_decision(
                'RELIANCE', ai_decision, market_context, validation_result
            )
            print(f"Decision logged: {decision_id}")
            
            # Log trade execution
            order_details = {
                'transaction_type': 'BUY',
                'quantity': 10,
                'order_type': 'MARKET'
            }
            
            execution_result = {
                'status': 'COMPLETE',
                'executed_price': 2505.0,
                'executed_quantity': 10,
                'order_id': 'ORD_123'
            }
            
            trade_id = await trade_logger.log_trade_execution(
                'RELIANCE', order_details, execution_result, decision_id
            )
            print(f"Trade logged: {trade_id}")
            
            # Generate daily report
            report = await trade_logger.generate_daily_report()
            print(f"Report generated with {report.get('trade_summary', {}).get('total_trades', 0)} trades")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    asyncio.run(test_trade_logger())
