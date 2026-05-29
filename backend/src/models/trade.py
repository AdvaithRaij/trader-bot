"""
Trade data models for MongoDB storage.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class TradeStatus(str, Enum):
    """Trade status enum"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class TradeDirection(str, Enum):
    """Trade direction enum"""
    BUY = "BUY"
    SELL = "SELL"


class ExitReason(str, Enum):
    """Reason for closing a trade"""
    TARGET_1_HIT = "TARGET_1_HIT"
    TARGET_2_HIT = "TARGET_2_HIT"
    STOP_LOSS_HIT = "STOP_LOSS_HIT"
    TRAILING_STOP_HIT = "TRAILING_STOP_HIT"
    END_OF_DAY = "END_OF_DAY"
    MANUAL_EXIT = "MANUAL_EXIT"
    STRATEGY_EXIT = "STRATEGY_EXIT"
    RISK_LIMIT_HIT = "RISK_LIMIT_HIT"


class OrderDetails(BaseModel):
    """Order details from broker"""
    orderId: Optional[str] = None
    orderStatus: Optional[str] = None
    filledQty: int = 0
    avgPrice: float = 0.0
    orderTime: Optional[datetime] = None
    message: Optional[str] = None


class TradeModel(BaseModel):
    """
    Trade model for storing individual trades in MongoDB.
    
    Represents a complete trade lifecycle from entry to exit.
    """
    # Trade identification
    tradeId: str = Field(..., description="Unique trade identifier (UUID)")
    strategyId: str = Field(..., description="Strategy that generated this trade")
    strategyName: str = Field(..., description="Human-readable strategy name")
    
    # Stock details
    symbol: str = Field(..., description="Stock symbol (e.g., RELIANCE, TCS)")
    exchange: str = Field(default="NSE", description="Exchange (NSE/BSE)")
    
    # Entry details
    direction: TradeDirection = Field(..., description="BUY or SELL")
    entryTime: datetime = Field(..., description="Trade entry timestamp")
    entryPrice: float = Field(..., description="Actual entry price")
    quantity: int = Field(..., description="Number of shares")
    entryOrderDetails: Optional[OrderDetails] = None
    
    # Exit details
    exitTime: Optional[datetime] = Field(None, description="Trade exit timestamp")
    exitPrice: Optional[float] = Field(None, description="Actual exit price")
    exitReason: Optional[ExitReason] = None
    exitOrderDetails: Optional[OrderDetails] = None
    
    # Trade levels (AI-suggested or strategy-defined)
    stopLoss: float = Field(..., description="Stop loss price")
    target1: Optional[float] = Field(None, description="First target price")
    target2: Optional[float] = Field(None, description="Second target price")
    trailingStopLoss: Optional[float] = Field(None, description="Trailing stop loss price")
    
    # P&L tracking
    pnl: Optional[float] = Field(None, description="Profit/Loss in rupees")
    pnlPercent: Optional[float] = Field(None, description="Profit/Loss percentage")
    charges: float = Field(default=0.0, description="Brokerage and charges")
    netPnl: Optional[float] = Field(None, description="Net P&L after charges")
    
    # Status
    status: TradeStatus = Field(default=TradeStatus.PENDING, description="Current trade status")
    
    # AI Analysis (from news or technical analysis)
    aiAnalysis: Optional[Dict[str, Any]] = Field(None, description="AI analysis that triggered this trade")
    newsArticles: Optional[List[str]] = Field(None, description="Related news article IDs")
    
    # Metadata
    createdAt: datetime = Field(default_factory=datetime.now, description="Record creation time")
    updatedAt: datetime = Field(default_factory=datetime.now, description="Last update time")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tradeId": "550e8400-e29b-41d4-a716-446655440000",
                "strategyId": "news_momentum_v1",
                "strategyName": "News-Driven Momentum",
                "symbol": "RELIANCE",
                "exchange": "NSE",
                "direction": "BUY",
                "entryTime": "2025-11-12T10:30:00",
                "entryPrice": 2450.0,
                "quantity": 8,
                "stopLoss": 2400.0,
                "target1": 2500.0,
                "target2": 2550.0,
                "status": "OPEN",
                "aiAnalysis": {
                    "impact": "HIGH",
                    "sentiment": "POSITIVE",
                    "analysis": "Strong bullish momentum after renewable energy news"
                }
            }
        }


class PositionModel(BaseModel):
    """
    Current open position (derived from Trade).
    Used for real-time monitoring.
    """
    tradeId: str
    symbol: str
    quantity: int
    entryPrice: float
    currentPrice: float
    stopLoss: float
    target1: Optional[float] = None
    target2: Optional[float] = None
    trailingStopLoss: Optional[float] = None
    unrealizedPnl: float
    unrealizedPnlPercent: float
    
    def update_current_price(self, price: float):
        """Update current price and recalculate P&L"""
        self.currentPrice = price
        self.unrealizedPnl = (price - self.entryPrice) * self.quantity
        self.unrealizedPnlPercent = ((price - self.entryPrice) / self.entryPrice) * 100
    
    def should_exit_stop_loss(self) -> bool:
        """Check if stop loss is hit"""
        return self.currentPrice <= self.stopLoss
    
    def should_exit_target1(self) -> bool:
        """Check if target 1 is hit"""
        return self.target1 and self.currentPrice >= self.target1
    
    def should_exit_target2(self) -> bool:
        """Check if target 2 is hit"""
        return self.target2 and self.currentPrice >= self.target2
    
    def should_exit_trailing_stop(self) -> bool:
        """Check if trailing stop loss is hit"""
        return self.trailingStopLoss and self.currentPrice <= self.trailingStopLoss


class TradeSignal(BaseModel):
    """
    Trade signal generated by a strategy.
    This is what the strategy engine produces.
    """
    symbol: str
    direction: TradeDirection
    signalTime: datetime = Field(default_factory=datetime.now)
    strategyId: str
    strategyName: str
    
    # Suggested levels
    entryPrice: float
    stopLoss: float
    target1: Optional[float] = None
    target2: Optional[float] = None
    
    # Signal strength and reasoning
    confidence: float = Field(..., ge=0, le=100, description="Signal confidence (0-100)")
    reasoning: str = Field(..., description="Why this trade is suggested")
    
    # Related data
    aiAnalysis: Optional[Dict[str, Any]] = None
    newsArticles: Optional[List[str]] = None
    
    # Position sizing (calculated by portfolio manager)
    suggestedQuantity: Optional[int] = None
    suggestedCapital: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "direction": "BUY",
                "strategyId": "news_momentum_v1",
                "strategyName": "News-Driven Momentum",
                "entryPrice": 2450.0,
                "stopLoss": 2400.0,
                "target1": 2500.0,
                "target2": 2550.0,
                "confidence": 85,
                "reasoning": "HIGH impact positive news on renewable energy expansion. Strong support at 2440."
            }
        }

