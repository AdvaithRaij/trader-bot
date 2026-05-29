"""
Pipeline Orchestrator - Implements the 3-stage trading pipeline from PLAN_OF_ACTION.md.

Pipeline Stages:
1. Stock Screener → Top 10 candidates with scores
2. AI Insight Provider → Trade plans with entry/SL/targets
3. Trade Executor → Live orders with risk validation

Cycles:
- Screening Cycle: Every 10 minutes during market hours
- Monitoring Cycle: Every 1 minute for open positions
- EOD Cycle: Square off at 3:15 PM
"""
import asyncio
from datetime import datetime, time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from config import get_config
from screener import StockScreener
from ai_insight_provider import AIInsightProvider
from trade_executor import TradeExecutor
from data_aggregator import DataAggregator
from multi_strategy_analyzer import MultiStrategyAnalyzer
from models.screener import ScreenerOutput
from models.trade_plan import TradePlanOutput, MultiStrategyOutput

config = get_config()


class PipelineState(Enum):
    """Pipeline state machine states."""
    IDLE = "idle"
    SCREENING = "screening"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    SQUARING_OFF = "squaring_off"
    STOPPED = "stopped"


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics."""
    screening_runs: int = 0
    candidates_found: int = 0
    plans_generated: int = 0
    trades_executed: int = 0
    trades_successful: int = 0
    total_pnl: float = 0.0
    last_screening_time: Optional[datetime] = None
    last_execution_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)


class PipelineOrchestrator:
    """
    Main orchestrator for the 3-stage trading pipeline.
    
    Implements PLAN_OF_ACTION.md architecture:
    - Stage 1: Stock Screener (every 10 min)
    - Stage 2: AI Insight Provider (on screener output)
    - Stage 3: Trade Executor (with risk validation)
    
    Features:
    - State machine for pipeline control
    - Configurable cycle intervals
    - WebSocket event emission
    - Comprehensive error handling
    - Metrics tracking
    """
    
    # Market hours (IST)
    MARKET_OPEN = time(9, 15)
    MARKET_CLOSE = time(15, 30)
    LAST_ENTRY = time(14, 30)
    EOD_SQUARE_OFF = time(15, 15)
    
    # Cycle intervals (seconds)
    SCREENING_INTERVAL = 600  # 10 minutes
    MONITORING_INTERVAL = 60  # 1 minute
    
    def __init__(
        self,
        screener: Optional[StockScreener] = None,
        insight_provider: Optional[AIInsightProvider] = None,
        executor: Optional[TradeExecutor] = None,
        data_aggregator: Optional[DataAggregator] = None,
        multi_strategy_analyzer: Optional[MultiStrategyAnalyzer] = None,
        broker=None,
        news_aggregator=None,
        websocket_manager=None
    ):
        """
        Initialize Pipeline Orchestrator.

        Args:
            screener: Stock screener instance
            insight_provider: AI insight provider instance
            executor: Trade executor instance
            data_aggregator: Data aggregator for multi-strategy analysis
            multi_strategy_analyzer: Multi-strategy analyzer instance
            broker: Broker instance for market data
            news_aggregator: News aggregator for sentiment data
            websocket_manager: WebSocket manager for events
        """
        self.screener = screener or StockScreener()
        self.insight_provider = insight_provider or AIInsightProvider()
        self.executor = executor or TradeExecutor(broker=broker)
        self.broker = broker
        self.news_aggregator = news_aggregator
        self.ws_manager = websocket_manager

        # Multi-strategy analysis components
        self.data_aggregator = data_aggregator or DataAggregator(
            broker=broker,
            news_aggregator=news_aggregator,
            screener=self.screener
        )
        self.multi_strategy_analyzer = multi_strategy_analyzer or MultiStrategyAnalyzer()

        # State management
        self.state = PipelineState.IDLE
        self.is_running = False
        self.metrics = PipelineMetrics()

        # Tasks
        self.screening_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.eod_task: Optional[asyncio.Task] = None

        # Latest outputs
        self.latest_screener_output: Optional[ScreenerOutput] = None
        self.latest_trade_plans: Optional[TradePlanOutput] = None
        self.latest_multi_strategy_output: Optional[MultiStrategyOutput] = None

        # Account equity (should be fetched from broker)
        self.equity = config.INITIAL_CAPITAL

        logger.info("🚀 Pipeline Orchestrator initialized")
    
    def _is_market_hours(self) -> bool:
        """Check if current time is within market hours."""
        now = datetime.now().time()
        return self.MARKET_OPEN <= now <= self.MARKET_CLOSE
    
    def _can_enter_trades(self) -> bool:
        """Check if new trades can be entered."""
        now = datetime.now().time()
        return self.MARKET_OPEN <= now <= self.LAST_ENTRY
    
    def _should_square_off(self) -> bool:
        """Check if it's time for EOD square off."""
        now = datetime.now().time()
        return now >= self.EOD_SQUARE_OFF
    
    async def _emit_event(self, event_type: str, data: Dict):
        """Emit WebSocket event."""
        if self.ws_manager:
            try:
                await self.ws_manager.broadcast({
                    "type": event_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to emit event: {e}")
    
    async def _update_equity(self):
        """Update account equity from broker."""
        if self.broker:
            try:
                margin = await self.broker.get_available_margin()
                if margin > 0:
                    self.equity = margin
            except Exception as e:
                logger.warning(f"Failed to update equity: {e}")

    async def run_screening_cycle(self) -> Optional[ScreenerOutput]:
        """
        Run Stage 1: Stock Screening.

        Returns:
            ScreenerOutput with top candidates
        """
        try:
            self.state = PipelineState.SCREENING
            logger.info("📊 Stage 1: Running stock screener...")

            # Run screener
            output = await self.screener.screen_stocks()

            self.latest_screener_output = output
            self.metrics.screening_runs += 1
            self.metrics.candidates_found += len(output.candidates)
            self.metrics.last_screening_time = datetime.now()

            # Emit event
            await self._emit_event("screening_complete", {
                "candidates": len(output.candidates),
                "market_context": output.market_context.model_dump() if output.market_context else None
            })

            logger.info(f"✅ Screening complete: {len(output.candidates)} candidates")
            return output

        except Exception as e:
            logger.error(f"❌ Screening cycle failed: {e}")
            self.metrics.errors.append(f"Screening: {e}")
            return None

    async def run_analysis_cycle(self, screener_output: ScreenerOutput) -> Optional[TradePlanOutput]:
        """
        Run Stage 2: AI Analysis.

        Args:
            screener_output: Output from Stage 1

        Returns:
            TradePlanOutput with trade plans
        """
        try:
            self.state = PipelineState.ANALYZING
            logger.info("🤖 Stage 2: Running AI analysis...")

            # Generate trade plans
            output = await self.insight_provider.generate_trade_plans(screener_output)

            self.latest_trade_plans = output
            self.metrics.plans_generated += len(output.plans)

            # Emit event
            await self._emit_event("analysis_complete", {
                "plans": len(output.plans),
                "executable": output.executable_count
            })

            logger.info(f"✅ Analysis complete: {len(output.plans)} plans, {output.executable_count} executable")
            return output

        except Exception as e:
            logger.error(f"❌ Analysis cycle failed: {e}")
            self.metrics.errors.append(f"Analysis: {e}")
            return None

    async def run_multi_strategy_analysis(
        self,
        screener_output: Optional[ScreenerOutput] = None
    ) -> Optional[MultiStrategyOutput]:
        """
        Run multi-strategy analysis on screened candidates.

        This is an enhanced Stage 2 that uses:
        1. DataAggregator to fetch complete data (fundamentals, news, technicals)
        2. MultiStrategyAnalyzer to run 3 parallel strategy analyses

        Args:
            screener_output: Optional screener output (uses latest if not provided)

        Returns:
            MultiStrategyOutput with all analyses
        """
        try:
            self.state = PipelineState.ANALYZING
            logger.info("🎯 Running multi-strategy analysis...")

            # Use provided or latest screener output
            output = screener_output or self.latest_screener_output
            if not output or not output.candidates:
                logger.warning("No screener candidates available for multi-strategy analysis")
                return None

            # Get symbols from top candidates
            symbols = [c.symbol for c in output.candidates[:10]]

            # Aggregate complete data
            stock_data = await self.data_aggregator.get_batch_stock_data(
                symbols=symbols,
                screener_candidates=output.candidates[:10]
            )

            if not stock_data:
                logger.warning("No stock data aggregated")
                return None

            # Run multi-strategy analysis
            analysis_output = await self.multi_strategy_analyzer.analyze_batch(stock_data)

            self.latest_multi_strategy_output = analysis_output

            # Emit event
            await self._emit_event("multi_strategy_complete", {
                "total_analyzed": analysis_output.total_analyzed,
                "duration_ms": analysis_output.analysis_duration_ms
            })

            logger.info(f"✅ Multi-strategy analysis complete: {analysis_output.total_analyzed} stocks analyzed")
            return analysis_output

        except Exception as e:
            logger.error(f"❌ Multi-strategy analysis failed: {e}")
            self.metrics.errors.append(f"MultiStrategy: {e}")
            return None

    async def generate_plan_for_symbol(self, symbol: str):
        """
        Generate a trade plan for a specific symbol.

        Uses the latest screener output to find the candidate and generate a plan.

        Args:
            symbol: Stock symbol to generate plan for

        Returns:
            TradePlan if successful, None otherwise
        """
        try:
            # Find candidate from latest screener output
            if not self.latest_screener_output:
                logger.warning(f"No screener output available for {symbol}")
                return None

            candidate = None
            for c in self.latest_screener_output.candidates:
                if c.symbol == symbol:
                    candidate = c
                    break

            if not candidate:
                logger.warning(f"Symbol {symbol} not found in screener candidates")
                return None

            # Generate plan using AI insight provider
            market_context = self.latest_screener_output.market_context
            plan = await self.insight_provider.generate_single_plan(candidate, market_context)

            if plan:
                # Store in latest output
                if not self.latest_trade_plans:
                    self.latest_trade_plans = TradePlanOutput(plans=[plan])
                else:
                    # Check if plan already exists
                    existing = next((i for i, p in enumerate(self.latest_trade_plans.plans)
                                     if p.symbol == symbol), None)
                    if existing is not None:
                        self.latest_trade_plans.plans[existing] = plan
                    else:
                        self.latest_trade_plans.plans.append(plan)

                self.metrics.plans_generated += 1
                logger.info(f"✅ Generated plan for {symbol}: {plan.direction} @ {plan.levels.entry}")

            return plan

        except Exception as e:
            logger.error(f"❌ Failed to generate plan for {symbol}: {e}")
            return None

    async def run_execution_cycle(self, trade_plans: TradePlanOutput) -> List[Dict]:
        """
        Run Stage 3: Trade Execution.

        Args:
            trade_plans: Output from Stage 2

        Returns:
            List of execution results
        """
        try:
            self.state = PipelineState.EXECUTING
            logger.info("⚡ Stage 3: Executing trades...")

            # Update equity before execution
            await self._update_equity()

            # Execute plans
            results = await self.executor.execute_plans(trade_plans, self.equity)

            # Update metrics
            for result in results:
                self.metrics.trades_executed += 1
                if result.success:
                    self.metrics.trades_successful += 1

            self.metrics.last_execution_time = datetime.now()

            # Emit event
            await self._emit_event("execution_complete", {
                "executed": len(results),
                "successful": sum(1 for r in results if r.success)
            })

            logger.info(f"✅ Execution complete: {sum(1 for r in results if r.success)}/{len(results)} successful")
            return [{"symbol": r.symbol, "success": r.success, "order_id": r.order_id} for r in results]

        except Exception as e:
            logger.error(f"❌ Execution cycle failed: {e}")
            self.metrics.errors.append(f"Execution: {e}")
            return []

    async def run_full_pipeline(self) -> Dict:
        """
        Run the complete 3-stage pipeline.

        Returns:
            Pipeline run summary
        """
        start_time = datetime.now()

        try:
            # Check market hours
            if not self._is_market_hours():
                logger.info("⏰ Outside market hours, skipping pipeline")
                return {"status": "skipped", "reason": "outside_market_hours"}

            # Stage 1: Screening
            screener_output = await self.run_screening_cycle()
            if not screener_output or not screener_output.candidates:
                return {"status": "no_candidates", "stage": 1}

            # Stage 2: Analysis
            trade_plans = await self.run_analysis_cycle(screener_output)
            if not trade_plans or not trade_plans.plans:
                return {"status": "no_plans", "stage": 2}

            # Check if we can still enter trades
            if not self._can_enter_trades():
                logger.info("⏰ Past last entry time, skipping execution")
                return {"status": "skipped", "reason": "past_last_entry", "plans": len(trade_plans.plans)}

            # Stage 3: Execution
            results = await self.run_execution_cycle(trade_plans)

            duration = (datetime.now() - start_time).total_seconds()

            return {
                "status": "complete",
                "duration_seconds": duration,
                "candidates": len(screener_output.candidates),
                "plans": len(trade_plans.plans),
                "executed": len(results),
                "successful": sum(1 for r in results if r.get("success"))
            }

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            self.state = PipelineState.MONITORING

    async def start(self):
        """Start the pipeline orchestrator."""
        if self.is_running:
            logger.warning("Pipeline already running")
            return

        self.is_running = True
        self.state = PipelineState.IDLE

        # Start screening loop
        self.screening_task = asyncio.create_task(self._screening_loop())

        # Start monitoring loop
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        # Start EOD check loop
        self.eod_task = asyncio.create_task(self._eod_loop())

        logger.info("🚀 Pipeline Orchestrator started")

        await self._emit_event("pipeline_started", {"timestamp": datetime.now().isoformat()})

    async def stop(self):
        """Stop the pipeline orchestrator."""
        self.is_running = False
        self.state = PipelineState.STOPPED

        # Cancel tasks
        for task in [self.screening_task, self.monitoring_task, self.eod_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("🛑 Pipeline Orchestrator stopped")

        await self._emit_event("pipeline_stopped", {"metrics": self.get_metrics()})

    async def _screening_loop(self):
        """Screening cycle loop - runs every 10 minutes."""
        logger.info("⏰ Screening loop started (10-min interval)")

        while self.is_running:
            try:
                if self._is_market_hours() and self._can_enter_trades():
                    await self.run_full_pipeline()

                await asyncio.sleep(self.SCREENING_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Screening loop error: {e}")
                await asyncio.sleep(60)

    async def _monitoring_loop(self):
        """Monitoring cycle loop - runs every 1 minute."""
        logger.info("👁️ Monitoring loop started (1-min interval)")

        while self.is_running:
            try:
                if self._is_market_hours():
                    # Update positions and check exits
                    # This is handled by the execution engine's monitoring
                    pass

                await asyncio.sleep(self.MONITORING_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)

    async def _eod_loop(self):
        """EOD square-off check loop."""
        logger.info("🔒 EOD loop started")

        while self.is_running:
            try:
                if self._should_square_off():
                    self.state = PipelineState.SQUARING_OFF
                    logger.info("🔒 EOD Square-off triggered")

                    results = await self.executor.square_off_all()

                    await self._emit_event("eod_square_off", {
                        "positions_closed": len(results)
                    })

                    # Wait until next day
                    await asyncio.sleep(3600)  # 1 hour

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"EOD loop error: {e}")
                await asyncio.sleep(60)

    def get_metrics(self) -> Dict:
        """Get pipeline metrics."""
        return {
            "state": self.state.value,
            "screening_runs": self.metrics.screening_runs,
            "candidates_found": self.metrics.candidates_found,
            "plans_generated": self.metrics.plans_generated,
            "trades_executed": self.metrics.trades_executed,
            "trades_successful": self.metrics.trades_successful,
            "success_rate": (
                self.metrics.trades_successful / self.metrics.trades_executed * 100
                if self.metrics.trades_executed > 0 else 0
            ),
            "total_pnl": self.metrics.total_pnl,
            "last_screening": self.metrics.last_screening_time.isoformat() if self.metrics.last_screening_time else None,
            "last_execution": self.metrics.last_execution_time.isoformat() if self.metrics.last_execution_time else None,
            "errors": self.metrics.errors[-10:]  # Last 10 errors
        }

    def get_status(self) -> Dict:
        """Get current pipeline status."""
        return {
            "is_running": self.is_running,
            "state": self.state.value,
            "market_hours": self._is_market_hours(),
            "can_enter_trades": self._can_enter_trades(),
            "should_square_off": self._should_square_off(),
            "equity": self.equity,
            "latest_candidates": len(self.latest_screener_output.candidates) if self.latest_screener_output else 0,
            "latest_plans": len(self.latest_trade_plans.plans) if self.latest_trade_plans else 0
        }

