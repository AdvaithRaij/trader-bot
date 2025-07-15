"""
Stock Screener Module for Trading Bot.
Screens and filters top stocks based on volume, volatility, and intraday trading potential.
"""

import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

from config import get_config

config = get_config()


class StockScreener:
    """
    Screens stocks for intraday trading opportunities.
    Pulls top stocks by volume and filters based on predefined criteria.
    """
    
    def __init__(self):
        self.config = config
        self.session = None
        
        # NSE Top 500 symbols (sample - in production, use full list)
        self.nse_symbols = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "KOTAKBANK",
            "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "ASIANPAINT", "MARUTI",
            "BAJFINANCE", "HCLTECH", "AXISBANK", "LT", "DMART", "SUNPHARMA",
            "TITAN", "ULTRACEMCO", "WIPRO", "NESTLEIND", "POWERGRID", "NTPC",
            "TECHM", "JSWSTEEL", "TATAMOTORS", "INDUSINDBK", "ADANIENT", "ONGC",
            "BAJAJFINSV", "COALINDIA", "HDFCLIFE", "GRASIM", "SBILIFE", "BRITANNIA",
            "DRREDDY", "EICHERMOT", "APOLLOHOSP", "ADANIPORTS", "CIPLA", "BPCL",
            "TATACONSUM", "DIVISLAB", "TATASTEEL", "HEROMOTOCO", "BAJAJ-AUTO",
            "HINDALCO", "UPL", "SHREECEM"
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def get_stock_data(self, symbol: str, period: str = "5d") -> Optional[pd.DataFrame]:
        """
        Fetch stock data using yfinance.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            period: Data period ('1d', '5d', '1mo')
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            # Add .NS suffix for NSE stocks
            if not symbol.endswith('.NS'):
                symbol = f"{symbol}.NS"
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval="1m")
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return None
                
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def calculate_volume_metrics(self, data: pd.DataFrame) -> Dict:
        """
        Calculate volume-based metrics for screening.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary with volume metrics
        """
        if data.empty or len(data) < 10:
            return {}
        
        try:
            current_volume = data['Volume'].iloc[-1]
            avg_volume_5d = data['Volume'].mean()
            volume_ratio = current_volume / avg_volume_5d if avg_volume_5d > 0 else 0
            
            # Price volatility (ATR-like measure)
            high_low = data['High'] - data['Low']
            volatility = high_low.mean() / data['Close'].mean() * 100
            
            # Recent price movement
            price_change = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / 
                          data['Close'].iloc[0]) * 100
            
            return {
                'current_volume': current_volume,
                'avg_volume_5d': avg_volume_5d,
                'volume_ratio': volume_ratio,
                'volatility_pct': volatility,
                'price_change_pct': price_change,
                'current_price': data['Close'].iloc[-1],
                'data_points': len(data)
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume metrics: {e}")
            return {}
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict:
        """
        Calculate basic technical indicators for filtering.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary with technical indicators
        """
        if data.empty or len(data) < 20:
            return {}
        
        try:
            close = data['Close']
            high = data['High']
            low = data['Low']
            volume = data['Volume']
            
            # VWAP calculation
            typical_price = (high + low + close) / 3
            vwap = (typical_price * volume).cumsum() / volume.cumsum()
            current_vwap = vwap.iloc[-1]
            
            # RSI calculation (simplified)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            
            # Simple moving averages
            sma_20 = close.rolling(window=20).mean().iloc[-1]
            sma_50 = close.rolling(window=min(50, len(close))).mean().iloc[-1]
            
            # Price relative to VWAP
            price_vs_vwap = ((close.iloc[-1] - current_vwap) / current_vwap) * 100
            
            return {
                'vwap': current_vwap,
                'rsi': current_rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'price_vs_vwap_pct': price_vs_vwap,
                'above_vwap': close.iloc[-1] > current_vwap
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}
    
    def screen_single_stock(self, symbol: str) -> Optional[Dict]:
        """
        Screen a single stock and return its metrics.
        
        Args:
            symbol: Stock symbol to screen
            
        Returns:
            Dictionary with stock screening results or None
        """
        try:
            logger.info(f"Screening {symbol}")
            
            # Get stock data
            data = self.get_stock_data(symbol)
            if data is None or data.empty:
                return None
            
            # Calculate metrics
            volume_metrics = self.calculate_volume_metrics(data)
            technical_metrics = self.calculate_technical_indicators(data)
            
            if not volume_metrics or not technical_metrics:
                return None
            
            # Combine all metrics
            result = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                **volume_metrics,
                **technical_metrics
            }
            
            logger.info(f"✅ Screened {symbol}: Vol ratio={volume_metrics.get('volume_ratio', 0):.2f}, "
                       f"RSI={technical_metrics.get('rsi', 0):.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error screening {symbol}: {e}")
            return None
    
    def apply_screening_filters(self, stock_data: List[Dict]) -> List[Dict]:
        """
        Apply filtering criteria to screened stocks.
        
        Args:
            stock_data: List of stock screening results
            
        Returns:
            Filtered list of stocks meeting criteria
        """
        filtered_stocks = []
        
        for stock in stock_data:
            try:
                # Filter criteria
                volume_ratio = stock.get('volume_ratio', 0)
                volatility = stock.get('volatility_pct', 0)
                rsi = stock.get('rsi', 50)
                current_volume = stock.get('current_volume', 0)
                price_change = abs(stock.get('price_change_pct', 0))
                
                # Filtering rules
                passes_volume = volume_ratio >= 1.2  # 20% above average volume
                passes_volatility = 0.5 <= volatility <= 5.0  # Reasonable volatility
                passes_rsi = 20 <= rsi <= 80  # Not extremely overbought/oversold
                passes_min_volume = current_volume >= 100000  # Minimum liquidity
                passes_movement = price_change >= 0.5  # At least 0.5% movement
                
                if all([passes_volume, passes_volatility, passes_rsi, 
                       passes_min_volume, passes_movement]):
                    
                    # Calculate screening score
                    score = (
                        min(volume_ratio, 3.0) * 0.3 +  # Volume weight
                        min(volatility, 3.0) * 0.2 +    # Volatility weight
                        price_change * 0.3 +             # Movement weight
                        (1 if stock.get('above_vwap', False) else 0.5) * 0.2  # VWAP weight
                    )
                    
                    stock['screening_score'] = score
                    filtered_stocks.append(stock)
                    
                    logger.info(f"✅ {stock['symbol']} passed filters (Score: {score:.2f})")
                else:
                    logger.debug(f"❌ {stock['symbol']} filtered out")
                    
            except Exception as e:
                logger.error(f"Error filtering {stock.get('symbol', 'unknown')}: {e}")
        
        return filtered_stocks
    
    async def get_top_stocks_by_volume(self, limit: int = 50) -> List[str]:
        """
        Get top stocks by volume (mock implementation).
        In production, this would connect to real market data APIs.
        
        Args:
            limit: Number of stocks to return
            
        Returns:
            List of stock symbols
        """
        # Mock implementation - return sample stocks
        # In production, this would query real market data APIs
        return self.nse_symbols[:limit]
    
    async def screen_stocks(self, max_stocks: int = 10) -> List[Dict]:
        """
        Main screening function to get top intraday trading candidates.
        
        Args:
            max_stocks: Maximum number of stocks to return
            
        Returns:
            List of top stocks for intraday trading
        """
        try:
            logger.info(f"🔍 Starting stock screening for top {max_stocks} stocks")
            
            # Get top stocks by volume
            top_symbols = await self.get_top_stocks_by_volume(50)
            logger.info(f"Got {len(top_symbols)} symbols for screening")
            
            # Screen each stock
            screened_stocks = []
            for symbol in top_symbols:
                stock_data = self.screen_single_stock(symbol)
                if stock_data:
                    screened_stocks.append(stock_data)
                
                # Don't overwhelm APIs
                await asyncio.sleep(0.1)
            
            logger.info(f"Screened {len(screened_stocks)} stocks successfully")
            
            # Apply filters
            filtered_stocks = self.apply_screening_filters(screened_stocks)
            logger.info(f"After filtering: {len(filtered_stocks)} stocks remain")
            
            # Sort by screening score and return top stocks
            filtered_stocks.sort(key=lambda x: x.get('screening_score', 0), reverse=True)
            top_stocks = filtered_stocks[:max_stocks]
            
            logger.info(f"🎯 Selected top {len(top_stocks)} stocks for trading:")
            for i, stock in enumerate(top_stocks, 1):
                logger.info(f"{i}. {stock['symbol']} (Score: {stock['screening_score']:.2f})")
            
            return top_stocks
            
        except Exception as e:
            logger.error(f"Error in stock screening: {e}")
            return []


# Standalone function for easy import
async def screen_top_stocks(max_stocks: int = 10) -> List[Dict]:
    """
    Convenience function to screen top stocks.
    
    Args:
        max_stocks: Maximum number of stocks to return
        
    Returns:
        List of top stocks for intraday trading
    """
    async with StockScreener() as screener:
        return await screener.screen_stocks(max_stocks)


if __name__ == "__main__":
    # Test the screener
    async def test_screener():
        try:
            stocks = await screen_top_stocks(5)
            print(f"\n✅ Successfully screened {len(stocks)} stocks")
            
            if stocks:
                print("\nTop stocks for intraday trading:")
                for i, stock in enumerate(stocks, 1):
                    print(f"{i}. {stock['symbol']}: "
                          f"Score={stock['screening_score']:.2f}, "
                          f"Vol Ratio={stock['volume_ratio']:.2f}, "
                          f"RSI={stock['rsi']:.1f}")
            else:
                print("No stocks passed the screening criteria")
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    asyncio.run(test_screener())
