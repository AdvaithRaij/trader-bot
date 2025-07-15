"""
Test suite for the screener module.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from screener import StockScreener, screen_top_stocks


class TestStockScreener:
    """Test cases for StockScreener class."""
    
    @pytest.fixture
    def screener(self):
        """Create a screener instance for testing."""
        return StockScreener()
    
    @pytest.fixture
    def mock_stock_data(self):
        """Mock stock data for testing."""
        dates = pd.date_range('2024-01-01', periods=100, freq='1min')
        data = pd.DataFrame({
            'Open': [100 + i * 0.1 for i in range(100)],
            'High': [101 + i * 0.1 for i in range(100)],
            'Low': [99 + i * 0.1 for i in range(100)],
            'Close': [100.5 + i * 0.1 for i in range(100)],
            'Volume': [10000 + i * 100 for i in range(100)]
        }, index=dates)
        return data
    
    def test_screener_initialization(self, screener):
        """Test screener initialization."""
        assert screener is not None
        assert screener.nse_symbols is not None
        assert len(screener.nse_symbols) > 0
    
    def test_calculate_volume_metrics(self, screener, mock_stock_data):
        """Test volume metrics calculation."""
        metrics = screener.calculate_volume_metrics(mock_stock_data)
        
        assert 'current_volume' in metrics
        assert 'avg_volume_5d' in metrics
        assert 'volume_ratio' in metrics
        assert 'volatility_pct' in metrics
        assert 'price_change_pct' in metrics
        
        # Check that values are reasonable
        assert metrics['current_volume'] > 0
        assert metrics['volume_ratio'] > 0
        assert metrics['volatility_pct'] >= 0
    
    def test_calculate_technical_indicators(self, screener, mock_stock_data):
        """Test technical indicators calculation."""
        indicators = screener.calculate_technical_indicators(mock_stock_data)
        
        assert 'vwap' in indicators
        assert 'rsi' in indicators
        assert 'sma_20' in indicators
        assert 'price_vs_vwap_pct' in indicators
        assert 'above_vwap' in indicators
        
        # Check RSI is in valid range
        assert 0 <= indicators['rsi'] <= 100
        assert isinstance(indicators['above_vwap'], bool)
    
    def test_apply_screening_filters(self, screener):
        """Test screening filters."""
        # Mock stock data
        mock_stocks = [
            {
                'symbol': 'TEST1',
                'volume_ratio': 1.5,
                'volatility_pct': 2.0,
                'rsi': 45,
                'current_volume': 200000,
                'price_change_pct': 1.0,
                'above_vwap': True
            },
            {
                'symbol': 'TEST2',
                'volume_ratio': 0.8,  # Below threshold
                'volatility_pct': 1.5,
                'rsi': 50,
                'current_volume': 150000,
                'price_change_pct': 0.8,
                'above_vwap': False
            }
        ]
        
        filtered = screener.apply_screening_filters(mock_stocks)
        
        # Only TEST1 should pass filters
        assert len(filtered) == 1
        assert filtered[0]['symbol'] == 'TEST1'
        assert 'screening_score' in filtered[0]
    
    @pytest.mark.asyncio
    async def test_get_top_stocks_by_volume(self, screener):
        """Test getting top stocks by volume."""
        stocks = await screener.get_top_stocks_by_volume(10)
        
        assert isinstance(stocks, list)
        assert len(stocks) <= 10
        assert all(isinstance(symbol, str) for symbol in stocks)
    
    @pytest.mark.asyncio
    async def test_screen_top_stocks_function(self):
        """Test the standalone screen_top_stocks function."""
        stocks = await screen_top_stocks(5)
        
        assert isinstance(stocks, list)
        assert len(stocks) <= 5
        
        # Check structure of returned stocks
        if stocks:
            stock = stocks[0]
            assert 'symbol' in stock
            assert 'screening_score' in stock
            assert 'volume_ratio' in stock


@pytest.mark.asyncio
async def test_screener_integration():
    """Integration test for the screener."""
    async with StockScreener() as screener:
        # Test screening a few stocks
        stocks = await screener.screen_stocks(3)
        
        assert isinstance(stocks, list)
        assert len(stocks) <= 3
        
        # Verify structure
        for stock in stocks:
            assert 'symbol' in stock
            assert 'timestamp' in stock
            assert 'screening_score' in stock


if __name__ == "__main__":
    pytest.main([__file__])
