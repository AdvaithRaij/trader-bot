"""
News Aggregator Module for Trading Bot.
Aggregates market-moving news from multiple sources and provides AI-powered impact analysis.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from loguru import logger
import json
import hashlib
import re

from config import get_config

config = get_config()


class NewsAggregator:
    """
    Aggregates market news from multiple sources with AI-powered analysis.
    Sources: Yahoo Finance, MoneyControl, Economic Times
    """
    
    def __init__(self):
        self.config = config
        self.news_cache = []
        self.cache_timestamp = None
        self.cache_duration = timedelta(minutes=15)  # Cache for 15 minutes

        # AI analysis cache
        self.analysis_cache = {}  # Cache AI analysis by news ID

        # Rate limiting
        self.last_api_call = None
        self.min_api_delay = 2  # Minimum 2 seconds between API calls

        # News categories
        self.categories = {
            'market': ['market', 'stock', 'equity', 'trading', 'nifty', 'sensex'],
            'finance': ['finance', 'banking', 'financial', 'rbi', 'monetary'],
            'economy': ['economy', 'gdp', 'inflation', 'economic', 'fiscal'],
            'corporate': ['corporate', 'earnings', 'results', 'merger', 'acquisition'],
            'policy': ['policy', 'regulation', 'government', 'budget', 'tax']
        }
    
    def generate_news_id(self, title: str, source: str) -> str:
        """Generate unique ID for news article."""
        unique_string = f"{title}_{source}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def categorize_news(self, title: str, summary: str) -> List[str]:
        """Categorize news based on keywords."""
        text = f"{title} {summary}".lower()
        categories = []
        
        for category, keywords in self.categories.items():
            if any(keyword in text for keyword in keywords):
                categories.append(category)
        
        return categories if categories else ['general']
    
    async def fetch_yahoo_finance_news(self, limit: int = 10) -> List[Dict]:
        """Fetch news from Yahoo Finance RSS feed."""
        news_items = []

        try:
            # Use Google News RSS for Yahoo Finance news
            url = "https://news.google.com/rss/search?q=stock+market+india+when:1d&hl=en-IN&gl=IN&ceid=IN:en"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'xml')

                        # Find news items in RSS feed
                        items = soup.find_all('item')[:limit]

                        for item in items:
                            try:
                                title_tag = item.find('title')
                                link_tag = item.find('link')
                                desc_tag = item.find('description')
                                pub_date_tag = item.find('pubDate')

                                if title_tag and link_tag:
                                    title = title_tag.get_text(strip=True)
                                    url = link_tag.get_text(strip=True)
                                    summary = desc_tag.get_text(strip=True) if desc_tag else title[:200]

                                    # Clean HTML from summary
                                    summary_soup = BeautifulSoup(summary, 'html.parser')
                                    summary = summary_soup.get_text(strip=True)[:300]

                                    pub_date = pub_date_tag.get_text(strip=True) if pub_date_tag else datetime.now().isoformat()

                                    news_items.append({
                                        'id': self.generate_news_id(title, 'google_news'),
                                        'title': title,
                                        'summary': summary,
                                        'source': 'Google News',
                                        'url': url,
                                        'publishedAt': pub_date,
                                        'categories': self.categorize_news(title, summary)
                                    })
                            except Exception as e:
                                logger.debug(f"Error parsing Google News item: {e}")
                                continue

                        logger.info(f"✅ Fetched {len(news_items)} articles from Google News")

        except Exception as e:
            logger.error(f"Error fetching Google News: {e}")

        return news_items
    
    async def fetch_moneycontrol_news(self, limit: int = 10) -> List[Dict]:
        """Fetch news from MoneyControl."""
        news_items = []
        
        try:
            url = "https://www.moneycontrol.com/news/business/markets/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find news articles
                        articles = soup.find_all('li', class_='clearfix')[:limit]
                        
                        for article in articles:
                            try:
                                link_tag = article.find('a')
                                if link_tag:
                                    title = link_tag.get('title', link_tag.get_text(strip=True))
                                    url = link_tag.get('href', '')
                                    
                                    # Get summary
                                    summary_tag = article.find('p')
                                    summary = summary_tag.get_text(strip=True) if summary_tag else title[:200]
                                    
                                    news_items.append({
                                        'id': self.generate_news_id(title, 'moneycontrol'),
                                        'title': title,
                                        'summary': summary,
                                        'source': 'MoneyControl',
                                        'url': url,
                                        'publishedAt': datetime.now().isoformat(),
                                        'categories': self.categorize_news(title, summary)
                                    })
                            except Exception as e:
                                logger.debug(f"Error parsing MoneyControl article: {e}")
                                continue
                        
                        logger.info(f"✅ Fetched {len(news_items)} articles from MoneyControl")
                    
        except Exception as e:
            logger.error(f"Error fetching MoneyControl news: {e}")
        
        return news_items
    
    async def fetch_economic_times_news(self, limit: int = 10) -> List[Dict]:
        """Fetch news from Economic Times RSS feed."""
        news_items = []

        try:
            # Use ET Markets RSS feed
            url = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'xml')

                        # Find news items in RSS feed
                        items = soup.find_all('item')[:limit]

                        for item in items:
                            try:
                                title_tag = item.find('title')
                                link_tag = item.find('link')
                                desc_tag = item.find('description')
                                pub_date_tag = item.find('pubDate')

                                if title_tag and link_tag:
                                    title = title_tag.get_text(strip=True)
                                    url = link_tag.get_text(strip=True)
                                    summary = desc_tag.get_text(strip=True) if desc_tag else title[:200]

                                    # Clean HTML from summary
                                    summary_soup = BeautifulSoup(summary, 'html.parser')
                                    summary = summary_soup.get_text(strip=True)[:300]

                                    pub_date = pub_date_tag.get_text(strip=True) if pub_date_tag else datetime.now().isoformat()

                                    news_items.append({
                                        'id': self.generate_news_id(title, 'et'),
                                        'title': title,
                                        'summary': summary,
                                        'source': 'Economic Times',
                                        'url': url,
                                        'publishedAt': pub_date,
                                        'categories': self.categorize_news(title, summary)
                                    })
                            except Exception as e:
                                logger.debug(f"Error parsing ET RSS item: {e}")
                                continue

                        logger.info(f"✅ Fetched {len(news_items)} articles from Economic Times")

        except Exception as e:
            logger.error(f"Error fetching Economic Times news: {e}")
        
        return news_items
    
    async def fetch_all_news(self, limit_per_source: int = 10) -> List[Dict]:
        """Fetch news from all sources concurrently."""
        try:
            # Fetch from all sources concurrently
            results = await asyncio.gather(
                self.fetch_yahoo_finance_news(limit_per_source),
                self.fetch_moneycontrol_news(limit_per_source),
                self.fetch_economic_times_news(limit_per_source),
                return_exceptions=True
            )
            
            # Combine all news
            all_news = []
            for result in results:
                if isinstance(result, list):
                    all_news.extend(result)
            
            # Remove duplicates based on similar titles
            unique_news = self.remove_duplicates(all_news)
            
            # Sort by published date (most recent first)
            unique_news.sort(key=lambda x: x['publishedAt'], reverse=True)
            
            logger.info(f"✅ Total unique news articles: {len(unique_news)}")
            
            return unique_news
            
        except Exception as e:
            logger.error(f"Error fetching all news: {e}")
            return []
    
    def remove_duplicates(self, news_list: List[Dict]) -> List[Dict]:
        """Remove duplicate news based on title similarity."""
        unique_news = []
        seen_titles = set()
        
        for news in news_list:
            # Normalize title for comparison
            normalized_title = re.sub(r'[^\w\s]', '', news['title'].lower())
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_news.append(news)
        
        return unique_news

    async def analyze_news_impact(self, news_item: Dict) -> Dict:
        """
        Analyze single news item (uses cache or mock for efficiency).
        For bulk analysis, use analyze_news_batch instead.
        """
        news_id = news_item.get('id')
        if news_id and news_id in self.analysis_cache:
            return self.analysis_cache[news_id]
        return self.mock_analysis(news_item)

    async def analyze_news_batch(self, news_items: List[Dict]) -> List[Dict]:
        """
        Batch analyze multiple news items in a SINGLE API call using Groq.
        This is much more efficient than calling API for each news item.

        Args:
            news_items: List of news articles to analyze

        Returns:
            List of news items with AI analysis added
        """
        if not news_items:
            return []

        # Filter out already analyzed items
        items_to_analyze = []
        already_analyzed = []

        for news in news_items:
            news_id = news.get('id')
            if news_id and news_id in self.analysis_cache:
                news['aiAnalysis'] = self.analysis_cache[news_id]
                already_analyzed.append(news)
            else:
                items_to_analyze.append(news)

        if not items_to_analyze:
            logger.info(f"📦 All {len(already_analyzed)} news items already cached")
            return news_items

        # Check if AI is enabled
        if config.MOCK_AI:
            logger.info("Using mock analysis (AI disabled)")
            for news in items_to_analyze:
                analysis = self.mock_analysis(news)
                news['aiAnalysis'] = analysis
                if news.get('id'):
                    self.analysis_cache[news['id']] = analysis
            return news_items

        # Use Groq for batch analysis (preferred)
        if config.GROQ_API_KEY and config.AI_PROVIDER.lower() == 'groq':
            try:
                analyzed = await self._batch_analyze_with_groq(items_to_analyze)
                return already_analyzed + analyzed
            except Exception as e:
                logger.error(f"Groq batch analysis failed: {e}")

        # Fallback to mock analysis
        logger.warning("⚠️ Using mock analysis (no AI provider available)")
        for news in items_to_analyze:
            analysis = self.mock_analysis(news)
            news['aiAnalysis'] = analysis
            if news.get('id'):
                self.analysis_cache[news['id']] = analysis

        return news_items

    async def _batch_analyze_with_groq(self, news_items: List[Dict]) -> List[Dict]:
        """Use Groq to analyze multiple news items in ONE API call."""
        from groq import Groq

        client = Groq(api_key=config.GROQ_API_KEY)

        # Prepare batch prompt with all news items
        news_summaries = []
        for i, news in enumerate(news_items[:10]):  # Max 10 items per batch
            news_summaries.append(f"""
NEWS {i+1}:
Title: {news['title']}
Summary: {news['summary'][:200]}
Source: {news['source']}
""")

        batch_prompt = f"""Analyze these Indian stock market news articles and provide impact assessment.
For EACH news item, determine:
1. impact: HIGH, MEDIUM, or LOW
2. sentiment: POSITIVE, NEGATIVE, or NEUTRAL
3. relatedStocks: List of affected NSE stock symbols (e.g., RELIANCE, TCS, NIFTY)
4. analysis: Brief 1-line analysis
5. timeframe: SHORT_TERM, MEDIUM_TERM, or LONG_TERM

{"".join(news_summaries)}

Respond with a JSON array containing analysis for each news item in order:
[
  {{"impact": "...", "sentiment": "...", "relatedStocks": [...], "analysis": "...", "timeframe": "..."}},
  ...
]
IMPORTANT: Return ONLY valid JSON array, no markdown, no explanation."""

        logger.info(f"🤖 Batch analyzing {len(news_items[:10])} news items with Groq...")

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert Indian stock market analyst. Always respond with valid JSON only."},
                {"role": "user", "content": batch_prompt}
            ],
            temperature=0.3,
            max_tokens=2048
        )

        response_text = response.choices[0].message.content.strip()

        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        analyses = json.loads(response_text)

        logger.info(f"✅ Batch analysis complete for {len(analyses)} news items (1 API call)")

        # Apply analysis to news items and cache
        for i, news in enumerate(news_items[:10]):
            if i < len(analyses):
                analysis = {
                    'impact': analyses[i].get('impact', 'MEDIUM'),
                    'sentiment': analyses[i].get('sentiment', 'NEUTRAL'),
                    'relatedStocks': analyses[i].get('relatedStocks', ['NIFTY']),
                    'analysis': analyses[i].get('analysis', 'Analysis not available'),
                    'timeframe': analyses[i].get('timeframe', 'SHORT_TERM'),
                    'relevance': 70
                }
            else:
                analysis = self.mock_analysis(news)

            news['aiAnalysis'] = analysis
            if news.get('id'):
                self.analysis_cache[news['id']] = analysis

        # For items beyond batch limit, use mock
        for news in news_items[10:]:
            analysis = self.mock_analysis(news)
            news['aiAnalysis'] = analysis
            if news.get('id'):
                self.analysis_cache[news['id']] = analysis

        return news_items

    def mock_analysis(self, news_item: Dict) -> Dict:
        """Provide mock analysis when AI is not available."""
        # Simple keyword-based analysis
        text = f"{news_item['title']} {news_item['summary']}".lower()

        # Determine impact
        high_impact_keywords = ['crash', 'surge', 'record', 'historic', 'major', 'significant']
        impact = 'HIGH' if any(kw in text for kw in high_impact_keywords) else 'MEDIUM'

        # Determine sentiment
        positive_keywords = ['gain', 'rise', 'up', 'growth', 'profit', 'positive', 'rally']
        negative_keywords = ['fall', 'drop', 'loss', 'decline', 'negative', 'crash', 'down']

        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)

        if positive_count > negative_count:
            sentiment = 'POSITIVE'
        elif negative_count > positive_count:
            sentiment = 'NEGATIVE'
        else:
            sentiment = 'NEUTRAL'

        # Identify related stocks
        related_stocks = []
        stock_keywords = {
            'NIFTY': ['nifty', 'index', 'market'],
            'BANKNIFTY': ['bank', 'banking', 'banknifty'],
            'RELIANCE': ['reliance', 'ril'],
            'TCS': ['tcs', 'tata consultancy'],
            'INFY': ['infosys', 'infy'],
            'HDFC': ['hdfc'],
            'ICICI': ['icici']
        }

        for stock, keywords in stock_keywords.items():
            if any(kw in text for kw in keywords):
                related_stocks.append(stock)

        if not related_stocks:
            related_stocks = ['NIFTY']

        # Calculate basic relevance score
        relevance = 60  # Default
        if impact == 'HIGH':
            relevance += 20
        if sentiment != 'NEUTRAL':
            relevance += 10
        if len(related_stocks) > 1:
            relevance += 10

        return {
            'impact': impact,
            'sentiment': sentiment,
            'relatedStocks': related_stocks,
            'analysis': f"This news may have {impact.lower()} impact on {', '.join(related_stocks[:3])} with {sentiment.lower()} sentiment.",
            'timeframe': 'SHORT_TERM',
            'relevance': min(relevance, 100)  # Cap at 100
        }

    async def get_news_with_analysis(self,
                                     limit: int = 10,
                                     category: Optional[str] = None,
                                     source: Optional[str] = None,
                                     refresh: bool = False) -> List[Dict]:
        """
        Get news with AI analysis, using cache when possible.

        Args:
            limit: Number of news items to return (for AI analysis optimization)
            category: Filter by category (market, finance, economy, etc.)
            source: Filter by source (Economic Times, Google News, MoneyControl)
            refresh: Force refresh cache

        Returns:
            List of news items with AI analysis
        """
        try:
            # Always fetch ALL articles from all sources (50 per source)
            # This ensures category and source filtering works across all sources
            limit_per_source = 50

            # Check cache - cache contains ALL articles from all sources
            if not refresh and self.news_cache and self.cache_timestamp:
                if datetime.now() - self.cache_timestamp < self.cache_duration:
                    logger.info("📦 Using cached news data")
                    all_news = self.news_cache
                else:
                    logger.info("🔄 Cache expired, fetching fresh news")
                    all_news = await self.fetch_all_news(limit_per_source=limit_per_source)
                    self.news_cache = all_news
                    self.cache_timestamp = datetime.now()
            else:
                logger.info("🔄 Fetching fresh news")
                all_news = await self.fetch_all_news(limit_per_source=limit_per_source)
                self.news_cache = all_news
                self.cache_timestamp = datetime.now()

            # Apply filters (AFTER fetching all)
            filtered_news = all_news

            # Filter by category if specified
            if category and category != 'all':
                filtered_news = [n for n in filtered_news if category in n.get('categories', [])]
                logger.info(f"📊 Filtered {len(filtered_news)} articles for category '{category}' from {len(all_news)} total")

            # Filter by source if specified
            if source and source != 'all':
                filtered_news = [n for n in filtered_news if n.get('source') == source]
                logger.info(f"📊 Filtered {len(filtered_news)} articles for source '{source}'")

            # Batch analyze news items (MUCH more efficient - 1 API call for up to 10 items)
            # Only analyze the items we'll actually display to save API quota
            items_to_display = filtered_news[:limit] if limit else filtered_news[:10]

            # Use batch analysis - single API call for all items
            await self.analyze_news_batch(items_to_display)

            # Return ALL filtered news (pagination happens in endpoint)
            return filtered_news

        except Exception as e:
            logger.error(f"Error getting news with analysis: {e}")
            return []


# Singleton instance
news_aggregator = NewsAggregator()

