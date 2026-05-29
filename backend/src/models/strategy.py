"""
Strategy configuration models for MongoDB storage.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class StrategyStatus(str, Enum):
    """Strategy status"""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"


class StockPickingType(str, Enum):
    """Type of stock picking strategy"""
    NEWS_BASED = "NEWS_BASED"
    TECHNICAL = "TECHNICAL"
    MOMENTUM = "MOMENTUM"
    AI_RECOMMENDED = "AI_RECOMMENDED"
    CUSTOM = "CUSTOM"


class ExecutionType(str, Enum):
    """Type of trade execution strategy"""
    BREAKOUT = "BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    SCALPING = "SCALPING"
    AI_ASSISTED = "AI_ASSISTED"
    CUSTOM = "CUSTOM"


class StockPickingConfig(BaseModel):
    """Configuration for stock picking logic"""
    type: StockPickingType
    
    # News-based filters
    newsFilters: Optional[Dict[str, Any]] = Field(
        None,
        description="Filters for news-based picking",
        json_schema_extra={
            "example": {
                "impact": "HIGH",
                "sentiment": "POSITIVE",
                "relevance": 80,
                "minConfidence": 70
            }
        }
    )
    
    # Technical filters
    technicalFilters: Optional[Dict[str, Any]] = Field(
        None,
        description="Technical indicator filters",
        json_schema_extra={
            "example": {
                "rsi": {"min": 30, "max": 70},
                "macd": "bullish_crossover",
                "volume": "above_average"
            }
        }
    )
    
    # Stock universe
    allowedSymbols: Optional[List[str]] = Field(
        None,
        description="Whitelist of symbols (None = all stocks)"
    )
    excludedSymbols: Optional[List[str]] = Field(
        default_factory=list,
        description="Blacklist of symbols"
    )
    
    # Limits
    maxStocks: int = Field(default=5, description="Maximum stocks to pick")
    minMarketCap: Optional[float] = Field(None, description="Minimum market cap filter")


class ExecutionConfig(BaseModel):
    """Configuration for trade execution logic"""
    type: ExecutionType
    
    # Entry conditions
    entryCondition: str = Field(
        ...,
        description="Entry condition logic",
        json_schema_extra={"example": "price > resistance"}
    )
    
    # Exit conditions
    stopLossPercent: float = Field(default=2.0, description="Stop loss percentage")
    takeProfitPercent: float = Field(default=5.0, description="Take profit percentage")
    useTrailingStop: bool = Field(default=False, description="Enable trailing stop loss")
    trailingStopPercent: Optional[float] = Field(None, description="Trailing stop percentage")
    
    # Targets
    useMultipleTargets: bool = Field(default=True, description="Use multiple profit targets")
    target1Percent: Optional[float] = Field(default=3.0, description="First target percentage")
    target2Percent: Optional[float] = Field(default=5.0, description="Second target percentage")
    
    # Exit at end of day
    exitAtEOD: bool = Field(default=True, description="Close all positions at end of day")
    eodExitTime: str = Field(default="15:15", description="Time to exit (HH:MM)")
    
    # AI assistance
    useAILevels: bool = Field(default=True, description="Use AI to suggest entry/exit levels")


class RiskManagementConfig(BaseModel):
    """Risk management configuration"""
    # Position sizing
    maxPositionSizePercent: float = Field(
        default=20.0,
        description="Max % of capital per position"
    )
    
    # Risk limits
    maxDailyLossPercent: float = Field(
        default=5.0,
        description="Max daily loss % (stop trading if hit)"
    )
    maxDrawdownPercent: float = Field(
        default=10.0,
        description="Max drawdown % from peak"
    )
    
    # Position limits
    maxOpenPositions: int = Field(default=5, description="Max concurrent positions")
    maxPositionsPerStock: int = Field(default=1, description="Max positions in same stock")
    
    # Diversification
    maxSectorExposurePercent: Optional[float] = Field(
        None,
        description="Max % of capital in one sector"
    )


class StrategyPerformance(BaseModel):
    """Strategy performance metrics"""
    totalTrades: int = 0
    winningTrades: int = 0
    losingTrades: int = 0
    winRate: float = 0.0
    
    totalPnl: float = 0.0
    avgPnl: float = 0.0
    avgWin: float = 0.0
    avgLoss: float = 0.0
    
    maxWin: float = 0.0
    maxLoss: float = 0.0
    maxDrawdown: float = 0.0
    
    sharpeRatio: Optional[float] = None
    profitFactor: Optional[float] = None
    
    lastUpdated: datetime = Field(default_factory=datetime.now)


class StrategyModel(BaseModel):
    """
    Complete strategy configuration model.
    
    Defines how to pick stocks and execute trades.
    """
    # Identification
    strategyId: str = Field(..., description="Unique strategy identifier")
    name: str = Field(..., description="Human-readable strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    version: str = Field(default="1.0", description="Strategy version")
    
    # Configuration
    stockPicking: StockPickingConfig
    execution: ExecutionConfig
    riskManagement: RiskManagementConfig
    
    # Status
    status: StrategyStatus = Field(default=StrategyStatus.ACTIVE)
    
    # Performance tracking
    performance: StrategyPerformance = Field(default_factory=StrategyPerformance)
    
    # Metadata
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    createdBy: str = Field(default="user", description="Creator user ID")
    
    # Backtesting results
    backtestResults: Optional[Dict[str, Any]] = Field(
        None,
        description="Results from backtesting this strategy"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategyId": "news_momentum_v1",
                "name": "News-Driven Momentum",
                "description": "Buy stocks with high-impact positive news and strong momentum",
                "version": "1.0",
                "stockPicking": {
                    "type": "NEWS_BASED",
                    "newsFilters": {
                        "impact": "HIGH",
                        "sentiment": "POSITIVE",
                        "relevance": 80
                    },
                    "maxStocks": 5
                },
                "execution": {
                    "type": "BREAKOUT",
                    "entryCondition": "price > resistance",
                    "stopLossPercent": 2.0,
                    "takeProfitPercent": 5.0,
                    "useTrailingStop": True,
                    "trailingStopPercent": 1.5,
                    "useMultipleTargets": True,
                    "target1Percent": 3.0,
                    "target2Percent": 5.0,
                    "exitAtEOD": True,
                    "eodExitTime": "15:15",
                    "useAILevels": True
                },
                "riskManagement": {
                    "maxPositionSizePercent": 20.0,
                    "maxDailyLossPercent": 5.0,
                    "maxDrawdownPercent": 10.0,
                    "maxOpenPositions": 5,
                    "maxPositionsPerStock": 1
                },
                "status": "ACTIVE"
            }
        }

