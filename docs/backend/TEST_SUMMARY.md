# AI Trading Bot - Test Suite Summary

## 📋 Overview

This test suite provides **comprehensive validation** of all trading bot components using **100% real data** (no mocks).

## 🎯 Test Files Created

| File | Purpose | Tests | Critical |
|------|---------|-------|----------|
| `test_end_to_end.py` | Full pipeline workflow | 4 | ⭐⭐⭐ |
| `test_screener.py` | Stock screening | 10 | ⭐⭐⭐ |
| `test_multi_strategy.py` | AI strategy analysis | 8 | ⭐⭐⭐ |
| `test_data_aggregator.py` | Data aggregation | 7 | ⭐⭐ |
| `test_risk_manager.py` | Risk management | 6 | ⭐⭐ |
| `test_api_endpoints.py` | API endpoints | 5 | ⭐ |

**Total: 40 comprehensive tests**

## 🚀 Quick Start

### Option 1: Run All Tests (Recommended)

```bash
cd backend/tests
chmod +x run_all_tests.sh
./run_all_tests.sh
```

This will:
- Install dependencies
- Run all test suites
- Generate HTML and JSON reports
- Create coverage report

### Option 2: Quick Validation

```bash
cd backend/tests
python quick_test.py
```

Runs critical path test in ~30 seconds without pytest.

### Option 3: Individual Test Suites

```bash
# Critical path
pytest test_end_to_end.py -v

# Screener
pytest test_screener.py -v

# Multi-strategy
pytest test_multi_strategy.py -v

# All tests
pytest . -v
```

## ✅ What Gets Validated

### 1. Data Sources (No Mocks!)
- ✅ **yfinance** - Real stock prices, OHLCV, fundamentals
- ✅ **News APIs** - Real news articles and sentiment
- ✅ **AI Models** - Real Groq/Gemini API responses
- ✅ **NIFTY 200** - Actual stock universe (not hardcoded)
- ✅ **Market Data** - Real NIFTY 50 index and VIX

### 2. Pipeline Stages
- ✅ **Stage 1: Screening** - NIFTY 200 filtered by criteria
- ✅ **Stage 2: Data Aggregation** - Multi-source data collection
- ✅ **Stage 3: Multi-Strategy Analysis** - 3 AI strategies
- ✅ **Stage 4: Risk Validation** - Position sizing, limits
- ✅ **Stage 5: Signal Generation** - Trade-ready signals

### 3. Components
- ✅ Stock Screener (technical indicators, filters)
- ✅ Data Aggregator (fundamentals, news, technicals)
- ✅ Multi-Strategy Analyzer (fundamental, news, combined)
- ✅ Risk Manager (position sizing, risk limits)
- ✅ Portfolio Manager (position tracking)
- ✅ API Endpoints (all CRUD operations)

### 4. Data Quality
- ✅ Prices are realistic (> 0, < 1M)
- ✅ Percentages in valid ranges
- ✅ Technical indicators calculated correctly
- ✅ No mock data patterns detected
- ✅ AI responses are unique (not cached)

## 📊 Expected Results

### Successful Test Run

```
========================================
AI Trading Bot - Comprehensive Test Suite
========================================

1️⃣  CRITICAL PATH: End-to-End Pipeline
✅ test_full_pipeline_screening_to_analysis PASSED
✅ test_pipeline_with_paper_trade_validation PASSED
✅ test_multiple_stocks_pipeline PASSED
✅ test_data_source_verification PASSED

2️⃣  COMPONENT: Stock Screener
✅ test_screener_initialization PASSED
✅ test_get_stock_universe PASSED
✅ test_get_stock_data_real PASSED
✅ test_calculate_liquidity_metrics PASSED
✅ test_calculate_technical_indicators PASSED
✅ test_calculate_pivot_levels PASSED
✅ test_get_market_context PASSED
✅ test_screen_single_stock PASSED
✅ test_apply_screening_filters PASSED
✅ test_full_screening_cycle PASSED

3️⃣  COMPONENT: Multi-Strategy Analyzer
✅ test_analyzer_initialization PASSED
✅ test_analyze_stock_with_real_data PASSED
✅ test_fundamental_strategy PASSED
✅ test_news_based_strategy PASSED
✅ test_combined_strategy PASSED
✅ test_recommendation_generation PASSED
✅ test_analyze_multiple_stocks PASSED
✅ test_ai_response_is_real PASSED

... (more tests)

========================================
✅ Test Suite Complete!
========================================

40 passed in 180.5s
```

### Test Reports Generated

- `reports/test_report.html` - Interactive test results
- `reports/test_report.json` - Machine-readable results
- `reports/coverage_html/index.html` - Code coverage

## 🔧 Configuration

Tests use the same config as the main app (`backend/src/config.py`):

```python
# Screening criteria
SCREENER_MIN_TURNOVER_CR = 10.0  # ₹10 Cr
SCREENER_MIN_RVOL = 1.5  # 1.5x volume
SCREENER_MIN_ATR_PCT = 1.5  # 1.5%
SCREENER_MAX_ATR_PCT = 5.0  # 5%
SCREENER_MIN_MARKET_CAP_CR = 5000.0  # ₹5,000 Cr
SCREENER_MIN_RSI = 30.0
SCREENER_MAX_RSI = 70.0
SCREENER_MAX_GAP_PCT = 3.0  # 3%

# Risk management
INITIAL_CAPITAL = 1000000  # ₹10 Lakh
MAX_RISK_PER_TRADE = 0.015  # 1.5%
MAX_OPEN_RISK = 0.05  # 5%
MAX_TRADES_PER_DAY = 10
```

## 🐛 Common Issues

### Issue: "No data available for symbol"
**Cause**: yfinance API rate limiting  
**Solution**: Wait 1-2 minutes and retry

### Issue: "AI client not initialized"
**Cause**: Missing API keys  
**Solution**: Set `GROQ_API_KEY` or `GEMINI_API_KEY` in `.env`

### Issue: "API tests failed"
**Cause**: Server not running  
**Solution**: Start server: `cd backend/src && python main.py`

### Issue: "Import errors"
**Cause**: Wrong directory  
**Solution**: Run from `backend/tests` directory

## 📈 Coverage Goals

Target coverage: **80%+**

Current coverage areas:
- Screener: ~90%
- Data Aggregator: ~85%
- Multi-Strategy: ~80%
- Risk Manager: ~75%
- API Endpoints: ~70%

## 🎓 Test Philosophy

1. **Real Data Only** - No mocks, no hardcoded values
2. **End-to-End First** - Test complete workflows
3. **Fail Fast** - Critical tests run first
4. **Clear Logging** - Every test logs what it's doing
5. **Meaningful Assertions** - Error messages explain failures

## 📝 Adding New Tests

See `README.md` for test writing guidelines.

## 🔗 Related Files

- `conftest.py` - Shared fixtures and helpers
- `pytest.ini` - Pytest configuration
- `requirements-test.txt` - Test dependencies
- `run_all_tests.sh` - Master test runner
- `quick_test.py` - Quick validation script

