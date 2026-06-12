"""SEC companyfacts API retrieval and parsing.

The SEC companyfacts API provides structured XBRL facts for each CIK:
https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json

This module fetches and parses companyfacts JSON to extract financial concepts
organized by taxonomy (us-gaap, dei, etc.) and units (USD, shares, etc.).

Example:
    >>> result = fetch_companyfacts("0001878313")
    >>> if result["ok"]:
    ...     facts = result["body"]["facts"]["us-gaap"]
    ...     cash = facts.get("Cash", {})
"""

from __future__ import annotations

import json
from sources.sec_common import sec_fetch


def fetch_companyfacts(cik: str) -> dict[str, any]:
    """Fetch SEC companyfacts JSON for a CIK.

    Args:
        cik: SEC Central Index Key (with or without leading zeros)

    Returns:
        dict with keys:
            ok: bool - whether fetch succeeded
            body: dict - parsed companyfacts JSON if ok=True
            error: str - error message if ok=False
            url: str - companyfacts URL
            from_cache: bool - whether response was from cache

    Example:
        >>> result = fetch_companyfacts("0001878313")
        >>> result["ok"]
        True
        >>> result["body"]["entityName"]
        "MAIA BIOTECHNOLOGY, INC."
    """
    # Ensure CIK is padded to 10 digits for SEC API
    cik_padded = cik.zfill(10)

    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"

    # Use 24-hour cache for companyfacts data (relatively static)
    resp = sec_fetch(url, cache_max_age=86400)

    if not resp["ok"]:
        return {
            "ok": False,
            "error": resp.get("error", "Unknown error"),
            "url": url,
        }

    try:
        data = json.loads(resp["body"])
        return {
            "ok": True,
            "body": data,
            "url": url,
            "from_cache": resp.get("from_cache", False),
        }
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"Invalid JSON from SEC companyfacts: {e}",
            "url": url,
        }


def parse_companyfacts(companyfacts_json: dict) -> dict[str, any]:
    """Parse companyfacts JSON into normalized structure.

    Args:
        companyfacts_json: Raw companyfacts JSON from SEC API or fixture

    Returns:
        dict with keys:
            ok: bool - whether parse succeeded
            cik: str - CIK from companyfacts
            entity_name: str - company name
            facts: dict - facts organized by taxonomy (us-gaap, dei, etc.)
            error: str - error message if ok=False

    Example:
        >>> parsed = parse_companyfacts(companyfacts_json)
        >>> parsed["ok"]
        True
        >>> parsed["entity_name"]
        "MAIA BIOTECHNOLOGY, INC."
        >>> "us-gaap" in parsed["facts"]
        True
    """
    try:
        return {
            "ok": True,
            "cik": companyfacts_json.get("cik", ""),
            "entity_name": companyfacts_json.get("entityName", ""),
            "facts": companyfacts_json.get("facts", {}),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"Failed to parse companyfacts: {e}",
        }


def get_concept_values(
    facts: dict,
    concept: str,
    taxonomy: str = "us-gaap",
    unit: str = "USD"
) -> list[dict]:
    """Extract all values for a specific concept from companyfacts.

    Args:
        facts: Facts dict from parsed companyfacts (e.g., parsed["facts"])
        concept: XBRL concept name (e.g., "Cash", "Assets")
        taxonomy: Taxonomy namespace (default: "us-gaap")
        unit: Unit to extract (default: "USD", can also be "shares")

    Returns:
        List of value dicts, each with keys:
            val: numeric value
            end: period end date (YYYY-MM-DD)
            start: period start date (YYYY-MM-DD) if duration-based
            accn: accession number
            fy: fiscal year
            fp: fiscal period (Q1, Q2, Q3, Q4, FY)
            form: form type (10-Q, 10-K, etc.)
            filed: filing date (YYYY-MM-DD)
            frame: frame identifier (optional)

    Example:
        >>> values = get_concept_values(facts["us-gaap"], "Cash")
        >>> latest = values[-1]
        >>> latest["val"]
        34413110
    """
    taxonomy_facts = facts.get(taxonomy, {})
    concept_data = taxonomy_facts.get(concept, {})
    units_data = concept_data.get("units", {})
    values = units_data.get(unit, [])
    return values


def get_latest_value(
    facts: dict,
    concept: str,
    taxonomy: str = "us-gaap",
    unit: str = "USD",
    form_filter: str | None = None,
    fiscal_period_filter: str | None = None
) -> dict | None:
    """Get the latest value for a concept with optional filters.

    Args:
        facts: Facts dict from parsed companyfacts
        concept: XBRL concept name
        taxonomy: Taxonomy namespace (default: "us-gaap")
        unit: Unit to extract (default: "USD")
        form_filter: Filter to specific form (e.g., "10-Q", "10-K")
        fiscal_period_filter: Filter to fiscal period (e.g., "Q1", "FY")

    Returns:
        Latest value dict or None if concept not found

    Example:
        >>> latest_q_cash = get_latest_value(facts, "Cash", form_filter="10-Q")
        >>> latest_q_cash["end"]
        "2026-03-31"
    """
    values = get_concept_values(facts, concept, taxonomy, unit)

    # Apply filters
    if form_filter:
        values = [v for v in values if v.get("form") == form_filter]

    if fiscal_period_filter:
        values = [v for v in values if v.get("fp") == fiscal_period_filter]

    # Return latest (values are chronologically ordered by SEC)
    return values[-1] if values else None
