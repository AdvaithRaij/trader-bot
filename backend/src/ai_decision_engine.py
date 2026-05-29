"""
AI Decision Engine for Trading Bot.
Integrates OpenAI/Claude/Gemini to make informed trading decisions based on market data and sentiment.
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from loguru import logger

from config import get_config
from prompt_loader import get_trading_decision_prompt

config = get_config()


def get_ai_client():
    """Get the appropriate AI client based on configuration."""
    provider = config.AI_PROVIDER.lower()

    if provider == "gemini" and config.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            # Use gemini-2.5-flash for faster responses and better quota management
            return genai.GenerativeModel('gemini-2.5-flash'), "gemini"
        except ImportError:
            logger.warning("google-generativeai not installed, falling back to mock mode")
            return None, "mock"

    elif provider == "openai" and config.OPENAI_API_KEY:
        try:
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=config.OPENAI_API_KEY), "openai"
        except ImportError:
            logger.warning("openai not installed, falling back to mock mode")
            return None, "mock"

    elif provider == "anthropic" and config.ANTHROPIC_API_KEY:
        try:
            from anthropic import AsyncAnthropic
            return AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY), "anthropic"
        except ImportError:
            logger.warning("anthropic not installed, falling back to mock mode")
            return None, "mock"

    logger.info("No AI provider configured or API key missing, using mock mode")
    return None, "mock"


class AIDecisionEngine:
    """
    AI-powered decision engine for trading decisions.
    Uses LLMs to analyze market data, sentiment, and technical indicators.
    """
    
    def __init__(self):
        self.config = config
        
        # Decision thresholds
        self.min_confidence = config.AI_CONFIDENCE_THRESHOLD
        self.min_risk_reward = config.MIN_RISK_REWARD_RATIO
        
        # Risk categories
        self.risk_levels = {
            'LOW': {'volatility_max': 2.0, 'rsi_range': (40, 60)},
            'MEDIUM': {'volatility_max': 4.0, 'rsi_range': (30, 70)},
            'HIGH': {'volatility_max': 10.0, 'rsi_range': (20, 80)}
        }
    
    def prepare_market_context(self, stock_data: Dict, sentiment_data: Dict) -> Dict:
        """
        Prepare comprehensive market context for AI analysis.
        
        Args:
            stock_data: Technical analysis data from screener
            sentiment_data: Sentiment analysis data
            
        Returns:
            Structured context for AI decision making
        """
        try:
            context = {
                'symbol': stock_data.get('symbol', 'UNKNOWN'),
                'timestamp': datetime.now().isoformat(),
                
                # Technical indicators
                'technical': {
                    'current_price': stock_data.get('current_price', 0),
                    'vwap': stock_data.get('vwap', 0),
                    'rsi': stock_data.get('rsi', 50),
                    'sma_20': stock_data.get('sma_20', 0),
                    'sma_50': stock_data.get('sma_50', 0),
                    'volume_ratio': stock_data.get('volume_ratio', 1),
                    'volatility_pct': stock_data.get('volatility_pct', 0),
                    'price_vs_vwap_pct': stock_data.get('price_vs_vwap_pct', 0),
                    'above_vwap': stock_data.get('above_vwap', False),
                    'price_change_pct': stock_data.get('price_change_pct', 0)
                },
                
                # Sentiment analysis
                'sentiment': {
                    'final_sentiment': sentiment_data.get('final_sentiment', 0),
                    'intraday_relevance': sentiment_data.get('intraday_relevance', 0),
                    'confidence': sentiment_data.get('confidence', 0),
                    'trade_signal': sentiment_data.get('trade_signal', 'NEUTRAL'),
                    'news_count': sentiment_data.get('news_count', 0),
                    'tweet_count': sentiment_data.get('tweet_count', 0)
                },
                
                # Market conditions
                'market': {
                    'trading_session': self.get_trading_session(),
                    'market_trend': self.assess_market_trend(stock_data),
                    'liquidity_score': self.calculate_liquidity_score(stock_data)
                }
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error preparing market context: {e}")
            return {}
    
    def get_trading_session(self) -> str:
        """Determine current trading session."""
        now = datetime.now()
        hour = now.hour
        
        if 9 <= hour < 11:
            return "OPENING"
        elif 11 <= hour < 14:
            return "MID_SESSION"
        elif 14 <= hour < 15:
            return "CLOSING"
        else:
            return "POST_MARKET"
    
    def assess_market_trend(self, stock_data: Dict) -> str:
        """Assess short-term market trend for the stock."""
        try:
            price_change = stock_data.get('price_change_pct', 0)
            above_vwap = stock_data.get('above_vwap', False)
            volume_ratio = stock_data.get('volume_ratio', 1)
            
            if price_change > 1 and above_vwap and volume_ratio > 1.5:
                return "STRONG_BULLISH"
            elif price_change > 0.5 and above_vwap:
                return "BULLISH"
            elif price_change < -1 and not above_vwap and volume_ratio > 1.5:
                return "STRONG_BEARISH"
            elif price_change < -0.5 and not above_vwap:
                return "BEARISH"
            else:
                return "SIDEWAYS"
                
        except Exception:
            return "UNKNOWN"
    
    def calculate_liquidity_score(self, stock_data: Dict) -> float:
        """Calculate liquidity score based on volume metrics."""
        try:
            volume_ratio = stock_data.get('volume_ratio', 1)
            current_volume = stock_data.get('current_volume', 0)
            
            # Normalize volume to 0-1 scale
            volume_score = min(volume_ratio / 3.0, 1.0)
            
            # Minimum volume threshold
            min_volume_score = 1.0 if current_volume > 100000 else 0.5
            
            return (volume_score + min_volume_score) / 2
            
        except Exception:
            return 0.5
    
    async def call_ai_for_decision(self, context: Dict) -> Dict:
        """
        Call AI service (GPT-4/Claude/Gemini) for trading decision.

        Args:
            context: Market context data

        Returns:
            AI trading decision with reasoning
        """
        if self.config.MOCK_AI:
            return self.mock_ai_decision(context)

        try:
            # Get AI client
            ai_client, provider = get_ai_client()

            if provider == "mock":
                logger.info("🤖 Using mock AI decision engine")
                return self.mock_ai_decision(context)

            # Build prompt
            prompt = self.build_ai_prompt(context)

            # Call appropriate AI service
            if provider == "gemini":
                return await self.call_gemini(ai_client, prompt, context)
            elif provider == "openai":
                return await self.call_openai(ai_client, prompt, context)
            elif provider == "anthropic":
                return await self.call_anthropic(ai_client, prompt, context)
            else:
                logger.warning(f"Unknown AI provider: {provider}, using mock decision")
                return self.mock_ai_decision(context)

        except Exception as e:
            logger.error(f"Error calling AI for decision: {e}")
            return {
                'decision': 'HOLD',
                'confidence': 0.0,
                'reasoning': f"Error in AI analysis: {e}",
                'entry_price': 0,
                'stop_loss': 0,
                'target_price': 0,
                'risk_reward_ratio': 0,
                'position_size': 0
            }

    async def call_gemini(self, model, prompt: str, context: Dict) -> Dict:
        """Call Google Gemini API for trading decision."""
        try:
            logger.info("🤖 Calling Gemini AI for trading decision")

            # Generate response
            response = model.generate_content(prompt)
            response_text = response.text

            # Try to parse JSON from response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                decision = json.loads(response_text)

                # Validate required fields
                required_fields = ['decision', 'confidence', 'reasoning', 'entry_price',
                                 'stop_loss', 'target_price', 'risk_reward_ratio', 'position_size']

                for field in required_fields:
                    if field not in decision:
                        logger.warning(f"Missing field {field} in Gemini response, using mock decision")
                        return self.mock_ai_decision(context)

                logger.info(f"✅ Gemini decision: {decision['decision']} (confidence: {decision['confidence']:.2f})")
                return decision

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.debug(f"Response text: {response_text}")
                return self.mock_ai_decision(context)

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return self.mock_ai_decision(context)

    async def call_openai(self, client, prompt: str, context: Dict) -> Dict:
        """Call OpenAI API for trading decision."""
        try:
            logger.info("🤖 Calling OpenAI for trading decision")

            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert intraday stock trader. Provide trading decisions in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            response_text = response.choices[0].message.content
            decision = json.loads(response_text)

            logger.info(f"✅ OpenAI decision: {decision['decision']} (confidence: {decision['confidence']:.2f})")
            return decision

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return self.mock_ai_decision(context)

    async def call_anthropic(self, client, prompt: str, context: Dict) -> Dict:
        """Call Anthropic Claude API for trading decision."""
        try:
            logger.info("🤖 Calling Claude for trading decision")

            response = await client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.content[0].text
            decision = json.loads(response_text)

            logger.info(f"✅ Claude decision: {decision['decision']} (confidence: {decision['confidence']:.2f})")
            return decision

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return self.mock_ai_decision(context)
    
    def build_ai_prompt(self, context: Dict) -> str:
        """Build structured prompt for AI analysis using centralized prompt loader."""
        symbol = context.get('symbol', 'UNKNOWN')

        # Use centralized prompt with all context variables
        prompt = get_trading_decision_prompt(
            symbol=symbol,
            current_price=f"{context['technical']['current_price']:.2f}",
            vwap=f"{context['technical']['vwap']:.2f}",
            rsi=f"{context['technical']['rsi']:.1f}",
            volume_ratio=f"{context['technical']['volume_ratio']:.2f}",
            volatility_pct=f"{context['technical']['volatility_pct']:.2f}",
            price_vs_vwap_pct=f"{context['technical']['price_vs_vwap_pct']:.2f}",
            above_vwap=context['technical']['above_vwap'],
            sentiment_score=f"{context['sentiment']['final_sentiment']:.2f}",
            intraday_relevance=f"{context['sentiment']['intraday_relevance']:.2f}",
            news_count=context['sentiment']['news_count'],
            sentiment_confidence=f"{context['sentiment'].get('confidence', 0.5):.2f}",
            current_time=datetime.now().strftime("%H:%M"),
            market_phase=context['market'].get('trading_session', 'UNKNOWN')
        )

        return prompt
    
    def mock_ai_decision(self, context: Dict) -> Dict:
        """
        Mock AI decision for testing purposes.
        
        Args:
            context: Market context data
            
        Returns:
            Mock trading decision
        """
        try:
            symbol = context.get('symbol', 'UNKNOWN')
            technical = context.get('technical', {})
            sentiment = context.get('sentiment', {})
            market = context.get('market', {})
            
            current_price = technical.get('current_price', 0)
            rsi = technical.get('rsi', 50)
            volume_ratio = technical.get('volume_ratio', 1)
            above_vwap = technical.get('above_vwap', False)
            sentiment_score = sentiment.get('final_sentiment', 0)
            intraday_relevance = sentiment.get('intraday_relevance', 0)
            
            # Simple decision logic
            bullish_signals = 0
            bearish_signals = 0
            
            # Technical signals
            if rsi < 40:  # Oversold
                bullish_signals += 1
            elif rsi > 70:  # Overbought
                bearish_signals += 1
            
            if above_vwap:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            if volume_ratio > 1.5:
                bullish_signals += 1
            
            # Sentiment signals
            if sentiment_score > 0.3:
                bullish_signals += 1
            elif sentiment_score < -0.3:
                bearish_signals += 1
            
            if intraday_relevance > 0.5:
                bullish_signals += 1
            
            # Make decision
            if bullish_signals >= 3 and current_price > 0:
                decision = "BUY"
                confidence = min(0.6 + (bullish_signals - 3) * 0.1, 0.9)
                entry_price = current_price
                stop_loss = current_price * 0.98  # 2% stop loss
                target_price = current_price * 1.04  # 4% target
                
            elif bearish_signals >= 3 and current_price > 0:
                decision = "SELL"
                confidence = min(0.6 + (bearish_signals - 3) * 0.1, 0.9)
                entry_price = current_price
                stop_loss = current_price * 1.02  # 2% stop loss
                target_price = current_price * 0.96  # 4% target
                
            else:
                decision = "HOLD"
                confidence = 0.3
                entry_price = current_price
                stop_loss = 0
                target_price = 0
            
            # Calculate risk-reward ratio
            if decision in ["BUY", "SELL"] and stop_loss != entry_price:
                risk = abs(entry_price - stop_loss)
                reward = abs(target_price - entry_price)
                risk_reward_ratio = reward / risk if risk > 0 else 0
            else:
                risk_reward_ratio = 0
            
            # Position sizing (percentage of capital)
            if decision == "HOLD" or confidence < self.min_confidence:
                position_size = 0
            else:
                position_size = min(confidence * 0.5, 0.3)  # Max 30% of capital
            
            reasoning = self.generate_reasoning(
                decision, bullish_signals, bearish_signals, 
                technical, sentiment, market
            )
            
            return {
                'decision': decision,
                'confidence': confidence,
                'reasoning': reasoning,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'target_price': target_price,
                'risk_reward_ratio': risk_reward_ratio,
                'position_size': position_size,
                'bullish_signals': bullish_signals,
                'bearish_signals': bearish_signals
            }
            
        except Exception as e:
            logger.error(f"Error in mock AI decision: {e}")
            return {
                'decision': 'HOLD',
                'confidence': 0.0,
                'reasoning': f"Error in analysis: {e}",
                'entry_price': 0,
                'stop_loss': 0,
                'target_price': 0,
                'risk_reward_ratio': 0,
                'position_size': 0
            }
    
    def generate_reasoning(self, decision: str, bullish_signals: int, 
                          bearish_signals: int, technical: Dict, 
                          sentiment: Dict, market: Dict) -> str:
        """Generate human-readable reasoning for the decision."""
        
        reasoning_parts = []
        
        # Technical analysis
        rsi = technical.get('rsi', 50)
        above_vwap = technical.get('above_vwap', False)
        volume_ratio = technical.get('volume_ratio', 1)
        
        if rsi < 40:
            reasoning_parts.append(f"RSI at {rsi:.1f} indicates oversold conditions")
        elif rsi > 70:
            reasoning_parts.append(f"RSI at {rsi:.1f} shows overbought levels")
        
        if above_vwap:
            reasoning_parts.append("Price trading above VWAP shows bullish bias")
        else:
            reasoning_parts.append("Price below VWAP indicates bearish pressure")
        
        if volume_ratio > 1.5:
            reasoning_parts.append(f"Volume {volume_ratio:.1f}x higher than average")
        
        # Sentiment analysis
        sentiment_score = sentiment.get('final_sentiment', 0)
        if sentiment_score > 0.3:
            reasoning_parts.append("Positive market sentiment detected")
        elif sentiment_score < -0.3:
            reasoning_parts.append("Negative sentiment in news and social media")
        
        # Market conditions
        trend = market.get('market_trend', 'UNKNOWN')
        if trend in ['STRONG_BULLISH', 'BULLISH']:
            reasoning_parts.append(f"Market showing {trend.lower()} trend")
        elif trend in ['STRONG_BEARISH', 'BEARISH']:
            reasoning_parts.append(f"Market exhibiting {trend.lower()} trend")
        
        # Decision summary
        if decision == "BUY":
            reasoning_parts.append(f"Total {bullish_signals} bullish signals support buy decision")
        elif decision == "SELL":
            reasoning_parts.append(f"Total {bearish_signals} bearish signals support sell decision")
        else:
            reasoning_parts.append("Mixed signals suggest holding position")
        
        return ". ".join(reasoning_parts) + "."
    
    def validate_decision(self, decision: Dict) -> Tuple[bool, str]:
        """
        Validate AI decision against risk parameters.
        
        Args:
            decision: AI decision dictionary
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            # Check confidence threshold
            if decision['confidence'] < self.min_confidence:
                return False, f"Confidence {decision['confidence']:.2f} below threshold {self.min_confidence}"
            
            # Check risk-reward ratio
            if decision['decision'] in ['BUY', 'SELL']:
                rr_ratio = decision.get('risk_reward_ratio', 0)
                if rr_ratio < self.min_risk_reward:
                    return False, f"Risk-reward ratio {rr_ratio:.2f} below minimum {self.min_risk_reward}"
            
            # Check position size
            position_size = decision.get('position_size', 0)
            if position_size > self.config.MAX_CAPITAL_PER_TRADE:
                return False, f"Position size {position_size:.2f} exceeds maximum {self.config.MAX_CAPITAL_PER_TRADE}"
            
            # Check stop loss and target validity
            if decision['decision'] == 'BUY':
                if decision['stop_loss'] >= decision['entry_price']:
                    return False, "Invalid stop loss for BUY order"
                if decision['target_price'] <= decision['entry_price']:
                    return False, "Invalid target price for BUY order"
            
            elif decision['decision'] == 'SELL':
                if decision['stop_loss'] <= decision['entry_price']:
                    return False, "Invalid stop loss for SELL order"
                if decision['target_price'] >= decision['entry_price']:
                    return False, "Invalid target price for SELL order"
            
            return True, "Decision passed all validation checks"
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    async def make_trading_decision(self, stock_data: Dict, sentiment_data: Dict) -> Dict:
        """
        Main function to make a trading decision.
        
        Args:
            stock_data: Technical analysis data
            sentiment_data: Sentiment analysis data
            
        Returns:
            Complete trading decision with validation
        """
        try:
            symbol = stock_data.get('symbol', 'UNKNOWN')
            logger.info(f"🤖 Making AI trading decision for {symbol}")
            
            # Prepare context
            context = self.prepare_market_context(stock_data, sentiment_data)
            
            # Get AI decision
            ai_decision = await self.call_ai_for_decision(context)
            
            # Validate decision
            is_valid, validation_message = self.validate_decision(ai_decision)
            
            # Compile final decision
            final_decision = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'ai_decision': ai_decision,
                'validation': {
                    'is_valid': is_valid,
                    'message': validation_message
                },
                'context': context,
                'final_action': ai_decision['decision'] if is_valid else 'HOLD',
                'should_trade': is_valid and ai_decision['decision'] in ['BUY', 'SELL']
            }
            
            if is_valid and ai_decision['decision'] in ['BUY', 'SELL']:
                logger.info(f"✅ {symbol}: {ai_decision['decision']} decision "
                           f"(Confidence: {ai_decision['confidence']:.2f}, "
                           f"R:R: {ai_decision['risk_reward_ratio']:.2f})")
            else:
                logger.info(f"❌ {symbol}: HOLD - {validation_message}")
            
            return final_decision
            
        except Exception as e:
            logger.error(f"Error making trading decision for {stock_data.get('symbol')}: {e}")
            return {
                'symbol': stock_data.get('symbol', 'UNKNOWN'),
                'timestamp': datetime.now(),
                'error': str(e),
                'final_action': 'HOLD',
                'should_trade': False
            }


# Standalone function for easy import
async def make_trading_decision(stock_data: Dict, sentiment_data: Dict) -> Dict:
    """
    Convenience function to make a trading decision.
    
    Args:
        stock_data: Technical analysis data
        sentiment_data: Sentiment analysis data
        
    Returns:
        Trading decision
    """
    engine = AIDecisionEngine()
    return await engine.make_trading_decision(stock_data, sentiment_data)


if __name__ == "__main__":
    # Test the AI decision engine
    async def test_ai_engine():
        # Mock data for testing
        stock_data = {
            'symbol': 'RELIANCE',
            'current_price': 2500.0,
            'vwap': 2480.0,
            'rsi': 35.0,
            'volume_ratio': 2.1,
            'volatility_pct': 1.8,
            'above_vwap': True,
            'price_change_pct': 1.2
        }
        
        sentiment_data = {
            'final_sentiment': 0.6,
            'intraday_relevance': 0.7,
            'confidence': 0.8,
            'trade_signal': 'BULLISH',
            'news_count': 5,
            'tweet_count': 15
        }
        
        try:
            decision = await make_trading_decision(stock_data, sentiment_data)
            
            print("🤖 AI Trading Decision:")
            print(f"Symbol: {decision['symbol']}")
            print(f"Final Action: {decision['final_action']}")
            print(f"Should Trade: {decision['should_trade']}")
            
            if 'ai_decision' in decision:
                ai = decision['ai_decision']
                print(f"Confidence: {ai['confidence']:.2f}")
                print(f"R:R Ratio: {ai['risk_reward_ratio']:.2f}")
                print(f"Entry: ₹{ai['entry_price']:.2f}")
                print(f"Stop Loss: ₹{ai['stop_loss']:.2f}")
                print(f"Target: ₹{ai['target_price']:.2f}")
                print(f"Reasoning: {ai['reasoning']}")
            
            if 'validation' in decision:
                print(f"Validation: {decision['validation']['message']}")
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
    
    asyncio.run(test_ai_engine())
