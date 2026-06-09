"""Tests for watchlist insider evidence scoring logic."""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from watchlist.scoring import (
    compute_net_buying_value_score,
    compute_buy_sell_imbalance_score,
    compute_distinct_buyer_breadth_score,
    compute_recency_score,
    compute_role_quality_score,
    compute_persistence_score,
    compute_data_quality_score,
    get_rating_label,
    compute_insider_evidence_score,
)


def test_net_buying_value_score_tiers():
    """Test net buying value score tier thresholds."""
    # No net buying
    score, _ = compute_net_buying_value_score(0, 0)
    assert score == 0.0

    # $1-$25k tier
    score, _ = compute_net_buying_value_score(10000, 0)
    assert score == 5.0

    # $25k-$100k tier
    score, _ = compute_net_buying_value_score(50000, 0)
    assert score == 10.0

    # $100k-$500k tier
    score, _ = compute_net_buying_value_score(250000, 0)
    assert score == 15.0

    # $500k-$1M tier
    score, _ = compute_net_buying_value_score(750000, 0)
    assert score == 20.0

    # >$1M tier
    score, _ = compute_net_buying_value_score(2000000, 0)
    assert score == 25.0

    # Net negative (sales > purchases)
    score, _ = compute_net_buying_value_score(50000, 100000)
    assert score == 0.0


def test_buy_sell_imbalance_score():
    """Test buy/sell imbalance scoring."""
    # Perfect: purchases with no sales
    score, _ = compute_buy_sell_imbalance_score(100000, 0, 10, 0)
    assert score == 20.0

    # 5:1 purchase-to-sale ratio
    score, _ = compute_buy_sell_imbalance_score(500000, 90000, 10, 2)
    assert score == 15.0

    # Net buying but < 5:1 ratio
    score, _ = compute_buy_sell_imbalance_score(200000, 100000, 5, 2)
    assert score == 10.0

    # No transactions
    score, _ = compute_buy_sell_imbalance_score(0, 0, 0, 0)
    assert score == 0.0

    # Sales >= purchases
    score, _ = compute_buy_sell_imbalance_score(100000, 150000, 2, 3)
    assert score == 0.0


def test_distinct_buyer_breadth_score():
    """Test distinct buyer breadth scoring."""
    assert compute_distinct_buyer_breadth_score(0)[0] == 0.0
    assert compute_distinct_buyer_breadth_score(1)[0] == 5.0
    assert compute_distinct_buyer_breadth_score(2)[0] == 8.0
    assert compute_distinct_buyer_breadth_score(3)[0] == 12.0
    assert compute_distinct_buyer_breadth_score(4)[0] == 12.0
    assert compute_distinct_buyer_breadth_score(5)[0] == 15.0
    assert compute_distinct_buyer_breadth_score(10)[0] == 15.0


def test_recency_score():
    """Test recency scoring based on latest purchase date."""
    now = datetime.now(timezone.utc)

    # <= 30 days
    date_20_days_ago = (now - timedelta(days=20)).isoformat()
    score, _ = compute_recency_score(date_20_days_ago)
    assert score == 15.0

    # 31-90 days
    date_60_days_ago = (now - timedelta(days=60)).isoformat()
    score, _ = compute_recency_score(date_60_days_ago)
    assert score == 12.0

    # 91-180 days
    date_120_days_ago = (now - timedelta(days=120)).isoformat()
    score, _ = compute_recency_score(date_120_days_ago)
    assert score == 8.0

    # 181-365 days
    date_200_days_ago = (now - timedelta(days=200)).isoformat()
    score, _ = compute_recency_score(date_200_days_ago)
    assert score == 5.0

    # > 365 days
    date_400_days_ago = (now - timedelta(days=400)).isoformat()
    score, _ = compute_recency_score(date_400_days_ago)
    assert score == 0.0

    # No date
    score, _ = compute_recency_score(None)
    assert score == 0.0


def test_role_quality_score():
    """Test role quality scoring based on buyer titles."""
    # Executive (CEO, CFO, etc.)
    score, _ = compute_role_quality_score(["Chief Executive Officer"])
    assert score == 10.0

    score, _ = compute_role_quality_score(["Chief Financial Officer"])
    assert score == 10.0

    score, _ = compute_role_quality_score(["President"])
    assert score == 10.0

    # Director
    score, _ = compute_role_quality_score(["Director"])
    assert score == 7.0

    # 10% owner
    score, _ = compute_role_quality_score(["10% Owner"])
    assert score == 7.0

    # Other insider
    score, _ = compute_role_quality_score(["Vice President"])
    assert score == 3.0

    # No roles
    score, _ = compute_role_quality_score(None)
    assert score == 0.0

    # Multiple roles (highest wins)
    score, _ = compute_role_quality_score(["Director", "CEO"])
    assert score == 10.0


def test_persistence_score():
    """Test persistence scoring based on purchase months."""
    # 3+ distinct months
    score, _ = compute_persistence_score(["2025-01", "2025-02", "2025-03"])
    assert score == 10.0

    score, _ = compute_persistence_score(["2024-01", "2024-05", "2024-10", "2025-02"])
    assert score == 10.0

    # 2 distinct months
    score, _ = compute_persistence_score(["2025-01", "2025-02", "2025-01"])
    assert score == 6.0

    # 1 month
    score, _ = compute_persistence_score(["2025-01", "2025-01", "2025-01"])
    assert score == 3.0

    # No months
    score, _ = compute_persistence_score(None)
    assert score == 0.0

    score, _ = compute_persistence_score([])
    assert score == 0.0


def test_data_quality_score():
    """Test data quality scoring based on Form 4 parsing success."""
    # >= 95% parsed
    score, _ = compute_data_quality_score(100, 100)
    assert score == 5.0

    score, _ = compute_data_quality_score(100, 96)
    assert score == 5.0

    # 80-94% parsed
    score, _ = compute_data_quality_score(100, 90)
    assert score == 3.0

    score, _ = compute_data_quality_score(100, 80)
    assert score == 3.0

    # 50-79% parsed
    score, _ = compute_data_quality_score(100, 70)
    assert score == 1.0

    score, _ = compute_data_quality_score(100, 50)
    assert score == 1.0

    # < 50% parsed
    score, _ = compute_data_quality_score(100, 40)
    assert score == 0.0

    # No filings found
    score, _ = compute_data_quality_score(0, 0)
    assert score == 0.0


def test_rating_label_mapping():
    """Test score-to-label mapping."""
    assert get_rating_label(90) == "Very Strong Insider Buying Evidence"
    assert get_rating_label(80) == "Very Strong Insider Buying Evidence"
    assert get_rating_label(75) == "Strong Insider Buying Evidence"
    assert get_rating_label(60) == "Strong Insider Buying Evidence"
    assert get_rating_label(55) == "Moderate Insider Buying Evidence"
    assert get_rating_label(40) == "Moderate Insider Buying Evidence"
    assert get_rating_label(35) == "Weak Insider Buying Evidence"
    assert get_rating_label(20) == "Weak Insider Buying Evidence"
    assert get_rating_label(15) == "Little/No Insider Buying Evidence"
    assert get_rating_label(0) == "Little/No Insider Buying Evidence"


def test_compute_insider_evidence_score_complete():
    """Test complete score computation with all fields."""
    now = datetime.now(timezone.utc)
    recent_date = (now - timedelta(days=10)).isoformat()

    metrics = {
        "ticker": "TEST",
        "purchase_value": 2000000.0,  # 25 pts
        "sale_value": 0.0,
        "purchase_count": 50,  # 20 pts (no sales)
        "sale_count": 0,
        "distinct_buyers": 6,  # 15 pts
        "latest_purchase_date": recent_date,  # 15 pts
        "buyer_roles": ["CEO", "Director"],  # 10 pts
        "purchase_months": ["2024-01", "2024-06", "2025-01"],  # 10 pts
        "form4_filings_found": 100,
        "form4_filings_parsed": 98,  # 5 pts
    }

    score = compute_insider_evidence_score("TEST", metrics)

    assert score.ticker == "TEST"
    assert score.total_score == 100.0  # Perfect score
    assert score.rating_label == "Very Strong Insider Buying Evidence"
    assert len(score.component_scores) == 7
    assert len(score.warnings) == 0


def test_compute_insider_evidence_score_missing_fields():
    """Test score computation with missing fields generates warnings."""
    metrics = {
        "ticker": "TEST",
        "purchase_value": 100000.0,
        "sale_value": 0.0,
        "purchase_count": 10,
        "sale_count": 0,
        "form4_filings_found": 50,
        "form4_filings_parsed": 48,
    }

    score = compute_insider_evidence_score("TEST", metrics)

    assert score.ticker == "TEST"
    assert score.total_score > 0  # Should still score
    assert len(score.warnings) > 0  # Should have warnings
    assert "distinct_buyers field missing" in score.warnings
    assert "latest_purchase_date field missing" in score.warnings
    assert "buyer_roles field missing" in score.warnings
    assert "purchase_months field missing" in score.warnings


def test_maia_like_fixture_scores_high():
    """Test MAIA-like fixture scores very high."""
    now = datetime.now(timezone.utc)
    recent_date = (now - timedelta(days=15)).isoformat()

    metrics = {
        "ticker": "MAIA",
        "purchase_value": 4921437.58,  # 25 pts (>$1M)
        "sale_value": 0.0,
        "purchase_count": 134,  # 20 pts (no sales)
        "sale_count": 0,
        "distinct_buyers": 5,  # 15 pts
        "latest_purchase_date": recent_date,  # 15 pts (< 30 days)
        "buyer_roles": ["CEO", "Director", "10% Owner"],  # 10 pts
        "purchase_months": ["2023-01", "2023-06", "2024-01", "2024-06"],  # 10 pts
        "form4_filings_found": 214,
        "form4_filings_parsed": 214,  # 5 pts (100%)
    }

    score = compute_insider_evidence_score("MAIA", metrics)

    assert score.total_score == 100.0
    assert score.rating_label == "Very Strong Insider Buying Evidence"


def test_sale_heavy_fixture_scores_low():
    """Test sale-heavy fixture scores low."""
    metrics = {
        "ticker": "SALE",
        "purchase_value": 10000.0,
        "sale_value": 500000.0,  # Sales > Purchases
        "purchase_count": 2,
        "sale_count": 10,
        "distinct_buyers": 1,
        "latest_purchase_date": None,
        "buyer_roles": None,
        "purchase_months": None,
        "form4_filings_found": 50,
        "form4_filings_parsed": 40,
    }

    score = compute_insider_evidence_score("SALE", metrics)

    assert score.total_score < 20  # Should be low
    assert "Weak" in score.rating_label or "Little" in score.rating_label
