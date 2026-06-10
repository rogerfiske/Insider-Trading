"""Tests for cash runway sensitivity analysis (CP23B).

Tests verify runway calculations across low/base/high scenarios.
"""

from __future__ import annotations

from datetime import datetime
import pytest
from scripts.maia_clinical_runway_research import calculate_cash_runway


def test_runway_calculation_base_scenario():
    """Test base scenario runway calculation."""
    result = calculate_cash_runway(
        cash_balance=40_000_000,
        quarterly_burn=10_000_000,
        scenario="base"
    )

    assert result["scenario"] == "base"
    assert result["quarterly_burn"] == 10_000_000
    assert result["monthly_burn"] == pytest.approx(3_333_333.33, rel=1e-2)
    assert result["cash_balance"] == 40_000_000
    assert result["runway_months"] == pytest.approx(12.0, rel=1e-1)
    assert "assumptions" in result
    assert "estimated_depletion_date" in result


def test_runway_calculation_low_scenario():
    """Test low (conservative) scenario with 85% of base burn."""
    result = calculate_cash_runway(
        cash_balance=40_000_000,
        quarterly_burn=10_000_000,
        scenario="low"
    )

    assert result["scenario"] == "low"
    assert result["quarterly_burn"] == 8_500_000  # 85% of base
    assert result["monthly_burn"] == pytest.approx(2_833_333.33, rel=1e-2)
    assert result["runway_months"] > 12.0  # Lower burn = longer runway


def test_runway_calculation_high_scenario():
    """Test high (Phase 3 ramp-up) scenario with 130% of base burn."""
    result = calculate_cash_runway(
        cash_balance=40_000_000,
        quarterly_burn=10_000_000,
        scenario="high"
    )

    assert result["scenario"] == "high"
    assert result["quarterly_burn"] == 13_000_000  # 130% of base
    assert result["monthly_burn"] == pytest.approx(4_333_333.33, rel=1e-2)
    assert result["runway_months"] < 12.0  # Higher burn = shorter runway


def test_runway_scenarios_ordering():
    """Test that low/base/high scenarios are properly ordered."""
    cash = 40_000_000
    burn = 10_000_000

    low = calculate_cash_runway(cash, burn, "low")
    base = calculate_cash_runway(cash, burn, "base")
    high = calculate_cash_runway(cash, burn, "high")

    # Runway should decrease from low -> base -> high
    assert low["runway_months"] > base["runway_months"]
    assert base["runway_months"] > high["runway_months"]

    # Burn should increase from low -> base -> high
    assert low["quarterly_burn"] < base["quarterly_burn"]
    assert base["quarterly_burn"] < high["quarterly_burn"]


def test_runway_with_low_cash():
    """Test runway calculation with low cash balance."""
    result = calculate_cash_runway(
        cash_balance=5_000_000,
        quarterly_burn=10_000_000,
        scenario="base"
    )

    # Should have very short runway (<2 quarters)
    assert result["runway_months"] < 6.0


def test_runway_with_zero_burn():
    """Test runway calculation handles zero burn gracefully."""
    result = calculate_cash_runway(
        cash_balance=40_000_000,
        quarterly_burn=0,
        scenario="base"
    )

    # Zero burn should result in zero runway (can't calculate)
    assert result["runway_months"] == 0


def test_runway_estimated_depletion_date_format():
    """Test that depletion date is in correct format."""
    result = calculate_cash_runway(
        cash_balance=40_000_000,
        quarterly_burn=10_000_000,
        scenario="base"
    )

    # Should be YYYY-MM-DD format
    depletion_date = result["estimated_depletion_date"]
    datetime.strptime(depletion_date, "%Y-%m-%d")  # Will raise if format wrong


def test_runway_with_march_2026_financing():
    """Test runway using actual March 2026 financing data from CP23A-Fix."""
    # March 2026 offering: ~$28M base, ~$32.3M with overallotment
    # Assume $10M quarterly burn (placeholder)

    base_result = calculate_cash_runway(
        cash_balance=28_000_000,
        quarterly_burn=10_000_000,
        scenario="base"
    )

    with_overallotment = calculate_cash_runway(
        cash_balance=32_300_000,
        quarterly_burn=10_000_000,
        scenario="base"
    )

    # With overallotment should have longer runway
    assert with_overallotment["runway_months"] > base_result["runway_months"]

    # Base case should be ~8.4 months
    assert base_result["runway_months"] == pytest.approx(8.4, rel=0.1)

    # With overallotment should be ~9.7 months
    assert with_overallotment["runway_months"] == pytest.approx(9.7, rel=0.1)


def test_runway_phase_3_escalation():
    """Test that high scenario represents realistic Phase 3 cost escalation."""
    result_high = calculate_cash_runway(
        cash_balance=40_000_000,
        quarterly_burn=10_000_000,
        scenario="high"
    )

    # High scenario should be 30% higher burn
    assert result_high["quarterly_burn"] == 13_000_000

    # With $40M cash and $13M quarterly burn, runway should be ~9.2 months
    assert result_high["runway_months"] == pytest.approx(9.2, rel=0.1)
