# AI Trading Bot - Validation Checklist

Use this checklist to verify the trading bot is working correctly with real data.

## ✅ Pre-Test Setup

- [ ] Python 3.9+ installed
- [ ] All dependencies installed (`pip install -r requirements-test.txt`)
- [ ] Environment variables set (`.env` file with API keys)
  - [ ] `GROQ_API_KEY` or `GEMINI_API_KEY`
  - [ ] News API keys (if using)
- [ ] Internet connection active (for yfinance, news APIs)
- [ ] In correct directory (`backend/tests`)

## ✅ Quick Validation (5 minutes)

Run: `python quick_test.py`

Expected output:
- [ ] ✅ Test 1: Stock Screener - finds candidates
- [ ] ✅ Test 2: Data Aggregation - fetches real price
- [ ] ✅ Test 3: Multi-Strategy Analysis - generates signals
- [ ] ✅ Test 4: Risk Management - validates trade
- [ ] ✅ Test 5: Data Source Verification - yfinance working
- [ ] ✅ ALL TESTS PASSED

If any test fails, check the error message and troubleshoot before proceeding.

## ✅ Component Tests (15 minutes)

### Screener Tests
Run: `pytest test_screener.py -v`

- [ ] ✅ Screener initializes
- [ ] ✅ Gets NIFTY 200 universe (not hardcoded)
- [ ] ✅ Fetches real stock data from yfinance
- [ ] ✅ Calculates liquidity metrics (turnover, RVOL)
- [ ] ✅ Calculates technical indicators (RSI, EMA, ATR)
- [ ] ✅ Calculates pivot levels
- [ ] ✅ Gets market context (NIFTY, VIX)
- [ ] ✅ Screens single stock correctly
- [ ] ✅ Applies filters correctly
- [ ] ✅ Full screening cycle works

### Multi-Strategy Tests
Run: `pytest test_multi_strategy.py -v`

- [ ] ✅ Analyzer initializes
- [ ] ✅ Analyzes stock with real data
- [ ] ✅ Fundamental strategy generates signal
- [ ] ✅ News-based strategy generates signal
- [ ] ✅ Combined strategy generates signal
- [ ] ✅ Recommendation generated
- [ ] ✅ Multiple stocks analyzed
- [ ] ✅ AI responses are real (not cached)

### Data Aggregator Tests
Run: `pytest test_data_aggregator.py -v`

- [ ] ✅ Aggregator initializes
- [ ] ✅ Gets fundamental data
- [ ] ✅ Gets news context
- [ ] ✅ Aggregates complete stock data
- [ ] ✅ Handles multiple stocks
- [ ] ✅ Market context aggregation works
- [ ] ✅ Caching works correctly

### Risk Manager Tests
Run: `pytest test_risk_manager.py -v`

- [ ] ✅ Risk manager initializes
- [ ] ✅ Validates valid trades
- [ ] ✅ Rejects high-risk trades
- [ ] ✅ Rejects poor risk-reward trades
- [ ] ✅ Position sizing calculated correctly
- [ ] ✅ Max trades limit enforced
- [ ] ✅ Max open risk limit configured

## ✅ End-to-End Tests (10 minutes)

Run: `pytest test_end_to_end.py -v`

- [ ] ✅ Full pipeline: Screening → Analysis → Signal
- [ ] ✅ Pipeline with risk validation
- [ ] ✅ Multiple stocks batch processing
- [ ] ✅ Data sources verified (no mocks)

## ✅ API Tests (5 minutes)

**Prerequisites**: Start server first
```bash
cd backend/src
python main.py
```

Run: `pytest test_api_endpoints.py -v`

- [ ] ✅ Health check endpoint
- [ ] ✅ Stock search endpoint
- [ ] ✅ Stock quote endpoint
- [ ] ✅ Pipeline screening endpoint
- [ ] ✅ Multi-strategy analysis endpoint

## ✅ Full Test Suite (20 minutes)

Run: `./run_all_tests.sh`

- [ ] ✅ All 40+ tests pass
- [ ] ✅ No mock data detected
- [ ] ✅ Coverage report generated
- [ ] ✅ HTML report generated
- [ ] ✅ JSON report generated

## ✅ Data Quality Verification

### Price Data
- [ ] Prices are realistic (₹10 - ₹100,000 range)
- [ ] Prices match yfinance directly
- [ ] OHLCV data is complete
- [ ] No zero or negative prices

### Technical Indicators
- [ ] RSI between 0-100
- [ ] EMA values reasonable
- [ ] ATR% between 0-10%
- [ ] Volume > 0

### Fundamental Data
- [ ] P/E ratio reasonable (0-100)
- [ ] Market cap > 0
- [ ] EPS values present
- [ ] ROE/ROCE in valid ranges

### News Data
- [ ] News articles fetched
- [ ] Sentiment score between -1 and 1
- [ ] Sentiment label (positive/negative/neutral)
- [ ] Recent articles (within 24h)

### AI Responses
- [ ] Strategies generate signals (BUY/SELL/HOLD)
- [ ] Confidence scores 0-100%
- [ ] Entry/SL/Target prices reasonable
- [ ] Reasoning text is meaningful (not generic)
- [ ] Responses differ between runs (not cached)

## ✅ Risk Management Verification

- [ ] Position sizes calculated correctly
- [ ] Risk per trade ≤ 1.5% (default)
- [ ] Stop-loss levels reasonable (0.5-4%)
- [ ] Risk-reward ratio ≥ 1:1
- [ ] Max trades limit enforced
- [ ] Max open risk limit enforced

## ✅ Performance Checks

- [ ] Screening completes in < 60s
- [ ] Single stock analysis < 30s
- [ ] API endpoints respond < 5s
- [ ] Full pipeline < 120s
- [ ] No memory leaks
- [ ] No excessive API calls

## ✅ Error Handling

- [ ] Invalid symbols handled gracefully
- [ ] API failures don't crash system
- [ ] Missing data handled (fallbacks)
- [ ] Rate limiting handled
- [ ] Network errors handled

## ✅ Reports Generated

After running `./run_all_tests.sh`:

- [ ] `reports/test_report.html` exists
- [ ] `reports/test_report.json` exists
- [ ] `reports/coverage_html/index.html` exists
- [ ] Coverage > 80%
- [ ] All critical paths covered

## 🎯 Final Validation

- [ ] All tests pass
- [ ] No mock data used anywhere
- [ ] Real data from all sources verified
- [ ] AI models responding correctly
- [ ] Risk management working
- [ ] API endpoints functional
- [ ] Reports generated successfully

## 📝 Sign-Off

Date: _______________

Tester: _______________

Result: ⬜ PASS  ⬜ FAIL

Notes:
_______________________________________
_______________________________________
_______________________________________

## 🚨 If Tests Fail

1. Check error messages in terminal
2. Review logs in `reports/` directory
3. Verify API keys are set correctly
4. Check internet connection
5. Ensure yfinance is not rate-limited
6. Verify server is running (for API tests)
7. Check Python version (3.9+)
8. Reinstall dependencies if needed

## 📞 Support

For issues:
1. Check `README.md` for troubleshooting
2. Review `TEST_SUMMARY.md` for common issues
3. Check logs for specific error messages
4. Verify configuration in `config.py`

