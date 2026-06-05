"""SEC Ticker-to-CIK resolver -- maps stock ticker symbols to SEC Central Index Key values.

Uses the SEC company tickers JSON endpoint to resolve equity ticker symbols to
issuer CIK values. Caches the mapping data to minimize network requests.

Example:
    result = resolve_ticker_to_cik("MAIA")
    if result.ok:
        print(f"{result.ticker} -> CIK {result.cik_padded} ({result.company_name})")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sources.sec_common import sec_fetch, utcnow_iso

# SEC company tickers JSON endpoint
_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Cache for 7 days (company tickers change infrequently)
_CACHE_MAX_AGE = 7 * 24 * 3600


@dataclass
class TickerCikResult:
    """Represents the result of resolving a ticker symbol to an SEC CIK.

    Attributes:
        ok: Whether resolution was successful
        ticker: Normalized ticker symbol (uppercase)
        cik: CIK as integer (0 if not found)
        cik_padded: Zero-padded 10-digit CIK string
        company_name: SEC company/issuer title
        source_url: SEC source URL for reference
        retrieved_at: ISO 8601 UTC timestamp of resolution
        error_type: Error category if resolution failed
        error_message: Human-readable error description
    """

    ok: bool
    ticker: str
    cik: int = 0
    cik_padded: str = ""
    company_name: str = ""
    source_url: str = ""
    retrieved_at: str = ""
    error_type: str | None = None
    error_message: str | None = None

    @staticmethod
    def success(
        ticker: str, cik: int, company_name: str, source_url: str
    ) -> TickerCikResult:
        """Create a successful resolution result."""
        return TickerCikResult(
            ok=True,
            ticker=ticker.upper(),
            cik=cik,
            cik_padded=str(cik).zfill(10),
            company_name=company_name,
            source_url=source_url,
            retrieved_at=utcnow_iso(),
        )

    @staticmethod
    def failure(
        ticker: str, error_type: str, error_message: str
    ) -> TickerCikResult:
        """Create a failed resolution result."""
        return TickerCikResult(
            ok=False,
            ticker=ticker.upper(),
            error_type=error_type,
            error_message=error_message,
            retrieved_at=utcnow_iso(),
        )


def _normalize_ticker(ticker: str) -> str:
    """Normalize a ticker symbol for lookup.

    Args:
        ticker: Raw ticker symbol input

    Returns:
        Normalized ticker (uppercase, trimmed)
    """
    return ticker.strip().upper()


def _fetch_company_tickers() -> dict[str, Any]:
    """Fetch SEC company tickers mapping data.

    Returns:
        dict with keys:
            ok: bool (success/failure)
            data: dict[int, dict] (mapping data if successful)
            error: str | None (error message if failed)
    """
    resp = sec_fetch(_COMPANY_TICKERS_URL, cache_max_age=_CACHE_MAX_AGE)

    if not resp["ok"]:
        return {
            "ok": False,
            "data": {},
            "error": resp["error"] or "Unknown error fetching company tickers",
        }

    try:
        data = json.loads(resp["body"])
        # SEC returns {0: {...}, 1: {...}, ...}
        return {"ok": True, "data": data, "error": None}
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "data": {},
            "error": f"Invalid JSON from SEC company tickers: {e}",
        }


def resolve_ticker_to_cik(ticker: str) -> TickerCikResult:
    """Resolve an equity ticker symbol to SEC CIK metadata.

    Fetches the SEC company tickers mapping and searches for the given ticker.
    Results are cached to minimize network requests.

    Args:
        ticker: Stock ticker symbol (e.g., "MAIA", "AAPL")

    Returns:
        TickerCikResult with resolution status and data

    Example:
        result = resolve_ticker_to_cik("MAIA")
        if result.ok:
            print(f"CIK: {result.cik_padded}")
            print(f"Company: {result.company_name}")
        else:
            print(f"Error: {result.error_message}")
    """
    normalized = _normalize_ticker(ticker)

    # Fetch company tickers mapping
    fetch_result = _fetch_company_tickers()
    if not fetch_result["ok"]:
        return TickerCikResult.failure(
            normalized,
            "sec_fetch_failed",
            fetch_result["error"] or "Failed to fetch SEC company tickers",
        )

    # Search for ticker in mapping
    # SEC data format: {0: {cik_str, ticker, title}, 1: {...}, ...}
    data = fetch_result["data"]
    for entry in data.values():
        if not isinstance(entry, dict):
            continue

        entry_ticker = entry.get("ticker", "").upper()
        if entry_ticker == normalized:
            cik = int(entry.get("cik_str", 0))
            title = entry.get("title", "")
            return TickerCikResult.success(
                normalized, cik, title, _COMPANY_TICKERS_URL
            )

    # Ticker not found in SEC mapping
    return TickerCikResult.failure(
        normalized,
        "ticker_not_found",
        f"Ticker '{normalized}' not found in SEC company tickers mapping",
    )


class SecTickerResolver:
    """Resolve stock tickers to SEC issuer CIK values using SEC company tickers data.

    This class provides an object-oriented interface to ticker-to-CIK resolution,
    suitable for use in connectors that need to resolve multiple tickers.

    Example:
        resolver = SecTickerResolver()
        result = resolver.resolve("MAIA")
        if result.ok:
            print(f"Resolved: {result.ticker} -> CIK {result.cik_padded}")
    """

    def resolve(self, ticker: str) -> TickerCikResult:
        """Resolve a ticker symbol to SEC CIK metadata.

        Args:
            ticker: Stock ticker symbol

        Returns:
            TickerCikResult with resolution status and data
        """
        return resolve_ticker_to_cik(ticker)
