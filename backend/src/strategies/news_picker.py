"""
News-Based Stock Picker - Selects stocks based on high-impact news.
"""
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from models import StockPickingConfig


class NewsBasedStockPicker:
    """
    Picks stocks based on news analysis.
    
    Filters news by:
    - Impact level (HIGH/MEDIUM/LOW)
    - Sentiment (POSITIVE/NEGATIVE/NEUTRAL)
    - Relevance score (0-100)
    - Timeframe (IMMEDIATE/SHORT_TERM/LONG_TERM)
    
    Extracts stock symbols from relatedStocks field.
    """
    
    def __init__(self, news_aggregator):
        """
        Initialize News-Based Stock Picker.
        
        Args:
            news_aggregator: NewsAggregator instance
        """
        self.news_aggregator = news_aggregator
        logger.info("📰 News-Based Stock Picker initialized")
    
    async def pick_stocks(
        self,
        config: StockPickingConfig,
        refresh_news: bool = False
    ) -> List[Dict]:
        """
        Pick stocks based on news and configuration.
        
        Args:
            config: Stock picking configuration
            refresh_news: Whether to refresh news cache
        
        Returns:
            List of stock picks with context:
            [
                {
                    "symbol": "RELIANCE",
                    "score": 95,
                    "news": [...],  # Related news articles
                    "reasoning": "High impact positive news on green energy"
                }
            ]
        """
        try:
            logger.info(f"🔍 Picking stocks with config: {config.type}")
            
            # Get all news with AI analysis
            all_news = await self.news_aggregator.get_news_with_analysis(
                limit=100,
                refresh=refresh_news
            )
            
            logger.info(f"📊 Fetched {len(all_news)} news articles")
            
            # Filter news based on config
            filtered_news = self._filter_news(all_news, config)
            
            logger.info(f"✅ Filtered to {len(filtered_news)} relevant articles")
            
            # Extract stocks from filtered news
            stock_picks = self._extract_stocks(filtered_news, config)
            
            logger.info(f"🎯 Selected {len(stock_picks)} stocks")
            
            return stock_picks
            
        except Exception as e:
            logger.error(f"❌ Error picking stocks: {e}")
            return []
    
    def _filter_news(
        self,
        news_list: List[Dict],
        config: StockPickingConfig
    ) -> List[Dict]:
        """Filter news based on configuration criteria"""
        filtered = []

        # Use newsFilters from config (the correct attribute name)
        filters = config.newsFilters or {}
        
        for news in news_list:
            ai_analysis = news.get('aiAnalysis', {})
            
            # Skip if no AI analysis
            if not ai_analysis:
                continue
            
            # Filter by impact
            if 'impact' in filters:
                required_impact = filters['impact']
                if isinstance(required_impact, str):
                    if ai_analysis.get('impact') != required_impact:
                        continue
                elif isinstance(required_impact, list):
                    if ai_analysis.get('impact') not in required_impact:
                        continue
            
            # Filter by sentiment
            if 'sentiment' in filters:
                required_sentiment = filters['sentiment']
                if isinstance(required_sentiment, str):
                    if ai_analysis.get('sentiment') != required_sentiment:
                        continue
                elif isinstance(required_sentiment, list):
                    if ai_analysis.get('sentiment') not in required_sentiment:
                        continue
            
            # Filter by relevance score
            if 'relevance' in filters:
                relevance_threshold = filters['relevance']
                news_relevance = ai_analysis.get('relevance', 0)
                
                # Handle different formats: ">=80", 80, etc.
                if isinstance(relevance_threshold, str):
                    if relevance_threshold.startswith('>='):
                        threshold = int(relevance_threshold[2:])
                        if news_relevance < threshold:
                            continue
                    elif relevance_threshold.startswith('>'):
                        threshold = int(relevance_threshold[1:])
                        if news_relevance <= threshold:
                            continue
                    elif relevance_threshold.startswith('<='):
                        threshold = int(relevance_threshold[2:])
                        if news_relevance > threshold:
                            continue
                    elif relevance_threshold.startswith('<'):
                        threshold = int(relevance_threshold[1:])
                        if news_relevance >= threshold:
                            continue
                else:
                    if news_relevance < relevance_threshold:
                        continue
            
            # Filter by timeframe
            if 'timeframe' in filters:
                required_timeframe = filters['timeframe']
                if isinstance(required_timeframe, str):
                    if ai_analysis.get('timeframe') != required_timeframe:
                        continue
                elif isinstance(required_timeframe, list):
                    if ai_analysis.get('timeframe') not in required_timeframe:
                        continue
            
            # Filter by category
            if 'category' in filters:
                required_categories = filters['category']
                if isinstance(required_categories, str):
                    required_categories = [required_categories]
                
                news_categories = news.get('categories', [])
                if not any(cat in news_categories for cat in required_categories):
                    continue
            
            filtered.append(news)
        
        return filtered
    
    def _extract_stocks(
        self,
        news_list: List[Dict],
        config: StockPickingConfig
    ) -> List[Dict]:
        """Extract and rank stocks from filtered news"""
        
        # Collect all stocks with their news
        stock_news_map = {}  # {symbol: [news_articles]}
        stock_scores = {}    # {symbol: total_score}
        
        for news in news_list:
            ai_analysis = news.get('aiAnalysis', {})
            related_stocks = ai_analysis.get('relatedStocks', [])
            relevance = ai_analysis.get('relevance', 0)
            
            # Skip if no related stocks
            if not related_stocks:
                continue
            
            for stock in related_stocks:
                # Clean stock symbol (remove exchange prefix if present)
                symbol = stock.strip().upper()
                if ':' in symbol:
                    symbol = symbol.split(':')[1]
                
                # Initialize if new stock
                if symbol not in stock_news_map:
                    stock_news_map[symbol] = []
                    stock_scores[symbol] = 0
                
                # Add news to stock
                stock_news_map[symbol].append(news)
                
                # Add to score (relevance + impact weight)
                impact_weight = {
                    'HIGH': 3,
                    'MEDIUM': 2,
                    'LOW': 1
                }.get(ai_analysis.get('impact', 'LOW'), 1)
                
                stock_scores[symbol] += relevance * impact_weight
        
        # Sort stocks by score
        sorted_stocks = sorted(
            stock_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Build stock picks
        stock_picks = []
        max_stocks = config.maxStocks or 5
        
        for symbol, score in sorted_stocks[:max_stocks]:
            news_articles = stock_news_map[symbol]
            
            # Generate reasoning
            reasoning = self._generate_reasoning(symbol, news_articles)
            
            stock_picks.append({
                'symbol': symbol,
                'score': round(score, 2),
                'newsCount': len(news_articles),
                'news': news_articles,
                'reasoning': reasoning
            })
        
        return stock_picks
    
    def _generate_reasoning(
        self,
        symbol: str,
        news_articles: List[Dict]
    ) -> str:
        """Generate human-readable reasoning for stock pick"""
        
        if not news_articles:
            return f"Selected {symbol}"
        
        # Get top news article
        top_news = max(
            news_articles,
            key=lambda x: x.get('aiAnalysis', {}).get('relevance', 0)
        )
        
        ai_analysis = top_news.get('aiAnalysis', {})
        impact = ai_analysis.get('impact', 'UNKNOWN')
        sentiment = ai_analysis.get('sentiment', 'NEUTRAL')
        analysis_text = ai_analysis.get('analysis', '')
        
        # Build reasoning
        reasoning_parts = [
            f"{impact} impact",
            f"{sentiment.lower()} sentiment"
        ]
        
        if len(news_articles) > 1:
            reasoning_parts.append(f"{len(news_articles)} related articles")
        
        reasoning = f"{symbol}: {', '.join(reasoning_parts)}"
        
        if analysis_text:
            # Add first sentence of analysis
            first_sentence = analysis_text.split('.')[0]
            reasoning += f" - {first_sentence}"
        
        return reasoning
    
    async def get_stock_context(
        self,
        symbol: str,
        days: int = 1
    ) -> Dict:
        """
        Get news context for a specific stock.
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
        
        Returns:
            {
                "symbol": "RELIANCE",
                "newsCount": 3,
                "news": [...],
                "avgRelevance": 85,
                "dominantSentiment": "POSITIVE"
            }
        """
        try:
            # Get all news
            all_news = await self.news_aggregator.get_news_with_analysis(limit=100)
            
            # Filter for this stock
            stock_news = []
            for news in all_news:
                ai_analysis = news.get('aiAnalysis', {})
                related_stocks = ai_analysis.get('relatedStocks', [])
                
                # Check if symbol is in related stocks
                for stock in related_stocks:
                    clean_symbol = stock.strip().upper()
                    if ':' in clean_symbol:
                        clean_symbol = clean_symbol.split(':')[1]
                    
                    if clean_symbol == symbol.upper():
                        stock_news.append(news)
                        break
            
            if not stock_news:
                return {
                    'symbol': symbol,
                    'newsCount': 0,
                    'news': [],
                    'avgRelevance': 0,
                    'dominantSentiment': 'NEUTRAL'
                }
            
            # Calculate metrics
            relevances = [n.get('aiAnalysis', {}).get('relevance', 0) for n in stock_news]
            avg_relevance = sum(relevances) / len(relevances) if relevances else 0
            
            sentiments = [n.get('aiAnalysis', {}).get('sentiment', 'NEUTRAL') for n in stock_news]
            dominant_sentiment = max(set(sentiments), key=sentiments.count)
            
            return {
                'symbol': symbol,
                'newsCount': len(stock_news),
                'news': stock_news,
                'avgRelevance': round(avg_relevance, 2),
                'dominantSentiment': dominant_sentiment
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting stock context: {e}")
            return {
                'symbol': symbol,
                'newsCount': 0,
                'news': [],
                'avgRelevance': 0,
                'dominantSentiment': 'NEUTRAL'
            }

