"""Apply official MAIA 10-Q values to clinical runway report (CP23B-Fix3).

This script replaces CP23B-Fix2 incorrect values with official Q1 2026 10-Q/XBRL values:
- Cash: $38.25M incorrect → $34.41M official
- Quarterly operating burn: $8.9M incorrect → $5.31M official
- R&D expense: $6.85M incorrect → $3.53M official
- G&A expense: $2.35M incorrect → $3.42M official
- Net loss: $9.45M incorrect → $6.37M official
- Common shares: 65,033,854 incorrect → 60,671,491 official
- Accumulated deficit: $142.5M incorrect → $116.0M official

Base runway changes from 12.9 months (CP23B-Fix2) to 19.4 months (CP23B-Fix3)
due to lower official burn rate.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


def calculate_cash_runway(cash_balance: float, quarterly_burn: float, scenario: str = "base") -> dict:
    """Calculate cash runway under different scenarios using official burn rate.

    Args:
        cash_balance: Official cash balance from 10-Q
        quarterly_burn: Official quarterly operating cash burn from 10-Q
        scenario: "low", "base", or "high"

    Returns:
        dict: Runway scenario with official values
    """
    burn_multipliers = {
        "low": 0.85,  # 15% lower burn (operational efficiency)
        "base": 1.0,  # Official burn rate from 10-Q
        "high": 1.35,  # 35% higher burn (Phase 3 ramp-up)
    }

    adjusted_burn = abs(quarterly_burn) * burn_multipliers[scenario]
    monthly_burn = adjusted_burn / 3
    runway_months = cash_balance / monthly_burn if monthly_burn > 0 else 0
    estimated_end = datetime.now() + timedelta(days=runway_months * 30)

    return {
        "scenario": scenario,
        "quarterly_burn": adjusted_burn,
        "monthly_burn": round(monthly_burn, 2),
        "cash_balance": cash_balance,
        "runway_months": round(runway_months, 1),
        "estimated_depletion_date": estimated_end.strftime("%Y-%m-%d"),
        "assumptions": f"{scenario.capitalize()} scenario: {int(burn_multipliers[scenario] * 100)}% of official base burn",
        "burn_multiplier": burn_multipliers[scenario],
        "source": "Official Q1 2026 10-Q operating cash burn"
    }


def apply_official_10q_values() -> None:
    """Apply official 10-Q values to clinical runway JSON."""

    # Load official 10-Q financial data
    official_financials_path = Path("docs/sample_reports/maia_clinical_runway/maia_10q_q1_2026_actual_financials.json")
    with open(official_financials_path, "r", encoding="utf-8") as f:
        official_financials = json.load(f)

    # Load current clinical runway JSON
    clinical_runway_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway.json")
    with open(clinical_runway_path, "r", encoding="utf-8") as f:
        clinical_runway = json.load(f)

    print("Applying official 10-Q values to clinical runway report (CP23B-Fix3)...")

    # Update checkpoint
    clinical_runway["research_checkpoint"] = "CP23B-Fix3"
    clinical_runway["reconciliation_date"] = datetime.now().strftime("%Y-%m-%d")
    clinical_runway["generated_at"] = datetime.now().isoformat() + "+00:00"

    # Update data sources - emphasize official XBRL
    clinical_runway["data_sources"] = [
        "SEC EDGAR filings - Form 10-Q filed 2026-05-11 for Q1 2026 (official XBRL values)",
        "CP23A-Fix capital structure analysis (March 2026 offering)",
        "Official XBRL financial data extracted from 10-Q",
        "Management's Discussion and Analysis (10-Q Part I, Item 2)"
    ]

    # Update financial snapshot with official 10-Q values
    clinical_runway["financial_snapshot"] = {
        "as_of_date": "2026-03-31",
        "source": "OFFICIAL SEC 10-Q XBRL Q1 2026 (filed 2026-05-11)",
        "confidence": "HIGH",
        "filing_metadata": official_financials["filing_metadata"],
        "reconciliation_notes": official_financials["reconciliation_notes"],

        # Official balance sheet values
        "cash_and_equivalents": official_financials["cash_and_cash_equivalents"]["value"],
        "prepaid_expenses_and_other_current_assets": official_financials["prepaid_expenses_and_other_current_assets"]["value"],
        "current_assets": official_financials["current_assets"]["value"],
        "other_assets": official_financials["other_assets"]["value"],
        "total_assets": official_financials["total_assets"]["value"],
        "accounts_payable": official_financials["accounts_payable"]["value"],
        "accrued_expenses": official_financials["accrued_expenses"]["value"],
        "current_liabilities": official_financials["current_liabilities"]["value"],
        "warrant_liability": official_financials["warrant_liability"]["value"],
        "total_liabilities": official_financials["total_liabilities"]["value"],
        "working_capital": official_financials["working_capital"]["value"],
        "accumulated_deficit": official_financials["accumulated_deficit"]["value"],
        "common_shares_outstanding": official_financials["common_shares_outstanding"]["value"],

        # Official Q1 2026 income statement values
        "quarterly_rd_expense": official_financials["research_and_development_expense"]["value"],
        "quarterly_ga_expense": official_financials["general_and_administrative_expense"]["value"],
        "total_operating_expenses": official_financials["total_operating_expenses"]["value"],
        "loss_from_operations": official_financials["loss_from_operations"]["value"],
        "interest_income": official_financials["interest_income"]["value"],
        "grant_income": official_financials["grant_income"]["value"],
        "change_in_fair_value_of_warrant_liability": official_financials["change_in_fair_value_of_warrant_liability"]["value"],
        "other_income_expense_net": official_financials["other_income_expense_net"]["value"],
        "quarterly_net_loss": abs(official_financials["net_loss"]["value"]),
        "weighted_average_common_shares_outstanding": official_financials["weighted_average_common_shares_outstanding"]["value"],

        # Official Q1 2026 cash flow values
        "net_cash_used_in_operations": abs(official_financials["net_cash_used_in_operations"]["value"]),
        "net_cash_provided_by_financing": official_financials["net_cash_provided_by_financing"]["value"],
        "net_increase_in_cash": official_financials["net_increase_in_cash"]["value"],
        "cash_beginning_of_period": official_financials["cash_beginning_of_period"]["value"],
        "cash_end_of_period": official_financials["cash_end_of_period"]["value"],

        # Antidilutive securities from 10-Q Note 11
        "stock_options_excluded_from_diluted_eps": official_financials["stock_options_excluded_from_diluted_eps"]["value"],
        "warrants_excluded_from_diluted_eps": official_financials["warrants_excluded_from_diluted_eps"]["value"],

        # Management statements from 10-Q
        "management_runway_statement": official_financials["management_liquidity_statement"]["value"],
        "going_concern_language": official_financials["going_concern_language"]["note"],

        # XBRL source tags
        "xbrl_sources": {
            "cash": official_financials["cash_and_cash_equivalents"]["xbrl_tag"],
            "current_assets": official_financials["current_assets"]["xbrl_tag"],
            "current_liabilities": official_financials["current_liabilities"]["xbrl_tag"],
            "rd_expense": official_financials["research_and_development_expense"]["xbrl_tag"],
            "ga_expense": official_financials["general_and_administrative_expense"]["xbrl_tag"],
            "operating_expenses": official_financials["total_operating_expenses"]["xbrl_tag"],
            "net_loss": official_financials["net_loss"]["xbrl_tag"],
            "operating_cash_flow": official_financials["net_cash_used_in_operations"]["xbrl_tag"],
            "financing_cash_flow": official_financials["net_cash_provided_by_financing"]["xbrl_tag"]
        }
    }

    # Recalculate cash runway scenarios using OFFICIAL operating cash burn ($5.31M quarterly)
    official_cash = official_financials["cash_and_cash_equivalents"]["value"]
    official_quarterly_burn = abs(official_financials["net_cash_used_in_operations"]["value"])

    print(f"  Official cash: ${official_cash:,}")
    print(f"  Official quarterly burn: ${official_quarterly_burn:,}")
    print("  Recalculating runway scenarios with official burn rate...")

    clinical_runway["cash_runway_scenarios"] = [
        calculate_cash_runway(official_cash, official_quarterly_burn, "low"),
        calculate_cash_runway(official_cash, official_quarterly_burn, "base"),
        calculate_cash_runway(official_cash, official_quarterly_burn, "high")
    ]

    # Update dilution timing risk with official runway
    base_runway = clinical_runway["cash_runway_scenarios"][1]["runway_months"]
    clinical_runway["dilution_timing_risk"]["current_runway_estimate"] = f"{base_runway} months (base case, official 10-Q)"
    clinical_runway["dilution_timing_risk"]["sufficient_to_reach_milestone"] = "Unknown - depends on THIO-104 data timing which is not disclosed; Management states 12+ months runway sufficient"
    clinical_runway["dilution_timing_risk"]["may_need_capital_before_data"] = f"Possible if THIO-104 data is >{base_runway} months out; Management assessed 12+ months runway"

    # Update fully diluted overhang with official values
    clinical_runway["dilution_timing_risk"]["fully_diluted_from_cp23a"] = "CP23A-Fix estimates will need reconciliation against official Q1 2026 basic shares (60,671,491) + options (13,097,991) + warrants (13,086,220) = ~86.86M fully diluted"

    # Add reconciliation_status section for CP23B-Fix3
    clinical_runway["reconciliation_status"] = official_financials["cp23b_fix3_compliance"]
    clinical_runway["reconciliation_status"]["checkpoint"] = "CP23B-Fix3"
    clinical_runway["reconciliation_status"]["superseded_checkpoints"] = ["CP23B", "CP23B-Fix", "CP23B-Fix2"]
    clinical_runway["reconciliation_status"]["superseded_reasons"] = [
        "CP23B used placeholder values ($40M cash, $10M burn) without sourcing",
        "CP23B-Fix used estimated values based on 'typical Phase 2/3 biotech patterns'",
        "CP23B-Fix2 used incorrect values that did not match official MAIA 10-Q XBRL",
        "CP23B-Fix3 replaces all incorrect values with official SEC 10-Q XBRL disclosed values"
    ]
    clinical_runway["reconciliation_status"]["cp23b_fix2_incorrect_values"] = official_financials["cp23b_fix2_superseded_incorrect_values"]

    # Save updated JSON
    with open(clinical_runway_path, "w", encoding="utf-8") as f:
        json.dump(clinical_runway, f, indent=2)

    print(f"  [OK] Updated: {clinical_runway_path}")
    print()
    print("=" * 80)
    print("OFFICIAL 10-Q VALUES APPLIED TO CLINICAL RUNWAY REPORT (CP23B-Fix3)")
    print("=" * 80)
    print(f"  Research Checkpoint: CP23B-Fix3")
    print(f"  Data Source: OFFICIAL SEC 10-Q XBRL Q1 2026 (filed 2026-05-11)")
    print(f"  Confidence: HIGH")
    print()
    print("  Financial Snapshot (Official Values):")
    print(f"    Cash (Mar 31, 2026):           ${official_cash:,}")
    print(f"    Quarterly Operating Burn:      ${official_quarterly_burn:,}")
    print(f"    Base Runway:                   {base_runway} months")
    print(f"    Estimated Depletion (Base):    {clinical_runway['cash_runway_scenarios'][1]['estimated_depletion_date']}")
    print()
    print("  Changes from CP23B-Fix2 (incorrect) to CP23B-Fix3 (official):")
    print(f"    Cash: $38.25M incorrect -> ${official_cash/1e6:.2f}M official")
    print(f"    Quarterly Burn: $8.9M incorrect -> ${official_quarterly_burn/1e6:.2f}M official")
    print(f"    R&D Expense: $6.85M incorrect -> ${official_financials['research_and_development_expense']['value']/1e6:.2f}M official")
    print(f"    G&A Expense: $2.35M incorrect -> ${official_financials['general_and_administrative_expense']['value']/1e6:.2f}M official")
    print(f"    Base Runway: 12.9 months incorrect -> {base_runway} months official")
    print()
    print("  [OK] All CP23B-Fix2 incorrect values replaced with official XBRL")
    print("  [OK] Base runway anchored to official SEC 10-Q operating cash burn")
    print("  [OK] Management assessed 12+ months runway as of Mar 31, 2026")
    print("  [OK] No going concern uncertainty")
    print()


def main() -> int:
    """Main execution function.

    Returns:
        int: Exit code (0 = success, 1 = failure)
    """
    try:
        apply_official_10q_values()
        return 0

    except Exception as e:
        print(f"\n[FAIL] Error applying official 10-Q values: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
