"""
Broker Interface Module for Trading Bot.
Wrapper around Fyers API with mock implementation for testing.
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
    MARKET = "2"
    LIMIT = "1"
    SL = "3"
    SL_M = "4"


class OrderStatus(Enum):
    """Order status types."""
    PENDING = "1"
    OPEN = "2"
    COMPLETE = "6"
    CANCELLED = "5"
    REJECTED = "7"


class TransactionType(Enum):
    """Transaction types."""
    BUY = "1"
    SELL = "-1"


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
        if self.transaction_type == "1":  # BUY
            self.unrealized_pnl = (price - self.average_price) * self.quantity
        else:  # SELL
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


class FyersBroker:
    """Fyers broker implementation."""
    
    def __init__(self):
        self.fyers = None
        self.access_token = None
        self.is_connected = False
        self._positions: Dict[str, Position] = {}
        self._orders: Dict[str, Order] = {}
        self._account_info = {
            'available_balance': 0.0,
            'used_margin': 0.0,
            'total_margin': 0.0
        }
        
        # Setup Fyers API if not in mock mode
        if not config.MOCK_MODE:
            self._setup_fyers_api()
    
    def _setup_fyers_api(self):
        """Setup Fyers API connection."""
        try:
            from fyers_apiv3 import fyersModel
            
            # Initialize Fyers API
            self.fyers = fyersModel.FyersModel(
                client_id=config.FYERS_APP_ID,
                is_async=False,
                token=config.FYERS_ACCESS_TOKEN,
                log_path=""
            )
            
            logger.info("✅ Fyers API initialized")
            
        except Exception as e:
            logger.error(f"❌ Error setting up Fyers API: {e}")
            raise
    
    async def initialize(self) -> bool:
        """Initialize the broker connection."""
        try:
            if config.MOCK_MODE:
                logger.info("🤖 Initializing mock broker interface")
                self.is_connected = True
                self._account_info = {
                    'available_balance': config.INITIAL_CAPITAL,
                    'used_margin': 0.0,
                    'total_margin': config.INITIAL_CAPITAL
                }
                return True
            
            # Test connection with Fyers API
            logger.info("🔌 Testing Fyers API connection...")
            profile = self.fyers.get_profile()
            
            if profile['s'] == 'ok':
                self.is_connected = True
                logger.info("✅ Fyers API connection successful")
                
                # Get account information
                await self._update_account_info()
                return True
            else:
                logger.error(f"❌ Fyers API connection failed: {profile}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing broker: {e}")
            return False
    
    async def _update_account_info(self):
        """Update account information from Fyers API."""
        try:
            if config.MOCK_MODE:
                return
            
            # Get funds information
            funds = self.fyers.funds()
            if funds['s'] == 'ok':
                fund_data = funds['fund_limit'][0]
                self._account_info = {
                    'available_balance': fund_data['equityAmount'],
                    'used_margin': fund_data['used_margin'],
                    'total_margin': fund_data['equityAmount'] + fund_data['used_margin']
                }
            
        except Exception as e:
            logger.error(f"Error updating account info: {e}")
    
    async def get_account_info(self) -> Dict:
        """Get account information."""
        await self._update_account_info()
        return self._account_info.copy()
    
    async def get_ltp(self, symbol: str) -> float:
        """Get Last Traded Price for a symbol."""
        try:
            if config.MOCK_MODE:
                # Return mock price based on symbol
                import random
                base_price = 100.0
                if 'RELIANCE' in symbol:
                    base_price = 2500.0
                elif 'TCS' in symbol:
                    base_price = 3500.0
                elif 'INFY' in symbol:
                    base_price = 1500.0
                elif 'HDFC' in symbol:
                    base_price = 1600.0
                
                # Add some random variation
                variation = random.uniform(-0.05, 0.05)
                return base_price * (1 + variation)
            
            # Format symbol for Fyers API (NSE:SYMBOL-EQ)
            fyers_symbol = f"NSE:{symbol}-EQ"
            
            # Get quotes
            quotes = self.fyers.quotes({"symbols": fyers_symbol})
            
            if quotes['s'] == 'ok' and quotes['d']:
                return quotes['d'][0]['v']['lp']
            else:
                logger.error(f"Error getting LTP for {symbol}: {quotes}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting LTP for {symbol}: {e}")
            return 0.0
    
    async def place_order(self, symbol: str, transaction_type: str, quantity: int,
                         order_type: str = OrderType.MARKET.value, price: float = 0,
                         stop_loss: float = None, target: float = None) -> Optional[str]:
        """Place a trading order."""
        try:
            if config.MOCK_MODE:
                # Generate mock order ID
                order_id = f"mock_order_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Create order object
                order = Order(
                    order_id=order_id,
                    symbol=symbol,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    order_type=order_type,
                    price=price
                )
                
                # Simulate order execution
                await asyncio.sleep(0.1)  # Simulate network delay
                
                # Mock fill the order
                current_price = await self.get_ltp(symbol)
                order.status = OrderStatus.COMPLETE
                order.filled_quantity = quantity
                order.average_price = current_price if order_type == OrderType.MARKET.value else price
                
                self._orders[order_id] = order
                
                # Update positions
                await self._update_position_from_order(order)
                
                logger.info(f"✅ Mock order placed: {order_id} - {symbol} {transaction_type} {quantity}")
                return order_id
            
            # Format symbol for Fyers API
            fyers_symbol = f"NSE:{symbol}-EQ"
            
            # Prepare order data
            order_data = {
                "symbol": fyers_symbol,
                "qty": quantity,
                "type": order_type,
                "side": transaction_type,
                "productType": "INTRADAY",
                "limitPrice": price if order_type == OrderType.LIMIT.value else 0,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False
            }
            
            # Place order
            response = self.fyers.place_order(order_data)
            
            if response['s'] == 'ok':
                order_id = response['id']
                logger.info(f"✅ Order placed successfully: {order_id}")
                return order_id
            else:
                logger.error(f"❌ Order placement failed: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return None
    
    async def _update_position_from_order(self, order: Order):
        """Update positions based on completed order."""
        try:
            symbol = order.symbol
            
            if symbol in self._positions:
                position = self._positions[symbol]
                
                if order.transaction_type == position.transaction_type:
                    # Same direction - average the prices
                    total_quantity = position.quantity + order.filled_quantity
                    total_value = (position.average_price * position.quantity + 
                                 order.average_price * order.filled_quantity)
                    position.average_price = total_value / total_quantity
                    position.quantity = total_quantity
                else:
                    # Opposite direction - reduce position
                    position.quantity -= order.filled_quantity
                    if position.quantity <= 0:
                        del self._positions[symbol]
            else:
                # New position
                self._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=order.filled_quantity,
                    average_price=order.average_price,
                    transaction_type=order.transaction_type,
                    timestamp=order.timestamp
                )
                
        except Exception as e:
            logger.error(f"Error updating position: {e}")
    
    async def get_positions(self) -> List[Position]:
        """Get current positions."""
        try:
            if config.MOCK_MODE:
                return list(self._positions.values())
            
            # Get positions from Fyers API
            positions = self.fyers.positions()
            
            if positions['s'] == 'ok':
                fyers_positions = []
                for pos in positions['netPositions']:
                    if pos['qty'] != 0:  # Only active positions
                        position = Position(
                            symbol=pos['symbol'].split(':')[1].replace('-EQ', ''),
                            quantity=abs(pos['qty']),
                            average_price=pos['avgPrice'],
                            transaction_type="1" if pos['qty'] > 0 else "-1",
                            timestamp=datetime.now()
                        )
                        position.current_price = pos['ltp']
                        position.unrealized_pnl = pos['pl']
                        fyers_positions.append(position)
                
                return fyers_positions
            else:
                logger.error(f"Error getting positions: {positions}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_orders(self) -> List[Order]:
        """Get order history."""
        try:
            if config.MOCK_MODE:
                return list(self._orders.values())
            
            # Get orders from Fyers API
            orders = self.fyers.orderbook()
            
            if orders['s'] == 'ok':
                fyers_orders = []
                for ord in orders['orderBook']:
                    order = Order(
                        order_id=ord['id'],
                        symbol=ord['symbol'].split(':')[1].replace('-EQ', ''),
                        transaction_type=ord['side'],
                        quantity=ord['qty'],
                        order_type=ord['type'],
                        price=ord['limitPrice']
                    )
                    order.status = OrderStatus(ord['status'])
                    order.filled_quantity = ord['filledQty']
                    order.average_price = ord['avgPrice']
                    fyers_orders.append(order)
                
                return fyers_orders
            else:
                logger.error(f"Error getting orders: {orders}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            if config.MOCK_MODE:
                if order_id in self._orders:
                    self._orders[order_id].status = OrderStatus.CANCELLED
                    logger.info(f"✅ Mock order cancelled: {order_id}")
                    return True
                return False
            
            # Cancel order via Fyers API
            response = self.fyers.cancel_order({"id": order_id})
            
            if response['s'] == 'ok':
                logger.info(f"✅ Order cancelled: {order_id}")
                return True
            else:
                logger.error(f"❌ Order cancellation failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error cancelling order: {e}")
            return False
    
    async def modify_order(self, order_id: str, quantity: int = None, 
                          price: float = None) -> bool:
        """Modify an existing order."""
        try:
            if config.MOCK_MODE:
                if order_id in self._orders:
                    order = self._orders[order_id]
                    if quantity:
                        order.quantity = quantity
                    if price:
                        order.price = price
                    logger.info(f"✅ Mock order modified: {order_id}")
                    return True
                return False
            
            # Modify order via Fyers API
            modify_data = {"id": order_id}
            if quantity:
                modify_data["qty"] = quantity
            if price:
                modify_data["limitPrice"] = price
            
            response = self.fyers.modify_order(modify_data)
            
            if response['s'] == 'ok':
                logger.info(f"✅ Order modified: {order_id}")
                return True
            else:
                logger.error(f"❌ Order modification failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error modifying order: {e}")
            return False
    
    async def close_position(self, symbol: str) -> bool:
        """Close a position by placing opposite order."""
        try:
            positions = await self.get_positions()
            position = next((p for p in positions if p.symbol == symbol), None)
            
            if not position:
                logger.warning(f"No position found for {symbol}")
                return False
            
            # Place opposite order
            opposite_transaction = "-1" if position.transaction_type == "1" else "1"
            
            order_id = await self.place_order(
                symbol=symbol,
                transaction_type=opposite_transaction,
                quantity=position.quantity,
                order_type=OrderType.MARKET.value
            )
            
            if order_id:
                logger.info(f"✅ Position closed for {symbol}")
                return True
            else:
                logger.error(f"❌ Failed to close position for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error closing position: {e}")
            return False
    
    async def force_exit_all_positions(self) -> bool:
        """Force exit all positions."""
        try:
            positions = await self.get_positions()
            
            if not positions:
                logger.info("No positions to exit")
                return True
            
            logger.info(f"🚪 Force exiting {len(positions)} positions...")
            
            success_count = 0
            for position in positions:
                if await self.close_position(position.symbol):
                    success_count += 1
            
            logger.info(f"✅ Successfully exited {success_count}/{len(positions)} positions")
            return success_count == len(positions)
            
        except Exception as e:
            logger.error(f"❌ Error force exiting positions: {e}")
            return False
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """Get historical data for a symbol."""
        try:
            if config.MOCK_MODE:
                # Return mock historical data
                import random
                data = []
                base_price = 100.0
                
                for i in range(days):
                    date = datetime.now() - timedelta(days=days-i)
                    open_price = base_price * random.uniform(0.95, 1.05)
                    high_price = open_price * random.uniform(1.0, 1.08)
                    low_price = open_price * random.uniform(0.92, 1.0)
                    close_price = open_price * random.uniform(0.96, 1.04)
                    volume = random.randint(100000, 1000000)
                    
                    data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': round(open_price, 2),
                        'high': round(high_price, 2),
                        'low': round(low_price, 2),
                        'close': round(close_price, 2),
                        'volume': volume
                    })
                    
                    base_price = close_price
                
                return data
            
            # Get historical data from Fyers API
            from datetime import datetime
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            fyers_symbol = f"NSE:{symbol}-EQ"
            
            data = {
                "symbol": fyers_symbol,
                "resolution": "D",
                "date_format": "1",
                "range_from": start_date.strftime("%Y-%m-%d"),
                "range_to": end_date.strftime("%Y-%m-%d"),
                "cont_flag": "1"
            }
            
            response = self.fyers.history(data)
            
            if response['s'] == 'ok':
                historical_data = []
                candles = response['candles']
                
                for candle in candles:
                    historical_data.append({
                        'date': datetime.fromtimestamp(candle[0]).strftime('%Y-%m-%d'),
                        'open': candle[1],
                        'high': candle[2],
                        'low': candle[3],
                        'close': candle[4],
                        'volume': candle[5]
                    })
                
                return historical_data
            else:
                logger.error(f"Error getting historical data: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []


# Global broker instance
broker = FyersBroker()


async def initialize_broker() -> bool:
    """Initialize the broker interface."""
    return await broker.initialize()


async def get_broker():
    """Get the broker instance."""
    return broker
