"""
Tests for Generic Ticker Market Confirmation (CP23C)
"""

import csv
import json
import pytest
from pathlib import Path


@pytest.fixture
def generic_maia_market_confirmation():
    """Load generic MAIA market confirmation plan."""
    path = Path("docs/sample_reports/generic_ticker/MAIA/market_confirmation/MAIA_market_confirmation_plan.json")
    if not path.exists():
        pytest.skip(f"Generic MAIA market confirmation not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_market_confirmation_structure(generic_maia_market_confirmation):
    """Test market confirmation has required structure."""
    required_keys = ["ticker", "cik", "purpose", "baseline", "reference_levels", "weekly_checklist"]

    for key in required_keys:
        assert key in generic_maia_market_confirmation, f"Missing required key: {key}"


def test_reference_price_documented(generic_maia_market_confirmation):
    """Test reference price levels are documented."""
    levels = generic_maia_market_confirmation["reference_levels"]
    assert isinstance(levels, list)
    assert len(levels) > 0


def test_csv_observation_template_exists():
    """Test CSV observation template was created."""
    path = Path("docs/sample_reports/generic_ticker/MAIA/market_confirmation/MAIA_market_observation_template.csv")
    assert path.exists(), "CSV observation template not found"

    # Verify CSV has required headers
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

        required_headers = ["Date", "Closing_Price_USD", "Daily_Volume"]

        for header in required_headers:
            assert header in headers, f"Missing required CSV header: {header}"
