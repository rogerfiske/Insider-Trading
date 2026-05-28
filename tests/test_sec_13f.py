"""Tests for SEC 13F-HR connector."""

from __future__ import annotations

import json
from unittest.mock import patch

from sources.sec_13f import Sec13FConnector


# Sample submissions response (simplified)
SAMPLE_SUBMISSIONS = {
    "cik": "1067983",
    "entityType": "investment",
    "name": "BERKSHIRE HATHAWAY INC",
    "filings": {
        "recent": {
            "accessionNumber": [
                "0001067983-26-000001",
                "0001067983-25-000999",
            ],
            "filingDate": ["2026-02-14", "2025-11-14"],
            "reportDate": ["2025-12-31", "2025-09-30"],
            "form": ["13F-HR", "13F-HR"],
            "primaryDocument": ["form13f.xml", "form13f.xml"],
        }
    },
}


class TestSec13FConnector:
    def test_fetch_success_single_manager(self) -> None:
        with patch("sources.sec_13f.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": True,
                "status": 200,
                "body": json.dumps(SAMPLE_SUBMISSIONS),
                "error": None,
                "from_cache": False,
            }
            connector = Sec13FConnector(
                managers=[("Berkshire Hathaway", "0001067983")]
            )
            result = connector.fetch()

        assert result.ok
        assert len(result.evidence) == 1
        ev = result.evidence[0]
        assert ev.normalized["manager_name"] == "Berkshire Hathaway"
        assert ev.normalized["accession_number"] == "0001067983-26-000001"
        assert ev.normalized["report_period"] == "2025-12-31"

    def test_fetch_no_13f_filing(self) -> None:
        no_13f = {
            "filings": {
                "recent": {
                    "accessionNumber": ["0001-26-000001"],
                    "filingDate": ["2026-01-01"],
                    "reportDate": ["2025-12-31"],
                    "form": ["10-K"],
                    "primaryDocument": ["doc.htm"],
                }
            }
        }
        with patch("sources.sec_13f.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": True,
                "status": 200,
                "body": json.dumps(no_13f),
                "error": None,
                "from_cache": False,
            }
            connector = Sec13FConnector(
                managers=[("Test Fund", "0001234567")]
            )
            result = connector.fetch()

        # No 13F found, but not a complete failure
        assert not result.ok
        assert "No 13F-HR" in (result.error_message or "")

    def test_fetch_http_error(self) -> None:
        with patch("sources.sec_13f.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": False,
                "status": 429,
                "body": "",
                "error": "HTTP 429: Rate limited",
                "from_cache": False,
            }
            connector = Sec13FConnector(
                managers=[("Test Fund", "0001234567")]
            )
            result = connector.fetch()

        assert not result.ok
        assert "429" in (result.error_message or "")

    def test_fetch_multiple_managers(self) -> None:
        with patch("sources.sec_13f.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": True,
                "status": 200,
                "body": json.dumps(SAMPLE_SUBMISSIONS),
                "error": None,
                "from_cache": False,
            }
            connector = Sec13FConnector(
                managers=[
                    ("Fund A", "0001111111"),
                    ("Fund B", "0002222222"),
                ]
            )
            result = connector.fetch()

        assert result.ok
        assert len(result.evidence) == 2

    def test_format_for_prompt_success(self) -> None:
        with patch("sources.sec_13f.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": True,
                "status": 200,
                "body": json.dumps(SAMPLE_SUBMISSIONS),
                "error": None,
                "from_cache": False,
            }
            connector = Sec13FConnector(
                managers=[("Berkshire Hathaway", "0001067983")]
            )
            result = connector.fetch()
            text = connector.format_for_prompt(result)

        assert "Berkshire Hathaway" in text
        assert "13F-HR" in text

    def test_format_for_prompt_failure(self) -> None:
        from evidence.schema import SourceFetchResult

        result = SourceFetchResult.failure(
            source_name="sec_13f",
            error_type="fetch_error",
            error_message="All managers failed",
        )
        connector = Sec13FConnector()
        text = connector.format_for_prompt(result)
        assert "FAILED" in text
