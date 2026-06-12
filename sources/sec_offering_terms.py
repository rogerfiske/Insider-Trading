"""SEC offering terms parser.

Parses offering terms from 424B, S-1, S-3, S-8, 8-K filings.

Example:
    >>> offering = {
    ...     "form": "424B5",
    ...     "securities_offered": "Common Stock",
    ...     "shares_offered": 20000000,
    ...     "price_per_share": 1.50
    ... }
    >>> result = parse_offering_terms(offering)
    >>> result["gross_proceeds"]
    30000000
"""

from __future__ import annotations


def parse_offering_terms(offering_data: dict) -> dict:
    """Parse offering terms from filing metadata.

    Args:
        offering_data: Dict with form, securities_offered, shares_offered, etc.

    Returns:
        Normalized offering terms dict with:
        - shares_offered
        - price_per_share
        - gross_proceeds
        - net_proceeds
        - warrants_included
        - pre_funded_warrants_included
        - placement_agent_or_underwriter_if_disclosed
        - overallotment_or_option_if_disclosed
        - parse_status
        - failure_reason (if parse_status != "success")
    """
    result = {
        "form": offering_data.get("form"),
        "accession_number": offering_data.get("accession_number"),
        "filing_date": offering_data.get("filing_date"),
        "report_date": offering_data.get("report_date"),
        "event_type": offering_data.get("event_type", "unknown"),
        "securities_offered": offering_data.get("securities_offered"),
        "shares_offered": offering_data.get("shares_offered"),
        "price_per_share": offering_data.get("price_per_share"),
        "gross_proceeds": offering_data.get("gross_proceeds"),
        "net_proceeds": offering_data.get("net_proceeds"),
        "warrants_included": offering_data.get("warrants_included", False),
        "pre_funded_warrants_included": offering_data.get(
            "pre_funded_warrants_included", False
        ),
        "placement_agent_or_underwriter_if_disclosed": offering_data.get(
            "placement_agent_or_underwriter_if_disclosed"
        ),
        "overallotment_or_option_if_disclosed": offering_data.get(
            "overallotment_or_option_if_disclosed"
        ),
        "status": offering_data.get("status", "unknown"),
        "parse_status": offering_data.get("parse_status", "success"),
        "failure_reason": offering_data.get("failure_reason"),
    }

    # Calculate gross proceeds if not provided but inputs available
    if (
        result["gross_proceeds"] is None
        and result["shares_offered"] is not None
        and result["price_per_share"] is not None
    ):
        result["gross_proceeds"] = result["shares_offered"] * result["price_per_share"]

    # Degraded parse status if critical fields missing
    if result["securities_offered"] and "unknown" in result["securities_offered"].lower():
        if result["parse_status"] == "success":
            result["parse_status"] = "degraded"
            result["failure_reason"] = "Unknown securities type"

    if not result["shares_offered"] and not result.get("shelf_amount"):
        if result["parse_status"] == "success":
            result["parse_status"] = "partial"
            if not result.get("failure_reason"):
                result["failure_reason"] = "Shares offered not disclosed"

    return result


def extract_offering_terms_from_filing(
    filing: dict, form: str
) -> dict | None:
    """Extract offering terms from a filing dict.

    Args:
        filing: Filing dict from submissions inventory
        form: Form type (424B5, S-1, S-3, S-8, etc.)

    Returns:
        Parsed offering terms or None if not offering-related form
    """
    # Map form types to event types
    event_type_map = {
        "424B5": "prospectus_supplement",
        "424B3": "prospectus_supplement",
        "424B4": "prospectus_supplement",
        "424B7": "prospectus_supplement",
        "S-1": "initial_public_offering",
        "S-1/A": "initial_public_offering",
        "S-3": "shelf_registration",
        "S-3/A": "shelf_registration",
        "S-3ASR": "shelf_registration",
        "S-8": "equity_compensation_registration",
        "8-K": "current_report_event",
    }

    event_type = event_type_map.get(form, "unknown")

    offering_data = {
        "form": filing.get("form", form),
        "accession_number": filing.get("accession_number"),
        "filing_date": filing.get("filing_date"),
        "report_date": filing.get("report_date"),
        "event_type": event_type,
        "securities_offered": filing.get("securities_offered", "Not disclosed"),
        "shares_offered": filing.get("shares_offered"),
        "price_per_share": filing.get("price_per_share"),
        "gross_proceeds": filing.get("gross_proceeds"),
        "net_proceeds": filing.get("net_proceeds"),
        "warrants_included": filing.get("warrants_included", False),
        "pre_funded_warrants_included": filing.get(
            "pre_funded_warrants_included", False
        ),
        "placement_agent_or_underwriter_if_disclosed": filing.get(
            "placement_agent_or_underwriter_if_disclosed"
        ),
        "overallotment_or_option_if_disclosed": filing.get(
            "overallotment_or_option_if_disclosed"
        ),
        "status": filing.get("status", "unknown"),
        "parse_status": "success",
    }

    return parse_offering_terms(offering_data)
