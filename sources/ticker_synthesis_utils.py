"""
Generic Ticker Synthesis Utilities

Common functions for generating generic ticker research packets.

SAFETY:
- SEC EDGAR public filings only
- NO Roger's uploaded spreadsheets
- NO OpenInsider data
- NO Telegram/email alerts
- NO scheduled task modification
- NO .env access
- NO buy/sell/hold recommendations
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_safety_flags() -> Dict[str, bool]:
    """Return standard safety flags for all outputs."""
    return {
        "report_only": True,
        "alerts_generated": False,
        "openinsider_spreadsheet_used": False,
        "telegram_sent": False,
        "email_sent": False,
        "scheduled_tasks_modified": False,
        "env_printed_or_changed": False,
        "buy_sell_hold_language_used": False,
    }


def get_ticker_profile_type(ticker: str, manual_profile: Optional[str] = None) -> str:
    """
    Determine ticker profile type for module activation.

    Args:
        ticker: Stock ticker symbol
        manual_profile: Optional manual override

    Returns:
        One of: biotech_clinical, small_cap_operating_company,
                pre_revenue_company, unknown_profile
    """
    if manual_profile:
        valid_profiles = [
            "biotech_clinical",
            "small_cap_operating_company",
            "pre_revenue_company",
            "unknown_profile",
        ]
        if manual_profile in valid_profiles:
            return manual_profile

    # For now, return unknown and require manual specification
    # In future, could infer from SIC code or 10-K/10-Q filing content
    return "unknown_profile"


def get_source_boundary(ticker: str, checkpoint: Optional[str] = None) -> List[str]:
    """Return approved source boundary for ticker research."""
    sources = [
        "SEC EDGAR public filings only",
        f"Generic ticker workflow for {ticker}",
        "NO Roger's uploaded MAIA spreadsheet",
        "NO OpenInsider data",
    ]

    if checkpoint:
        sources.insert(1, f"Checkpoint: {checkpoint}")

    return sources


def get_evidence_matrix_template() -> List[Dict[str, Any]]:
    """Return template for evidence matrix with standard categories."""
    return [
        {
            "category": "Insider buying strength",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "Insider selling absence/presence",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "Buyer/seller breadth",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "Recency of insider activity",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "Persistence over time",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "Capital raise / cash position",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "Dilution overhang",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "Cash runway / liquidity",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "13D/G ownership",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "13F institutional visibility",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "Form 144 selling intent",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
        {
            "category": "Market confirmation",
            "evidence": "",
            "direction": "Unknown",
            "strength": "N/A",
            "confidence": "Low",
            "source": "",
            "comment": "",
        },
    ]


def calculate_insider_score(purchases: int, sales: int, purchase_value: float, sale_value: float) -> int:
    """
    Calculate insider evidence score (0-100).

    Args:
        purchases: Number of open-market purchases
        sales: Number of open-market sales
        purchase_value: Total purchase value USD
        sale_value: Total sale value USD

    Returns:
        Score 0-100 (higher = stronger buying evidence)
    """
    if purchases == 0 and sales == 0:
        return 0

    # Perfect score: purchases > 0, sales = 0
    if purchases > 0 and sales == 0:
        return 100

    # Strong buying but some selling
    if purchases > sales * 3 and purchase_value > sale_value * 3:
        return 85

    # More buying than selling
    if purchases > sales and purchase_value > sale_value:
        return 70

    # Balanced
    if abs(purchases - sales) <= 2:
        return 50

    # More selling than buying
    if sales > purchases:
        return max(0, 30 - (sales - purchases) * 5)

    return 50


def get_insider_rating(score: int) -> str:
    """Convert insider score to rating label."""
    if score >= 95:
        return "Very Strong Insider Buying Evidence"
    elif score >= 80:
        return "Strong Insider Buying Evidence"
    elif score >= 65:
        return "Moderate Insider Buying Evidence"
    elif score >= 45:
        return "Mixed Insider Activity"
    elif score >= 25:
        return "Weak Insider Buying Evidence"
    else:
        return "Insider Selling Dominates"


def get_overall_posture(
    insider_score: int,
    cash_runway_months: Optional[float],
    clinical_data_timing_known: bool,
    has_business_milestones: bool,
) -> str:
    """
    Determine overall research posture label (NO buy/sell/hold language).

    Args:
        insider_score: Insider evidence score (0-100)
        cash_runway_months: Cash runway in months, or None if revenue-positive
        clinical_data_timing_known: Whether clinical catalyst timing is known
        has_business_milestones: Whether operating milestones are defined

    Returns:
        Posture label without recommendation language
    """
    # Strong insider evidence
    if insider_score >= 80:
        if cash_runway_months is not None and not clinical_data_timing_known:
            return "Strong insider-evidence / high clinical-timing uncertainty profile"
        elif cash_runway_months is not None and cash_runway_months < 12:
            return "Strong insider-evidence / near-term financing risk profile"
        elif not clinical_data_timing_known and not has_business_milestones:
            return "Strong insider-evidence / high catalyst-timing uncertainty profile"
        else:
            return "Strong insider-evidence / improving confirmation profile"

    # Moderate insider evidence
    elif insider_score >= 50:
        return "Mixed evidence / moderate uncertainty profile"

    # Weak insider evidence
    elif insider_score >= 25:
        return "Weak insider-evidence / incomplete data profile"

    # Minimal evidence
    else:
        return "Incomplete evidence / high uncertainty profile"


def load_maia_baseline() -> Dict[str, Any]:
    """
    Load approved MAIA baseline values for validation.

    Returns:
        Dict with MAIA baseline values
    """
    return {
        "ticker": "MAIA",
        "cik": "0001878313",
        "insider_purchases": 134,
        "insider_sales": 0,
        "purchase_value_usd": 4921437.58,
        "distinct_buyers": 10,
        "latest_purchase_date": "2026-06-01",
        "cash_balance_usd": 34413110,
        "working_capital_usd": 28992690,
        "operating_cash_burn_quarterly": 5311328,
        "base_runway_months": 19.4,
        "offering_reference_price_usd": 1.50,
        "common_shares_outstanding": 60671491,
        "approximate_fully_diluted_shares": 86860000,
        "13f_visibility": "partial; no MAIA matches among parsed filings",
        "critical_unknown": "THIO-104 Phase 3 timing not disclosed",
    }


def validate_safety_flags(data: Dict[str, Any]) -> List[str]:
    """
    Validate that safety flags are correctly set.

    Args:
        data: Output JSON data containing safety section

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if "safety" not in data:
        errors.append("Missing 'safety' section")
        return errors

    safety = data["safety"]
    expected = get_safety_flags()

    for flag, expected_value in expected.items():
        if flag not in safety:
            errors.append(f"Missing safety flag: {flag}")
        elif safety[flag] != expected_value:
            errors.append(
                f"Safety flag '{flag}': expected {expected_value}, got {safety[flag]}"
            )

    return errors


def validate_no_recommendation_language(data: Dict[str, Any]) -> List[str]:
    """
    Validate that output contains no buy/sell/hold recommendation language.

    Args:
        data: Output JSON data

    Returns:
        List of violations (empty if clean)
    """
    violations = []

    # Convert to JSON string for text search
    text = json.dumps(data).lower()

    forbidden = [
        "strong buy",
        "strong sell",
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "price target",
        "expected return",
        "investment recommendation",
    ]

    for term in forbidden:
        if term in text:
            violations.append(f"Found forbidden recommendation language: '{term}'")

    return violations


def save_json_output(data: Dict[str, Any], output_path: Path) -> None:
    """
    Save JSON output with proper formatting.

    Args:
        data: Data to save
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Saved JSON to: {output_path}")


def save_markdown_output(content: str, output_path: Path) -> None:
    """
    Save markdown output.

    Args:
        content: Markdown content
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] Saved Markdown to: {output_path}")
