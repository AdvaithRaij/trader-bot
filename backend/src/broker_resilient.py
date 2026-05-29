"""
Resilient Broker Wrapper - Adds retry logic, circuit breaker, and error recovery.
Wraps the FyersBroker to make it production-ready.
"""
import asyncio
import functools
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Callable, Any
from enum import Enum
from loguru import logger

from config import get_config

config = get_config()


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing - reject calls
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascading failures by stopping calls to a failing service.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
    
    def can_execute(self) -> bool:
        """Check if we can execute a call."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info("🔌 Circuit breaker: HALF_OPEN - Testing recovery")
                    return True
            return False
        
        # HALF_OPEN - allow limited calls
        return self.half_open_calls < self.half_open_max_calls
    
    def record_success(self):
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("✅ Circuit breaker: CLOSED - Service recovered")
        else:
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("🔴 Circuit breaker: OPEN - Recovery failed")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"🔴 Circuit breaker: OPEN - {self.failure_count} failures")
    
    def reset(self):
        """Reset the circuit breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0
):
    """
    Decorator for adding retry logic with exponential backoff.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.warning(
                            f"⚠️ {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"❌ {func.__name__} failed after {max_retries + 1} attempts: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


class TradingCircuitBreaker:
    """
    Emergency trading circuit breaker.
    Monitors losses and halts trading if thresholds are exceeded.
    """
    
    def __init__(self):
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.is_halted = False
        self.halt_reason = ""
        self.last_reset_date = datetime.now().date()
        
        # Thresholds from config
        self.max_daily_loss = config.INITIAL_CAPITAL * config.MAX_DAILY_DRAWDOWN
        self.max_daily_trades = 20
        self.max_consecutive_losses = config.MAX_DAILY_LOSSES
    
    def reset_daily(self):
        """Reset daily counters at market open."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_loss = 0.0
            self.daily_trades = 0
            self.consecutive_losses = 0
            self.is_halted = False
            self.halt_reason = ""
            self.last_reset_date = today
            logger.info("📊 Daily trading limits reset")

    def record_trade(self, pnl: float):
        """Record a completed trade and check thresholds."""
        self.reset_daily()  # Ensure daily reset

        self.daily_trades += 1
        self.daily_loss += min(0, pnl)  # Only count losses

        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        # Check thresholds
        self._check_thresholds()

    def _check_thresholds(self):
        """Check if any trading thresholds are breached."""
        if abs(self.daily_loss) >= self.max_daily_loss:
            self.halt_trading(f"Daily loss limit exceeded: ₹{abs(self.daily_loss):,.2f}")

        if self.consecutive_losses >= self.max_consecutive_losses:
            self.halt_trading(f"Consecutive losses limit: {self.consecutive_losses} losses")

        if self.daily_trades >= self.max_daily_trades:
            self.halt_trading(f"Daily trade limit exceeded: {self.daily_trades} trades")

    def halt_trading(self, reason: str):
        """Halt all trading."""
        self.is_halted = True
        self.halt_reason = reason
        logger.error(f"🛑 TRADING HALTED: {reason}")

    def can_trade(self) -> tuple[bool, str]:
        """Check if trading is allowed."""
        self.reset_daily()
        if self.is_halted:
            return False, self.halt_reason
        return True, ""

    def force_resume(self):
        """Manually resume trading (for emergency override)."""
        self.is_halted = False
        self.halt_reason = ""
        logger.warning("⚠️ Trading manually resumed - use with caution!")

    def get_status(self) -> Dict:
        """Get current circuit breaker status."""
        return {
            "is_halted": self.is_halted,
            "halt_reason": self.halt_reason,
            "daily_loss": self.daily_loss,
            "daily_trades": self.daily_trades,
            "consecutive_losses": self.consecutive_losses,
            "max_daily_loss": self.max_daily_loss,
            "max_consecutive_losses": self.max_consecutive_losses,
            "remaining_loss_budget": self.max_daily_loss - abs(self.daily_loss),
            "remaining_trades": self.max_daily_trades - self.daily_trades
        }


# Global trading circuit breaker instance
trading_circuit_breaker = TradingCircuitBreaker()


class ResilientBroker:
    """
    Resilient wrapper around FyersBroker.
    Adds retry logic, circuit breaker, and connection management.
    """

    def __init__(self, broker):
        self.broker = broker
        self.api_circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        self.last_successful_call = datetime.now()
        self.connection_healthy = True

    async def get_ltp_safe(self, symbol: str) -> tuple[float, bool]:
        """
        Get LTP with retry and circuit breaker.
        Returns (price, success_flag).
        """
        if not self.api_circuit.can_execute():
            logger.warning(f"⚠️ API circuit open - using cached/fallback price for {symbol}")
            return 0.0, False

        try:
            price = await self._get_ltp_with_retry(symbol)
            self.api_circuit.record_success()
            self.last_successful_call = datetime.now()
            self.connection_healthy = True
            return price, True
        except Exception as e:
            self.api_circuit.record_failure()
            self.connection_healthy = False
            logger.error(f"❌ Failed to get LTP for {symbol}: {e}")
            return 0.0, False

    @with_retry(max_retries=3, base_delay=0.5, max_delay=5.0)
    async def _get_ltp_with_retry(self, symbol: str) -> float:
        """Get LTP with automatic retry."""
        price = await self.broker.get_ltp(symbol)
        if price <= 0:
            raise ValueError(f"Invalid price received: {price}")
        return price

    async def place_order_safe(
        self,
        symbol: str,
        transaction_type: str,
        quantity: int,
        order_type: str = "2",  # MARKET
        price: float = 0
    ) -> tuple[Optional[str], str]:
        """
        Place order with safety checks.
        Returns (order_id, error_message).
        """
        # Check trading circuit breaker
        can_trade, reason = trading_circuit_breaker.can_trade()
        if not can_trade:
            return None, f"Trading halted: {reason}"

        # Check API circuit breaker
        if not self.api_circuit.can_execute():
            return None, "API circuit breaker open - cannot place orders"

        try:
            order_id = await self._place_order_with_retry(
                symbol, transaction_type, quantity, order_type, price
            )
            self.api_circuit.record_success()
            return order_id, ""
        except Exception as e:
            self.api_circuit.record_failure()
            return None, str(e)

    @with_retry(max_retries=2, base_delay=1.0, max_delay=5.0)
    async def _place_order_with_retry(
        self,
        symbol: str,
        transaction_type: str,
        quantity: int,
        order_type: str,
        price: float
    ) -> str:
        """Place order with retry."""
        order_id = await self.broker.place_order(
            symbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=order_type,
            price=price
        )
        if not order_id:
            raise ValueError("Order placement returned None")
        return order_id

    async def verify_order_status(
        self,
        order_id: str,
        timeout_seconds: int = 30,
        check_interval: float = 1.0
    ) -> tuple[str, Dict]:
        """
        Verify order execution status with timeout.
        Returns (status, order_details).
        """
        start_time = datetime.now()
        last_status = "UNKNOWN"

        while (datetime.now() - start_time).total_seconds() < timeout_seconds:
            try:
                orders = await self.broker.get_orders()
                order = next((o for o in orders if o.order_id == order_id), None)

                if order:
                    last_status = order.status.value

                    if order.status.value in ["COMPLETE", "FILLED", "2"]:
                        logger.info(f"✅ Order {order_id} filled @ ₹{order.average_price}")
                        return "FILLED", order.to_dict()

                    elif order.status.value in ["REJECTED", "CANCELLED", "5", "6"]:
                        logger.error(f"❌ Order {order_id} rejected/cancelled")
                        return "REJECTED", order.to_dict()

                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.warning(f"⚠️ Error checking order status: {e}")
                await asyncio.sleep(check_interval)

        logger.warning(f"⚠️ Order {order_id} status timeout - last status: {last_status}")
        return last_status, {}

    async def emergency_close_all(self) -> tuple[int, int]:
        """
        Emergency close all positions.
        Returns (closed_count, failed_count).
        """
        logger.error("🚨 EMERGENCY: Closing all positions!")

        try:
            positions = await self.broker.get_positions()
            closed = 0
            failed = 0

            for position in positions:
                try:
                    success = await self.broker.close_position(position.symbol)
                    if success:
                        closed += 1
                        logger.info(f"✅ Emergency closed: {position.symbol}")
                    else:
                        failed += 1
                        logger.error(f"❌ Failed to close: {position.symbol}")
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Error closing {position.symbol}: {e}")

            # Halt trading after emergency close
            trading_circuit_breaker.halt_trading("Emergency close triggered")

            return closed, failed

        except Exception as e:
            logger.error(f"❌ Emergency close failed: {e}")
            return 0, 0

    def get_health_status(self) -> Dict:
        """Get broker health status."""
        return {
            "connection_healthy": self.connection_healthy,
            "api_circuit_state": self.api_circuit.state.value,
            "api_failure_count": self.api_circuit.failure_count,
            "last_successful_call": self.last_successful_call.isoformat(),
            "trading_circuit": trading_circuit_breaker.get_status()
        }

