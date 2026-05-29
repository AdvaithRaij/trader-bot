"""
Trade Plan models matching PLAN_OF_ACTION.md Stage 2 output schema.

Extended with StrategyAnalysis and MultiStrategyResult for multi-strategy pipeline.
"""
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field


# ============================================
# MULTI-STRATEGY ANALYSIS MODELS (NEW)
# ============================================

class StrategyAnalysis(BaseModel):
    """
    Analysis result from a single strategy.
    Each of the 3 strategies (Fundamental, News-Based, Combined) produces this.
    """
    # Strategy identification
    strategy_id: Literal["fundamental", "news_based", "combined"] = Field(
        ..., description="Strategy identifier"
    )
    strategy_name: str = Field(..., description="Human-readable strategy name")

    # Trade direction and confidence
    direction: Literal["BUY", "SELL", "HOLD"] = Field(
        ..., description="Recommended trade direction"
    )
    confidence: float = Field(
        ..., ge=0, le=100, description="Confidence score 0-100"
    )

    # Price levels
    entry: float = Field(..., description="Suggested entry price")
    stop_loss: float = Field(..., description="Stop loss price")
    stop_loss_pct: float = Field(..., description="Stop loss % from entry")
    target_1: float = Field(..., description="First target price")
    target_1_pct: float = Field(..., description="Target 1 % from entry")
    target_2: Optional[float] = Field(None, description="Second target price")
    target_2_pct: Optional[float] = Field(None, description="Target 2 % from entry")

    # Risk metrics
    risk_reward_ratio: float = Field(..., ge=0, description="Risk:Reward ratio")
    risk_per_share: float = Field(..., description="Risk per share (entry - SL)")

    # Reasoning
    reasoning: str = Field(..., description="2-3 sentence explanation")
    risks: List[str] = Field(default_factory=list, description="Key risks")
    catalysts: List[str] = Field(default_factory=list, description="Key catalysts")

    # Timeframe
    timeframe: str = Field(
        default="1-3 days", description="Expected holding period"
    )

    # Validation
    is_actionable: bool = Field(
        default=True, description="Whether this analysis suggests action"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "fundamental",
                "strategy_name": "Fundamental Analysis",
                "direction": "BUY",
                "confidence": 72,
                "entry": 2445,
                "stop_loss": 2408,
                "stop_loss_pct": -1.5,
                "target_1": 2520,
                "target_1_pct": 3.1,
                "target_2": 2570,
                "target_2_pct": 5.1,
                "risk_reward_ratio": 2.0,
                "risk_per_share": 37,
                "reasoning": "P/E below sector average, strong EPS growth...",
                "risks": ["Market volatility", "Crude price dependency"],
                "timeframe": "2-5 days"
            }
        }


class StrategyRecommendation(BaseModel):
    """
    AI recommendation comparing all 3 strategies.
    Explains which strategy is best and why.
    """
    best_strategy: Literal["fundamental", "news_based", "combined"] = Field(
        ..., description="Recommended strategy ID"
    )
    best_strategy_name: str = Field(..., description="Recommended strategy name")
    confidence: float = Field(..., ge=0, le=100, description="Recommendation confidence")
    reasoning: str = Field(..., description="Why this strategy is recommended")

    # Comparison summary
    strategy_comparison: Dict[str, str] = Field(
        default_factory=dict,
        description="Brief comparison of each strategy"
    )

    # Overall assessment
    overall_sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        default="neutral", description="Overall market sentiment for this stock"
    )
    trade_quality: Literal["excellent", "good", "fair", "poor"] = Field(
        default="fair", description="Overall trade quality assessment"
    )


class MultiStrategyResult(BaseModel):
    """
    Complete multi-strategy analysis result for a single stock.
    Contains analyses from all 3 strategies plus AI recommendation.
    """
    # Stock identification
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    current_price: float = Field(..., description="Current price at analysis time")
    day_change_pct: float = Field(default=0, description="Day change %")

    # Individual strategy analyses
    fundamental: StrategyAnalysis = Field(..., description="Fundamental strategy analysis")
    news_based: StrategyAnalysis = Field(..., description="News-based strategy analysis")
    combined: StrategyAnalysis = Field(..., description="Combined strategy analysis")

    # AI recommendation
    recommendation: StrategyRecommendation = Field(
        ..., description="AI recommendation comparing strategies"
    )

    # Screener data reference
    screener_score: float = Field(default=0, description="Original screener score")

    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    analysis_duration_ms: int = Field(default=0, description="Time taken for analysis")

    def get_best_strategy(self) -> StrategyAnalysis:
        """Get the recommended strategy analysis."""
        strategy_map = {
            "fundamental": self.fundamental,
            "news_based": self.news_based,
            "combined": self.combined
        }
        return strategy_map[self.recommendation.best_strategy]

    def get_strategy_by_id(self, strategy_id: str) -> Optional[StrategyAnalysis]:
        """Get a specific strategy analysis by ID."""
        strategy_map = {
            "fundamental": self.fundamental,
            "news_based": self.news_based,
            "combined": self.combined
        }
        return strategy_map.get(strategy_id)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE",
                "name": "Reliance Industries Ltd",
                "current_price": 2450.50,
                "day_change_pct": 1.2,
                "screener_score": 87
            }
        }


class MultiStrategyOutput(BaseModel):
    """
    Complete output from multi-strategy analysis pipeline.
    Contains results for all analyzed stocks.
    """
    timestamp: datetime = Field(default_factory=datetime.now)

    # Market context
    market_context: Dict[str, Any] = Field(
        default_factory=dict, description="Market context at analysis time"
    )

    # Analysis results
    analyses: List[MultiStrategyResult] = Field(
        default_factory=list, description="Multi-strategy results for each stock"
    )

    # Summary stats
    total_analyzed: int = Field(default=0, description="Total stocks analyzed")
    analysis_duration_ms: int = Field(default=0, description="Total analysis time")

    def get_top_by_confidence(self, n: int = 5) -> List[MultiStrategyResult]:
        """Get top N stocks by best strategy confidence."""
        sorted_results = sorted(
            self.analyses,
            key=lambda x: x.get_best_strategy().confidence,
            reverse=True
        )
        return sorted_results[:n]

    def get_by_strategy(self, strategy_id: str) -> List[Dict[str, Any]]:
        """Get all stocks ranked by a specific strategy's confidence."""
        results = []
        for analysis in self.analyses:
            strategy = analysis.get_strategy_by_id(strategy_id)
            if strategy:
                results.append({
                    "symbol": analysis.symbol,
                    "strategy": strategy,
                    "is_recommended": analysis.recommendation.best_strategy == strategy_id
                })
        return sorted(results, key=lambda x: x["strategy"].confidence, reverse=True)


# ============================================
# ORIGINAL TRADE PLAN MODELS
# ============================================

class TradePlanLevels(BaseModel):
    """Entry, stop loss, and target levels for a trade plan."""
    entry: float = Field(..., description="Entry price")
    stop_loss: float = Field(..., description="Stop loss price")
    target_1: float = Field(..., description="Conservative target (1.5R)")
    target_2: Optional[float] = Field(None, description="Aggressive target (2R)")
    risk_per_share: float = Field(..., description="|entry - stop_loss|")
    reward_per_share: float = Field(..., description="|target_1 - entry|")
    risk_reward_ratio: float = Field(..., ge=0, description="R:R ratio")


class TradePlanRationale(BaseModel):
    """AI reasoning for the trade plan."""
    setup_type: str = Field(..., description="breakout/pullback/reversal/momentum")
    key_levels: List[str] = Field(default_factory=list, description="Key support/resistance levels")
    catalysts: List[str] = Field(default_factory=list, description="News/events driving the trade")
    risks: List[str] = Field(default_factory=list, description="Potential risks to the trade")
    summary: str = Field(..., description="Brief trade thesis")


class TradePlan(BaseModel):
    """
    Complete trade plan for a screened candidate.
    Matches PLAN_OF_ACTION.md Stage 2 output schema.
    """
    symbol: str = Field(..., description="Stock symbol")
    direction: Literal["BUY", "SELL"] = Field(..., description="Trade direction")
    confidence: float = Field(..., ge=0, le=100, description="AI confidence score 0-100")
    levels: TradePlanLevels
    rationale: TradePlanRationale
    position_size: Optional[int] = Field(None, description="Suggested quantity (filled by executor)")
    max_capital: Optional[float] = Field(None, description="Max capital for this trade")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Validation flags
    passes_rr_check: bool = Field(default=False, description="R:R >= 1.5")
    passes_confidence_check: bool = Field(default=False, description="Confidence >= 75")
    is_executable: bool = Field(default=False, description="Passes all validation checks")
    
    def validate_for_execution(self, min_rr: float = 1.5, min_confidence: float = 75.0) -> bool:
        """
        Validate trade plan for execution.
        
        Args:
            min_rr: Minimum risk:reward ratio (default 1.5)
            min_confidence: Minimum confidence score (default 75)
            
        Returns:
            True if trade plan is executable
        """
        self.passes_rr_check = self.levels.risk_reward_ratio >= min_rr
        self.passes_confidence_check = self.confidence >= min_confidence
        self.is_executable = self.passes_rr_check and self.passes_confidence_check
        return self.is_executable


class TradePlanOutput(BaseModel):
    """Output from AI Insight Provider containing multiple trade plans."""
    timestamp: datetime = Field(default_factory=datetime.now)
    plans: List[TradePlan] = Field(default_factory=list)
    executable_count: int = Field(default=0, description="Number of executable plans")
    total_count: int = Field(default=0, description="Total plans generated")
    
    def get_executable_plans(self) -> List[TradePlan]:
        """Get only executable trade plans."""
        return [p for p in self.plans if p.is_executable]
    
    def get_top_plans(self, n: int = 5) -> List[TradePlan]:
        """Get top N plans by confidence score."""
        sorted_plans = sorted(self.plans, key=lambda x: x.confidence, reverse=True)
        return sorted_plans[:n]

