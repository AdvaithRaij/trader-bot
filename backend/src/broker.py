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
    
    def _setup_fyers_api(self, token: str = None):
        """Setup Fyers API connection.

        Args:
            token: Optional token to use. If not provided, uses config.FYERS_ACCESS_TOKEN
        """
        try:
            from fyers_apiv3 import fyersModel

            # Use provided token or fall back to config
            access_token = token or config.FYERS_ACCESS_TOKEN

            # Initialize Fyers API
            self.fyers = fyersModel.FyersModel(
                client_id=config.FYERS_APP_ID,
                is_async=False,
                token=access_token,
                log_path=""
            )

            logger.info("✅ Fyers API initialized")

        except Exception as e:
            logger.error(f"❌ Error setting up Fyers API: {e}")
            raise

    def reinitialize_with_token(self, new_token: str):
        """Reinitialize the Fyers API with a new token.

        Args:
            new_token: The new access token to use
        """
        logger.info("🔄 Reinitializing Fyers API with new token...")
        self._setup_fyers_api(token=new_token)
        self.is_connected = False  # Reset connection status
    
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
            logger.debug(f"Fyers funds response: {funds}")

            if funds.get('s') == 'ok' and funds.get('fund_limit'):
                fund_data = funds['fund_limit'][0]
                logger.debug(f"Fund data keys: {fund_data.keys()}")

                # Try different field names that Fyers might use
                available = (
                    fund_data.get('equityAmount') or
                    fund_data.get('equity') or
                    fund_data.get('available_balance') or
                    fund_data.get('availableBalance') or
                    fund_data.get('total') or
                    0.0
                )

                used = (
                    fund_data.get('used_margin') or
                    fund_data.get('usedMargin') or
                    fund_data.get('utilized') or
                    0.0
                )

                self._account_info = {
                    'available_balance': float(available),
                    'used_margin': float(used),
                    'total_margin': float(available) + float(used)
                }
                logger.info(f"💰 Account info updated: Available={available}, Used={used}")
            else:
                logger.warning(f"Fyers funds response not OK: {funds}")

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
                # Use cached mock prices to prevent random changes on each refresh
                if not hasattr(self, '_mock_price_cache'):
                    self._mock_price_cache = {}
                    self._mock_price_timestamp = {}

                import random
                from datetime import datetime, timedelta

                # Base prices for common stocks
                base_prices = {
                    'RELIANCE': 2413.80, 'TCS': 3890.50, 'INFY': 1520.25,
                    'HDFCBANK': 1645.30, 'ICICIBANK': 1050.75, 'SBIN': 750.60,
                    'KOTAKBANK': 1780.40, 'AXISBANK': 1090.25, 'WIPRO': 485.30,
                    'HINDUNILVR': 2450.80, 'ITC': 455.25, 'BHARTIARTL': 1580.60,
                    'ASIANPAINT': 2890.40, 'MARUTI': 11250.75, 'LT': 3450.20,
                    'BAJFINANCE': 6850.30, 'TITAN': 3250.45, 'TATAMOTORS': 780.25,
                    'SUNPHARMA': 1680.50, 'TECHM': 1540.75
                }

                # Check if we have a cached price that's still valid (within 5 minutes)
                now = datetime.now()
                cache_key = symbol.upper().replace('NSE:', '').replace('-EQ', '')

                if cache_key in self._mock_price_cache:
                    cached_time = self._mock_price_timestamp.get(cache_key, now)
                    if (now - cached_time) < timedelta(minutes=5):
                        # Add tiny variation for realism (0.1% max)
                        return self._mock_price_cache[cache_key] * (1 + random.uniform(-0.001, 0.001))

                # Generate new cached price
                base_price = base_prices.get(cache_key, 1000.0)
                # Add initial variation (-2% to +2%)
                variation = random.uniform(-0.02, 0.02)
                cached_price = round(base_price * (1 + variation), 2)

                self._mock_price_cache[cache_key] = cached_price
                self._mock_price_timestamp[cache_key] = now

                return cached_price
            
            # Use batch LTP with cache
            prices = await self.get_batch_ltp([symbol])
            return prices.get(symbol, 0.0)

        except Exception as e:
            logger.error(f"Error getting LTP for {symbol}: {e}")
            return 0.0

    async def get_batch_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get Last Traded Price for multiple symbols in a single API call.
        Results are cached for 5 seconds to prevent rate limiting.
        """
        import time

        # Initialize cache if not exists
        if not hasattr(self, '_ltp_cache'):
            self._ltp_cache: Dict[str, float] = {}
            self._ltp_cache_time: float = 0

        now = time.time()
        cache_ttl = 5  # 5 seconds cache

        # Check if cache is still valid
        if now - self._ltp_cache_time < cache_ttl:
            # Return cached prices for requested symbols
            result = {s: self._ltp_cache.get(s, 0.0) for s in symbols}
            if all(result.values()):  # All symbols found in cache
                return result

        try:
            if config.MOCK_MODE:
                # Return mock prices
                base_prices = {
                    'RELIANCE': 2413.80, 'TCS': 3890.50, 'INFY': 1520.25,
                    'HDFCBANK': 1645.30, 'ICICIBANK': 1050.75, 'SBIN': 750.60,
                    'ASIANPAINT': 2890.40, 'ADANIENT': 2350.50
                }
                return {s: base_prices.get(s, 1000.0) for s in symbols}

            # Filter out empty/invalid symbols
            valid_symbols = [s for s in symbols if s and isinstance(s, str) and s.strip()]
            if not valid_symbols:
                logger.warning("No valid symbols provided for batch LTP")
                return {s: 0.0 for s in symbols}

            # Format symbols for Fyers API (NSE:SYMBOL-EQ)
            fyers_symbols = ",".join([f"NSE:{s}-EQ" for s in valid_symbols])
            logger.debug(f"Fetching batch LTP for: {fyers_symbols}")

            # Single API call for all symbols
            quotes = self.fyers.quotes({"symbols": fyers_symbols})

            if quotes['s'] == 'ok' and quotes['d']:
                result = {}
                for quote in quotes['d']:
                    # Extract symbol name from NSE:SYMBOL-EQ format
                    full_symbol = quote['n']
                    symbol_name = full_symbol.replace('NSE:', '').replace('-EQ', '')
                    price = quote['v']['lp']
                    result[symbol_name] = price
                    self._ltp_cache[symbol_name] = price

                self._ltp_cache_time = now
                logger.debug(f"📊 Batch LTP fetched for {len(symbols)} symbols (1 API call)")
                return result
            else:
                logger.error(f"Error getting batch LTP: {quotes}")
                return {s: 0.0 for s in symbols}

        except Exception as e:
            logger.error(f"Error getting batch LTP: {e}")
            return {s: 0.0 for s in symbols}
    
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
        """Get historical data for a symbol (daily timeframe)."""
        return await self.get_candles(symbol, "D", days)

    async def get_candles(
        self,
        symbol: str,
        resolution: str = "5",
        days: int = 5,
        end_time: int = None
    ) -> List[Dict]:
        """
        Get candle data for a symbol with specified resolution.

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            resolution: Timeframe - '1', '5', '15', '30', '60', '240', 'D', 'W'
            days: Number of days of data to fetch
            end_time: Unix timestamp for end time (optional, defaults to now)

        Returns:
            List of candle dictionaries with time, open, high, low, close, volume
        """
        try:
            # Get current LTP for realistic mock data
            current_price = await self.get_ltp(symbol) or 1000

            if config.MOCK_MODE:
                return self._generate_mock_candles(current_price, resolution, days)

            # Get candles from Fyers API
            end_ts = end_time or int(datetime.now().timestamp())
            start_ts = end_ts - (days * 24 * 60 * 60)

            fyers_symbol = f"NSE:{symbol}-EQ"

            data = {
                "symbol": fyers_symbol,
                "resolution": resolution,
                "date_format": "0",  # Use epoch timestamp
                "range_from": str(start_ts),
                "range_to": str(end_ts),
                "cont_flag": "1"
            }

            response = self.fyers.history(data)

            if response.get('s') == 'ok':
                candles = response.get('candles', [])
                return [
                    {
                        'time': int(c[0]),
                        'open': c[1],
                        'high': c[2],
                        'low': c[3],
                        'close': c[4],
                        'volume': c[5]
                    }
                    for c in candles
                ]
            else:
                logger.error(f"Error getting candles: {response}")
                # Fallback to mock data
                return self._generate_mock_candles(current_price, resolution, days)

        except Exception as e:
            logger.error(f"Error getting candles for {symbol}: {e}")
            current_price = await self.get_ltp(symbol) or 1000
            return self._generate_mock_candles(current_price, resolution, days)

    def _generate_mock_candles(self, current_price: float, resolution: str, days: int) -> List[Dict]:
        """Generate realistic mock candle data ending at current price."""
        import random

        # Convert resolution to minutes
        res_map = {'1': 1, '5': 5, '15': 15, '30': 30, '60': 60, '240': 240, 'D': 1440, 'W': 10080}
        interval_minutes = res_map.get(resolution, 5)

        # Calculate number of candles (account for market hours ~6.25h/day = 375 min)
        if interval_minutes >= 1440:  # Daily or weekly
            total_candles = days * (1440 // interval_minutes) if interval_minutes == 1440 else days // 7
        else:
            candles_per_day = 375 // interval_minutes
            total_candles = days * candles_per_day

        total_candles = max(50, min(500, total_candles))  # Limit range

        # Work backwards from current price
        candles = []
        now = datetime.now()
        price = current_price

        # Volatility scales with timeframe
        base_volatility = 0.002
        volatility = base_volatility * (interval_minutes / 5) ** 0.5

        for i in range(total_candles - 1, -1, -1):
            # Calculate time for this candle
            if interval_minutes >= 1440:
                candle_time = now - timedelta(days=i)
            else:
                candle_time = now - timedelta(minutes=i * interval_minutes)

            # Skip weekends for intraday
            if interval_minutes < 1440 and candle_time.weekday() >= 5:
                continue

            # Generate realistic OHLC
            change = random.gauss(0, volatility)
            open_price = price * (1 - change)
            close_price = price
            high_price = max(open_price, close_price) * random.uniform(1.001, 1.003 + volatility)
            low_price = min(open_price, close_price) * random.uniform(0.997 - volatility, 0.999)

            candles.append({
                'time': int(candle_time.timestamp()),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': random.randint(50000, 500000)
            })

            # Move price backwards (reverse the change)
            price = open_price

        # Sort by time ascending
        candles.sort(key=lambda x: x['time'])
        return candles


# Global broker instance
broker = FyersBroker()


async def initialize_broker() -> bool:
    """Initialize the broker interface."""
    return await broker.initialize()


async def get_broker():
    """Get the broker instance."""
    return broker
