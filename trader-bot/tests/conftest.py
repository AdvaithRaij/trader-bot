"""
Test configuration for pytest.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        'INITIAL_CAPITAL': 100000.0,
        'MAX_CAPITAL_PER_TRADE': 0.01,
        'MAX_ACTIVE_TRADES': 2,
        'AI_CONFIDENCE_THRESHOLD': 0.8,
        'MOCK_MODE': True,
        'MOCK_BROKER': True,
        'MOCK_AI': True
    }
