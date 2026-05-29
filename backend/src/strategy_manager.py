"""
Strategy Manager - CRUD operations for trading strategies.
"""
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger

from models import StrategyModel, StrategyStatus


class StrategyManager:
    """
    Manages trading strategies.
    
    Responsibilities:
    - Create/Read/Update/Delete strategies
    - Load/save strategies to MongoDB
    - Enable/disable strategies
    - Validate strategy configurations
    """
    
    def __init__(self, db_collection=None):
        """
        Initialize Strategy Manager.
        
        Args:
            db_collection: MongoDB collection for strategies
        """
        self.db_collection = db_collection
        self.strategies: Dict[str, StrategyModel] = {}
        
        logger.info("⚙️ Strategy Manager initialized")
    
    async def load_strategies(self) -> List[StrategyModel]:
        """Load all strategies from database"""
        if self.db_collection is None:
            logger.warning("No database collection configured")
            return []
        
        try:
            cursor = self.db_collection.find({})
            strategies_data = await cursor.to_list(length=100)
            
            self.strategies.clear()
            for strategy_dict in strategies_data:
                strategy = StrategyModel(**strategy_dict)
                self.strategies[strategy.strategyId] = strategy
            
            logger.info(f"📂 Loaded {len(self.strategies)} strategies from database")
            return list(self.strategies.values())
            
        except Exception as e:
            logger.error(f"❌ Error loading strategies: {e}")
            return []
    
    async def get_strategy(self, strategy_id: str) -> Optional[StrategyModel]:
        """Get a strategy by ID"""
        # Try from cache first
        if strategy_id in self.strategies:
            return self.strategies[strategy_id]

        # Try from database
        if self.db_collection is None:
            return None
        
        try:
            strategy_dict = await self.db_collection.find_one({"strategyId": strategy_id})
            if strategy_dict:
                strategy = StrategyModel(**strategy_dict)
                self.strategies[strategy_id] = strategy
                return strategy
            return None
        except Exception as e:
            logger.error(f"❌ Error getting strategy {strategy_id}: {e}")
            return None
    
    async def create_strategy(self, strategy: StrategyModel) -> bool:
        """Create a new strategy"""
        try:
            # Check if strategy already exists
            if strategy.strategyId in self.strategies:
                logger.warning(f"⚠️ Strategy {strategy.strategyId} already exists")
                return False
            
            # Validate strategy
            if not self._validate_strategy(strategy):
                logger.error(f"❌ Invalid strategy configuration")
                return False
            
            # Set creation time
            strategy.createdAt = datetime.now()
            strategy.updatedAt = datetime.now()
            
            # Save to database
            if self.db_collection is not None:
                strategy_dict = strategy.model_dump()
                await self.db_collection.insert_one(strategy_dict)
            
            # Add to cache
            self.strategies[strategy.strategyId] = strategy
            
            logger.info(f"✅ Created strategy: {strategy.name} ({strategy.strategyId})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating strategy: {e}")
            return False
    
    async def update_strategy(
        self,
        strategy_id: str,
        updates: Dict
    ) -> bool:
        """Update an existing strategy"""
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                logger.warning(f"⚠️ Strategy {strategy_id} not found")
                return False
            
            # Update fields
            for key, value in updates.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
            
            # Update timestamp
            strategy.updatedAt = datetime.now()
            
            # Validate updated strategy
            if not self._validate_strategy(strategy):
                logger.error(f"❌ Invalid strategy configuration after update")
                return False
            
            # Save to database
            if self.db_collection is not None:
                strategy_dict = strategy.model_dump()
                await self.db_collection.update_one(
                    {"strategyId": strategy_id},
                    {"$set": strategy_dict}
                )
            
            # Update cache
            self.strategies[strategy_id] = strategy
            
            logger.info(f"✅ Updated strategy: {strategy.name} ({strategy_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating strategy: {e}")
            return False
    
    async def delete_strategy(self, strategy_id: str) -> bool:
        """Delete a strategy"""
        try:
            # Remove from database
            if self.db_collection is not None:
                result = await self.db_collection.delete_one({"strategyId": strategy_id})
                if result.deleted_count == 0:
                    logger.warning(f"⚠️ Strategy {strategy_id} not found in database")
                    return False
            
            # Remove from cache
            if strategy_id in self.strategies:
                del self.strategies[strategy_id]
            
            logger.info(f"🗑️ Deleted strategy: {strategy_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting strategy: {e}")
            return False
    
    async def toggle_strategy(self, strategy_id: str) -> Optional[StrategyStatus]:
        """Toggle strategy status (ACTIVE <-> PAUSED)"""
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                logger.warning(f"⚠️ Strategy {strategy_id} not found")
                return None
            
            # Toggle status
            if strategy.status == StrategyStatus.ACTIVE:
                new_status = StrategyStatus.PAUSED
            elif strategy.status == StrategyStatus.PAUSED:
                new_status = StrategyStatus.ACTIVE
            else:
                # If DISABLED, activate it
                new_status = StrategyStatus.ACTIVE
            
            # Update strategy
            await self.update_strategy(strategy_id, {"status": new_status})
            
            logger.info(f"🔄 Toggled strategy {strategy.name}: {strategy.status} -> {new_status}")
            return new_status
            
        except Exception as e:
            logger.error(f"❌ Error toggling strategy: {e}")
            return None
    
    async def get_active_strategies(self) -> List[StrategyModel]:
        """Get all active strategies"""
        return [
            strategy for strategy in self.strategies.values()
            if strategy.status == StrategyStatus.ACTIVE
        ]
    
    async def update_strategy_performance(
        self,
        strategy_id: str,
        trade_result: Dict
    ):
        """Update strategy performance metrics after a trade"""
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return
            
            perf = strategy.performance
            
            # Update trade count
            perf.totalTrades += 1
            
            # Update P&L
            pnl = trade_result.get('pnl', 0)
            perf.totalPnl += pnl
            
            # Update win/loss
            if pnl > 0:
                perf.winningTrades += 1
            else:
                perf.losingTrades += 1
            
            # Update win rate
            if perf.totalTrades > 0:
                perf.winRate = (perf.winningTrades / perf.totalTrades) * 100
            
            # Update max win/loss
            if pnl > perf.maxWin:
                perf.maxWin = pnl
            if pnl < perf.maxLoss:
                perf.maxLoss = pnl
            
            # Update average P&L
            perf.avgPnl = perf.totalPnl / perf.totalTrades
            
            # Update last trade time
            perf.lastTradeTime = datetime.now()
            
            # Save to database
            await self.update_strategy(strategy_id, {"performance": perf})
            
            logger.debug(f"📊 Updated performance for {strategy.name}")
            
        except Exception as e:
            logger.error(f"❌ Error updating strategy performance: {e}")
    
    def _validate_strategy(self, strategy: StrategyModel) -> bool:
        """Validate strategy configuration"""
        try:
            # Check required fields
            if not strategy.strategyId or not strategy.name:
                logger.error("Strategy must have ID and name")
                return False
            
            # Validate stock picking config
            if not strategy.stockPicking:
                logger.error("Strategy must have stock picking configuration")
                return False
            
            # Validate execution config
            if not strategy.execution:
                logger.error("Strategy must have execution configuration")
                return False
            
            # Validate risk management
            if not strategy.riskManagement:
                logger.error("Strategy must have risk management configuration")
                return False
            
            # Validate percentages
            if strategy.execution.stopLossPercent <= 0:
                logger.error("Stop loss percent must be positive")
                return False
            
            if strategy.execution.takeProfitPercent <= 0:
                logger.error("Take profit percent must be positive")
                return False
            
            if strategy.riskManagement.maxPositionSizePercent <= 0 or strategy.riskManagement.maxPositionSizePercent > 100:
                logger.error("Max position size must be between 0 and 100")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating strategy: {e}")
            return False
    
    async def get_strategy_summary(self, strategy_id: str) -> Optional[Dict]:
        """Get strategy summary for API/UI"""
        strategy = await self.get_strategy(strategy_id)
        if not strategy:
            return None
        
        return {
            "strategyId": strategy.strategyId,
            "name": strategy.name,
            "description": strategy.description,
            "status": strategy.status.value,
            "stockPickingType": strategy.stockPicking.type.value,
            "executionType": strategy.execution.type.value,
            "performance": {
                "totalTrades": strategy.performance.totalTrades,
                "winRate": strategy.performance.winRate,
                "totalPnl": strategy.performance.totalPnl,
                "avgPnl": strategy.performance.avgPnl
            },
            "createdAt": strategy.createdAt.isoformat() if strategy.createdAt else None,
            "updatedAt": strategy.updatedAt.isoformat() if strategy.updatedAt else None
        }
    
    async def list_strategies_summary(self) -> List[Dict]:
        """Get summary of all strategies"""
        summaries = []
        for strategy_id in self.strategies.keys():
            summary = await self.get_strategy_summary(strategy_id)
            if summary:
                summaries.append(summary)
        return summaries

