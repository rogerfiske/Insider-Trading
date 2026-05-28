"""Tests for Federal Reserve speeches connector."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sources.fed_speeches import (
    FedSpeechesConnector,
    _extract_speaker,
    _extract_speech_text,
    keyword_tone,
)


# Sample speeches listing HTML (simplified structure)
SAMPLE_SPEECHES_HTML = """
<html><body>
<div class="eventlist">
  <time datetime="{date1}"></time>
  <a href="/newsevents/speech/test20260115a.htm">Governor Waller on Monetary Policy</a>
</div>
<div class="eventlist">
  <time datetime="{date2}"></time>
  <a href="/newsevents/speech/test20260110a.htm">Chair Powell on Economic Outlook</a>
</div>
<div class="eventlist">
  <time datetime="2025-06-01"></time>
  <a href="/newsevents/speech/old.htm">Old Speech</a>
</div>
</body></html>
"""

SAMPLE_SPEECH_PAGE = """
<html><body>
<div class="col-xs-12 col-sm-8 col-md-8">
<p>Good morning. I want to discuss the current state of inflation and our
commitment to price stability. Inflation remains too high and we must maintain
a restrictive stance. Rate hikes may be necessary if inflation persists.
However, the labor market shows signs of soft landing.</p>
</div>
</div>
</body></html>
"""


class TestKeywordTone:
    def test_hawkish_text(self) -> None:
        text = "Inflation remains too high. We must tighten restrictive policy."
        tone = keyword_tone(text)
        assert tone["hawkish"] > 0
        assert tone["hawkish"] > tone["dovish"]

    def test_dovish_text(self) -> None:
        text = "The labor market weakness suggests we should be patient and accommodative."
        tone = keyword_tone(text)
        assert tone["dovish"] > 0
        assert tone["dovish"] > tone["hawkish"]

    def test_neutral_text(self) -> None:
        text = "The weather is nice today."
        tone = keyword_tone(text)
        assert tone["hawkish"] == 0
        assert tone["dovish"] == 0


class TestExtractSpeaker:
    def test_from_title(self) -> None:
        speaker = _extract_speaker("Governor Waller on Monetary Policy", "")
        assert "Waller" in speaker

    def test_chair_powell(self) -> None:
        speaker = _extract_speaker("Chair Powell on Economic Outlook", "")
        assert "Powell" in speaker

    def test_unknown(self) -> None:
        speaker = _extract_speaker("Some Title", "some text")
        assert speaker == "Unknown"


class TestExtractSpeechText:
    def test_extracts_text(self) -> None:
        text = _extract_speech_text(SAMPLE_SPEECH_PAGE)
        assert "inflation" in text.lower()
        assert len(text) > 0

    def test_truncates_long_text(self) -> None:
        long_page = (
            '<html><body><div class="col-xs-12">'
            + "word " * 1000
            + "</div></div></body></html>"
        )
        text = _extract_speech_text(long_page)
        assert len(text) <= 2000

    def test_empty_html(self) -> None:
        text = _extract_speech_text("")
        assert text == ""


class TestFedSpeechesConnector:
    def _make_html(self) -> str:
        now = datetime.now(timezone.utc)
        d1 = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        d2 = (now - timedelta(days=3)).strftime("%Y-%m-%d")
        return SAMPLE_SPEECHES_HTML.format(date1=d1, date2=d2)

    def test_fetch_success(self) -> None:
        html = self._make_html()
        with patch("sources.fed_speeches._fetch_page") as mock_fetch:
            mock_fetch.side_effect = [
                html,  # Listing page
                SAMPLE_SPEECH_PAGE,  # First speech
                SAMPLE_SPEECH_PAGE,  # Second speech
            ]
            connector = FedSpeechesConnector(lookback_days=7)
            result = connector.fetch()

        assert result.ok
        assert len(result.evidence) == 2
        assert "Waller" in result.evidence[0].normalized.get("speaker", "")

    def test_fetch_listing_failure(self) -> None:
        with patch("sources.fed_speeches._fetch_page", return_value=None):
            connector = FedSpeechesConnector()
            result = connector.fetch()

        assert not result.ok
        assert result.error_type == "http_error"

    def test_fetch_filters_old_speeches(self) -> None:
        # All speeches are old (> 7 days ago)
        old_html = SAMPLE_SPEECHES_HTML.format(
            date1="2025-01-01", date2="2025-01-02"
        )
        with patch("sources.fed_speeches._fetch_page") as mock_fetch:
            mock_fetch.return_value = old_html
            connector = FedSpeechesConnector(lookback_days=7)
            result = connector.fetch()

        assert result.ok
        assert len(result.evidence) == 0

    def test_format_for_prompt_success(self) -> None:
        html = self._make_html()
        with patch("sources.fed_speeches._fetch_page") as mock_fetch:
            mock_fetch.side_effect = [
                html,
                SAMPLE_SPEECH_PAGE,
                SAMPLE_SPEECH_PAGE,
            ]
            connector = FedSpeechesConnector(lookback_days=7)
            result = connector.fetch()
            text = connector.format_for_prompt(result)

        assert "speeches found" in text
        assert "hawkish" in text.lower() or "dovish" in text.lower()

    def test_format_for_prompt_failure(self) -> None:
        from evidence.schema import SourceFetchResult

        result = SourceFetchResult.failure(
            source_name="fed_speeches",
            error_type="http_error",
            error_message="Connection refused",
        )
        connector = FedSpeechesConnector()
        text = connector.format_for_prompt(result)
        assert "FAILED" in text
