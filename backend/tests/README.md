# AI Trading Bot - Comprehensive Test Suite

This directory contains a complete testing suite for the AI Trading Bot that verifies **ALL components work with real data** (no mocks).

## 🎯 Test Coverage

### Critical Path Tests
- **`test_end_to_end.py`** - Full pipeline: Screening → Analysis → Signal → Paper Trade
  - Most important test - verifies the entire workflow
  - Uses real data from yfinance, news APIs, and AI models
  - Validates no mock data is used anywhere

### Component Tests
- **`test_screener.py`** - Stock screening with NIFTY 200 universe
  - Real data from yfinance
  - Technical indicators (RSI, EMA, ATR)
  - Volume and liquidity filters
  - Market context (NIFTY, VIX)

- **`test_multi_strategy.py`** - Multi-strategy AI analysis
  - Fundamental strategy (P/E, EPS, valuation)
  - News-based strategy (sentiment, momentum)
  - Combined strategy (holistic analysis)
  - Real AI responses from Groq/Gemini

- **`test_risk_manager.py`** - Risk management
  - Position sizing calculations
  - Stop-loss validation
  - Risk-reward ratio checks
  - Max trades and open risk limits

- **`test_api_endpoints.py`** - FastAPI endpoints
  - Stock search (NIFTY 200)
  - Real-time quotes
  - Screening API
  - Multi-strategy analysis API

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend/tests
pip install -r requirements-test.txt
```

### 2. Run All Tests

```bash
chmod +x run_all_tests.sh
./run_all_tests.sh
```

### 3. Run Specific Tests

```bash
# Critical path only
pytest test_end_to_end.py -v

# Screener tests
pytest test_screener.py -v

# Multi-strategy tests
pytest test_multi_strategy.py -v

# Risk manager tests
pytest test_risk_manager.py -v

# API tests (requires server running)
pytest test_api_endpoints.py -v
```

## 📊 Test Reports

After running tests, reports are generated in `reports/`:

- **`test_report.html`** - Interactive HTML test report
- **`test_report.json`** - Machine-readable JSON report
- **`coverage_html/index.html`** - Code coverage report

View coverage:
```bash
open reports/coverage_html/index.html
```

## ✅ What Gets Tested

### Data Sources Verification
- ✅ yfinance for stock prices and fundamentals
- ✅ News aggregator for real news and sentiment
- ✅ AI models (Groq/Gemini) for strategy analysis
- ✅ NIFTY 200 universe (not hardcoded lists)
- ✅ Market context (NIFTY 50, VIX)

### Pipeline Stages
1. **Screening** - NIFTY 200 stocks filtered by liquidity, volatility, RSI
2. **Data Aggregation** - Fundamentals, news, technical indicators
3. **Multi-Strategy Analysis** - 3 AI strategies generate signals
4. **Risk Validation** - Position sizing, stop-loss checks
5. **Paper Trade Signal** - Ready-to-execute trade details

### Assertions
- No mock data patterns detected
- Prices are realistic (> 0, < 1M)
- Percentages are valid (-100% to 1000%)
- Technical indicators in valid ranges
- AI responses are unique (not cached)
- Risk metrics within configured limits

## 🔧 Configuration

Tests use the same configuration as the main application (`config.py`).

Key settings:
- `INITIAL_CAPITAL` - Starting capital for position sizing
- `MAX_RISK_PER_TRADE` - Maximum risk per trade (default 1.5%)
- `MAX_OPEN_RISK` - Maximum total open risk (default 5%)
- `SCREENER_MIN_TURNOVER_CR` - Minimum turnover (default ₹10 Cr)
- `SCREENER_MIN_RVOL` - Minimum relative volume (default 1.5x)

## 🐛 Troubleshooting

### Tests Fail with "No data available"
- **Cause**: yfinance API rate limiting or network issues
- **Solution**: Wait a few minutes and retry, or reduce test parallelism

### API Tests Fail
- **Cause**: FastAPI server not running
- **Solution**: Start the server first:
  ```bash
  cd backend/src
  python main.py
  ```

### AI Tests Fail
- **Cause**: Missing API keys (GROQ_API_KEY or GEMINI_API_KEY)
- **Solution**: Set environment variables in `.env` file

### Import Errors
- **Cause**: Python path not set correctly
- **Solution**: Run from `backend/tests` directory or set PYTHONPATH:
  ```bash
  export PYTHONPATH="${PYTHONPATH}:$(pwd)/../src"
  ```

## 📝 Writing New Tests

Follow this pattern:

```python
import pytest
from loguru import logger
from conftest import assert_real_price, assert_no_mock_data

class TestMyComponent:
    """Test description."""
    
    @pytest.mark.asyncio
    async def test_my_feature(self):
        """Test specific feature."""
        logger.info("Testing my feature...")
        
        # Your test code here
        result = await my_function()
        
        # Assertions
        assert result is not None
        assert_real_price(result.price, "SYMBOL")
        assert_no_mock_data(result.model_dump(), "context")
        
        logger.success("✅ Test passed")
```

## 🎓 Best Practices

1. **Always use real data** - No mocks, no hardcoded values
2. **Log progress** - Use logger.info() to show what's being tested
3. **Meaningful assertions** - Include context in error messages
4. **Test isolation** - Each test should be independent
5. **Async tests** - Use `@pytest.mark.asyncio` for async functions
6. **Timeouts** - Set reasonable timeouts for API calls

## 📈 Success Criteria

A successful test run should show:
- ✅ All data from real sources (yfinance, news APIs, AI)
- ✅ No mock data patterns detected
- ✅ Prices and metrics in realistic ranges
- ✅ Full pipeline executes without errors
- ✅ Risk management validates trades correctly
- ✅ API endpoints return expected data structures

## 🔗 Related Documentation

- [PLAN_OF_ACTION.md](../../PLAN_OF_ACTION.md) - Trading strategy and pipeline design
- [backend/src/README.md](../src/README.md) - Source code documentation
- [pytest documentation](https://docs.pytest.org/) - Testing framework docs

