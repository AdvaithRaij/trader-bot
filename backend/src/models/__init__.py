"""
Data models for the trading bot.
"""
from .trade import (
    TradeModel,
    TradeStatus,
    TradeDirection,
    ExitReason,
    OrderDetails,
    PositionModel,
    TradeSignal
)
from .strategy import (
    StrategyModel,
    StrategyStatus,
    StockPickingType,
    ExecutionType,
    StockPickingConfig,
    ExecutionConfig,
    RiskManagementConfig,
    StrategyPerformance
)
from .portfolio import (
    PortfolioModel,
    PortfolioPosition,
    DailyPerformance
)
from .screener import (
    MarketContext,
    LiquidityMetrics,
    PriceAction,
    TechnicalIndicators,
    PivotLevels,
    NewsContext,
    ScreenerCandidate,
    ScreenerOutput,
    # New multi-strategy models
    FundamentalData,
    EnhancedNewsContext,
    StockAnalysisData
)
from .trade_plan import (
    TradePlanLevels,
    TradePlanRationale,
    TradePlan,
    TradePlanOutput,
    # New multi-strategy models
    StrategyAnalysis,
    StrategyRecommendation,
    MultiStrategyResult,
    MultiStrategyOutput
)

__all__ = [
    # Trade models
    "TradeModel",
    "TradeStatus",
    "TradeDirection",
    "ExitReason",
    "OrderDetails",
    "PositionModel",
    "TradeSignal",

    # Strategy models
    "StrategyModel",
    "StrategyStatus",
    "StockPickingType",
    "ExecutionType",
    "StockPickingConfig",
    "ExecutionConfig",
    "RiskManagementConfig",
    "StrategyPerformance",

    # Portfolio models
    "PortfolioModel",
    "PortfolioPosition",
    "DailyPerformance",

    # Screener models
    "MarketContext",
    "LiquidityMetrics",
    "PriceAction",
    "TechnicalIndicators",
    "PivotLevels",
    "NewsContext",
    "ScreenerCandidate",
    "ScreenerOutput",
    "FundamentalData",
    "EnhancedNewsContext",
    "StockAnalysisData",

    # Trade plan models
    "TradePlanLevels",
    "TradePlanRationale",
    "TradePlan",
    "TradePlanOutput",
    "StrategyAnalysis",
    "StrategyRecommendation",
    "MultiStrategyResult",
    "MultiStrategyOutput",
]

