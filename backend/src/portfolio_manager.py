"""
Portfolio Manager - Manages capital allocation, positions, and risk limits.
"""
import asyncio
from datetime import datetime, date
from typing import Dict, Optional, List
from loguru import logger

from models import (
    PortfolioModel,
    PortfolioPosition,
    TradeSignal,
    TradeModel,
    DailyPerformance
)


class PortfolioManager:
    """
    Manages trading portfolio with capital allocation and risk management.
    
    Responsibilities:
    - Track total capital and available cash
    - Manage open positions
    - Calculate position sizes based on risk
    - Enforce risk limits (max positions, daily loss, drawdown)
    - Update P&L in real-time
    - Persist portfolio state to MongoDB
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        max_position_size_percent: float = 20.0,
        max_daily_loss_percent: float = 5.0,
        max_drawdown_percent: float = 10.0,
        max_open_positions: int = 5,
        db_collection=None
    ):
        """
        Initialize Portfolio Manager.
        
        Args:
            initial_capital: Starting capital in rupees
            max_position_size_percent: Max % of capital per position
            max_daily_loss_percent: Max daily loss % (stop trading if hit)
            max_drawdown_percent: Max drawdown % from peak
            max_open_positions: Max concurrent positions
            db_collection: MongoDB collection for persistence
        """
        self.initial_capital = initial_capital
        self.max_position_size_percent = max_position_size_percent
        self.max_daily_loss_percent = max_daily_loss_percent
        self.max_drawdown_percent = max_drawdown_percent
        self.max_open_positions = max_open_positions
        self.db_collection = db_collection
        
        # Initialize portfolio state
        self.portfolio = PortfolioModel(
            initialCapital=initial_capital,
            currentCapital=initial_capital,
            availableCapital=initial_capital,
            peakCapital=initial_capital
        )
        
        logger.info(f"💼 Portfolio Manager initialized with ₹{initial_capital:,.2f}")
    
    async def load_from_db(self) -> bool:
        """Load portfolio state from MongoDB"""
        if self.db_collection is None:
            logger.warning("No database collection configured")
            return False
        
        try:
            portfolio_data = await self.db_collection.find_one({"portfolioId": "main"})
            if portfolio_data:
                self.portfolio = PortfolioModel(**portfolio_data)
                logger.info(f"📂 Loaded portfolio from DB: ₹{self.portfolio.currentCapital:,.2f}")
                return True
            else:
                logger.info("📂 No existing portfolio found, using new portfolio")
                await self.save_to_db()
                return True
        except Exception as e:
            logger.error(f"❌ Error loading portfolio from DB: {e}")
            return False
    
    async def save_to_db(self):
        """Save portfolio state to MongoDB"""
        if self.db_collection is None:
            return
        
        try:
            portfolio_dict = self.portfolio.model_dump()
            await self.db_collection.update_one(
                {"portfolioId": "main"},
                {"$set": portfolio_dict},
                upsert=True
            )
            logger.debug("💾 Portfolio saved to DB")
        except Exception as e:
            logger.error(f"❌ Error saving portfolio to DB: {e}")
    
    def calculate_position_size(
        self,
        signal: TradeSignal,
        current_price: float,
        atr: float = None
    ) -> tuple[int, float]:
        """
        Calculate position size based on available capital, risk limits, and volatility.

        Uses ATR-based position sizing when ATR is provided:
        - Higher volatility (ATR) = smaller position size
        - Lower volatility (ATR) = larger position size

        Args:
            signal: Trade signal with entry and stop loss
            current_price: Current market price
            atr: Average True Range (optional, for volatility adjustment)

        Returns:
            (quantity, allocated_capital) tuple
        """
        # Calculate max capital for this position
        max_capital = self.portfolio.currentCapital * (self.max_position_size_percent / 100)

        # Use available capital (can't exceed what we have)
        allocated_capital = min(max_capital, self.portfolio.availableCapital)

        # ATR-based volatility adjustment
        if atr and atr > 0 and signal.entryPrice > 0:
            # Calculate ATR as percentage of price
            atr_percent = (atr / signal.entryPrice) * 100

            # Volatility adjustment factor:
            # - If ATR% < 1.5%, use full position (low volatility)
            # - If ATR% > 3%, reduce position by 50% (high volatility)
            # - Linear interpolation between
            if atr_percent <= 1.5:
                volatility_factor = 1.0
            elif atr_percent >= 3.0:
                volatility_factor = 0.5
            else:
                # Linear interpolation: 1.0 at 1.5%, 0.5 at 3%
                volatility_factor = 1.0 - ((atr_percent - 1.5) / 1.5) * 0.5

            allocated_capital = allocated_capital * volatility_factor
            logger.info(f"📊 ATR adjustment: {atr_percent:.2f}% → factor {volatility_factor:.2f}")

        # Risk-based position sizing using stop loss
        if signal.stopLoss and signal.stopLoss > 0:
            risk_per_share = abs(signal.entryPrice - signal.stopLoss)
            if risk_per_share > 0:
                # Risk 1% of capital per trade
                max_risk = self.portfolio.currentCapital * 0.01
                risk_based_quantity = int(max_risk / risk_per_share)

                # Use the smaller of capital-based and risk-based quantity
                capital_based_quantity = int(allocated_capital / signal.entryPrice)
                quantity = min(capital_based_quantity, risk_based_quantity)

                logger.info(
                    f"📊 Risk-based sizing: risk/share=₹{risk_per_share:.2f}, "
                    f"max_risk=₹{max_risk:.2f}, qty={quantity}"
                )
            else:
                quantity = int(allocated_capital / signal.entryPrice)
        else:
            # Fallback to simple capital-based sizing
            quantity = int(allocated_capital / signal.entryPrice)

        # Ensure minimum quantity
        quantity = max(quantity, 0)

        # Recalculate actual allocated capital
        actual_allocated = quantity * signal.entryPrice

        logger.info(
            f"📊 Position size for {signal.symbol}: "
            f"{quantity} shares @ ₹{signal.entryPrice} = ₹{actual_allocated:,.2f}"
        )

        return quantity, actual_allocated
    
    def can_open_position(
        self,
        symbol: str,
        required_capital: float
    ) -> tuple[bool, str]:
        """
        Check if we can open a new position.
        
        Args:
            symbol: Stock symbol
            required_capital: Capital needed for position
        
        Returns:
            (can_open, reason) tuple
        """
        # Check if trading is enabled
        if not self.portfolio.tradingEnabled:
            return False, "Trading is disabled (risk limits hit)"
        
        # Check daily loss limit
        if self.portfolio.dailyLossLimitHit:
            return False, f"Daily loss limit hit ({self.max_daily_loss_percent}%)"
        
        # Check drawdown limit
        if self.portfolio.drawdownLimitHit:
            return False, f"Drawdown limit hit ({self.max_drawdown_percent}%)"
        
        # Check max positions
        if len(self.portfolio.openPositions) >= self.max_open_positions:
            return False, f"Max positions limit reached ({self.max_open_positions})"
        
        # Check if already have position in this symbol
        if symbol in self.portfolio.openPositions:
            return False, f"Already have open position in {symbol}"
        
        # Check available capital
        if required_capital > self.portfolio.availableCapital:
            return False, f"Insufficient capital (need ₹{required_capital:,.2f}, have ₹{self.portfolio.availableCapital:,.2f})"
        
        return True, "OK"
    
    async def open_position(
        self,
        trade: TradeModel,
        current_price: float
    ):
        """
        Open a new position in the portfolio.
        
        Args:
            trade: Trade model with entry details
            current_price: Current market price
        """
        allocated_capital = trade.quantity * trade.entryPrice
        
        position = PortfolioPosition(
            symbol=trade.symbol,
            tradeId=trade.tradeId,
            quantity=trade.quantity,
            entryPrice=trade.entryPrice,
            currentPrice=current_price,
            stopLoss=trade.stopLoss,
            target1=trade.target1,
            target2=trade.target2,
            unrealizedPnl=0.0,
            unrealizedPnlPercent=0.0,
            allocatedCapital=allocated_capital,
            strategyId=trade.strategyId,
            entryTime=trade.entryTime
        )
        
        # Add to open positions
        self.portfolio.openPositions[trade.symbol] = position
        
        # Update capital
        self.portfolio.availableCapital -= allocated_capital
        self.portfolio.allocatedCapital += allocated_capital
        
        # Update metrics
        self.portfolio.update_metrics()
        self.portfolio.lastTradeTime = datetime.now()
        
        await self.save_to_db()
        
        logger.info(
            f"✅ Opened position: {trade.symbol} x{trade.quantity} @ ₹{trade.entryPrice} "
            f"(Allocated: ₹{allocated_capital:,.2f}, Available: ₹{self.portfolio.availableCapital:,.2f})"
        )
    
    async def close_position(
        self,
        symbol: str,
        exit_price: float,
        realized_pnl: float
    ):
        """
        Close an existing position.
        
        Args:
            symbol: Stock symbol
            exit_price: Exit price
            realized_pnl: Realized P&L from the trade
        """
        if symbol not in self.portfolio.openPositions:
            logger.warning(f"⚠️ Cannot close position: {symbol} not in open positions")
            return
        
        position = self.portfolio.openPositions[symbol]
        
        # Release capital
        self.portfolio.availableCapital += position.allocatedCapital
        self.portfolio.allocatedCapital -= position.allocatedCapital
        
        # Update P&L
        self.portfolio.totalRealizedPnl += realized_pnl
        self.portfolio.todayRealizedPnl += realized_pnl
        
        # Update trade statistics
        self.portfolio.totalTrades += 1
        if realized_pnl > 0:
            self.portfolio.winningTrades += 1
        else:
            self.portfolio.losingTrades += 1
        
        # Remove from open positions
        del self.portfolio.openPositions[symbol]
        
        # Update metrics
        self.portfolio.update_metrics()
        
        # Check risk limits
        await self._check_risk_limits()
        
        await self.save_to_db()
        
        logger.info(
            f"🔒 Closed position: {symbol} @ ₹{exit_price} "
            f"(P&L: ₹{realized_pnl:,.2f}, Available: ₹{self.portfolio.availableCapital:,.2f})"
        )
    
    async def update_position_price(
        self,
        symbol: str,
        current_price: float
    ):
        """
        Update current price for a position and recalculate P&L.
        
        Args:
            symbol: Stock symbol
            current_price: Current market price
        """
        if symbol not in self.portfolio.openPositions:
            return
        
        position = self.portfolio.openPositions[symbol]
        position.currentPrice = current_price
        position.unrealizedPnl = (current_price - position.entryPrice) * position.quantity
        position.unrealizedPnlPercent = ((current_price - position.entryPrice) / position.entryPrice) * 100
        
        # Update portfolio metrics
        self.portfolio.update_metrics()
    
    async def _check_risk_limits(self):
        """Check and enforce risk limits"""
        # Check daily loss limit
        daily_loss_percent = (self.portfolio.todayRealizedPnl / self.initial_capital) * 100
        if daily_loss_percent <= -self.max_daily_loss_percent:
            self.portfolio.dailyLossLimitHit = True
            self.portfolio.tradingEnabled = False
            logger.warning(
                f"🚨 DAILY LOSS LIMIT HIT: {daily_loss_percent:.2f}% "
                f"(Limit: {self.max_daily_loss_percent}%)"
            )
        
        # Check drawdown limit
        if self.portfolio.currentDrawdown >= self.max_drawdown_percent:
            self.portfolio.drawdownLimitHit = True
            self.portfolio.tradingEnabled = False
            logger.warning(
                f"🚨 DRAWDOWN LIMIT HIT: {self.portfolio.currentDrawdown:.2f}% "
                f"(Limit: {self.max_drawdown_percent}%)"
            )
    
    async def reset_daily_limits(self):
        """Reset daily limits (call at start of new trading day)"""
        self.portfolio.todayRealizedPnl = 0.0
        self.portfolio.todayUnrealizedPnl = 0.0
        self.portfolio.dailyLossLimitHit = False
        
        # Re-enable trading if only daily limit was hit (not drawdown)
        if not self.portfolio.drawdownLimitHit:
            self.portfolio.tradingEnabled = True
        
        logger.info("🌅 Daily limits reset for new trading day")
        await self.save_to_db()
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary for API/UI"""
        return {
            "totalCapital": self.portfolio.currentCapital,
            "availableCapital": self.portfolio.availableCapital,
            "allocatedCapital": self.portfolio.allocatedCapital,
            "totalRealizedPnl": self.portfolio.totalRealizedPnl,
            "totalUnrealizedPnl": self.portfolio.totalUnrealizedPnl,
            "todayPnl": self.portfolio.todayRealizedPnl + self.portfolio.todayUnrealizedPnl,
            "openPositions": len(self.portfolio.openPositions),
            "totalTrades": self.portfolio.totalTrades,
            "winRate": self.portfolio.winRate,
            "currentDrawdown": self.portfolio.currentDrawdown,
            "tradingEnabled": self.portfolio.tradingEnabled
        }

