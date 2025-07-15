"""
Configuration module for the Trading Bot.
Handles all environment variables, API keys, and system settings.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class TradingBotConfig(BaseSettings):
    """Configuration settings for the trading bot."""
    
    # Trading Parameters
    INITIAL_CAPITAL: float = Field(default=100000.0, description="Initial capital in INR")
    MAX_CAPITAL_PER_TRADE: float = Field(default=0.01, description="Max 1% capital per trade")
    MAX_ACTIVE_TRADES: int = Field(default=2, description="Maximum concurrent trades")
    MAX_DAILY_LOSSES: int = Field(default=3, description="Maximum daily losses allowed")
    MAX_DAILY_DRAWDOWN: float = Field(default=0.05, description="Maximum daily drawdown (5%)")
    MIN_RISK_REWARD_RATIO: float = Field(default=1.5, description="Minimum risk:reward ratio")
    AI_CONFIDENCE_THRESHOLD: float = Field(default=0.8, description="Minimum AI confidence required")
    
    # Market Hours
    MARKET_OPEN_HOUR: int = Field(default=9, description="Market open hour")
    MARKET_OPEN_MINUTE: int = Field(default=15, description="Market open minute")
    FORCE_EXIT_HOUR: int = Field(default=15, description="Force exit hour")
    FORCE_EXIT_MINUTE: int = Field(default=10, description="Force exit minute")
    
    # Trading Hours Configuration
    TRADING_HOURS_START: str = Field(default="09:15", env="TRADING_HOURS_START")
    TRADING_HOURS_END: str = Field(default="15:30", env="TRADING_HOURS_END") 
    FORCE_EXIT_TIME: str = Field(default="15:10", env="FORCE_EXIT_TIME")
    
    # Polling Intervals
    INACTIVE_POLL_INTERVAL: int = Field(default=600, description="10 minutes for inactive stocks")
    ACTIVE_POLL_INTERVAL: int = Field(default=60, description="1 minute for active trades")
    
    # API Keys - Fyers
    FYERS_APP_ID: Optional[str] = Field(default=None, env="FYERS_APP_ID")
    FYERS_SECRET_KEY: Optional[str] = Field(default=None, env="FYERS_SECRET_KEY")
    FYERS_ACCESS_TOKEN: Optional[str] = Field(default=None, env="FYERS_ACCESS_TOKEN")
    FYERS_REDIRECT_URI: Optional[str] = Field(default="https://trade.fyers.in/api-login/redirect-uri/index.html", env="FYERS_REDIRECT_URI")
    
    # AI API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")
    
    # Database
    MONGODB_URL: str = Field(default="mongodb://localhost:27017/", env="MONGODB_URL")
    MONGODB_URI: str = Field(default="mongodb://localhost:27017", env="MONGODB_URI")
    DATABASE_NAME: str = Field(default="trading_bot", env="DATABASE_NAME")
    MONGODB_DATABASE: str = Field(default="trading_bot", env="MONGODB_DATABASE")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # News Sources
    NEWS_SOURCES: str = Field(default="google,moneycontrol,economic_times", env="NEWS_SOURCES")
    
    # External APIs
    SCREENER_API_KEY: Optional[str] = Field(default=None, env="SCREENER_API_KEY")
    CHARTINK_API_KEY: Optional[str] = Field(default=None, env="CHARTINK_API_KEY")
    TRADINGVIEW_API_KEY: Optional[str] = Field(default=None, env="TRADINGVIEW_API_KEY")
    TWITTER_BEARER_TOKEN: Optional[str] = Field(default=None, env="TWITTER_BEARER_TOKEN")
    
    # Mock Mode
    MOCK_MODE: bool = Field(default=True, env="MOCK_MODE")
    MOCK_BROKER: bool = Field(default=True, env="MOCK_BROKER")
    MOCK_AI: bool = Field(default=True, env="MOCK_AI")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE_PATH: str = Field(default="logs/trading_bot.log", env="LOG_FILE_PATH")
    
    # Data Sources
    DATA_SOURCE: str = Field(default="yfinance", description="Primary data source")
    BACKUP_DATA_SOURCE: str = Field(default="mock", description="Backup data source")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global configuration instance
config = TradingBotConfig()


def get_config() -> TradingBotConfig:
    """Get the global configuration instance."""
    return config


def validate_config() -> bool:
    """Validate that all required configuration is present."""
    if not config.MOCK_MODE:
        required_fields = [
            'FYERS_APP_ID',
            'FYERS_SECRET_KEY',
            'FYERS_ACCESS_TOKEN',
            'OPENAI_API_KEY',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHAT_ID'
        ]
        
        missing_fields = []
        for field in required_fields:
            if getattr(config, field) is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
    
    return True


if __name__ == "__main__":
    # Test configuration loading
    try:
        validate_config()
        print("✅ Configuration loaded successfully")
        print(f"Mock Mode: {config.MOCK_MODE}")
        print(f"Initial Capital: ₹{config.INITIAL_CAPITAL:,.2f}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
