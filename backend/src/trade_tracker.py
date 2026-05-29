"""
Trade Tracker - Tracks trade history and calculates performance metrics.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

from models import TradeModel, TradeStatus


class TradeTracker:
    """
    Tracks trade history and calculates performance analytics.
    
    Responsibilities:
    - Query trade history from database
    - Calculate performance metrics (win rate, avg P&L, Sharpe ratio)
    - Generate daily/weekly/monthly reports
    - Strategy-wise performance comparison
    """
    
    def __init__(self, db_collection=None):
        """
        Initialize Trade Tracker.
        
        Args:
            db_collection: MongoDB collection for trades
        """
        self.db_collection = db_collection
        logger.info("📊 Trade Tracker initialized")
    
    async def get_trade_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None,
        status: Optional[TradeStatus] = None,
        limit: int = 100
    ) -> List[TradeModel]:
        """
        Get trade history with filters.
        
        Args:
            start_date: Filter trades after this date
            end_date: Filter trades before this date
            strategy_id: Filter by strategy
            symbol: Filter by symbol
            status: Filter by status
            limit: Max number of trades to return
        
        Returns:
            List of TradeModel objects
        """
        if not self.db_collection:
            return []
        
        try:
            # Build query
            query = {}
            
            if start_date or end_date:
                query["entryTime"] = {}
                if start_date:
                    query["entryTime"]["$gte"] = start_date
                if end_date:
                    query["entryTime"]["$lte"] = end_date
            
            if strategy_id:
                query["strategyId"] = strategy_id
            
            if symbol:
                query["symbol"] = symbol
            
            if status:
                query["status"] = status.value
            
            # Execute query
            cursor = self.db_collection.find(query).sort("entryTime", -1).limit(limit)
            trades_data = await cursor.to_list(length=limit)
            
            trades = [TradeModel(**trade_dict) for trade_dict in trades_data]
            
            logger.info(f"📂 Retrieved {len(trades)} trades from history")
            return trades
            
        except Exception as e:
            logger.error(f"❌ Error getting trade history: {e}")
            return []
    
    async def get_closed_trades(
        self,
        days: Optional[int] = None,
        strategy_id: Optional[str] = None
    ) -> List[TradeModel]:
        """Get closed trades for performance analysis"""
        start_date = None
        if days:
            start_date = datetime.now() - timedelta(days=days)
        
        return await self.get_trade_history(
            start_date=start_date,
            strategy_id=strategy_id,
            status=TradeStatus.CLOSED,
            limit=1000
        )
    
    async def calculate_performance_metrics(
        self,
        trades: List[TradeModel]
    ) -> Dict:
        """
        Calculate performance metrics from trades.
        
        Args:
            trades: List of closed trades
        
        Returns:
            Dictionary with performance metrics
        """
        if not trades:
            return {
                "totalTrades": 0,
                "winningTrades": 0,
                "losingTrades": 0,
                "winRate": 0.0,
                "totalPnl": 0.0,
                "avgPnl": 0.0,
                "avgWin": 0.0,
                "avgLoss": 0.0,
                "maxWin": 0.0,
                "maxLoss": 0.0,
                "profitFactor": 0.0,
                "avgHoldingTime": "0h 0m"
            }
        
        # Filter only closed trades with P&L
        closed_trades = [t for t in trades if t.status == TradeStatus.CLOSED and t.pnl is not None]
        
        if not closed_trades:
            return {"totalTrades": 0}
        
        # Calculate metrics
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in closed_trades)
        total_wins = sum(t.pnl for t in winning_trades)
        total_losses = abs(sum(t.pnl for t in losing_trades))
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        avg_win = total_wins / len(winning_trades) if winning_trades else 0
        avg_loss = total_losses / len(losing_trades) if losing_trades else 0
        
        max_win = max((t.pnl for t in winning_trades), default=0)
        max_loss = min((t.pnl for t in losing_trades), default=0)
        
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Calculate average holding time
        holding_times = []
        for trade in closed_trades:
            if trade.exitTime and trade.entryTime:
                duration = trade.exitTime - trade.entryTime
                holding_times.append(duration.total_seconds())
        
        avg_holding_seconds = sum(holding_times) / len(holding_times) if holding_times else 0
        avg_holding_hours = int(avg_holding_seconds // 3600)
        avg_holding_minutes = int((avg_holding_seconds % 3600) // 60)
        
        return {
            "totalTrades": total_trades,
            "winningTrades": len(winning_trades),
            "losingTrades": len(losing_trades),
            "winRate": round(win_rate, 2),
            "totalPnl": round(total_pnl, 2),
            "avgPnl": round(avg_pnl, 2),
            "avgWin": round(avg_win, 2),
            "avgLoss": round(avg_loss, 2),
            "maxWin": round(max_win, 2),
            "maxLoss": round(max_loss, 2),
            "profitFactor": round(profit_factor, 2),
            "avgHoldingTime": f"{avg_holding_hours}h {avg_holding_minutes}m"
        }
    
    async def get_strategy_performance(
        self,
        strategy_id: str,
        days: Optional[int] = None
    ) -> Dict:
        """Get performance metrics for a specific strategy"""
        trades = await self.get_closed_trades(days=days, strategy_id=strategy_id)
        return await self.calculate_performance_metrics(trades)
    
    async def get_daily_performance(
        self,
        days: int = 30
    ) -> List[Dict]:
        """
        Get daily performance breakdown.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            List of daily performance dictionaries
        """
        start_date = datetime.now() - timedelta(days=days)
        trades = await self.get_closed_trades(days=days)
        
        # Group trades by date
        daily_trades = {}
        for trade in trades:
            if trade.exitTime:
                date_key = trade.exitTime.date().isoformat()
                if date_key not in daily_trades:
                    daily_trades[date_key] = []
                daily_trades[date_key].append(trade)
        
        # Calculate daily metrics
        daily_performance = []
        for date_key in sorted(daily_trades.keys()):
            day_trades = daily_trades[date_key]
            metrics = await self.calculate_performance_metrics(day_trades)
            metrics["date"] = date_key
            daily_performance.append(metrics)
        
        return daily_performance
    
    async def get_symbol_performance(self) -> List[Dict]:
        """Get performance breakdown by symbol"""
        trades = await self.get_closed_trades()
        
        # Group by symbol
        symbol_trades = {}
        for trade in trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)
        
        # Calculate metrics per symbol
        symbol_performance = []
        for symbol, trades_list in symbol_trades.items():
            metrics = await self.calculate_performance_metrics(trades_list)
            metrics["symbol"] = symbol
            symbol_performance.append(metrics)
        
        # Sort by total P&L
        symbol_performance.sort(key=lambda x: x.get("totalPnl", 0), reverse=True)
        
        return symbol_performance
    
    async def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trades for display"""
        trades = await self.get_trade_history(limit=limit)
        
        return [
            {
                "tradeId": trade.tradeId,
                "symbol": trade.symbol,
                "direction": trade.direction.value,
                "entryTime": trade.entryTime.isoformat(),
                "entryPrice": trade.entryPrice,
                "exitTime": trade.exitTime.isoformat() if trade.exitTime else None,
                "exitPrice": trade.exitPrice,
                "quantity": trade.quantity,
                "pnl": trade.pnl,
                "pnlPercent": trade.pnlPercent,
                "status": trade.status.value,
                "exitReason": trade.exitReason.value if trade.exitReason else None,
                "strategyName": trade.strategyName
            }
            for trade in trades
        ]
    
    async def get_trade_by_id(self, trade_id: str) -> Optional[TradeModel]:
        """Get a specific trade by ID"""
        if not self.db_collection:
            return None
        
        try:
            trade_dict = await self.db_collection.find_one({"tradeId": trade_id})
            if trade_dict:
                return TradeModel(**trade_dict)
            return None
        except Exception as e:
            logger.error(f"❌ Error getting trade by ID: {e}")
            return None

