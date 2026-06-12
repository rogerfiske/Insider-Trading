"""SEC XBRL financial extraction and normalization.

This module extracts canonical financial metrics from SEC companyfacts data
using tag alias mapping to handle multiple XBRL concept names for the same
financial metric.

Example:
    >>> from sources.sec_companyfacts import fetch_companyfacts, parse_companyfacts
    >>> cf = fetch_companyfacts("0001878313")
    >>> parsed = parse_companyfacts(cf["body"])
    >>> metrics = extract_financial_metrics(parsed["facts"]["us-gaap"], period_end="2026-03-31")
    >>> metrics["cash_and_cash_equivalents"]["value"]
    34413110
"""

from __future__ import annotations

from sources.sec_companyfacts import get_concept_values, get_latest_value


# Tag alias map: canonical metric name -> list of possible XBRL concept names
# Maps standardized financial metric names to one or more US-GAAP XBRL tags
TAG_ALIAS_MAP = {
    "cash_and_cash_equivalents": [
        "Cash",
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        "CashAndCashEquivalentsAtCarryingValueIncludingDisposalGroupAndDiscontinuedOperations",
    ],
    "short_term_investments": [
        "ShortTermInvestments",
        "AvailableForSaleSecuritiesCurrent",
    ],
    "current_assets": [
        "AssetsCurrent",
    ],
    "current_liabilities": [
        "LiabilitiesCurrent",
    ],
    "total_assets": [
        "Assets",
    ],
    "total_liabilities": [
        "Liabilities",
    ],
    "stockholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "accumulated_deficit": [
        "RetainedEarningsAccumulatedDeficit",
        "AccumulatedDeficit",
    ],
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
    ],
    "cost_of_revenue": [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
    ],
    "gross_profit": [
        "GrossProfit",
    ],
    "research_and_development_expense": [
        "ResearchAndDevelopmentExpense",
    ],
    "selling_general_and_administrative_expense": [
        "SellingGeneralAndAdministrativeExpense",
    ],
    "general_and_administrative_expense": [
        "GeneralAndAdministrativeExpense",
    ],
    "operating_expenses": [
        "OperatingExpenses",
        "OperatingExpensesAbstract",
    ],
    "operating_loss": [
        "OperatingIncomeLoss",
    ],
    "net_loss": [
        "NetIncomeLoss",
        "ProfitLoss",
    ],
    "weighted_average_shares_basic": [
        "WeightedAverageNumberOfSharesOutstandingBasic",
    ],
    "weighted_average_shares_diluted": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
    "basic_eps": [
        "EarningsPerShareBasic",
    ],
    "diluted_eps": [
        "EarningsPerShareDiluted",
    ],
    "net_cash_used_in_operating_activities": [
        "NetCashProvidedByUsedInOperatingActivities",
    ],
    "net_cash_used_in_investing_activities": [
        "NetCashProvidedByUsedInInvestingActivities",
    ],
    "net_cash_provided_by_financing_activities": [
        "NetCashProvidedByUsedInFinancingActivities",
    ],
    "net_increase_in_cash": [
        "CashAndCashEquivalentsPeriodIncreaseDecrease",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseExcludingExchangeRateEffect",
    ],
    "capital_expenditures": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "CapitalExpendituresIncurredButNotYetPaid",
    ],
    "common_shares_outstanding": [
        "CommonStockSharesOutstanding",
    ],
    "common_shares_issued": [
        "CommonStockSharesIssued",
    ],
    "preferred_shares_outstanding": [
        "PreferredStockSharesOutstanding",
    ],
    "stock_based_compensation": [
        "StockBasedCompensation",
        "AllocatedShareBasedCompensationExpense",
    ],
    "warrant_liability": [
        "WarrantLiability",
        "DerivativeLiabilityCurrent",
    ],
}


# Reverse map for looking up canonical name from XBRL concept
CONCEPT_TO_CANONICAL = {}
for canonical, concepts in TAG_ALIAS_MAP.items():
    for concept in concepts:
        CONCEPT_TO_CANONICAL[concept] = canonical


def extract_financial_metrics(
    facts_us_gaap: dict,
    period_end: str | None = None,
    fiscal_period: str | None = None
) -> dict[str, dict]:
    """Extract standardized financial metrics from US-GAAP facts.

    Args:
        facts_us_gaap: US-GAAP taxonomy facts from parsed companyfacts
        period_end: Optional period end date filter (YYYY-MM-DD)
        fiscal_period: Optional fiscal period filter (Q1, Q2, Q3, Q4, FY)

    Returns:
        dict mapping canonical metric names to metric dicts with:
            value: numeric value
            unit: unit (USD, shares, etc.)
            concept: XBRL concept name used
            period_end: period end date
            period_start: period start date (for duration metrics)
            fiscal_year: fiscal year
            fiscal_period: fiscal period
            form: form type
            filed: filing date
            source: "sec_companyfacts"
            status: "ok" or "not_available"

    Example:
        >>> metrics = extract_financial_metrics(facts, period_end="2026-03-31")
        >>> metrics["cash_and_cash_equivalents"]["value"]
        34413110
    """
    metrics = {}

    for canonical_name, concept_aliases in TAG_ALIAS_MAP.items():
        metric_found = False

        for concept in concept_aliases:
            # Determine expected unit
            if "shares" in canonical_name.lower() or "eps" in canonical_name.lower():
                unit = "shares"
            else:
                unit = "USD"

            # Get concept data directly from facts_us_gaap
            concept_data = facts_us_gaap.get(concept, {})
            units_data = concept_data.get("units", {})
            values = units_data.get(unit, [])

            if not values:
                continue

            # Apply period filter if specified
            if period_end:
                values = [v for v in values if v.get("end") == period_end]

            if fiscal_period:
                values = [v for v in values if v.get("fp") == fiscal_period]

            if not values:
                continue

            # Take latest value
            latest = values[-1]

            metrics[canonical_name] = {
                "value": latest.get("val"),
                "unit": unit,
                "concept": concept,
                "period_end": latest.get("end"),
                "period_start": latest.get("start"),
                "fiscal_year": latest.get("fy"),
                "fiscal_period": latest.get("fp"),
                "form": latest.get("form"),
                "filed": latest.get("filed"),
                "accession": latest.get("accn"),
                "frame": latest.get("frame"),
                "source": "sec_companyfacts",
                "status": "ok",
            }

            metric_found = True
            break  # Found metric, no need to try other aliases

        if not metric_found:
            # Record missing metric
            metrics[canonical_name] = {
                "value": None,
                "status": "not_available",
                "source": "sec_companyfacts",
            }

    return metrics


def select_latest_quarter(facts_us_gaap: dict) -> dict | None:
    """Select the latest quarterly period from facts.

    Args:
        facts_us_gaap: US-GAAP taxonomy facts from parsed companyfacts

    Returns:
        dict with period information:
            period_end: period end date
            fiscal_year: fiscal year
            fiscal_period: fiscal period (Q1, Q2, Q3, or Q4)
            form: form type (should be 10-Q)
            filed: filing date
        or None if no quarterly period found

    Example:
        >>> latest_q = select_latest_quarter(facts)
        >>> latest_q["period_end"]
        "2026-03-31"
    """
    # Need to pass the full facts dict with 'us-gaap' key
    if "us-gaap" not in facts_us_gaap:
        # Already received us-gaap facts directly
        us_gaap_facts = facts_us_gaap
    else:
        # Received full facts dict
        us_gaap_facts = facts_us_gaap["us-gaap"]

    # Use Assets as a representative concept to find periods
    assets_concept = us_gaap_facts.get("Assets", {})
    assets_values = assets_concept.get("units", {}).get("USD", [])

    if not assets_values:
        return None

    # Filter to quarterly periods (Q1, Q2, Q3, Q4)
    quarterly = [v for v in assets_values if v.get("fp") in ["Q1", "Q2", "Q3", "Q4"]]

    if not quarterly:
        return None

    latest = quarterly[-1]

    return {
        "period_end": latest.get("end"),
        "fiscal_year": latest.get("fy"),
        "fiscal_period": latest.get("fp"),
        "form": latest.get("form"),
        "filed": latest.get("filed"),
        "accession": latest.get("accn"),
    }


def select_latest_annual(facts_us_gaap: dict) -> dict | None:
    """Select the latest annual period from facts.

    Args:
        facts_us_gaap: US-GAAP taxonomy facts from parsed companyfacts

    Returns:
        dict with period information:
            period_end: period end date
            fiscal_year: fiscal year
            fiscal_period: "FY"
            form: form type (should be 10-K)
            filed: filing date
        or None if no annual period found

    Example:
        >>> latest_annual = select_latest_annual(facts)
        >>> latest_annual["period_end"]
        "2025-12-31"
    """
    # Need to pass the full facts dict with 'us-gaap' key
    if "us-gaap" not in facts_us_gaap:
        # Already received us-gaap facts directly
        us_gaap_facts = facts_us_gaap
    else:
        # Received full facts dict
        us_gaap_facts = facts_us_gaap["us-gaap"]

    # Use Assets as a representative concept to find periods
    assets_concept = us_gaap_facts.get("Assets", {})
    assets_values = assets_concept.get("units", {}).get("USD", [])

    if not assets_values:
        return None

    # Filter to annual periods (FY)
    annual = [v for v in assets_values if v.get("fp") == "FY"]

    if not annual:
        return None

    latest = annual[-1]

    return {
        "period_end": latest.get("end"),
        "fiscal_year": latest.get("fy"),
        "fiscal_period": latest.get("fp"),
        "form": latest.get("form"),
        "filed": latest.get("filed"),
        "accession": latest.get("accn"),
    }


def calculate_derived_metrics(metrics: dict[str, dict]) -> dict[str, dict]:
    """Calculate derived financial metrics from extracted base metrics.

    Args:
        metrics: Extracted financial metrics from extract_financial_metrics()

    Returns:
        dict mapping derived metric names to metric dicts with:
            value: calculated value
            unit: unit
            calculation: formula used
            status: "ok", "not_meaningful", or "not_applicable"

    Derived metrics:
        - working_capital = current_assets - current_liabilities
        - quarterly_burn = abs(net_cash_used_in_operating_activities) if negative
        - monthly_burn = quarterly_burn / 3
        - cash_runway_months = cash / monthly_burn (if burn > 0)
        - current_ratio = current_assets / current_liabilities

    Example:
        >>> derived = calculate_derived_metrics(metrics)
        >>> derived["working_capital"]["value"]
        29781476
    """
    derived = {}

    # Working capital = current_assets - current_liabilities
    current_assets = metrics.get("current_assets", {}).get("value")
    current_liabilities = metrics.get("current_liabilities", {}).get("value")

    if current_assets is not None and current_liabilities is not None:
        derived["working_capital"] = {
            "value": current_assets - current_liabilities,
            "unit": "USD",
            "calculation": "current_assets - current_liabilities",
            "status": "ok",
        }
    else:
        derived["working_capital"] = {
            "value": None,
            "status": "not_available",
        }

    # Current ratio = current_assets / current_liabilities
    if current_assets is not None and current_liabilities is not None and current_liabilities > 0:
        derived["current_ratio"] = {
            "value": current_assets / current_liabilities,
            "unit": "ratio",
            "calculation": "current_assets / current_liabilities",
            "status": "ok",
        }
    else:
        derived["current_ratio"] = {
            "value": None,
            "status": "not_available",
        }

    # Burn rate and runway (for cash-burning companies only)
    operating_cash_flow = metrics.get("net_cash_used_in_operating_activities", {}).get("value")
    cash = metrics.get("cash_and_cash_equivalents", {}).get("value")

    if operating_cash_flow is not None and operating_cash_flow < 0:
        # Company is cash-burning (negative operating cash flow)
        quarterly_burn = abs(operating_cash_flow)
        monthly_burn = quarterly_burn / 3

        derived["quarterly_burn"] = {
            "value": quarterly_burn,
            "unit": "USD",
            "calculation": "abs(net_cash_used_in_operating_activities)",
            "status": "ok",
        }

        derived["monthly_burn"] = {
            "value": monthly_burn,
            "unit": "USD",
            "calculation": "quarterly_burn / 3",
            "status": "ok",
        }

        # Calculate runway if cash available
        if cash is not None and monthly_burn > 0:
            runway_months = cash / monthly_burn
            derived["cash_runway_months"] = {
                "value": runway_months,
                "unit": "months",
                "calculation": "cash / monthly_burn",
                "status": "ok",
            }
        else:
            derived["cash_runway_months"] = {
                "value": None,
                "status": "not_available",
            }
    else:
        # Company is profitable or cash-flow positive - runway not meaningful
        derived["quarterly_burn"] = {
            "value": 0,
            "unit": "USD",
            "status": "not_applicable",
            "note": "Company has positive or zero operating cash flow",
        }

        derived["monthly_burn"] = {
            "value": 0,
            "unit": "USD",
            "status": "not_applicable",
            "note": "Company has positive or zero operating cash flow",
        }

        derived["cash_runway_months"] = {
            "value": None,
            "status": "not_meaningful",
            "note": "Runway calculation not meaningful for profitable/cash-positive companies",
        }

    return derived


def reconcile_with_targets(
    metrics: dict[str, dict],
    targets: dict[str, float]
) -> dict:
    """Reconcile extracted metrics against known target values.

    Args:
        metrics: Extracted financial metrics
        targets: dict mapping canonical metric names to expected values

    Returns:
        dict with:
            status: "matched", "reconciled_with_differences", or "failed"
            differences: list of dicts describing discrepancies
            matched_count: number of exact matches
            total_targets: total number of target metrics

    Example:
        >>> targets = {"cash_and_cash_equivalents": 34413110}
        >>> reconciliation = reconcile_with_targets(metrics, targets)
        >>> reconciliation["status"]
        "matched"
    """
    differences = []
    matched_count = 0
    total_targets = len(targets)

    for metric_name, expected_value in targets.items():
        actual_metric = metrics.get(metric_name, {})
        actual_value = actual_metric.get("value")

        if actual_value == expected_value:
            matched_count += 1
        elif actual_value is not None:
            # Value differs
            differences.append({
                "metric": metric_name,
                "expected": expected_value,
                "actual": actual_value,
                "difference": actual_value - expected_value,
                "concept_used": actual_metric.get("concept"),
                "period_end": actual_metric.get("period_end"),
            })
        else:
            # Value not available
            differences.append({
                "metric": metric_name,
                "expected": expected_value,
                "actual": None,
                "status": "not_available",
            })

    if matched_count == total_targets and len(differences) == 0:
        status = "matched"
    elif matched_count > 0 or (len(differences) > 0 and any(d.get("status") != "not_available" for d in differences)):
        status = "reconciled_with_differences"
    else:
        status = "failed"

    return {
        "status": status,
        "differences": differences,
        "matched_count": matched_count,
        "total_targets": total_targets,
    }
