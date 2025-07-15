"""
Broker Interface Module for Trading Bot.
Wrapper around Zerodha Kite Connect API with mock implementation for testing.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
from loguru import logger

from config import get_config

config = get_config()


class OrderType(Enum):
    """Order types supported by the broker."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"


class OrderStatus(Enum):
    """Order status types."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class TransactionType(Enum):
    """Transaction types."""
    BUY = "BUY"
    SELL = "SELL"


class Position:
    """Represents a trading position."""
    
    def __init__(self, symbol: str, quantity: int, average_price: float, 
                 transaction_type: str, timestamp: datetime = None):
        self.symbol = symbol
        self.quantity = quantity
        self.average_price = average_price
        self.transaction_type = transaction_type
        self.timestamp = timestamp or datetime.now()
        self.current_price = average_price
        self.unrealized_pnl = 0.0
        self.stop_loss = None
        self.target = None
    
    def update_current_price(self, price: float):
        """Update current price and calculate P&L."""
        self.current_price = price
        if self.transaction_type == "BUY":
            self.unrealized_pnl = (price - self.average_price) * self.quantity
        else:
            self.unrealized_pnl = (self.average_price - price) * self.quantity
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary."""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'average_price': self.average_price,
            'current_price': self.current_price,
            'transaction_type': self.transaction_type,
            'unrealized_pnl': self.unrealized_pnl,
            'stop_loss': self.stop_loss,
            'target': self.target,
            'timestamp': self.timestamp.isoformat()
        }


class Order:
    """Represents a trading order."""
    
    def __init__(self, order_id: str, symbol: str, transaction_type: str,
                 quantity: int, order_type: str, price: float = 0):
        self.order_id = order_id
        self.symbol = symbol
        self.transaction_type = transaction_type
        self.quantity = quantity
        self.order_type = order_type
        self.price = price
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0
        self.average_price = 0
        self.timestamp = datetime.now()
        self.exchange_timestamp = None
        self.tag = None
    
    def to_dict(self) -> Dict:
        """Convert order to dictionary."""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'order_type': self.order_type,
            'price': self.price,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'average_price': self.average_price,
            'timestamp': self.timestamp.isoformat(),
            'tag': self.tag
        }


class BrokerInterface:
    """
    Interface for broker operations with mock implementation.
    In production, this would use actual Zerodha Kite Connect API.
    """
    
    def __init__(self):
        self.config = config
        self.is_mock = config.MOCK_BROKER
        self.kite = None
        
        # Mock data storage
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.order_counter = 1000
        
        # Mock account info
        self.account_balance = config.INITIAL_CAPITAL
        self.available_margin = config.INITIAL_CAPITAL
        self.used_margin = 0.0
        
        # Trading limits
        self.daily_loss_count = 0
        self.daily_pnl = 0.0
        
    async def initialize(self) -> bool:
        """
        Initialize broker connection.
        
        Returns:
            Success status
        """
        try:
            if self.is_mock:
                logger.info("🤖 Initializing mock broker interface")
                return True
            else:
                # In production, initialize actual Kite Connect
                logger.info("🔗 Initializing Zerodha Kite Connect")
                
                # Import and initialize KiteConnect
                # from kiteconnect import KiteConnect
                # self.kite = KiteConnect(api_key=self.config.KITE_API_KEY)
                # self.kite.set_access_token(self.config.KITE_ACCESS_TOKEN)
                
                # For now, use mock even if not in mock mode
                logger.warning("Using mock broker - configure Kite Connect for production")
                self.is_mock = True
                return True
                
        except Exception as e:
            logger.error(f"Error initializing broker: {e}")
            return False
    
    def generate_order_id(self) -> str:
        """Generate unique order ID."""
        self.order_counter += 1
        return f"ORD_{self.order_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price or None if failed
        """
        try:
            if self.is_mock:
                # Mock price generation with some randomness
                import random
                base_prices = {
                    'RELIANCE': 2500.0,
                    'TCS': 3800.0,
                    'INFY': 1600.0,
                    'HDFCBANK': 1650.0,
                    'ICICIBANK': 950.0,
                    'KOTAKBANK': 1800.0
                }
                
                base_price = base_prices.get(symbol, 1000.0)
                # Add random variation of ±2%
                variation = random.uniform(-0.02, 0.02)
                current_price = base_price * (1 + variation)
                
                return round(current_price, 2)
            else:
                # Use actual Kite Connect API
                # quote = self.kite.quote(f"NSE:{symbol}")
                # return quote[f"NSE:{symbol}"]["last_price"]
                return None
                
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    async def place_order(self, symbol: str, transaction_type: str, 
                         quantity: int, order_type: str = "MARKET",
                         price: float = 0, tag: str = None) -> Optional[str]:
        """
        Place a trading order.
        
        Args:
            symbol: Stock symbol
            transaction_type: BUY or SELL
            quantity: Number of shares
            order_type: Order type (MARKET, LIMIT, etc.)
            price: Price for limit orders
            tag: Order tag for identification
            
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            order_id = self.generate_order_id()
            
            if self.is_mock:
                # Mock order placement
                order = Order(
                    order_id=order_id,
                    symbol=symbol,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    order_type=order_type,
                    price=price
                )
                order.tag = tag
                
                # Simulate order execution for MARKET orders
                if order_type == "MARKET":
                    current_price = await self.get_current_price(symbol)
                    if current_price:
                        order.status = OrderStatus.COMPLETE
                        order.filled_quantity = quantity
                        order.average_price = current_price
                        order.exchange_timestamp = datetime.now()
                        
                        # Update positions
                        await self.update_position_from_order(order)
                        
                        logger.info(f"✅ Mock order executed: {order_id} - "
                                   f"{transaction_type} {quantity} {symbol} @ ₹{current_price}")
                    else:
                        order.status = OrderStatus.REJECTED
                        logger.error(f"❌ Mock order rejected: Could not get price for {symbol}")
                else:
                    order.status = OrderStatus.OPEN
                    logger.info(f"📋 Mock {order_type} order placed: {order_id}")
                
                self.orders[order_id] = order
                return order_id
                
            else:
                # Use actual Kite Connect API
                # order_params = {
                #     "tradingsymbol": symbol,
                #     "exchange": "NSE",
                #     "transaction_type": transaction_type,
                #     "quantity": quantity,
                #     "order_type": order_type,
                #     "product": "MIS",  # Intraday
                #     "validity": "DAY"
                # }
                # if order_type == "LIMIT":
                #     order_params["price"] = price
                # if tag:
                #     order_params["tag"] = tag
                
                # order_response = self.kite.place_order(**order_params)
                # return order_response["order_id"]
                return None
                
        except Exception as e:
            logger.error(f"Error placing order for {symbol}: {e}")
            return None
    
    async def update_position_from_order(self, order: Order):
        """Update positions based on executed order."""
        try:
            symbol = order.symbol
            
            if symbol in self.positions:
                # Existing position
                position = self.positions[symbol]
                
                if order.transaction_type == position.transaction_type:
                    # Same direction - average the price
                    total_quantity = position.quantity + order.filled_quantity
                    total_value = (position.quantity * position.average_price + 
                                 order.filled_quantity * order.average_price)
                    position.average_price = total_value / total_quantity
                    position.quantity = total_quantity
                else:
                    # Opposite direction - reduce or close position
                    if order.filled_quantity >= position.quantity:
                        # Close existing and create new position
                        remaining_qty = order.filled_quantity - position.quantity
                        if remaining_qty > 0:
                            position.quantity = remaining_qty
                            position.transaction_type = order.transaction_type
                            position.average_price = order.average_price
                        else:
                            # Exact close
                            del self.positions[symbol]
                    else:
                        # Partial close
                        position.quantity -= order.filled_quantity
            else:
                # New position
                position = Position(
                    symbol=symbol,
                    quantity=order.filled_quantity,
                    average_price=order.average_price,
                    transaction_type=order.transaction_type
                )
                self.positions[symbol] = position
            
            # Update margin
            order_value = order.filled_quantity * order.average_price
            if order.transaction_type == "BUY":
                self.used_margin += order_value
                self.available_margin -= order_value
            else:
                self.used_margin -= order_value
                self.available_margin += order_value
                
        except Exception as e:
            logger.error(f"Error updating position from order: {e}")
    
    async def place_bracket_order(self, symbol: str, transaction_type: str,
                                quantity: int, entry_price: float,
                                stop_loss: float, target: float,
                                tag: str = None) -> Optional[Dict]:
        """
        Place a bracket order with entry, stop loss, and target.
        
        Args:
            symbol: Stock symbol
            transaction_type: BUY or SELL
            quantity: Number of shares
            entry_price: Entry price
            stop_loss: Stop loss price
            target: Target price
            tag: Order tag
            
        Returns:
            Dictionary with order IDs
        """
        try:
            # Place main entry order
            entry_order_id = await self.place_order(
                symbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type="LIMIT",
                price=entry_price,
                tag=f"{tag}_ENTRY" if tag else "ENTRY"
            )
            
            if not entry_order_id:
                logger.error(f"Failed to place entry order for {symbol}")
                return None
            
            # For mock implementation, immediately execute and place SL/Target
            if self.is_mock:
                # Place stop loss order
                sl_transaction = "SELL" if transaction_type == "BUY" else "BUY"
                sl_order_id = await self.place_order(
                    symbol=symbol,
                    transaction_type=sl_transaction,
                    quantity=quantity,
                    order_type="SL-M",
                    price=stop_loss,
                    tag=f"{tag}_SL" if tag else "SL"
                )
                
                # Place target order
                target_order_id = await self.place_order(
                    symbol=symbol,
                    transaction_type=sl_transaction,
                    quantity=quantity,
                    order_type="LIMIT",
                    price=target,
                    tag=f"{tag}_TARGET" if tag else "TARGET"
                )
                
                return {
                    'entry_order_id': entry_order_id,
                    'stop_loss_order_id': sl_order_id,
                    'target_order_id': target_order_id
                }
            
            return {'entry_order_id': entry_order_id}
            
        except Exception as e:
            logger.error(f"Error placing bracket order for {symbol}: {e}")
            return None
    
    async def get_positions(self) -> Dict[str, Position]:
        """
        Get current positions.
        
        Returns:
            Dictionary of positions
        """
        try:
            if self.is_mock:
                # Update current prices for all positions
                for position in self.positions.values():
                    current_price = await self.get_current_price(position.symbol)
                    if current_price:
                        position.update_current_price(current_price)
                
                return self.positions
            else:
                # Use actual Kite Connect API
                # positions = self.kite.positions()
                # return self.parse_kite_positions(positions)
                return {}
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    async def get_orders(self) -> Dict[str, Order]:
        """
        Get all orders.
        
        Returns:
            Dictionary of orders
        """
        try:
            if self.is_mock:
                return self.orders
            else:
                # Use actual Kite Connect API
                # orders = self.kite.orders()
                # return self.parse_kite_orders(orders)
                return {}
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return {}
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Success status
        """
        try:
            if self.is_mock:
                if order_id in self.orders:
                    order = self.orders[order_id]
                    if order.status == OrderStatus.OPEN:
                        order.status = OrderStatus.CANCELLED
                        logger.info(f"✅ Cancelled order: {order_id}")
                        return True
                    else:
                        logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
                        return False
                else:
                    logger.error(f"Order {order_id} not found")
                    return False
            else:
                # Use actual Kite Connect API
                # self.kite.cancel_order(order_id=order_id)
                return True
                
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def exit_position(self, symbol: str) -> bool:
        """
        Exit a position by placing market order.
        
        Args:
            symbol: Symbol to exit
            
        Returns:
            Success status
        """
        try:
            if symbol not in self.positions:
                logger.warning(f"No position found for {symbol}")
                return False
            
            position = self.positions[symbol]
            
            # Determine exit transaction type
            exit_transaction = "SELL" if position.transaction_type == "BUY" else "BUY"
            
            # Place market order to exit
            order_id = await self.place_order(
                symbol=symbol,
                transaction_type=exit_transaction,
                quantity=position.quantity,
                order_type="MARKET",
                tag="EXIT"
            )
            
            if order_id:
                logger.info(f"✅ Exit order placed for {symbol}: {order_id}")
                return True
            else:
                logger.error(f"Failed to place exit order for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Error exiting position for {symbol}: {e}")
            return False
    
    async def get_account_info(self) -> Dict:
        """
        Get account information.
        
        Returns:
            Account details
        """
        try:
            # Calculate total P&L
            total_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            
            return {
                'account_balance': self.account_balance,
                'available_margin': self.available_margin,
                'used_margin': self.used_margin,
                'total_positions': len(self.positions),
                'total_unrealized_pnl': total_pnl,
                'daily_pnl': self.daily_pnl,
                'daily_loss_count': self.daily_loss_count
            }
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    async def force_exit_all_positions(self) -> bool:
        """
        Force exit all positions (for end of day).
        
        Returns:
            Success status
        """
        try:
            logger.info("🚨 Force exiting all positions")
            
            exit_results = []
            for symbol in list(self.positions.keys()):
                result = await self.exit_position(symbol)
                exit_results.append(result)
            
            success_count = sum(exit_results)
            total_count = len(exit_results)
            
            logger.info(f"Force exit completed: {success_count}/{total_count} positions closed")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"Error in force exit: {e}")
            return False


# Global broker instance
broker = BrokerInterface()


async def initialize_broker() -> bool:
    """Initialize the global broker instance."""
    return await broker.initialize()


if __name__ == "__main__":
    # Test the broker interface
    async def test_broker():
        try:
            # Initialize broker
            success = await initialize_broker()
            if not success:
                print("❌ Failed to initialize broker")
                return
            
            print("✅ Broker initialized successfully")
            
            # Test current price
            price = await broker.get_current_price("RELIANCE")
            print(f"RELIANCE current price: ₹{price}")
            
            # Test order placement
            order_id = await broker.place_order(
                symbol="RELIANCE",
                transaction_type="BUY",
                quantity=10,
                order_type="MARKET",
                tag="TEST"
            )
            print(f"Order placed: {order_id}")
            
            # Test positions
            positions = await broker.get_positions()
            print(f"Positions: {len(positions)}")
            
            for symbol, pos in positions.items():
                print(f"  {symbol}: {pos.quantity} @ ₹{pos.average_price} "
                      f"(P&L: ₹{pos.unrealized_pnl:.2f})")
            
            # Test account info
            account = await broker.get_account_info()
            print(f"Account Balance: ₹{account['account_balance']}")
            print(f"Available Margin: ₹{account['available_margin']}")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    asyncio.run(test_broker())
