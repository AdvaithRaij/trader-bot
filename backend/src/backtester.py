"""
Backtesting Framework for Strategy Testing

Tests strategies on historical data to evaluate performance before live trading.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from loguru import logger
import asyncio

from config import get_config
from broker_fyers import broker
from models.strategy import StrategyModel, StockPickingType
from models.trade import TradeDirection


class BacktestTrade(BaseModel):
    """Represents a simulated trade during backtesting"""
    symbol: str
    direction: TradeDirection
    entryDate: str
    entryPrice: float
    exitDate: Optional[str] = None
    exitPrice: Optional[float] = None
    quantity: int
    stopLoss: float
    target1: float
    target2: Optional[float] = None
    pnl: float = 0.0
    pnlPercent: float = 0.0
    exitReason: Optional[str] = None
    isOpen: bool = True


class BacktestResult(BaseModel):
    """Results from a backtest run"""
    strategyId: str
    strategyName: str
    startDate: str
    endDate: str
    initialCapital: float
    finalCapital: float
    totalPnl: float
    totalPnlPercent: float
    totalTrades: int
    winningTrades: int
    losingTrades: int
    winRate: float
    avgWin: float
    avgLoss: float
    maxDrawdown: float
    maxDrawdownPercent: float
    sharpeRatio: float
    profitFactor: float
    trades: List[BacktestTrade]


class Backtester:
    """
    Backtesting engine for strategy evaluation.

    Usage:
        backtester = Backtester(
            strategy_id="news_momentum_v1",
            start_date="2024-01-01",
            end_date="2024-11-01",
            initial_capital=100000,
            db_collection=db.strategies  # MongoDB collection
        )
        results = await backtester.run()
    """

    def __init__(
        self,
        strategy_id: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000,
        slippage_percent: float = 0.1,
        commission_per_trade: float = 20,
        db_collection=None
    ):
        self.strategy_id = strategy_id
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.initial_capital = initial_capital
        self.slippage_percent = slippage_percent
        self.commission_per_trade = commission_per_trade
        self.db_collection = db_collection

        self.config = get_config()
        self.strategy: Optional[StrategyModel] = None
        self.trades: List[BacktestTrade] = []
        self.capital = initial_capital
        self.peak_capital = initial_capital
        self.max_drawdown = 0.0

        logger.info(f"📊 Backtester initialized for {strategy_id}")
        logger.info(f"   Period: {start_date} to {end_date}")
        logger.info(f"   Capital: ₹{initial_capital:,.2f}")
    
    async def run(self, symbols: Optional[List[str]] = None) -> BacktestResult:
        """
        Run the backtest simulation.
        
        Args:
            symbols: List of symbols to test (optional, uses strategy defaults)
            
        Returns:
            BacktestResult with performance metrics
        """
        try:
            logger.info(f"🚀 Starting backtest for {self.strategy_id}")

            # Load strategy from database
            from strategy_manager import StrategyManager
            strategy_manager = StrategyManager(db_collection=self.db_collection)
            self.strategy = await strategy_manager.get_strategy(self.strategy_id)

            if not self.strategy:
                raise ValueError(f"Strategy {self.strategy_id} not found. Make sure MongoDB is connected and strategies are seeded.")
            
            # Get symbols to test
            test_symbols = symbols or self.strategy.stockPicking.allowedSymbols or [
                'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK'
            ]
            
            logger.info(f"📈 Testing on symbols: {test_symbols}")
            
            # Get historical data for each symbol
            for symbol in test_symbols:
                await self._backtest_symbol(symbol)
            
            # Calculate final metrics
            result = self._calculate_results()
            
            logger.info(f"✅ Backtest complete: {result.totalTrades} trades, "
                       f"P&L: ₹{result.totalPnl:,.2f} ({result.totalPnlPercent:.2f}%)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Backtest error: {e}")
            raise
    
    async def _backtest_symbol(self, symbol: str):
        """Run backtest for a single symbol"""
        try:
            # Calculate days between start and end
            days = (self.end_date - self.start_date).days

            # Get historical data
            historical_data = await broker.get_historical_data(symbol, days)

            if not historical_data:
                logger.warning(f"⚠️ No historical data for {symbol}")
                return

            logger.info(f"📊 Processing {len(historical_data)} candles for {symbol}")

            # Simulate trading through each day
            # Pass historical context for moving average calculations
            for i, candle in enumerate(historical_data):
                past_candles = historical_data[max(0, i-20):i+1]  # Last 20 candles for MA
                await self._process_candle(symbol, candle, past_candles)

        except Exception as e:
            logger.error(f"❌ Error backtesting {symbol}: {e}")

    async def _process_candle(
        self,
        symbol: str,
        candle: Dict,
        past_candles: List[Dict]
    ):
        """Process a single candle and check for trade opportunities"""

        # Check existing open trades for exits
        for trade in self.trades:
            if trade.symbol == symbol and trade.isOpen:
                self._check_exit(trade, candle)

        # Check for new entry signals with historical context
        if self._should_enter(symbol, candle, past_candles):
            self._enter_trade(symbol, candle)

    def _should_enter(
        self,
        symbol: str,
        candle: Dict,
        past_candles: List[Dict] = None
    ) -> bool:
        """
        Check if we should enter a trade based on strategy rules.

        Uses multiple technical conditions for more realistic backtesting:
        1. Bullish candle (close > open)
        2. Volume confirmation (if available)
        3. Price above moving average (trend confirmation)
        4. Not already in a position
        5. Sufficient capital
        """
        # Check if we already have an open position
        open_positions = [t for t in self.trades if t.symbol == symbol and t.isOpen]
        if open_positions:
            return False

        # Check capital availability
        max_per_trade = self.config.MAX_CAPITAL_PER_TRADE
        position_size = self.capital * max_per_trade
        if position_size < 500:  # Minimum ₹500 per trade
            return False

        # Technical conditions for entry
        close = candle.get('close', 0)
        open_price = candle.get('open', 0)
        high = candle.get('high', 0)
        low = candle.get('low', 0)
        volume = candle.get('volume', 0)

        if close <= 0 or open_price <= 0:
            return False

        # Condition 1: Bullish candle
        is_bullish = close > open_price

        # Condition 2: Strong body (body is at least 50% of candle range)
        body = abs(close - open_price)
        candle_range = high - low
        strong_body = (body / candle_range) >= 0.5 if candle_range > 0 else False

        # Condition 3: Not a doji (indecision candle)
        not_doji = (body / open_price) > 0.001

        # Condition 4: Volume above minimum (if available)
        has_volume = volume > 10000 if volume > 0 else True

        # Condition 5: Price above 10-period moving average (trend confirmation)
        above_ma = True
        if past_candles and len(past_candles) >= 10:
            closes = [c.get('close', 0) for c in past_candles[-10:]]
            ma_10 = sum(closes) / len(closes) if closes else 0
            above_ma = close > ma_10

        # Entry signal: All conditions must be met
        if is_bullish and strong_body and not_doji and has_volume and above_ma:
            return True

        return False

    def _enter_trade(self, symbol: str, candle: Dict):
        """Enter a new trade"""
        entry_price = candle['close'] * (1 + self.slippage_percent / 100)

        # Calculate position size (10% of capital)
        position_value = self.capital * 0.1
        quantity = int(position_value / entry_price)

        if quantity < 1:
            return

        # Calculate levels from strategy
        sl_percent = self.strategy.execution.stopLossPercent or 2.0
        tp1_percent = self.strategy.execution.target1Percent or 3.0
        tp2_percent = self.strategy.execution.target2Percent or 5.0

        stop_loss = entry_price * (1 - sl_percent / 100)
        target1 = entry_price * (1 + tp1_percent / 100)
        target2 = entry_price * (1 + tp2_percent / 100)

        trade = BacktestTrade(
            symbol=symbol,
            direction=TradeDirection.BUY,
            entryDate=candle['date'],
            entryPrice=entry_price,
            quantity=quantity,
            stopLoss=stop_loss,
            target1=target1,
            target2=target2
        )

        self.trades.append(trade)
        self.capital -= (entry_price * quantity + self.commission_per_trade)

        logger.debug(f"📈 ENTRY: {symbol} @ ₹{entry_price:.2f} x {quantity}")

    def _check_exit(self, trade: BacktestTrade, candle: Dict):
        """Check if trade should be exited"""
        high = candle['high']
        low = candle['low']
        close = candle['close']

        exit_price = None
        exit_reason = None

        # Check stop loss hit
        if low <= trade.stopLoss:
            exit_price = trade.stopLoss * (1 - self.slippage_percent / 100)
            exit_reason = "STOP_LOSS"

        # Check target 1 hit
        elif high >= trade.target1:
            exit_price = trade.target1 * (1 - self.slippage_percent / 100)
            exit_reason = "TARGET_1"

        # Check target 2 hit
        elif trade.target2 and high >= trade.target2:
            exit_price = trade.target2 * (1 - self.slippage_percent / 100)
            exit_reason = "TARGET_2"

        if exit_price:
            self._exit_trade(trade, exit_price, candle['date'], exit_reason)

    def _exit_trade(self, trade: BacktestTrade, exit_price: float, exit_date: str, reason: str):
        """Exit a trade and calculate P&L"""
        trade.exitPrice = exit_price
        trade.exitDate = exit_date
        trade.exitReason = reason
        trade.isOpen = False

        # Calculate P&L
        if trade.direction == TradeDirection.BUY:
            trade.pnl = (exit_price - trade.entryPrice) * trade.quantity - self.commission_per_trade
        else:
            trade.pnl = (trade.entryPrice - exit_price) * trade.quantity - self.commission_per_trade

        trade.pnlPercent = (trade.pnl / (trade.entryPrice * trade.quantity)) * 100

        # Update capital
        self.capital += (exit_price * trade.quantity)

        # Track drawdown
        if self.capital > self.peak_capital:
            self.peak_capital = self.capital
        else:
            drawdown = self.peak_capital - self.capital
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown

        logger.debug(f"📉 EXIT: {trade.symbol} @ ₹{exit_price:.2f} | P&L: ₹{trade.pnl:.2f} ({reason})")

    def _calculate_results(self) -> BacktestResult:
        """Calculate final backtest metrics"""
        # Close any remaining open trades at last price
        for trade in self.trades:
            if trade.isOpen:
                trade.exitReason = "END_OF_BACKTEST"
                trade.isOpen = False

        # Calculate metrics
        closed_trades = [t for t in self.trades if not t.isOpen or t.exitReason]
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl <= 0]

        total_pnl = sum(t.pnl for t in closed_trades)
        win_rate = len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0

        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0

        profit_factor = abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades and sum(t.pnl for t in losing_trades) != 0 else 0

        # Simplified Sharpe ratio calculation
        returns = [t.pnlPercent for t in closed_trades]
        if returns:
            import statistics
            avg_return = statistics.mean(returns)
            std_return = statistics.stdev(returns) if len(returns) > 1 else 1
            sharpe_ratio = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
        else:
            sharpe_ratio = 0

        return BacktestResult(
            strategyId=self.strategy_id,
            strategyName=self.strategy.name if self.strategy else self.strategy_id,
            startDate=self.start_date.strftime("%Y-%m-%d"),
            endDate=self.end_date.strftime("%Y-%m-%d"),
            initialCapital=self.initial_capital,
            finalCapital=self.capital,
            totalPnl=total_pnl,
            totalPnlPercent=(total_pnl / self.initial_capital) * 100,
            totalTrades=len(closed_trades),
            winningTrades=len(winning_trades),
            losingTrades=len(losing_trades),
            winRate=win_rate,
            avgWin=avg_win,
            avgLoss=avg_loss,
            maxDrawdown=self.max_drawdown,
            maxDrawdownPercent=(self.max_drawdown / self.peak_capital) * 100 if self.peak_capital > 0 else 0,
            sharpeRatio=sharpe_ratio,
            profitFactor=profit_factor,
            trades=self.trades
        )

