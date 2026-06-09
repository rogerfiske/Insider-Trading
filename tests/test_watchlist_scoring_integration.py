"""Integration tests for watchlist scoring with full workflow."""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from watchlist.scoring import compute_insider_evidence_score


def test_scoring_integrates_with_metrics_extraction():
    """Test that scoring works with typical metrics structure."""
    # Simulate metrics from extract_ticker_metrics()
    now = datetime.now(timezone.utc)
    recent_date = (now - timedelta(days=20)).isoformat()

    metrics = {
        "ticker": "TEST",
        "company_name": "Test Corp",
        "purchase_value": 500000.0,
        "sale_value": 0.0,
        "purchase_count": 25,
        "sale_count": 0,
        "distinct_buyers": 4,
        "latest_purchase_date": recent_date,
        "buyer_roles": ["CEO", "Director"],
        "purchase_months": ["2024-01", "2024-06", "2025-01"],
        "form4_filings_found": 50,
        "form4_filings_parsed": 48,
    }

    score = compute_insider_evidence_score("TEST", metrics)

    # Verify score object structure
    assert score.ticker == "TEST"
    assert 0 <= score.total_score <= 100
    assert score.rating_label in [
        "Very Strong Insider Buying Evidence",
        "Strong Insider Buying Evidence",
        "Moderate Insider Buying Evidence",
        "Weak Insider Buying Evidence",
        "Little/No Insider Buying Evidence",
    ]
    assert len(score.component_scores) == 7
    assert len(score.component_explanations) == 7


def test_scoring_handles_minimal_metrics():
    """Test scoring with minimal required fields only."""
    minimal_metrics = {
        "ticker": "MIN",
        "purchase_value": 50000.0,
        "sale_value": 10000.0,
        "purchase_count": 5,
        "sale_count": 1,
        "form4_filings_found": 20,
        "form4_filings_parsed": 18,
        # Missing: distinct_buyers, latest_purchase_date, buyer_roles, purchase_months
    }

    score = compute_insider_evidence_score("MIN", minimal_metrics)

    # Should still produce a score
    assert score.ticker == "MIN"
    assert score.total_score > 0  # Net buying value + imbalance + data quality should contribute
    assert len(score.warnings) > 0  # Should warn about missing fields
    assert "distinct_buyers field missing" in score.warnings
    assert "latest_purchase_date field missing" in score.warnings


def test_scoring_to_dict_serializes_correctly():
    """Test that score.to_dict() produces clean JSON-serializable output."""
    now = datetime.now(timezone.utc)
    recent_date = (now - timedelta(days=10)).isoformat()

    metrics = {
        "ticker": "JSON",
        "purchase_value": 1000000.0,
        "sale_value": 0.0,
        "purchase_count": 50,
        "sale_count": 0,
        "distinct_buyers": 5,
        "latest_purchase_date": recent_date,
        "buyer_roles": ["CEO"],
        "purchase_months": ["2024-01", "2024-06", "2025-01"],
        "form4_filings_found": 100,
        "form4_filings_parsed": 98,
    }

    score = compute_insider_evidence_score("JSON", metrics)
    score_dict = score.to_dict()

    # Verify structure
    assert "ticker" in score_dict
    assert "total_score" in score_dict
    assert "rating_label" in score_dict
    assert "component_scores" in score_dict
    assert "component_explanations" in score_dict
    assert "warnings" in score_dict

    # Verify types
    assert isinstance(score_dict["ticker"], str)
    assert isinstance(score_dict["total_score"], (int, float))
    assert isinstance(score_dict["rating_label"], str)
    assert isinstance(score_dict["component_scores"], dict)
    assert isinstance(score_dict["component_explanations"], dict)
    assert isinstance(score_dict["warnings"], list)

    # Verify all component scores are rounded to 2 decimals
    for component, points in score_dict["component_scores"].items():
        assert isinstance(points, (int, float))
        assert points == round(points, 2)


def test_scoring_ranks_strong_buying_higher():
    """Test that strong buying patterns score higher than weak ones."""
    now = datetime.now(timezone.utc)
    recent_date = (now - timedelta(days=10)).isoformat()

    # Strong buying pattern
    strong_metrics = {
        "ticker": "STRONG",
        "purchase_value": 2000000.0,
        "sale_value": 0.0,
        "purchase_count": 100,
        "sale_count": 0,
        "distinct_buyers": 6,
        "latest_purchase_date": recent_date,
        "buyer_roles": ["CEO", "CFO", "Director"],
        "purchase_months": ["2023-01", "2024-01", "2024-06", "2025-01"],
        "form4_filings_found": 200,
        "form4_filings_parsed": 200,
    }

    # Weak buying pattern
    weak_metrics = {
        "ticker": "WEAK",
        "purchase_value": 10000.0,
        "sale_value": 5000.0,
        "purchase_count": 2,
        "sale_count": 1,
        "distinct_buyers": 1,
        "latest_purchase_date": None,
        "buyer_roles": None,
        "purchase_months": None,
        "form4_filings_found": 10,
        "form4_filings_parsed": 5,
    }

    strong_score = compute_insider_evidence_score("STRONG", strong_metrics)
    weak_score = compute_insider_evidence_score("WEAK", weak_metrics)

    # Strong should score much higher
    assert strong_score.total_score > weak_score.total_score
    assert strong_score.total_score >= 80  # Should be Very Strong
    assert weak_score.total_score < 40  # Should be Weak or lower


def test_scoring_components_sum_correctly():
    """Test that component scores sum to total_score."""
    now = datetime.now(timezone.utc)
    recent_date = (now - timedelta(days=15)).isoformat()

    metrics = {
        "ticker": "SUM",
        "purchase_value": 750000.0,
        "sale_value": 0.0,
        "purchase_count": 40,
        "sale_count": 0,
        "distinct_buyers": 4,
        "latest_purchase_date": recent_date,
        "buyer_roles": ["CEO", "Director"],
        "purchase_months": ["2024-01", "2024-06", "2025-01"],
        "form4_filings_found": 80,
        "form4_filings_parsed": 76,
    }

    score = compute_insider_evidence_score("SUM", metrics)

    # Sum all component scores
    component_sum = sum(score.component_scores.values())

    # Should match total_score (allowing for small floating-point differences)
    assert abs(score.total_score - component_sum) < 0.01


def test_zero_purchases_scores_zero():
    """Test that zero purchases yields zero score."""
    metrics = {
        "ticker": "ZERO",
        "purchase_value": 0.0,
        "sale_value": 100000.0,
        "purchase_count": 0,
        "sale_count": 10,
        "distinct_buyers": 0,
        "latest_purchase_date": None,
        "buyer_roles": None,
        "purchase_months": None,
        "form4_filings_found": 20,
        "form4_filings_parsed": 18,
    }

    score = compute_insider_evidence_score("ZERO", metrics)

    # Should score very low (only data quality might contribute)
    assert score.total_score < 10
    assert "Weak" in score.rating_label or "Little" in score.rating_label


def test_scoring_preserves_ticker_identity():
    """Test that ticker identity is preserved through scoring."""
    metrics = {
        "ticker": "PRESERVE",
        "purchase_value": 100000.0,
        "sale_value": 0.0,
        "purchase_count": 10,
        "sale_count": 0,
        "form4_filings_found": 30,
        "form4_filings_parsed": 28,
    }

    score = compute_insider_evidence_score("PRESERVE", metrics)

    assert score.ticker == "PRESERVE"
    score_dict = score.to_dict()
    assert score_dict["ticker"] == "PRESERVE"


def test_scoring_component_explanations_not_empty():
    """Test that all component explanations are populated."""
    metrics = {
        "ticker": "EXPLAIN",
        "purchase_value": 250000.0,
        "sale_value": 50000.0,
        "purchase_count": 15,
        "sale_count": 3,
        "distinct_buyers": 3,
        "latest_purchase_date": datetime.now(timezone.utc).isoformat(),
        "buyer_roles": ["Director"],
        "purchase_months": ["2024-06", "2025-01"],
        "form4_filings_found": 40,
        "form4_filings_parsed": 38,
    }

    score = compute_insider_evidence_score("EXPLAIN", metrics)

    # All 7 components should have explanations
    assert len(score.component_explanations) == 7

    for component, explanation in score.component_explanations.items():
        assert isinstance(explanation, str)
        assert len(explanation) > 0


def test_scoring_rating_labels_match_thresholds():
    """Test that rating labels correctly map to score ranges."""
    # Very Strong: 80-100
    very_strong_metrics = {
        "ticker": "VS",
        "purchase_value": 2000000.0,
        "sale_value": 0.0,
        "purchase_count": 100,
        "sale_count": 0,
        "distinct_buyers": 6,
        "latest_purchase_date": datetime.now(timezone.utc).isoformat(),
        "buyer_roles": ["CEO"],
        "purchase_months": ["2024-01", "2024-06", "2025-01"],
        "form4_filings_found": 100,
        "form4_filings_parsed": 100,
    }
    vs_score = compute_insider_evidence_score("VS", very_strong_metrics)
    assert vs_score.total_score >= 80
    assert vs_score.rating_label == "Very Strong Insider Buying Evidence"

    # Weak: 20-39
    weak_metrics = {
        "ticker": "WK",
        "purchase_value": 20000.0,
        "sale_value": 10000.0,
        "purchase_count": 3,
        "sale_count": 2,
        "distinct_buyers": 1,
        "latest_purchase_date": None,
        "buyer_roles": None,
        "purchase_months": None,
        "form4_filings_found": 10,
        "form4_filings_parsed": 5,
    }
    weak_score = compute_insider_evidence_score("WK", weak_metrics)
    assert 20 <= weak_score.total_score < 40
    assert weak_score.rating_label == "Weak Insider Buying Evidence"
