"""Schedule 13D/G (Beneficial Ownership) parser.

Schedule 13D and 13G report beneficial ownership of more than 5% of a company's shares.

Key distinctions:
- 13D = Active investment (intent to influence control)
- 13G = Passive investment (no intent to influence)
- /A suffix = Amendment to previous filing

Form variants:
- SC 13D, SC 13D/A (active)
- SC 13G, SC 13G/A (passive)
- 13D, 13D/A (active)
- 13G, 13G/A (passive)

Extraction targets:
- Filer identity (reporting person/entity)
- Beneficial owner (if different from filer)
- Shares beneficially owned
- Percent of class
- Voting power (sole, shared)
- Dispositive power (sole, shared)
- Type of reporting person (individual, partnership, corporation, etc.)
- Purpose of transaction (for 13D only)
- Event date (for amendments)

Parse failures are preserved with evidence provenance for debugging.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Callable

from sources.sec_common import sec_fetch
from sources.sec_submissions import SecSubmissionFiling


@dataclass
class Ownership13DG:
    """Represents a Schedule 13D or 13G filing.

    Attributes:
        ticker: Stock ticker symbol
        issuer_cik: Issuer CIK (10-digit padded)
        accession_number: SEC accession number
        filing_date: Filing date (YYYY-MM-DD)
        form: Form type (SC 13D, SC 13G, SC 13D/A, SC 13G/A, etc.)
        filer_name: Name of filer (reporting person)
        filer_cik: Filer CIK (if available)
        beneficial_owner_name: Name of beneficial owner (if different from filer)
        ownership_percent: Percent of class owned
        shares_beneficially_owned: Number of shares owned
        sole_voting_power: Shares with sole voting power
        shared_voting_power: Shares with shared voting power
        sole_dispositive_power: Shares with sole dispositive power
        shared_dispositive_power: Shares with shared dispositive power
        type_of_reporting_person: Type (individual, partnership, corporation, etc.)
        active_or_passive_classification: "active" (13D) or "passive" (13G)
        amendment_number: Amendment number (for /A filings)
        event_date: Event date (for amendments)
        purpose_of_transaction: Purpose (for 13D only)
        parse_status: success, partial, or failed
        error_message: Error message if parse_status=failed
    """

    ticker: str
    issuer_cik: str
    accession_number: str
    filing_date: str
    form: str
    filer_name: str | None
    filer_cik: str | None
    beneficial_owner_name: str | None
    ownership_percent: str | None
    shares_beneficially_owned: str | None
    sole_voting_power: str | None
    shared_voting_power: str | None
    sole_dispositive_power: str | None
    shared_dispositive_power: str | None
    type_of_reporting_person: str | None
    active_or_passive_classification: str  # "active" or "passive"
    amendment_number: str | None
    event_date: str | None
    purpose_of_transaction: str | None
    parse_status: str  # success, partial, failed
    error_message: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class OwnershipSummary:
    """Summary statistics for Schedule 13D/G filings.

    Attributes:
        ticker: Stock ticker symbol
        issuer_cik: Issuer CIK (10-digit padded)
        total_filings: Total 13D/G filings found
        active_13d_count: Count of active (13D) filings
        passive_13g_count: Count of passive (13G) filings
        amendment_count: Count of amendment filings
        successful_parses: Number of successful parses
        failed_parses: Number of failed parses
        partial_parses: Number of partial parses
        earliest_filing_date: Earliest filing date
        latest_filing_date: Latest filing date
        distinct_filers: Count of distinct filers
        report_only: Safety flag (always True)
        alert_enabled: Safety flag (always False)
        openinsider_required: Safety flag (always False)
        generated_at: ISO timestamp of report generation
    """

    ticker: str
    issuer_cik: str
    total_filings: int
    active_13d_count: int
    passive_13g_count: int
    amendment_count: int
    successful_parses: int
    failed_parses: int
    partial_parses: int
    earliest_filing_date: str | None
    latest_filing_date: str | None
    distinct_filers: int
    report_only: bool
    alert_enabled: bool
    openinsider_required: bool
    generated_at: str

    @staticmethod
    def from_filings(filings: list[Ownership13DG]) -> OwnershipSummary:
        """Generate summary from list of 13D/G filings."""
        from sources.sec_common import utcnow_iso

        if not filings:
            return OwnershipSummary(
                ticker="UNKNOWN",
                issuer_cik="",
                total_filings=0,
                active_13d_count=0,
                passive_13g_count=0,
                amendment_count=0,
                successful_parses=0,
                failed_parses=0,
                partial_parses=0,
                earliest_filing_date=None,
                latest_filing_date=None,
                distinct_filers=0,
                report_only=True,
                alert_enabled=False,
                openinsider_required=False,
                generated_at=utcnow_iso(),
            )

        ticker = filings[0].ticker
        issuer_cik = filings[0].issuer_cik

        active_count = sum(
            1 for f in filings if f.active_or_passive_classification == "active"
        )
        passive_count = sum(
            1 for f in filings if f.active_or_passive_classification == "passive"
        )
        amendment_count = sum(1 for f in filings if "/A" in f.form)

        successful = sum(1 for f in filings if f.parse_status == "success")
        failed = sum(1 for f in filings if f.parse_status == "failed")
        partial = sum(1 for f in filings if f.parse_status == "partial")

        filing_dates = sorted([f.filing_date for f in filings if f.filing_date])
        earliest = filing_dates[0] if filing_dates else None
        latest = filing_dates[-1] if filing_dates else None

        filers = set()
        for f in filings:
            if f.filer_name:
                filers.add(f.filer_name)

        return OwnershipSummary(
            ticker=ticker,
            issuer_cik=issuer_cik,
            total_filings=len(filings),
            active_13d_count=active_count,
            passive_13g_count=passive_count,
            amendment_count=amendment_count,
            successful_parses=successful,
            failed_parses=failed,
            partial_parses=partial,
            earliest_filing_date=earliest,
            latest_filing_date=latest,
            distinct_filers=len(filers),
            report_only=True,
            alert_enabled=False,
            openinsider_required=False,
            generated_at=utcnow_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def parse_13dg_filing(
    filing: SecSubmissionFiling,
    fetch_func: Callable[[str], dict[str, Any]] | None = None,
) -> Ownership13DG:
    """Parse a single Schedule 13D or 13G filing.

    Args:
        filing: SecSubmissionFiling object for 13D/G
        fetch_func: Optional fetch function (for testing, defaults to sec_fetch)

    Returns:
        Ownership13DG object with parsed data
    """
    if fetch_func is None:
        fetch_func = sec_fetch

    # Classify as active (13D) or passive (13G)
    form_upper = filing.form.upper()
    if "13D" in form_upper:
        classification = "active"
    elif "13G" in form_upper:
        classification = "passive"
    else:
        classification = "unknown"

    # Determine if amendment
    is_amendment = "/A" in filing.form
    amendment_number = None
    if is_amendment:
        # Try to extract amendment number from form
        match = re.search(r"/A(\d+)?", filing.form)
        if match and match.group(1):
            amendment_number = match.group(1)
        else:
            amendment_number = "1"  # Default to 1 if not specified

    # Fetch the primary document
    url = filing.primary_document_url
    result = fetch_func(url)

    if not result.get("ok"):
        return Ownership13DG(
            ticker="UNKNOWN",
            issuer_cik=filing.cik,
            accession_number=filing.accession_number,
            filing_date=filing.filing_date,
            form=filing.form,
            filer_name=None,
            filer_cik=None,
            beneficial_owner_name=None,
            ownership_percent=None,
            shares_beneficially_owned=None,
            sole_voting_power=None,
            shared_voting_power=None,
            sole_dispositive_power=None,
            shared_dispositive_power=None,
            type_of_reporting_person=None,
            active_or_passive_classification=classification,
            amendment_number=amendment_number,
            event_date=None,
            purpose_of_transaction=None,
            parse_status="failed",
            error_message=result.get("error", "Unknown fetch error"),
        )

    body = result.get("body", "")

    # Extract fields using regex patterns
    ticker = _extract_ticker_13dg(body)
    filer_name = _extract_filer_name(body)
    filer_cik = _extract_filer_cik(body)
    beneficial_owner_name = _extract_beneficial_owner_name(body)
    ownership_percent = _extract_ownership_percent(body)
    shares_beneficially_owned = _extract_shares_beneficially_owned(body)
    sole_voting_power = _extract_sole_voting_power(body)
    shared_voting_power = _extract_shared_voting_power(body)
    sole_dispositive_power = _extract_sole_dispositive_power(body)
    shared_dispositive_power = _extract_shared_dispositive_power(body)
    type_of_reporting_person = _extract_type_of_reporting_person(body)
    event_date = _extract_event_date(body)
    purpose_of_transaction = _extract_purpose_of_transaction(body)

    # Determine parse status
    # Success requires filer_name and at least one ownership metric
    if filer_name and (ownership_percent or shares_beneficially_owned):
        parse_status = "success"
    elif ticker or filer_name:
        parse_status = "partial"
    else:
        parse_status = "partial"

    return Ownership13DG(
        ticker=ticker or "UNKNOWN",
        issuer_cik=filing.cik,
        accession_number=filing.accession_number,
        filing_date=filing.filing_date,
        form=filing.form,
        filer_name=filer_name,
        filer_cik=filer_cik,
        beneficial_owner_name=beneficial_owner_name,
        ownership_percent=ownership_percent,
        shares_beneficially_owned=shares_beneficially_owned,
        sole_voting_power=sole_voting_power,
        shared_voting_power=shared_voting_power,
        sole_dispositive_power=sole_dispositive_power,
        shared_dispositive_power=shared_dispositive_power,
        type_of_reporting_person=type_of_reporting_person,
        active_or_passive_classification=classification,
        amendment_number=amendment_number,
        event_date=event_date,
        purpose_of_transaction=purpose_of_transaction,
        parse_status=parse_status,
        error_message=None,
    )


def _extract_ticker_13dg(body: str) -> str | None:
    """Extract ticker symbol from 13D/G text."""
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


def _extract_filer_name(body: str) -> str | None:
    """Extract filer (reporting person) name."""
    patterns = [
        r"Name of Reporting Person[:\s]+([A-Za-z\s\.,&]+)",
        r"Reporting Person[:\s]+([A-Za-z\s\.,&]+)",
        r"Filer[:\s]+([A-Za-z\s\.,&]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if "\n" in name:
                name = name.split("\n")[0].strip()
            return name
    return None


def _extract_filer_cik(body: str) -> str | None:
    """Extract filer CIK."""
    patterns = [
        r"Filer CIK[:\s]+([0-9]{1,10})",
        r"CIK[:\s]+([0-9]{1,10})",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).zfill(10)
    return None


def _extract_beneficial_owner_name(body: str) -> str | None:
    """Extract beneficial owner name (if different from filer)."""
    patterns = [
        r"Beneficial Owner[:\s]+([A-Za-z\s\.,&]+)",
        r"Name of Beneficial Owner[:\s]+([A-Za-z\s\.,&]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if "\n" in name:
                name = name.split("\n")[0].strip()
            return name
    return None


def _extract_ownership_percent(body: str) -> str | None:
    """Extract percent of class owned."""
    patterns = [
        r"Percent of Class[:\s]+([0-9\.]+%)",
        r"Percentage[:\s]+([0-9\.]+%)",
        r"([0-9\.]+)%\s*of\s*class",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_shares_beneficially_owned(body: str) -> str | None:
    """Extract number of shares beneficially owned."""
    patterns = [
        r"Shares Beneficially Owned[:\s]+([0-9,]+)",
        r"Beneficial Ownership[:\s]+([0-9,]+)\s*shares?",
        r"Number of Shares[:\s]+([0-9,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_sole_voting_power(body: str) -> str | None:
    """Extract sole voting power."""
    patterns = [
        r"Sole Voting Power[:\s]+([0-9,]+)",
        r"Sole Power to Vote[:\s]+([0-9,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_shared_voting_power(body: str) -> str | None:
    """Extract shared voting power."""
    patterns = [
        r"Shared Voting Power[:\s]+([0-9,]+)",
        r"Shared Power to Vote[:\s]+([0-9,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_sole_dispositive_power(body: str) -> str | None:
    """Extract sole dispositive power."""
    patterns = [
        r"Sole Dispositive Power[:\s]+([0-9,]+)",
        r"Sole Power to Dispose[:\s]+([0-9,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_shared_dispositive_power(body: str) -> str | None:
    """Extract shared dispositive power."""
    patterns = [
        r"Shared Dispositive Power[:\s]+([0-9,]+)",
        r"Shared Power to Dispose[:\s]+([0-9,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_type_of_reporting_person(body: str) -> str | None:
    """Extract type of reporting person."""
    patterns = [
        r"Type of Reporting Person[:\s]+([A-Z]{2,3})",
        r"Reporting Person Type[:\s]+([A-Za-z]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_event_date(body: str) -> str | None:
    """Extract event date (for amendments)."""
    patterns = [
        r"Event Date[:\s]+([0-9/\-]+)",
        r"Date of Event[:\s]+([0-9/\-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_purpose_of_transaction(body: str) -> str | None:
    """Extract purpose of transaction (13D only)."""
    patterns = [
        r"Purpose of Transaction[:\s]+([A-Za-z\s,\.]+)",
        r"Purpose[:\s]+([A-Za-z\s,\.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            purpose = match.group(1).strip()
            # Limit to first line or 200 chars
            if "\n" in purpose:
                purpose = purpose.split("\n")[0].strip()
            if len(purpose) > 200:
                purpose = purpose[:200].strip()
            return purpose
    return None
