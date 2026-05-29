"""
Seed default trading strategies into the database.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

from config import get_config
from models import (
    StrategyModel,
    StockPickingConfig,
    ExecutionConfig,
    RiskManagementConfig,
    StrategyPerformance,
    StockPickingType,
    ExecutionType,
    StrategyStatus
)
from strategy_manager import StrategyManager

config = get_config()


async def create_default_strategies():
    """Create default trading strategies"""
    
    strategies = []
    
    # Strategy 1: News Momentum (High Impact Positive News)
    news_momentum = StrategyModel(
        strategyId="news_momentum_v1",
        name="News-Driven Momentum",
        description="Trades stocks with high-impact positive news. Targets 5% profit with 2% stop loss.",
        stockPicking=StockPickingConfig(
            type=StockPickingType.NEWS_BASED,
            newsFilters={
                "impact": "HIGH",
                "sentiment": "POSITIVE",
                "relevance": ">=80",
                "timeframe": ["IMMEDIATE", "SHORT_TERM"]
            },
            maxStocks=5
        ),
        execution=ExecutionConfig(
            type=ExecutionType.AI_ASSISTED,
            entryCondition="AI-suggested entry price",
            stopLossPercent=2.0,
            takeProfitPercent=5.0,
            useTrailingStop=False,
            useMultipleTargets=True,
            exitAtEOD=True,
            eodExitTime="15:15",
            useAILevels=True
        ),
        riskManagement=RiskManagementConfig(
            maxPositionSizePercent=20.0,
            maxDailyLossPercent=5.0,
            maxDrawdownPercent=10.0,
            maxOpenPositions=5
        ),
        status=StrategyStatus.ACTIVE,
        performance=StrategyPerformance()
    )
    strategies.append(news_momentum)
    
    # Strategy 2: Conservative News Trading
    conservative_news = StrategyModel(
        strategyId="conservative_news_v1",
        name="Conservative News Trading",
        description="Conservative approach with medium-high impact news. Lower risk with 1.5% stop loss and 3% target.",
        stockPicking=StockPickingConfig(
            type=StockPickingType.NEWS_BASED,
            newsFilters={
                "impact": ["HIGH", "MEDIUM"],
                "sentiment": "POSITIVE",
                "relevance": ">=70"
            },
            maxStocks=3
        ),
        execution=ExecutionConfig(
            type=ExecutionType.AI_ASSISTED,
            entryCondition="AI-suggested entry price",
            stopLossPercent=1.5,
            takeProfitPercent=3.0,
            useTrailingStop=True,
            trailingStopPercent=1.0,
            useMultipleTargets=False,
            exitAtEOD=True,
            eodExitTime="15:15",
            useAILevels=True
        ),
        riskManagement=RiskManagementConfig(
            maxPositionSizePercent=15.0,
            maxDailyLossPercent=3.0,
            maxDrawdownPercent=8.0,
            maxOpenPositions=3
        ),
        status=StrategyStatus.PAUSED,  # Start paused
        performance=StrategyPerformance()
    )
    strategies.append(conservative_news)
    
    # Strategy 3: Aggressive News Scalping
    aggressive_scalp = StrategyModel(
        strategyId="aggressive_scalp_v1",
        name="Aggressive News Scalping",
        description="Quick scalps on immediate high-impact news. Higher risk with 3% stop loss and 8% target.",
        stockPicking=StockPickingConfig(
            type=StockPickingType.NEWS_BASED,
            newsFilters={
                "impact": "HIGH",
                "sentiment": "POSITIVE",
                "relevance": ">=85",
                "timeframe": "IMMEDIATE"
            },
            maxStocks=2
        ),
        execution=ExecutionConfig(
            type=ExecutionType.AI_ASSISTED,
            entryCondition="AI-suggested entry price",
            stopLossPercent=3.0,
            takeProfitPercent=8.0,
            useTrailingStop=True,
            trailingStopPercent=2.0,
            useMultipleTargets=True,
            exitAtEOD=True,
            eodExitTime="15:00",  # Exit earlier for scalping
            useAILevels=True
        ),
        riskManagement=RiskManagementConfig(
            maxPositionSizePercent=25.0,
            maxDailyLossPercent=5.0,
            maxDrawdownPercent=10.0,
            maxOpenPositions=2
        ),
        status=StrategyStatus.PAUSED,  # Start paused
        performance=StrategyPerformance()
    )
    strategies.append(aggressive_scalp)
    
    return strategies


async def seed_database():
    """Seed strategies into MongoDB"""
    
    logger.info("🌱 Seeding default strategies...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(config.MONGODB_URL)
        db = client[config.MONGODB_DATABASE]
        strategies_collection = db.strategies
        
        # Create strategy manager
        strategy_manager = StrategyManager(db_collection=strategies_collection)
        
        # Create default strategies
        default_strategies = await create_default_strategies()
        
        # Seed each strategy
        for strategy in default_strategies:
            # Check if already exists
            existing = await strategies_collection.find_one({"strategyId": strategy.strategyId})
            
            if existing:
                logger.info(f"⏭️  Strategy already exists: {strategy.name}")
            else:
                success = await strategy_manager.create_strategy(strategy)
                if success:
                    logger.info(f"✅ Created strategy: {strategy.name} ({strategy.strategyId})")
                else:
                    logger.error(f"❌ Failed to create strategy: {strategy.name}")
        
        # List all strategies
        all_strategies = await strategy_manager.load_strategies()
        logger.info(f"\n📊 Total strategies in database: {len(all_strategies)}")
        
        for strategy in all_strategies:
            status_emoji = "✅" if strategy.status == StrategyStatus.ACTIVE else "⏸️"
            logger.info(
                f"{status_emoji} {strategy.name} ({strategy.strategyId}) - {strategy.status.value}"
            )
        
        logger.info("\n🎉 Seeding complete!")
        
        # Close connection
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error seeding strategies: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(seed_database())

