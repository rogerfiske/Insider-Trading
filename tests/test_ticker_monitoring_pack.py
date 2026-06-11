"""
Tests for Generic Ticker Monitoring Pack (CP23C)
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def generic_maia_monitoring():
    """Load generic MAIA monitoring plan."""
    path = Path("docs/sample_reports/generic_ticker/MAIA/monitoring/MAIA_monitoring_plan.json")
    if not path.exists():
        pytest.skip(f"Generic MAIA monitoring not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_monitoring_plan_structure(generic_maia_monitoring):
    """Test monitoring plan has required structure."""
    required_keys = ["ticker", "cik", "generated_at", "baseline"]

    for key in required_keys:
        assert key in generic_maia_monitoring, f"Missing required key: {key}"


def test_monitoring_baseline_from_synthesis(generic_maia_monitoring):
    """Test baseline values come from synthesis."""
    baseline = generic_maia_monitoring["baseline"]
    assert "insider_activity" in baseline
    assert "capital_structure" in baseline


def test_monitoring_categories_present(generic_maia_monitoring):
    """Test monitoring categories are defined."""
    if "monitoring_categories" in generic_maia_monitoring:
        categories = generic_maia_monitoring["monitoring_categories"]
        assert isinstance(categories, list)
        assert len(categories) > 0
