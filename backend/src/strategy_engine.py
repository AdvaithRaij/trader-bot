"""
Strategy Engine - Orchestrates stock picking and trade signal generation.
"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from models import (
    StrategyModel,
    TradeSignal,
    TradeDirection,
    StockPickingType,
    ExecutionType
)
from strategy_manager import StrategyManager
from strategies.news_picker import NewsBasedStockPicker
from ai_trade_assistant import AITradeAssistant
from news_aggregator import NewsAggregator
from broker import FyersBroker


class StrategyEngine:
    """
    Main strategy orchestrator.
    
    Responsibilities:
    - Load and manage active strategies
    - Execute stock picking logic
    - Generate trade signals
    - Schedule periodic strategy runs
    """
    
    def __init__(
        self,
        strategy_manager: StrategyManager,
        news_aggregator: NewsAggregator,
        broker: FyersBroker,
        ai_assistant: Optional[AITradeAssistant] = None
    ):
        """
        Initialize Strategy Engine.
        
        Args:
            strategy_manager: Strategy manager instance
            news_aggregator: News aggregator instance
            broker: Broker instance for price data
            ai_assistant: AI trade assistant (optional)
        """
        self.strategy_manager = strategy_manager
        self.news_aggregator = news_aggregator
        self.broker = broker
        self.ai_assistant = ai_assistant or AITradeAssistant()
        
        # Stock pickers
        self.news_picker = NewsBasedStockPicker(news_aggregator)
        
        # Scheduler
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        logger.info("🎯 Strategy Engine initialized")
    
    async def run_all_strategies(self) -> List[TradeSignal]:
        """
        Run all active strategies and generate signals.
        
        Returns:
            List of trade signals
        """
        try:
            logger.info("🚀 Running all active strategies...")
            
            # Get active strategies
            active_strategies = await self.strategy_manager.get_active_strategies()
            
            if not active_strategies:
                logger.info("ℹ️ No active strategies found")
                return []
            
            logger.info(f"📊 Found {len(active_strategies)} active strategies")
            
            # Run each strategy
            all_signals = []
            for strategy in active_strategies:
                signals = await self.run_strategy(strategy.strategyId)
                all_signals.extend(signals)
            
            logger.info(f"✅ Generated {len(all_signals)} trade signals")
            return all_signals
            
        except Exception as e:
            logger.error(f"❌ Error running strategies: {e}")
            return []
    
    async def run_strategy(self, strategy_id: str) -> List[TradeSignal]:
        """
        Run a specific strategy and generate signals.
        
        Args:
            strategy_id: Strategy ID to run
        
        Returns:
            List of trade signals
        """
        try:
            logger.info(f"🎯 Running strategy: {strategy_id}")
            
            # Get strategy
            strategy = await self.strategy_manager.get_strategy(strategy_id)
            if not strategy:
                logger.warning(f"⚠️ Strategy {strategy_id} not found")
                return []
            
            # Step 1: Pick stocks based on strategy
            stock_picks = await self._pick_stocks(strategy)
            
            if not stock_picks:
                logger.info(f"ℹ️ No stocks picked by {strategy.name}")
                return []
            
            logger.info(f"📊 Picked {len(stock_picks)} stocks: {[s['symbol'] for s in stock_picks]}")
            
            # Step 2: Generate trade signals for each stock
            signals = []
            for stock_pick in stock_picks:
                signal = await self._generate_signal(strategy, stock_pick)
                if signal:
                    signals.append(signal)
            
            logger.info(f"✅ Generated {len(signals)} signals from {strategy.name}")
            return signals
            
        except Exception as e:
            logger.error(f"❌ Error running strategy {strategy_id}: {e}")
            return []
    
    async def _pick_stocks(self, strategy: StrategyModel) -> List[Dict]:
        """Pick stocks based on strategy configuration"""
        
        stock_picking = strategy.stockPicking
        
        # News-based stock picking
        if stock_picking.type == StockPickingType.NEWS_BASED:
            return await self.news_picker.pick_stocks(stock_picking)
        
        # Technical analysis (TODO: implement in Phase 3)
        elif stock_picking.type == StockPickingType.TECHNICAL:
            logger.warning("⚠️ Technical stock picking not yet implemented")
            return []
        
        # Momentum-based (TODO: implement in Phase 3)
        elif stock_picking.type == StockPickingType.MOMENTUM:
            logger.warning("⚠️ Momentum stock picking not yet implemented")
            return []
        
        # AI-recommended (TODO: implement in Phase 3)
        elif stock_picking.type == StockPickingType.AI_RECOMMENDED:
            logger.warning("⚠️ AI-recommended stock picking not yet implemented")
            return []
        
        else:
            logger.error(f"❌ Unknown stock picking type: {stock_picking.type}")
            return []
    
    async def _generate_signal(
        self,
        strategy: StrategyModel,
        stock_pick: Dict
    ) -> Optional[TradeSignal]:
        """Generate trade signal for a stock pick"""
        
        try:
            symbol = stock_pick['symbol']
            news_context = stock_pick.get('news', [])
            
            logger.info(f"📈 Generating signal for {symbol}")
            
            # Get current price
            current_price = await self.broker.get_ltp(symbol)
            
            if not current_price or current_price <= 0:
                logger.warning(f"⚠️ Invalid price for {symbol}: {current_price}")
                return None
            
            # Determine direction (for now, always BUY for positive news)
            # TODO: Add SELL logic for negative news
            direction = TradeDirection.BUY
            
            # Get AI-suggested levels
            levels = await self.ai_assistant.suggest_levels(
                symbol=symbol,
                current_price=current_price,
                direction=direction,
                news_context=news_context,
                execution_config=strategy.execution,
                price_data=None  # TODO: Add price data from broker
            )
            
            # Create trade signal
            signal = TradeSignal(
                symbol=symbol,
                direction=direction,
                strategyId=strategy.strategyId,
                strategyName=strategy.name,
                entryPrice=levels['entryPrice'],
                stopLoss=levels['stopLoss'],
                target1=levels['target1'],
                target2=levels.get('target2'),
                confidence=levels['confidence'],
                reasoning=levels['reasoning'],
                newsArticles=[article.get('id') for article in news_context[:3]] if news_context else None,  # Top 3 news article IDs
                aiAnalysis={
                    'expectedMove': levels.get('expectedMove'),
                    'riskRewardRatio': levels.get('riskRewardRatio'),
                    'stockScore': stock_pick.get('score')
                }
            )
            
            logger.info(
                f"✅ Signal generated: {direction.value} {symbol} @ ₹{signal.entryPrice} "
                f"(SL: ₹{signal.stopLoss}, T1: ₹{signal.target1}, Confidence: {signal.confidence}%)"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error generating signal for {stock_pick.get('symbol')}: {e}")
            return None
    
    async def start_scheduler(self, interval_minutes: int = 15):
        """
        Start periodic strategy execution.
        
        Args:
            interval_minutes: Run strategies every N minutes
        """
        if self.is_running:
            logger.warning("⚠️ Scheduler already running")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(
            self._scheduler_loop(interval_minutes)
        )
        
        logger.info(f"⏰ Strategy scheduler started (interval: {interval_minutes} minutes)")
    
    async def stop_scheduler(self):
        """Stop periodic strategy execution"""
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Strategy scheduler stopped")
    
    async def _scheduler_loop(self, interval_minutes: int):
        """Scheduler loop that runs strategies periodically"""
        logger.info("⏰ Strategy scheduler loop started")
        
        while self.is_running:
            try:
                # Run all strategies
                signals = await self.run_all_strategies()
                
                if signals:
                    logger.info(f"📊 Scheduler generated {len(signals)} signals")
                    # Signals will be picked up by the main trading loop
                else:
                    logger.info("ℹ️ Scheduler run completed, no signals generated")
                
                # Wait for next interval
                await asyncio.sleep(interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
        
        logger.info("⏰ Strategy scheduler loop stopped")
    
    async def generate_manual_signal(
        self,
        symbol: str,
        strategy_id: Optional[str] = None
    ) -> Optional[TradeSignal]:
        """
        Manually generate a signal for a specific symbol.
        
        Args:
            symbol: Stock symbol
            strategy_id: Strategy to use (if None, uses first active strategy)
        
        Returns:
            Trade signal or None
        """
        try:
            logger.info(f"🎯 Manually generating signal for {symbol}")
            
            # Get strategy
            if strategy_id:
                strategy = await self.strategy_manager.get_strategy(strategy_id)
            else:
                # Use first active strategy
                active_strategies = await self.strategy_manager.get_active_strategies()
                strategy = active_strategies[0] if active_strategies else None
            
            if not strategy:
                logger.warning("⚠️ No strategy available")
                return None
            
            # Get news context for this symbol
            news_context = await self.news_picker.get_stock_context(symbol)
            
            # Create stock pick
            stock_pick = {
                'symbol': symbol,
                'score': news_context.get('avgRelevance', 50),
                'news': news_context.get('news', []),
                'reasoning': f"Manual signal for {symbol}"
            }
            
            # Generate signal
            signal = await self._generate_signal(strategy, stock_pick)
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error generating manual signal: {e}")
            return None

