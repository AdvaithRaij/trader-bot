"""
Test Suite for AI Trading Bot

This package contains comprehensive tests for all components of the trading bot.
Tests verify that all components work with real data (no mocks).

Test Structure:
- test_screener.py: Stock screening with NIFTY 200 universe
- test_data_aggregator.py: Data aggregation from multiple sources
- test_multi_strategy.py: Multi-strategy AI analysis
- test_strategies.py: Strategy engine CRUD and execution
- test_risk_manager.py: Risk management and position sizing
- test_trade_executor.py: Trade execution and validation
- test_api_endpoints.py: FastAPI endpoint testing
- test_end_to_end.py: Full pipeline workflows

Usage:
    # Run all tests
    pytest backend/tests/

    # Run specific test file
    pytest backend/tests/test_screener.py

    # Run with verbose output
    pytest backend/tests/ -v

    # Run with coverage
    pytest backend/tests/ --cov=backend/src
"""

import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

