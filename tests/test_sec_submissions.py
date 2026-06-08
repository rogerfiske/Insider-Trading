"""Tests for SEC issuer-specific submissions retrieval.

Tests cover:
- fetch_company_submissions parsing
- get_form4_filings_for_cik filtering and lookback logic
- Archive URL construction
- CIK handling (with/without leading zeros)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from sources.sec_submissions import (
    SecSubmissionFiling,
    fetch_company_submissions,
    get_form4_filings_for_cik,
)


def test_get_form4_filings_for_cik_filters_form4_only():
    """Test that only Form 4 filings are returned, not other form types."""
    mock_response = {
        "ok": True,
        "body": {
            "cik": "1878313",
            "filings": {
                "recent": {
                    "accessionNumber": ["0001878313-26-000001", "0001878313-26-000002", "0001878313-26-000003"],
                    "filingDate": ["2026-06-01", "2026-05-15", "2026-04-01"],
                    "reportDate": ["2026-05-31", "2026-05-14", "2026-03-31"],
                    "acceptanceDateTime": ["2026-06-01T10:00:00", "2026-05-15T11:00:00", "2026-04-01T12:00:00"],
                    "form": ["4", "10-K", "4"],
                    "primaryDocument": ["form4.xml", "report.htm", "xslF345X06/form4.xml"],
                    "primaryDocDescription": ["Form 4", "Annual Report", "Form 4"],
                }
            },
        },
        "url": "https://data.sec.gov/submissions/CIK0001878313.json",
    }

    with patch("sources.sec_submissions.fetch_company_submissions", return_value=mock_response):
        filings = get_form4_filings_for_cik("0001878313", lookback_days=365)

    # Should only include Form 4 filings (2 out of 3)
    assert len(filings) == 2
    assert all(f.form == "4" for f in filings)


def test_get_form4_filings_for_cik_applies_lookback_window():
    """Test that lookback window correctly filters filings by filing date."""
    now = datetime.now(timezone.utc)
    recent_date = (now - timedelta(days=10)).strftime("%Y-%m-%d")
    old_date = (now - timedelta(days=400)).strftime("%Y-%m-%d")

    mock_response = {
        "ok": True,
        "body": {
            "cik": "1878313",
            "filings": {
                "recent": {
                    "accessionNumber": ["0001878313-26-000001", "0001878313-26-000002"],
                    "filingDate": [recent_date, old_date],
                    "reportDate": ["", ""],
                    "acceptanceDateTime": ["", ""],
                    "form": ["4", "4"],
                    "primaryDocument": ["form4.xml", "form4.xml"],
                    "primaryDocDescription": ["Form 4", "Form 4"],
                }
            },
        },
        "url": "https://data.sec.gov/submissions/CIK0001878313.json",
    }

    with patch("sources.sec_submissions.fetch_company_submissions", return_value=mock_response):
        filings = get_form4_filings_for_cik("0001878313", lookback_days=365)

    # Should only include recent filing within 365-day lookback
    assert len(filings) == 1
    assert filings[0].filing_date == recent_date


def test_get_form4_filings_for_cik_constructs_correct_urls():
    """Test that archive directory and primary document URLs are correctly constructed."""
    mock_response = {
        "ok": True,
        "body": {
            "cik": "1878313",
            "filings": {
                "recent": {
                    "accessionNumber": ["0001878313-26-000001"],
                    "filingDate": ["2026-06-01"],
                    "reportDate": ["2026-05-31"],
                    "acceptanceDateTime": ["2026-06-01T10:00:00"],
                    "form": ["4"],
                    "primaryDocument": ["xslF345X06/form4.xml"],
                    "primaryDocDescription": ["Form 4"],
                }
            },
        },
        "url": "https://data.sec.gov/submissions/CIK0001878313.json",
    }

    with patch("sources.sec_submissions.fetch_company_submissions", return_value=mock_response):
        filings = get_form4_filings_for_cik("0001878313", lookback_days=365)

    assert len(filings) == 1
    filing = filings[0]

    # Check CIK handling
    assert filing.cik == "0001878313"
    assert filing.cik_no_leading_zeros == "1878313"

    # Check accession number handling
    assert filing.accession_number == "0001878313-26-000001"
    assert filing.accession_no_dashes == "000187831326000001"

    # Check URLs
    expected_archive = "https://www.sec.gov/Archives/edgar/data/1878313/000187831326000001/"
    assert filing.archive_directory_url == expected_archive

    expected_doc_url = "https://www.sec.gov/Archives/edgar/data/1878313/000187831326000001/xslF345X06/form4.xml"
    assert filing.primary_document_url == expected_doc_url


def test_get_form4_filings_for_cik_handles_empty_filings():
    """Test that empty filings list is handled gracefully."""
    mock_response = {
        "ok": True,
        "body": {
            "cik": "1878313",
            "filings": {"recent": {}},
        },
        "url": "https://data.sec.gov/submissions/CIK0001878313.json",
    }

    with patch("sources.sec_submissions.fetch_company_submissions", return_value=mock_response):
        filings = get_form4_filings_for_cik("0001878313", lookback_days=365)

    assert filings == []


def test_get_form4_filings_for_cik_handles_fetch_failure():
    """Test that fetch failure returns empty list."""
    mock_response = {
        "ok": False,
        "error": "HTTP 404",
        "url": "https://data.sec.gov/submissions/CIK0001878313.json",
    }

    with patch("sources.sec_submissions.fetch_company_submissions", return_value=mock_response):
        filings = get_form4_filings_for_cik("0001878313", lookback_days=365)

    assert filings == []


def test_get_form4_filings_for_cik_sorts_by_filing_date_descending():
    """Test that filings are sorted by filing date (most recent first)."""
    mock_response = {
        "ok": True,
        "body": {
            "cik": "1878313",
            "filings": {
                "recent": {
                    "accessionNumber": ["0001878313-26-000001", "0001878313-26-000002", "0001878313-26-000003"],
                    "filingDate": ["2026-04-01", "2026-06-01", "2026-05-01"],
                    "reportDate": ["", "", ""],
                    "acceptanceDateTime": ["", "", ""],
                    "form": ["4", "4", "4"],
                    "primaryDocument": ["form4.xml", "form4.xml", "form4.xml"],
                    "primaryDocDescription": ["Form 4", "Form 4", "Form 4"],
                }
            },
        },
        "url": "https://data.sec.gov/submissions/CIK0001878313.json",
    }

    with patch("sources.sec_submissions.fetch_company_submissions", return_value=mock_response):
        filings = get_form4_filings_for_cik("0001878313", lookback_days=365)

    # Should be sorted by filing date descending (most recent first)
    assert len(filings) == 3
    assert filings[0].filing_date == "2026-06-01"
    assert filings[1].filing_date == "2026-05-01"
    assert filings[2].filing_date == "2026-04-01"
