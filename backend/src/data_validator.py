"""
Data Validator - Ensures data integrity for trading operations.
Critical for accuracy since the system deals with money.

From PLAN_OF_ACTION.md:
- All non-LLM bottlenecks should be handled properly
- System should be as accurate as possible
"""
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, time
from dataclasses import dataclass
from loguru import logger


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self) -> bool:
        return self.is_valid


class DataValidator:
    """
    Validates trading data to ensure accuracy and prevent errors.
    
    Validates:
    - Price data (LTP, OHLC)
    - Order parameters
    - Trade signals
    - Position data
    - Risk calculations
    """
    
    # Price validation limits
    MIN_PRICE = 0.01
    MAX_PRICE = 1000000  # 10 lakh
    MAX_PRICE_CHANGE_PCT = 20  # Circuit limit
    
    # Quantity limits
    MIN_QUANTITY = 1
    MAX_QUANTITY = 100000
    
    # Risk limits
    MAX_RISK_PER_TRADE_PCT = 5.0
    MAX_STOP_LOSS_PCT = 10.0
    MIN_RR_RATIO = 1.0
    
    @classmethod
    def validate_price(cls, price: float, symbol: str = "") -> ValidationResult:
        """
        Validate a price value.
        
        Args:
            price: Price to validate
            symbol: Symbol for context
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        if price is None:
            errors.append(f"Price is None for {symbol}")
            return ValidationResult(False, errors, warnings)
        
        if not isinstance(price, (int, float)):
            errors.append(f"Price is not a number: {type(price)}")
            return ValidationResult(False, errors, warnings)
        
        if price <= cls.MIN_PRICE:
            errors.append(f"Price too low: {price} <= {cls.MIN_PRICE}")
        
        if price > cls.MAX_PRICE:
            errors.append(f"Price too high: {price} > {cls.MAX_PRICE}")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    @classmethod
    def validate_ohlc(cls, ohlc: Dict, symbol: str = "") -> ValidationResult:
        """
        Validate OHLC data.
        
        Args:
            ohlc: Dictionary with open, high, low, close
            symbol: Symbol for context
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        required_fields = ['open', 'high', 'low', 'close']
        
        for field in required_fields:
            if field not in ohlc:
                errors.append(f"Missing {field} in OHLC data")
                continue
            
            price_result = cls.validate_price(ohlc[field], f"{symbol}.{field}")
            errors.extend(price_result.errors)
            warnings.extend(price_result.warnings)
        
        if not errors:
            # Validate OHLC relationships
            o, h, l, c = ohlc['open'], ohlc['high'], ohlc['low'], ohlc['close']
            
            if h < l:
                errors.append(f"High ({h}) < Low ({l})")
            
            if h < o or h < c:
                warnings.append(f"High ({h}) is not the highest value")
            
            if l > o or l > c:
                warnings.append(f"Low ({l}) is not the lowest value")
        
        return ValidationResult(len(errors) == 0, errors, warnings)
    
    @classmethod
    def validate_order_params(
        cls,
        symbol: str,
        quantity: int,
        price: float,
        stop_loss: Optional[float] = None,
        target: Optional[float] = None,
        direction: str = "BUY"
    ) -> ValidationResult:
        """
        Validate order parameters before placement.
        
        Args:
            symbol: Stock symbol
            quantity: Order quantity
            price: Entry price
            stop_loss: Stop loss price
            target: Target price
            direction: BUY or SELL
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            errors.append("Invalid symbol")
        
        # Validate quantity
        if quantity < cls.MIN_QUANTITY:
            errors.append(f"Quantity too low: {quantity} < {cls.MIN_QUANTITY}")
        
        if quantity > cls.MAX_QUANTITY:
            errors.append(f"Quantity too high: {quantity} > {cls.MAX_QUANTITY}")
        
        # Validate price
        price_result = cls.validate_price(price, symbol)
        errors.extend(price_result.errors)
        
        # Validate direction
        if direction not in ["BUY", "SELL"]:
            errors.append(f"Invalid direction: {direction}")
        
        # Validate stop loss
        if stop_loss is not None:
            sl_result = cls.validate_price(stop_loss, f"{symbol}.SL")
            errors.extend(sl_result.errors)
            
            if not sl_result.errors:
                sl_pct = abs(price - stop_loss) / price * 100
                
                if sl_pct > cls.MAX_STOP_LOSS_PCT:
                    warnings.append(f"Stop loss too wide: {sl_pct:.1f}%")
                
                # Check SL direction
                if direction == "BUY" and stop_loss >= price:
                    errors.append(f"BUY stop loss ({stop_loss}) >= entry ({price})")
                elif direction == "SELL" and stop_loss <= price:
                    errors.append(f"SELL stop loss ({stop_loss}) <= entry ({price})")

        # Validate target
        if target is not None and stop_loss is not None:
            target_result = cls.validate_price(target, f"{symbol}.Target")
            errors.extend(target_result.errors)

            if not target_result.errors:
                # Check target direction
                if direction == "BUY" and target <= price:
                    errors.append(f"BUY target ({target}) <= entry ({price})")
                elif direction == "SELL" and target >= price:
                    errors.append(f"SELL target ({target}) >= entry ({price})")

                # Check R:R ratio
                risk = abs(price - stop_loss)
                reward = abs(target - price)
                rr_ratio = reward / risk if risk > 0 else 0

                if rr_ratio < cls.MIN_RR_RATIO:
                    warnings.append(f"R:R ratio too low: {rr_ratio:.2f}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    @classmethod
    def validate_trade_signal(cls, signal: Dict) -> ValidationResult:
        """
        Validate a trade signal before execution.

        Args:
            signal: Trade signal dictionary

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        required_fields = ['symbol', 'direction', 'entryPrice', 'stopLoss']

        for field in required_fields:
            if field not in signal:
                errors.append(f"Missing required field: {field}")

        if errors:
            return ValidationResult(False, errors, warnings)

        # Validate order params
        order_result = cls.validate_order_params(
            symbol=signal['symbol'],
            quantity=signal.get('quantity', 1),
            price=signal['entryPrice'],
            stop_loss=signal['stopLoss'],
            target=signal.get('target1'),
            direction=signal['direction']
        )

        errors.extend(order_result.errors)
        warnings.extend(order_result.warnings)

        # Validate confidence
        confidence = signal.get('confidence', 0)
        if confidence < 0 or confidence > 100:
            errors.append(f"Invalid confidence: {confidence}")
        elif confidence < 50:
            warnings.append(f"Low confidence: {confidence}%")

        return ValidationResult(len(errors) == 0, errors, warnings)

    @classmethod
    def validate_position_size(
        cls,
        quantity: int,
        price: float,
        equity: float,
        max_position_pct: float = 25.0
    ) -> ValidationResult:
        """
        Validate position size against capital limits.

        Args:
            quantity: Position quantity
            price: Entry price
            equity: Account equity
            max_position_pct: Maximum position as % of equity

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        position_value = quantity * price
        position_pct = (position_value / equity) * 100 if equity > 0 else 100

        if position_pct > max_position_pct:
            errors.append(
                f"Position size ({position_pct:.1f}%) exceeds limit ({max_position_pct}%)"
            )
        elif position_pct > max_position_pct * 0.8:
            warnings.append(
                f"Position size ({position_pct:.1f}%) approaching limit ({max_position_pct}%)"
            )

        return ValidationResult(len(errors) == 0, errors, warnings)

    @classmethod
    def validate_market_hours(cls) -> ValidationResult:
        """
        Validate if current time is within market hours.

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        now = datetime.now()
        current_time = now.time()

        market_open = time(9, 15)
        market_close = time(15, 30)
        last_entry = time(14, 30)

        # Check if weekend
        if now.weekday() >= 5:
            errors.append("Market closed on weekends")
            return ValidationResult(False, errors, warnings)

        # Check market hours
        if current_time < market_open:
            errors.append(f"Market not open yet (opens at {market_open})")
        elif current_time > market_close:
            errors.append(f"Market closed (closed at {market_close})")
        elif current_time > last_entry:
            warnings.append(f"Past last entry time ({last_entry})")

        return ValidationResult(len(errors) == 0, errors, warnings)

    @classmethod
    def sanitize_symbol(cls, symbol: str) -> str:
        """
        Sanitize and normalize a stock symbol.

        Args:
            symbol: Raw symbol string

        Returns:
            Normalized symbol
        """
        if not symbol:
            return ""

        # Remove whitespace and convert to uppercase
        symbol = symbol.strip().upper()

        # Remove common prefixes/suffixes
        prefixes = ['NSE:', 'BSE:', 'NSE-', 'BSE-']
        for prefix in prefixes:
            if symbol.startswith(prefix):
                symbol = symbol[len(prefix):]

        # Remove -EQ suffix if present
        if symbol.endswith('-EQ'):
            symbol = symbol[:-3]

        return symbol

    @classmethod
    def validate_and_log(cls, validation_result: ValidationResult, context: str = ""):
        """
        Log validation results.

        Args:
            validation_result: Validation result to log
            context: Context string for logging
        """
        if validation_result.is_valid:
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"⚠️ {context}: {warning}")
        else:
            for error in validation_result.errors:
                logger.error(f"❌ {context}: {error}")
            for warning in validation_result.warnings:
                logger.warning(f"⚠️ {context}: {warning}")

