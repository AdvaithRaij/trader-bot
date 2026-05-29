"""
AI Trade Assistant - Uses Groq/Gemini AI to suggest optimal entry/exit levels.
"""
import json
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from loguru import logger

from config import get_config
from prompt_loader import get_trade_levels_prompt
from models import ExecutionConfig, TradeDirection

config = get_config()

# Global rate limit tracking - skip AI calls if rate limited
_groq_rate_limited_until = 0
_ai_suggestions_cache = {}
_ai_suggestions_cache_expiry = {}
AI_CACHE_TTL = 300  # 5 minutes cache for AI suggestions


class AITradeAssistant:
    """
    AI-powered trade assistant using Groq or Gemini AI.

    Analyzes:
    - Stock symbol and current price
    - News context and sentiment
    - Recent price action (support/resistance)
    - Strategy configuration

    Suggests:
    - Entry price
    - Stop loss level
    - Target 1 (conservative)
    - Target 2 (aggressive)
    - Confidence score
    - Reasoning
    """

    def __init__(self, ai_client=None):
        """
        Initialize AI Trade Assistant.

        Args:
            ai_client: AI client (optional, will create based on AI_PROVIDER)
        """
        self.ai_client = ai_client
        self.ai_provider = config.AI_PROVIDER.lower()
        self._setup_ai_client()

        logger.info(f"🤖 AI Trade Assistant initialized with provider: {self.ai_provider}")

    def _setup_ai_client(self):
        """Setup AI client based on configured provider"""
        if self.ai_client:
            return

        # Try Groq first (preferred)
        if self.ai_provider == "groq" or (not self.ai_client and config.GROQ_API_KEY):
            self._setup_groq()
            if self.ai_client:
                return

        # Fallback to Gemini
        if self.ai_provider == "gemini" or (not self.ai_client and config.GEMINI_API_KEY):
            self._setup_gemini()

    def _setup_groq(self):
        """Setup Groq AI client"""
        try:
            from groq import Groq

            if not config.GROQ_API_KEY:
                logger.warning("⚠️ GROQ_API_KEY not set")
                return

            self.ai_client = Groq(api_key=config.GROQ_API_KEY)
            self.ai_provider = "groq"

            logger.info(f"✅ Groq AI configured: {config.GROQ_MODEL}")

        except ImportError:
            logger.warning("⚠️ groq package not installed, trying other providers")
        except Exception as e:
            logger.error(f"❌ Error setting up Groq AI: {e}")

    def _setup_gemini(self):
        """Setup Gemini AI client"""
        try:
            import google.generativeai as genai

            if not config.GEMINI_API_KEY:
                logger.warning("⚠️ GEMINI_API_KEY not set, AI assistant will use fallback")
                return

            genai.configure(api_key=config.GEMINI_API_KEY)
            self.ai_client = genai.GenerativeModel(config.GEMINI_MODEL)
            self.ai_provider = "gemini"

            logger.info(f"✅ Gemini AI configured: {config.GEMINI_MODEL}")

        except Exception as e:
            logger.error(f"❌ Error setting up Gemini AI: {e}")
    
    async def suggest_levels(
        self,
        symbol: str,
        current_price: float,
        direction: TradeDirection,
        news_context: List[Dict],
        execution_config: ExecutionConfig,
        price_data: Optional[Dict] = None
    ) -> Dict:
        """
        Suggest trading levels using AI with caching.

        Args:
            symbol: Stock symbol
            current_price: Current market price
            direction: BUY or SELL
            news_context: List of related news articles
            execution_config: Strategy execution configuration
            price_data: Recent price data (high, low, support, resistance)

        Returns:
            {
                "entryPrice": 2450.0,
                "stopLoss": 2400.0,
                "target1": 2525.0,
                "target2": 2575.0,
                "confidence": 85,
                "reasoning": "...",
                "expectedMove": "+3.5%",
                "riskRewardRatio": 1.5
            }
        """
        global _groq_rate_limited_until, _ai_suggestions_cache, _ai_suggestions_cache_expiry
        import time

        try:
            # Check cache first
            cache_key = f"{symbol}:{direction.value}"
            now = time.time()

            if cache_key in _ai_suggestions_cache and cache_key in _ai_suggestions_cache_expiry:
                if now < _ai_suggestions_cache_expiry[cache_key]:
                    logger.debug(f"📦 Using cached AI suggestion for {symbol}")
                    return _ai_suggestions_cache[cache_key]

            logger.info(f"🤖 Generating trade levels for {symbol} @ ₹{current_price}")

            # Check if Groq is rate limited - use fallback directly
            if now < _groq_rate_limited_until:
                wait_time = int(_groq_rate_limited_until - now)
                logger.debug(f"⏳ Groq rate limited, using rule-based fallback (wait {wait_time}s)")
                levels = self._fallback_suggest_levels(
                    symbol, current_price, direction, news_context,
                    execution_config, price_data
                )
            elif self.ai_client:
                levels = await self._ai_suggest_levels(
                    symbol, current_price, direction, news_context,
                    execution_config, price_data
                )
            else:
                levels = self._fallback_suggest_levels(
                    symbol, current_price, direction, news_context,
                    execution_config, price_data
                )

            # Cache the result
            _ai_suggestions_cache[cache_key] = levels
            _ai_suggestions_cache_expiry[cache_key] = now + AI_CACHE_TTL
            
            logger.info(
                f"✅ Levels generated: Entry=₹{levels['entryPrice']}, "
                f"SL=₹{levels['stopLoss']}, T1=₹{levels['target1']}, "
                f"Confidence={levels['confidence']}%"
            )
            
            return levels
            
        except Exception as e:
            logger.error(f"❌ Error suggesting levels: {e}")
            # Return fallback levels
            return self._fallback_suggest_levels(
                symbol, current_price, direction, news_context,
                execution_config, price_data
            )
    
    async def _ai_suggest_levels(
        self,
        symbol: str,
        current_price: float,
        direction: TradeDirection,
        news_context: List[Dict],
        execution_config: ExecutionConfig,
        price_data: Optional[Dict]
    ) -> Dict:
        """Use AI (Groq or Gemini) to suggest levels"""

        # Prepare news summary
        news_summary = self._prepare_news_summary(news_context)

        # Prepare price data summary
        price_summary = self._prepare_price_summary(current_price, price_data)

        # Build prompt
        prompt = f"""
Stock: {symbol}
Direction: {direction.value}
Current Price: ₹{current_price}

{price_summary}

News Context:
{news_summary}

Strategy Configuration:
- Stop Loss: {execution_config.stopLossPercent}%
- Take Profit: {execution_config.takeProfitPercent}%
- Use Multiple Targets: {execution_config.useMultipleTargets}
- Exit at EOD: {execution_config.exitAtEOD}

{get_trade_levels_prompt()}
"""

        try:
            response_text = ""

            if self.ai_provider == "groq":
                # Call Groq API
                response = await asyncio.to_thread(
                    self.ai_client.chat.completions.create,
                    model=config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert stock trading analyst. Always respond with valid JSON only, no markdown."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1024
                )
                response_text = response.choices[0].message.content.strip()
            else:
                # Call Gemini API
                response = await asyncio.to_thread(
                    self.ai_client.generate_content,
                    prompt
                )
                response_text = response.text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            levels = json.loads(response_text)

            # Validate levels
            levels = self._validate_levels(levels, current_price, direction, execution_config)

            return levels

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            return self._fallback_suggest_levels(
                symbol, current_price, direction, news_context,
                execution_config, price_data
            )
        except Exception as e:
            global _groq_rate_limited_until
            error_str = str(e)

            # Check if rate limited (429 error)
            if '429' in error_str or 'rate_limit' in error_str.lower():
                # Set backoff time based on error message or default to 10 minutes
                import re
                import time
                match = re.search(r'try again in (\d+)m', error_str)
                if match:
                    backoff_minutes = int(match.group(1)) + 1  # Add 1 minute buffer
                else:
                    backoff_minutes = 10

                _groq_rate_limited_until = time.time() + (backoff_minutes * 60)
                logger.warning(f"⏳ Groq rate limited - will use fallback for {backoff_minutes} minutes")
            else:
                logger.error(f"❌ Error calling {self.ai_provider} API: {e}")

            return self._fallback_suggest_levels(
                symbol, current_price, direction, news_context,
                execution_config, price_data
            )
    
    def _fallback_suggest_levels(
        self,
        symbol: str,
        current_price: float,
        direction: TradeDirection,
        news_context: List[Dict],
        execution_config: ExecutionConfig,
        price_data: Optional[Dict]
    ) -> Dict:
        """Rule-based fallback for suggesting levels"""
        
        logger.info(f"📊 Using rule-based levels for {symbol}")
        
        # Calculate levels based on percentages
        if direction == TradeDirection.BUY:
            entry_price = current_price
            stop_loss = current_price * (1 - execution_config.stopLossPercent / 100)
            target1 = current_price * (1 + execution_config.takeProfitPercent / 100)
            
            # Target 2 is 1.5x the target 1 move
            if execution_config.useMultipleTargets:
                target2 = current_price * (1 + execution_config.takeProfitPercent * 1.5 / 100)
            else:
                target2 = target1
        else:
            # SELL direction
            entry_price = current_price
            stop_loss = current_price * (1 + execution_config.stopLossPercent / 100)
            target1 = current_price * (1 - execution_config.takeProfitPercent / 100)
            
            if execution_config.useMultipleTargets:
                target2 = current_price * (1 - execution_config.takeProfitPercent * 1.5 / 100)
            else:
                target2 = target1
        
        # Calculate risk-reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(target1 - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        # Calculate expected move
        expected_move_pct = ((target1 - entry_price) / entry_price) * 100
        expected_move = f"{expected_move_pct:+.1f}%"
        
        # Determine confidence based on news
        confidence = self._calculate_confidence(news_context)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(symbol, news_context, direction)
        
        return {
            'entryPrice': round(entry_price, 2),
            'stopLoss': round(stop_loss, 2),
            'target1': round(target1, 2),
            'target2': round(target2, 2),
            'confidence': confidence,
            'reasoning': reasoning,
            'expectedMove': expected_move,
            'riskRewardRatio': round(risk_reward_ratio, 2)
        }
    
    def _validate_levels(
        self,
        levels: Dict,
        current_price: float,
        direction: TradeDirection,
        execution_config: ExecutionConfig
    ) -> Dict:
        """Validate and adjust AI-suggested levels"""
        
        # Ensure all required fields exist
        required_fields = ['entryPrice', 'stopLoss', 'target1', 'target2', 'confidence', 'reasoning']
        for field in required_fields:
            if field not in levels:
                logger.warning(f"⚠️ Missing field in AI response: {field}")
                # Use fallback for missing fields
                if field == 'confidence':
                    levels[field] = 70
                elif field == 'reasoning':
                    levels[field] = "AI-suggested levels"
        
        # Validate price levels for BUY
        if direction == TradeDirection.BUY:
            # Stop loss should be below entry
            if levels['stopLoss'] >= levels['entryPrice']:
                levels['stopLoss'] = levels['entryPrice'] * (1 - execution_config.stopLossPercent / 100)
            
            # Targets should be above entry
            if levels['target1'] <= levels['entryPrice']:
                levels['target1'] = levels['entryPrice'] * (1 + execution_config.takeProfitPercent / 100)
            
            if levels['target2'] <= levels['target1']:
                levels['target2'] = levels['target1'] * 1.02  # 2% above target1
        
        # Validate price levels for SELL
        else:
            # Stop loss should be above entry
            if levels['stopLoss'] <= levels['entryPrice']:
                levels['stopLoss'] = levels['entryPrice'] * (1 + execution_config.stopLossPercent / 100)
            
            # Targets should be below entry
            if levels['target1'] >= levels['entryPrice']:
                levels['target1'] = levels['entryPrice'] * (1 - execution_config.takeProfitPercent / 100)
            
            if levels['target2'] >= levels['target1']:
                levels['target2'] = levels['target1'] * 0.98  # 2% below target1
        
        # Ensure confidence is 0-100
        levels['confidence'] = max(0, min(100, levels.get('confidence', 70)))
        
        return levels
    
    def _prepare_news_summary(self, news_context: List[Dict]) -> str:
        """Prepare news summary for AI prompt"""
        if not news_context:
            return "No recent news available."
        
        summary_parts = []
        for i, news in enumerate(news_context[:3], 1):  # Top 3 news
            ai_analysis = news.get('aiAnalysis', {})
            title = news.get('title', 'Unknown')
            impact = ai_analysis.get('impact', 'UNKNOWN')
            sentiment = ai_analysis.get('sentiment', 'NEUTRAL')
            analysis = ai_analysis.get('analysis', '')
            
            summary_parts.append(
                f"{i}. {title}\n"
                f"   Impact: {impact}, Sentiment: {sentiment}\n"
                f"   Analysis: {analysis}"
            )
        
        return "\n\n".join(summary_parts)
    
    def _prepare_price_summary(self, current_price: float, price_data: Optional[Dict]) -> str:
        """Prepare price data summary"""
        if not price_data:
            return f"Current Price: ₹{current_price}"
        
        parts = [f"Current Price: ₹{current_price}"]
        
        if 'high' in price_data:
            parts.append(f"Day High: ₹{price_data['high']}")
        if 'low' in price_data:
            parts.append(f"Day Low: ₹{price_data['low']}")
        if 'support' in price_data:
            parts.append(f"Support: ₹{price_data['support']}")
        if 'resistance' in price_data:
            parts.append(f"Resistance: ₹{price_data['resistance']}")
        
        return "\n".join(parts)
    
    def _calculate_confidence(self, news_context: List[Dict]) -> int:
        """Calculate confidence based on news quality"""
        if not news_context:
            return 50
        
        # Average relevance from news
        relevances = [
            n.get('aiAnalysis', {}).get('relevance', 50)
            for n in news_context
        ]
        
        avg_relevance = sum(relevances) / len(relevances) if relevances else 50
        
        # Boost confidence if multiple high-impact news
        high_impact_count = sum(
            1 for n in news_context
            if n.get('aiAnalysis', {}).get('impact') == 'HIGH'
        )
        
        confidence = avg_relevance
        if high_impact_count >= 2:
            confidence = min(100, confidence + 10)
        
        return int(confidence)
    
    def _generate_reasoning(
        self,
        symbol: str,
        news_context: List[Dict],
        direction: TradeDirection
    ) -> str:
        """Generate reasoning for the trade"""
        if not news_context:
            return f"{direction.value} {symbol} based on strategy criteria"
        
        top_news = news_context[0]
        ai_analysis = top_news.get('aiAnalysis', {})
        
        impact = ai_analysis.get('impact', 'MEDIUM')
        sentiment = ai_analysis.get('sentiment', 'NEUTRAL')
        analysis = ai_analysis.get('analysis', '')
        
        reasoning = f"{impact} impact {sentiment.lower()} news. "
        
        if analysis:
            # Add first sentence of analysis
            first_sentence = analysis.split('.')[0]
            reasoning += first_sentence + "."
        
        return reasoning

