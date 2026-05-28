"""Federal Reserve speeches connector -- conservative HTML-based retrieval.

Fetches the speeches listing page from federalreserve.gov and extracts
recent speech metadata (title, speaker, date, URL).  For each recent
speech, fetches the speech page and extracts an excerpt.

Limitations:
  - No JSON API exists for Fed speeches.  This connector parses HTML, which
    is inherently fragile.  If the page layout changes, parsing may fail
    gracefully with empty results.
  - Only extracts the first ~2000 characters of each speech as an excerpt.
  - Policy-tone classification (hawkish/dovish) is a simple keyword heuristic,
    clearly labeled as such.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

from evidence.schema import SourceEvidence, SourceFetchResult
from sources.base import BaseConnector
from sources.sec_common import utcnow_iso


_SPEECHES_URL = "https://www.federalreserve.gov/newsevents/speeches.htm"
_BASE_URL = "https://www.federalreserve.gov"

_REQUEST_TIMEOUT = 30

# Simple policy-tone keyword lists (heuristic, not definitive)
_HAWKISH_KEYWORDS = [
    "inflation", "tighten", "restrictive", "rate hike", "higher rates",
    "price stability", "overheating", "too high", "above target",
    "persistent inflation", "wage pressure",
]
_DOVISH_KEYWORDS = [
    "employment", "labor market", "rate cut", "easing", "accommodative",
    "slow", "weakness", "downside risk", "below target", "soft landing",
    "supportive", "patient",
]


class _SpeechListParser(HTMLParser):
    """Parse the Fed speeches listing page to extract speech entries."""

    def __init__(self) -> None:
        super().__init__()
        self.speeches: list[dict[str, str]] = []
        self._in_row = False
        self._in_date = False
        self._in_link = False
        self._current: dict[str, str] = {}
        self._current_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        if tag == "div" and "eventlist" in attr_dict.get("class", ""):
            self._in_row = True
        if tag == "time" and self._in_row:
            self._in_date = True
            self._current["date"] = attr_dict.get("datetime", "")
        if tag == "a" and self._in_row:
            href = attr_dict.get("href", "")
            if href and "/newsevents/speech/" in href:
                self._in_link = True
                if href.startswith("/"):
                    href = _BASE_URL + href
                self._current["url"] = href

    def handle_endtag(self, tag: str) -> None:
        if tag == "time" and self._in_date:
            self._in_date = False
        if tag == "a" and self._in_link:
            self._current["title"] = self._current_text.strip()
            self._current_text = ""
            self._in_link = False
        if tag == "div" and self._in_row and self._current.get("url"):
            self.speeches.append(self._current)
            self._current = {}
            self._in_row = False

    def handle_data(self, data: str) -> None:
        if self._in_link:
            self._current_text += data


def _fetch_page(url: str) -> str | None:
    """Fetch a web page with a polite user-agent. Returns body or None."""
    req = urllib.request.Request(url)
    req.add_header(
        "User-Agent",
        "InsiderRoutines/1.0 (Fed speech monitor)",
    )
    req.add_header("Accept", "text/html")
    try:
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


def _extract_speech_text(html: str) -> str:
    """Extract the main speech text from a Fed speech page.

    Uses a simple regex approach to find the article body content.
    Returns the first ~2000 characters of cleaned text.
    """
    # Try to find the main content div
    match = re.search(
        r'<div[^>]*class="[^"]*col-xs-12[^"]*"[^>]*>(.*?)</div>\s*</div>',
        html,
        re.DOTALL,
    )
    if not match:
        # Fallback: just strip all tags from body
        match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL)

    if not match:
        return ""

    text = match.group(1)
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:2000]


def _extract_speaker(title: str, text: str) -> str:
    """Try to extract the speaker name from the title or first lines."""
    # Common pattern: "Governor Waller" or "Chair Powell"
    titles_pattern = (
        r"(?:Chair|Vice Chair|Governor|President)\s+"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    )
    match = re.search(titles_pattern, title)
    if match:
        return match.group(0)
    match = re.search(titles_pattern, text[:500])
    if match:
        return match.group(0)
    return "Unknown"


def keyword_tone(text: str) -> dict[str, int]:
    """Simple keyword-based policy tone heuristic.

    Returns counts of hawkish and dovish keyword matches.
    This is a rough first-pass signal, NOT a definitive classification.
    """
    lower = text.lower()
    hawkish = sum(1 for kw in _HAWKISH_KEYWORDS if kw in lower)
    dovish = sum(1 for kw in _DOVISH_KEYWORDS if kw in lower)
    return {"hawkish": hawkish, "dovish": dovish}


class FedSpeechesConnector(BaseConnector):
    """Fetch recent Federal Reserve speeches from federalreserve.gov."""

    def __init__(self, lookback_days: int = 7) -> None:
        self.lookback_days = lookback_days

    def fetch(self) -> SourceFetchResult:
        """Fetch the speeches listing page and extract recent entries."""
        html = _fetch_page(_SPEECHES_URL)
        if html is None:
            return SourceFetchResult.failure(
                source_name="fed_speeches",
                error_type="http_error",
                error_message="Failed to fetch speeches listing page",
            )

        parser = _SpeechListParser()
        try:
            parser.feed(html)
        except Exception as e:
            return SourceFetchResult.failure(
                source_name="fed_speeches",
                error_type="parse_error",
                error_message=f"HTML parse error: {e}",
            )

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.lookback_days)
        evidence_list: list[SourceEvidence] = []

        for speech in parser.speeches[:10]:  # Limit processing
            date_str = speech.get("date", "")
            try:
                speech_date = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue

            if speech_date < cutoff:
                continue

            url = speech.get("url", "")
            title = speech.get("title", "")
            excerpt = ""
            speaker = ""
            tone: dict[str, int] = {}

            # Fetch individual speech page for excerpt
            if url:
                speech_html = _fetch_page(url)
                if speech_html:
                    excerpt = _extract_speech_text(speech_html)
                    speaker = _extract_speaker(title, excerpt)
                    tone = keyword_tone(excerpt)

            evidence_list.append(
                SourceEvidence(
                    source_type="fed_speech",
                    source_name="Federal Reserve Speech",
                    source_url=url,
                    retrieved_at=utcnow_iso(),
                    canonical_id=url or None,
                    raw_excerpt=excerpt[:2000] if excerpt else None,
                    normalized={
                        "title": title,
                        "speaker": speaker,
                        "date": date_str,
                        "url": url,
                        "excerpt_length": len(excerpt),
                    },
                    metadata={
                        "hawkish_keywords": tone.get("hawkish", 0),
                        "dovish_keywords": tone.get("dovish", 0),
                        "tone_method": "keyword_heuristic",
                    },
                )
            )

        return SourceFetchResult(
            ok=True,
            source_name="fed_speeches",
            evidence=evidence_list,
        )

    def format_for_prompt(self, result: SourceFetchResult) -> str:
        """Format speech evidence as text for Claude's prompt."""
        if not result.ok:
            return (
                f"[Fed speeches fetch FAILED: {result.error_message}]\n"
                "No live speech data is available for this run. "
                "Output a NEUTRAL signal with confidence 1."
            )

        if not result.evidence:
            return (
                "[Federal Reserve: No speeches found in the last "
                f"{self.lookback_days} days.]\n"
                "Output a NEUTRAL signal with confidence 1 and reason "
                "'no Fed speeches this week'."
            )

        lines = [
            f"[Federal Reserve: {len(result.evidence)} speeches found "
            f"in the last {self.lookback_days} days]",
            "",
        ]
        for i, ev in enumerate(result.evidence, 1):
            n = ev.normalized
            lines.append(
                f"{i}. {n.get('title', '?')}"
            )
            lines.append(
                f"   Speaker: {n.get('speaker', '?')} | "
                f"Date: {n.get('date', '?')}"
            )
            hawk = ev.metadata.get("hawkish_keywords", 0)
            dove = ev.metadata.get("dovish_keywords", 0)
            lines.append(
                f"   Keyword tone (heuristic): "
                f"hawkish={hawk}, dovish={dove}"
            )
            if ev.raw_excerpt:
                # Include first 500 chars of excerpt for Claude
                lines.append(f"   Excerpt: {ev.raw_excerpt[:500]}...")
            lines.append(f"   URL: {n.get('url', '?')}")
            lines.append("")

        lines.append(
            "Analyze these speeches. For each, classify as hawkish/dovish/neutral "
            "with a supporting quote. Aggregate the net tilt for risk assets."
        )
        return "\n".join(lines)
