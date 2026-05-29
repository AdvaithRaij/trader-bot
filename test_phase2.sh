#!/bin/bash

# Test script for Phase 1 & 2 integration

echo "🧪 Testing Phase 1 & 2 Integration"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Seed strategies
echo -e "${BLUE}Step 1: Seeding default strategies...${NC}"
cd backend/src
python seed_strategies.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Strategies seeded successfully${NC}"
else
    echo -e "${RED}❌ Failed to seed strategies${NC}"
    exit 1
fi
echo ""

# Step 2: Test strategy endpoints
echo -e "${BLUE}Step 2: Testing strategy endpoints...${NC}"
cd ../..

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 2

# Test GET /strategies
echo -e "${YELLOW}Testing GET /strategies...${NC}"
curl -s http://localhost:8000/strategies | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ Found {data[\"total\"]} strategies')
    for s in data['strategies']:
        print(f'  - {s[\"name\"]} ({s[\"status\"]})')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
echo ""

# Test GET /strategies/{id}
echo -e "${YELLOW}Testing GET /strategies/news_momentum_v1...${NC}"
curl -s http://localhost:8000/strategies/news_momentum_v1 | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    s = data['strategy']
    print(f'✅ Strategy: {s[\"name\"]}')
    print(f'  Status: {s[\"status\"]}')
    print(f'  Total Trades: {s[\"performance\"][\"totalTrades\"]}')
    print(f'  Win Rate: {s[\"performance\"][\"winRate\"]}%')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
echo ""

# Test POST /strategies/{id}/run
echo -e "${YELLOW}Testing POST /strategies/news_momentum_v1/run...${NC}"
curl -s -X POST http://localhost:8000/strategies/news_momentum_v1/run | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ {data[\"message\"]}')
    if data['signals']:
        for signal in data['signals']:
            print(f'  - {signal[\"symbol\"]} {signal[\"direction\"]} @ ₹{signal[\"entryPrice\"]} (Confidence: {signal[\"confidence\"]}%)')
            print(f'    SL: ₹{signal[\"stopLoss\"]} | T1: ₹{signal[\"target1\"]}')
    else:
        print('  ℹ️  No signals generated (this is normal if no high-impact news)')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
echo ""

# Test POST /signals/generate
echo -e "${YELLOW}Testing POST /signals/generate for RELIANCE...${NC}"
curl -s -X POST http://localhost:8000/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE"}' | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f'ℹ️  {data[\"error\"]}')
    else:
        signal = data['signal']
        print(f'✅ Signal generated for {signal[\"symbol\"]}')
        print(f'  Direction: {signal[\"direction\"]}')
        print(f'  Entry: ₹{signal[\"entryPrice\"]}')
        print(f'  Stop Loss: ₹{signal[\"stopLoss\"]}')
        print(f'  Target 1: ₹{signal[\"target1\"]}')
        print(f'  Confidence: {signal[\"confidence\"]}%')
        print(f'  Reasoning: {signal[\"reasoning\"][:100]}...')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"
echo ""

# Step 3: Test portfolio endpoints
echo -e "${BLUE}Step 3: Testing portfolio endpoints...${NC}"

echo -e "${YELLOW}Testing GET /api/portfolio...${NC}"
curl -s http://localhost:8000/api/portfolio | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f'ℹ️  Portfolio not initialized yet (this is normal)')
        print(f'  Error: {data[\"error\"]}')
    else:
        print(f'✅ Portfolio loaded')
        print(f'  Total Capital: ₹{data[\"totalCapital\"]}')
        print(f'  Available Cash: ₹{data[\"availableCash\"]}')
        print(f'  Open Positions: {data[\"openPositions\"]}/{data[\"maxPositions\"]}')
except Exception as e:
    print(f'❌ Error: {e}')
"
echo ""

echo -e "${GREEN}=================================="
echo -e "✅ Phase 2 Testing Complete!"
echo -e "==================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Start the backend: cd backend/src && python main.py --mode web"
echo "2. Start the frontend: cd frontend && npm run dev"
echo "3. Open http://localhost:3001 in your browser"
echo "4. Navigate to 'Strategy Manager' to run strategies"
echo "5. Navigate to 'Trading Dashboard' to see portfolio"
echo ""

