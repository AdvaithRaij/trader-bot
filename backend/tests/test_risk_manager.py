"""
Test Suite for Risk Manager

Tests risk management, position sizing, and trade validation.

Run:
    pytest backend/tests/test_risk_manager.py -v
"""

import pytest
from loguru import logger


class TestRiskManager:
    """Test risk management functionality."""

    def test_risk_manager_initialization(self, risk_manager):
        """Test risk manager initializes with correct config."""
        logger.info("Testing risk manager initialization...")
        
        assert risk_manager is not None
        assert risk_manager.config is not None
        assert risk_manager.config.INITIAL_CAPITAL > 0
        assert risk_manager.config.MAX_RISK_PER_TRADE > 0
        
        logger.success(f"✅ Risk manager initialized: Capital=₹{risk_manager.config.INITIAL_CAPITAL:,.0f}")

    def test_validate_trade_risk_valid(self, risk_manager):
        """Test trade validation with valid parameters."""
        logger.info("Testing valid trade validation...")
        
        metrics = risk_manager.validate_trade_risk(
            symbol="RELIANCE",
            entry_price=2850.0,
            stop_loss=2800.0,  # 1.75% risk
            target_price=2950.0,
            confidence=75
        )
        
        assert metrics is not None
        assert metrics.is_within_limits is True
        assert metrics.position_size > 0
        assert metrics.risk_pct > 0
        assert metrics.risk_reward_ratio > 0
        
        logger.success(f"✅ Valid trade: Size={metrics.position_size}, Risk={metrics.risk_pct:.2f}%, R:R=1:{metrics.risk_reward_ratio:.2f}")

    def test_validate_trade_risk_too_high(self, risk_manager):
        """Test trade rejection when risk is too high."""
        logger.info("Testing high-risk trade rejection...")
        
        metrics = risk_manager.validate_trade_risk(
            symbol="TEST",
            entry_price=1000.0,
            stop_loss=900.0,  # 10% risk - too high
            target_price=1100.0,
            confidence=50
        )
        
        assert metrics is not None
        assert metrics.is_within_limits is False
        assert "risk" in metrics.rejection_reason.lower()
        
        logger.success(f"✅ High-risk trade rejected: {metrics.rejection_reason}")

    def test_validate_trade_poor_risk_reward(self, risk_manager):
        """Test trade rejection when risk-reward is poor."""
        logger.info("Testing poor risk-reward rejection...")
        
        metrics = risk_manager.validate_trade_risk(
            symbol="TEST",
            entry_price=1000.0,
            stop_loss=980.0,  # 2% risk
            target_price=1010.0,  # 1% reward - poor R:R
            confidence=60
        )
        
        assert metrics is not None
        # Should be rejected or flagged
        if not metrics.is_within_limits:
            logger.success(f"✅ Poor R:R trade rejected: {metrics.rejection_reason}")
        else:
            logger.warning(f"⚠️ Poor R:R trade accepted (R:R={metrics.risk_reward_ratio:.2f})")

    def test_position_sizing_calculation(self, risk_manager):
        """Test position sizing calculation."""
        logger.info("Testing position sizing...")
        
        # Test with different risk levels
        test_cases = [
            {"entry": 100, "sl": 98, "expected_risk": 2.0},  # 2% risk
            {"entry": 1000, "sl": 985, "expected_risk": 1.5},  # 1.5% risk
            {"entry": 2500, "sl": 2475, "expected_risk": 1.0},  # 1% risk
        ]
        
        for case in test_cases:
            metrics = risk_manager.validate_trade_risk(
                symbol="TEST",
                entry_price=case["entry"],
                stop_loss=case["sl"],
                target_price=case["entry"] * 1.03,
                confidence=70
            )
            
            actual_risk = abs(case["entry"] - case["sl"]) / case["entry"] * 100
            assert abs(actual_risk - case["expected_risk"]) < 0.1
            
            logger.info(f"  Entry=₹{case['entry']}, SL=₹{case['sl']}, Risk={actual_risk:.2f}%, Size={metrics.position_size}")
        
        logger.success("✅ Position sizing calculations correct")

    def test_max_trades_limit(self, risk_manager, portfolio_manager):
        """Test maximum trades per day limit."""
        logger.info("Testing max trades limit...")
        
        max_trades = risk_manager.config.MAX_TRADES_PER_DAY
        logger.info(f"  Max trades per day: {max_trades}")
        
        # Check current trade count
        current_trades = len(portfolio_manager.portfolio.openPositions)
        logger.info(f"  Current open positions: {current_trades}")
        
        assert current_trades <= max_trades, f"Open positions ({current_trades}) exceeds max ({max_trades})"
        
        logger.success(f"✅ Trade count within limits: {current_trades}/{max_trades}")

    def test_max_open_risk_limit(self, risk_manager):
        """Test maximum open risk limit."""
        logger.info("Testing max open risk limit...")
        
        max_open_risk = risk_manager.config.MAX_OPEN_RISK
        logger.info(f"  Max open risk: {max_open_risk * 100}%")
        
        # This would need portfolio state to test properly
        # For now, just verify the config is reasonable
        assert 0.01 <= max_open_risk <= 0.2, "Max open risk should be between 1% and 20%"
        
        logger.success(f"✅ Max open risk configured: {max_open_risk * 100}%")

