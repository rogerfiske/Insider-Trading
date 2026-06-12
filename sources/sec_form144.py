"""Form 144 (Notice of Proposed Sale) parser.

Form 144 is a NOTICE of PROPOSED SALE, not an actual sale.
It indicates intent to sell restricted securities within 90 days.

Key distinction:
- Form 144 = Notice of INTENT to sell (sale_status = "proposed")
- Actual sales are reported in Form 4 with transaction code "S"

Extraction targets:
- Reporting person (seller) name
- Relationship to issuer (officer, director, 10% owner)
- Securities to be sold (quantity/description)
- Approximate date of sale
- Broker name (if applicable)
- Exchange (if applicable)
- Aggregate market value (if available)

Parse failures are preserved with evidence provenance for debugging.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Callable

from sources.sec_common import sec_fetch
from sources.sec_submissions import SecSubmissionFiling


@dataclass
class Form144Filing:
    """Represents a Form 144 filing (notice of proposed sale).

    Attributes:
        ticker: Stock ticker symbol
        issuer_cik: Issuer CIK (10-digit padded)
        accession_number: SEC accession number
        filing_date: Filing date (YYYY-MM-DD)
        seller_name: Name of person proposing to sell
        seller_relationship: Relationship to issuer (officer, director, etc.)
        securities_to_be_sold: Description/quantity of securities
        aggregate_market_value: Total market value (if available)
        approximate_date_of_sale: Approximate sale date
        broker_name: Broker name (if applicable)
        exchange: Exchange symbol (if applicable)
        notice_date: Date of notice filing
        sale_status: Always "proposed" (Form 144 is intent, not actual sale)
        parse_status: success, partial, or failed
        error_message: Error message if parse_status=failed
    """

    ticker: str
    issuer_cik: str
    accession_number: str
    filing_date: str
    seller_name: str | None
    seller_relationship: str | None
    securities_to_be_sold: str | None
    aggregate_market_value: str | None
    approximate_date_of_sale: str | None
    broker_name: str | None
    exchange: str | None
    notice_date: str
    sale_status: str  # Always "proposed"
    parse_status: str  # success, partial, failed
    error_message: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class Form144Summary:
    """Summary statistics for Form 144 filings.

    Attributes:
        ticker: Stock ticker symbol
        issuer_cik: Issuer CIK (10-digit padded)
        total_filings: Total Form 144 filings found
        successful_parses: Number of successful parses
        failed_parses: Number of failed parses
        partial_parses: Number of partial parses (some fields missing)
        earliest_filing_date: Earliest filing date
        latest_filing_date: Latest filing date
        distinct_sellers: Count of distinct sellers
        report_only: Safety flag (always True)
        alert_enabled: Safety flag (always False)
        openinsider_required: Safety flag (always False)
        generated_at: ISO timestamp of report generation
    """

    ticker: str
    issuer_cik: str
    total_filings: int
    successful_parses: int
    failed_parses: int
    partial_parses: int
    earliest_filing_date: str | None
    latest_filing_date: str | None
    distinct_sellers: int
    report_only: bool
    alert_enabled: bool
    openinsider_required: bool
    generated_at: str

    @staticmethod
    def from_filings(filings: list[Form144Filing]) -> Form144Summary:
        """Generate summary from list of Form 144 filings."""
        from sources.sec_common import utcnow_iso

        if not filings:
            return Form144Summary(
                ticker="UNKNOWN",
                issuer_cik="",
                total_filings=0,
                successful_parses=0,
                failed_parses=0,
                partial_parses=0,
                earliest_filing_date=None,
                latest_filing_date=None,
                distinct_sellers=0,
                report_only=True,
                alert_enabled=False,
                openinsider_required=False,
                generated_at=utcnow_iso(),
            )

        ticker = filings[0].ticker
        issuer_cik = filings[0].issuer_cik

        successful = sum(1 for f in filings if f.parse_status == "success")
        failed = sum(1 for f in filings if f.parse_status == "failed")
        partial = sum(1 for f in filings if f.parse_status == "partial")

        filing_dates = sorted([f.filing_date for f in filings if f.filing_date])
        earliest = filing_dates[0] if filing_dates else None
        latest = filing_dates[-1] if filing_dates else None

        sellers = set()
        for f in filings:
            if f.seller_name:
                sellers.add(f.seller_name)

        return Form144Summary(
            ticker=ticker,
            issuer_cik=issuer_cik,
            total_filings=len(filings),
            successful_parses=successful,
            failed_parses=failed,
            partial_parses=partial,
            earliest_filing_date=earliest,
            latest_filing_date=latest,
            distinct_sellers=len(sellers),
            report_only=True,
            alert_enabled=False,
            openinsider_required=False,
            generated_at=utcnow_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def parse_form144_filing(
    filing: SecSubmissionFiling,
    fetch_func: Callable[[str], dict[str, Any]] | None = None,
) -> Form144Filing:
    """Parse a single Form 144 filing.

    Args:
        filing: SecSubmissionFiling object for Form 144
        fetch_func: Optional fetch function (for testing, defaults to sec_fetch)

    Returns:
        Form144Filing object with parsed data

    Note:
        Form 144 is a NOTICE of PROPOSED SALE, not an actual sale.
        sale_status is always "proposed".
    """
    if fetch_func is None:
        fetch_func = sec_fetch

    # Fetch the primary document
    url = filing.primary_document_url
    result = fetch_func(url)

    if not result.get("ok"):
        return Form144Filing(
            ticker="UNKNOWN",
            issuer_cik=filing.cik,
            accession_number=filing.accession_number,
            filing_date=filing.filing_date,
            seller_name=None,
            seller_relationship=None,
            securities_to_be_sold=None,
            aggregate_market_value=None,
            approximate_date_of_sale=None,
            broker_name=None,
            exchange=None,
            notice_date=filing.filing_date,
            sale_status="proposed",
            parse_status="failed",
            error_message=result.get("error", "Unknown fetch error"),
        )

    body = result.get("body", "")

    # Extract fields using regex patterns
    ticker = _extract_ticker(body)
    seller_name = _extract_seller_name(body)
    seller_relationship = _extract_seller_relationship(body)
    securities_to_be_sold = _extract_securities_to_be_sold(body)
    aggregate_market_value = _extract_aggregate_market_value(body)
    approximate_date_of_sale = _extract_approximate_date_of_sale(body)
    broker_name = _extract_broker_name(body)
    exchange = _extract_exchange(body)

    # Determine parse status
    if ticker and seller_name and securities_to_be_sold:
        parse_status = "success"
    elif ticker or seller_name:
        parse_status = "partial"
    else:
        parse_status = "partial"

    return Form144Filing(
        ticker=ticker or "UNKNOWN",
        issuer_cik=filing.cik,
        accession_number=filing.accession_number,
        filing_date=filing.filing_date,
        seller_name=seller_name,
        seller_relationship=seller_relationship,
        securities_to_be_sold=securities_to_be_sold,
        aggregate_market_value=aggregate_market_value,
        approximate_date_of_sale=approximate_date_of_sale,
        broker_name=broker_name,
        exchange=exchange,
        notice_date=filing.filing_date,
        sale_status="proposed",  # Form 144 is always proposed, never actual sale
        parse_status=parse_status,
        error_message=None,
    )


def _extract_ticker(body: str) -> str | None:
    """Extract ticker symbol from Form 144 text."""
    patterns = [
        r"Ticker[:\s]+([A-Z]{1,5})",
        r"Trading Symbol[:\s]+([A-Z]{1,5})",
        r"Symbol[:\s]+([A-Z]{1,5})",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def _extract_seller_name(body: str) -> str | None:
    """Extract seller (reporting person) name from Form 144 text."""
    patterns = [
        r"Name of Person[:\s]+([A-Za-z\s\.,]+)",
        r"Reporting Person[:\s]+([A-Za-z\s\.,]+)",
        r"Name of Reporting Person[:\s]+([A-Za-z\s\.,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Trim if line break or "Relationship" appears
            if "\n" in name:
                name = name.split("\n")[0].strip()
            return name
    return None


def _extract_seller_relationship(body: str) -> str | None:
    """Extract seller relationship to issuer."""
    patterns = [
        r"Relationship[:\s]+([A-Za-z\s,]+)",
        r"Relationship to Issuer[:\s]+([A-Za-z\s,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            rel = match.group(1).strip()
            if "\n" in rel:
                rel = rel.split("\n")[0].strip()
            return rel
    return None


def _extract_securities_to_be_sold(body: str) -> str | None:
    """Extract securities to be sold."""
    patterns = [
        r"Securities to be Sold[:\s]+([0-9,\s]+shares?)",
        r"Number of Shares[:\s]+([0-9,\s]+)",
        r"Shares to be Sold[:\s]+([0-9,\s]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_aggregate_market_value(body: str) -> str | None:
    """Extract aggregate market value."""
    patterns = [
        r"Aggregate Market Value[:\s]+\$?([0-9,\.]+)",
        r"Market Value[:\s]+\$?([0-9,\.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_approximate_date_of_sale(body: str) -> str | None:
    """Extract approximate date of sale."""
    patterns = [
        r"Approximate Date of Sale[:\s]+([0-9/\-]+)",
        r"Proposed Sale Date[:\s]+([0-9/\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_broker_name(body: str) -> str | None:
    """Extract broker name."""
    patterns = [
        r"Broker[:\s]+([A-Za-z\s\.,&]+)",
        r"Broker Name[:\s]+([A-Za-z\s\.,&]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if "\n" in name:
                name = name.split("\n")[0].strip()
            return name
    return None


def _extract_exchange(body: str) -> str | None:
    """Extract exchange symbol."""
    patterns = [
        r"Exchange[:\s]+([A-Z]{3,6})",
        r"Market[:\s]+([A-Z]{3,6})",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None
