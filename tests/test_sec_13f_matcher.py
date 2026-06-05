"""Tests for SEC 13F issuer matching."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sources.sec_13f_parser import Form13FHolding
from sources.sec_13f_matcher import (
    _normalize_issuer_name,
    match_ticker_to_13f_holdings,
)


def test_normalize_issuer_name():
    """Test issuer name normalization."""
    variants = _normalize_issuer_name("MAIA Biotechnology, Inc.")
    assert "maia biotechnology" in variants
    assert "maia" in variants


def test_normalize_issuer_name_with_corp():
    """Test normalization removes common suffixes."""
    variants = _normalize_issuer_name("Apple Inc.")
    assert "apple" in variants


def test_match_ticker_exact_name():
    """Test exact issuer name matching."""
    holding = Form13FHolding(
        manager_name="Test Manager",
        manager_cik="0001234567",
        filing_accession="test-123",
        filing_date="2024-02-14",
        report_period="2023-12-31",
        issuer_name="MAIA Biotechnology, Inc.",
        title_of_class="COM",
        cusip="55405N100",
        value_usd_thousands=1000.0,
        shares_or_principal_amount=10000.0,
        share_type="SH",
    )

    matches = match_ticker_to_13f_holdings(
        ticker="MAIA",
        resolved_company_name="MAIA Biotechnology, Inc.",
        resolved_cik="0001878313",
        holdings=[holding],
        cusip=None,
    )

    assert len(matches) == 1
    assert matches[0].confidence in ("EXACT_ISSUER_NAME", "NORMALIZED_ISSUER_NAME")


def test_match_ticker_normalized_name():
    """Test normalized issuer name matching."""
    holding = Form13FHolding(
        manager_name="Test Manager",
        manager_cik="0001234567",
        filing_accession="test-123",
        filing_date="2024-02-14",
        report_period="2023-12-31",
        issuer_name="MAIA BIOTECHNOLOGY INC",
        title_of_class="COM",
        cusip="55405N100",
        value_usd_thousands=1000.0,
        shares_or_principal_amount=10000.0,
        share_type="SH",
    )

    matches = match_ticker_to_13f_holdings(
        ticker="MAIA",
        resolved_company_name="MAIA Biotechnology, Inc.",
        resolved_cik="0001878313",
        holdings=[holding],
        cusip=None,
    )

    assert len(matches) == 1
    # After normalization, "MAIA BIOTECHNOLOGY INC" and "MAIA Biotechnology, Inc." are exact matches
    assert matches[0].confidence == "EXACT_ISSUER_NAME"


def test_match_ticker_no_match():
    """Test no match when issuer name differs."""
    holding = Form13FHolding(
        manager_name="Test Manager",
        manager_cik="0001234567",
        filing_accession="test-123",
        filing_date="2024-02-14",
        report_period="2023-12-31",
        issuer_name="Apple Inc.",
        title_of_class="COM",
        cusip="037833100",
        value_usd_thousands=5000.0,
        shares_or_principal_amount=50000.0,
        share_type="SH",
    )

    matches = match_ticker_to_13f_holdings(
        ticker="MAIA",
        resolved_company_name="MAIA Biotechnology, Inc.",
        resolved_cik="0001878313",
        holdings=[holding],
        cusip=None,
    )

    assert len(matches) == 0


def test_match_ticker_cusip_match():
    """Test CUSIP matching when CUSIP is available."""
    holding = Form13FHolding(
        manager_name="Test Manager",
        manager_cik="0001234567",
        filing_accession="test-123",
        filing_date="2024-02-14",
        report_period="2023-12-31",
        issuer_name="Some Different Name",
        title_of_class="COM",
        cusip="55405N100",
        value_usd_thousands=1000.0,
        shares_or_principal_amount=10000.0,
        share_type="SH",
    )

    matches = match_ticker_to_13f_holdings(
        ticker="MAIA",
        resolved_company_name="MAIA Biotechnology, Inc.",
        resolved_cik="0001878313",
        holdings=[holding],
        cusip="55405N100",
    )

    assert len(matches) == 1
    assert matches[0].confidence == "EXACT_CUSIP"
