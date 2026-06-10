"""MAIA Biotechnology capital structure and dilution research.

This script produces a SEC-only capital structure analysis for MAIA,
covering March 2026 financing, warrant overhang, institutional ownership,
and fully diluted share count.

Research-only. No alerts. No messages.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# SAFETY: Force dry-run mode for capital structure research
# This ensures capital structure research can never send Telegram/email
os.environ["ROSS_DRY_RUN"] = "true"
os.environ["ALERT_ENABLE_TELEGRAM"] = "false"
os.environ["ALERT_ENABLE_EMAIL"] = "false"

from sources.sec_common import sec_fetch
from sources.sec_submissions import fetch_company_submissions


# MAIA ticker and CIK
MAIA_TICKER = "MAIA"
MAIA_CIK = "0001878313"

# Date range for filing analysis
START_DATE = "2024-01-01"

# Form types to analyze
FORM_TYPES_OF_INTEREST = [
    "10-K",
    "10-Q",
    "8-K",
    "424B3",
    "424B5",
    "S-1",
    "S-3",
    "S-1/A",
    "S-3/A",
    "DEF 14A",
    "PRE 14A",
    "13D",
    "13D/A",
    "13G",
    "13G/A",
    "144",
]


@dataclass
class CapitalStructureItem:
    """Represents one line in the capital structure table."""

    security: str
    source_filing: str
    date: str
    count: int | None
    exercise_price: str
    expiration: str
    blocker: str
    in_the_money: str
    dilution_impact: str
    confidence: str
    notes: str


@dataclass
class BeneficialOwner:
    """Represents one beneficial owner from 13D/G filings."""

    holder_name: str
    filing_type: str
    filing_date: str
    shares_owned: int | None
    percent_owned: str
    passive_active: str
    source_accession: str
    notes: str


@dataclass
class Form144Filing:
    """Represents one Form 144 filing."""

    seller: str
    filing_date: str
    shares_to_sell: int | None
    approximate_sale_date: str
    relationship: str
    source_accession: str


def get_filings_by_form_types(
    cik: str, form_types: list[str], start_date: str
) -> list[dict[str, Any]]:
    """Fetch SEC filings for specified form types and date range.

    Args:
        cik: SEC Central Index Key
        form_types: List of form types to include (e.g., ["10-K", "8-K"])
        start_date: Start date in YYYY-MM-DD format

    Returns:
        List of filing metadata dictionaries
    """
    result = fetch_company_submissions(cik)

    if not result["ok"]:
        return []

    body = result["body"]
    filings_recent = body.get("filings", {}).get("recent", {})

    if not filings_recent:
        return []

    # Extract parallel arrays
    accession_numbers = filings_recent.get("accessionNumber", [])
    filing_dates = filings_recent.get("filingDate", [])
    report_dates = filings_recent.get("reportDate", [])
    forms = filings_recent.get("form", [])
    primary_documents = filings_recent.get("primaryDocument", [])
    primary_doc_descriptions = filings_recent.get("primaryDocDescription", [])

    cik_padded = cik.zfill(10)
    cik_no_leading_zeros = str(int(cik))

    matched_filings = []

    for i in range(len(accession_numbers)):
        form = forms[i] if i < len(forms) else ""
        filing_date = filing_dates[i] if i < len(filing_dates) else ""

        # Filter by form type and date
        if form not in form_types:
            continue

        if filing_date < start_date:
            continue

        accession_number = accession_numbers[i]
        accession_no_dashes = accession_number.replace("-", "")
        report_date = report_dates[i] if i < len(report_dates) else ""
        primary_document = primary_documents[i] if i < len(primary_documents) else ""
        primary_doc_description = (
            primary_doc_descriptions[i] if i < len(primary_doc_descriptions) else ""
        )

        archive_directory_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_no_leading_zeros}/{accession_no_dashes}/"
        )

        primary_document_url = ""
        if primary_document:
            primary_document_url = archive_directory_url + primary_document

        matched_filings.append(
            {
                "cik": cik_padded,
                "accession_number": accession_number,
                "accession_no_dashes": accession_no_dashes,
                "form": form,
                "filing_date": filing_date,
                "report_date": report_date,
                "primary_document": primary_document,
                "primary_doc_description": primary_doc_description,
                "archive_directory_url": archive_directory_url,
                "primary_document_url": primary_document_url,
            }
        )

    # Sort by filing date (most recent first)
    matched_filings.sort(key=lambda f: f["filing_date"], reverse=True)

    return matched_filings


def fetch_filing_text(url: str) -> dict[str, Any]:
    """Fetch filing document text from SEC Archives.

    Args:
        url: Full URL to filing document

    Returns:
        Response dict with {"ok": bool, "body": str, ...}
    """
    return sec_fetch(url, cache_max_age=86400)


def analyze_march_2026_financing(filings: list[dict[str, Any]]) -> dict[str, Any]:
    """Identify and analyze March 2026 financing filings.

    Args:
        filings: List of filing metadata dictionaries

    Returns:
        Dictionary with March 2026 financing findings
    """
    # Look for 8-K, 424B5, and related filings in March 2026
    march_2026_filings = [
        f
        for f in filings
        if f["filing_date"].startswith("2026-03") and f["form"] in ["8-K", "424B5", "424B3", "S-3", "S-3/A"]
    ]

    if not march_2026_filings:
        return {
            "found": False,
            "note": "No March 2026 financing filings identified",
            "filings_reviewed": [],
        }

    # Fetch and analyze key documents
    filings_reviewed = []
    offering_details = {
        "offering_date": None,
        "closing_date": None,
        "gross_proceeds": None,
        "net_proceeds": None,
        "share_price": None,
        "common_shares_sold": None,
        "prefunded_warrants_sold": None,
        "common_warrants_sold": None,
        "warrant_exercise_price": None,
        "warrant_expiration": None,
        "underwriter": None,
        "investors": "Not disclosed or described as healthcare-dedicated investors",
        "blocker": None,
        "use_of_proceeds": None,
    }

    for filing in march_2026_filings[:5]:  # Limit to first 5 filings to avoid excessive fetching
        filings_reviewed.append(
            {
                "form": filing["form"],
                "filing_date": filing["filing_date"],
                "accession": filing["accession_number"],
                "url": filing["primary_document_url"],
            }
        )

        if filing["primary_document_url"]:
            resp = fetch_filing_text(filing["primary_document_url"])
            if resp["ok"]:
                text = resp["body"]

                # Simple pattern matching for key terms
                # (Real implementation would parse more carefully)

                # Look for offering amounts
                gross_match = re.search(
                    r"gross\s+proceeds.*?\$([0-9.]+)\s*million", text, re.IGNORECASE
                )
                if gross_match:
                    offering_details["gross_proceeds"] = f"${gross_match.group(1)} million"

                net_match = re.search(
                    r"net\s+proceeds.*?\$([0-9.]+)\s*million", text, re.IGNORECASE
                )
                if net_match:
                    offering_details["net_proceeds"] = f"${net_match.group(1)} million"

                # Look for share counts
                shares_match = re.search(
                    r"([0-9,]+)\s+shares\s+of\s+common\s+stock", text, re.IGNORECASE
                )
                if shares_match:
                    offering_details["common_shares_sold"] = shares_match.group(1)

                # Look for warrants
                warrant_match = re.search(
                    r"([0-9,]+)\s+(?:common\s+)?warrants", text, re.IGNORECASE
                )
                if warrant_match:
                    offering_details["common_warrants_sold"] = warrant_match.group(1)

                prefunded_match = re.search(
                    r"([0-9,]+)\s+pre-funded\s+warrants", text, re.IGNORECASE
                )
                if prefunded_match:
                    offering_details["prefunded_warrants_sold"] = prefunded_match.group(1)

                # Look for exercise price
                exercise_match = re.search(
                    r"exercise\s+price\s+of\s+\$([0-9.]+)", text, re.IGNORECASE
                )
                if exercise_match:
                    offering_details["warrant_exercise_price"] = f"${exercise_match.group(1)}"

                # Look for blocker provisions
                if "4.99%" in text or "9.99%" in text:
                    offering_details["blocker"] = "Beneficial ownership blocker present (4.99% or 9.99%)"

    return {
        "found": True,
        "offering_details": offering_details,
        "filings_reviewed": filings_reviewed,
        "note": "Pattern-based extraction from SEC filings. Manual review recommended.",
    }


def build_capital_structure(
    filings: list[dict[str, Any]], march_2026_data: dict[str, Any]
) -> list[CapitalStructureItem]:
    """Build capital structure table from filings and March 2026 analysis.

    Args:
        filings: List of filing metadata
        march_2026_data: March 2026 financing analysis results

    Returns:
        List of CapitalStructureItem objects
    """
    items = []

    # Add common shares outstanding (from latest 10-Q or proxy)
    latest_10q = next((f for f in filings if f["form"] == "10-Q"), None)
    if latest_10q:
        items.append(
            CapitalStructureItem(
                security="Common Stock Outstanding",
                source_filing=f"10-Q {latest_10q['filing_date']}",
                date=latest_10q['filing_date'],
                count=None,  # Would need to parse filing
                exercise_price="N/A",
                expiration="N/A",
                blocker="N/A",
                in_the_money="N/A",
                dilution_impact="Base",
                confidence="High",
                notes="Requires manual extraction from 10-Q",
            )
        )

    # Add March 2026 financing instruments
    if march_2026_data.get("found"):
        offering = march_2026_data["offering_details"]

        if offering.get("common_shares_sold"):
            items.append(
                CapitalStructureItem(
                    security="Common Shares (March 2026 Offering)",
                    source_filing="424B5/8-K March 2026",
                    date="2026-03",
                    count=None,  # Parse from offering["common_shares_sold"]
                    exercise_price="N/A",
                    expiration="N/A",
                    blocker=offering.get("blocker", "Unknown"),
                    in_the_money="N/A",
                    dilution_impact="Immediate",
                    confidence="Medium",
                    notes=f"Shares sold: {offering.get('common_shares_sold', 'TBD')}",
                )
            )

        if offering.get("prefunded_warrants_sold"):
            items.append(
                CapitalStructureItem(
                    security="Pre-Funded Warrants (March 2026)",
                    source_filing="424B5 March 2026",
                    date="2026-03",
                    count=None,
                    exercise_price="$0.0001 (typical pre-funded)",
                    expiration="Perpetual (typical)",
                    blocker=offering.get("blocker", "Unknown"),
                    in_the_money="Yes (deeply in-the-money)",
                    dilution_impact="Near-immediate",
                    confidence="Medium",
                    notes=f"Warrants sold: {offering.get('prefunded_warrants_sold', 'TBD')}",
                )
            )

        if offering.get("common_warrants_sold"):
            items.append(
                CapitalStructureItem(
                    security="Common Warrants (March 2026)",
                    source_filing="424B5 March 2026",
                    date="2026-03",
                    count=None,
                    exercise_price=offering.get("warrant_exercise_price", "TBD"),
                    expiration="TBD (typically 5 years)",
                    blocker=offering.get("blocker", "Unknown"),
                    in_the_money="TBD (requires current stock price)",
                    dilution_impact="Potential",
                    confidence="Medium",
                    notes=f"Warrants sold: {offering.get('common_warrants_sold', 'TBD')}",
                )
            )

    # Add equity incentive plan placeholder
    latest_proxy = next((f for f in filings if f["form"] == "DEF 14A"), None)
    if latest_proxy:
        items.append(
            CapitalStructureItem(
                security="Equity Incentive Plan",
                source_filing=f"DEF 14A {latest_proxy['filing_date']}",
                date=latest_proxy['filing_date'],
                count=None,
                exercise_price="Varies",
                expiration="Varies",
                blocker="N/A",
                in_the_money="Varies",
                dilution_impact="Potential",
                confidence="High",
                notes="Requires manual extraction from proxy statement",
            )
        )

    return items


def check_13d_13g_filings(filings: list[dict[str, Any]]) -> list[BeneficialOwner]:
    """Extract 13D/13G beneficial ownership holders.

    Args:
        filings: List of filing metadata

    Returns:
        List of BeneficialOwner objects
    """
    owners = []

    for filing in filings:
        if filing["form"] not in ["13D", "13D/A", "13G", "13G/A"]:
            continue

        # Fetch filing and extract holder info
        # (Real implementation would parse XML/HTML)
        passive_active = "Passive" if "13G" in filing["form"] else "Active/Potential activist"

        owners.append(
            BeneficialOwner(
                holder_name="TBD (requires filing parse)",
                filing_type=filing["form"],
                filing_date=filing["filing_date"],
                shares_owned=None,
                percent_owned="TBD",
                passive_active=passive_active,
                source_accession=filing["accession_number"],
                notes=f"Filing URL: {filing['primary_document_url']}",
            )
        )

    return owners


def check_form_144_filings(filings: list[dict[str, Any]]) -> list[Form144Filing]:
    """Check for Form 144 restricted stock sale filings.

    Args:
        filings: List of filing metadata

    Returns:
        List of Form144Filing objects
    """
    form_144s = []

    for filing in filings:
        if filing["form"] != "144":
            continue

        form_144s.append(
            Form144Filing(
                seller="TBD (requires filing parse)",
                filing_date=filing["filing_date"],
                shares_to_sell=None,
                approximate_sale_date="TBD",
                relationship="TBD",
                source_accession=filing["accession_number"],
            )
        )

    return form_144s


def generate_fully_diluted_estimate(
    capital_structure: list[CapitalStructureItem],
) -> dict[str, Any]:
    """Calculate fully diluted share count estimate.

    Args:
        capital_structure: List of CapitalStructureItem objects

    Returns:
        Dictionary with fully diluted estimate breakdown
    """
    # This is a placeholder - real implementation would parse actual counts
    return {
        "basic_shares_outstanding": "TBD (from 10-Q)",
        "prefunded_warrants": "TBD",
        "common_warrants": "TBD",
        "options_rsus": "TBD (from proxy/10-K)",
        "other_convertibles": "None identified",
        "estimated_fully_diluted_low": "TBD",
        "estimated_fully_diluted_high": "TBD",
        "note": "Requires manual extraction of share counts from filings",
        "methodology": "Basic + Pre-funded + Common warrants + Options/RSUs",
    }


def generate_hidden_institutional_assessment() -> list[str]:
    """Generate assessment of hidden/lagged institutional ownership.

    Returns:
        List of assessment points
    """
    return [
        "Unnamed healthcare-dedicated investors: March 2026 offering may reference 'healthcare-dedicated investors' without naming them. These could be biotech-focused hedge funds or institutional investors below 13F/13D reporting thresholds.",
        "13F threshold and lag: 13F-HR filings report positions as of quarter-end with a 45-day lag. Positions below $200M AUM or below reporting thresholds are not disclosed.",
        "13D/G 5% threshold: Only holders with ≥5% beneficial ownership must file 13D/13G. Significant positions at 2-4% are invisible.",
        "Beneficial ownership blockers: Pre-funded warrants and common warrants often include 4.99% or 9.99% blockers, preventing exercise that would trigger 13D filing. This allows large investors to remain below disclosure thresholds.",
        "Pre-funded warrant structures: These are economically equivalent to common stock but structured as warrants. Investors can control large positions without triggering reporting.",
        "Private placements and resale registrations: MAIA may conduct private placements with resale registrations following the offering. Initial buyers may not be named in prospectus supplements.",
        "Short/derivative exposure: 13F filings do not capture short positions or derivative exposure (swaps, total return swaps, etc.). Hedge funds may have synthetic short exposure not visible in SEC filings.",
        "Underwriter and placement agent positions: Underwriters, placement agents, and their affiliates may take proprietary positions in connection with offerings. These positions may not be immediately disclosed.",
        "Why Maggie 13F check may miss investors: Maggie's 13F analysis relies on CUSIP or issuer-name matching. MAIA's CUSIP availability and issuer-name match quality may be limited. Small-cap biotechs often have incomplete 13F coverage.",
    ]


def generate_markdown_report(
    filings: list[dict[str, Any]],
    march_2026_data: dict[str, Any],
    capital_structure: list[CapitalStructureItem],
    fully_diluted: dict[str, Any],
    beneficial_owners: list[BeneficialOwner],
    form_144s: list[Form144Filing],
    hidden_institutional: list[str],
) -> str:
    """Generate comprehensive markdown report.

    Args:
        filings: List of all filings reviewed
        march_2026_data: March 2026 financing analysis
        capital_structure: Capital structure table
        fully_diluted: Fully diluted estimate
        beneficial_owners: 13D/13G holders
        form_144s: Form 144 filings
        hidden_institutional: Hidden institutional assessment points

    Returns:
        Markdown report string
    """
    report = f"""# MAIA Biotechnology Capital Structure and Dilution Research

**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
**Ticker**: {MAIA_TICKER}
**CIK**: {MAIA_CIK}
**Data Sources**: SEC EDGAR only
**Date Range**: {START_DATE} to present

---

## Executive Summary

This report provides a SEC-only analysis of MAIA Biotechnology's capital structure, focusing on the March 2026 financing, warrant overhang, institutional ownership (13D/G, 13F), Form 144 activity, and fully diluted share count estimate.

**Key Findings**:
- March 2026 financing identified: {march_2026_data.get('found', False)}
- 13D/13G holders found: {len(beneficial_owners)}
- Form 144 filings found: {len(form_144s)}
- Capital structure items: {len(capital_structure)}

**Important**: This is a pattern-based extraction from SEC filings. Manual review of source documents is strongly recommended before investment decisions.

---

## SEC Source Boundary

This report uses only SEC EDGAR public filings:
- Company submissions JSON API (data.sec.gov)
- SEC Archives (www.sec.gov/Archives/edgar/data/)
- No OpenInsider data
- No Roger's uploaded spreadsheet
- No third-party paid data sources

All findings are cited to specific SEC accession numbers.

---

## Filing Inventory

Total filings reviewed: {len(filings)}

### Filings by Form Type
"""

    # Count filings by form type
    form_counts: dict[str, int] = {}
    for filing in filings:
        form = filing["form"]
        form_counts[form] = form_counts.get(form, 0) + 1

    for form, count in sorted(form_counts.items()):
        report += f"- **{form}**: {count}\n"

    report += f"""
### Filing Date Range
- Earliest: {min(f['filing_date'] for f in filings) if filings else 'N/A'}
- Latest: {max(f['filing_date'] for f in filings) if filings else 'N/A'}

---

## March 2026 Financing Summary

**Status**: {march_2026_data.get('note', 'No March 2026 financing filings identified')}

"""

    if march_2026_data.get("found"):
        offering = march_2026_data["offering_details"]
        report += f"""### Offering Details

| Item | Value |
|------|-------|
| Gross Proceeds | {offering.get('gross_proceeds') or 'TBD'} |
| Net Proceeds | {offering.get('net_proceeds') or 'TBD'} |
| Share Price | {offering.get('share_price') or 'TBD'} |
| Common Shares Sold | {offering.get('common_shares_sold') or 'TBD'} |
| Pre-Funded Warrants Sold | {offering.get('prefunded_warrants_sold') or 'TBD'} |
| Common Warrants Sold | {offering.get('common_warrants_sold') or 'TBD'} |
| Warrant Exercise Price | {offering.get('warrant_exercise_price') or 'TBD'} |
| Warrant Expiration | {offering.get('warrant_expiration') or 'TBD (typically 5 years)'} |
| Beneficial Ownership Blocker | {offering.get('blocker') or 'TBD'} |
| Named Investors | {offering.get('investors') or 'TBD'} |
| Use of Proceeds | {offering.get('use_of_proceeds') or 'TBD'} |

### Filings Reviewed for March 2026 Financing

"""
        for filing_info in march_2026_data.get("filings_reviewed", []):
            report += f"- **{filing_info['form']}** filed {filing_info['filing_date']} - [{filing_info['accession']}]({filing_info['url']})\n"

    report += """
---

## Capital Structure Table

| Security | Source Filing | Date | Count | Exercise Price | Expiration | Blocker | In-the-Money | Dilution Impact | Confidence | Notes |
|----------|---------------|------|-------|----------------|------------|---------|--------------|-----------------|------------|-------|
"""

    for item in capital_structure:
        report += f"| {item.security} | {item.source_filing} | {item.date} | {item.count or 'TBD'} | {item.exercise_price} | {item.expiration} | {item.blocker} | {item.in_the_money} | {item.dilution_impact} | {item.confidence} | {item.notes} |\n"

    report += f"""
---

## Fully Diluted Share Count Estimate

**Methodology**: {fully_diluted.get('methodology', 'TBD')}

| Component | Count |
|-----------|-------|
| Basic Shares Outstanding | {fully_diluted.get('basic_shares_outstanding', 'TBD')} |
| Pre-Funded Warrants | {fully_diluted.get('prefunded_warrants', 'TBD')} |
| Common Warrants | {fully_diluted.get('common_warrants', 'TBD')} |
| Options/RSUs | {fully_diluted.get('options_rsus', 'TBD')} |
| Other Convertibles | {fully_diluted.get('other_convertibles', 'None identified')} |
| **Estimated Fully Diluted (Low)** | **{fully_diluted.get('estimated_fully_diluted_low', 'TBD')}** |
| **Estimated Fully Diluted (High)** | **{fully_diluted.get('estimated_fully_diluted_high', 'TBD')}** |

**Note**: {fully_diluted.get('note', '')}

---

## 13D/13G Beneficial Ownership Holders

Total holders identified: {len(beneficial_owners)}

"""

    if beneficial_owners:
        report += """| Holder Name | Filing Type | Filing Date | Shares Owned | Percent Owned | Passive/Active | Accession | Notes |
|-------------|-------------|-------------|--------------|---------------|----------------|-----------|-------|
"""
        for owner in beneficial_owners:
            report += f"| {owner.holder_name} | {owner.filing_type} | {owner.filing_date} | {owner.shares_owned or 'TBD'} | {owner.percent_owned} | {owner.passive_active} | {owner.source_accession} | {owner.notes} |\n"
    else:
        report += "No 13D/13G filings found for MAIA in the review period.\n"

    report += """
---

## Proxy Beneficial Ownership Table Summary

**Status**: Requires manual extraction from latest DEF 14A filing.

Latest proxy identified: """

    latest_proxy = next((f for f in filings if f["form"] == "DEF 14A"), None)
    if latest_proxy:
        report += f"[DEF 14A {latest_proxy['filing_date']}]({latest_proxy['primary_document_url']})\n"
    else:
        report += "No DEF 14A filing found in review period.\n"

    report += """
**Expected Content**:
- Directors and named executive officers ownership
- 5% beneficial holders
- Insider group total ownership

---

## 13F Institutional Holder Review

**Status**: Requires integration with project 13F matching infrastructure.

**Limitations** (per CP21D findings):
- MAIA CUSIP availability/uncertainty may limit matching
- Issuer-name matching quality unknown
- 13F reporting lag (45 days after quarter-end)
- Positions below $200M AUM not disclosed
- Positions below reporting thresholds not disclosed
- Private placements/warrants may not appear cleanly in 13F data
- Short/derivative exposure not visible in 13F filings

**Recommendation**: Manually review recent 13F-HR filings for MAIA issuer-name or CUSIP matches via SEC EDGAR search.

---

## Form 144 Review

Total Form 144 filings identified: """
    report += f"{len(form_144s)}\n\n"

    if form_144s:
        report += """| Seller | Filing Date | Shares to Sell | Approximate Sale Date | Relationship | Accession |
|--------|-------------|----------------|----------------------|--------------|-----------|
"""
        for f144 in form_144s:
            report += f"| {f144.seller} | {f144.filing_date} | {f144.shares_to_sell or 'TBD'} | {f144.approximate_sale_date} | {f144.relationship} | {f144.source_accession} |\n"
    else:
        report += "No Form 144 filings found for MAIA in the review period.\n"

    report += """
---

## Hidden/Lagged Institutional Ownership Assessment

### Institutional/Hedge-Fund Involvement That May Not Be Visible

"""

    for i, point in enumerate(hidden_institutional, start=1):
        report += f"{i}. {point}\n\n"

    report += """
---

## Dilution Risk Assessment

### Key Dilution Risks

1. **Pre-Funded Warrant Overhang**: Pre-funded warrants are economically equivalent to common stock and are likely to be exercised immediately or near-term. Dilution impact is near-immediate.

2. **Common Warrant Overhang**: Common warrants from March 2026 offering represent potential future dilution. If stock price rises above exercise price, warrants become in-the-money and dilutive.

3. **Equity Incentive Plan**: Stock options and RSUs granted to employees, directors, and executives represent ongoing dilution as they vest and are exercised.

4. **Future Financing Risk**: Biotech companies often require multiple rounds of financing. MAIA may conduct additional offerings, ATM programs, or shelf takedowns that create further dilution.

5. **Beneficial Ownership Blockers**: Blockers (4.99% or 9.99%) may limit dilution from any single investor but do not prevent aggregate dilution from multiple investors exercising warrants.

### Monitoring Checklist

- [ ] Monitor 8-K filings for new financing announcements
- [ ] Track 424B prospectus supplements for shelf takedowns
- [ ] Review quarterly 10-Q filings for updated share counts
- [ ] Check for new 13D/13G filings (5% beneficial ownership changes)
- [ ] Monitor Form 144 filings for insider sales
- [ ] Track warrant exercise activity (if disclosed in 8-K or press releases)
- [ ] Review DEF 14A proxy statements for equity plan amendments
- [ ] Check for S-3/S-1 registration statements for future offerings

---

## Key Uncertainties / Limitations

1. **Pattern-Based Extraction**: This report uses regex pattern matching on SEC filing text. Results require manual verification against source documents.

2. **Share Count Precision**: Exact share counts for common stock, warrants, and options require manual extraction from financial statements and footnotes.

3. **Warrant Terms**: Warrant exercise prices, expiration dates, and blocker provisions require careful reading of warrant certificates or prospectus supplements.

4. **Unnamed Investors**: March 2026 offering may reference "healthcare-dedicated investors" without naming them. True investor identities may not be disclosed until 13D/13G or 13F filings appear.

5. **13F Coverage**: MAIA may have limited 13F coverage due to CUSIP/issuer-name matching challenges. Manual SEC EDGAR search recommended.

6. **Current Stock Price**: In-the-money status for warrants requires current MAIA stock price, which is not sourced from SEC filings.

7. **Hidden Institutional Ownership**: Significant institutional positions may exist below 13D/13G and 13F reporting thresholds.

---

## Appendix: Source Filings Reviewed

Total filings: {len(filings)}

"""

    for filing in filings[:20]:  # Show first 20
        report += f"- **{filing['form']}** filed {filing['filing_date']} - [{filing['accession_number']}]({filing['primary_document_url']})\n"

    if len(filings) > 20:
        report += f"\n... and {len(filings) - 20} more filings.\n"

    report += f"""
---

## Safety Confirmations

- **Roger's OpenInsider spreadsheet used**: No
- **Telegram message sent**: No
- **Email sent**: No
- **Scheduled tasks modified or triggered**: No
- **`.env` file printed or changed**: No
- **Secrets printed**: No

---

**Report generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
**Generated by**: CP23A MAIA Capital Structure Research
**For**: Roger Fiske / Insider-Trading project
**Disclaimer**: This report is informational only and does not constitute investment advice.
"""

    return report


def generate_json_report(
    filings: list[dict[str, Any]],
    march_2026_data: dict[str, Any],
    capital_structure: list[CapitalStructureItem],
    fully_diluted: dict[str, Any],
    beneficial_owners: list[BeneficialOwner],
    form_144s: list[Form144Filing],
    hidden_institutional: list[str],
) -> dict[str, Any]:
    """Generate JSON report with all research findings.

    Args:
        filings: List of all filings reviewed
        march_2026_data: March 2026 financing analysis
        capital_structure: Capital structure table
        fully_diluted: Fully diluted estimate
        beneficial_owners: 13D/13G holders
        form_144s: Form 144 filings
        hidden_institutional: Hidden institutional assessment points

    Returns:
        Dictionary suitable for JSON serialization
    """
    return {
        "ticker": MAIA_TICKER,
        "cik": MAIA_CIK,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": ["SEC EDGAR"],
        "filings_reviewed": [
            {
                "form": f["form"],
                "filing_date": f["filing_date"],
                "accession": f["accession_number"],
                "url": f["primary_document_url"],
            }
            for f in filings
        ],
        "march_2026_financing": march_2026_data,
        "capital_structure": [asdict(item) for item in capital_structure],
        "fully_diluted_estimate": fully_diluted,
        "beneficial_ownership_13d_13g": [asdict(owner) for owner in beneficial_owners],
        "proxy_beneficial_ownership": {"status": "Requires manual extraction from DEF 14A"},
        "institutional_13f": {
            "status": "Requires 13F matching integration",
            "limitations": [
                "CUSIP availability uncertain",
                "Issuer-name matching quality unknown",
                "13F reporting lag (45 days)",
                "Positions below thresholds not disclosed",
            ],
        },
        "form_144": [asdict(f144) for f144 in form_144s],
        "hidden_institutional_assessment": hidden_institutional,
        "limitations": [
            "Pattern-based extraction requires manual verification",
            "Share counts require manual extraction from financial statements",
            "Warrant terms require prospectus supplement review",
            "Unnamed investors may not be disclosed until 13D/13G/13F filings",
            "13F coverage may be limited for MAIA",
            "In-the-money status requires current stock price",
            "Hidden institutional positions below reporting thresholds",
        ],
        "safety": {
            "openinsider_spreadsheet_used": False,
            "telegram_sent": False,
            "email_sent": False,
            "scheduled_tasks_modified": False,
        },
    }


def main():
    """Main research execution."""
    print(f"Starting MAIA capital structure research...")
    print(f"Ticker: {MAIA_TICKER}")
    print(f"CIK: {MAIA_CIK}")
    print(f"Date range: {START_DATE} to present")
    print()

    # Fetch all filings
    print("Fetching SEC filings...")
    filings = get_filings_by_form_types(MAIA_CIK, FORM_TYPES_OF_INTEREST, START_DATE)
    print(f"Found {len(filings)} filings")
    print()

    # Analyze March 2026 financing
    print("Analyzing March 2026 financing...")
    march_2026_data = analyze_march_2026_financing(filings)
    print(f"March 2026 financing found: {march_2026_data.get('found', False)}")
    print()

    # Build capital structure
    print("Building capital structure table...")
    capital_structure = build_capital_structure(filings, march_2026_data)
    print(f"Capital structure items: {len(capital_structure)}")
    print()

    # Generate fully diluted estimate
    print("Generating fully diluted estimate...")
    fully_diluted = generate_fully_diluted_estimate(capital_structure)
    print()

    # Check 13D/13G
    print("Checking 13D/13G filings...")
    beneficial_owners = check_13d_13g_filings(filings)
    print(f"13D/13G holders found: {len(beneficial_owners)}")
    print()

    # Check Form 144
    print("Checking Form 144 filings...")
    form_144s = check_form_144_filings(filings)
    print(f"Form 144 filings found: {len(form_144s)}")
    print()

    # Generate hidden institutional assessment
    print("Generating hidden institutional ownership assessment...")
    hidden_institutional = generate_hidden_institutional_assessment()
    print(f"Assessment points: {len(hidden_institutional)}")
    print()

    # Generate reports
    print("Generating markdown report...")
    markdown_report = generate_markdown_report(
        filings,
        march_2026_data,
        capital_structure,
        fully_diluted,
        beneficial_owners,
        form_144s,
        hidden_institutional,
    )

    print("Generating JSON report...")
    json_report = generate_json_report(
        filings,
        march_2026_data,
        capital_structure,
        fully_diluted,
        beneficial_owners,
        form_144s,
        hidden_institutional,
    )

    # Write reports
    output_dir = Path(__file__).parent.parent / "docs" / "sample_reports" / "maia_capital_structure"
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = output_dir / "MAIA_capital_structure_dilution_report.md"
    json_path = output_dir / "MAIA_capital_structure_dilution.json"

    print(f"Writing markdown report to {markdown_path}...")
    markdown_path.write_text(markdown_report, encoding="utf-8")

    print(f"Writing JSON report to {json_path}...")
    json_path.write_text(json.dumps(json_report, indent=2), encoding="utf-8")

    print()
    print("Research complete!")
    print(f"Markdown report: {markdown_path}")
    print(f"JSON report: {json_path}")


if __name__ == "__main__":
    main()
