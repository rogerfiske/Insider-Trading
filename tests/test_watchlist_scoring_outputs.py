"""Tests for watchlist scoring output format validation."""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from watchlist.scoring import compute_insider_evidence_score


def test_score_dict_has_required_keys():
    """Test that score dict contains all required keys."""
    metrics = {
        "ticker": "KEYS",
        "purchase_value": 100000.0,
        "sale_value": 0.0,
        "purchase_count": 10,
        "sale_count": 0,
        "form4_filings_found": 30,
        "form4_filings_parsed": 28,
    }

    score = compute_insider_evidence_score("KEYS", metrics)
    score_dict = score.to_dict()

    required_keys = [
        "ticker",
        "total_score",
        "rating_label",
        "component_scores",
        "component_explanations",
        "warnings",
    ]

    for key in required_keys:
        assert key in score_dict, f"Missing required key: {key}"


def test_component_scores_dict_has_all_components():
    """Test that component_scores contains all 7 components."""
    metrics = {
        "ticker": "COMP",
        "purchase_value": 500000.0,
        "sale_value": 0.0,
        "purchase_count": 25,
        "sale_count": 0,
        "distinct_buyers": 4,
        "latest_purchase_date": datetime.now(timezone.utc).isoformat(),
        "buyer_roles": ["CEO"],
        "purchase_months": ["2024-01", "2025-01"],
        "form4_filings_found": 50,
        "form4_filings_parsed": 48,
    }

    score = compute_insider_evidence_score("COMP", metrics)

    expected_components = [
        "net_buying_value",
        "buy_sell_imbalance",
        "buyer_breadth",
        "recency",
        "role_quality",
        "persistence",
        "data_quality",
    ]

    for component in expected_components:
        assert component in score.component_scores, f"Missing component: {component}"
        assert component in score.component_explanations, f"Missing explanation: {component}"


def test_total_score_is_numeric():
    """Test that total_score is a valid number."""
    metrics = {
        "ticker": "NUM",
        "purchase_value": 250000.0,
        "sale_value": 50000.0,
        "purchase_count": 15,
        "sale_count": 3,
        "form4_filings_found": 40,
        "form4_filings_parsed": 38,
    }

    score = compute_insider_evidence_score("NUM", metrics)

    assert isinstance(score.total_score, (int, float))
    assert score.total_score >= 0
    assert score.total_score <= 100


def test_rating_label_is_valid_string():
    """Test that rating_label is one of the expected values."""
    metrics = {
        "ticker": "LABEL",
        "purchase_value": 100000.0,
        "sale_value": 0.0,
        "purchase_count": 10,
        "sale_count": 0,
        "form4_filings_found": 30,
        "form4_filings_parsed": 28,
    }

    score = compute_insider_evidence_score("LABEL", metrics)

    valid_labels = [
        "Very Strong Insider Buying Evidence",
        "Strong Insider Buying Evidence",
        "Moderate Insider Buying Evidence",
        "Weak Insider Buying Evidence",
        "Little/No Insider Buying Evidence",
    ]

    assert score.rating_label in valid_labels


def test_component_scores_are_numeric():
    """Test that all component scores are numeric."""
    metrics = {
        "ticker": "NUMCOMP",
        "purchase_value": 750000.0,
        "sale_value": 0.0,
        "purchase_count": 40,
        "sale_count": 0,
        "distinct_buyers": 5,
        "latest_purchase_date": datetime.now(timezone.utc).isoformat(),
        "buyer_roles": ["CEO", "Director"],
        "purchase_months": ["2024-01", "2024-06", "2025-01"],
        "form4_filings_found": 80,
        "form4_filings_parsed": 76,
    }

    score = compute_insider_evidence_score("NUMCOMP", metrics)

    for component, points in score.component_scores.items():
        assert isinstance(points, (int, float))
        assert points >= 0


def test_component_explanations_are_strings():
    """Test that all component explanations are strings."""
    metrics = {
        "ticker": "STREXP",
        "purchase_value": 300000.0,
        "sale_value": 100000.0,
        "purchase_count": 20,
        "sale_count": 5,
        "distinct_buyers": 3,
        "latest_purchase_date": datetime.now(timezone.utc).isoformat(),
        "buyer_roles": ["Director"],
        "purchase_months": ["2024-06", "2025-01"],
        "form4_filings_found": 50,
        "form4_filings_parsed": 45,
    }

    score = compute_insider_evidence_score("STREXP", metrics)

    for component, explanation in score.component_explanations.items():
        assert isinstance(explanation, str)
        assert len(explanation) > 0


def test_warnings_is_list():
    """Test that warnings field is a list."""
    metrics = {
        "ticker": "WARN",
        "purchase_value": 50000.0,
        "sale_value": 0.0,
        "purchase_count": 5,
        "sale_count": 0,
        "form4_filings_found": 20,
        "form4_filings_parsed": 18,
        # Missing optional fields will generate warnings
    }

    score = compute_insider_evidence_score("WARN", metrics)

    assert isinstance(score.warnings, list)
    for warning in score.warnings:
        assert isinstance(warning, str)


def test_score_dict_is_json_serializable():
    """Test that score dict can be JSON serialized."""
    import json

    metrics = {
        "ticker": "JSON",
        "purchase_value": 1000000.0,
        "sale_value": 0.0,
        "purchase_count": 50,
        "sale_count": 0,
        "distinct_buyers": 5,
        "latest_purchase_date": datetime.now(timezone.utc).isoformat(),
        "buyer_roles": ["CEO"],
        "purchase_months": ["2024-01", "2024-06", "2025-01"],
        "form4_filings_found": 100,
        "form4_filings_parsed": 98,
    }

    score = compute_insider_evidence_score("JSON", metrics)
    score_dict = score.to_dict()

    # Should not raise exception
    json_str = json.dumps(score_dict)
    assert isinstance(json_str, str)

    # Should round-trip correctly
    parsed = json.loads(json_str)
    assert parsed["ticker"] == "JSON"
    assert parsed["total_score"] == score_dict["total_score"]


def test_scores_are_rounded_to_two_decimals():
    """Test that all scores are rounded to 2 decimal places in dict."""
    metrics = {
        "ticker": "ROUND",
        "purchase_value": 333333.33,
        "sale_value": 111111.11,
        "purchase_count": 17,
        "sale_count": 3,
        "distinct_buyers": 3,
        "latest_purchase_date": datetime.now(timezone.utc).isoformat(),
        "buyer_roles": ["Director"],
        "purchase_months": ["2024-06", "2025-01"],
        "form4_filings_found": 47,
        "form4_filings_parsed": 43,
    }

    score = compute_insider_evidence_score("ROUND", metrics)
    score_dict = score.to_dict()

    # Check total_score
    total_str = str(score_dict["total_score"])
    if "." in total_str:
        decimals = len(total_str.split(".")[1])
        assert decimals <= 2, f"total_score has {decimals} decimals: {score_dict['total_score']}"

    # Check component scores
    for component, points in score_dict["component_scores"].items():
        points_str = str(points)
        if "." in points_str:
            decimals = len(points_str.split(".")[1])
            assert decimals <= 2, f"{component} has {decimals} decimals: {points}"


def test_ticker_field_matches_input():
    """Test that ticker field in output matches input ticker."""
    input_ticker = "MATCH"
    metrics = {
        "ticker": input_ticker,
        "purchase_value": 150000.0,
        "sale_value": 0.0,
        "purchase_count": 12,
        "sale_count": 0,
        "form4_filings_found": 35,
        "form4_filings_parsed": 33,
    }

    score = compute_insider_evidence_score(input_ticker, metrics)

    assert score.ticker == input_ticker
    assert score.to_dict()["ticker"] == input_ticker


def test_zero_score_has_valid_output():
    """Test that zero score produces valid output structure."""
    metrics = {
        "ticker": "ZERO",
        "purchase_value": 0.0,
        "sale_value": 100000.0,
        "purchase_count": 0,
        "sale_count": 10,
        "form4_filings_found": 20,
        "form4_filings_parsed": 18,
    }

    score = compute_insider_evidence_score("ZERO", metrics)
    score_dict = score.to_dict()

    # Should have all required fields even with zero score
    assert "ticker" in score_dict
    assert "total_score" in score_dict
    assert "rating_label" in score_dict
    assert "component_scores" in score_dict
    assert "component_explanations" in score_dict
    assert "warnings" in score_dict


def test_perfect_score_has_valid_output():
    """Test that perfect 100 score produces valid output."""
    metrics = {
        "ticker": "PERFECT",
        "purchase_value": 2000000.0,
        "sale_value": 0.0,
        "purchase_count": 100,
        "sale_count": 0,
        "distinct_buyers": 6,
        "latest_purchase_date": datetime.now(timezone.utc).isoformat(),
        "buyer_roles": ["CEO"],
        "purchase_months": ["2023-01", "2024-01", "2024-06", "2025-01"],
        "form4_filings_found": 200,
        "form4_filings_parsed": 200,
    }

    score = compute_insider_evidence_score("PERFECT", metrics)
    score_dict = score.to_dict()

    assert score_dict["total_score"] == 100.0
    assert score_dict["rating_label"] == "Very Strong Insider Buying Evidence"
    assert len(score_dict["warnings"]) == 0


def test_output_consistent_across_calls():
    """Test that same input produces same output across multiple calls."""
    metrics = {
        "ticker": "CONSISTENT",
        "purchase_value": 500000.0,
        "sale_value": 100000.0,
        "purchase_count": 25,
        "sale_count": 5,
        "distinct_buyers": 4,
        "latest_purchase_date": "2025-01-15T12:00:00+00:00",
        "buyer_roles": ["CEO", "Director"],
        "purchase_months": ["2024-01", "2024-06", "2025-01"],
        "form4_filings_found": 75,
        "form4_filings_parsed": 70,
    }

    score1 = compute_insider_evidence_score("CONSISTENT", metrics)
    score2 = compute_insider_evidence_score("CONSISTENT", metrics)

    dict1 = score1.to_dict()
    dict2 = score2.to_dict()

    assert dict1 == dict2


def test_component_names_are_snake_case():
    """Test that component keys use snake_case naming."""
    metrics = {
        "ticker": "SNAKE",
        "purchase_value": 250000.0,
        "sale_value": 0.0,
        "purchase_count": 15,
        "sale_count": 0,
        "distinct_buyers": 3,
        "latest_purchase_date": datetime.now(timezone.utc).isoformat(),
        "buyer_roles": ["Director"],
        "purchase_months": ["2024-06", "2025-01"],
        "form4_filings_found": 50,
        "form4_filings_parsed": 48,
    }

    score = compute_insider_evidence_score("SNAKE", metrics)

    # Check component_scores keys
    for component in score.component_scores.keys():
        # Should be snake_case (lowercase with underscores)
        assert component.islower() or "_" in component
        assert " " not in component

    # Check component_explanations keys
    for component in score.component_explanations.keys():
        assert component.islower() or "_" in component
        assert " " not in component
