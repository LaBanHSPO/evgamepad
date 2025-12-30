"""
Unit tests for RiskAnalyzer.
Tests position sizing, risk/reward calculations, and risk management functions.
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.advisor.risk_analyzer import RiskAnalyzer, RiskProfile, PROFILE_SETTINGS


class TestRiskAnalyzer:
    """Test suite for RiskAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create RiskAnalyzer instance."""
        return RiskAnalyzer()

    def test_initialization(self, analyzer):
        """Test analyzer initializes correctly."""
        assert analyzer is not None

    def test_get_profile_settings(self, analyzer):
        """Test getting profile settings."""
        # Test valid profiles
        conservative = analyzer.get_profile_settings("conservative")
        assert conservative.risk_per_trade == 0.01
        assert conservative.min_rr_ratio == 3.0

        moderate = analyzer.get_profile_settings("moderate")
        assert moderate.risk_per_trade == 0.02
        assert moderate.min_rr_ratio == 2.0

        aggressive = analyzer.get_profile_settings("aggressive")
        assert aggressive.risk_per_trade == 0.03
        assert aggressive.min_rr_ratio == 1.5

        # Test invalid profile defaults to moderate
        invalid = analyzer.get_profile_settings("invalid")
        assert invalid.risk_per_trade == 0.02

    def test_fixed_fractional_long(self, analyzer):
        """Test fixed fractional position sizing for long trade."""
        result = analyzer.calculate_position_size_fixed_fractional(
            account_balance=10000,
            risk_per_trade=0.02,  # 2%
            entry_price=2100,
            stop_loss=2095
        )

        assert result["method"] == "fixed_fractional"
        assert result["direction"] == "long"
        assert result["risk_amount"] == 200  # 2% of 10000
        assert result["stop_distance"] == 5
        assert result["position_size"] == 40  # 200 / 5
        assert "error" not in result

    def test_fixed_fractional_short(self, analyzer):
        """Test fixed fractional position sizing for short trade."""
        result = analyzer.calculate_position_size_fixed_fractional(
            account_balance=10000,
            risk_per_trade=0.02,
            entry_price=2095,
            stop_loss=2100
        )

        assert result["direction"] == "short"
        assert result["risk_amount"] == 200
        assert result["stop_distance"] == 5
        assert result["position_size"] == 40

    def test_fixed_fractional_validation(self, analyzer):
        """Test validation errors in fixed fractional."""
        # Negative balance
        result = analyzer.calculate_position_size_fixed_fractional(
            account_balance=-100,
            risk_per_trade=0.02,
            entry_price=2100,
            stop_loss=2095
        )
        assert "error" in result

        # Invalid risk percentage
        result = analyzer.calculate_position_size_fixed_fractional(
            account_balance=10000,
            risk_per_trade=0.15,  # 15% too high
            entry_price=2100,
            stop_loss=2095
        )
        assert "error" in result

        # Same entry and stop
        result = analyzer.calculate_position_size_fixed_fractional(
            account_balance=10000,
            risk_per_trade=0.02,
            entry_price=2100,
            stop_loss=2100
        )
        assert "error" in result

    def test_kelly_criterion_positive(self, analyzer):
        """Test Kelly criterion with positive expectancy."""
        result = analyzer.calculate_position_size_kelly(
            account_balance=10000,
            win_rate=0.6,  # 60%
            avg_win=150,
            avg_loss=100,
            entry_price=2100,
            stop_loss=2095,
            kelly_fraction=0.5
        )

        assert result["method"] == "kelly"
        assert result["win_rate"] == 0.6
        assert result["win_loss_ratio"] == 1.5
        assert result["expected_value"] > 0  # Positive expectancy
        assert result["position_size"] > 0
        assert "error" not in result

    def test_kelly_criterion_negative(self, analyzer):
        """Test Kelly criterion with negative expectancy (losing strategy)."""
        result = analyzer.calculate_position_size_kelly(
            account_balance=10000,
            win_rate=0.3,  # 30%
            avg_win=100,
            avg_loss=150,
            entry_price=2100,
            stop_loss=2095,
            kelly_fraction=0.5
        )

        assert result["method"] == "kelly"
        assert result["position_size"] == 0
        assert result["recommendation"] == "Negative expectancy - DO NOT TRADE"
        assert result["kelly_raw"] < 0

    def test_kelly_validation(self, analyzer):
        """Test validation errors in Kelly criterion."""
        # Invalid win rate
        result = analyzer.calculate_position_size_kelly(
            account_balance=10000,
            win_rate=1.5,  # Invalid
            avg_win=100,
            avg_loss=100,
            entry_price=2100,
            stop_loss=2095
        )
        assert "error" in result

        # Negative average win/loss
        result = analyzer.calculate_position_size_kelly(
            account_balance=10000,
            win_rate=0.5,
            avg_win=-100,
            avg_loss=100,
            entry_price=2100,
            stop_loss=2095
        )
        assert "error" in result

    def test_atr_based_sizing(self, analyzer):
        """Test ATR-based position sizing."""
        result = analyzer.calculate_position_size_atr_based(
            account_balance=10000,
            risk_per_trade=0.02,
            entry_price=2100,
            atr=10,
            atr_multiplier=1.5
        )

        assert result["method"] == "atr_based"
        assert result["atr"] == 10
        assert result["atr_multiplier"] == 1.5
        assert result["stop_distance"] == 15  # 10 * 1.5
        assert result["risk_amount"] == 200  # 2% of 10000
        assert result["position_size"] == pytest.approx(13.33, rel=0.01)  # 200 / 15
        assert result["stop_loss_long"] == 2085  # 2100 - 15
        assert result["stop_loss_short"] == 2115  # 2100 + 15

    def test_atr_validation(self, analyzer):
        """Test validation errors in ATR-based sizing."""
        # Negative ATR
        result = analyzer.calculate_position_size_atr_based(
            account_balance=10000,
            risk_per_trade=0.02,
            entry_price=2100,
            atr=-10
        )
        assert "error" in result

    def test_calculate_stop_loss_long_atr(self, analyzer):
        """Test stop loss calculation for long position using ATR."""
        result = analyzer.calculate_stop_loss(
            entry_price=2100,
            direction="long",
            atr=10,
            atr_multiplier=1.5
        )

        assert result["direction"] == "long"
        assert "atr" in result["methods"]
        assert result["methods"]["atr"]["stop_loss"] == 2085  # 2100 - 15
        assert result["methods"]["atr"]["distance"] == 15

    def test_calculate_stop_loss_with_sr(self, analyzer):
        """Test stop loss calculation with S/R level."""
        result = analyzer.calculate_stop_loss(
            entry_price=2100,
            direction="long",
            atr=10,
            atr_multiplier=1.5,
            nearest_sr=2090
        )

        assert "atr" in result["methods"]
        assert "support_resistance" in result["methods"]
        assert result["methods"]["support_resistance"]["sr_level"] == 2090
        assert result["recommended"] is not None

    def test_risk_reward_long(self, analyzer):
        """Test risk/reward calculation for long position."""
        result = analyzer.calculate_risk_reward(
            entry_price=2100,
            stop_loss=2095,
            take_profit=2115
        )

        assert result["direction"] == "long"
        assert result["risk"] == 5  # 2100 - 2095
        assert result["reward"] == 15  # 2115 - 2100
        assert result["rr_ratio"] == 3.0  # 15 / 5
        assert result["recommendation"] == "excellent"
        assert "breakeven_win_rate" in result

    def test_risk_reward_short(self, analyzer):
        """Test risk/reward calculation for short position."""
        result = analyzer.calculate_risk_reward(
            entry_price=2100,
            stop_loss=2105,
            take_profit=2085
        )

        assert result["direction"] == "short"
        assert result["risk"] == 5  # 2105 - 2100
        assert result["reward"] == 15  # 2100 - 2085
        assert result["rr_ratio"] == 3.0

    def test_risk_reward_poor_ratio(self, analyzer):
        """Test risk/reward with poor ratio."""
        result = analyzer.calculate_risk_reward(
            entry_price=2100,
            stop_loss=2095,
            take_profit=2103  # Only 3 points reward
        )

        assert result["rr_ratio"] == 0.6  # 3 / 5
        assert result["recommendation"] == "poor"

    def test_analyze_full_risk_conservative(self, analyzer):
        """Test full risk analysis with conservative profile."""
        result = analyzer.analyze_full_risk(
            account_balance=10000,
            entry_price=2100,
            stop_loss=2095,
            take_profit=2115,
            risk_profile="conservative",
            atr=10
        )

        assert result["risk_profile"] == "conservative"
        assert result["profile_settings"]["risk_per_trade"] == 1  # 1%
        assert "risk_reward" in result
        assert "position_sizing" in result
        assert "fixed_fractional" in result["position_sizing"]
        assert "atr_based" in result["position_sizing"]
        assert "recommendation" in result
        assert result["recommendation"]["action"] == "trade"  # R/R is 3.0, meets minimum

    def test_analyze_full_risk_insufficient_rr(self, analyzer):
        """Test full risk analysis with insufficient R/R ratio."""
        result = analyzer.analyze_full_risk(
            account_balance=10000,
            entry_price=2100,
            stop_loss=2095,
            take_profit=2105,  # Only 1:1 R/R
            risk_profile="conservative"  # Requires 3:1 minimum
        )

        assert result["recommendation"]["action"] == "adjust_targets"
        assert "R/R ratio" in result["recommendation"]["reason"]

    def test_analyze_full_risk_with_kelly(self, analyzer):
        """Test full risk analysis including Kelly criterion."""
        result = analyzer.analyze_full_risk(
            account_balance=10000,
            entry_price=2100,
            stop_loss=2095,
            take_profit=2115,
            risk_profile="moderate",
            win_rate=0.6,
            avg_win=150,
            avg_loss=100
        )

        assert "kelly" in result["position_sizing"]
        assert result["position_sizing"]["kelly"]["win_rate"] == 0.6

    def test_enforce_limits(self, analyzer):
        """Test position size limit enforcement."""
        # Create scenario where position size would be very large
        result = analyzer.calculate_position_size_fixed_fractional(
            account_balance=10000,
            risk_per_trade=0.02,
            entry_price=2100,
            stop_loss=2099.5,  # Very tight stop
            enforce_limits=True
        )

        # With 0.5 stop distance and 200 risk amount, position would be 400
        # But it should be capped at 10% of account = 1000
        assert "position_size" in result
        if result.get("limit_exceeded"):
            assert result["position_size"] <= 1000

    def test_profile_settings_values(self):
        """Test all risk profile settings are correct."""
        conservative = PROFILE_SETTINGS[RiskProfile.CONSERVATIVE]
        assert conservative.risk_per_trade == 0.01
        assert conservative.max_daily_drawdown == 0.03
        assert conservative.max_weekly_drawdown == 0.05
        assert conservative.atr_stop_multiplier == 2.0
        assert conservative.min_rr_ratio == 3.0

        moderate = PROFILE_SETTINGS[RiskProfile.MODERATE]
        assert moderate.risk_per_trade == 0.02
        assert moderate.max_daily_drawdown == 0.05
        assert moderate.max_weekly_drawdown == 0.07
        assert moderate.atr_stop_multiplier == 1.5
        assert moderate.min_rr_ratio == 2.0

        aggressive = PROFILE_SETTINGS[RiskProfile.AGGRESSIVE]
        assert aggressive.risk_per_trade == 0.03
        assert aggressive.max_daily_drawdown == 0.07
        assert aggressive.max_weekly_drawdown == 0.10
        assert aggressive.atr_stop_multiplier == 1.0
        assert aggressive.min_rr_ratio == 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
