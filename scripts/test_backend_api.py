"""
Test script for all backend API endpoints.
Tests each endpoint to ensure they work correctly.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

async def test_endpoint(session, method, endpoint, data=None, params=None):
    """Test a single endpoint."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            async with session.get(url, params=params) as response:
                result = await response.json()
                status = response.status
        elif method == "POST":
            async with session.post(url, json=data) as response:
                result = await response.json()
                status = response.status
        elif method == "PUT":
            async with session.put(url, json=data) as response:
                result = await response.json()
                status = response.status
        
        if status == 200:
            print(f"{Colors.GREEN}✅ {method} {endpoint}{Colors.RESET}")
            return True, result
        else:
            print(f"{Colors.RED}❌ {method} {endpoint} - Status: {status}{Colors.RESET}")
            return False, result
            
    except Exception as e:
        print(f"{Colors.RED}❌ {method} {endpoint} - Error: {e}{Colors.RESET}")
        return False, None

async def main():
    """Test all backend endpoints."""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🧪 Testing Backend API Endpoints")
    print(f"{'='*60}{Colors.RESET}\n")
    
    async with aiohttp.ClientSession() as session:
        results = {}
        
        # Test basic endpoints
        print(f"{Colors.YELLOW}📍 Basic Endpoints{Colors.RESET}")
        results['root'] = await test_endpoint(session, "GET", "/")
        results['status'] = await test_endpoint(session, "GET", "/status")
        results['health'] = await test_endpoint(session, "GET", "/health")
        print()
        
        # Test screener endpoints
        print(f"{Colors.YELLOW}📍 Screener Endpoints{Colors.RESET}")
        results['screener_stocks'] = await test_endpoint(session, "GET", "/screener/stocks")
        results['screener_watchlist'] = await test_endpoint(session, "GET", "/screener/watchlist")
        print()
        
        # Test portfolio endpoints
        print(f"{Colors.YELLOW}📍 Portfolio Endpoints{Colors.RESET}")
        results['portfolio'] = await test_endpoint(session, "GET", "/portfolio")
        results['positions'] = await test_endpoint(session, "GET", "/portfolio/positions")
        print()
        
        # Test trade endpoints
        print(f"{Colors.YELLOW}📍 Trade Endpoints{Colors.RESET}")
        results['trades'] = await test_endpoint(session, "GET", "/trades", params={"limit": 10})
        results['trades_history'] = await test_endpoint(session, "GET", "/trades/history", params={"days": 7})
        results['trades_today'] = await test_endpoint(session, "GET", "/trades/today")
        print()
        
        # Test sentiment endpoints
        print(f"{Colors.YELLOW}📍 Sentiment Endpoints{Colors.RESET}")
        results['sentiment_news'] = await test_endpoint(session, "GET", "/sentiment/news", params={"limit": 5})
        results['sentiment_analysis'] = await test_endpoint(session, "GET", "/sentiment/analysis", params={"symbol": "RELIANCE"})
        print()
        
        # Test risk endpoints
        print(f"{Colors.YELLOW}📍 Risk Management Endpoints{Colors.RESET}")
        results['risk_metrics'] = await test_endpoint(session, "GET", "/risk/metrics")
        print()
        
        # Test AI endpoints
        print(f"{Colors.YELLOW}📍 AI Endpoints{Colors.RESET}")
        results['ai_insights'] = await test_endpoint(session, "GET", "/ai/insights")
        print()
        
        # Test decision endpoints
        print(f"{Colors.YELLOW}📍 Decision Endpoints{Colors.RESET}")
        results['decisions_today'] = await test_endpoint(session, "GET", "/decisions/today")
        results['report_today'] = await test_endpoint(session, "GET", "/report/today")
        print()
        
        # Summary
        print(f"\n{Colors.BLUE}{'='*60}")
        print("📊 Test Summary")
        print(f"{'='*60}{Colors.RESET}\n")
        
        total = len(results)
        passed = sum(1 for success, _ in results.values() if success)
        failed = total - passed
        
        print(f"Total Endpoints: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"Success Rate: {passed/total*100:.1f}%\n")
        
        # Show sample data from key endpoints
        if results['health'][0]:
            print(f"{Colors.YELLOW}🏥 Health Status:{Colors.RESET}")
            health_data = results['health'][1]
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Components: {json.dumps(health_data.get('components', {}), indent=6)}")
            print()
        
        if results['portfolio'][0]:
            print(f"{Colors.YELLOW}💼 Portfolio:{Colors.RESET}")
            portfolio_data = results['portfolio'][1]
            print(f"   Total Value: ₹{portfolio_data.get('totalValue', 0):,.2f}")
            print(f"   Day P&L: ₹{portfolio_data.get('dayPnl', 0):,.2f}")
            print(f"   Positions: {len(portfolio_data.get('positions', []))}")
            print()
        
        if results['screener_stocks'][0]:
            print(f"{Colors.YELLOW}📈 Screened Stocks:{Colors.RESET}")
            stocks_data = results['screener_stocks'][1]
            print(f"   Count: {stocks_data.get('count', 0)}")
            if stocks_data.get('stocks'):
                for stock in stocks_data['stocks'][:3]:
                    print(f"   - {stock.get('symbol')}: ₹{stock.get('price', 0):.2f}")
            print()
        
        if results['risk_metrics'][0]:
            print(f"{Colors.YELLOW}⚠️  Risk Metrics:{Colors.RESET}")
            risk_data = results['risk_metrics'][1]
            print(f"   Win Rate: {risk_data.get('winRate', 0):.1f}%")
            print(f"   Total Trades: {risk_data.get('totalTrades', 0)}")
            print(f"   Sharpe Ratio: {risk_data.get('sharpeRatio', 0):.2f}")
            print()
        
        print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        if failed == 0:
            print(f"{Colors.GREEN}🎉 All endpoints are working correctly!{Colors.RESET}\n")
        else:
            print(f"{Colors.YELLOW}⚠️  Some endpoints need attention.{Colors.RESET}\n")

if __name__ == "__main__":
    print(f"\n{Colors.BLUE}Starting Backend API Tests...{Colors.RESET}")
    print(f"{Colors.YELLOW}Make sure the backend server is running on {API_BASE_URL}{Colors.RESET}\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Error running tests: {e}{Colors.RESET}\n")

