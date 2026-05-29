#!/usr/bin/env python3
"""
Test script to check Gemini API access and available models.
"""

import sys
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from config import get_config
import google.generativeai as genai

def test_gemini_access():
    """Test Gemini API access and list available models."""
    
    config = get_config()
    
    print("🤖 Testing Gemini API Access")
    print("=" * 60)
    
    # Check if API key is configured
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "your_gemini_api_key_here":
        print("❌ GEMINI_API_KEY not configured in .env file")
        print("\nPlease add your Gemini API key to .env:")
        print("GEMINI_API_KEY=your_actual_api_key_here")
        return False
    
    print(f"✅ API Key found: {config.GEMINI_API_KEY[:10]}...{config.GEMINI_API_KEY[-4:]}")
    print()
    
    try:
        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # List available models
        print("📋 Available Gemini Models:")
        print("-" * 60)
        
        available_models = []
        for model in genai.list_models():
            # Check if model supports generateContent
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)
                print(f"✅ {model.name}")
                print(f"   Display Name: {model.display_name}")
                print(f"   Description: {model.description}")
                print(f"   Input Token Limit: {model.input_token_limit}")
                print(f"   Output Token Limit: {model.output_token_limit}")
                print()
        
        if not available_models:
            print("❌ No models available for content generation")
            return False
        
        print(f"\n✅ Total models available: {len(available_models)}")
        print()
        
        # Test a simple generation with the first available model
        print("🧪 Testing Content Generation...")
        print("-" * 60)
        
        # Use gemini-pro as default, or first available model
        test_model_name = "models/gemini-pro" if "models/gemini-pro" in available_models else available_models[0]
        print(f"Using model: {test_model_name}")
        
        model = genai.GenerativeModel(test_model_name)
        
        # Simple test prompt
        test_prompt = "Say 'Hello! I am working correctly.' in exactly those words."
        
        print(f"\nTest Prompt: {test_prompt}")
        print("\nGenerating response...")
        
        response = model.generate_content(test_prompt)
        
        print(f"\n✅ Response received:")
        print(f"{response.text}")
        print()
        
        # Test with a trading-related prompt
        print("🧪 Testing Trading Analysis...")
        print("-" * 60)
        
        trading_prompt = """
        Analyze this stock data and provide a brief trading recommendation in JSON format:
        
        Stock: RELIANCE
        Current Price: ₹2500
        RSI: 45
        Volume: High
        Sentiment: Positive
        
        Respond with JSON containing: decision (BUY/SELL/HOLD), confidence (0-1), and brief reasoning.
        """
        
        print("Generating trading analysis...")
        response = model.generate_content(trading_prompt)
        
        print(f"\n✅ Trading Analysis Response:")
        print(response.text)
        print()
        
        print("=" * 60)
        print("✅ Gemini API is working correctly!")
        print(f"✅ Recommended model for trading: {test_model_name}")
        print()
        print("You can now use Gemini for AI-powered trading decisions.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing Gemini API: {e}")
        print(f"\nError type: {type(e).__name__}")
        
        if "API_KEY_INVALID" in str(e) or "invalid" in str(e).lower():
            print("\n⚠️  Your API key appears to be invalid.")
            print("Please check:")
            print("1. The API key is correct")
            print("2. The API key is enabled in Google AI Studio")
            print("3. You have access to Gemini API")
        
        return False

if __name__ == "__main__":
    success = test_gemini_access()
    sys.exit(0 if success else 1)

