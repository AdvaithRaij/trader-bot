"""
Trade Executor - Stage 3 of the 3-stage pipeline.
Validates and executes trade plans with comprehensive risk management.

From PLAN_OF_ACTION.md:
- Validates trade plans before execution
- Implements position sizing formula
- Enforces all risk limits
- Performs pre-execution checks
- Places orders with SL-M and target orders
"""
import asyncio
from datetime import datetime, time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from loguru import logger

from config import get_config
from models.trade_plan import TradePlan, TradePlanOutput
from models import TradeSignal, TradeDirection, TradeStatus

config = get_config()


@dataclass
class ExecutionResult:
    """Result of trade execution attempt."""
    success: bool
    symbol: str
    order_id: Optional[str] = None
    quantity: int = 0
    entry_price: float = 0.0
    rejection_reason: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PreExecutionCheck:
    """Pre-execution validation result."""
    passed: bool
    checks: Dict[str, bool]
    rejection_reasons: List[str]


class TradeExecutor:
    """
    Trade Executor implementing Stage 3 of the pipeline.
    
    Validation Rules (from PLAN_OF_ACTION.md):
    - Confidence >= 75%
    - R:R >= 1.5
    - Max Risk/Trade: 1.5% of capital
    - Max Open Risk: 5% of capital
    - Max Daily Loss: 3% of capital
    - Max Trades/Day: 10
    - Trading Hours: 9:15 AM - 3:15 PM IST
    - Last Entry: 2:30 PM
    - EOD Square Off: 3:15 PM
    
    Pre-Execution Checks:
    - Price deviation <= 0.5% from plan
    - Circuit check (stock not in circuit)
    - Margin check
    - Market hours validation
    """
    
    # Trading hours (IST)
    MARKET_OPEN = time(9, 15)
    LAST_ENTRY = time(14, 30)
    EOD_SQUARE_OFF = time(15, 15)
    MARKET_CLOSE = time(15, 30)
    
    # Risk limits from PLAN_OF_ACTION.md
    MAX_RISK_PER_TRADE_PCT = 1.5
    MAX_OPEN_RISK_PCT = 5.0
    MAX_DAILY_LOSS_PCT = 3.0
    MAX_TRADES_PER_DAY = 10
    MIN_CONFIDENCE = 75.0
    MIN_RR_RATIO = 1.5
    MAX_PRICE_DEVIATION_PCT = 0.5
    
    def __init__(self, broker=None, portfolio_manager=None, risk_manager=None):
        """
        Initialize Trade Executor.
        
        Args:
            broker: Broker instance for order placement
            portfolio_manager: Portfolio manager for position tracking
            risk_manager: Risk manager for limit checks
        """
        self.broker = broker
        self.portfolio = portfolio_manager
        self.risk_manager = risk_manager
        
        # Daily tracking
        self.daily_trades_count = 0
        self.daily_loss = 0.0
        self.open_risk = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Active orders
        self.pending_orders: Dict[str, Dict] = {}
        
        logger.info("⚡ Trade Executor initialized with PLAN_OF_ACTION.md rules")
    
    def _reset_daily_metrics(self):
        """Reset daily metrics at start of new trading day."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_trades_count = 0
            self.daily_loss = 0.0
            self.last_reset_date = today
            logger.info("🔄 Daily metrics reset for new trading day")
    
    def _is_market_hours(self) -> Tuple[bool, str]:
        """Check if current time is within trading hours."""
        now = datetime.now().time()
        
        if now < self.MARKET_OPEN:
            return False, f"Market not open yet (opens at {self.MARKET_OPEN})"
        
        if now > self.LAST_ENTRY:
            return False, f"Past last entry time ({self.LAST_ENTRY})"
        
        return True, "Within trading hours"
    
    def _should_square_off(self) -> bool:
        """Check if it's time for EOD square off."""
        now = datetime.now().time()
        return now >= self.EOD_SQUARE_OFF
    
    def calculate_position_size(self, plan: TradePlan, equity: float) -> Tuple[int, float]:
        """
        Calculate position size using PLAN_OF_ACTION.md formula.
        
        Formula:
        max_money_risk = equity × max_risk_per_trade_pct / 100
        risk_per_share = |entry_price - stop_loss|
        quantity = floor(max_money_risk / risk_per_share)
        
        Args:
            plan: Trade plan with entry and stop loss
            equity: Current account equity
            
        Returns:
            Tuple of (quantity, capital_required)
        """
        max_money_risk = equity * (self.MAX_RISK_PER_TRADE_PCT / 100)
        risk_per_share = plan.levels.risk_per_share
        
        if risk_per_share <= 0:
            logger.warning(f"Invalid risk per share for {plan.symbol}")
            return 0, 0.0
        
        quantity = int(max_money_risk / risk_per_share)
        capital_required = quantity * plan.levels.entry
        
        # Ensure we don't exceed available capital
        max_capital = equity * 0.25  # Max 25% per trade
        if capital_required > max_capital:
            quantity = int(max_capital / plan.levels.entry)
            capital_required = quantity * plan.levels.entry
        
        logger.info(f"Position size for {plan.symbol}: {quantity} shares, ₹{capital_required:,.2f}")
        return quantity, capital_required

    async def run_pre_execution_checks(self, plan: TradePlan,
                                        current_price: float,
                                        equity: float) -> PreExecutionCheck:
        """
        Run all pre-execution checks from PLAN_OF_ACTION.md.

        Checks:
        1. Confidence >= 75%
        2. R:R >= 1.5
        3. Price deviation <= 0.5%
        4. Market hours
        5. Daily trade limit
        6. Daily loss limit
        7. Open risk limit
        8. Circuit check (if broker available)
        9. Margin check (if broker available)

        Args:
            plan: Trade plan to validate
            current_price: Current market price
            equity: Current account equity

        Returns:
            PreExecutionCheck with results
        """
        self._reset_daily_metrics()

        checks = {}
        rejection_reasons = []

        # 1. Confidence check
        checks['confidence'] = plan.confidence >= self.MIN_CONFIDENCE
        if not checks['confidence']:
            rejection_reasons.append(
                f"Confidence {plan.confidence:.1f}% < {self.MIN_CONFIDENCE}%"
            )

        # 2. R:R ratio check
        checks['risk_reward'] = plan.levels.risk_reward_ratio >= self.MIN_RR_RATIO
        if not checks['risk_reward']:
            rejection_reasons.append(
                f"R:R {plan.levels.risk_reward_ratio:.2f} < {self.MIN_RR_RATIO}"
            )

        # 3. Price deviation check
        price_deviation = abs(current_price - plan.levels.entry) / plan.levels.entry * 100
        checks['price_deviation'] = price_deviation <= self.MAX_PRICE_DEVIATION_PCT
        if not checks['price_deviation']:
            rejection_reasons.append(
                f"Price deviation {price_deviation:.2f}% > {self.MAX_PRICE_DEVIATION_PCT}%"
            )

        # 4. Market hours check
        is_market_hours, hours_msg = self._is_market_hours()
        checks['market_hours'] = is_market_hours
        if not checks['market_hours']:
            rejection_reasons.append(hours_msg)

        # 5. Daily trade limit
        checks['daily_trades'] = self.daily_trades_count < self.MAX_TRADES_PER_DAY
        if not checks['daily_trades']:
            rejection_reasons.append(
                f"Daily trade limit reached ({self.MAX_TRADES_PER_DAY})"
            )

        # 6. Daily loss limit
        max_daily_loss = equity * (self.MAX_DAILY_LOSS_PCT / 100)
        checks['daily_loss'] = self.daily_loss < max_daily_loss
        if not checks['daily_loss']:
            rejection_reasons.append(
                f"Daily loss limit reached (₹{max_daily_loss:,.2f})"
            )

        # 7. Open risk limit
        quantity, _ = self.calculate_position_size(plan, equity)
        trade_risk = quantity * plan.levels.risk_per_share
        max_open_risk = equity * (self.MAX_OPEN_RISK_PCT / 100)
        checks['open_risk'] = (self.open_risk + trade_risk) <= max_open_risk
        if not checks['open_risk']:
            rejection_reasons.append(
                f"Open risk would exceed limit (₹{max_open_risk:,.2f})"
            )

        # 8. Circuit check (if broker available)
        if self.broker:
            try:
                # Check if stock is in circuit
                quote = await self.broker.get_quote(plan.symbol)
                if quote:
                    upper_circuit = quote.get('upper_circuit', float('inf'))
                    lower_circuit = quote.get('lower_circuit', 0)
                    checks['circuit'] = lower_circuit < current_price < upper_circuit
                    if not checks['circuit']:
                        rejection_reasons.append("Stock in circuit")
                else:
                    checks['circuit'] = True  # Assume OK if no data
            except Exception as e:
                logger.warning(f"Circuit check failed: {e}")
                checks['circuit'] = True  # Assume OK on error
        else:
            checks['circuit'] = True

        # 9. Margin check (if broker available)
        if self.broker and self.portfolio:
            try:
                available_margin = await self.broker.get_available_margin()
                capital_required = quantity * plan.levels.entry
                checks['margin'] = available_margin >= capital_required
                if not checks['margin']:
                    rejection_reasons.append(
                        f"Insufficient margin (need ₹{capital_required:,.2f})"
                    )
            except Exception as e:
                logger.warning(f"Margin check failed: {e}")
                checks['margin'] = True  # Assume OK on error
        else:
            checks['margin'] = True

        passed = all(checks.values())

        if passed:
            logger.info(f"✅ Pre-execution checks passed for {plan.symbol}")
        else:
            logger.warning(f"❌ Pre-execution checks failed for {plan.symbol}: {rejection_reasons}")

        return PreExecutionCheck(
            passed=passed,
            checks=checks,
            rejection_reasons=rejection_reasons
        )

    async def execute_plan(self, plan: TradePlan, equity: float) -> ExecutionResult:
        """
        Execute a validated trade plan.

        Args:
            plan: Trade plan to execute
            equity: Current account equity

        Returns:
            ExecutionResult with outcome
        """
        try:
            # Get current price
            if self.broker:
                current_price = await self.broker.get_ltp(plan.symbol)
            else:
                current_price = plan.levels.entry

            # Run pre-execution checks
            pre_check = await self.run_pre_execution_checks(plan, current_price, equity)

            if not pre_check.passed:
                return ExecutionResult(
                    success=False,
                    symbol=plan.symbol,
                    rejection_reason="; ".join(pre_check.rejection_reasons)
                )

            # Calculate position size
            quantity, capital_required = self.calculate_position_size(plan, equity)

            if quantity <= 0:
                return ExecutionResult(
                    success=False,
                    symbol=plan.symbol,
                    rejection_reason="Position size is 0"
                )

            # Create trade signal for execution engine
            signal = TradeSignal(
                strategyId="ai_pipeline",
                strategyName="AI Trade Pipeline",
                symbol=plan.symbol,
                direction=TradeDirection.BUY if plan.direction == "BUY" else TradeDirection.SELL,
                entryPrice=current_price,
                stopLoss=plan.levels.stop_loss,
                target1=plan.levels.target_1,
                target2=plan.levels.target_2,
                aiAnalysis=plan.rationale.summary,
                confidence=plan.confidence / 100  # Convert to 0-1 scale
            )

            # Place order if broker available
            if self.broker:
                order_id = await self._place_bracket_order(plan, quantity, current_price)

                if not order_id:
                    return ExecutionResult(
                        success=False,
                        symbol=plan.symbol,
                        rejection_reason="Order placement failed"
                    )

                # Update tracking
                self.daily_trades_count += 1
                self.open_risk += quantity * plan.levels.risk_per_share

                logger.info(
                    f"✅ Order placed: {plan.direction} {plan.symbol} x{quantity} @ ₹{current_price}"
                )

                return ExecutionResult(
                    success=True,
                    symbol=plan.symbol,
                    order_id=order_id,
                    quantity=quantity,
                    entry_price=current_price
                )
            else:
                # Simulation mode
                logger.info(
                    f"📝 [SIMULATION] Would execute: {plan.direction} {plan.symbol} "
                    f"x{quantity} @ ₹{current_price}"
                )

                self.daily_trades_count += 1
                self.open_risk += quantity * plan.levels.risk_per_share

                return ExecutionResult(
                    success=True,
                    symbol=plan.symbol,
                    order_id="SIM_" + plan.symbol,
                    quantity=quantity,
                    entry_price=current_price
                )

        except Exception as e:
            logger.error(f"❌ Error executing plan for {plan.symbol}: {e}")
            return ExecutionResult(
                success=False,
                symbol=plan.symbol,
                rejection_reason=str(e)
            )

    async def _place_bracket_order(self, plan: TradePlan, quantity: int,
                                    entry_price: float) -> Optional[str]:
        """
        Place bracket order with SL and target.

        Args:
            plan: Trade plan
            quantity: Order quantity
            entry_price: Entry price

        Returns:
            Order ID if successful
        """
        try:
            # Calculate SL and target points
            sl_points = abs(entry_price - plan.levels.stop_loss)
            target_points = abs(plan.levels.target_1 - entry_price)

            transaction_type = "1" if plan.direction == "BUY" else "-1"

            # Place bracket order
            order_id = await self.broker.place_bracket_order(
                symbol=plan.symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                price=entry_price,
                stop_loss=sl_points,
                target=target_points
            )

            return order_id

        except Exception as e:
            logger.error(f"❌ Error placing bracket order: {e}")
            return None

    async def execute_plans(self, plan_output: TradePlanOutput,
                            equity: float) -> List[ExecutionResult]:
        """
        Execute multiple trade plans.

        Args:
            plan_output: Output from AI Insight Provider
            equity: Current account equity

        Returns:
            List of execution results
        """
        results = []

        # Only execute plans that are marked as executable
        executable_plans = [p for p in plan_output.plans if p.is_executable]

        logger.info(f"📊 Executing {len(executable_plans)} of {len(plan_output.plans)} plans")

        for plan in executable_plans:
            # Check if we've hit daily limits
            if self.daily_trades_count >= self.MAX_TRADES_PER_DAY:
                logger.warning("Daily trade limit reached, stopping execution")
                break

            result = await self.execute_plan(plan, equity)
            results.append(result)

            # Small delay between orders
            await asyncio.sleep(0.5)

        successful = sum(1 for r in results if r.success)
        logger.info(f"✅ Executed {successful}/{len(results)} trades successfully")

        return results

    def record_trade_exit(self, symbol: str, pnl: float, risk_amount: float):
        """
        Record trade exit for tracking.

        Args:
            symbol: Stock symbol
            pnl: Realized P&L
            risk_amount: Risk amount that was at stake
        """
        # Update open risk
        self.open_risk = max(0, self.open_risk - risk_amount)

        # Update daily loss if applicable
        if pnl < 0:
            self.daily_loss += abs(pnl)

        logger.info(f"📊 Trade exit recorded: {symbol}, P&L: ₹{pnl:,.2f}")

    async def square_off_all(self) -> List[ExecutionResult]:
        """
        Square off all open positions (EOD).

        Returns:
            List of execution results
        """
        results = []

        if not self.broker:
            logger.warning("No broker connected, cannot square off")
            return results

        try:
            positions = await self.broker.get_positions()

            for pos in positions:
                if pos.quantity != 0:
                    # Close position
                    transaction_type = "-1" if pos.quantity > 0 else "1"

                    order_id = await self.broker.place_order(
                        symbol=pos.symbol,
                        transaction_type=transaction_type,
                        quantity=abs(pos.quantity),
                        order_type="MARKET"
                    )

                    results.append(ExecutionResult(
                        success=order_id is not None,
                        symbol=pos.symbol,
                        order_id=order_id,
                        quantity=abs(pos.quantity)
                    ))

            logger.info(f"🔒 Squared off {len(results)} positions")

        except Exception as e:
            logger.error(f"❌ Error squaring off positions: {e}")

        return results

