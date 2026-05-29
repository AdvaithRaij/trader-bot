"""
Test script for news API endpoints.
"""

import asyncio
import aiohttp
import json

API_BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

async def test_news_endpoint():
    """Test the news endpoint with pagination and filtering."""
    print(f"\n{Colors.BLUE}{'='*70}")
    print("🧪 Testing News API Endpoints")
    print(f"{'='*70}{Colors.RESET}\n")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Get first page of all news
        print(f"{Colors.YELLOW}📰 Test 1: Get first page of news (limit=10){Colors.RESET}")
        async with session.get(f"{API_BASE_URL}/news?page=1&limit=10&refresh=true") as response:
            if response.status == 200:
                data = await response.json()
                print(f"{Colors.GREEN}✅ Success!{Colors.RESET}")
                print(f"   Total Items: {data['pagination']['totalItems']}")
                print(f"   Total Pages: {data['pagination']['totalPages']}")
                print(f"   Current Page: {data['pagination']['currentPage']}")
                print(f"   News Count: {len(data['news'])}")
                
                # Show first 3 news items
                print(f"\n{Colors.CYAN}   📋 Sample News:{Colors.RESET}")
                for i, news in enumerate(data['news'][:3], 1):
                    print(f"\n   {i}. {news['title'][:80]}...")
                    print(f"      Source: {news['source']}")
                    print(f"      Categories: {', '.join(news.get('categories', []))}")
                    if 'aiAnalysis' in news:
                        ai = news['aiAnalysis']
                        print(f"      Impact: {ai.get('impact')} | Sentiment: {ai.get('sentiment')}")
                        print(f"      Related Stocks: {', '.join(ai.get('relatedStocks', []))}")
                        print(f"      Analysis: {ai.get('analysis', '')[:100]}...")
            else:
                print(f"{Colors.RED}❌ Failed with status {response.status}{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'-'*70}{Colors.RESET}\n")
        
        # Test 2: Filter by category
        print(f"{Colors.YELLOW}📰 Test 2: Filter by 'market' category{Colors.RESET}")
        async with session.get(f"{API_BASE_URL}/news?page=1&limit=5&category=market") as response:
            if response.status == 200:
                data = await response.json()
                print(f"{Colors.GREEN}✅ Success!{Colors.RESET}")
                print(f"   Filtered Items: {data['pagination']['totalItems']}")
                print(f"   Category: {data['filters']['category']}")
                print(f"   News Count: {len(data['news'])}")
            else:
                print(f"{Colors.RED}❌ Failed with status {response.status}{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'-'*70}{Colors.RESET}\n")
        
        # Test 3: Get specific news analysis
        print(f"{Colors.YELLOW}📰 Test 3: Get detailed analysis for first news item{Colors.RESET}")
        # First get a news ID
        async with session.get(f"{API_BASE_URL}/news?page=1&limit=1") as response:
            if response.status == 200:
                data = await response.json()
                if data['news']:
                    news_id = data['news'][0]['id']
                    
                    # Get detailed analysis
                    async with session.get(f"{API_BASE_URL}/news/{news_id}/analysis") as analysis_response:
                        if analysis_response.status == 200:
                            analysis_data = await analysis_response.json()
                            print(f"{Colors.GREEN}✅ Success!{Colors.RESET}")
                            print(f"\n   Title: {analysis_data['title']}")
                            print(f"   Source: {analysis_data['source']}")
                            print(f"   URL: {analysis_data['url']}")
                            print(f"\n   {Colors.CYAN}AI Analysis:{Colors.RESET}")
                            ai = analysis_data.get('aiAnalysis', {})
                            print(f"   Impact: {ai.get('impact')}")
                            print(f"   Sentiment: {ai.get('sentiment')}")
                            print(f"   Timeframe: {ai.get('timeframe')}")
                            print(f"   Related Stocks: {', '.join(ai.get('relatedStocks', []))}")
                            print(f"   Analysis: {ai.get('analysis', '')}")
                        else:
                            print(f"{Colors.RED}❌ Failed with status {analysis_response.status}{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'-'*70}{Colors.RESET}\n")
        
        # Test 4: Test pagination
        print(f"{Colors.YELLOW}📰 Test 4: Test pagination (page 2){Colors.RESET}")
        async with session.get(f"{API_BASE_URL}/news?page=2&limit=5") as response:
            if response.status == 200:
                data = await response.json()
                print(f"{Colors.GREEN}✅ Success!{Colors.RESET}")
                print(f"   Current Page: {data['pagination']['currentPage']}")
                print(f"   Has Next: {data['pagination']['hasNext']}")
                print(f"   Has Previous: {data['pagination']['hasPrevious']}")
                print(f"   News Count: {len(data['news'])}")
            else:
                print(f"{Colors.RED}❌ Failed with status {response.status}{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'-'*70}{Colors.RESET}\n")
        
        # Test 5: Test all categories
        print(f"{Colors.YELLOW}📰 Test 5: Test different categories{Colors.RESET}")
        categories = ['market', 'finance', 'economy', 'corporate', 'policy']
        for category in categories:
            async with session.get(f"{API_BASE_URL}/news?page=1&limit=3&category={category}") as response:
                if response.status == 200:
                    data = await response.json()
                    count = data['pagination']['totalItems']
                    print(f"   {category.capitalize()}: {count} articles")
                else:
                    print(f"   {category.capitalize()}: {Colors.RED}Failed{Colors.RESET}")
        
        print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        print(f"{Colors.GREEN}🎉 All news API tests completed!{Colors.RESET}\n")

if __name__ == "__main__":
    print(f"\n{Colors.BLUE}Starting News API Tests...{Colors.RESET}")
    print(f"{Colors.YELLOW}Make sure the backend server is running on {API_BASE_URL}{Colors.RESET}\n")
    
    try:
        asyncio.run(test_news_endpoint())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Error running tests: {e}{Colors.RESET}\n")

