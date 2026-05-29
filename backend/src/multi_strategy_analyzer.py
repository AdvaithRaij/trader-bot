"""
Multi-Strategy Analyzer for Trading Pipeline.

Generates trade plans using three distinct analytical approaches:
1. Fundamental Analysis - P/E, EPS, Market Cap, D/E focus
2. News-Based Analysis - Sentiment, impact, timing focus
3. Combined Analysis - Holistic weighted approach

Each strategy produces entry/SL/target levels with confidence scores.
"""

import json
import asyncio
from typing import Dict, Optional, List, Literal, Any
from datetime import datetime
import time
from loguru import logger

from config import get_config
from models.screener import StockAnalysisData
from models.trade_plan import (
    StrategyAnalysis,
    StrategyRecommendation,
    MultiStrategyResult,
    MultiStrategyOutput
)

config = get_config()


class MultiStrategyAnalyzer:
    """
    Analyzes stocks using three distinct strategies.
    
    Each strategy focuses on different aspects:
    - Fundamental: Value-based, conservative
    - News-Based: Event-driven, momentum
    - Combined: Holistic, balanced
    """
    
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0
    
    def __init__(self, news_aggregator=None):
        self.ai_client = None
        self.ai_provider = config.AI_PROVIDER.lower()
        self.news_aggregator = news_aggregator
        self._setup_ai_client()
        logger.info(f"🎯 MultiStrategyAnalyzer initialized with provider: {self.ai_provider}")
    
    def _setup_ai_client(self):
        """Setup AI client based on configured provider."""
        if self.ai_provider == "openai" and config.OPENAI_API_KEY:
            self._setup_openai()
            if self.ai_client:
                return

        if self.ai_provider == "groq" and config.GROQ_API_KEY:
            self._setup_groq()
            if self.ai_client:
                return

        if self.ai_provider == "gemini" and config.GEMINI_API_KEY:
            self._setup_gemini()
            if self.ai_client:
                return

        # Fallback
        if config.OPENAI_API_KEY and not self.ai_client:
            self._setup_openai()
        if config.GROQ_API_KEY and not self.ai_client:
            self._setup_groq()
        if config.GEMINI_API_KEY and not self.ai_client:
            self._setup_gemini()
    
    def _setup_openai(self):
        """Setup OpenAI AI client."""
        try:
            from openai import OpenAI
            self.ai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.ai_provider = "openai"
            logger.info(f"✅ OpenAI configured for MultiStrategyAnalyzer: {config.OPENAI_MODEL}")
        except Exception as e:
            logger.error(f"❌ Error setting up OpenAI: {e}")

    def _setup_gemini(self):
        """Setup Gemini AI client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.ai_client = genai.GenerativeModel(config.GEMINI_MODEL)
            self.ai_provider = "gemini"
            logger.info(f"✅ Gemini configured for MultiStrategyAnalyzer")
        except Exception as e:
            logger.error(f"❌ Error setting up Gemini: {e}")

    def _setup_groq(self):
        """Setup Groq AI client."""
        try:
            from groq import Groq
            self.ai_client = Groq(api_key=config.GROQ_API_KEY)
            self.ai_provider = "groq"
            logger.info(f"✅ Groq configured for MultiStrategyAnalyzer with model: {config.GROQ_MODEL}")
        except Exception as e:
            logger.error(f"❌ Error setting up Groq: {e}")
    
    async def analyze_stock(self, data: StockAnalysisData) -> MultiStrategyResult:
        """
        Generate all three strategy analyses for a stock.
        
        Args:
            data: Complete StockAnalysisData from DataAggregator
            
        Returns:
            MultiStrategyResult with all 3 strategies and recommendation
        """
        start_time = time.time()
        
        try:
            # Generate all 3 strategies in parallel
            fundamental_task = self._analyze_fundamental(data)
            news_task = self._analyze_news_based(data)
            combined_task = self._analyze_combined(data)
            
            fundamental, news_based, combined = await asyncio.gather(
                fundamental_task, news_task, combined_task,
                return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(fundamental, Exception):
                logger.error(f"Fundamental analysis failed: {fundamental}")
                fundamental = self._generate_fallback_analysis(data, "fundamental")
            if isinstance(news_based, Exception):
                logger.error(f"News-based analysis failed: {news_based}")
                news_based = self._generate_fallback_analysis(data, "news_based")
            if isinstance(combined, Exception):
                logger.error(f"Combined analysis failed: {combined}")
                combined = self._generate_fallback_analysis(data, "combined")
            
            # Generate recommendation
            recommendation = await self._generate_recommendation(
                data, fundamental, news_based, combined
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return MultiStrategyResult(
                symbol=data.symbol,
                name=data.name,
                current_price=data.current_price,
                day_change_pct=data.day_change_pct,
                fundamental=fundamental,
                news_based=news_based,
                combined=combined,
                recommendation=recommendation,
                screener_score=data.screener_score,
                analysis_timestamp=datetime.now(),
                analysis_duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {data.symbol}: {e}")
            raise

    async def _analyze_fundamental(self, data: StockAnalysisData) -> StrategyAnalysis:
        """Generate fundamental strategy analysis."""
        prompt = self._build_fundamental_prompt(data)
        return await self._call_ai_for_strategy(data, "fundamental", prompt)

    async def _analyze_news_based(self, data: StockAnalysisData) -> StrategyAnalysis:
        """Generate news-based strategy analysis."""
        # Fetch actual news articles for this stock
        self._current_stock_news = await self._get_stock_news_articles(data.symbol)
        prompt = self._build_news_prompt(data)
        return await self._call_ai_for_strategy(data, "news_based", prompt)

    async def _analyze_combined(self, data: StockAnalysisData) -> StrategyAnalysis:
        """Generate combined strategy analysis."""
        prompt = self._build_combined_prompt(data)
        return await self._call_ai_for_strategy(data, "combined", prompt)

    async def _call_ai_for_strategy(
        self,
        data: StockAnalysisData,
        strategy_id: str,
        prompt: str
    ) -> StrategyAnalysis:
        """Call AI to generate strategy analysis."""
        for attempt in range(self.MAX_RETRIES):
            try:
                if not self.ai_client:
                    return self._generate_fallback_analysis(data, strategy_id)

                if self.ai_provider == "gemini":
                    response = await asyncio.to_thread(
                        self.ai_client.generate_content,
                        prompt
                    )
                    response_text = response.text.strip()
                elif self.ai_provider == "openai":
                    logger.info(f"🤖 Calling OpenAI model: {config.OPENAI_MODEL} for {strategy_id} strategy")
                    response = await asyncio.to_thread(
                        self.ai_client.chat.completions.create,
                        model=config.OPENAI_MODEL,
                        messages=[
                            {"role": "system", "content": self._get_system_prompt()},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=3000  # Increased for verbose reasoning
                    )
                    response_text = response.choices[0].message.content.strip()
                    logger.info(f"✅ OpenAI response received for {strategy_id}, length: {len(response_text)} chars")
                else:  # groq
                    logger.info(f"🤖 Calling Groq model: {config.GROQ_MODEL} for {strategy_id} strategy")
                    response = await asyncio.to_thread(
                        self.ai_client.chat.completions.create,
                        model=config.GROQ_MODEL,
                        messages=[
                            {"role": "system", "content": self._get_system_prompt()},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=8192  # Increased for verbose reasoning (Groq max)
                    )
                    response_text = response.choices[0].message.content.strip()
                    logger.info(f"✅ Groq response received for {strategy_id}, length: {len(response_text)} chars")

                return self._parse_strategy_response(response_text, data, strategy_id)

            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"AI call failed for {strategy_id}: {e}")
                    return self._generate_fallback_analysis(data, strategy_id)

        return self._generate_fallback_analysis(data, strategy_id)

    def _get_system_prompt(self) -> str:
        """Get system prompt for AI."""
        return """You are an expert Indian stock market analyst. Provide concise, actionable analysis.

CRITICAL REQUIREMENTS:
1. RESPOND WITH ONLY THE JSON OBJECT - NO text before/after, NO markdown, NO comments
2. Use EXACT JSON structure - do NOT modify field names or structure
3. Be CONCISE - 1-2 sentences per reasoning field, straight to the point
4. Reference specific data (P/E values, RSI, news) but avoid lengthy calculations
5. ENSURE VALID JSON: proper quotes, commas, no trailing commas, matching braces
6. For HOLD: use 0 for entry/stop_loss/target prices, NOT null

CONFIDENCE CALCULATION (systematic):
Base 50, then: Trend match +15/-10, RSI 40-60 +10, RVOL >2x +10, News support +10/-10, P/E favorable +10, R:R >=2 +10. Max 95, Min 20.

Price levels: Conservative SL (1-3%), realistic targets (2-8%)."""

    def _build_fundamental_prompt(self, data: StockAnalysisData) -> str:
        """Build prompt for fundamental analysis."""
        f = data.fundamentals
        return f"""Analyze {data.symbol} - FUNDAMENTAL strategy.

DATA: P/E {f.pe_ratio or 'N/A'}, Fwd P/E {f.forward_pe or 'N/A'}, EPS ₹{f.eps or 'N/A'}, ROE {f.roe or 'N/A'}%, D/E {f.debt_to_equity or 'N/A'}
PRICE: ₹{data.current_price:.2f} ({data.day_change_pct:+.1f}%), RSI {data.rsi_14:.0f}, Trend: {data.trend}

CONSERVATIVE plan. SL: 1-2%, Targets: 3-5%.

{{
    "direction": "BUY/SELL/HOLD",
    "confidence": 0-100,
    "entry": price,
    "stop_loss": price,
    "target_1": price,
    "target_2": price,
    "reasoning": "Valuation: [P/E assessment]. Financials: [Debt, ROE]. Growth: [EPS outlook]. Technicals: [RSI, trend]. Conclusion: [Trade thesis]. (Keep each section 1-2 sentences, straight to point)",
    "risks": ["Risk 1", "Risk 2"],
    "catalysts": ["Catalyst 1", "Catalyst 2"]
}}"""

    async def _get_stock_news_articles(self, symbol: str) -> List[Dict]:
        """Fetch actual news articles for a stock."""
        try:
            if not self.news_aggregator:
                return []

            # Get all news
            all_news = await self.news_aggregator.get_news_with_analysis(limit=100)

            # Filter for this stock
            stock_news = []
            symbol_upper = symbol.upper()

            for news in all_news:
                ai_analysis = news.get('aiAnalysis', {})
                related_stocks = ai_analysis.get('relatedStocks', [])

                # Check if symbol is in related stocks
                for stock in related_stocks:
                    clean_symbol = stock.strip().upper()
                    if ':' in clean_symbol:
                        clean_symbol = clean_symbol.split(':')[1]

                    if clean_symbol == symbol_upper:
                        stock_news.append(news)
                        break

            return stock_news[:10]  # Return max 10 most relevant articles

        except Exception as e:
            logger.error(f"Error fetching news articles for {symbol}: {e}")
            return []

    def _build_news_prompt(self, data: StockAnalysisData) -> str:
        """Build prompt for news-based analysis."""
        n = data.news

        # Build news articles section
        news_articles_text = ""
        if hasattr(self, '_current_stock_news') and self._current_stock_news:
            news_articles_text = "\n\nRELATED NEWS ARTICLES:\n"
            for i, article in enumerate(self._current_stock_news[:10], 1):
                ai_analysis = article.get('aiAnalysis', {})
                news_articles_text += f"""
Article {i}:
- Title: {article.get('title', 'N/A')}
- Summary: {article.get('summary', 'N/A')[:300]}
- Source: {article.get('source', 'N/A')}
- Published: {article.get('publishedAt', 'N/A')}
- AI Impact: {ai_analysis.get('impact', 'N/A')}
- AI Sentiment: {ai_analysis.get('sentiment', 'N/A')}
- AI Analysis: {ai_analysis.get('analysis', 'N/A')}
"""
        else:
            news_articles_text = "\n\nNO RECENT NEWS ARTICLES FOUND FOR THIS STOCK.\n"

        return f"""Analyze {data.symbol} ({data.name}) using NEWS-BASED analysis.

NEWS SUMMARY:
- Has Recent News: {n.has_recent_news}
- News Count (24h): {n.news_count_24h}
- Sentiment: {n.sentiment.upper()}
- Sentiment Score: {n.sentiment_score}
- Impact: {n.impact}
- Latest Headline: {n.latest_headline or 'No recent news'}
- Hours Since Latest: {n.hours_since_latest or 'N/A'}
- Categories: {', '.join(n.categories) if n.categories else 'None'}
{news_articles_text}

FUNDAMENTAL CONTEXT:
- P/E Ratio: {data.fundamentals.pe_ratio or 'N/A'}
- Market Cap: ₹{data.fundamentals.market_cap_cr:,.0f} Cr
- Sector: {data.fundamentals.sector}

CURRENT PRICE: ₹{data.current_price:.2f}
DAY CHANGE: {data.day_change_pct:.2f}%
RVOL: {data.rvol:.1f}x
RSI: {data.rsi_14:.1f}

MOMENTUM plan. SL: 2-3%, Targets: 4-8%. If no news, HOLD.

{{
    "direction": "BUY/SELL/HOLD",
    "confidence": 0-100,
    "entry": price,
    "stop_loss": price,
    "target_1": price,
    "target_2": price,
    "reasoning": "News Impact: [What news says]. Sentiment: [Bullish/bearish why]. Fundamentals: [Alignment]. Momentum: [RVOL, RSI]. Conclusion: [Trade thesis]. (1-2 sentences each)",
    "risks": ["Risk 1", "Risk 2"],
    "catalysts": ["Catalyst 1", "Catalyst 2"]
}}"""

    def _build_combined_prompt(self, data: StockAnalysisData) -> str:
        """Build prompt for combined analysis."""
        f = data.fundamentals
        n = data.news
        return f"""Analyze {data.symbol} ({data.name}) using COMBINED analysis.

FUNDAMENTAL SUMMARY:
- P/E: {f.pe_ratio or 'N/A'}, EPS: ₹{f.eps or 'N/A'}, MCap: ₹{f.market_cap_cr:,.0f} Cr
- D/E: {f.debt_to_equity or 'N/A'}, ROE: {f.roe or 'N/A'}%
- Sector: {f.sector}

TECHNICAL SUMMARY:
- Price: ₹{data.current_price:.2f} ({data.day_change_pct:+.2f}%)
- RSI: {data.rsi_14:.1f}, Trend: {data.trend}
- RVOL: {data.rvol:.1f}x, ATR%: {data.atr_pct:.2f}%
- Pivot: ₹{data.pivot_pp:.2f}, S1: ₹{data.support_1:.2f}, R1: ₹{data.resistance_1:.2f}

NEWS SUMMARY:
- Sentiment: {n.sentiment.upper()} (Score: {n.sentiment_score})
- Impact: {n.impact}
- Headline: {n.latest_headline or 'No recent news'}

MARKET CONTEXT:
- NIFTY Trend: {data.nifty_trend}
- VIX: {data.vix}

BALANCED plan. Weight: Tech 35%, Fund 30%, News 25%, Market 10%. SL: 1.5-2.5%, Targets: 3-6%.

{{
    "direction": "BUY/SELL/HOLD",
    "confidence": 0-100,
    "entry": price,
    "stop_loss": price,
    "target_1": price,
    "target_2": price,
    "reasoning": "Fundamentals (30%): [Valuation, health]. Technicals (35%): [RSI, trend, pivots]. News (25%): [Sentiment]. Market (10%): [NIFTY, VIX]. Confluence: [Alignment]. Conclusion: [Trade thesis]. (1-2 sentences each)",
    "risks": ["Risk 1", "Risk 2"],
    "catalysts": ["Catalyst 1", "Catalyst 2"]
}}"""

    def _parse_strategy_response(
        self,
        response_text: str,
        data: StockAnalysisData,
        strategy_id: str
    ) -> StrategyAnalysis:
        """Parse AI response into StrategyAnalysis."""
        try:
            # Clean response
            text = response_text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            # Extract JSON object - find first { and last }
            # This handles cases where AI adds extra text after JSON
            start_idx = text.find('{')
            end_idx = text.rfind('}')

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON object found in response")

            json_text = text[start_idx:end_idx + 1]

            # Try to parse JSON, if it fails, try to fix common issues
            try:
                result = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error for {strategy_id}: {e}. Attempting to fix...")
                # Try to fix common issues like missing commas or quotes
                # For now, just re-raise and use fallback
                raise

            # Extract values with defaults (handle null/None values)
            direction = result.get("direction", "HOLD").upper()
            confidence = float(result.get("confidence") or 50)

            # Handle null/None values for prices
            entry_raw = result.get("entry")
            entry = float(entry_raw) if entry_raw is not None else data.current_price

            stop_loss_raw = result.get("stop_loss")
            stop_loss = float(stop_loss_raw) if stop_loss_raw is not None else entry * 0.98

            target_1_raw = result.get("target_1")
            target_1 = float(target_1_raw) if target_1_raw is not None else entry * 1.03

            target_2_raw = result.get("target_2")
            target_2 = float(target_2_raw) if target_2_raw is not None else None

            # Validate entry price
            if entry <= 0:
                logger.warning(f"Invalid entry price {entry} for {data.symbol}, using current price")
                entry = data.current_price if data.current_price > 0 else 100
                stop_loss = entry * 0.98
                target_1 = entry * 1.03

            # Calculate percentages (with division by zero protection)
            stop_loss_pct = ((stop_loss - entry) / entry) * 100 if entry > 0 else 0
            target_1_pct = ((target_1 - entry) / entry) * 100 if entry > 0 else 0
            target_2_pct = ((target_2 - entry) / entry) * 100 if (target_2 and entry > 0) else None

            # Calculate risk/reward
            risk_per_share = abs(entry - stop_loss)
            reward_per_share = abs(target_1 - entry)
            risk_reward = reward_per_share / risk_per_share if risk_per_share > 0 else 0

            strategy_names = {
                "fundamental": "Fundamental Analysis",
                "news_based": "News-Based Analysis",
                "combined": "Combined Analysis"
            }

            # Parse reasoning - can be string or dict
            reasoning_data = result.get("reasoning", "AI analysis")
            if isinstance(reasoning_data, dict):
                # Convert verbose structured reasoning to formatted string
                reasoning_parts = []
                for key, value in reasoning_data.items():
                    if value:
                        # Format key nicely (e.g., "valuation_analysis" -> "Valuation Analysis")
                        formatted_key = key.replace('_', ' ').title()
                        reasoning_parts.append(f"**{formatted_key}:** {value}")
                reasoning_text = "\n\n".join(reasoning_parts)
            else:
                reasoning_text = str(reasoning_data)

            # Parse risks - can be list of strings or list of dicts
            risks_data = result.get("risks", [])
            risks_list = []
            for risk in risks_data:
                if isinstance(risk, dict):
                    risk_text = risk.get("risk", "")
                    explanation = risk.get("explanation", "")
                    if risk_text and explanation:
                        risks_list.append(f"{risk_text}: {explanation}")
                    elif risk_text:
                        risks_list.append(risk_text)
                else:
                    risks_list.append(str(risk))

            # Parse catalysts - can be list of strings or list of dicts
            catalysts_data = result.get("catalysts", [])
            catalysts_list = []
            for catalyst in catalysts_data:
                if isinstance(catalyst, dict):
                    catalyst_text = catalyst.get("catalyst", "")
                    explanation = catalyst.get("explanation", "")
                    if catalyst_text and explanation:
                        catalysts_list.append(f"{catalyst_text}: {explanation}")
                    elif catalyst_text:
                        catalysts_list.append(catalyst_text)
                else:
                    catalysts_list.append(str(catalyst))

            return StrategyAnalysis(
                strategy_id=strategy_id,
                strategy_name=strategy_names.get(strategy_id, strategy_id),
                direction=direction,
                confidence=confidence,
                entry=round(entry, 2),
                stop_loss=round(stop_loss, 2),
                stop_loss_pct=round(stop_loss_pct, 2),
                target_1=round(target_1, 2),
                target_1_pct=round(target_1_pct, 2),
                target_2=round(target_2, 2) if target_2 else None,
                target_2_pct=round(target_2_pct, 2) if target_2_pct else None,
                risk_reward_ratio=round(risk_reward, 2),
                risk_per_share=round(risk_per_share, 2),
                reasoning=reasoning_text,
                risks=risks_list,
                catalysts=catalysts_list,
                timeframe=result.get("timeframe", "1-3 days"),
                is_actionable=direction != "HOLD"
            )

        except Exception as e:
            logger.error(f"Error parsing AI response for {strategy_id}: {e}")
            logger.error(f"Raw AI response (first 500 chars): {response_text[:500]}")
            return self._generate_fallback_analysis(data, strategy_id)

    def _generate_fallback_analysis(
        self,
        data: StockAnalysisData,
        strategy_id: str
    ) -> StrategyAnalysis:
        """Generate rule-based fallback analysis."""
        price = data.current_price

        # If price is 0 or invalid, return HOLD
        if price <= 0:
            return StrategyAnalysis(
                strategy_id=strategy_id,
                direction="HOLD",
                confidence=0,
                entry=0,
                stop_loss=0,
                target_1=0,
                target_2=0,
                stop_loss_pct=0,
                target_1_pct=0,
                target_2_pct=0,
                risk_per_share=0,
                reward_per_share=0,
                risk_reward_ratio=0,
                reasoning="No valid price data available",
                key_factors=[],
                risks=["No price data"],
                catalysts=[]
            )

        # Determine direction based on available data
        if strategy_id == "fundamental":
            # Use P/E and trend
            pe = data.fundamentals.pe_ratio
            if pe and pe < 20 and data.trend == "uptrend":
                direction = "BUY"
                confidence = 60
            elif pe and pe > 40:
                direction = "SELL"
                confidence = 55
            else:
                direction = "HOLD"
                confidence = 40
            sl_pct = 0.015
            t1_pct = 0.035
            t2_pct = 0.05
            timeframe = "2-5 days"

        elif strategy_id == "news_based":
            # Use news sentiment
            if data.news.sentiment == "bullish" and data.news.impact in ["HIGH", "MEDIUM"]:
                direction = "BUY"
                confidence = 70 if data.news.impact == "HIGH" else 55
            elif data.news.sentiment == "bearish" and data.news.impact in ["HIGH", "MEDIUM"]:
                direction = "SELL"
                confidence = 65 if data.news.impact == "HIGH" else 50
            else:
                direction = "HOLD"
                confidence = 35
            sl_pct = 0.02
            t1_pct = 0.05
            t2_pct = 0.08
            timeframe = "intraday to 1 day"

        else:  # combined
            # Use RSI and trend
            if data.rsi_14 < 40 and data.trend == "uptrend":
                direction = "BUY"
                confidence = 65
            elif data.rsi_14 > 70 and data.trend == "downtrend":
                direction = "SELL"
                confidence = 60
            elif data.trend == "uptrend" and data.news.sentiment != "bearish":
                direction = "BUY"
                confidence = 55
            else:
                direction = "HOLD"
                confidence = 45
            sl_pct = 0.018
            t1_pct = 0.04
            t2_pct = 0.06
            timeframe = "1-3 days"

        # Calculate levels
        if direction == "BUY":
            entry = price
            stop_loss = price * (1 - sl_pct)
            target_1 = price * (1 + t1_pct)
            target_2 = price * (1 + t2_pct)
        elif direction == "SELL":
            entry = price
            stop_loss = price * (1 + sl_pct)
            target_1 = price * (1 - t1_pct)
            target_2 = price * (1 - t2_pct)
        else:
            entry = price
            stop_loss = price * 0.98
            target_1 = price * 1.02
            target_2 = price * 1.04

        stop_loss_pct = ((stop_loss - entry) / entry) * 100
        target_1_pct = ((target_1 - entry) / entry) * 100
        target_2_pct = ((target_2 - entry) / entry) * 100
        risk_per_share = abs(entry - stop_loss)
        reward_per_share = abs(target_1 - entry)
        risk_reward = reward_per_share / risk_per_share if risk_per_share > 0 else 0

        strategy_names = {
            "fundamental": "Fundamental Analysis",
            "news_based": "News-Based Analysis",
            "combined": "Combined Analysis"
        }

        return StrategyAnalysis(
            strategy_id=strategy_id,
            strategy_name=strategy_names.get(strategy_id, strategy_id),
            direction=direction,
            confidence=confidence,
            entry=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            stop_loss_pct=round(stop_loss_pct, 2),
            target_1=round(target_1, 2),
            target_1_pct=round(target_1_pct, 2),
            target_2=round(target_2, 2),
            target_2_pct=round(target_2_pct, 2),
            risk_reward_ratio=round(risk_reward, 2),
            risk_per_share=round(risk_per_share, 2),
            reasoning=f"Rule-based {strategy_id} analysis based on available data.",
            risks=["Market volatility", "Limited data"],
            catalysts=[],
            timeframe=timeframe,
            is_actionable=direction != "HOLD"
        )

    async def _generate_recommendation(
        self,
        data: StockAnalysisData,
        fundamental: StrategyAnalysis,
        news_based: StrategyAnalysis,
        combined: StrategyAnalysis
    ) -> StrategyRecommendation:
        """Generate AI recommendation comparing all strategies."""
        # Simple rule-based recommendation
        strategies = {
            "fundamental": fundamental,
            "news_based": news_based,
            "combined": combined
        }

        # Find best strategy by confidence (with actionability preference)
        best_id = "combined"
        best_confidence = 0

        for sid, strategy in strategies.items():
            score = strategy.confidence
            if strategy.is_actionable:
                score += 10  # Prefer actionable strategies
            if strategy.risk_reward_ratio >= 1.5:
                score += 5  # Prefer good R:R

            if score > best_confidence:
                best_confidence = score
                best_id = sid

        best = strategies[best_id]

        # Determine overall sentiment
        directions = [s.direction for s in strategies.values()]
        buy_count = directions.count("BUY")
        sell_count = directions.count("SELL")

        if buy_count >= 2:
            overall_sentiment = "bullish"
        elif sell_count >= 2:
            overall_sentiment = "bearish"
        else:
            overall_sentiment = "neutral"

        # Determine trade quality using systematic scoring
        # Quality Score = (Avg Confidence * 0.4) + (R:R Score * 0.3) + (Consensus Score * 0.3)
        avg_confidence = sum(s.confidence for s in strategies.values()) / 3

        # R:R Score (0-100)
        rr_score = 0
        if best.risk_reward_ratio >= 3:
            rr_score = 100
        elif best.risk_reward_ratio >= 2.5:
            rr_score = 85
        elif best.risk_reward_ratio >= 2:
            rr_score = 70
        elif best.risk_reward_ratio >= 1.5:
            rr_score = 50
        else:
            rr_score = 25

        # Consensus Score (0-100) - how many strategies agree
        directions = [s.direction for s in strategies.values()]
        buy_count = directions.count("BUY")
        sell_count = directions.count("SELL")
        max_agreement = max(buy_count, sell_count)
        if max_agreement == 3:
            consensus_score = 100  # All agree
        elif max_agreement == 2:
            consensus_score = 60   # 2 out of 3 agree
        else:
            consensus_score = 20   # No consensus

        # Calculate weighted quality score
        quality_score = (avg_confidence * 0.4) + (rr_score * 0.3) + (consensus_score * 0.3)

        # Map quality score to label
        if quality_score >= 80:
            trade_quality = "excellent"
        elif quality_score >= 65:
            trade_quality = "good"
        elif quality_score >= 50:
            trade_quality = "fair"
        else:
            trade_quality = "poor"

        logger.info(f"📊 Trade Quality for {data.symbol}: {trade_quality} (Score: {quality_score:.1f}, Conf: {avg_confidence:.1f}, R:R: {best.risk_reward_ratio:.1f}, Consensus: {max_agreement}/3)")

        # Build comparison
        comparison = {}
        for sid, strategy in strategies.items():
            comparison[sid] = f"{strategy.direction} ({strategy.confidence:.0f}% conf, R:R {strategy.risk_reward_ratio:.1f})"

        # Build reasoning
        reasoning = f"The {best.strategy_name} offers the best risk-adjusted return with {best.confidence:.0f}% confidence and {best.risk_reward_ratio:.1f} R:R ratio."
        if best_id == "combined":
            reasoning += " This balanced approach considers all factors for higher conviction."
        elif best_id == "news_based":
            reasoning += " News momentum provides a clear catalyst for the trade."
        else:
            reasoning += " Strong fundamentals support the valuation thesis."

        return StrategyRecommendation(
            best_strategy=best_id,
            best_strategy_name=best.strategy_name,
            confidence=best.confidence,
            reasoning=reasoning,
            strategy_comparison=comparison,
            overall_sentiment=overall_sentiment,
            trade_quality=trade_quality
        )

    async def analyze_batch(
        self,
        stocks: List[StockAnalysisData]
    ) -> MultiStrategyOutput:
        """
        Analyze multiple stocks in parallel.

        Args:
            stocks: List of StockAnalysisData from DataAggregator

        Returns:
            MultiStrategyOutput with all analyses
        """
        start_time = time.time()

        # Analyze all stocks in parallel
        tasks = [self.analyze_stock(stock) for stock in stocks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing {stocks[i].symbol}: {result}")
            else:
                valid_results.append(result)

        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(f"🎯 Analyzed {len(valid_results)}/{len(stocks)} stocks in {duration_ms}ms")

        return MultiStrategyOutput(
            timestamp=datetime.now(),
            analyses=valid_results,
            total_analyzed=len(valid_results),
            analysis_duration_ms=duration_ms
        )

