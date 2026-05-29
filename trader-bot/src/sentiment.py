"""
Sentiment Analysis Module for Trading Bot.
Scrapes news headlines, analyzes sentiment, and scores stocks for intraday relevance.
"""

import asyncio
import aiohttp
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
from textblob import TextBlob
import json
from loguru import logger

from config import get_config

config = get_config()


class SentimentAnalyzer:
    """
    Analyzes sentiment from news sources and social media for trading decisions.
    """
    
    def __init__(self):
        self.config = config
        self.session = None
        
        # News sources
        self.news_sources = {
            'moneycontrol': 'https://www.moneycontrol.com/news/business/stocks/',
            'economic_times': 'https://economictimes.indiatimes.com/markets/stocks/news',
            'business_standard': 'https://www.business-standard.com/markets/capital-market-news'
        }
        
        # Keywords for intraday relevance
        self.intraday_keywords = [
            'breakout', 'surge', 'rally', 'jump', 'soar', 'gain', 'rise',
            'fall', 'drop', 'crash', 'decline', 'sell-off', 'correction',
            'volume', 'trading', 'buy', 'sell', 'target', 'resistance',
            'support', 'technical', 'momentum', 'trend', 'pattern'
        ]
        
        # Positive sentiment words
        self.positive_words = [
            'bullish', 'positive', 'strong', 'growth', 'profit', 'revenue',
            'beat', 'exceed', 'outperform', 'upgrade', 'recommendation',
            'buy', 'accumulate', 'momentum', 'breakout', 'rally'
        ]
        
        # Negative sentiment words
        self.negative_words = [
            'bearish', 'negative', 'weak', 'loss', 'decline', 'miss',
            'underperform', 'downgrade', 'sell', 'concern', 'risk',
            'fall', 'drop', 'correction', 'pressure'
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis."""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\']', '', text)
        
        return text.lower()
    
    def calculate_sentiment_score(self, text: str) -> Dict:
        """
        Calculate sentiment score using TextBlob and custom keywords.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment metrics
        """
        try:
            cleaned_text = self.clean_text(text)
            
            # TextBlob sentiment
            blob = TextBlob(cleaned_text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Custom keyword scoring
            positive_count = sum(1 for word in self.positive_words if word in cleaned_text)
            negative_count = sum(1 for word in self.negative_words if word in cleaned_text)
            
            # Intraday relevance scoring
            intraday_score = sum(1 for keyword in self.intraday_keywords if keyword in cleaned_text)
            intraday_relevance = min(intraday_score / 5.0, 1.0)  # Normalize to 0-1
            
            # Combined sentiment score
            keyword_sentiment = (positive_count - negative_count) / max(positive_count + negative_count, 1)
            combined_sentiment = (polarity + keyword_sentiment) / 2
            
            return {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'combined_sentiment': combined_sentiment,
                'positive_keywords': positive_count,
                'negative_keywords': negative_count,
                'intraday_relevance': intraday_relevance,
                'confidence': 1 - subjectivity  # Higher confidence for objective text
            }
            
        except Exception as e:
            logger.error(f"Error calculating sentiment: {e}")
            return {
                'polarity': 0, 'subjectivity': 0.5, 'combined_sentiment': 0,
                'positive_keywords': 0, 'negative_keywords': 0,
                'intraday_relevance': 0, 'confidence': 0
            }
    
    async def scrape_google_news(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Scrape Google News for stock-related headlines.
        
        Args:
            query: Search query (stock symbol or name)
            max_results: Maximum number of results
            
        Returns:
            List of news articles with metadata
        """
        try:
            # Mock implementation for now
            # In production, use proper Google News API or scraping
            mock_headlines = [
                f"{query} shares surge 5% on strong quarterly results",
                f"Technical breakout seen in {query} stock",
                f"Analysts upgrade {query} with buy recommendation",
                f"{query} reports better than expected earnings",
                f"Heavy volume trading observed in {query}",
                f"{query} stock hits new resistance level",
                f"Market sentiment positive for {query} sector",
                f"{query} shows bullish momentum in today's session"
            ]
            
            articles = []
            for i, headline in enumerate(mock_headlines[:max_results]):
                articles.append({
                    'title': headline,
                    'url': f'https://example.com/news/{i}',
                    'source': 'Google News',
                    'timestamp': datetime.now() - timedelta(hours=i),
                    'content': f"Full article content about {headline}..."
                })
            
            logger.info(f"Scraped {len(articles)} articles for {query}")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping Google News for {query}: {e}")
            return []
    
    async def scrape_moneycontrol_news(self, symbol: str) -> List[Dict]:
        """
        Scrape Moneycontrol for stock-specific news.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            List of news articles
        """
        try:
            # Mock implementation - in production, scrape actual MoneyControl
            mock_articles = [
                {
                    'title': f"{symbol}: Strong buying interest seen at lower levels",
                    'content': f"Technical analysis suggests {symbol} may find support...",
                    'source': 'MoneyControl',
                    'timestamp': datetime.now() - timedelta(hours=1),
                    'url': f'https://moneycontrol.com/{symbol.lower()}'
                },
                {
                    'title': f"{symbol} stock in focus: Key levels to watch",
                    'content': f"Traders are closely watching {symbol} for breakout signals...",
                    'source': 'MoneyControl',
                    'timestamp': datetime.now() - timedelta(hours=2),
                    'url': f'https://moneycontrol.com/{symbol.lower()}-2'
                }
            ]
            
            logger.info(f"Scraped MoneyControl news for {symbol}")
            return mock_articles
            
        except Exception as e:
            logger.error(f"Error scraping MoneyControl for {symbol}: {e}")
            return []
    
    async def get_twitter_sentiment(self, symbol: str) -> Dict:
        """
        Get Twitter sentiment for a stock symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Twitter sentiment analysis
        """
        try:
            # Mock implementation - in production, use Twitter API
            mock_tweets = [
                f"${symbol} looking strong today! Breakout imminent #trading",
                f"Heavy volume in ${symbol}, something big coming",
                f"${symbol} technical setup looks bullish for intraday",
                f"Caution on ${symbol}, showing signs of weakness",
                f"${symbol} hitting resistance, watch for reversal"
            ]
            
            sentiments = []
            for tweet in mock_tweets:
                sentiment = self.calculate_sentiment_score(tweet)
                sentiments.append(sentiment)
            
            # Aggregate sentiment
            if sentiments:
                avg_sentiment = sum(s['combined_sentiment'] for s in sentiments) / len(sentiments)
                avg_relevance = sum(s['intraday_relevance'] for s in sentiments) / len(sentiments)
                avg_confidence = sum(s['confidence'] for s in sentiments) / len(sentiments)
            else:
                avg_sentiment = avg_relevance = avg_confidence = 0
            
            return {
                'tweet_count': len(mock_tweets),
                'average_sentiment': avg_sentiment,
                'intraday_relevance': avg_relevance,
                'confidence': avg_confidence,
                'tweets_analyzed': len(sentiments)
            }
            
        except Exception as e:
            logger.error(f"Error getting Twitter sentiment for {symbol}: {e}")
            return {
                'tweet_count': 0, 'average_sentiment': 0,
                'intraday_relevance': 0, 'confidence': 0,
                'tweets_analyzed': 0
            }
    
    async def call_ai_sentiment_analysis(self, text: str, symbol: str) -> Dict:
        """
        Use AI (GPT-4/Claude) for advanced sentiment analysis.
        
        Args:
            text: Text to analyze
            symbol: Stock symbol for context
            
        Returns:
            AI-powered sentiment analysis
        """
        if self.config.MOCK_AI:
            # Mock AI response
            return {
                'ai_sentiment': 0.6,
                'intraday_impact': 0.7,
                'confidence': 0.8,
                'reasoning': f"Positive sentiment detected for {symbol} based on bullish keywords and market context",
                'trade_recommendation': 'WATCH',
                'risk_level': 'MEDIUM'
            }
        
        try:
            # In production, implement actual AI API calls
            prompt = f"""
            Analyze the sentiment of this financial news/text for intraday trading of {symbol}:
            
            Text: {text}
            
            Provide:
            1. Sentiment score (-1 to 1)
            2. Intraday impact score (0 to 1)
            3. Confidence level (0 to 1)
            4. Brief reasoning
            5. Trade recommendation (BUY/SELL/WATCH/AVOID)
            6. Risk level (LOW/MEDIUM/HIGH)
            
            Return as JSON.
            """
            
            # Mock response for now
            return {
                'ai_sentiment': 0.3,
                'intraday_impact': 0.5,
                'confidence': 0.7,
                'reasoning': f"Mixed sentiment with moderate intraday relevance for {symbol}",
                'trade_recommendation': 'WATCH',
                'risk_level': 'MEDIUM'
            }
            
        except Exception as e:
            logger.error(f"Error in AI sentiment analysis: {e}")
            return {
                'ai_sentiment': 0, 'intraday_impact': 0, 'confidence': 0,
                'reasoning': 'Error in analysis', 'trade_recommendation': 'AVOID',
                'risk_level': 'HIGH'
            }
    
    async def analyze_stock_sentiment(self, symbol: str) -> Dict:
        """
        Comprehensive sentiment analysis for a stock.
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            Complete sentiment analysis report
        """
        try:
            logger.info(f"🔍 Analyzing sentiment for {symbol}")
            
            # Gather news from multiple sources
            google_news = await self.scrape_google_news(symbol, 5)
            moneycontrol_news = await self.scrape_moneycontrol_news(symbol)
            twitter_sentiment = await self.get_twitter_sentiment(symbol)
            
            # Combine all news text
            all_headlines = []
            all_content = []
            
            for article in google_news + moneycontrol_news:
                all_headlines.append(article['title'])
                all_content.append(article.get('content', ''))
            
            combined_text = ' '.join(all_headlines + all_content)
            
            # Basic sentiment analysis
            basic_sentiment = self.calculate_sentiment_score(combined_text)
            
            # AI-powered analysis
            ai_sentiment = await self.call_ai_sentiment_analysis(combined_text, symbol)
            
            # Calculate final sentiment score
            news_weight = 0.4
            twitter_weight = 0.3
            ai_weight = 0.3
            
            final_sentiment = (
                basic_sentiment['combined_sentiment'] * news_weight +
                twitter_sentiment['average_sentiment'] * twitter_weight +
                ai_sentiment['ai_sentiment'] * ai_weight
            )
            
            # Calculate intraday relevance
            intraday_relevance = (
                basic_sentiment['intraday_relevance'] * 0.4 +
                twitter_sentiment['intraday_relevance'] * 0.3 +
                ai_sentiment['intraday_impact'] * 0.3
            )
            
            # Calculate confidence
            confidence = (
                basic_sentiment['confidence'] * 0.3 +
                twitter_sentiment['confidence'] * 0.3 +
                ai_sentiment['confidence'] * 0.4
            )
            
            result = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'final_sentiment': final_sentiment,
                'intraday_relevance': intraday_relevance,
                'confidence': confidence,
                'news_count': len(google_news + moneycontrol_news),
                'tweet_count': twitter_sentiment['tweet_count'],
                'basic_sentiment': basic_sentiment,
                'twitter_sentiment': twitter_sentiment,
                'ai_sentiment': ai_sentiment,
                'trade_signal': self.generate_trade_signal(final_sentiment, intraday_relevance, confidence)
            }
            
            logger.info(f"✅ Sentiment analysis complete for {symbol}: "
                       f"Sentiment={final_sentiment:.2f}, "
                       f"Relevance={intraday_relevance:.2f}, "
                       f"Confidence={confidence:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'final_sentiment': 0,
                'intraday_relevance': 0,
                'confidence': 0,
                'error': str(e)
            }
    
    def generate_trade_signal(self, sentiment: float, relevance: float, confidence: float) -> str:
        """
        Generate trade signal based on sentiment analysis.
        
        Args:
            sentiment: Sentiment score (-1 to 1)
            relevance: Intraday relevance (0 to 1)
            confidence: Analysis confidence (0 to 1)
            
        Returns:
            Trade signal string
        """
        # Minimum thresholds
        min_relevance = 0.3
        min_confidence = 0.4
        
        if relevance < min_relevance or confidence < min_confidence:
            return "INSUFFICIENT_DATA"
        
        if sentiment > 0.3 and relevance > 0.5 and confidence > 0.6:
            return "BULLISH"
        elif sentiment < -0.3 and relevance > 0.5 and confidence > 0.6:
            return "BEARISH"
        elif abs(sentiment) < 0.2:
            return "NEUTRAL"
        else:
            return "WATCH"
    
    async def analyze_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Analyze sentiment for multiple stocks.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary with sentiment analysis for each stock
        """
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = await self.analyze_stock_sentiment(symbol)
                # Rate limiting
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results


# Standalone function for easy import
async def analyze_sentiment(symbols: List[str]) -> Dict[str, Dict]:
    """
    Convenience function to analyze sentiment for stocks.
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        Sentiment analysis for each stock
    """
    async with SentimentAnalyzer() as analyzer:
        return await analyzer.analyze_multiple_stocks(symbols)


if __name__ == "__main__":
    # Test the sentiment analyzer
    async def test_sentiment():
        test_symbols = ["RELIANCE", "TCS", "INFY"]
        
        try:
            results = await analyze_sentiment(test_symbols)
            
            print(f"✅ Sentiment analysis complete for {len(results)} stocks\n")
            
            for symbol, analysis in results.items():
                if 'error' not in analysis:
                    print(f"{symbol}:")
                    print(f"  Sentiment: {analysis['final_sentiment']:.2f}")
                    print(f"  Relevance: {analysis['intraday_relevance']:.2f}")
                    print(f"  Confidence: {analysis['confidence']:.2f}")
                    print(f"  Signal: {analysis['trade_signal']}")
                    print()
                else:
                    print(f"{symbol}: Error - {analysis['error']}")
                    
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    asyncio.run(test_sentiment())
