"""
AI Insight Provider - Stage 2 of the 3-stage pipeline.
Generates structured trade plans from screened candidates.

From PLAN_OF_ACTION.md:
- Takes screener output (top 10 candidates)
- Generates trade plans with entry/SL/targets
- Calculates R:R ratios
- Provides confidence scores
- Validates plans for execution
"""
import json
import asyncio
from typing import Dict, Optional, List, Literal
from datetime import datetime
import time
from loguru import logger

from config import get_config
from models.screener import ScreenerCandidate, ScreenerOutput
from models.trade_plan import TradePlan, TradePlanLevels, TradePlanRationale, TradePlanOutput

config = get_config()

# Rate limiting and caching
_rate_limited_until = 0
_trade_plan_cache: Dict[str, tuple] = {}  # symbol -> (plan, timestamp)
CACHE_TTL = 300  # 5 minutes


class AIInsightProvider:
    """
    AI Insight Provider implementing Stage 2 of the pipeline.
    
    Features:
    - Structured trade plan generation
    - Multiple LLM provider support (Gemini primary, Groq batch, Claude fallback)
    - R:R calculation and validation
    - Confidence scoring
    - Retry logic with exponential backoff
    - Rule-based fallback analysis
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    
    def __init__(self):
        self.ai_client = None
        self.ai_provider = config.AI_PROVIDER.lower()
        self._setup_ai_client()
        logger.info(f"🤖 AI Insight Provider initialized with provider: {self.ai_provider}")
    
    def _setup_ai_client(self):
        """Setup AI client based on configured provider."""
        # Use the configured AI_PROVIDER first
        if self.ai_provider == "groq" and config.GROQ_API_KEY:
            self._setup_groq()
            if self.ai_client:
                return

        if self.ai_provider == "gemini" and config.GEMINI_API_KEY:
            self._setup_gemini()
            if self.ai_client:
                return

        # Fallback: try any available provider
        if config.GROQ_API_KEY and not self.ai_client:
            self._setup_groq()
        if config.GEMINI_API_KEY and not self.ai_client:
            self._setup_gemini()
    
    def _setup_gemini(self):
        """Setup Gemini AI client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.ai_client = genai.GenerativeModel(config.GEMINI_MODEL)
            self.ai_provider = "gemini"
            logger.info(f"✅ Gemini AI configured: {config.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"❌ Error setting up Gemini: {e}")
    
    def _setup_groq(self):
        """Setup Groq AI client."""
        try:
            from groq import Groq
            self.ai_client = Groq(api_key=config.GROQ_API_KEY)
            self.ai_provider = "groq"
            logger.info(f"✅ Groq AI configured: {config.GROQ_MODEL}")
        except Exception as e:
            logger.error(f"❌ Error setting up Groq: {e}")
    
    async def generate_trade_plans(self, screener_output: ScreenerOutput) -> TradePlanOutput:
        """
        Generate trade plans for all screened candidates.
        
        Args:
            screener_output: Output from Stage 1 (Screener)
            
        Returns:
            TradePlanOutput with validated trade plans
        """
        plans: List[TradePlan] = []
        
        for candidate in screener_output.candidates:
            try:
                plan = await self.generate_single_plan(candidate, screener_output.market_context)
                if plan:
                    # Validate for execution
                    plan.validate_for_execution(
                        min_rr=config.MIN_RISK_REWARD_RATIO,
                        min_confidence=config.AI_CONFIDENCE_THRESHOLD
                    )
                    plans.append(plan)
            except Exception as e:
                logger.error(f"Error generating plan for {candidate.symbol}: {e}")
        
        # Sort by confidence
        plans.sort(key=lambda x: x.confidence, reverse=True)
        
        executable_count = sum(1 for p in plans if p.is_executable)
        
        logger.info(f"📊 Generated {len(plans)} trade plans, {executable_count} executable")
        
        return TradePlanOutput(
            timestamp=datetime.now(),
            plans=plans,
            executable_count=executable_count,
            total_count=len(plans)
        )
    
    async def generate_single_plan(self, candidate: ScreenerCandidate, 
                                    market_context=None) -> Optional[TradePlan]:
        """Generate a trade plan for a single candidate."""
        global _rate_limited_until, _trade_plan_cache
        
        # Check cache
        cache_key = candidate.symbol
        if cache_key in _trade_plan_cache:
            plan, timestamp = _trade_plan_cache[cache_key]
            if (time.time() - timestamp) < CACHE_TTL:
                logger.debug(f"📦 Using cached plan for {candidate.symbol}")
                return plan
        
        # Check rate limiting
        if time.time() < _rate_limited_until:
            logger.debug(f"⏳ Rate limited, using rule-based plan for {candidate.symbol}")
            return self._generate_rule_based_plan(candidate)
        
        # Try AI generation with retries
        for attempt in range(self.MAX_RETRIES):
            try:
                if self.ai_client:
                    plan = await self._generate_ai_plan(candidate, market_context)
                else:
                    plan = self._generate_rule_based_plan(candidate)
                
                # Cache the result
                _trade_plan_cache[cache_key] = (plan, time.time())
                return plan
                
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    _rate_limited_until = time.time() + 600  # 10 min backoff
                    logger.warning(f"⏳ Rate limited, using fallback")
                    return self._generate_rule_based_plan(candidate)
                
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"Failed after {self.MAX_RETRIES} attempts: {e}")
                    return self._generate_rule_based_plan(candidate)

        return None

    async def _generate_ai_plan(self, candidate: ScreenerCandidate,
                                 market_context=None) -> TradePlan:
        """Generate trade plan using AI."""
        prompt = self._build_prompt(candidate, market_context)

        try:
            if self.ai_provider == "gemini":
                response = await asyncio.to_thread(
                    self.ai_client.generate_content,
                    prompt
                )
                response_text = response.text.strip()
            else:  # groq
                response = await asyncio.to_thread(
                    self.ai_client.chat.completions.create,
                    model=config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1024
                )
                response_text = response.choices[0].message.content.strip()

            # Parse JSON response
            plan_data = self._parse_ai_response(response_text)
            return self._create_trade_plan(candidate, plan_data)

        except Exception as e:
            logger.error(f"AI plan generation failed: {e}")
            raise

    def _get_system_prompt(self) -> str:
        """Get system prompt for trade plan generation."""
        return """You are an expert intraday stock trading analyst for the Indian market (NSE).
Your task is to analyze stock candidates and generate precise trade plans.

ALWAYS respond with valid JSON only, no markdown or explanations.

Output format:
{
    "direction": "BUY" or "SELL",
    "confidence": 0-100,
    "entry": price,
    "stop_loss": price,
    "target_1": price (1.5R minimum),
    "target_2": price (2R),
    "setup_type": "breakout/pullback/reversal/momentum",
    "key_levels": ["level1", "level2"],
    "catalysts": ["catalyst1"],
    "risks": ["risk1"],
    "summary": "Brief trade thesis"
}

Rules:
1. R:R ratio must be >= 1.5
2. Stop loss within 2% of entry for intraday
3. Consider market context (bullish/bearish/sideways)
4. Factor in VWAP, pivot levels, and ATR for levels
5. Higher confidence for setups with multiple confirmations"""

    def _build_prompt(self, candidate: ScreenerCandidate, market_context=None) -> str:
        """Build prompt for AI trade plan generation."""
        pa = candidate.price_action
        tech = candidate.technicals
        levels = candidate.levels
        liq = candidate.liquidity

        prompt = f"""Analyze this stock for an intraday trade:

STOCK: {candidate.symbol}
MARKET CAP: ₹{candidate.market_cap_cr:,.0f} Cr

PRICE ACTION:
- Last Price: ₹{pa.last_price}
- Today's Range: ₹{pa.today_low} - ₹{pa.today_high}
- Change: {pa.today_pct_change:+.2f}%
- Gap: {pa.gap_pct:+.2f}%
- VWAP: ₹{pa.vwap} (Distance: {pa.vwap_distance_pct:+.2f}%)

TECHNICALS:
- RSI: {tech.rsi:.1f}
- ATR: ₹{tech.atr} ({tech.atr_pct:.2f}%)
- Trend: {tech.trend_label}
- Above 20 EMA: {tech.above_20ema}
- Above 50 EMA: {tech.above_50ema}

PIVOT LEVELS:
- R2: ₹{levels.r2}, R1: ₹{levels.r1}
- PP: ₹{levels.pivot_pp}
- S1: ₹{levels.s1}, S2: ₹{levels.s2}

LIQUIDITY:
- RVOL: {liq.rvol:.2f}x
- Turnover: ₹{liq.today_turnover_cr:.1f} Cr

SCREENING SCORE: {candidate.score:.1f}/100
"""

        if market_context:
            prompt += f"""
MARKET CONTEXT:
- NIFTY: {market_context.nifty_trend} ({market_context.nifty_change_pct:+.2f}%)
- VIX: {market_context.vix}
- Breadth: {market_context.market_breadth}
"""

        if candidate.news.has_fresh_news:
            prompt += f"""
NEWS:
- Sentiment: {candidate.news.sentiment}
- Category: {candidate.news.category or 'N/A'}
- Summary: {candidate.news.summary or 'N/A'}
"""

        prompt += "\nGenerate a trade plan with entry, stop loss, and targets. Respond with JSON only."
        return prompt

    def _parse_ai_response(self, response_text: str) -> Dict:
        """Parse AI response and extract JSON."""
        # Handle markdown code blocks
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()

        return json.loads(response_text)

    def _create_trade_plan(self, candidate: ScreenerCandidate, plan_data: Dict) -> TradePlan:
        """Create TradePlan from parsed AI response."""
        entry = float(plan_data.get('entry', candidate.price_action.last_price))
        stop_loss = float(plan_data.get('stop_loss', entry * 0.98))
        target_1 = float(plan_data.get('target_1', entry * 1.03))
        target_2 = float(plan_data.get('target_2', entry * 1.04))

        risk_per_share = abs(entry - stop_loss)
        reward_per_share = abs(target_1 - entry)
        rr_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else 0

        levels = TradePlanLevels(
            entry=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            target_1=round(target_1, 2),
            target_2=round(target_2, 2),
            risk_per_share=round(risk_per_share, 2),
            reward_per_share=round(reward_per_share, 2),
            risk_reward_ratio=round(rr_ratio, 2)
        )

        rationale = TradePlanRationale(
            setup_type=plan_data.get('setup_type', 'momentum'),
            key_levels=plan_data.get('key_levels', []),
            catalysts=plan_data.get('catalysts', []),
            risks=plan_data.get('risks', []),
            summary=plan_data.get('summary', 'AI-generated trade plan')
        )

        return TradePlan(
            symbol=candidate.symbol,
            direction=plan_data.get('direction', 'BUY'),
            confidence=float(plan_data.get('confidence', 70)),
            levels=levels,
            rationale=rationale
        )

    def _generate_rule_based_plan(self, candidate: ScreenerCandidate) -> TradePlan:
        """Generate trade plan using rule-based analysis (fallback)."""
        pa = candidate.price_action
        tech = candidate.technicals
        levels = candidate.levels

        # Determine direction based on technicals
        if tech.trend_label == "uptrend" and pa.vwap_distance_pct > 0:
            direction = "BUY"
        elif tech.trend_label == "downtrend" and pa.vwap_distance_pct < 0:
            direction = "SELL"
        elif tech.rsi < 40:
            direction = "BUY"  # Oversold bounce
        elif tech.rsi > 60:
            direction = "SELL"  # Overbought fade
        else:
            direction = "BUY" if pa.today_pct_change > 0 else "SELL"

        # Calculate levels based on ATR
        atr = tech.atr
        entry = pa.last_price

        if direction == "BUY":
            stop_loss = max(entry - (1.5 * atr), levels.s1)
            target_1 = min(entry + (2.0 * atr), levels.r1)
            target_2 = min(entry + (3.0 * atr), levels.r2)
        else:
            stop_loss = min(entry + (1.5 * atr), levels.r1)
            target_1 = max(entry - (2.0 * atr), levels.s1)
            target_2 = max(entry - (3.0 * atr), levels.s2)

        risk_per_share = abs(entry - stop_loss)
        reward_per_share = abs(target_1 - entry)
        rr_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else 0

        # Calculate confidence based on multiple factors
        confidence = 50.0
        if tech.trend_label == "uptrend" and direction == "BUY":
            confidence += 15
        elif tech.trend_label == "downtrend" and direction == "SELL":
            confidence += 15
        if candidate.liquidity.rvol >= 2.0:
            confidence += 10
        if 40 <= tech.rsi <= 60:
            confidence += 5
        if rr_ratio >= 1.5:
            confidence += 10
        if candidate.news.has_fresh_news and candidate.news.sentiment != "neutral":
            confidence += 10

        confidence = min(confidence, 95)

        plan_levels = TradePlanLevels(
            entry=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            target_1=round(target_1, 2),
            target_2=round(target_2, 2),
            risk_per_share=round(risk_per_share, 2),
            reward_per_share=round(reward_per_share, 2),
            risk_reward_ratio=round(rr_ratio, 2)
        )

        rationale = TradePlanRationale(
            setup_type="momentum" if abs(pa.today_pct_change) > 1 else "pullback",
            key_levels=[f"VWAP: ₹{pa.vwap}", f"PP: ₹{levels.pivot_pp}"],
            catalysts=["Technical setup"] + (["Fresh news"] if candidate.news.has_fresh_news else []),
            risks=["Intraday volatility", "Market reversal"],
            summary=f"{direction} {candidate.symbol} based on {tech.trend_label} with {rr_ratio:.1f}R setup"
        )

        logger.info(f"📊 Rule-based plan for {candidate.symbol}: {direction} @ ₹{entry}, R:R={rr_ratio:.2f}")

        return TradePlan(
            symbol=candidate.symbol,
            direction=direction,
            confidence=confidence,
            levels=plan_levels,
            rationale=rationale
        )

