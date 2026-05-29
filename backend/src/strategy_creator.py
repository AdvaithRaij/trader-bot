"""
LLM Strategy Creator

Converts natural language strategy descriptions into executable strategy configurations.
This is the core feature that allows users to describe trading strategies in plain English
and have the AI convert them into actionable trading rules.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
from loguru import logger

from config import get_config
from models.strategy import (
    StrategyModel, StockPickingConfig, ExecutionConfig,
    StockPickingType, ExecutionType, StrategyStatus
)

config = get_config()


STRATEGY_CREATION_PROMPT = """You are an expert trading strategy designer. Convert the user's natural language description into a structured trading strategy configuration.

The user will describe their trading strategy in plain English. You need to extract:

1. **Stock Picking Logic** - How to select stocks:
   - NEWS_BASED: Based on news sentiment and impact
   - TECHNICAL: Based on technical indicators (RSI, MACD, etc.)
   - MOMENTUM: Based on price/volume momentum
   - AI_RECOMMENDED: Let AI pick stocks

2. **Execution Logic** - How to enter/exit trades:
   - BREAKOUT: Enter on price breakouts
   - MEAN_REVERSION: Enter on price reversals
   - SCALPING: Quick in-and-out trades
   - AI_ASSISTED: Let AI determine entry/exit

3. **Risk Parameters**:
   - Stop loss percentage (default 2%)
   - Take profit / target percentages
   - Position sizing rules
   - Maximum stocks to trade

4. **Filters**:
   - News impact level (HIGH, MEDIUM, LOW)
   - Sentiment (POSITIVE, NEGATIVE, NEUTRAL)
   - Relevance score threshold
   - Timeframe (IMMEDIATE, SHORT_TERM, MEDIUM_TERM, LONG_TERM)

USER'S STRATEGY DESCRIPTION:
{user_description}

Respond with a JSON object in this exact format:
{{
    "name": "Strategy Name",
    "description": "Brief description of the strategy",
    "stockPicking": {{
        "type": "NEWS_BASED|TECHNICAL|MOMENTUM|AI_RECOMMENDED",
        "newsFilters": {{
            "impact": "HIGH|MEDIUM|LOW" or ["HIGH", "MEDIUM"],
            "sentiment": "POSITIVE|NEGATIVE|NEUTRAL" or ["POSITIVE", "NEUTRAL"],
            "relevance": ">=80" or number,
            "timeframe": "IMMEDIATE|SHORT_TERM|MEDIUM_TERM|LONG_TERM" or array
        }},
        "technicalFilters": {{
            "rsi": {{"min": 30, "max": 70}},
            "macd": "bullish_crossover|bearish_crossover",
            "volume": "above_average|below_average"
        }},
        "maxStocks": 5,
        "allowedSymbols": null or ["RELIANCE", "TCS"],
        "excludedSymbols": []
    }},
    "execution": {{
        "type": "BREAKOUT|MEAN_REVERSION|SCALPING|AI_ASSISTED",
        "entryCondition": "description of entry condition",
        "stopLossPercent": 2.0,
        "takeProfitPercent": 5.0,
        "useTrailingStop": true|false,
        "trailingStopPercent": 1.5,
        "useMultipleTargets": true|false,
        "target1Percent": 3.0,
        "target2Percent": 5.0,
        "exitAtEOD": true|false,
        "eodExitTime": "15:15",
        "useAILevels": true|false
    }},
    "riskManagement": {{
        "maxPositionPercent": 20,
        "maxDailyLoss": 5,
        "maxDrawdown": 10
    }}
}}

Only respond with the JSON object, no additional text."""


class StrategyCreator:
    """
    Creates trading strategies from natural language descriptions using LLM.
    """

    def __init__(self):
        self.ai_client = None
        self.ai_provider = config.AI_PROVIDER.lower()
        self._setup_ai_client()
        logger.info(f"🧠 Strategy Creator initialized with provider: {self.ai_provider}")

    def _setup_ai_client(self):
        """Setup AI client based on configured provider"""
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
            logger.info(f"✅ Groq configured for strategy creation: {config.GROQ_MODEL}")
        except ImportError:
            logger.warning("⚠️ groq package not installed")
        except Exception as e:
            logger.error(f"❌ Error setting up Groq: {e}")

    def _setup_gemini(self):
        """Setup Gemini AI client"""
        try:
            import google.generativeai as genai

            if not config.GEMINI_API_KEY:
                logger.warning("⚠️ GEMINI_API_KEY not set")
                return

            genai.configure(api_key=config.GEMINI_API_KEY)
            self.ai_client = genai.GenerativeModel(config.GEMINI_MODEL)
            self.ai_provider = "gemini"
            logger.info(f"✅ Gemini configured for strategy creation: {config.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"❌ Error setting up Gemini: {e}")

    def _call_ai(self, prompt: str) -> str:
        """Call the AI provider and return the response text."""
        if self.ai_provider == "groq":
            response = self.ai_client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert trading strategy designer. Always respond with valid JSON only, no markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2048
            )
            return response.choices[0].message.content.strip()
        else:
            response = self.ai_client.generate_content(prompt)
            return response.text.strip()
    
    async def create_strategy_from_description(
        self,
        description: str,
        strategy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert a natural language description into a strategy configuration.

        Args:
            description: User's natural language strategy description
            strategy_id: Optional custom strategy ID

        Returns:
            Dictionary with strategy configuration or error
        """
        try:
            logger.info(f"🧠 Creating strategy from description: {description[:100]}...")

            if not self.ai_client:
                return {"error": f"AI not configured. Please set GROQ_API_KEY or GEMINI_API_KEY."}

            # Generate strategy using LLM
            prompt = STRATEGY_CREATION_PROMPT.format(user_description=description)

            response_text = await asyncio.to_thread(self._call_ai, prompt)

            # Clean up response (remove markdown code blocks if present)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            # Parse JSON response
            strategy_config = json.loads(response_text.strip())
            
            # Generate strategy ID if not provided
            if not strategy_id:
                import hashlib
                hash_input = f"{strategy_config['name']}_{datetime.now().isoformat()}"
                strategy_id = f"custom_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
            
            # Build the strategy model
            strategy_data = self._build_strategy_model(strategy_id, strategy_config)
            
            logger.info(f"✅ Strategy created: {strategy_data['name']} ({strategy_id})")
            
            return {
                "success": True,
                "strategy": strategy_data,
                "originalDescription": description
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response: {e}")
            return {"error": f"Failed to parse strategy configuration: {e}"}
        except Exception as e:
            logger.error(f"❌ Error creating strategy: {e}")
            return {"error": str(e)}

    def _build_strategy_model(self, strategy_id: str, config: Dict) -> Dict:
        """Build a strategy model dictionary from parsed config"""

        # Parse stock picking config
        stock_picking = config.get("stockPicking", {})
        picking_type = stock_picking.get("type", "NEWS_BASED")

        stock_picking_config = {
            "type": picking_type,
            "newsFilters": stock_picking.get("newsFilters"),
            "technicalFilters": stock_picking.get("technicalFilters"),
            "allowedSymbols": stock_picking.get("allowedSymbols"),
            "excludedSymbols": stock_picking.get("excludedSymbols", []),
            "maxStocks": stock_picking.get("maxStocks", 5)
        }

        # Parse execution config
        execution = config.get("execution", {})
        execution_type = execution.get("type", "BREAKOUT")

        execution_config = {
            "type": execution_type,
            "entryCondition": execution.get("entryCondition", "AI determined"),
            "stopLossPercent": execution.get("stopLossPercent", 2.0),
            "takeProfitPercent": execution.get("takeProfitPercent", 5.0),
            "useTrailingStop": execution.get("useTrailingStop", False),
            "trailingStopPercent": execution.get("trailingStopPercent", 1.5),
            "useMultipleTargets": execution.get("useMultipleTargets", True),
            "target1Percent": execution.get("target1Percent", 3.0),
            "target2Percent": execution.get("target2Percent", 5.0),
            "exitAtEOD": execution.get("exitAtEOD", True),
            "eodExitTime": execution.get("eodExitTime", "15:15"),
            "useAILevels": execution.get("useAILevels", True)
        }

        # Parse risk management
        risk = config.get("riskManagement", {})
        risk_config = {
            "maxPositionPercent": risk.get("maxPositionPercent", 20),
            "maxDailyLoss": risk.get("maxDailyLoss", 5),
            "maxDrawdown": risk.get("maxDrawdown", 10)
        }

        return {
            "strategyId": strategy_id,
            "name": config.get("name", "Custom Strategy"),
            "description": config.get("description", "AI-generated strategy"),
            "version": "1.0",
            "status": "PAUSED",  # Start paused for safety
            "stockPicking": stock_picking_config,
            "execution": execution_config,
            "riskManagement": risk_config,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            "createdBy": "ai_creator"
        }

    async def refine_strategy(
        self,
        strategy_id: str,
        refinement_request: str
    ) -> Dict[str, Any]:
        """
        Refine an existing strategy based on user feedback.

        Args:
            strategy_id: ID of strategy to refine
            refinement_request: User's refinement request

        Returns:
            Updated strategy configuration
        """
        try:
            from strategy_manager import StrategyManager

            manager = StrategyManager()
            existing = await manager.get_strategy(strategy_id)

            if not existing:
                return {"error": f"Strategy {strategy_id} not found"}

            # Create refinement prompt
            refinement_prompt = f"""You are refining an existing trading strategy.

CURRENT STRATEGY:
{json.dumps(existing.model_dump(), indent=2, default=str)}

USER'S REFINEMENT REQUEST:
{refinement_request}

Apply the user's requested changes to the strategy and return the updated configuration.
Only modify the parts that the user specifically requested to change.
Respond with the complete updated JSON configuration in the same format as the original."""

            if not self.ai_client:
                return {"error": "AI not configured"}

            response_text = await asyncio.to_thread(self._call_ai, refinement_prompt)

            # Clean up response
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            updated_config = json.loads(response_text.strip())

            logger.info(f"✅ Strategy refined: {strategy_id}")

            return {
                "success": True,
                "strategy": updated_config,
                "refinementApplied": refinement_request
            }

        except Exception as e:
            logger.error(f"❌ Error refining strategy: {e}")
            return {"error": str(e)}


# Global instance
strategy_creator = StrategyCreator()
