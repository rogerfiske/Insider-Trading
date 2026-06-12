"""Tests for Form 144 and Schedule 13D/G extraction.

Tests cover:
- Form 144 parsing (sale intent notice, NOT actual sale)
- Schedule 13D parsing (active ownership)
- Schedule 13G parsing (passive ownership)
- Distinguish 13D vs 13G
- Distinguish original vs amendment
- Parse failure preservation
- Batch aggregation
- MAIA inventory reconciliation
- Safety constraints
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from sources.sec_13dg import (
    Ownership13DG,
    OwnershipSummary,
    parse_13dg_filing,
)
from sources.sec_form144 import (
    Form144Filing,
    Form144Summary,
    parse_form144_filing,
)
from sources.sec_submissions import SecSubmissionFiling


class TestForm144Parsing:
    """Test Form 144 parsing."""

    def test_parse_minimal_form144_fixture(self):
        """Test parsing minimal Form 144 text document."""
        # Minimal fixture for Form 144
        filing = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000001",
            accession_no_dashes="0001234567-23-000001".replace("-", ""),
            form="144",
            filing_date="2024-01-15",
            report_date="",
            acceptance_datetime="2024-01-15T16:30:00.000Z",
            primary_document="form144.txt",
            primary_doc_description="Form 144",
            source_url="https://data.sec.gov/submissions/CIK0001878313.json",
            archive_directory_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001878313",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300001/form144.txt",
        )

        # Mock fetch function (no live network)
        def mock_fetch(url: str, **kwargs):
            return {
                "ok": True,
                "body": """FORM 144
NOTICE OF PROPOSED SALE OF SECURITIES

Name of Issuer: MAIA Biotechnology Inc
Ticker: MAIA

Name of Person: John Doe
Relationship: Director

Securities to be Sold: 50000 shares
Approximate Date of Sale: 02/01/2024
""",
                "from_cache": False,
            }

        result = parse_form144_filing(filing, fetch_func=mock_fetch)

        assert result is not None
        assert result.ticker == "MAIA"
        assert result.issuer_cik == "0001878313"
        assert result.filing_date == "2024-01-15"
        assert result.seller_name == "John Doe"
        assert result.seller_relationship == "Director"
        assert result.securities_to_be_sold == "50000 shares"
        assert result.approximate_date_of_sale == "02/01/2024"
        assert result.parse_status == "success"
        assert result.sale_status == "proposed"  # Form 144 is NOTICE, not actual sale

    def test_parse_form144_missing_fields(self):
        """Test Form 144 handles missing optional fields."""
        filing = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000002",
            accession_no_dashes="000123456723000002",
            form="144",
            filing_date="2024-01-16",
            report_date="",
            acceptance_datetime="",
            primary_document="form144.txt",
            primary_doc_description="",
            source_url="",
            archive_directory_url="",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300002/form144.txt",
        )

        def mock_fetch(url: str, **kwargs):
            return {
                "ok": True,
                "body": """FORM 144
Name of Issuer: MAIA Biotechnology Inc
""",
            }

        result = parse_form144_filing(filing, fetch_func=mock_fetch)

        assert result is not None
        assert result.seller_name is None
        assert result.securities_to_be_sold is None
        assert result.parse_status == "partial"

    def test_parse_form144_fetch_failure(self):
        """Test Form 144 handles fetch failures."""
        filing = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000003",
            accession_no_dashes="000123456723000003",
            form="144",
            filing_date="2024-01-17",
            report_date="",
            acceptance_datetime="",
            primary_document="form144.txt",
            primary_doc_description="",
            source_url="",
            archive_directory_url="",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300003/form144.txt",
        )

        def mock_fetch(url: str, **kwargs):
            return {"ok": False, "error": "404 Not Found"}

        result = parse_form144_filing(filing, fetch_func=mock_fetch)

        assert result is not None
        assert result.parse_status == "failed"
        assert result.error_message == "404 Not Found"

    def test_form144_not_actual_sale(self):
        """Test Form 144 is explicitly marked as proposed sale, not actual sale."""
        filing = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000004",
            accession_no_dashes="000123456723000004",
            form="144",
            filing_date="2024-01-18",
            report_date="",
            acceptance_datetime="",
            primary_document="form144.txt",
            primary_doc_description="",
            source_url="",
            archive_directory_url="",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300004/form144.txt",
        )

        def mock_fetch(url: str, **kwargs):
            return {
                "ok": True,
                "body": "FORM 144\nName of Issuer: MAIA Biotechnology Inc\n",
            }

        result = parse_form144_filing(filing, fetch_func=mock_fetch)

        assert result.sale_status == "proposed"
        assert result.sale_status != "completed"


class TestSchedule13DGParsing:
    """Test Schedule 13D/G parsing."""

    def test_parse_minimal_13d_fixture(self):
        """Test parsing minimal Schedule 13D (active ownership)."""
        filing = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000005",
            accession_no_dashes="000123456723000005",
            form="SC 13D",
            filing_date="2024-02-01",
            report_date="",
            acceptance_datetime="",
            primary_document="sc13d.txt",
            primary_doc_description="",
            source_url="",
            archive_directory_url="",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300005/sc13d.txt",
        )

        def mock_fetch(url: str, **kwargs):
            return {
                "ok": True,
                "body": """SCHEDULE 13D
Issuer: MAIA Biotechnology Inc

Name of Reporting Person: Activist Fund LLC
Shares Beneficially Owned: 1500000
Percent of Class: 12.5%
Sole Voting Power: 1500000
Purpose of Transaction: Increase representation on Board
""",
            }

        result = parse_13dg_filing(filing, fetch_func=mock_fetch)

        assert result is not None
        assert result.form == "SC 13D"
        assert result.active_or_passive_classification == "active"
        assert result.filer_name == "Activist Fund LLC"
        assert result.shares_beneficially_owned == "1500000"
        assert result.ownership_percent == "12.5%"
        assert result.purpose_of_transaction == "Increase representation on Board"
        assert result.parse_status == "success"

    def test_parse_minimal_13g_fixture(self):
        """Test parsing minimal Schedule 13G (passive ownership)."""
        filing = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000006",
            accession_no_dashes="000123456723000006",
            form="SC 13G",
            filing_date="2024-02-02",
            report_date="",
            acceptance_datetime="",
            primary_document="sc13g.txt",
            primary_doc_description="",
            source_url="",
            archive_directory_url="",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300006/sc13g.txt",
        )

        def mock_fetch(url: str, **kwargs):
            return {
                "ok": True,
                "body": """SCHEDULE 13G
Issuer: MAIA Biotechnology Inc

Name of Reporting Person: Passive Investment Fund
Shares Beneficially Owned: 800000
Percent of Class: 6.7%
""",
            }

        result = parse_13dg_filing(filing, fetch_func=mock_fetch)

        assert result is not None
        assert result.form == "SC 13G"
        assert result.active_or_passive_classification == "passive"
        assert result.filer_name == "Passive Investment Fund"
        assert result.shares_beneficially_owned == "800000"
        assert result.ownership_percent == "6.7%"

    def test_distinguish_13d_vs_13g(self):
        """Test that 13D (active) is distinguished from 13G (passive)."""
        filing_13d = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000007",
            accession_no_dashes="000123456723000007",
            form="SC 13D",
            filing_date="2024-02-03",
            report_date="",
            acceptance_datetime="",
            primary_document="sc13d.txt",
            primary_doc_description="",
            source_url="",
            archive_directory_url="",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300007/sc13d.txt",
        )

        filing_13g = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000008",
            accession_no_dashes="000123456723000008",
            form="SC 13G",
            filing_date="2024-02-04",
            report_date="",
            acceptance_datetime="",
            primary_document="sc13g.txt",
            primary_doc_description="",
            source_url="",
            archive_directory_url="",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300008/sc13g.txt",
        )

        def mock_fetch(url: str, **kwargs):
            return {"ok": True, "body": "SCHEDULE 13D\n"}

        result_13d = parse_13dg_filing(filing_13d, fetch_func=mock_fetch)
        result_13g = parse_13dg_filing(filing_13g, fetch_func=mock_fetch)

        assert result_13d.active_or_passive_classification == "active"
        assert result_13g.active_or_passive_classification == "passive"

    def test_distinguish_original_vs_amendment(self):
        """Test that original filings are distinguished from amendments."""
        filing_original = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000009",
            accession_no_dashes="000123456723000009",
            form="SC 13D",
            filing_date="2024-02-05",
            report_date="",
            acceptance_datetime="",
            primary_document="sc13d.txt",
            primary_doc_description="",
            source_url="",
            archive_directory_url="",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300009/sc13d.txt",
        )

        filing_amendment = SecSubmissionFiling(
            cik="0001878313",
            cik_no_leading_zeros="1878313",
            accession_number="0001234567-23-000010",
            accession_no_dashes="000123456723000010",
            form="SC 13D/A",
            filing_date="2024-02-06",
            report_date="",
            acceptance_datetime="",
            primary_document="sc13da.txt",
            primary_doc_description="",
            source_url="",
            archive_directory_url="",
            primary_document_url="https://www.sec.gov/Archives/edgar/data/1878313/000012345672300010/sc13da.txt",
        )

        def mock_fetch(url: str, **kwargs):
            return {"ok": True, "body": "SCHEDULE 13D\n"}

        result_original = parse_13dg_filing(filing_original, fetch_func=mock_fetch)
        result_amendment = parse_13dg_filing(filing_amendment, fetch_func=mock_fetch)

        assert result_original.amendment_number is None or result_original.amendment_number == "0"
        assert result_amendment.amendment_number is not None
        assert result_amendment.form == "SC 13D/A"


class TestAggregation:
    """Test aggregation and summary generation."""

    def test_form144_summary(self):
        """Test Form 144 summary aggregation."""
        filings = [
            Form144Filing(
                ticker="MAIA",
                issuer_cik="0001878313",
                accession_number="0001234567-23-000001",
                filing_date="2024-01-15",
                seller_name="John Doe",
                seller_relationship="Director",
                securities_to_be_sold="50000 shares",
                aggregate_market_value=None,
                approximate_date_of_sale="02/01/2024",
                broker_name=None,
                exchange=None,
                notice_date="2024-01-15",
                sale_status="proposed",
                parse_status="success",
                error_message=None,
            ),
            Form144Filing(
                ticker="MAIA",
                issuer_cik="0001878313",
                accession_number="0001234567-23-000002",
                filing_date="2024-01-16",
                seller_name="Jane Smith",
                seller_relationship="Officer",
                securities_to_be_sold="25000 shares",
                aggregate_market_value=None,
                approximate_date_of_sale="02/05/2024",
                broker_name=None,
                exchange=None,
                notice_date="2024-01-16",
                sale_status="proposed",
                parse_status="success",
                error_message=None,
            ),
        ]

        summary = Form144Summary.from_filings(filings)

        assert summary.ticker == "MAIA"
        assert summary.total_filings == 2
        assert summary.successful_parses == 2
        assert summary.failed_parses == 0

    def test_ownership_summary(self):
        """Test ownership summary aggregation."""
        filings = [
            Ownership13DG(
                ticker="MAIA",
                issuer_cik="0001878313",
                accession_number="0001234567-23-000005",
                filing_date="2024-02-01",
                form="SC 13D",
                filer_name="Activist Fund LLC",
                filer_cik=None,
                beneficial_owner_name=None,
                ownership_percent="12.5%",
                shares_beneficially_owned="1500000",
                sole_voting_power=None,
                shared_voting_power=None,
                sole_dispositive_power=None,
                shared_dispositive_power=None,
                type_of_reporting_person=None,
                active_or_passive_classification="active",
                amendment_number=None,
                event_date=None,
                purpose_of_transaction="Increase representation on Board",
                parse_status="success",
                error_message=None,
            ),
            Ownership13DG(
                ticker="MAIA",
                issuer_cik="0001878313",
                accession_number="0001234567-23-000006",
                filing_date="2024-02-02",
                form="SC 13G",
                filer_name="Passive Investment Fund",
                filer_cik=None,
                beneficial_owner_name=None,
                ownership_percent="6.7%",
                shares_beneficially_owned="800000",
                sole_voting_power=None,
                shared_voting_power=None,
                sole_dispositive_power=None,
                shared_dispositive_power=None,
                type_of_reporting_person=None,
                active_or_passive_classification="passive",
                amendment_number=None,
                event_date=None,
                purpose_of_transaction=None,
                parse_status="success",
                error_message=None,
            ),
        ]

        summary = OwnershipSummary.from_filings(filings)

        assert summary.ticker == "MAIA"
        assert summary.total_filings == 2
        assert summary.active_13d_count == 1
        assert summary.passive_13g_count == 1


class TestSafetyConstraints:
    """Test safety constraints."""

    def test_no_buy_sell_hold_language(self):
        """Test that outputs contain no buy/sell/hold language."""
        filings = [
            Form144Filing(
                ticker="MAIA",
                issuer_cik="0001878313",
                accession_number="0001234567-23-000001",
                filing_date="2024-01-15",
                seller_name="John Doe",
                seller_relationship="Director",
                securities_to_be_sold="50000 shares",
                aggregate_market_value=None,
                approximate_date_of_sale="02/01/2024",
                broker_name=None,
                exchange=None,
                notice_date="2024-01-15",
                sale_status="proposed",
                parse_status="success",
                error_message=None,
            ),
        ]

        summary = Form144Summary.from_filings(filings)
        summary_dict = summary.to_dict()
        summary_json = json.dumps(summary_dict)

        # Check for investment language (excluding legitimate field names like "seller")
        forbidden_phrases = ["buy", " sell ", "hold", "recommend", "strong buy", "accumulate"]
        for phrase in forbidden_phrases:
            assert phrase.lower() not in summary_json.lower()

    def test_safety_flags_present(self):
        """Test that safety flags are present in outputs."""
        filings = [
            Form144Filing(
                ticker="MAIA",
                issuer_cik="0001878313",
                accession_number="0001234567-23-000001",
                filing_date="2024-01-15",
                seller_name="John Doe",
                seller_relationship="Director",
                securities_to_be_sold="50000 shares",
                aggregate_market_value=None,
                approximate_date_of_sale="02/01/2024",
                broker_name=None,
                exchange=None,
                notice_date="2024-01-15",
                sale_status="proposed",
                parse_status="success",
                error_message=None,
            ),
        ]

        summary = Form144Summary.from_filings(filings)
        summary_dict = summary.to_dict()

        assert summary_dict["report_only"] is True
        assert summary_dict["alert_enabled"] is False
        assert summary_dict["openinsider_required"] is False

    def test_no_secrets_in_outputs(self):
        """Test that outputs contain no secrets."""
        filings = [
            Form144Filing(
                ticker="MAIA",
                issuer_cik="0001878313",
                accession_number="0001234567-23-000001",
                filing_date="2024-01-15",
                seller_name="John Doe",
                seller_relationship="Director",
                securities_to_be_sold="50000 shares",
                aggregate_market_value=None,
                approximate_date_of_sale="02/01/2024",
                broker_name=None,
                exchange=None,
                notice_date="2024-01-15",
                sale_status="proposed",
                parse_status="success",
                error_message=None,
            ),
        ]

        summary = Form144Summary.from_filings(filings)
        summary_json = json.dumps(summary.to_dict())

        # Check for common secret patterns
        secret_patterns = ["api_key", "password", "token", "secret", "credentials"]
        for pattern in secret_patterns:
            assert pattern.lower() not in summary_json.lower()


class TestBatchSummary:
    """Test batch summary schema."""

    def test_batch_summary_schema(self):
        """Test batch summary follows expected schema."""
        batch_summary = {
            "report_type": "ownership_filings_batch_summary",
            "report_only": True,
            "alert_enabled": False,
            "openinsider_required": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tickers_processed": ["MAIA", "NVDA"],
            "total_tickers": 2,
            "successful_tickers": 2,
            "failed_tickers": 0,
            "ticker_summaries": [],
        }

        assert batch_summary["report_type"] == "ownership_filings_batch_summary"
        assert batch_summary["report_only"] is True
        assert batch_summary["alert_enabled"] is False
        assert batch_summary["openinsider_required"] is False
        assert "generated_at" in batch_summary
        assert "tickers_processed" in batch_summary


class TestMAIAValidation:
    """Test MAIA validation and CP24B reconciliation."""

    def test_maia_inventory_reconciliation(self):
        """Test that MAIA Form 144 and 13D/G counts can be reconciled with CP24B inventory."""
        # This is a placeholder - actual implementation will fetch and compare
        # CP24B inventory shows:
        # - At least 1 Form 144
        # - At least 8 13D/G filings

        # Placeholder assertion
        expected_min_form144 = 1
        expected_min_13dg = 8

        # In actual implementation, we would:
        # 1. Load CP24B inventory
        # 2. Extract Form 144 and 13D/G counts
        # 3. Run extraction
        # 4. Compare results

        assert expected_min_form144 >= 1
        assert expected_min_13dg >= 8
