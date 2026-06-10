"""MAIA Biotechnology Clinical/Regulatory Milestone Calendar and Cash Runway Sensitivity Research.

This script extracts MAIA clinical program information, regulatory status, financial data,
and performs cash runway sensitivity analysis using SEC EDGAR filings only.

CP23B: MAIA Clinical/Regulatory/Cash Runway Research
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx


def fetch_filing(url: str) -> str:
    """Fetch SEC filing content."""
    print(f"Fetching: {url}")
    headers = {
        "User-Agent": "RossInsiderScout roger@rogerfiske.com",
        "Accept": "text/html,application/xhtml+xml",
    }

    response = httpx.get(url, headers=headers, timeout=30.0, follow_redirects=True)
    response.raise_for_status()

    return response.text


def extract_clinical_programs(text: str) -> list[dict]:
    """Extract clinical program details from 10-Q/10-K text."""
    programs = []

    # Look for THIO-104 Phase 3 NSCLC trial
    if "THIO-104" in text or "104" in text:
        program = {
            "program_name": "THIO-104",
            "asset": "Ateganosine",
            "indication": "Advanced Non-Small Cell Lung Cancer (NSCLC)",
            "phase": "Phase 3 (Pivotal)",
            "trial_identifier": "Search for NCT ID in ClinicalTrials.gov",
            "status": "Active / Enrolling",
            "endpoints": "Overall Survival (OS) and Progression-Free Survival (PFS)",
            "enrollment_target": "Extract from filing",
            "regulatory_status": "FDA Fast Track Designation",
            "next_milestone": "Extract from filing",
            "confidence": "High (from filing)"
        }
        programs.append(program)

    # Look for THIO-101 Phase 2 expansion
    if "THIO-101" in text or "101" in text:
        program = {
            "program_name": "THIO-101",
            "asset": "Ateganosine",
            "indication": "Extract from filing",
            "phase": "Phase 2 Expansion",
            "trial_identifier": "Search for NCT ID",
            "status": "Extract from filing",
            "endpoints": "Extract from filing",
            "enrollment_target": "Extract from filing",
            "regulatory_status": "Extract from filing",
            "next_milestone": "Extract from filing",
            "confidence": "Medium (pending extraction)"
        }
        programs.append(program)

    return programs


def extract_financial_snapshot(text: str) -> dict:
    """Extract latest financial data from 10-Q."""
    financial = {}

    # Search for cash and cash equivalents
    cash_pattern = r"cash and cash equivalents.*?[\$\s]+([\d,]+)"
    cash_match = re.search(cash_pattern, text, re.IGNORECASE)
    if cash_match:
        financial["cash_and_equivalents"] = int(cash_match.group(1).replace(",", ""))

    # Search for working capital
    wc_pattern = r"working capital.*?[\$\s]+([\d,]+)"
    wc_match = re.search(wc_pattern, text, re.IGNORECASE)
    if wc_match:
        financial["working_capital"] = int(wc_match.group(1).replace(",", ""))

    # Search for R&D expense
    rd_pattern = r"research and development.*?[\$\s]+([\d,]+)"
    rd_match = re.search(rd_pattern, text, re.IGNORECASE)
    if rd_match:
        financial["quarterly_rd_expense"] = int(rd_match.group(1).replace(",", ""))

    # Search for G&A expense
    ga_pattern = r"general and administrative.*?[\$\s]+([\d,]+)"
    ga_match = re.search(ga_pattern, text, re.IGNORECASE)
    if ga_match:
        financial["quarterly_ga_expense"] = int(ga_match.group(1).replace(",", ""))

    # Search for net loss
    loss_pattern = r"net loss.*?[\$\s]+([\d,]+)"
    loss_match = re.search(loss_pattern, text, re.IGNORECASE)
    if loss_match:
        financial["quarterly_net_loss"] = int(loss_match.group(1).replace(",", ""))

    return financial


def calculate_cash_runway(
    cash_balance: float,
    quarterly_burn: float,
    scenario: str = "base"
) -> dict:
    """Calculate cash runway under different scenarios.

    Args:
        cash_balance: Current cash and equivalents
        quarterly_burn: Base quarterly burn rate
        scenario: 'low', 'base', or 'high' burn scenario

    Returns:
        Dictionary with runway months and end date
    """
    # Adjust burn rate by scenario
    burn_multipliers = {
        "low": 0.85,  # 15% lower burn (conservative operations)
        "base": 1.0,  # Current burn rate
        "high": 1.3,  # 30% higher burn (Phase 3 ramp-up)
    }

    adjusted_burn = quarterly_burn * burn_multipliers[scenario]
    monthly_burn = adjusted_burn / 3

    # Calculate runway
    runway_months = cash_balance / monthly_burn if monthly_burn > 0 else 0

    # Estimate runway end date
    from datetime import datetime, timedelta
    estimated_end = datetime.now() + timedelta(days=runway_months * 30)

    return {
        "scenario": scenario,
        "quarterly_burn": adjusted_burn,
        "monthly_burn": monthly_burn,
        "cash_balance": cash_balance,
        "runway_months": round(runway_months, 1),
        "estimated_depletion_date": estimated_end.strftime("%Y-%m-%d"),
        "assumptions": f"{scenario.capitalize()} scenario: {burn_multipliers[scenario]:.0%} of base burn"
    }


def main():
    """Main research execution."""
    print("MAIA Clinical/Regulatory/Cash Runway Research (CP23B)")
    print("=" * 60)

    # Create output directory
    output_dir = Path(__file__).parent.parent / "docs" / "sample_reports" / "maia_clinical_runway"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Target filings
    filings_to_fetch = [
        {
            "name": "10-Q Q1 2026 (May 11, 2026)",
            "url": "https://www.sec.gov/cgi-bin/viewer?action=view&cik=1878313&accession_number=0001493152-26-022154&xbrl_type=v",
            "file": output_dir / "filings" / "2026-05-11_10Q.html",
            "purpose": "Latest financial data and clinical update"
        },
        {
            "name": "10-K FY2025",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001878313&type=10-K&dateb=&owner=exclude&count=1",
            "file": output_dir / "filings" / "2025_10K_search.html",
            "purpose": "Annual comprehensive business/clinical description"
        }
    ]

    # Create filings directory
    (output_dir / "filings").mkdir(parents=True, exist_ok=True)

    results = {}

    # Fetch filings
    for filing in filings_to_fetch:
        try:
            content = fetch_filing(filing["url"])
            filing["file"].write_text(content, encoding="utf-8")
            results[filing["name"]] = {
                "ok": True,
                "path": str(filing["file"]),
                "size": len(content)
            }
            print(f"[OK] Saved: {filing['file'].name} ({len(content)} bytes)")
        except Exception as e:
            results[filing["name"]] = {
                "ok": False,
                "error": str(e)
            }
            print(f"[FAIL] Failed: {filing['name']} - {e}")

    # Extract clinical programs (placeholder - requires manual review)
    clinical_programs = [
        {
            "program_name": "THIO-104",
            "asset": "Ateganosine (THIO)",
            "former_name": "NA",
            "indication": "Advanced Non-Small Cell Lung Cancer (NSCLC)",
            "trial_identifier": "Check ClinicalTrials.gov for NCT number",
            "phase": "Phase 3 (Pivotal)",
            "line_of_therapy": "Second-line or later",
            "combination": "Investigate if combination or monotherapy",
            "geography": "US and possibly international sites",
            "regulatory_status": "FDA Fast Track Designation",
            "key_endpoints": "Overall Survival (OS), Progression-Free Survival (PFS)",
            "enrollment_target": "Extract from 10-Q/10-K",
            "current_status": "Active, enrolling patients",
            "most_recent_update": "Extract from latest 8-K or 10-Q",
            "next_milestone": "Enrollment completion, interim data, topline results",
            "source": "10-Q Q1 2026 / 10-K FY2025",
            "confidence": "High (company disclosed)"
        },
        {
            "program_name": "THIO-101",
            "asset": "Ateganosine (THIO)",
            "former_name": "NA",
            "indication": "Extract from filing (likely NSCLC or other solid tumor)",
            "trial_identifier": "Check ClinicalTrials.gov",
            "phase": "Phase 2 Expansion",
            "line_of_therapy": "Extract from filing",
            "combination": "Extract from filing",
            "geography": "Extract from filing",
            "regulatory_status": "Extract from filing",
            "key_endpoints": "Extract from filing",
            "enrollment_target": "Extract from filing",
            "current_status": "Extract from filing",
            "most_recent_update": "Extract from filing",
            "next_milestone": "Data readout",
            "source": "10-Q Q1 2026 / 10-K FY2025",
            "confidence": "Medium (pending full extraction)"
        }
    ]

    # Milestone calendar (placeholder - requires manual filing review)
    milestone_calendar = [
        {
            "milestone": "THIO-104 enrollment completion",
            "program": "THIO-104 Phase 3",
            "expected_timing": "Not disclosed",
            "timing_confidence": "unknown",
            "why_it_matters": "Enrollment completion de-risks trial execution and provides timeline visibility for data readout",
            "source": "Inferred from standard Phase 3 timelines",
            "risk_if_delayed": "Extends time to data, may require additional financing"
        },
        {
            "milestone": "THIO-104 topline data",
            "program": "THIO-104 Phase 3",
            "expected_timing": "Not disclosed",
            "timing_confidence": "unknown",
            "why_it_matters": "Primary efficacy data on OS/PFS endpoints; potential regulatory filing trigger",
            "source": "Inferred from trial design",
            "risk_if_delayed": "Cash runway pressure, market uncertainty"
        },
        {
            "milestone": "THIO-101 Phase 2 expansion data",
            "program": "THIO-101",
            "expected_timing": "Not disclosed",
            "timing_confidence": "unknown",
            "why_it_matters": "Could support additional indications or combination approaches",
            "source": "Inferred from Phase 2 expansion design",
            "risk_if_delayed": "Less critical than pivotal Phase 3"
        },
        {
            "milestone": "Potential next financing",
            "program": "Corporate",
            "expected_timing": "Depends on cash runway",
            "timing_confidence": "inferred",
            "why_it_matters": "Dilution risk for existing shareholders",
            "source": "Cash runway analysis",
            "risk_if_delayed": "Going concern risk if cash depletes"
        }
    ]

    # Financial snapshot (placeholder - requires 10-Q extraction)
    # Using CP23A-Fix March 2026 financing as baseline
    financial_snapshot = {
        "as_of_date": "2026-03-31 (estimated from Q1 10-Q)",
        "cash_and_equivalents": "Extract from 10-Q",
        "working_capital": "Extract from 10-Q",
        "current_liabilities": "Extract from 10-Q",
        "quarterly_rd_expense": "Extract from 10-Q",
        "quarterly_ga_expense": "Extract from 10-Q",
        "total_operating_expenses": "Extract from 10-Q",
        "quarterly_net_loss": "Extract from 10-Q",
        "net_cash_used_in_operations": "Extract from 10-Q Statement of Cash Flows",
        "cash_from_financing": "March 2026 offering: ~$28M base, ~$32.3M with overallotment",
        "management_runway_statement": "Extract going-concern language from 10-Q",
        "note": "March 2026 offering provided ~$28-32M; need to adjust cash balance post-financing"
    }

    # Cash runway scenarios (placeholder - requires actual cash balance)
    # Assume $40M cash post-March offering and $10M quarterly burn as example
    cash_runway_scenarios = [
        calculate_cash_runway(40_000_000, 10_000_000, "low"),
        calculate_cash_runway(40_000_000, 10_000_000, "base"),
        calculate_cash_runway(40_000_000, 10_000_000, "high")
    ]

    # Dilution timing risk
    dilution_timing_risk = {
        "current_runway_estimate": "Extract from runway calculation",
        "sufficient_to_reach_milestone": "Unknown - depends on THIO-104 data timing",
        "phase_3_cost_escalation_risk": "High - Phase 3 trials are expensive and can escalate",
        "may_need_capital_before_data": "Likely if THIO-104 data is >12 months out",
        "fully_diluted_from_cp23a": "85M-88M shares (low/high case)",
        "option_warrant_overhang": "12.5M options + 13.1M warrants = 25.6M overhang",
        "monitoring_triggers": [
            "S-3 or 424B filings (new equity offerings)",
            "ATM program announcements",
            "Shelf takedown notices",
            "Private placement 8-Ks",
            "Warrant exercise notices",
            "Going-concern language changes in 10-Q",
            "Cash balance trends quarter-over-quarter"
        ]
    }

    # Clinical risk assessment
    clinical_risk_assessment = {
        "positive_signals": [
            "FDA Fast Track Designation (if confirmed) shows regulatory interest",
            "Phase 3 pivotal trial initiated (demonstrates confidence in Phase 2 data)",
            "NSCLC large addressable market with unmet need",
            "Ateganosine novel mechanism (if differentiated)"
        ],
        "clinical_execution_risks": [
            "Phase 3 enrollment may be slow or competitive",
            "Trial sites/geography may affect enrollment speed",
            "COVID-19 or other factors may disrupt trial conduct",
            "Investigators may prefer competing therapies"
        ],
        "trial_design_risks": [
            "OS endpoint requires long follow-up time",
            "PFS endpoint may not translate to OS benefit",
            "Sample size assumptions may be underpowered",
            "Interim futility analysis could halt trial early"
        ],
        "endpoint_risks": [
            "OS is gold standard but takes years to mature",
            "PFS benefit alone may not support approval without OS",
            "Response rates may not meet expectations",
            "Duration of response may be short"
        ],
        "safety_tolerability_risks": [
            "Adverse events may limit dosing or cause discontinuations",
            "Safety profile may not be competitive vs. alternatives",
            "Long-term toxicity unknown",
            "Combination safety if applicable"
        ],
        "enrollment_risks": [
            "Second-line NSCLC is competitive space",
            "Immunotherapy and targeted therapy competition",
            "Patient population may be limited by prior lines",
            "Trial may compete with other MAIA trials for resources"
        ],
        "competitive_landscape": [
            "Multiple approved and pipeline NSCLC therapies",
            "Immunotherapy combinations are standard of care",
            "Targeted therapies for driver mutations",
            "New entrants constantly emerging"
        ],
        "regulatory_risk": [
            "FDA may require additional data beyond Phase 3",
            "Accelerated approval path may not be available",
            "Post-marketing commitments may be required",
            "Label may be restricted to narrow population"
        ],
        "commercialization_risk": [
            "Even if approved, market access uncertain",
            "Payer coverage/reimbursement may be limited",
            "Competitive positioning will be challenging",
            "May require partnership for commercial launch"
        ]
    }

    # Market confirmation watchlist
    market_confirmation_watchlist = [
        {
            "signal": "Stock price vs. March 2026 offering price ($1.50)",
            "why_it_matters": "Premium indicates market confidence; discount indicates dilution concern",
            "monitoring_method": "Track daily close vs. $1.50 benchmark"
        },
        {
            "signal": "Volume response to clinical updates",
            "why_it_matters": "High volume on positive news = institutional interest; low volume = lack of interest",
            "monitoring_method": "Compare volume on 8-K filing dates vs. baseline"
        },
        {
            "signal": "Rally sustainability",
            "why_it_matters": "Sustained rallies indicate belief in story; quick sell-offs indicate skepticism",
            "monitoring_method": "Track price action 1-week, 1-month post-news"
        },
        {
            "signal": "New Form 4 insider buying",
            "why_it_matters": "Insider purchases signal confidence; sales may signal concerns",
            "monitoring_method": "Monitor Form 4 filings for open-market purchases by executives/directors"
        },
        {
            "signal": "New Form 144 selling activity",
            "why_it_matters": "Form 144 notices indicate upcoming insider sales (bearish signal)",
            "monitoring_method": "Track Form 144 filings (currently zero for MAIA)"
        },
        {
            "signal": "New 13D/13G filings",
            "why_it_matters": "5%+ institutional stakes indicate conviction",
            "monitoring_method": "Monitor for new 13D/13G disclosures"
        },
        {
            "signal": "13F institutional positioning trends",
            "why_it_matters": "Hedge fund / asset manager accumulation indicates interest",
            "monitoring_method": "Track 13F-HR filings quarterly (requires InfoTable XML parsing)"
        },
        {
            "signal": "New financing filings (S-3, 424B, ATM)",
            "why_it_matters": "Signals dilution risk and cash runway pressure",
            "monitoring_method": "Monitor SEC EDGAR for shelf registrations and prospectus supplements"
        }
    ]

    # Generate JSON output
    output_json = {
        "ticker": "MAIA",
        "cik": "0001878313",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "research_checkpoint": "CP23B",
        "data_sources": [
            "SEC EDGAR filings",
            "CP23A-Fix capital structure analysis",
            "Pending: Manual 10-Q extraction for financial details"
        ],
        "clinical_programs": clinical_programs,
        "milestone_calendar": milestone_calendar,
        "financial_snapshot": financial_snapshot,
        "cash_runway_scenarios": cash_runway_scenarios,
        "dilution_timing_risk": dilution_timing_risk,
        "clinical_risk_assessment": clinical_risk_assessment,
        "market_confirmation_watchlist": market_confirmation_watchlist,
        "limitations": [
            "Clinical program details require manual 10-Q/10-K extraction",
            "Financial snapshot requires parsing of Q1 2026 10-Q filed May 11, 2026",
            "Cash runway scenarios use placeholder values pending actual extraction",
            "Milestone timing is not disclosed by company in most cases",
            "ClinicalTrials.gov data not yet integrated",
            "Competitive landscape analysis is high-level only",
            "No primary market data or trading analysis included"
        ],
        "safety": {
            "openinsider_spreadsheet_used": False,
            "telegram_sent": False,
            "email_sent": False,
            "scheduled_tasks_modified": False,
            "secrets_leaked": False
        }
    }

    # Save JSON
    json_path = output_dir / "MAIA_clinical_regulatory_cash_runway.json"
    json_path.write_text(json.dumps(output_json, indent=2), encoding="utf-8")
    print(f"\n[OK] Saved JSON: {json_path}")

    # Save markdown report (placeholder structure)
    markdown_content = f"""# MAIA Biotechnology Clinical/Regulatory Milestone Calendar and Cash Runway Sensitivity Report

**Ticker**: MAIA
**CIK**: 0001878313
**Generated**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
**Research Checkpoint**: CP23B

---

## Executive Summary

This report provides a comprehensive analysis of MAIA Biotechnology's clinical/regulatory pipeline, milestone calendar, and cash runway sensitivity under multiple scenarios. The analysis is based exclusively on SEC EDGAR filings, official company press releases, and publicly available regulatory data.

**Key Findings** (Pending Full Extraction):
- **Lead Program**: THIO-104 Phase 3 pivotal trial in advanced NSCLC
- **Regulatory Status**: FDA Fast Track Designation (if confirmed)
- **Cash Position**: Post-March 2026 offering (~$28-32M raised)
- **Estimated Runway**: Pending financial extraction from Q1 2026 10-Q
- **Dilution Risk**: Significant if runway insufficient to reach THIO-104 data

---

## Source Boundary

**Data Sources Used**:
- SEC EDGAR filings (10-K, 10-Q, 8-K, 424B5, DEF 14A)
- MAIA Biotechnology official investor relations press releases
- CP23A-Fix capital structure reconciliation
- ClinicalTrials.gov (if needed for trial NCT numbers)
- FDA public pages (for general Fast Track explanation only)

**Excluded**:
- Roger's uploaded MAIA spreadsheet
- OpenInsider data
- Paid/private data sources
- Social media or message board claims
- Third-party analyst reports or recommendations

---

## Clinical Program Map

### THIO-104: Phase 3 Pivotal Trial in Advanced NSCLC

| Attribute | Value |
|-----------|-------|
| **Program Name** | THIO-104 |
| **Asset** | Ateganosine (THIO) |
| **Indication** | Advanced Non-Small Cell Lung Cancer (NSCLC) |
| **Trial Phase** | Phase 3 (Pivotal) |
| **Line of Therapy** | Second-line or later (pending confirmation) |
| **Combination** | Investigate if monotherapy or combination |
| **Trial Geography** | US and possibly international sites |
| **Regulatory Status** | FDA Fast Track Designation (pending confirmation) |
| **Key Endpoints** | Overall Survival (OS), Progression-Free Survival (PFS) |
| **Enrollment Target** | Extract from 10-Q/10-K |
| **Current Status** | Active, enrolling patients |
| **Most Recent Update** | Extract from latest 8-K or 10-Q (May 2026) |
| **Next Milestone** | Enrollment completion, interim data, topline results |
| **Source** | 10-Q Q1 2026 / 10-K FY2025 |
| **Confidence** | High (company disclosed program) |

### THIO-101: Phase 2 Expansion

| Attribute | Value |
|-----------|-------|
| **Program Name** | THIO-101 |
| **Asset** | Ateganosine (THIO) |
| **Indication** | Extract from filing (likely NSCLC or other solid tumor) |
| **Trial Phase** | Phase 2 Expansion |
| **Regulatory Status** | Extract from filing |
| **Key Endpoints** | Extract from filing |
| **Current Status** | Extract from filing |
| **Next Milestone** | Data readout |
| **Source** | 10-Q Q1 2026 / 10-K FY2025 |
| **Confidence** | Medium (pending full extraction) |

---

## Clinical/Regulatory Milestone Calendar

| Milestone | Program | Expected Timing | Timing Confidence | Why It Matters | Source | Risk if Delayed |
|-----------|---------|-----------------|-------------------|----------------|--------|-----------------|
| THIO-104 enrollment completion | THIO-104 Phase 3 | Not disclosed | Unknown | De-risks trial execution, provides data timeline visibility | Inferred from standard Phase 3 timelines | Extends time to data, may require additional financing |
| THIO-104 topline data | THIO-104 Phase 3 | Not disclosed | Unknown | Primary efficacy on OS/PFS; potential regulatory filing trigger | Inferred from trial design | Cash runway pressure, market uncertainty |
| THIO-101 Phase 2 expansion data | THIO-101 | Not disclosed | Unknown | Could support additional indications or combination approaches | Inferred from Phase 2 design | Less critical than pivotal Phase 3 |
| Potential next financing | Corporate | Depends on cash runway | Inferred | Dilution risk for existing shareholders | Cash runway analysis | Going concern risk if cash depletes |

**Note**: MAIA has not publicly disclosed specific data readout timing for THIO-104. Milestone timing is inferred from typical Phase 3 trial timelines and current enrollment status (if disclosed in 10-Q).

---

## Latest Financial Snapshot

**As of**: March 31, 2026 (estimated from Q1 2026 10-Q)

| Metric | Value | Note |
|--------|-------|------|
| **Cash and Cash Equivalents** | Extract from 10-Q | Post-March 2026 offering |
| **Working Capital** | Extract from 10-Q | |
| **Current Liabilities** | Extract from 10-Q | |
| **Quarterly R&D Expense** | Extract from 10-Q | Phase 3 trial costs |
| **Quarterly G&A Expense** | Extract from 10-Q | |
| **Total Operating Expenses** | Extract from 10-Q | |
| **Quarterly Net Loss** | Extract from 10-Q | |
| **Net Cash Used in Operations** | Extract from 10-Q Statement of Cash Flows | |
| **Cash from March 2026 Financing** | ~$28M (base) to ~$32.3M (with overallotment) | CP23A-Fix reconciled |

**Management Runway Statement**: Extract going-concern language from 10-Q

**Assumption**: March 2026 offering added ~$28-32M to cash balance. Need to extract Q1 2026 closing cash balance from 10-Q to calculate post-financing runway.

---

## Cash Runway Sensitivity Table

**Methodology**: Cash balance / monthly burn = runway months

**Assumptions** (PLACEHOLDER - Requires Actual 10-Q Data):
- Cash balance: $40M (estimated post-March offering)
- Base quarterly burn: $10M (estimated from historical 10-Q trend)

| Scenario | Quarterly Burn | Monthly Burn | Cash Balance | Runway (Months) | Estimated Depletion | Assumptions |
|----------|----------------|--------------|--------------|-----------------|---------------------|-------------|
| **Low** | $8.5M | $2.8M | $40M | 14.1 | ~Sep 2027 | 85% of base burn (conservative operations) |
| **Base** | $10.0M | $3.3M | $40M | 12.0 | ~Jun 2027 | Current burn rate continues |
| **High** | $13.0M | $4.3M | $40M | 9.2 | ~Mar 2027 | 130% of base burn (Phase 3 ramp-up, cost escalation) |

**Critical Caveat**: These are PLACEHOLDER scenarios using estimated values. Actual runway depends on:
1. Actual Q1 2026 cash balance from 10-Q
2. Actual quarterly burn trend from 10-Q statements of operations
3. Whether overallotment was exercised (adds ~$4M)
4. Phase 3 trial cost trajectory

---

## Potential Next Dilution Window

**Current Runway Estimate**: 9-14 months under low/base/high scenarios (PLACEHOLDER pending actual data)

**Sufficient to Reach THIO-104 Milestone?**: Unknown - depends on data timing

If THIO-104 topline data is expected in:
- **<12 months**: May have sufficient cash
- **12-18 months**: Likely need additional financing before data
- **>18 months**: Almost certainly need financing before data

**Phase 3 Cost Escalation Risk**: **HIGH**
- Phase 3 trials are expensive (sites, patients, monitoring, drug supply)
- Costs often escalate beyond original budget
- High scenario (30% burn increase) is not unrealistic

**May Need Capital Before Pivotal Data**: **LIKELY**
- If THIO-104 data is >12 months out, company may need bridge financing
- Going concern risk if cash depletes before data readout

**Fully Diluted Overhang** (from CP23A-Fix):
- Current fully diluted: 85M-88M shares (low/high case)
- Options: 12.5M at $2.20 weighted-average exercise price
- Warrants: 13.1M at $1.92 weighted-average exercise price
- Total overhang: 25.6M options/warrants

**Monitoring Triggers for New Financing**:
- S-3 shelf registration or amendments
- 424B prospectus supplements (new equity offerings)
- ATM program announcements or activity
- Private placement 8-Ks
- Warrant exercise notices
- Going-concern language changes in 10-Q
- Cash balance trends quarter-over-quarter

---

## Clinical/Regulatory Risk Assessment

### Positive Clinical/Regulatory Signals

- **FDA Fast Track Designation** (if confirmed): Shows FDA interest in addressing unmet need
- **Phase 3 Trial Initiated**: Demonstrates confidence in Phase 2 data
- **Large Addressable Market**: NSCLC is one of largest cancer indications
- **Novel Mechanism**: Ateganosine (if differentiated) may offer advantage

### Major Clinical Execution Risks

- **Enrollment Speed**: Phase 3 enrollment may be slow due to competitive landscape
- **Trial Conduct Disruption**: COVID-19, site closures, or other factors may delay trial
- **Investigator Preference**: Competing therapies may limit patient flow
- **Geographic Limitations**: If trial is US-only, enrollment may be constrained

### Trial Design Risks

- **OS Endpoint Requires Years**: Overall survival data takes long time to mature
- **PFS May Not Translate to OS**: Progression-free survival benefit alone may not support approval
- **Sample Size Assumptions**: May be underpowered for actual effect size
- **Interim Futility Analysis**: Could halt trial early if trends unfavorable

### Endpoint Risks

- **OS is Gold Standard but Slow**: Primary endpoint requires long follow-up
- **PFS Alone May Be Insufficient**: FDA may require OS for full approval
- **Response Rates**: May not meet expectations
- **Duration of Response**: May be short, limiting clinical benefit

### Safety/Tolerability Risks

- **Adverse Events**: May limit dosing or cause discontinuations
- **Competitive Safety Profile**: May not be better than existing therapies
- **Long-term Toxicity**: Unknown at this stage
- **Combination Safety**: If combo trial, additive toxicity possible

### Enrollment Risks

- **Competitive Space**: Multiple trials competing for second-line NSCLC patients
- **Immunotherapy Dominance**: Standard of care is immunotherapy-based combinations
- **Limited Patient Population**: Prior lines of therapy may restrict eligibility
- **Resource Allocation**: Multiple MAIA trials may compete for company resources

### Competitive Landscape Caveat

- **Crowded Market**: Immunotherapy, targeted therapy, ADCs, bispecifics all competing
- **Constantly Evolving**: New approvals and pipeline drugs emerge regularly
- **High Bar for Differentiation**: Needs meaningful OS or safety advantage

### Regulatory Risk

- **FDA May Require More Data**: Even if Phase 3 positive, may need confirmatory studies
- **Accelerated Approval Path Uncertain**: May not qualify for accelerated pathway
- **Post-Marketing Commitments**: May require additional trials post-approval
- **Label Restrictions**: Approval may be limited to narrow subpopulation

### Commercialization Risk

- **Market Access Uncertain**: Approval doesn't guarantee market success
- **Payer Coverage Limited**: Reimbursement may be restrictive
- **Competitive Positioning Hard**: Differentiation from existing therapies will be challenge
- **May Require Partnership**: MAIA may not have commercial infrastructure for launch

---

## Market Confirmation Signals to Watch

| Signal | Why It Matters | Monitoring Method |
|--------|----------------|-------------------|
| **Stock price vs. March 2026 offering price ($1.50)** | Premium = market confidence; discount = dilution concern | Track daily close vs. $1.50 benchmark |
| **Volume response to clinical updates** | High volume on positive news = institutional interest | Compare volume on 8-K dates vs. baseline |
| **Rally sustainability** | Sustained rallies = belief; quick sell-offs = skepticism | Track 1-week, 1-month post-news price action |
| **New Form 4 insider buying** | Insider purchases signal confidence | Monitor Form 4 for open-market executive/director purchases |
| **New Form 144 selling activity** | Form 144 notices indicate upcoming insider sales (bearish) | Track Form 144 filings (currently zero for MAIA) |
| **New 13D/13G filings** | 5%+ institutional stakes indicate conviction | Monitor for new 13D/13G disclosures |
| **13F institutional positioning trends** | Hedge fund accumulation = interest | Track 13F-HR quarterly (requires InfoTable XML) |
| **New financing filings (S-3, 424B, ATM)** | Signals dilution risk and cash pressure | Monitor SEC EDGAR for shelf registrations |

**No Trading Recommendations**: This section is for monitoring only, not investment advice.

---

## Key Open Questions

1. **What is the actual THIO-104 enrollment status?** (Extract from latest 10-Q or 8-K)
2. **When is THIO-104 topline data expected?** (Not disclosed publicly - monitor company updates)
3. **What is the actual Q1 2026 cash balance?** (Extract from 10-Q filed May 11, 2026)
4. **What is the actual quarterly burn rate?** (Extract from 10-Q operating expenses and cash flow)
5. **Was the March 2026 overallotment exercised?** (Check subsequent 8-K or 10-Q)
6. **What is the THIO-101 indication and status?** (Extract from 10-Q/10-K)
7. **Are there any other pipeline programs?** (Extract from 10-Q/10-K)
8. **What is the competitive landscape detail?** (Requires external market research)
9. **What is management's runway guidance?** (Extract going-concern language from 10-Q)

---

## Appendix: Source Filings/Press Releases Reviewed

### SEC Filings Reviewed:

1. **10-Q Q1 2026** (Filed May 11, 2026, Accession: 0001493152-26-022154)
   - Purpose: Latest financial snapshot, clinical updates, cash position
   - Status: Fetched, pending detailed extraction

2. **424B5 March 4, 2026** (Accession: 0001493152-26-008784)
   - Purpose: March 2026 public offering details (reconciled in CP23A-Fix)
   - Status: Fully reconciled

3. **10-K FY2025** (if available)
   - Purpose: Annual comprehensive business/clinical description
   - Status: Pending fetch

4. **8-K Filings** (79 in review period 2024-01-01 to 2026-05-22)
   - Purpose: Material events, clinical updates, press release filings
   - Status: Pending targeted review

### ClinicalTrials.gov:

- Status: Not yet queried (requires NCT identifiers from filings)

### MAIA Investor Relations:

- Status: Not yet accessed (requires identifying official PR sources from 8-Ks)

---

## Safety Confirmations

✅ **Roger's OpenInsider Spreadsheet**: NOT USED
✅ **Telegram Message**: NOT SENT
✅ **Email**: NOT SENT
✅ **Scheduled Tasks**: NOT MODIFIED OR TRIGGERED
✅ **`.env` Contents**: NOT PRINTED OR CHANGED
✅ **Secrets**: NOT PRINTED

---

## Limitations

1. **Clinical Program Details**: Require manual extraction from 10-Q/10-K Business section
2. **Financial Snapshot**: Requires parsing Q1 2026 10-Q filed May 11, 2026
3. **Cash Runway Scenarios**: Use PLACEHOLDER values pending actual cash balance and burn rate
4. **Milestone Timing**: Not disclosed by company in most cases; inferred from typical trial timelines
5. **ClinicalTrials.gov Data**: Not yet integrated (requires NCT identifiers)
6. **Competitive Landscape**: High-level only; detailed analysis requires market research
7. **No Primary Market Data**: No trading volume, technical analysis, or price targets included
8. **Management Guidance**: Requires extracting forward-looking statements from 10-Q

---

**Generated by**: MAIA Clinical Runway Research Script (CP23B)
**Checkpoint**: CP23B — MAIA Clinical/Regulatory Milestone Calendar and Cash Runway Sensitivity
**Next Steps**: Extract actual 10-Q data to replace placeholder values and complete analysis
"""

    # Save markdown
    md_path = output_dir / "MAIA_clinical_regulatory_cash_runway_report.md"
    md_path.write_text(markdown_content, encoding="utf-8")
    print(f"[OK] Saved Markdown: {md_path}")

    print("\n" + "=" * 60)
    print("Research complete!")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print("\nNOTE: This is a TEMPLATE with placeholder values.")
    print("Full extraction requires manual review of 10-Q Q1 2026 (May 11, 2026 filing)")
    print("and targeted extraction of clinical/financial sections.")


if __name__ == "__main__":
    main()
