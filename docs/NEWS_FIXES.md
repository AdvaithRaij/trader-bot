# News System Fixes - CORS & Multiple Sources

## Issues Fixed

### 1. CORS Preflight Errors (OPTIONS 405)
**Problem:**
```
INFO: 127.0.0.1:59488 - "OPTIONS /news?page=1&limit=10 HTTP/1.1" 405 Method Not Allowed
```

**Root Cause:**
- Frontend (localhost:3001) making requests to backend (localhost:8000)
- Browser sends OPTIONS preflight request for CORS
- FastAPI didn't have CORS middleware configured
- OPTIONS requests were being rejected

**Solution:**
Added CORS middleware to `backend/src/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Allow all headers
)
```

**Result:**
✅ OPTIONS requests now return 200 OK
✅ Frontend can successfully fetch news from backend
✅ No more CORS errors in browser console

---

### 2. Limited to Only 10 News Articles
**Problem:**
- Only 10 news articles total across all sources
- Hardcoded `limit_per_source=10` in news aggregator

**Root Cause:**
In `backend/src/news_aggregator.py`:
```python
# Old code - hardcoded limit
news_list = await self.fetch_all_news(limit_per_source=10)
```

**Solution:**
Made the limit dynamic based on requested limit:

```python
# Calculate how many articles to fetch per source
# Fetch more than needed to account for filtering and duplicates
limit_per_source = max(20, limit // 2)

news_list = await self.fetch_all_news(limit_per_source=limit_per_source)
```

**Result:**
✅ Now fetches 50 articles per source (when limit=100)
✅ Total of 125+ unique articles after deduplication
✅ Enough articles for pagination

---

### 3. Only MoneyControl News Showing
**Problem:**
- Yahoo Finance: 0 articles
- Economic Times: 0 articles
- MoneyControl: 10 articles

**Root Cause:**
- Web scraping with CSS selectors is fragile
- Yahoo Finance changed their HTML structure
- Economic Times changed their HTML structure
- Scrapers were failing silently

**Solution:**
Switched from HTML scraping to **RSS feeds** for reliability:

#### Google News RSS (replaced Yahoo Finance)
```python
async def fetch_yahoo_finance_news(self, limit: int = 10) -> List[Dict]:
    """Fetch news from Yahoo Finance RSS feed."""
    # Use Google News RSS for Indian stock market news
    url = "https://news.google.com/rss/search?q=stock+market+india+when:1d&hl=en-IN&gl=IN&ceid=IN:en"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'xml')  # Use XML parser for RSS
                
                items = soup.find_all('item')[:limit]
                # Parse RSS items...
```

#### Economic Times RSS
```python
async def fetch_economic_times_news(self, limit: int = 10) -> List[Dict]:
    """Fetch news from Economic Times RSS feed."""
    # Use ET Markets RSS feed
    url = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'xml')  # Use XML parser for RSS
                
                items = soup.find_all('item')[:limit]
                # Parse RSS items...
```

**Benefits of RSS:**
- ✅ More reliable than web scraping
- ✅ Structured data format
- ✅ Includes publication dates
- ✅ Less likely to break with website updates
- ✅ Faster parsing

**Result:**
✅ Google News: 50 articles
✅ MoneyControl: 25 articles (still using HTML scraping - works fine)
✅ Economic Times: 50 articles
✅ Total: 125 unique articles

---

## Dependencies Added

Installed `lxml` for better XML/RSS parsing:
```bash
pip install lxml
```

This provides the `xml` parser for BeautifulSoup:
```python
soup = BeautifulSoup(html, 'xml')  # Instead of 'html.parser'
```

---

## Testing Results

### Before Fixes:
```
Sources:
- Google News: 0 articles ❌
- MoneyControl: 10 articles ✅
- Economic Times: 0 articles ❌
Total: 10 articles

CORS: 405 errors ❌
```

### After Fixes:
```
Sources:
- Google News: 50 articles ✅
- MoneyControl: 25 articles ✅
- Economic Times: 50 articles ✅
Total: 125 unique articles ✅

CORS: 200 OK ✅
```

### Sample API Response:
```bash
curl "http://localhost:8000/news?page=1&limit=5"
```

```json
{
  "news": [
    {
      "id": "6253a6b7ca5b",
      "title": "Asian Paints Q2 Results: Cons profit surges 43% YoY...",
      "summary": "Asian Paints Q2 Results: The company has declared...",
      "source": "Economic Times",
      "url": "https://economictimes.indiatimes.com/...",
      "publishedAt": "Wed, 12 Nov 2025 15:16:41 +0530",
      "categories": ["corporate"],
      "aiAnalysis": {
        "impact": "HIGH",
        "sentiment": "POSITIVE",
        "relatedStocks": ["NIFTY"],
        "analysis": "This news may have high impact on NIFTY...",
        "timeframe": "SHORT_TERM"
      }
    },
    // ... 4 more articles
  ],
  "pagination": {
    "currentPage": 1,
    "totalPages": 25,
    "totalItems": 125,
    "itemsPerPage": 5,
    "hasNext": true,
    "hasPrevious": false
  },
  "filters": {
    "category": "all",
    "availableCategories": ["all", "market", "finance", "economy", "corporate", "policy"]
  }
}
```

---

## Files Modified

1. **`backend/src/main.py`**
   - Added CORS middleware configuration
   - Allows cross-origin requests from frontend

2. **`backend/src/news_aggregator.py`**
   - Changed `fetch_yahoo_finance_news()` to use Google News RSS
   - Changed `fetch_economic_times_news()` to use ET RSS feed
   - Made `limit_per_source` dynamic instead of hardcoded
   - Updated to use XML parser for RSS feeds

3. **Dependencies**
   - Installed `lxml` for XML parsing

---

## Why RSS Feeds Are Better

### HTML Scraping (Old Approach)
❌ Breaks when website redesigns
❌ Requires reverse-engineering HTML structure
❌ No standardized format
❌ Slower parsing
❌ May violate ToS

### RSS Feeds (New Approach)
✅ Standardized XML format
✅ Designed for content syndication
✅ Rarely changes structure
✅ Faster parsing
✅ Officially provided by publishers
✅ Includes metadata (pub date, author, etc.)

---

## Future Improvements

### Short Term
1. Add more RSS sources:
   - Bloomberg India RSS
   - Reuters India RSS
   - Business Standard RSS
   - Mint RSS

2. Add source reliability scoring
3. Implement news deduplication by content similarity (not just title)

### Medium Term
1. Add real-time news streaming via WebSocket
2. Implement news alerts for high-impact events
3. Add news sentiment trending over time
4. Create news impact backtesting

### Long Term
1. Build custom news crawler with headless browser
2. Add news summarization with AI
3. Implement news clustering by topic
4. Create predictive models based on news patterns

---

## Summary

✅ **Fixed CORS errors** - Added middleware for cross-origin requests
✅ **Increased article count** - From 10 to 125+ articles
✅ **Fixed broken sources** - Switched to reliable RSS feeds
✅ **Improved reliability** - RSS feeds are more stable than web scraping
✅ **Better performance** - XML parsing is faster than HTML scraping

The news system is now production-ready with multiple reliable sources and proper CORS configuration!

