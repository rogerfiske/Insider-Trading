"""Tests for MAIA-like scoring with populated transaction details.

Verifies that a ticker with detailed transaction data scores higher than one with
only aggregate metrics, demonstrating the value of populated scoring inputs.
"""

import pytest

from watchlist.scoring import compute_insider_evidence_score


def test_scoring_with_full_details_vs_aggregates_only():
    """Test that detailed metrics produce higher scores than aggregates alone."""
    # Ticker with only aggregate metrics (like pre-fix MAIA)
    aggregate_only = {
        "ticker": "AGGREGATE_ONLY",
        "purchase_count": 134,
        "purchase_value": 4921437.58,
        "sale_count": 0,
        "sale_value": 0.0,
        "net_purchase_value": 4921437.58,
        # Detail fields missing/null
        "distinct_buyers": None,
        "latest_purchase_date": None,
        "buyer_roles": None,
        "purchase_months": None,
        "form4_filings_found": 214,
        "form4_filings_parsed": 0,  # Shows parsing failed
    }

    # Same ticker with populated details (like post-fix MAIA)
    with_details = {
        "ticker": "WITH_DETAILS",
        "purchase_count": 134,
        "purchase_value": 4921437.58,
        "sale_count": 0,
        "sale_value": 0.0,
        "net_purchase_value": 4921437.58,
        # Detail fields populated
        "distinct_buyers": 10,
        "latest_purchase_date": "2026-06-01",
        "buyer_roles": ["Chief Executive Officer", "Chief Financial Officer", "Director"],
        "purchase_months": [
            "2022-07",
            "2022-08",
            "2023-01",
            "2023-02",
            "2024-03",
            "2025-05",
        ],  # 6 months
        "form4_filings_found": 214,
        "form4_filings_parsed": 214,  # Shows parsing succeeded
    }

    score_aggregate = compute_insider_evidence_score("AGGREGATE_ONLY", aggregate_only)
    score_detailed = compute_insider_evidence_score("WITH_DETAILS", with_details)

    # Detailed metrics should score significantly higher
    assert score_detailed.total_score > score_aggregate.total_score
    # Specifically, detailed should have non-zero scores for:
    assert score_detailed.component_scores["buyer_breadth"] > 0
    assert score_detailed.component_scores["recency"] > 0
    assert score_detailed.component_scores["role_quality"] > 0
    assert score_detailed.component_scores["persistence"] > 0
    assert score_detailed.component_scores["data_quality"] > 0

    # Aggregate-only should have zeros for these components
    assert score_aggregate.component_scores["buyer_breadth"] == 0
    assert score_aggregate.component_scores["recency"] == 0
    assert score_aggregate.component_scores["role_quality"] == 0
    assert score_aggregate.component_scores["persistence"] == 0
    assert score_aggregate.component_scores["data_quality"] == 0


def test_maia_scoring_improvement():
    """Test that MAIA-like metrics score in Very Strong range (80-100)."""
    # MAIA-like metrics with all details populated
    maia_like = {
        "ticker": "MAIA_LIKE",
        "purchase_count": 134,
        "purchase_value": 4921437.58,
        "sale_count": 0,
        "sale_value": 0.0,
        "net_purchase_value": 4921437.58,
        "distinct_buyers": 10,
        "latest_purchase_date": "2026-06-01",  # Recent
        "buyer_roles": ["Chief Executive Officer", "Chief Financial Officer", "Chief Scientific Officer", "Director"],
        "purchase_months": [
            "2022-07",
            "2022-08",
            "2022-09",
            "2023-01",
            "2023-02",
            "2023-03",
            "2024-03",
            "2025-05",
        ],  # 8 months (>= 3)
        "form4_filings_found": 214,
        "form4_filings_parsed": 214,
    }

    score = compute_insider_evidence_score("MAIA_LIKE", maia_like)

    # Should score in Very Strong range (80-100)
    assert score.total_score >= 80
    assert score.rating_label == "Very Strong Insider Buying Evidence"

    # Verify all components contribute
    assert score.component_scores["net_buying_value"] == 25  # Perfect
    assert score.component_scores["buy_sell_imbalance"] == 20  # Perfect
    assert score.component_scores["buyer_breadth"] == 15  # Perfect (10+ buyers)
    assert score.component_scores["recency"] > 0  # Should be high (recent date)
    assert score.component_scores["role_quality"] == 10  # Perfect (CEO/CFO)
    assert score.component_scores["persistence"] == 10  # Perfect (>= 3 months)
    assert score.component_scores["data_quality"] == 5  # Perfect (100% parsed)


def test_partial_details_still_improve_score():
    """Test that even partial details improve scores meaningfully."""
    # Base case: only net value
    minimal = {
        "ticker": "MINIMAL",
        "purchase_count": 50,
        "purchase_value": 1000000.0,
        "sale_count": 0,
        "sale_value": 0.0,
        "net_purchase_value": 1000000.0,
        "distinct_buyers": None,
        "latest_purchase_date": None,
        "buyer_roles": None,
        "purchase_months": None,
        "form4_filings_found": 50,
        "form4_filings_parsed": 0,
    }

    # Same but with buyer count only
    with_buyers = {
        **minimal,
        "ticker": "WITH_BUYERS",
        "distinct_buyers": 5,
    }

    # Same but with roles only
    with_roles = {
        **minimal,
        "ticker": "WITH_ROLES",
        "buyer_roles": ["Chief Executive Officer"],
    }

    # Same but with recent date only
    with_recency = {
        **minimal,
        "ticker": "WITH_RECENCY",
        "latest_purchase_date": "2026-06-01",
    }

    score_minimal = compute_insider_evidence_score("MINIMAL", minimal)
    score_buyers = compute_insider_evidence_score("WITH_BUYERS", with_buyers)
    score_roles = compute_insider_evidence_score("WITH_ROLES", with_roles)
    score_recency = compute_insider_evidence_score("WITH_RECENCY", with_recency)

    # Each partial detail should improve the score
    assert score_buyers.total_score > score_minimal.total_score
    assert score_roles.total_score > score_minimal.total_score
    assert score_recency.total_score > score_minimal.total_score


def test_graceful_degradation_with_missing_fields():
    """Test that scoring degrades gracefully when some fields are missing."""
    # Metrics with some fields missing
    partial = {
        "ticker": "PARTIAL",
        "purchase_count": 100,
        "purchase_value": 2000000.0,
        "sale_count": 10,
        "sale_value": 100000.0,
        "net_purchase_value": 1900000.0,
        "distinct_buyers": 3,
        "latest_purchase_date": None,  # Missing
        "buyer_roles": ["Director"],
        "purchase_months": None,  # Missing
        "form4_filings_found": 100,
        "form4_filings_parsed": 95,
    }

    score = compute_insider_evidence_score("PARTIAL", partial)

    # Should still score reasonably
    assert 40 <= score.total_score <= 80

    # Present components should score
    assert score.component_scores["net_buying_value"] > 0
    assert score.component_scores["buy_sell_imbalance"] > 0
    assert score.component_scores["buyer_breadth"] > 0
    assert score.component_scores["role_quality"] > 0
    assert score.component_scores["data_quality"] > 0

    # Missing components should score 0
    assert score.component_scores["recency"] == 0
    assert score.component_scores["persistence"] == 0
