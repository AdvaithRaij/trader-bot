"""
Risk Management Module for Trading Bot.
Handles position sizing, drawdown limits, maximum trades, and risk controls.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from config import get_config

config = get_config()


@dataclass
class RiskMetrics:
    """Risk metrics for a trading decision."""
    position_size: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    capital_at_risk_pct: float
    is_within_limits: bool
    rejection_reason: Optional[str] = None


@dataclass
class AccountRisk:
    """Account-level risk metrics."""
    total_capital: float
    available_capital: float
    used_capital: float
    daily_pnl: float
    daily_loss_count: int
    max_drawdown_today: float
    active_trades: int
    is_trading_allowed: bool
    risk_status: str


class RiskManager:
    """
    Comprehensive risk management system for the trading bot.
    Enforces position sizing, drawdown limits, and trading rules.
    """
    
    def __init__(self):
        self.config = config
        
        # Risk parameters
        self.initial_capital = config.INITIAL_CAPITAL
        self.max_capital_per_trade = config.MAX_CAPITAL_PER_TRADE
        self.max_active_trades = config.MAX_ACTIVE_TRADES
        self.max_daily_losses = config.MAX_DAILY_LOSSES
        self.max_daily_drawdown = config.MAX_DAILY_DRAWDOWN
        self.min_risk_reward = config.MIN_RISK_REWARD_RATIO
        
        # Current state
        self.daily_trades = []
        self.daily_pnl = 0.0
        self.daily_loss_count = 0
        self.max_drawdown_today = 0.0
        self.start_of_day_capital = self.initial_capital
        
        # Reset daily metrics
        self.last_reset_date = datetime.now().date()
    
    def reset_daily_metrics(self):
        """Reset daily risk metrics at start of new trading day."""
        today = datetime.now().date()
        
        if today != self.last_reset_date:
            logger.info("🔄 Resetting daily risk metrics for new trading day")
            
            self.daily_trades = []
            self.daily_pnl = 0.0
            self.daily_loss_count = 0
            self.max_drawdown_today = 0.0
            self.start_of_day_capital = self.get_current_capital()
            self.last_reset_date = today
    
    def get_current_capital(self) -> float:
        """Get current available capital."""
        # In production, this would query the broker for actual balance
        return self.initial_capital + self.daily_pnl
    
    def calculate_position_size(self, entry_price: float, stop_loss: float,
                              risk_amount: float = None) -> Tuple[int, float]:
        """
        Calculate optimal position size based on risk management rules.
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            risk_amount: Maximum amount to risk (optional)
            
        Returns:
            Tuple of (quantity, actual_risk_amount)
        """
        try:
            current_capital = self.get_current_capital()
            
            # Calculate maximum risk amount if not provided
            if risk_amount is None:
                risk_amount = current_capital * self.max_capital_per_trade
            
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss)
            
            if risk_per_share <= 0:
                logger.warning("Invalid risk per share calculated")
                return 0, 0.0
            
            # Calculate maximum quantity based on risk
            max_quantity = int(risk_amount / risk_per_share)
            
            # Ensure we don't exceed capital limits
            max_value = max_quantity * entry_price
            max_capital_limit = current_capital * 0.9  # Keep 10% buffer
            
            if max_value > max_capital_limit:
                max_quantity = int(max_capital_limit / entry_price)
            
            # Calculate actual risk amount
            actual_risk = max_quantity * risk_per_share
            
            logger.info(f"Position sizing: Qty={max_quantity}, Risk=₹{actual_risk:.2f}")
            
            return max_quantity, actual_risk
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0, 0.0
    
    def validate_trade_risk(self, symbol: str, entry_price: float,
                           stop_loss: float, target_price: float,
                           confidence: float) -> RiskMetrics:
        """
        Validate if a trade meets risk management criteria.
        
        Args:
            symbol: Stock symbol
            entry_price: Proposed entry price
            stop_loss: Proposed stop loss
            target_price: Proposed target price
            confidence: AI confidence in the trade
            
        Returns:
            RiskMetrics object with validation results
        """
        try:
            self.reset_daily_metrics()
            
            # Calculate risk and reward
            risk_per_share = abs(entry_price - stop_loss)
            reward_per_share = abs(target_price - entry_price)
            
            # Calculate risk-reward ratio
            if risk_per_share <= 0:
                return RiskMetrics(
                    position_size=0,
                    risk_amount=0,
                    reward_amount=0,
                    risk_reward_ratio=0,
                    capital_at_risk_pct=0,
                    is_within_limits=False,
                    rejection_reason="Invalid stop loss price"
                )
            
            risk_reward_ratio = reward_per_share / risk_per_share
            
            # Check minimum R:R ratio
            if risk_reward_ratio < self.min_risk_reward:
                return RiskMetrics(
                    position_size=0,
                    risk_amount=0,
                    reward_amount=0,
                    risk_reward_ratio=risk_reward_ratio,
                    capital_at_risk_pct=0,
                    is_within_limits=False,
                    rejection_reason=f"R:R ratio {risk_reward_ratio:.2f} below minimum {self.min_risk_reward}"
                )
            
            # Calculate position size
            quantity, risk_amount = self.calculate_position_size(entry_price, stop_loss)
            
            if quantity <= 0:
                return RiskMetrics(
                    position_size=0,
                    risk_amount=0,
                    reward_amount=0,
                    risk_reward_ratio=risk_reward_ratio,
                    capital_at_risk_pct=0,
                    is_within_limits=False,
                    rejection_reason="Cannot calculate valid position size"
                )
            
            # Calculate metrics
            position_value = quantity * entry_price
            reward_amount = quantity * reward_per_share
            current_capital = self.get_current_capital()
            capital_at_risk_pct = risk_amount / current_capital
            
            # Validate capital at risk
            if capital_at_risk_pct > self.max_capital_per_trade:
                return RiskMetrics(
                    position_size=quantity,
                    risk_amount=risk_amount,
                    reward_amount=reward_amount,
                    risk_reward_ratio=risk_reward_ratio,
                    capital_at_risk_pct=capital_at_risk_pct,
                    is_within_limits=False,
                    rejection_reason=f"Capital at risk {capital_at_risk_pct:.1%} exceeds limit {self.max_capital_per_trade:.1%}"
                )
            
            return RiskMetrics(
                position_size=quantity,
                risk_amount=risk_amount,
                reward_amount=reward_amount,
                risk_reward_ratio=risk_reward_ratio,
                capital_at_risk_pct=capital_at_risk_pct,
                is_within_limits=True
            )
            
        except Exception as e:
            logger.error(f"Error validating trade risk for {symbol}: {e}")
            return RiskMetrics(
                position_size=0,
                risk_amount=0,
                reward_amount=0,
                risk_reward_ratio=0,
                capital_at_risk_pct=0,
                is_within_limits=False,
                rejection_reason=f"Error in risk validation: {e}"
            )
    
    def check_trading_allowed(self, active_positions: Dict) -> AccountRisk:
        """
        Check if new trading is allowed based on current risk state.
        
        Args:
            active_positions: Current active positions
            
        Returns:
            AccountRisk object with current risk status
        """
        try:
            self.reset_daily_metrics()
            
            current_capital = self.get_current_capital()
            active_trades = len(active_positions)
            
            # Calculate unrealized P&L
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in active_positions.values())
            
            # Update daily P&L
            self.daily_pnl = total_unrealized_pnl
            
            # Calculate drawdown
            if current_capital < self.start_of_day_capital:
                current_drawdown = (self.start_of_day_capital - current_capital) / self.start_of_day_capital
                self.max_drawdown_today = max(self.max_drawdown_today, current_drawdown)
            
            # Determine trading status
            is_trading_allowed = True
            risk_status = "NORMAL"
            
            # Check maximum active trades
            if active_trades >= self.max_active_trades:
                is_trading_allowed = False
                risk_status = "MAX_TRADES_REACHED"
            
            # Check daily loss limit
            elif self.daily_loss_count >= self.max_daily_losses:
                is_trading_allowed = False
                risk_status = "MAX_DAILY_LOSSES"
            
            # Check drawdown limit
            elif self.max_drawdown_today >= self.max_daily_drawdown:
                is_trading_allowed = False
                risk_status = "MAX_DRAWDOWN_EXCEEDED"
            
            # Check if near market close
            elif self.is_near_market_close():
                is_trading_allowed = False
                risk_status = "NEAR_MARKET_CLOSE"
            
            return AccountRisk(
                total_capital=self.initial_capital,
                available_capital=current_capital,
                used_capital=self.initial_capital - current_capital,
                daily_pnl=self.daily_pnl,
                daily_loss_count=self.daily_loss_count,
                max_drawdown_today=self.max_drawdown_today,
                active_trades=active_trades,
                is_trading_allowed=is_trading_allowed,
                risk_status=risk_status
            )
            
        except Exception as e:
            logger.error(f"Error checking trading allowed: {e}")
            return AccountRisk(
                total_capital=self.initial_capital,
                available_capital=0,
                used_capital=0,
                daily_pnl=0,
                daily_loss_count=999,  # Force stop trading
                max_drawdown_today=1.0,
                active_trades=0,
                is_trading_allowed=False,
                risk_status="ERROR"
            )
    
    def is_near_market_close(self) -> bool:
        """Check if we're near market close time."""
        now = datetime.now()
        
        # Don't trade after 3:00 PM IST
        if now.hour >= 15:
            return True
        
        # Don't trade in last 10 minutes before 3:10 PM
        close_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
        time_to_close = close_time - now
        
        return time_to_close.total_seconds() < 600  # 10 minutes
    
    def record_trade_outcome(self, symbol: str, entry_price: float,
                           exit_price: float, quantity: int,
                           transaction_type: str) -> Dict:
        """
        Record trade outcome for risk tracking.
        
        Args:
            symbol: Stock symbol
            entry_price: Entry price
            exit_price: Exit price
            quantity: Quantity traded
            transaction_type: BUY or SELL
            
        Returns:
            Trade outcome summary
        """
        try:
            # Calculate P&L
            if transaction_type == "BUY":
                pnl = (exit_price - entry_price) * quantity
            else:
                pnl = (entry_price - exit_price) * quantity
            
            # Calculate percentage return
            pnl_pct = (pnl / (entry_price * quantity)) * 100
            
            # Record trade
            trade_record = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'transaction_type': transaction_type,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'is_loss': pnl < 0
            }
            
            self.daily_trades.append(trade_record)
            self.daily_pnl += pnl
            
            # Update loss count
            if pnl < 0:
                self.daily_loss_count += 1
                logger.warning(f"📉 Loss recorded: {symbol} - ₹{pnl:.2f} ({pnl_pct:.2f}%)")
            else:
                logger.info(f"📈 Profit recorded: {symbol} - ₹{pnl:.2f} ({pnl_pct:.2f}%)")
            
            return trade_record
            
        except Exception as e:
            logger.error(f"Error recording trade outcome: {e}")
            return {}
    
    def get_risk_summary(self) -> Dict:
        """
        Get comprehensive risk summary.
        
        Returns:
            Risk summary dictionary
        """
        try:
            self.reset_daily_metrics()
            
            # Calculate trade statistics
            total_trades = len(self.daily_trades)
            winning_trades = len([t for t in self.daily_trades if t['pnl'] > 0])
            losing_trades = len([t for t in self.daily_trades if t['pnl'] < 0])
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate average P&L
            if self.daily_trades:
                avg_pnl = sum(t['pnl'] for t in self.daily_trades) / total_trades
                avg_win = sum(t['pnl'] for t in self.daily_trades if t['pnl'] > 0) / max(winning_trades, 1)
                avg_loss = sum(t['pnl'] for t in self.daily_trades if t['pnl'] < 0) / max(losing_trades, 1)
            else:
                avg_pnl = avg_win = avg_loss = 0
            
            return {
                'daily_pnl': self.daily_pnl,
                'daily_loss_count': self.daily_loss_count,
                'max_drawdown_today': self.max_drawdown_today,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate_pct': win_rate,
                'avg_pnl': avg_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'current_capital': self.get_current_capital(),
                'capital_change_pct': (self.daily_pnl / self.initial_capital) * 100,
                'risk_status': self.get_current_risk_status()
            }
            
        except Exception as e:
            logger.error(f"Error getting risk summary: {e}")
            return {}
    
    def get_current_risk_status(self) -> str:
        """Get current risk status description."""
        if self.daily_loss_count >= self.max_daily_losses:
            return "STOPPED - Max daily losses reached"
        elif self.max_drawdown_today >= self.max_daily_drawdown:
            return "STOPPED - Max drawdown exceeded"
        elif self.is_near_market_close():
            return "STOPPING - Near market close"
        elif self.daily_loss_count >= self.max_daily_losses * 0.7:
            return "CAUTION - Approaching loss limit"
        elif self.max_drawdown_today >= self.max_daily_drawdown * 0.7:
            return "CAUTION - Approaching drawdown limit"
        else:
            return "NORMAL - Trading allowed"
    
    def should_force_exit_all(self) -> bool:
        """Check if we should force exit all positions."""
        now = datetime.now()
        
        # Force exit at 3:10 PM
        if now.hour >= 15 and now.minute >= 10:
            return True
        
        # Force exit if max drawdown exceeded
        if self.max_drawdown_today >= self.max_daily_drawdown:
            return True
        
        # Force exit if too many losses
        if self.daily_loss_count >= self.max_daily_losses:
            return True
        
        return False


# Global risk manager instance
risk_manager = RiskManager()


def get_risk_manager() -> RiskManager:
    """Get the global risk manager instance."""
    return risk_manager


if __name__ == "__main__":
    # Test the risk manager
    def test_risk_manager():
        try:
            rm = RiskManager()
            
            print("🛡️ Testing Risk Manager")
            
            # Test position sizing
            quantity, risk = rm.calculate_position_size(
                entry_price=2500.0,
                stop_loss=2450.0
            )
            print(f"Position sizing: {quantity} shares, Risk: ₹{risk:.2f}")
            
            # Test trade validation
            risk_metrics = rm.validate_trade_risk(
                symbol="RELIANCE",
                entry_price=2500.0,
                stop_loss=2450.0,
                target_price=2600.0,
                confidence=0.8
            )
            
            print(f"Trade validation: {risk_metrics}")
            
            # Test trading status
            account_risk = rm.check_trading_allowed({})
            print(f"Trading allowed: {account_risk.is_trading_allowed}")
            print(f"Risk status: {account_risk.risk_status}")
            
            # Test trade recording
            trade_outcome = rm.record_trade_outcome(
                symbol="RELIANCE",
                entry_price=2500.0,
                exit_price=2550.0,
                quantity=10,
                transaction_type="BUY"
            )
            print(f"Trade outcome: ₹{trade_outcome.get('pnl', 0):.2f}")
            
            # Get risk summary
            summary = rm.get_risk_summary()
            print(f"Risk Summary: {summary}")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    test_risk_manager()
