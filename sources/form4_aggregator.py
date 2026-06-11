"""Form 4 transaction aggregation and normalization.

Aggregates Form 4 insider transactions across multiple filings and produces
canonical statistics for open-market purchases/sales, distinct buyers/sellers,
and transaction code classification.

This module distinguishes:
- Open-market transactions (P = purchase, S = sale)
- Non-open-market transactions (A = grant, M = option exercise, F = tax withholding, etc.)

Transaction codes:
- P: Open-market purchase
- S: Open-market sale
- A: Grant/award (NOT open-market)
- M: Option exercise (NOT open-market)
- F: Tax withholding/disposition (NOT open-market)
- G: Gift (NOT open-market)
- J: Other (NOT open-market)
- D: Disposition to issuer
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sources.sec_form4_details import (
    Form4FilingDetails,
    Form4Owner,
    Form4Transaction,
)


@dataclass
class CanonicalTransaction:
    """Canonical representation of a Form 4 transaction for aggregation.

    Attributes:
        ticker: Stock ticker
        issuer_cik: Issuer CIK (10-digit padded)
        accession_number: SEC accession number
        filing_date: Filing date (YYYY-MM-DD)
        period_of_report: Period/date of report (YYYY-MM-DD)
        reporting_owner_name: Name of reporting owner
        reporting_owner_cik: Reporting owner CIK (if available)
        officer_title: Officer title (if officer)
        director: Whether owner is a director
        ten_percent_owner: Whether owner is 10% beneficial owner
        security_title: Title of security (e.g., "Common Stock")
        transaction_date: Transaction date (YYYY-MM-DD)
        transaction_code: SEC transaction code (P, S, M, A, F, G, D, J)
        transaction_code_description: Human-readable description
        transaction_classification: Classification (OPEN_MARKET_PURCHASE, etc.)
        is_open_market_purchase: True if code=P
        is_open_market_sale: True if code=S
        is_derivative: False for non-derivative transactions
        shares: Number of shares transacted
        price_per_share: Price per share (may be None for grants)
        transaction_value: Calculated transaction value (shares × price)
        shares_owned_following: Shares owned after transaction
        ownership_nature_direct_or_indirect: 'D' for direct, 'I' for indirect
        ownership_nature_explanation: Nature of indirect ownership (if indirect)
    """

    ticker: str
    issuer_cik: str
    accession_number: str
    filing_date: str
    period_of_report: str
    reporting_owner_name: str
    reporting_owner_cik: str | None
    officer_title: str | None
    director: bool
    ten_percent_owner: bool
    security_title: str
    transaction_date: str
    transaction_code: str
    transaction_code_description: str
    transaction_classification: str
    is_open_market_purchase: bool
    is_open_market_sale: bool
    is_derivative: bool
    shares: float
    price_per_share: float | None
    transaction_value: float | None
    shares_owned_following: float | None
    ownership_nature_direct_or_indirect: str
    ownership_nature_explanation: str | None


@dataclass
class TopTrader:
    """Top buyer or seller summary.

    Attributes:
        name: Reporting owner name
        cik: Reporting owner CIK (if available)
        title: Officer title (if officer)
        is_director: Whether owner is a director
        is_officer: Whether owner is an officer
        transaction_count: Number of transactions
        total_value: Total transaction value
        total_shares: Total shares transacted
        latest_transaction_date: Most recent transaction date
    """

    name: str
    cik: str | None
    title: str | None
    is_director: bool
    is_officer: bool
    transaction_count: int
    total_value: float
    total_shares: float
    latest_transaction_date: str


@dataclass
class Form4AggregationSummary:
    """Aggregated statistics from Form 4 insider transactions.

    Attributes:
        form4_filings_found: Total Form 4 filings found
        form4_filings_parsed: Successfully parsed filings
        form4_filings_failed: Failed parse attempts
        transactions_extracted: Total transactions extracted (all codes)
        open_market_purchases: Count of open-market purchases (code=P)
        open_market_sales: Count of open-market sales (code=S)
        open_market_purchase_value: Total value of open-market purchases
        open_market_sale_value: Total value of open-market sales
        net_open_market_value: Net open-market value (purchases - sales)
        distinct_buyers: Number of distinct buyers (code=P)
        distinct_sellers: Number of distinct sellers (code=S)
        latest_open_market_purchase_date: Most recent purchase date (code=P)
        latest_open_market_sale_date: Most recent sale date (code=S)
        transaction_code_counts: Counts by transaction code {code: count}
    """

    form4_filings_found: int
    form4_filings_parsed: int
    form4_filings_failed: int
    transactions_extracted: int
    open_market_purchases: int
    open_market_sales: int
    open_market_purchase_value: float
    open_market_sale_value: float
    net_open_market_value: float
    distinct_buyers: int
    distinct_sellers: int
    latest_open_market_purchase_date: str | None
    latest_open_market_sale_date: str | None
    transaction_code_counts: dict[str, int]


# Transaction code descriptions
TRANSACTION_CODE_DESCRIPTIONS = {
    "P": "Open-market purchase",
    "S": "Open-market sale",
    "M": "Option exercise",
    "A": "Grant or award",
    "F": "Tax withholding or payment in securities",
    "G": "Gift",
    "D": "Disposition to the issuer",
    "J": "Other",
}


def _classify_transaction_for_aggregation(code: str) -> tuple[bool, bool]:
    """Classify a transaction as open-market purchase or sale.

    Args:
        code: SEC transaction code (P, S, M, A, F, G, D, J)

    Returns:
        (is_open_market_purchase, is_open_market_sale)
    """
    code_upper = code.upper()
    return (code_upper == "P", code_upper == "S")


def _normalize_transaction(
    txn: Form4Transaction,
    filing: Form4FilingDetails,
    owner: Form4Owner,
    ticker: str,
) -> CanonicalTransaction:
    """Normalize a Form 4 transaction to canonical format.

    Args:
        txn: Form4Transaction from parsed filing
        filing: Form4FilingDetails from parsed filing
        owner: Form4Owner from parsed filing
        ticker: Stock ticker

    Returns:
        CanonicalTransaction with all required fields
    """
    is_open_market_purchase, is_open_market_sale = _classify_transaction_for_aggregation(
        txn.transaction_code
    )

    return CanonicalTransaction(
        ticker=ticker,
        issuer_cik=filing.issuer_cik,
        accession_number=filing.accession_number,
        filing_date=filing.filing_date,
        period_of_report=filing.period_of_report,
        reporting_owner_name=owner.name,
        reporting_owner_cik=owner.cik,
        officer_title=owner.officer_title,
        director=owner.is_director,
        ten_percent_owner=owner.is_ten_percent_owner,
        security_title=txn.security_title,
        transaction_date=txn.transaction_date,
        transaction_code=txn.transaction_code,
        transaction_code_description=TRANSACTION_CODE_DESCRIPTIONS.get(
            txn.transaction_code.upper(), "Unknown transaction code"
        ),
        transaction_classification=txn.classification,
        is_open_market_purchase=is_open_market_purchase,
        is_open_market_sale=is_open_market_sale,
        is_derivative=False,  # Non-derivative transactions only
        shares=txn.shares,
        price_per_share=txn.price_per_share,
        transaction_value=txn.transaction_value,
        shares_owned_following=txn.shares_owned_following,
        ownership_nature_direct_or_indirect=txn.direct_or_indirect,
        ownership_nature_explanation=txn.ownership_nature,
    )


def aggregate_form4_transactions(
    filings: list[Form4FilingDetails],
    ticker: str,
) -> dict[str, Any]:
    """Aggregate Form 4 transactions across multiple filings.

    Args:
        filings: List of parsed Form4FilingDetails
        ticker: Stock ticker

    Returns:
        Dictionary with:
        - summary: Form4AggregationSummary
        - transactions: List[CanonicalTransaction]
        - top_buyers_by_value: List[TopTrader]
        - top_sellers_by_value: List[TopTrader]
        - filing_parse_results: List of parse status per filing
    """
    # Normalize all transactions
    canonical_transactions: list[CanonicalTransaction] = []
    parse_results = []

    for filing in filings:
        parse_results.append(
            {
                "accession_number": filing.accession_number,
                "filing_date": filing.filing_date,
                "parse_status": filing.parse_status,
                "error_type": filing.error_type,
                "error_message": filing.error_message,
                "transactions_extracted": len(filing.transactions),
                "owners_extracted": len(filing.owners),
            }
        )

        if filing.parse_status != "success":
            continue

        # Match each transaction to its owner
        # Note: Form 4 XML structure has one reportingOwner per filing,
        # but we'll handle multiple owners gracefully
        for owner in filing.owners:
            for txn in filing.transactions:
                canonical_txn = _normalize_transaction(txn, filing, owner, ticker)
                canonical_transactions.append(canonical_txn)

    # Calculate aggregation metrics
    open_market_purchases = [t for t in canonical_transactions if t.is_open_market_purchase]
    open_market_sales = [t for t in canonical_transactions if t.is_open_market_sale]

    # Calculate total values (only for transactions with non-None values)
    purchase_value = sum(
        t.transaction_value for t in open_market_purchases if t.transaction_value is not None
    )
    sale_value = sum(
        t.transaction_value for t in open_market_sales if t.transaction_value is not None
    )

    # Distinct buyers/sellers
    distinct_buyers = len(set(t.reporting_owner_name for t in open_market_purchases))
    distinct_sellers = len(set(t.reporting_owner_name for t in open_market_sales))

    # Latest transaction dates
    latest_purchase_date = None
    if open_market_purchases:
        latest_purchase_date = max(t.transaction_date for t in open_market_purchases)

    latest_sale_date = None
    if open_market_sales:
        latest_sale_date = max(t.transaction_date for t in open_market_sales)

    # Transaction code counts
    code_counts: dict[str, int] = {}
    for t in canonical_transactions:
        code = t.transaction_code.upper()
        code_counts[code] = code_counts.get(code, 0) + 1

    # Build summary
    summary = Form4AggregationSummary(
        form4_filings_found=len(filings),
        form4_filings_parsed=sum(1 for r in parse_results if r["parse_status"] == "success"),
        form4_filings_failed=sum(1 for r in parse_results if r["parse_status"] == "failed"),
        transactions_extracted=len(canonical_transactions),
        open_market_purchases=len(open_market_purchases),
        open_market_sales=len(open_market_sales),
        open_market_purchase_value=purchase_value,
        open_market_sale_value=sale_value,
        net_open_market_value=purchase_value - sale_value,
        distinct_buyers=distinct_buyers,
        distinct_sellers=distinct_sellers,
        latest_open_market_purchase_date=latest_purchase_date,
        latest_open_market_sale_date=latest_sale_date,
        transaction_code_counts=code_counts,
    )

    # Calculate top buyers/sellers by value
    top_buyers = _calculate_top_traders(open_market_purchases)
    top_sellers = _calculate_top_traders(open_market_sales)

    return {
        "summary": asdict(summary),
        "transactions": [asdict(t) for t in canonical_transactions],
        "top_buyers_by_value": [asdict(t) for t in top_buyers],
        "top_sellers_by_value": [asdict(t) for t in top_sellers],
        "filing_parse_results": parse_results,
    }


def _calculate_top_traders(transactions: list[CanonicalTransaction]) -> list[TopTrader]:
    """Calculate top traders (buyers or sellers) by total transaction value.

    Args:
        transactions: List of canonical transactions (all purchases or all sales)

    Returns:
        List of TopTrader sorted by total value descending
    """
    # Group by owner name
    trader_map: dict[str, dict[str, Any]] = {}

    for t in transactions:
        if t.reporting_owner_name not in trader_map:
            trader_map[t.reporting_owner_name] = {
                "name": t.reporting_owner_name,
                "cik": t.reporting_owner_cik,
                "title": t.officer_title,
                "is_director": t.director,
                "is_officer": t.officer_title is not None,
                "transaction_count": 0,
                "total_value": 0.0,
                "total_shares": 0.0,
                "latest_transaction_date": t.transaction_date,
            }

        trader = trader_map[t.reporting_owner_name]
        trader["transaction_count"] += 1
        trader["total_shares"] += t.shares

        if t.transaction_value is not None:
            trader["total_value"] += t.transaction_value

        # Update latest transaction date
        if t.transaction_date > trader["latest_transaction_date"]:
            trader["latest_transaction_date"] = t.transaction_date

    # Convert to TopTrader objects and sort by total value descending
    top_traders = [
        TopTrader(
            name=t["name"],
            cik=t["cik"],
            title=t["title"],
            is_director=t["is_director"],
            is_officer=t["is_officer"],
            transaction_count=t["transaction_count"],
            total_value=t["total_value"],
            total_shares=t["total_shares"],
            latest_transaction_date=t["latest_transaction_date"],
        )
        for t in trader_map.values()
    ]

    top_traders.sort(key=lambda x: x.total_value, reverse=True)

    return top_traders
