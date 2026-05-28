"""Tests for SEC Form 4 connector."""

from __future__ import annotations

import json
from unittest.mock import patch

from sources.sec_form4 import SecForm4Connector


# Sample EFTS search response
SAMPLE_EFTS_RESPONSE = {
    "hits": {
        "hits": [
            {
                "_id": "0001234567-26-000001",
                "_source": {
                    "file_date": "2026-01-15",
                    "display_names": ["John Smith", "CEO"],
                    "entity_name": "ACME Corp",
                    "file_num": "001-12345",
                    "period_of_report": "2026-01-14",
                    "file_path": "/Archives/edgar/data/123456/",
                },
            },
            {
                "_id": "0009876543-26-000002",
                "_source": {
                    "file_date": "2026-01-15",
                    "display_names": ["Jane Doe", "Director"],
                    "entity_name": "Widget Inc",
                    "file_num": "001-67890",
                    "period_of_report": "2026-01-14",
                    "file_path": "/Archives/edgar/data/789012/",
                },
            },
        ]
    }
}


class TestSecForm4Connector:
    def test_fetch_success(self) -> None:
        with patch("sources.sec_form4.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": True,
                "status": 200,
                "body": json.dumps(SAMPLE_EFTS_RESPONSE),
                "error": None,
                "from_cache": False,
            }
            connector = SecForm4Connector()
            result = connector.fetch()

        assert result.ok
        assert result.source_name == "sec_form4"
        assert len(result.evidence) == 2
        assert result.evidence[0].normalized["entity_name"] == "ACME Corp"
        assert result.evidence[0].canonical_id == "0001234567-26-000001"

    def test_fetch_empty_results(self) -> None:
        with patch("sources.sec_form4.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": True,
                "status": 200,
                "body": json.dumps({"hits": {"hits": []}}),
                "error": None,
                "from_cache": False,
            }
            connector = SecForm4Connector()
            result = connector.fetch()

        assert result.ok
        assert len(result.evidence) == 0

    def test_fetch_http_error(self) -> None:
        with patch("sources.sec_form4.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": False,
                "status": 403,
                "body": "",
                "error": "HTTP 403: Forbidden",
                "from_cache": False,
            }
            connector = SecForm4Connector()
            result = connector.fetch()

        assert not result.ok
        assert result.error_type == "http_error"
        assert "403" in (result.error_message or "")

    def test_fetch_invalid_json(self) -> None:
        with patch("sources.sec_form4.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": True,
                "status": 200,
                "body": "not json",
                "error": None,
                "from_cache": False,
            }
            connector = SecForm4Connector()
            result = connector.fetch()

        assert not result.ok
        assert result.error_type == "parse_error"

    def test_format_for_prompt_success(self) -> None:
        with patch("sources.sec_form4.sec_fetch") as mock_fetch:
            mock_fetch.return_value = {
                "ok": True,
                "status": 200,
                "body": json.dumps(SAMPLE_EFTS_RESPONSE),
                "error": None,
                "from_cache": False,
            }
            connector = SecForm4Connector()
            result = connector.fetch()
            text = connector.format_for_prompt(result)

        assert "ACME Corp" in text
        assert "Widget Inc" in text
        assert "2 filings found" in text

    def test_format_for_prompt_failure(self) -> None:
        from evidence.schema import SourceFetchResult

        result = SourceFetchResult.failure(
            source_name="sec_form4",
            error_type="http_error",
            error_message="403 Forbidden",
        )
        connector = SecForm4Connector()
        text = connector.format_for_prompt(result)
        assert "FAILED" in text
        assert "NEUTRAL" in text

    def test_format_for_prompt_empty(self) -> None:
        from evidence.schema import SourceFetchResult

        result = SourceFetchResult(
            ok=True, source_name="sec_form4", evidence=[]
        )
        connector = SecForm4Connector()
        text = connector.format_for_prompt(result)
        assert "No filings found" in text
