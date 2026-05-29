"""
Pytest configuration and shared fixtures for all tests.

This file contains common fixtures and configuration used across all test files.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Configure logger for tests
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_symbols():
    """Provide a list of test symbols from NIFTY 50."""
    return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]


@pytest.fixture
def test_timestamp():
    """Provide a consistent timestamp for tests."""
    return datetime.now()


@pytest.fixture
async def screener():
    """Create a StockScreener instance."""
    from screener import StockScreener
    async with StockScreener() as s:
        yield s


@pytest.fixture
async def data_aggregator():
    """Create a DataAggregator instance."""
    from data_aggregator import DataAggregator
    from news_aggregator import NewsAggregator
    
    news_agg = NewsAggregator()
    agg = DataAggregator(news_aggregator=news_agg)
    yield agg


@pytest.fixture
def multi_strategy_analyzer():
    """Create a MultiStrategyAnalyzer instance."""
    from multi_strategy_analyzer import MultiStrategyAnalyzer
    return MultiStrategyAnalyzer()


@pytest.fixture
def risk_manager():
    """Create a RiskManager instance."""
    from risk_manager import RiskManager
    return RiskManager()


@pytest.fixture
def portfolio_manager():
    """Create a PortfolioManager instance."""
    from portfolio_manager import PortfolioManager
    return PortfolioManager()


# Test data validation helpers
def assert_real_price(price: float, symbol: str):
    """Assert that a price is real (not mock data)."""
    assert price > 0, f"Price for {symbol} must be positive"
    assert price < 1000000, f"Price for {symbol} seems unrealistic: {price}"
    assert isinstance(price, (int, float)), f"Price must be numeric, got {type(price)}"


def assert_valid_percentage(pct: float, field_name: str):
    """Assert that a percentage is valid."""
    assert -100 <= pct <= 1000, f"{field_name} must be between -100% and 1000%, got {pct}%"
    assert isinstance(pct, (int, float)), f"{field_name} must be numeric"


def assert_no_mock_data(data: dict, context: str):
    """Assert that data doesn't contain obvious mock patterns."""
    # Check for common mock indicators
    str_data = str(data).lower()
    mock_indicators = ["mock", "fake", "test_", "dummy", "placeholder"]
    
    for indicator in mock_indicators:
        assert indicator not in str_data, f"Found mock indicator '{indicator}' in {context}: {data}"

