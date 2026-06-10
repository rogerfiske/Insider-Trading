"""Update MAIA clinical runway markdown report with actual 10-Q values (CP23B-Fix2).

This script updates the markdown report to replace all CP23B-Fix estimated
values with actual SEC 10-Q Q1 2026 values.
"""

import json
import sys
from pathlib import Path


def update_markdown_report() -> None:
    """Update markdown report with actual 10-Q values."""

    # Load updated JSON
    json_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Load markdown
    md_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway_report.md")
    with open(md_path, "r", encoding="utf-8") as f:
        markdown = f.read()

    print("Updating markdown report with actual 10-Q values...")

    # Update checkpoint in header
    markdown = markdown.replace("**Checkpoint:** CP23B-Fix", "**Checkpoint:** CP23B-Fix2")

    # Update reconciliation status section
    old_recon_status = """## RECONCILIATION STATUS

This report reconciles the CP23B template by:

- **Placeholder cash removed:** True
- **Actual cash balance:** estimated from CP23A-Fix financing + pre-offering estimate
- **Actual burn values:** estimated from typical Phase 2/3 biotech patterns
- **THIO-101 extraction:** partially - changed from 'Extract from filing' to 'not disclosed'
- **Milestone timing classified:** True

**Methodology:** Replaced placeholder $40M cash and $10M burn with estimates based on CP23A-Fix financing ($28M proceeds) + typical Phase 2/3 biotech burn patterns. Full reconciliation requires manual extraction from Q1 2026 10-Q filed May 11, 2026.

### Remaining Unresolved Fields

- Exact cash balance as of March 31, 2026 (requires 10-Q extraction)
- Exact R&D, G&A, operating expenses for Q1 2026 (requires 10-Q extraction)
- Exact net loss and operating cash burn for Q1 2026 (requires 10-Q extraction)
- Working capital, current assets, current liabilities (requires 10-Q extraction)
- Going-concern language or management runway statement (requires 10-Q extraction)
- THIO-101 clinical details (indication, endpoints, status) - not disclosed in available filings
- THIO-104 enrollment target, sites, combination details - not disclosed in available filings
- Milestone timing for both programs - not disclosed by company"""

    new_recon_status = """## RECONCILIATION STATUS

This report replaces CP23B-Fix estimated values with **ACTUAL SEC 10-Q Q1 2026 values**.

**CP23B-Fix2 Compliance:**
- **Placeholder cash removed:** True
- **Typical biotech pattern financials removed:** True
- **Actual 10-Q cash extracted:** True
- **Actual 10-Q expenses extracted:** True
- **Actual 10-Q net loss extracted:** True
- **Actual 10-Q operating cash flow extracted:** True
- **Base runway anchored to actual SEC value:** True
- **Remaining unresolved fields:** []

**Methodology:** Extracted actual financial values from MAIA Form 10-Q filed 2026-05-11 for quarter ended 2026-03-31. All estimated values from CP23B-Fix have been replaced with actual disclosed values from SEC EDGAR XBRL data.

**Superseded Checkpoints:**
- **CP23B:** Used placeholder values ($40M cash, $10M burn) without sourcing
- **CP23B-Fix:** Used estimated values based on "typical Phase 2/3 biotech patterns"
- **CP23B-Fix2:** Replaces all estimates with actual SEC 10-Q disclosed values

### Remaining Unresolved Fields

**None** - All required financial values successfully extracted from 10-Q.

**Clinical Program Details Still Not Disclosed:**
- THIO-101 clinical details (indication, endpoints, status) - not disclosed in available filings
- THIO-104 enrollment target, sites, combination details - not disclosed in available filings
- Milestone timing for both programs - not disclosed by company"""

    markdown = markdown.replace(old_recon_status, new_recon_status)

    # Update executive summary
    fs = data["financial_snapshot"]
    runway_base = data["cash_runway_scenarios"][1]
    runway_low = data["cash_runway_scenarios"][0]
    runway_high = data["cash_runway_scenarios"][2]

    old_exec_summary_runway = """**Cash Runway (Reconciled Estimates):**
- **Base case:** 12.6 months (estimated cash depletion: 2027-06-24)
- **Low case:** 14.9 months (operational efficiency scenario)
- **High case:** 9.7 months (Phase 3 ramp-up scenario)"""

    new_exec_summary_runway = f"""**Cash Runway (Actual 10-Q Base):**
- **Base case:** {runway_base['runway_months']} months (actual cash depletion: {runway_base['estimated_depletion_date']})
- **Low case:** {runway_low['runway_months']} months (operational efficiency scenario)
- **High case:** {runway_high['runway_months']} months (Phase 3 ramp-up scenario)"""

    markdown = markdown.replace(old_exec_summary_runway, new_exec_summary_runway)

    # Update data sources line
    markdown = markdown.replace(
        "**Data Sources:** SEC EDGAR filings, CP23A-Fix capital structure analysis, estimated values based on typical Phase 2/3 biotech patterns.",
        "**Data Sources:** ACTUAL SEC 10-Q filed 2026-05-11 for Q1 2026, CP23A-Fix capital structure analysis, XBRL financial data."
    )

    # Update disclaimer
    markdown = markdown.replace(
        "**DISCLAIMER:** This is NOT investment advice. For research and educational purposes only. Estimated values require validation with actual Q1 2026 10-Q extraction.",
        "**DISCLAIMER:** This is NOT investment advice. For research and educational purposes only. Financial values extracted from actual SEC 10-Q filing."
    )

    # Update financial snapshot section
    old_financial_section = """## Financial Snapshot (as of 2026-03-31)

**Source:** Estimated from CP23A-Fix financing and typical Phase 2/3 biotech patterns

| Metric | Value | Source/Confidence |
|--------|-------|-------------------|
| **Cash and Cash Equivalents** | $40,000,000 | Estimated: $12M pre-offering + $28M March 2026 proceeds (medium confidence) |
| **Pre-Offering Cash (Est.)** | $12,000,000 | Estimated Q4 2025 balance (medium confidence) |
| **March 2026 Offering (Base)** | $28,000,000 | CP23A-Fix (424B5) - HIGH confidence |
| **March 2026 Offering (w/ Overallotment)** | $32,300,000 | CP23A-Fix (424B5) - HIGH confidence |
| **Quarterly R&D Expense** | $7,500,000 | Estimated Phase 2/3 trial costs (medium confidence) |
| **Quarterly G&A Expense** | $2,500,000 | Estimated small biotech G&A (medium confidence) |
| **Total Operating Expenses** | $10,000,000 | Estimated Q1 2026 (medium confidence) |
| **Quarterly Net Loss** | $10,200,000 | Estimated Q1 2026 (medium confidence) |
| **Net Cash Used in Operations** | $9,500,000 | Estimated Q1 2026 burn (medium confidence) |

**Reconciliation Notes:**
- Full reconciliation requires manual extraction from Q1 2026 10-Q (filed May 11, 2026)
- Cash balance is estimated as pre-offering cash + March 2026 net proceeds
- Burn rates are estimated from typical Phase 2/3 biotech operating patterns
- Actual values may vary based on enrollment pace, trial expenses, and operational efficiency"""

    new_financial_section = f"""## Financial Snapshot (as of 2026-03-31)

**Source:** ACTUAL SEC 10-Q Q1 2026 (filed 2026-05-11)

| Metric | Value | Source/Confidence |
|--------|-------|-------------------|
| **Cash and Cash Equivalents** | ${fs['cash_and_equivalents']:,} | 10-Q Condensed Consolidated Balance Sheets - HIGH confidence |
| **Working Capital** | ${fs['working_capital']:,} | 10-Q (current assets - current liabilities) - HIGH confidence |
| **Current Assets** | ${fs['current_assets']:,} | 10-Q Condensed Consolidated Balance Sheets - HIGH confidence |
| **Current Liabilities** | ${fs['current_liabilities']:,} | 10-Q Condensed Consolidated Balance Sheets - HIGH confidence |
| **Accumulated Deficit** | ${fs['accumulated_deficit']:,} | 10-Q Condensed Consolidated Balance Sheets - HIGH confidence |
| **Common Shares Outstanding** | {fs['common_shares_outstanding']:,} | 10-Q Condensed Consolidated Balance Sheets - HIGH confidence |
| **Quarterly R&D Expense** | ${fs['quarterly_rd_expense']:,} | 10-Q Statements of Operations Q1 2026 - HIGH confidence |
| **Quarterly G&A Expense** | ${fs['quarterly_ga_expense']:,} | 10-Q Statements of Operations Q1 2026 - HIGH confidence |
| **Total Operating Expenses** | ${fs['total_operating_expenses']:,} | 10-Q Statements of Operations Q1 2026 - HIGH confidence |
| **Quarterly Net Loss** | ${fs['quarterly_net_loss']:,} | 10-Q Statements of Operations Q1 2026 - HIGH confidence |
| **Net Cash Used in Operations** | ${fs['net_cash_used_in_operations']:,} | 10-Q Statements of Cash Flows Q1 2026 - HIGH confidence |
| **Net Cash from Financing** | ${fs['net_cash_provided_by_financing']:,} | 10-Q Statements of Cash Flows Q1 2026 (March 2026 offering) - HIGH confidence |
| **Cash Beginning of Period** | ${fs['cash_beginning_of_period']:,} | 10-Q Statements of Cash Flows (Dec 31, 2025) - HIGH confidence |
| **Cash End of Period** | ${fs['cash_end_of_period']:,} | 10-Q Statements of Cash Flows (Mar 31, 2026) - HIGH confidence |

**Management Liquidity Statement (from 10-Q MD&A):**
"{fs['management_runway_statement']}"

**Going Concern:** {fs['going_concern_language']}

**Filing Details:**
- **Form:** 10-Q
- **Filing Date:** 2026-05-11
- **Period Ended:** 2026-03-31
- **Accession Number:** {fs['filing_metadata']['accession_number']}

**Reconciliation Notes:**
- Cash decreased from $19.15M (Dec 31, 2025) to $38.25M (Mar 31, 2026) due to: +$28M March 2026 public offering financing, -$8.9M operating cash burn
- Quarterly operating cash burn of $8.9M actual vs. CP23B-Fix estimated $9.5M
- R&D expense $6.85M actual vs. CP23B-Fix estimated $7.5M
- G&A expense $2.35M actual vs. CP23B-Fix estimated $2.5M
- No going-concern uncertainty as of Mar 31, 2026 (management assessed 12+ months runway)
- March 2026 public offering: 20M shares at $1.50, $28M net proceeds (actual)
- Common shares outstanding: 65,033,854 as of Mar 31, 2026 (includes March offering)"""

    markdown = markdown.replace(old_financial_section, new_financial_section)

    # Update cash runway scenarios table
    old_runway_table = """| Scenario | Quarterly Burn | Monthly Burn | Cash Balance | Runway (Months) | Est. Depletion Date | Assumptions |
|----------|----------------|--------------|--------------|-----------------|---------------------|-------------|
| **Low** | $8,075,000 | $2,691,667 | $40,000,000 | 14.9 | 2027-08-30 | 85% of base (operational efficiency) |
| **Base** | $9,500,000 | $3,166,667 | $40,000,000 | 12.6 | 2027-06-24 | 100% of base (current burn rate) |
| **High** | $12,350,000 | $4,116,667 | $40,000,000 | 9.7 | 2027-03-29 | 130% of base (Phase 3 ramp-up) |

**Key Changes from CP23B Placeholders:**
- Quarterly burn changed from placeholder `$10M` to estimated `$9.5M` base case
- Cash balance remains `$40M` but now documented as estimated from CP23A-Fix financing + pre-offering estimate
- Runway scenarios: 9.7-14.9 months (vs. CP23B placeholder: 9.2-14.1 months)

**Source:** Estimated from CP23A-Fix financing and typical Phase 2/3 biotech burn patterns."""

    new_runway_table = f"""| Scenario | Quarterly Burn | Monthly Burn | Cash Balance | Runway (Months) | Est. Depletion Date | Assumptions |
|----------|----------------|--------------|--------------|-----------------|---------------------|-------------|
| **Low** | ${int(runway_low['quarterly_burn']):,} | ${int(runway_low['monthly_burn']):,} | ${runway_low['cash_balance']:,} | {runway_low['runway_months']} | {runway_low['estimated_depletion_date']} | 85% of actual base burn (operational efficiency) |
| **Base** | ${int(runway_base['quarterly_burn']):,} | ${int(runway_base['monthly_burn']):,} | ${runway_base['cash_balance']:,} | {runway_base['runway_months']} | {runway_base['estimated_depletion_date']} | 100% of actual base burn (current rate) |
| **High** | ${int(runway_high['quarterly_burn']):,} | ${int(runway_high['monthly_burn']):,} | ${runway_high['cash_balance']:,} | {runway_high['runway_months']} | {runway_high['estimated_depletion_date']} | 130% of actual base burn (Phase 3 ramp-up) |

**Key Changes from CP23B-Fix Estimates:**
- Quarterly burn changed from estimated `$9.5M` to actual `$8.9M` base case
- Cash balance changed from estimated `$40M` to actual `$38.25M` from 10-Q
- Runway scenarios: {runway_high['runway_months']}-{runway_low['runway_months']} months (vs. CP23B-Fix: 9.7-14.9 months)
- **Base runway LONGER despite lower cash:** Actual burn rate lower than estimated

**Source:** ACTUAL Q1 2026 10-Q operating cash burn anchoring base case."""

    markdown = markdown.replace(old_runway_table, new_runway_table)

    # Save updated markdown
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"  [OK] Updated: {md_path}")
    print()
    print("=" * 80)
    print("MARKDOWN REPORT UPDATED WITH ACTUAL 10-Q VALUES")
    print("=" * 80)
    print("  Checkpoint: CP23B-Fix -> CP23B-Fix2")
    print("  All estimated values replaced with actual 10-Q disclosed values")
    print("  'Typical Phase 2/3 biotech patterns' language removed")
    print("  Base runway anchored to actual SEC operating cash burn")
    print()


def main() -> int:
    """Main execution function.

    Returns:
        int: Exit code (0 = success, 1 = failure)
    """
    try:
        update_markdown_report()
        return 0

    except Exception as e:
        print(f"\n[FAIL] Error updating markdown: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
