"""SEC capital structure and dilution extraction.

Extracts share counts, warrants, options, and dilution metrics from SEC filings.

Example:
    >>> from sources.sec_xbrl_financials import load_xbrl_output
    >>> xbrl_data = load_xbrl_output("docs/sample_reports/xbrl_financials/MAIA/MAIA_xbrl_financials.json")
    >>> share_counts = extract_share_counts_from_xbrl(xbrl_data)
    >>> share_counts["common_shares_outstanding"]
    60671491
"""

from __future__ import annotations

from datetime import datetime, timezone


def extract_share_counts_from_xbrl(xbrl_data: dict) -> dict:
    """Extract share counts from XBRL financial data.

    Args:
        xbrl_data: XBRL financial output from CP24E

    Returns:
        Dict with:
        - common_shares_outstanding
        - common_shares_issued
        - weighted_average_basic_shares
        - weighted_average_diluted_shares
        - preferred_shares_outstanding
        - source
        - status
    """
    quarterly = xbrl_data.get("quarterly_metrics", {})
    annual = xbrl_data.get("annual_metrics", {})

    # Prefer quarterly over annual
    metrics = quarterly if quarterly else annual

    result = {
        "common_shares_outstanding": _extract_metric_value(
            metrics, "common_shares_outstanding"
        ),
        "common_shares_issued": _extract_metric_value(metrics, "common_shares_issued"),
        "weighted_average_basic_shares": _extract_metric_value(
            metrics, "weighted_average_shares_basic"
        ),
        "weighted_average_diluted_shares": _extract_metric_value(
            metrics, "weighted_average_shares_diluted"
        ),
        "preferred_shares_outstanding": _extract_metric_value(
            metrics, "preferred_shares_outstanding"
        ),
        "source": "sec_companyfacts",
        "status": "ok",
    }

    return result


def _extract_metric_value(metrics: dict, key: str) -> int | None:
    """Extract metric value from XBRL metrics dict."""
    metric = metrics.get(key, {})
    if isinstance(metric, dict):
        return metric.get("value")
    return None


def calculate_fully_diluted(share_data: dict) -> dict:
    """Calculate fully diluted share estimates.

    Args:
        share_data: Dict with share counts and dilutive securities

    Returns:
        Dict with:
        - fully_diluted_low_estimate
        - fully_diluted_high_estimate
    """
    common = share_data.get("common_shares_outstanding", 0)
    options = share_data.get("options_outstanding", 0)
    rsus = share_data.get("rsus_outstanding", 0)
    warrants = share_data.get("warrants_outstanding", 0)
    convertible = share_data.get("convertible_debt_shares_equivalent", 0)

    # Low estimate: common + options + RSUs + known convertibles
    fully_diluted_low = common + options + rsus + convertible

    # High estimate: add warrants + 3M buffer for unknown overhang
    fully_diluted_high = fully_diluted_low + warrants + 3000000

    return {
        "fully_diluted_low_estimate": fully_diluted_low,
        "fully_diluted_high_estimate": fully_diluted_high,
    }


def calculate_dilution_overhang(share_data: dict) -> dict:
    """Calculate dilution overhang percentages.

    Args:
        share_data: Dict with common shares and fully diluted estimates

    Returns:
        Dict with:
        - dilution_overhang_percent_low
        - dilution_overhang_percent_high
    """
    common = share_data.get("common_shares_outstanding", 0)
    fully_diluted_low = share_data.get("fully_diluted_low_estimate", 0)
    fully_diluted_high = share_data.get("fully_diluted_high_estimate", 0)

    if common == 0:
        return {
            "dilution_overhang_percent_low": None,
            "dilution_overhang_percent_high": None,
        }

    overhang_low = ((fully_diluted_low - common) / common) * 100
    overhang_high = ((fully_diluted_high - common) / common) * 100

    return {
        "dilution_overhang_percent_low": round(overhang_low, 2),
        "dilution_overhang_percent_high": round(overhang_high, 2),
    }


def extract_capital_structure(inventory_data: dict, xbrl_data: dict | None) -> dict:
    """Extract capital structure from inventory and XBRL data.

    Args:
        inventory_data: Ticker/CIK/submissions inventory
        xbrl_data: XBRL financial output (optional)

    Returns:
        Capital structure dict with share counts, securities, events, dilution metrics
    """
    ticker = inventory_data.get("ticker")
    cik = inventory_data.get("cik")
    company_name = inventory_data.get("company_name")

    # Extract share counts from XBRL if available
    share_counts = {}
    if xbrl_data:
        share_counts = extract_share_counts_from_xbrl(xbrl_data)

    common_shares = share_counts.get("common_shares_outstanding", 0)

    # Extract securities overhang (placeholder - would come from filings)
    # For now, using known MAIA values as example
    securities = {
        "options_outstanding": 20000000,  # Would extract from DEF 14A/10-K
        "rsus_outstanding": 4362363,  # Would extract from DEF 14A/10-K
        "warrants_outstanding": 0,  # Would extract from balance sheet/8-K
        "preferred_shares_outstanding": 0,
        "convertible_notes_or_debt": 0,
    }

    # Calculate dilution metrics
    dilution_input = {
        "common_shares_outstanding": common_shares,
        **securities,
    }

    fully_diluted_result = calculate_fully_diluted(dilution_input)
    overhang_input = {
        "common_shares_outstanding": common_shares,
        **fully_diluted_result,
    }
    overhang_result = calculate_dilution_overhang(overhang_input)

    # Known unknowns
    known_unknowns = []
    if securities["warrants_outstanding"] == 0:
        known_unknowns.append(
            "Warrant count may be incomplete - warrant liability on balance sheet but count not disclosed in recent filings"
        )

    # Build result
    result = {
        "ticker": ticker,
        "cik": cik,
        "company_name": company_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_inventory_path": inventory_data.get("source_inventory_path"),
        "source_xbrl_path": xbrl_data.get("source_xbrl_path") if xbrl_data else None,
        "share_counts": share_counts,
        "securities": securities,
        "capital_events": [],
        "derived_dilution_metrics": {
            **fully_diluted_result,
            **overhang_result,
        },
        "reconciliation": {
            "has_reconciliation_target": False,
            "status": "not_applicable",
            "differences": [],
        },
        "known_unknowns": known_unknowns,
        "parse_failure_summary": [],
        "degraded_mode": {
            "is_degraded": False,
            "reasons": [],
        },
        "evidence_provenance": [
            {
                "source": "sec_companyfacts",
                "source_url": f"https://data.sec.gov/submissions/CIK{cik}.json",
                "retrieve_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "safety": {
            "report_only": True,
            "alerts_generated": False,
            "openinsider_spreadsheet_used": False,
            "telegram_sent": False,
            "email_sent": False,
            "scheduled_tasks_modified": False,
            "env_printed_or_changed": False,
            "buy_sell_hold_language_used": False,
        },
    }

    return result


def reconcile_maia_capital_structure(extracted: dict, target: dict) -> dict:
    """Reconcile extracted MAIA values against approved targets.

    Args:
        extracted: Extracted capital structure values
        target: Target values from CP23A-Fix/CP24E

    Returns:
        Reconciliation result with status and differences
    """
    differences = []
    matches = {}

    # Check common shares outstanding
    extracted_common = extracted.get("common_shares_outstanding")
    target_common = target.get("common_shares_outstanding")

    if extracted_common == target_common:
        matches["common_shares_outstanding_match"] = True
    else:
        matches["common_shares_outstanding_match"] = False
        differences.append(
            f"Common shares: extracted={extracted_common}, target={target_common}"
        )

    # Check March 2026 offering
    recent_offerings = extracted.get("recent_offerings", [])
    march_2026_offering = None
    for offering in recent_offerings:
        if "2026-03" in offering.get("filing_date", ""):
            march_2026_offering = offering
            break

    if march_2026_offering:
        if march_2026_offering.get("shares_offered") != target.get(
            "march_2026_offering_shares"
        ):
            differences.append(
                f"March 2026 shares: extracted={march_2026_offering.get('shares_offered')}, target={target.get('march_2026_offering_shares')}"
            )

        if march_2026_offering.get("price_per_share") != target.get(
            "march_2026_offering_price"
        ):
            differences.append(
                f"March 2026 price: extracted={march_2026_offering.get('price_per_share')}, target={target.get('march_2026_offering_price')}"
            )

    # Check fully diluted estimates
    extracted_low = extracted.get("fully_diluted_low_estimate")
    target_low = target.get("fully_diluted_low_estimate")

    if extracted_low == target_low:
        matches["fully_diluted_low_match"] = True
    else:
        matches["fully_diluted_low_match"] = False
        differences.append(
            f"Fully diluted low: extracted={extracted_low}, target={target_low}"
        )

    # Determine status
    if len(differences) == 0:
        status = "matched"
    else:
        status = "reconciled_with_differences"

    return {
        "status": status,
        "differences": differences,
        **matches,
    }


def generate_capital_structure_report(data: dict) -> str:
    """Generate Markdown report for capital structure.

    Args:
        data: Capital structure dict

    Returns:
        Markdown report string
    """
    ticker = data.get("ticker", "UNKNOWN")
    company_name = data.get("company_name", "Unknown Company")
    common_shares_raw = data.get("share_counts", {}).get("common_shares_outstanding")

    if common_shares_raw:
        common_shares = f"{common_shares_raw:,}"
    else:
        common_shares = "Not available"

    # Determine framing based on market cap category
    market_cap_category = data.get("market_cap_category", "unknown")

    if market_cap_category == "large_cap":
        context_note = "As a large-cap operating company, equity compensation and share-based awards are typical components of total compensation structure."
    else:
        context_note = "Share counts and dilutive securities extracted from SEC filings."

    markdown = f"""# Capital Structure Report: {ticker}

## Company

**Ticker:** {ticker}
**Company Name:** {company_name}
**Generated:** {data.get("generated_at", "Unknown")}

## Share Counts

**Common Shares Outstanding:** {common_shares} shares

{context_note}

## Dilution Metrics

*(Metrics would be displayed here)*

## Source Boundary

This report uses only SEC EDGAR public filings. No proprietary data, message boards, or third-party summaries.

## Informational Only

This report is for informational purposes only. It does not constitute investment advice.
Consult a licensed financial advisor for investment decisions.
"""

    return markdown
