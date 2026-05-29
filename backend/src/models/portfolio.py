"""
Portfolio data models for MongoDB storage.
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PortfolioPosition(BaseModel):
    """Individual position in the portfolio"""
    symbol: str
    tradeId: str
    quantity: int
    entryPrice: float
    currentPrice: float
    stopLoss: float
    target1: Optional[float] = None
    target2: Optional[float] = None
    unrealizedPnl: float = 0.0
    unrealizedPnlPercent: float = 0.0
    allocatedCapital: float
    strategyId: str
    entryTime: datetime


class DailyPerformance(BaseModel):
    """Daily performance snapshot"""
    date: str  # YYYY-MM-DD
    startingCapital: float
    endingCapital: float
    realizedPnl: float
    unrealizedPnl: float
    totalPnl: float
    pnlPercent: float
    tradesExecuted: int
    winningTrades: int
    losingTrades: int


class PortfolioModel(BaseModel):
    """
    Portfolio state model.
    
    Tracks capital, positions, and performance.
    """
    # Identification
    portfolioId: str = Field(default="main", description="Portfolio identifier")
    userId: str = Field(default="user", description="Owner user ID")
    
    # Capital tracking
    initialCapital: float = Field(..., description="Starting capital")
    currentCapital: float = Field(..., description="Current total capital (cash + positions)")
    availableCapital: float = Field(..., description="Available cash for new trades")
    allocatedCapital: float = Field(default=0.0, description="Capital in open positions")
    
    # Positions
    openPositions: Dict[str, PortfolioPosition] = Field(
        default_factory=dict,
        description="Open positions keyed by symbol"
    )
    
    # P&L tracking
    totalRealizedPnl: float = Field(default=0.0, description="Total realized P&L")
    totalUnrealizedPnl: float = Field(default=0.0, description="Total unrealized P&L")
    todayRealizedPnl: float = Field(default=0.0, description="Today's realized P&L")
    todayUnrealizedPnl: float = Field(default=0.0, description="Today's unrealized P&L")
    
    # Performance metrics
    peakCapital: float = Field(..., description="Highest capital reached")
    currentDrawdown: float = Field(default=0.0, description="Current drawdown from peak")
    maxDrawdown: float = Field(default=0.0, description="Maximum drawdown ever")
    
    # Daily performance history
    dailyPerformance: List[DailyPerformance] = Field(
        default_factory=list,
        description="Daily performance snapshots"
    )
    
    # Risk status
    dailyLossLimitHit: bool = Field(default=False, description="Daily loss limit reached")
    drawdownLimitHit: bool = Field(default=False, description="Drawdown limit reached")
    tradingEnabled: bool = Field(default=True, description="Trading enabled/disabled")
    
    # Statistics
    totalTrades: int = Field(default=0, description="Total trades executed")
    winningTrades: int = Field(default=0, description="Number of winning trades")
    losingTrades: int = Field(default=0, description="Number of losing trades")
    winRate: float = Field(default=0.0, description="Win rate percentage")
    
    # Metadata
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)
    lastTradeTime: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "portfolioId": "main",
                "userId": "user",
                "initialCapital": 100000.0,
                "currentCapital": 102450.0,
                "availableCapital": 62450.0,
                "allocatedCapital": 40000.0,
                "openPositions": {
                    "RELIANCE": {
                        "symbol": "RELIANCE",
                        "tradeId": "trade-123",
                        "quantity": 8,
                        "entryPrice": 2450.0,
                        "currentPrice": 2485.0,
                        "stopLoss": 2400.0,
                        "target1": 2500.0,
                        "target2": 2550.0,
                        "unrealizedPnl": 280.0,
                        "unrealizedPnlPercent": 1.43,
                        "allocatedCapital": 19600.0,
                        "strategyId": "news_momentum_v1",
                        "entryTime": "2025-11-12T10:30:00"
                    }
                },
                "totalRealizedPnl": 2450.0,
                "totalUnrealizedPnl": 280.0,
                "todayRealizedPnl": 1200.0,
                "todayUnrealizedPnl": 280.0,
                "peakCapital": 103000.0,
                "currentDrawdown": 550.0,
                "maxDrawdown": 2000.0,
                "totalTrades": 15,
                "winningTrades": 10,
                "losingTrades": 5,
                "winRate": 66.67,
                "tradingEnabled": True
            }
        }
    
    def calculate_total_capital(self) -> float:
        """Calculate total capital (cash + positions)"""
        position_value = sum(
            pos.currentPrice * pos.quantity 
            for pos in self.openPositions.values()
        )
        return self.availableCapital + position_value
    
    def calculate_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L"""
        return sum(pos.unrealizedPnl for pos in self.openPositions.values())
    
    def calculate_drawdown(self) -> float:
        """Calculate current drawdown from peak"""
        current = self.calculate_total_capital()
        if self.peakCapital > 0:
            return ((self.peakCapital - current) / self.peakCapital) * 100
        return 0.0
    
    def update_metrics(self):
        """Update all calculated metrics"""
        self.currentCapital = self.calculate_total_capital()
        self.totalUnrealizedPnl = self.calculate_unrealized_pnl()
        self.currentDrawdown = self.calculate_drawdown()
        
        if self.currentCapital > self.peakCapital:
            self.peakCapital = self.currentCapital
        
        if self.currentDrawdown > self.maxDrawdown:
            self.maxDrawdown = self.currentDrawdown
        
        if self.totalTrades > 0:
            self.winRate = (self.winningTrades / self.totalTrades) * 100
        
        self.updatedAt = datetime.now()

