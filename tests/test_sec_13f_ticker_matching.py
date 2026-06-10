"""Tests for SEC 13F ticker matching.

This test suite validates the 13F ticker/issuer matching functionality
from CP23F 13F InfoTable matching integration.
"""

from sources.sec_13f_parser import Form13FHolding
from sources.sec_13f_matcher import (
    match_ticker_to_13f_holdings,
    _normalize_issuer_name,
    _calculate_match_confidence,
)


def test_cusip_exact_match_high_confidence():
    """Test CUSIP exact match returns high confidence."""
    holdings = [
        Form13FHolding(
            manager_name="Test Manager",
            manager_cik="0001234567",
            filing_accession="0001234567-24-000001",
            filing_date="2024-05-15",
            report_period="2024-03-31",
            issuer_name="APPLE INC",
            title_of_class="COM",
            cusip="037833100",
            value_usd_thousands=100000.0,
            shares_or_principal_amount=5000.0,
            share_type="SH",
        ),
    ]

    matches = match_ticker_to_13f_holdings(
        ticker="AAPL",
        resolved_company_name="Apple Inc.",
        resolved_cik="0000320193",
        holdings=holdings,
        cusip="037833100",  # CUSIP match
    )

    assert len(matches) == 1
    assert matches[0].confidence == "EXACT_CUSIP"
    assert matches[0].ticker == "AAPL"


def test_exact_issuer_name_match():
    """Test exact issuer name match returns medium confidence."""
    holdings = [
        Form13FHolding(
            manager_name="Test Manager",
            manager_cik="0001234567",
            filing_accession="0001234567-24-000001",
            filing_date="2024-05-15",
            report_period="2024-03-31",
            issuer_name="APPLE INC",
            title_of_class="COM",
            cusip="037833100",
            value_usd_thousands=100000.0,
            shares_or_principal_amount=5000.0,
            share_type="SH",
        ),
    ]

    matches = match_ticker_to_13f_holdings(
        ticker="AAPL",
        resolved_company_name="Apple Inc.",
        resolved_cik="0000320193",
        holdings=holdings,
        cusip=None,  # No CUSIP, use name matching
    )

    assert len(matches) == 1
    assert matches[0].confidence == "EXACT_ISSUER_NAME"


def test_normalized_issuer_name_match():
    """Test normalized issuer name match returns medium confidence."""
    holdings = [
        Form13FHolding(
            manager_name="Test Manager",
            manager_cik="0001234567",
            filing_accession="0001234567-24-000001",
            filing_date="2024-05-15",
            report_period="2024-03-31",
            issuer_name="MAIA BIOTECHNOLOGY INC",
            title_of_class="COM",
            cusip="596278107",
            value_usd_thousands=250.0,
            shares_or_principal_amount=100000.0,
            share_type="SH",
        ),
    ]

    # MAIA Biotechnology, Inc. should normalize to match MAIA BIOTECHNOLOGY INC
    matches = match_ticker_to_13f_holdings(
        ticker="MAIA",
        resolved_company_name="MAIA Biotechnology, Inc.",
        resolved_cik="0001878313",
        holdings=holdings,
        cusip=None,
    )

    assert len(matches) == 1
    assert matches[0].confidence in ("EXACT_ISSUER_NAME", "NORMALIZED_ISSUER_NAME")
    assert matches[0].holding.issuer_name == "MAIA BIOTECHNOLOGY INC"


def test_maia_name_variants_normalize():
    """Test MAIA name variants normalize correctly."""
    variants = [
        "MAIA BIOTECHNOLOGY INC",
        "MAIA BIOTECHNOLOGY, INC.",
        "Maia Biotechnology Inc",
        "MAIA Biotechnology, Inc.",
    ]

    for variant in variants:
        normalized = _normalize_issuer_name(variant)
        assert "maia biotechnology" in normalized or "maia" in normalized


def test_no_match_returns_empty():
    """Test non-match does not produce false positive."""
    holdings = [
        Form13FHolding(
            manager_name="Test Manager",
            manager_cik="0001234567",
            filing_accession="0001234567-24-000001",
            filing_date="2024-05-15",
            report_period="2024-03-31",
            issuer_name="COMPLETELY DIFFERENT COMPANY",
            title_of_class="COM",
            cusip="999999999",
            value_usd_thousands=100000.0,
            shares_or_principal_amount=5000.0,
            share_type="SH",
        ),
    ]

    matches = match_ticker_to_13f_holdings(
        ticker="MAIA",
        resolved_company_name="MAIA Biotechnology, Inc.",
        resolved_cik="0001878313",
        holdings=holdings,
        cusip="596278107",  # Different CUSIP
    )

    # Should not match
    assert len(matches) == 0


def test_fuzzy_match_excluded():
    """Test weak/fuzzy issuer-name match excluded from results."""
    holdings = [
        Form13FHolding(
            manager_name="Test Manager",
            manager_cik="0001234567",
            filing_accession="0001234567-24-000001",
            filing_date="2024-05-15",
            report_period="2024-03-31",
            issuer_name="ALPHABET INC CLASS A",  # Contains "A" but not "APPLE"
            title_of_class="COM",
            cusip="02079K107",
            value_usd_thousands=100000.0,
            shares_or_principal_amount=5000.0,
            share_type="SH",
        ),
    ]

    matches = match_ticker_to_13f_holdings(
        ticker="AAPL",
        resolved_company_name="Apple Inc.",
        resolved_cik="0000320193",
        holdings=holdings,
        cusip=None,
    )

    # Fuzzy matches are filtered out
    assert len(matches) == 0


def test_calculate_match_confidence_cusip():
    """Test confidence calculation for CUSIP match."""
    confidence, method = _calculate_match_confidence(
        resolved_name="Apple Inc.",
        holding_name="APPLE INC",
        cusip_match=True,
    )

    assert confidence == "EXACT_CUSIP"
    assert "CUSIP" in method


def test_calculate_match_confidence_exact_name():
    """Test confidence calculation for exact name match."""
    confidence, method = _calculate_match_confidence(
        resolved_name="Apple Inc.",
        holding_name="Apple Inc.",
        cusip_match=False,
    )

    assert confidence == "EXACT_ISSUER_NAME"


def test_calculate_match_confidence_normalized():
    """Test confidence calculation for normalized name match."""
    confidence, method = _calculate_match_confidence(
        resolved_name="MAIA Biotechnology, Inc.",
        holding_name="MAIA BIOTECHNOLOGY INC",
        cusip_match=False,
    )

    assert confidence in ("EXACT_ISSUER_NAME", "NORMALIZED_ISSUER_NAME")


def test_multiple_holdings_same_issuer():
    """Test matching handles multiple holdings for same issuer."""
    holdings = [
        Form13FHolding(
            manager_name="Manager A",
            manager_cik="0001111111",
            filing_accession="0001111111-24-000001",
            filing_date="2024-05-15",
            report_period="2024-03-31",
            issuer_name="MAIA BIOTECHNOLOGY INC",
            title_of_class="COM",
            cusip="596278107",
            value_usd_thousands=100.0,
            shares_or_principal_amount=50000.0,
            share_type="SH",
        ),
        Form13FHolding(
            manager_name="Manager B",
            manager_cik="0002222222",
            filing_accession="0002222222-24-000001",
            filing_date="2024-05-15",
            report_period="2024-03-31",
            issuer_name="MAIA BIOTECHNOLOGY INC",
            title_of_class="COM",
            cusip="596278107",
            value_usd_thousands=200.0,
            shares_or_principal_amount=100000.0,
            share_type="SH",
        ),
    ]

    matches = match_ticker_to_13f_holdings(
        ticker="MAIA",
        resolved_company_name="MAIA Biotechnology, Inc.",
        resolved_cik="0001878313",
        holdings=holdings,
        cusip=None,
    )

    # Should match both
    assert len(matches) == 2
    assert all(m.ticker == "MAIA" for m in matches)


def test_normalize_issuer_name():
    """Test issuer name normalization logic."""
    # Test basic normalization
    assert "apple" in _normalize_issuer_name("Apple Inc.")
    assert "maia biotechnology" in _normalize_issuer_name("MAIA Biotechnology, Inc.")

    # Test suffix removal
    variants = _normalize_issuer_name("Test Company, Inc.")
    assert any("test company" in v for v in variants)

    # Test punctuation removal
    variants = _normalize_issuer_name("Test, Company.")
    assert any("test company" in v for v in variants)


def test_empty_holdings_list():
    """Test matching against empty holdings list returns empty."""
    matches = match_ticker_to_13f_holdings(
        ticker="MAIA",
        resolved_company_name="MAIA Biotechnology, Inc.",
        resolved_cik="0001878313",
        holdings=[],
        cusip=None,
    )

    assert len(matches) == 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
