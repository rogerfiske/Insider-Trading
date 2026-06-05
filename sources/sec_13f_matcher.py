"""SEC 13F issuer matching for ticker drilldowns.

Matches ticker-resolved issuer names to 13F holdings using CUSIP (when available)
or normalized issuer name matching.

Example:
    # Match MAIA to 13F holdings
    matches = match_ticker_to_13f_holdings(
        ticker="MAIA",
        resolved_company_name="MAIA Biotechnology, Inc.",
        resolved_cik="0001878313",
        holdings=[...],
        cusip=None  # CUSIP not available from ticker resolution
    )

    for match in matches:
        if match.confidence == "EXACT_ISSUER_NAME":
            print(f"Found holding: {match.holding.issuer_name}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sources.sec_13f_parser import Form13FHolding


@dataclass
class IssuerIdentifier:
    """Represents normalized issuer identifiers used for 13F matching.

    Attributes:
        ticker: Stock ticker symbol
        cik: SEC CIK (if available)
        company_name: Official company name from SEC
        cusip: CUSIP identifier (if available)
        normalized_names: List of normalized name variants for matching
    """

    ticker: str
    cik: str | None
    company_name: str
    cusip: str | None = None
    normalized_names: list[str] = None

    def __post_init__(self) -> None:
        if self.normalized_names is None:
            self.normalized_names = _normalize_issuer_name(self.company_name)


@dataclass
class HoldingMatchResult:
    """Represents the result of matching a ticker-resolved issuer to a 13F holding.

    Attributes:
        holding: The matched 13F holding
        confidence: Match confidence level
        match_method: Description of how the match was made
        ticker: Original ticker that was matched
    """

    holding: Form13FHolding
    confidence: str  # EXACT_CUSIP, EXACT_ISSUER_NAME, NORMALIZED_ISSUER_NAME, FUZZY_ISSUER_NAME
    match_method: str
    ticker: str


def _normalize_issuer_name(name: str) -> list[str]:
    """Normalize an issuer name into multiple variant forms for matching.

    Args:
        name: Issuer/company name

    Returns:
        List of normalized name variants (most specific to least specific)

    Example:
        "MAIA Biotechnology, Inc." ->
        [
            "maia biotechnology inc",
            "maia biotechnology",
            "maia",
        ]
    """
    if not name:
        return []

    # Convert to lowercase
    normalized = name.lower()

    # Remove common suffixes and punctuation
    normalized = re.sub(r'\s+(inc\.?|corp\.?|ltd\.?|llc|l\.?l\.?c\.?|co\.?|company|incorporated|corporation|limited)\s*$', '', normalized)
    normalized = re.sub(r'[,\.]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()

    variants = []

    # Full normalized form
    if normalized:
        variants.append(normalized)

    # First word only (for single-word tickers like "MAIA")
    first_word = normalized.split()[0] if normalized else ""
    if first_word and first_word not in variants:
        variants.append(first_word)

    return variants


def _calculate_match_confidence(
    resolved_name: str,
    holding_name: str,
    cusip_match: bool = False,
) -> tuple[str, str]:
    """Calculate match confidence level and method.

    Args:
        resolved_name: Ticker-resolved company name
        holding_name: 13F holding issuer name
        cusip_match: Whether this is a CUSIP-based match

    Returns:
        Tuple of (confidence, match_method)
    """
    if cusip_match:
        return ("EXACT_CUSIP", f"Matched by CUSIP")

    # Check for exact name match (ignoring case and punctuation)
    resolved_normalized = re.sub(r'[,\.\s]+', '', resolved_name.lower())
    holding_normalized = re.sub(r'[,\.\s]+', '', holding_name.lower())

    if resolved_normalized == holding_normalized:
        return ("EXACT_ISSUER_NAME", f"Exact issuer name match: '{holding_name}'")

    # Check for normalized variants
    resolved_variants = _normalize_issuer_name(resolved_name)
    holding_variants = _normalize_issuer_name(holding_name)

    # Check if any resolved variant matches any holding variant
    for r_var in resolved_variants:
        for h_var in holding_variants:
            if r_var == h_var:
                return ("NORMALIZED_ISSUER_NAME", f"Normalized name match: '{r_var}' = '{h_var}'")

    # Check if resolved name is contained in holding name or vice versa
    if resolved_normalized in holding_normalized or holding_normalized in resolved_normalized:
        return ("FUZZY_ISSUER_NAME", f"Fuzzy name match (substring): '{resolved_name}' ~ '{holding_name}'")

    return ("NO_MATCH", "No match")


def match_ticker_to_13f_holdings(
    ticker: str,
    resolved_company_name: str,
    resolved_cik: str | None,
    holdings: list[Form13FHolding],
    cusip: str | None = None,
) -> list[HoldingMatchResult]:
    """Match a ticker-resolved issuer to 13F holdings.

    Args:
        ticker: Stock ticker symbol
        resolved_company_name: Official company name from ticker resolution
        resolved_cik: CIK from ticker resolution (if available)
        holdings: List of 13F holdings to search
        cusip: CUSIP identifier if available (optional)

    Returns:
        List of HoldingMatchResult for all matches (may be empty)

    Matching priority:
        1. CUSIP match (if CUSIP provided and holding has matching CUSIP)
        2. Exact issuer name match (case/punctuation-insensitive)
        3. Normalized issuer name match (common suffixes removed)
        4. Fuzzy issuer name match (substring matching)
    """
    matches = []

    # Create issuer identifier for matching
    identifier = IssuerIdentifier(
        ticker=ticker,
        cik=resolved_cik,
        company_name=resolved_company_name,
        cusip=cusip,
    )

    for holding in holdings:
        # Try CUSIP match first if available
        if cusip and holding.cusip and holding.cusip.upper() == cusip.upper():
            confidence, method = _calculate_match_confidence(
                resolved_company_name,
                holding.issuer_name,
                cusip_match=True,
            )
            matches.append(
                HoldingMatchResult(
                    holding=holding,
                    confidence=confidence,
                    match_method=method,
                    ticker=ticker,
                )
            )
            continue

        # Try issuer name matching
        confidence, method = _calculate_match_confidence(
            resolved_company_name,
            holding.issuer_name,
            cusip_match=False,
        )

        # Only include confident matches
        if confidence in ("EXACT_ISSUER_NAME", "NORMALIZED_ISSUER_NAME"):
            matches.append(
                HoldingMatchResult(
                    holding=holding,
                    confidence=confidence,
                    match_method=method,
                    ticker=ticker,
                )
            )

    return matches


def summarize_13f_matches_for_report(
    ticker: str,
    matches: list[HoldingMatchResult],
) -> dict[str, Any]:
    """Summarize 13F holding matches for diagnostic reporting.

    Args:
        ticker: Stock ticker symbol
        matches: List of holding match results

    Returns:
        Dictionary with summary statistics
    """
    if not matches:
        return {
            "ticker": ticker,
            "match_count": 0,
            "total_value_usd": 0.0,
            "total_shares": 0.0,
            "managers": [],
            "matches": [],
        }

    # Group by manager
    managers_dict = {}
    for match in matches:
        mgr_name = match.holding.manager_name
        if mgr_name not in managers_dict:
            managers_dict[mgr_name] = {
                "name": mgr_name,
                "cik": match.holding.manager_cik,
                "report_period": match.holding.report_period,
                "holdings": [],
            }
        managers_dict[mgr_name]["holdings"].append(match)

    # Calculate totals
    total_value_usd = sum(match.holding.value_usd for match in matches)
    total_shares = sum(
        match.holding.shares_or_principal_amount
        for match in matches
        if match.holding.share_type == "SH"
    )

    return {
        "ticker": ticker,
        "match_count": len(matches),
        "total_value_usd": total_value_usd,
        "total_shares": total_shares,
        "managers": list(managers_dict.values()),
        "matches": matches,
    }
