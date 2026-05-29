"""
Execution Engine - Handles trade execution and position monitoring.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from loguru import logger

from models import (
    TradeModel,
    TradeSignal,
    TradeStatus,
    TradeDirection,
    ExitReason,
    OrderDetails
)
from portfolio_manager import PortfolioManager
from broker import FyersBroker, OrderType
from broker_resilient import trading_circuit_breaker


class ExecutionEngine:
    """
    Manages trade execution and real-time position monitoring.
    
    Responsibilities:
    - Execute trades based on signals
    - Monitor open positions for SL/TP
    - Handle order placement and failures
    - Update portfolio manager
    - Persist trades to database
    """
    
    def __init__(
        self,
        broker: FyersBroker,
        portfolio_manager: PortfolioManager,
        db_collection=None
    ):
        """
        Initialize Execution Engine.
        
        Args:
            broker: Fyers broker instance
            portfolio_manager: Portfolio manager instance
            db_collection: MongoDB collection for trade persistence
        """
        self.broker = broker
        self.portfolio = portfolio_manager
        self.db_collection = db_collection
        
        # Active trades and monitoring
        self.active_trades: Dict[str, TradeModel] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False

        logger.info("⚡ Execution Engine initialized")

    async def _calculate_atr(self, symbol: str, period: int = 14) -> float:
        """
        Calculate Average True Range (ATR) for volatility-based position sizing.

        Args:
            symbol: Stock symbol
            period: ATR period (default 14)

        Returns:
            ATR value or 0 if calculation fails
        """
        try:
            # Get historical data for ATR calculation
            historical = await self.broker.get_historical_data(
                symbol=symbol,
                resolution="D",  # Daily candles
                days=period + 5  # Extra days for calculation
            )

            if not historical or len(historical) < period:
                logger.warning(f"⚠️ Insufficient data for ATR calculation: {symbol}")
                return 0.0

            # Calculate True Range for each candle
            true_ranges = []
            for i in range(1, len(historical)):
                high = historical[i].get('high', 0)
                low = historical[i].get('low', 0)
                prev_close = historical[i-1].get('close', 0)

                # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                true_ranges.append(tr)

            # Calculate ATR as average of last 'period' true ranges
            if len(true_ranges) >= period:
                atr = sum(true_ranges[-period:]) / period
                logger.info(f"📊 ATR for {symbol}: ₹{atr:.2f}")
                return atr

            return 0.0

        except Exception as e:
            logger.error(f"❌ Error calculating ATR for {symbol}: {e}")
            return 0.0

    async def execute_signal(self, signal: TradeSignal) -> Optional[TradeModel]:
        """
        Execute a trade signal.
        
        Args:
            signal: Trade signal to execute
        
        Returns:
            TradeModel if successful, None otherwise
        """
        try:
            logger.info(f"📊 Executing signal: {signal.direction} {signal.symbol} @ ₹{signal.entryPrice}")

            # Calculate ATR for volatility-based position sizing
            atr = await self._calculate_atr(signal.symbol)

            # Calculate position size with ATR adjustment
            quantity, allocated_capital = self.portfolio.calculate_position_size(
                signal,
                signal.entryPrice,
                atr=atr
            )

            if quantity == 0:
                logger.warning(f"⚠️ Position size is 0, skipping trade")
                return None
            
            # Check if we can open position
            can_open, reason = self.portfolio.can_open_position(signal.symbol, allocated_capital)
            if not can_open:
                logger.warning(f"⚠️ Cannot open position: {reason}")
                return None
            
            # Create trade model
            trade = TradeModel(
                tradeId=str(uuid.uuid4()),
                strategyId=signal.strategyId,
                strategyName=signal.strategyName,
                symbol=signal.symbol,
                direction=signal.direction,
                entryTime=datetime.now(),
                entryPrice=signal.entryPrice,
                quantity=quantity,
                stopLoss=signal.stopLoss,
                target1=signal.target1,
                target2=signal.target2,
                status=TradeStatus.PENDING,
                aiAnalysis=signal.aiAnalysis,
                newsArticles=signal.newsArticles
            )
            
            # Check if trading is allowed
            can_trade, halt_reason = trading_circuit_breaker.can_trade()
            if not can_trade:
                logger.warning(f"⚠️ Trading halted: {halt_reason}")
                return None

            # Place order with broker
            order_id = await self._place_entry_order(trade)

            if not order_id:
                logger.error(f"❌ Failed to place order for {signal.symbol}")
                trade.status = TradeStatus.FAILED
                await self._save_trade(trade)
                return None

            # Verify order execution (wait up to 10 seconds)
            order_status = await self._verify_order_execution(order_id, timeout=10)

            if order_status == "REJECTED":
                logger.error(f"❌ Order rejected for {signal.symbol}")
                trade.status = TradeStatus.FAILED
                trade.entryOrderDetails = OrderDetails(
                    orderId=order_id,
                    orderStatus="REJECTED",
                    orderTime=datetime.now()
                )
                await self._save_trade(trade)
                return None

            # Update trade with order details
            trade.entryOrderDetails = OrderDetails(
                orderId=order_id,
                orderStatus=order_status,
                orderTime=datetime.now()
            )
            trade.status = TradeStatus.OPEN

            # Add to portfolio
            await self.portfolio.open_position(trade, signal.entryPrice)
            
            # Add to active trades
            self.active_trades[trade.symbol] = trade
            
            # Save to database
            await self._save_trade(trade)
            
            logger.info(
                f"✅ Trade executed: {trade.symbol} x{trade.quantity} @ ₹{trade.entryPrice} "
                f"(SL: ₹{trade.stopLoss}, Target: ₹{trade.target1})"
            )
            
            # Start monitoring if not already running
            if not self.is_monitoring:
                await self.start_monitoring()
            
            return trade
            
        except Exception as e:
            logger.error(f"❌ Error executing signal: {e}")
            return None
    
    async def _place_entry_order(self, trade: TradeModel) -> Optional[str]:
        """Place entry order with broker"""
        try:
            transaction_type = "1" if trade.direction == TradeDirection.BUY else "-1"

            order_id = await self.broker.place_order(
                symbol=trade.symbol,
                transaction_type=transaction_type,
                quantity=trade.quantity,
                order_type=OrderType.MARKET.value
            )

            return order_id

        except Exception as e:
            logger.error(f"❌ Error placing entry order: {e}")
            return None

    async def _verify_order_execution(
        self,
        order_id: str,
        timeout: int = 10
    ) -> str:
        """
        Verify order execution status.

        Args:
            order_id: Order ID to verify
            timeout: Max seconds to wait

        Returns:
            Order status: "FILLED", "PENDING", "REJECTED", or "UNKNOWN"
        """
        try:
            start_time = datetime.now()
            check_interval = 0.5  # Check every 500ms

            while (datetime.now() - start_time).total_seconds() < timeout:
                orders = await self.broker.get_orders()
                order = next((o for o in orders if o.order_id == order_id), None)

                if order:
                    status_val = order.status.value

                    # Check for filled status
                    if status_val in ["COMPLETE", "FILLED", "2"]:
                        logger.info(f"✅ Order {order_id} filled @ ₹{order.average_price}")
                        return "FILLED"

                    # Check for rejection
                    if status_val in ["REJECTED", "CANCELLED", "5", "6"]:
                        logger.error(f"❌ Order {order_id} was rejected")
                        return "REJECTED"

                await asyncio.sleep(check_interval)

            logger.warning(f"⚠️ Order {order_id} verification timeout - assuming filled")
            return "FILLED"  # Assume filled for market orders

        except Exception as e:
            logger.error(f"❌ Error verifying order: {e}")
            return "UNKNOWN"

    async def close_position(
        self,
        symbol: str,
        exit_reason: ExitReason,
        exit_price: Optional[float] = None
    ) -> bool:
        """
        Close an open position.
        
        Args:
            symbol: Stock symbol
            exit_reason: Reason for closing
            exit_price: Exit price (if None, uses current market price)
        
        Returns:
            True if successful
        """
        try:
            if symbol not in self.active_trades:
                logger.warning(f"⚠️ No active trade found for {symbol}")
                return False
            
            trade = self.active_trades[symbol]
            
            # Get current price if not provided
            if exit_price is None:
                exit_price = await self.broker.get_ltp(symbol)
            
            # Place exit order
            transaction_type = "-1" if trade.direction == TradeDirection.BUY else "1"
            
            order_id = await self.broker.place_order(
                symbol=symbol,
                transaction_type=transaction_type,
                quantity=trade.quantity,
                order_type=OrderType.MARKET.value
            )
            
            if not order_id:
                logger.error(f"❌ Failed to place exit order for {symbol}")
                return False
            
            # Calculate P&L
            if trade.direction == TradeDirection.BUY:
                pnl = (exit_price - trade.entryPrice) * trade.quantity
            else:
                pnl = (trade.entryPrice - exit_price) * trade.quantity
            
            pnl_percent = (pnl / (trade.entryPrice * trade.quantity)) * 100
            
            # Update trade
            trade.exitTime = datetime.now()
            trade.exitPrice = exit_price
            trade.exitReason = exit_reason
            trade.pnl = pnl
            trade.pnlPercent = pnl_percent
            trade.netPnl = pnl  # TODO: Subtract charges
            trade.status = TradeStatus.CLOSED
            trade.exitOrderDetails = OrderDetails(
                orderId=order_id,
                orderStatus="PLACED",
                orderTime=datetime.now()
            )
            
            # Update portfolio
            await self.portfolio.close_position(symbol, exit_price, pnl)

            # Remove from active trades
            del self.active_trades[symbol]

            # Record trade in circuit breaker (for daily loss tracking)
            trading_circuit_breaker.record_trade(pnl)

            # Save to database
            await self._save_trade(trade)

            logger.info(
                f"🔒 Position closed: {symbol} @ ₹{exit_price} "
                f"(P&L: ₹{pnl:,.2f} / {pnl_percent:.2f}%, Reason: {exit_reason.value})"
            )

            return True
            
        except Exception as e:
            logger.error(f"❌ Error closing position: {e}")
            return False
    
    async def start_monitoring(self):
        """Start monitoring active positions"""
        if self.is_monitoring:
            logger.warning("⚠️ Monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitor_positions())
        logger.info("👁️ Started position monitoring")
    
    async def stop_monitoring(self):
        """Stop monitoring active positions"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Stopped position monitoring")
    
    async def _monitor_positions(self):
        """
        Monitor active positions for SL/TP.

        IMPORTANT: Monitoring interval is now 2 seconds for faster execution.
        For day trading, quick reaction to SL/TP hits is critical.
        """
        logger.info("👁️ Position monitoring loop started (2s interval)")

        # Monitoring interval in seconds (configurable)
        MONITOR_INTERVAL = 2  # Reduced from 10s to 2s for faster response

        while self.is_monitoring:
            try:
                # Check if trading is halted by circuit breaker
                can_trade, halt_reason = trading_circuit_breaker.can_trade()
                if not can_trade and self.active_trades:
                    logger.warning(f"⚠️ Trading halted: {halt_reason} - closing all positions")
                    await self.close_all_positions(ExitReason.RISK_LIMIT)
                    continue

                if not self.active_trades:
                    await asyncio.sleep(5)
                    continue

                for symbol, trade in list(self.active_trades.items()):
                    # Get current price
                    current_price = await self.broker.get_ltp(symbol)

                    if current_price <= 0:
                        logger.warning(f"⚠️ Invalid price for {symbol}, skipping check")
                        continue

                    # Update portfolio position price
                    await self.portfolio.update_position_price(symbol, current_price)

                    # Check exit conditions
                    position = self.portfolio.portfolio.openPositions.get(symbol)
                    if not position:
                        continue

                    # Check stop loss
                    if position.should_exit_stop_loss():
                        logger.warning(f"🔴 Stop loss hit for {symbol} @ ₹{current_price}")
                        await self.close_position(symbol, ExitReason.STOP_LOSS_HIT, current_price)
                        continue

                    # Check target 1
                    if position.should_exit_target1():
                        logger.info(f"🎯 Target 1 hit for {symbol} @ ₹{current_price}")
                        await self.close_position(symbol, ExitReason.TARGET_1_HIT, current_price)
                        continue

                    # Check target 2
                    if position.should_exit_target2():
                        logger.info(f"🎯 Target 2 hit for {symbol} @ ₹{current_price}")
                        await self.close_position(symbol, ExitReason.TARGET_2_HIT, current_price)
                        continue

                    # Check trailing stop
                    if position.should_exit_trailing_stop():
                        logger.info(f"📉 Trailing stop hit for {symbol} @ ₹{current_price}")
                        await self.close_position(symbol, ExitReason.TRAILING_STOP_HIT, current_price)
                        continue

                # Sleep before next check - faster monitoring
                await asyncio.sleep(MONITOR_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(MONITOR_INTERVAL)

        logger.info("👁️ Position monitoring loop stopped")
    
    async def close_all_positions(self, reason: ExitReason = ExitReason.END_OF_DAY):
        """Close all open positions (e.g., at end of day)"""
        logger.info(f"🔒 Closing all positions (Reason: {reason.value})")
        
        symbols = list(self.active_trades.keys())
        for symbol in symbols:
            await self.close_position(symbol, reason)
        
        logger.info("✅ All positions closed")
    
    async def _save_trade(self, trade: TradeModel):
        """Save trade to database"""
        if not self.db_collection:
            return
        
        try:
            trade_dict = trade.model_dump()
            await self.db_collection.update_one(
                {"tradeId": trade.tradeId},
                {"$set": trade_dict},
                upsert=True
            )
            logger.debug(f"💾 Trade saved: {trade.tradeId}")
        except Exception as e:
            logger.error(f"❌ Error saving trade to DB: {e}")
    
    async def load_active_trades(self):
        """Load active trades from database on startup"""
        if not self.db_collection:
            return
        
        try:
            cursor = self.db_collection.find({"status": TradeStatus.OPEN.value})
            trades = await cursor.to_list(length=100)
            
            for trade_dict in trades:
                trade = TradeModel(**trade_dict)
                self.active_trades[trade.symbol] = trade
                logger.info(f"📂 Loaded active trade: {trade.symbol}")
            
            if self.active_trades:
                await self.start_monitoring()
                
        except Exception as e:
            logger.error(f"❌ Error loading active trades: {e}")

