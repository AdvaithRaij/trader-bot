"""
Fyers Data Socket for Real-Time Price Streaming.

Uses Fyers WebSocket API for tick-by-tick price updates.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Callable, Optional, Set
from loguru import logger
import threading

from config import get_config

config = get_config()


class FyersDataSocket:
    """
    Real-time data socket for Fyers API.
    
    Provides tick-by-tick price updates via WebSocket.
    Falls back to polling if WebSocket is unavailable.
    """
    
    def __init__(self):
        self.fyers_socket = None
        self.is_connected = False
        self.subscribed_symbols: Set[str] = set()
        self.price_callbacks: List[Callable] = []
        self.latest_prices: Dict[str, Dict] = {}
        self._socket_thread: Optional[threading.Thread] = None
        
    def _on_message(self, message: Dict):
        """Handle incoming WebSocket message."""
        try:
            if isinstance(message, dict):
                symbol = message.get('symbol', '')
                if symbol:
                    # Clean symbol name (remove NSE: prefix and -EQ suffix)
                    clean_symbol = symbol.replace('NSE:', '').replace('-EQ', '')
                    
                    price_data = {
                        'symbol': clean_symbol,
                        'ltp': message.get('ltp', 0),
                        'open': message.get('open_price', 0),
                        'high': message.get('high_price', 0),
                        'low': message.get('low_price', 0),
                        'close': message.get('prev_close_price', 0),
                        'volume': message.get('vol_traded_today', 0),
                        'change': message.get('ch', 0),
                        'changePercent': message.get('chp', 0),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self.latest_prices[clean_symbol] = price_data
                    
                    # Notify all callbacks
                    for callback in self.price_callbacks:
                        try:
                            callback(price_data)
                        except Exception as e:
                            logger.error(f"Error in price callback: {e}")
                            
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    def _on_error(self, error):
        """Handle WebSocket error."""
        logger.error(f"Fyers WebSocket error: {error}")
        self.is_connected = False
    
    def _on_close(self):
        """Handle WebSocket close."""
        logger.warning("Fyers WebSocket closed")
        self.is_connected = False
    
    def _on_open(self):
        """Handle WebSocket open."""
        logger.info("✅ Fyers WebSocket connected")
        self.is_connected = True
    
    async def connect(self) -> bool:
        """
        Connect to Fyers data socket.
        
        Returns:
            True if connected successfully
        """
        if config.MOCK_MODE:
            logger.info("🤖 Mock mode - using simulated price updates")
            self.is_connected = True
            return True
        
        try:
            from fyers_apiv3.FyersWebsocket import data_ws
            
            # Initialize data socket
            self.fyers_socket = data_ws.FyersDataSocket(
                access_token=f"{config.FYERS_APP_ID}:{config.FYERS_ACCESS_TOKEN}",
                log_path="",
                litemode=False,
                write_to_file=False,
                reconnect=True,
                on_connect=self._on_open,
                on_close=self._on_close,
                on_error=self._on_error,
                on_message=self._on_message
            )
            
            # Connect in a separate thread
            def run_socket():
                self.fyers_socket.connect()
            
            self._socket_thread = threading.Thread(target=run_socket, daemon=True)
            self._socket_thread.start()
            
            # Wait for connection
            await asyncio.sleep(2)
            
            if self.is_connected:
                logger.info("✅ Fyers data socket connected")
                return True
            else:
                logger.warning("⚠️ Fyers data socket connection pending")
                return True  # Still return True, connection may establish later
                
        except ImportError:
            logger.warning("⚠️ fyers_apiv3 not installed - using polling fallback")
            return False
        except Exception as e:
            logger.error(f"❌ Error connecting to Fyers data socket: {e}")
            return False
    
    def subscribe(self, symbols: List[str]):
        """Subscribe to price updates for symbols."""
        if not symbols:
            return
        
        # Format symbols for Fyers
        fyers_symbols = [f"NSE:{s}-EQ" for s in symbols if ':' not in s]
        
        self.subscribed_symbols.update(symbols)
        
        if self.fyers_socket and self.is_connected:
            try:
                self.fyers_socket.subscribe(symbols=fyers_symbols, data_type="SymbolUpdate")
                logger.info(f"📊 Subscribed to: {symbols}")
            except Exception as e:
                logger.error(f"Error subscribing to symbols: {e}")
    
    def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from price updates."""
        fyers_symbols = [f"NSE:{s}-EQ" for s in symbols if ':' not in s]

        for s in symbols:
            self.subscribed_symbols.discard(s)

        if self.fyers_socket and self.is_connected:
            try:
                self.fyers_socket.unsubscribe(symbols=fyers_symbols)
                logger.info(f"📊 Unsubscribed from: {symbols}")
            except Exception as e:
                logger.error(f"Error unsubscribing: {e}")

    def add_price_callback(self, callback: Callable):
        """Add a callback for price updates."""
        if callback not in self.price_callbacks:
            self.price_callbacks.append(callback)

    def remove_price_callback(self, callback: Callable):
        """Remove a price callback."""
        if callback in self.price_callbacks:
            self.price_callbacks.remove(callback)

    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """Get the latest cached price for a symbol."""
        return self.latest_prices.get(symbol)

    def get_all_prices(self) -> Dict[str, Dict]:
        """Get all cached prices."""
        return self.latest_prices.copy()

    def disconnect(self):
        """Disconnect from data socket."""
        if self.fyers_socket:
            try:
                self.fyers_socket.close_connection()
            except Exception as e:
                logger.error(f"Error closing data socket: {e}")

        self.is_connected = False
        self.subscribed_symbols.clear()
        logger.info("📊 Fyers data socket disconnected")


# Global data socket instance
fyers_data_socket = FyersDataSocket()

