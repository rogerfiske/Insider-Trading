"""Tests for evidence schema -- SourceEvidence, SourceFetchResult, EvidenceBundle."""

from __future__ import annotations

import json

from evidence.schema import EvidenceBundle, SourceEvidence, SourceFetchResult


class TestSourceEvidence:
    def test_create_basic(self) -> None:
        ev = SourceEvidence(
            source_type="sec_form4",
            source_name="SEC Form 4",
            source_url="https://example.com/filing",
            retrieved_at="2026-01-01T00:00:00Z",
        )
        assert ev.source_type == "sec_form4"
        assert ev.canonical_id is None
        assert ev.normalized == {}
        assert ev.metadata == {}

    def test_create_full(self) -> None:
        ev = SourceEvidence(
            source_type="sec_form4",
            source_name="SEC Form 4",
            source_url="https://example.com/filing",
            retrieved_at="2026-01-01T00:00:00Z",
            canonical_id="0001234567-26-000001",
            raw_excerpt="some raw text",
            normalized={"ticker": "AAPL"},
            metadata={"from_cache": False},
        )
        assert ev.canonical_id == "0001234567-26-000001"
        assert ev.normalized["ticker"] == "AAPL"

    def test_to_dict(self) -> None:
        ev = SourceEvidence(
            source_type="test",
            source_name="Test",
            source_url="https://test.com",
            retrieved_at="2026-01-01T00:00:00Z",
            normalized={"key": "value"},
        )
        d = ev.to_dict()
        assert d["source_type"] == "test"
        assert d["normalized"]["key"] == "value"

    def test_to_json_roundtrip(self) -> None:
        ev = SourceEvidence(
            source_type="test",
            source_name="Test",
            source_url="https://test.com",
            retrieved_at="2026-01-01T00:00:00Z",
            canonical_id="abc123",
        )
        json_str = ev.to_json()
        parsed = json.loads(json_str)
        ev2 = SourceEvidence.from_dict(parsed)
        assert ev2.source_type == ev.source_type
        assert ev2.canonical_id == ev.canonical_id

    def test_from_dict_missing_fields(self) -> None:
        ev = SourceEvidence.from_dict({"source_type": "x"})
        assert ev.source_type == "x"
        assert ev.source_name == ""
        assert ev.normalized == {}


class TestSourceFetchResult:
    def test_success(self) -> None:
        result = SourceFetchResult(
            ok=True,
            source_name="test",
            evidence=[
                SourceEvidence(
                    source_type="test",
                    source_name="Test",
                    source_url="https://test.com",
                    retrieved_at="2026-01-01T00:00:00Z",
                )
            ],
        )
        assert result.ok
        assert len(result.evidence) == 1
        assert result.error_type is None

    def test_failure_factory(self) -> None:
        result = SourceFetchResult.failure(
            source_name="test",
            error_type="http_error",
            error_message="404 Not Found",
        )
        assert not result.ok
        assert result.error_type == "http_error"
        assert "404" in (result.error_message or "")
        assert result.evidence == []

    def test_auto_timestamp(self) -> None:
        result = SourceFetchResult(ok=True, source_name="test")
        assert result.retrieved_at  # Should be auto-populated

    def test_to_json_roundtrip(self) -> None:
        ev = SourceEvidence(
            source_type="test",
            source_name="Test",
            source_url="https://test.com",
            retrieved_at="2026-01-01T00:00:00Z",
        )
        result = SourceFetchResult(
            ok=True,
            source_name="test",
            evidence=[ev],
        )
        json_str = result.to_json()
        parsed = json.loads(json_str)
        result2 = SourceFetchResult.from_dict(parsed)
        assert result2.ok
        assert len(result2.evidence) == 1
        assert result2.evidence[0].source_type == "test"


class TestEvidenceBundle:
    def test_create(self) -> None:
        result = SourceFetchResult(ok=True, source_name="test")
        bundle = EvidenceBundle(agent="eddie", fetch_result=result)
        assert bundle.agent == "eddie"
        assert bundle.evidence_path is None

    def test_to_dict(self) -> None:
        result = SourceFetchResult(ok=True, source_name="test")
        bundle = EvidenceBundle(
            agent="eddie",
            fetch_result=result,
            evidence_path="/tmp/test.json",
        )
        d = bundle.to_dict()
        assert d["agent"] == "eddie"
        assert d["evidence_path"] == "/tmp/test.json"
        assert d["fetch_result"]["ok"] is True
