#!/bin/bash

# Master Test Runner for AI Trading Bot
# Runs all tests and generates comprehensive reports

set -e  # Exit on error

echo "=========================================="
echo "AI Trading Bot - Comprehensive Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "run_all_tests.sh" ]; then
    echo -e "${RED}Error: Please run this script from the backend/tests directory${NC}"
    exit 1
fi

# Install test dependencies
echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
pip install -q -r requirements-test.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Create reports directory
mkdir -p reports

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../src"

echo -e "${YELLOW}🧪 Running Test Suite...${NC}"
echo ""

# Run tests with different configurations

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  CRITICAL PATH: End-to-End Pipeline"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pytest test_end_to_end.py -v --tb=short --color=yes || true
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  COMPONENT: Stock Screener"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pytest test_screener.py -v --tb=short --color=yes || true
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  COMPONENT: Multi-Strategy Analyzer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pytest test_multi_strategy.py -v --tb=short --color=yes || true
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  COMPONENT: Risk Manager"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pytest test_risk_manager.py -v --tb=short --color=yes || true
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  API ENDPOINTS (requires server running)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Note: Make sure the server is running on localhost:8001${NC}"
pytest test_api_endpoints.py -v --tb=short --color=yes || echo -e "${YELLOW}⚠️  API tests skipped (server not running)${NC}"
echo ""

# Run all tests with coverage
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 FULL TEST SUITE WITH COVERAGE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pytest . -v \
    --cov=../src \
    --cov-report=html:reports/coverage_html \
    --cov-report=term-missing \
    --html=reports/test_report.html \
    --self-contained-html \
    --json-report \
    --json-report-file=reports/test_report.json \
    --tb=short \
    --color=yes

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Test Suite Complete!${NC}"
echo "=========================================="
echo ""
echo "📊 Reports generated:"
echo "  - HTML Report: reports/test_report.html"
echo "  - JSON Report: reports/test_report.json"
echo "  - Coverage Report: reports/coverage_html/index.html"
echo ""
echo "To view coverage report:"
echo "  open reports/coverage_html/index.html"
echo ""

