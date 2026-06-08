"""SEC Form 4 XML transaction detail extraction.

Parses individual Form 4 XML documents to extract insider transaction details including
reporting owners, relationships, transaction codes, shares, prices, and ownership changes.

Example:
    details = fetch_and_parse_form4(
        accession_number="0001878313-26-000012",
        cik="0001878313"
    )
    if details.parse_status == "success":
        for txn in details.transactions:
            print(f"{txn.owner_name}: {txn.transaction_code} {txn.shares} shares @ ${txn.price_per_share}")
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from sources.sec_common import sec_fetch, utcnow_iso


@dataclass
class Form4Owner:
    """Represents a Form 4 reporting owner.

    Attributes:
        name: Reporting owner name
        cik: Reporting owner CIK (if available)
        is_director: Whether the owner is a director
        is_officer: Whether the owner is an officer
        is_ten_percent_owner: Whether the owner is a 10% beneficial owner
        is_other: Whether the relationship is classified as "other"
        officer_title: Officer title if applicable (CEO, CFO, etc.)
    """

    name: str
    cik: str | None = None
    is_director: bool = False
    is_officer: bool = False
    is_ten_percent_owner: bool = False
    is_other: bool = False
    officer_title: str | None = None


@dataclass
class Form4Transaction:
    """Represents a parsed SEC Form 4 non-derivative transaction.

    Attributes:
        transaction_date: Date of transaction (YYYY-MM-DD)
        transaction_code: SEC transaction code (P, S, M, A, F, etc.)
        transaction_acquired_disposed: 'A' for acquired, 'D' for disposed
        security_title: Title of security (e.g., "Common Stock")
        shares: Number of shares transacted
        price_per_share: Price per share (may be None for grants)
        transaction_value: Calculated transaction value (shares × price)
        shares_owned_following: Shares owned after transaction
        direct_or_indirect: 'D' for direct, 'I' for indirect
        ownership_nature: Nature of indirect ownership (if indirect)
        classification: Classified transaction type
    """

    transaction_date: str
    transaction_code: str
    transaction_acquired_disposed: str  # A = acquired, D = disposed
    security_title: str
    shares: float
    price_per_share: float | None = None
    transaction_value: float | None = None
    shares_owned_following: float | None = None
    direct_or_indirect: str = "D"
    ownership_nature: str | None = None
    classification: str = "OTHER_OR_UNCLASSIFIED"


@dataclass
class Form4FilingDetails:
    """Represents parsed details from a single Form 4 filing.

    Attributes:
        issuer_cik: Issuer CIK (10-digit padded)
        issuer_name: Issuer company name
        ticker: Stock ticker (if available)
        accession_number: SEC accession number
        filing_date: Filing date
        period_of_report: Period/date of report
        source_url: SEC EDGAR source URL
        owners: List of reporting owners
        transactions: List of non-derivative transactions
        parse_status: "success", "partial", or "failed"
        error_type: Error category if parsing failed
        error_message: Human-readable error description
        retrieved_at: ISO 8601 UTC timestamp
    """

    issuer_cik: str
    issuer_name: str
    ticker: str | None
    accession_number: str
    filing_date: str
    period_of_report: str
    source_url: str
    owners: list[Form4Owner] = field(default_factory=list)
    transactions: list[Form4Transaction] = field(default_factory=list)
    parse_status: str = "success"  # success, partial, failed
    error_type: str | None = None
    error_message: str | None = None
    retrieved_at: str = ""

    def __post_init__(self) -> None:
        if not self.retrieved_at:
            self.retrieved_at = utcnow_iso()


# Transaction code mapping for classification
TRANSACTION_CODE_MAP = {
    "P": "OPEN_MARKET_PURCHASE",
    "S": "OPEN_MARKET_SALE",
    "M": "OPTION_EXERCISE",
    "A": "GRANT_AWARD",
    "F": "TAX_WITHHOLDING_OR_DISPOSITION",
    "G": "GIFT",
    "D": "DISPOSITION_TO_ISSUER",
}


def classify_transaction(
    code: str, acquired_disposed: str
) -> str:
    """Classify a Form 4 transaction based on code and acquired/disposed flag.

    Args:
        code: SEC transaction code (P, S, M, A, F, G, D, etc.)
        acquired_disposed: 'A' for acquired, 'D' for disposed

    Returns:
        Classification string (OPEN_MARKET_PURCHASE, OPEN_MARKET_SALE, etc.)
    """
    classification = TRANSACTION_CODE_MAP.get(code.upper(), "OTHER_OR_UNCLASSIFIED")

    # Refine classification based on acquired/disposed
    if classification == "OPTION_EXERCISE" and acquired_disposed == "D":
        # M + D = option exercise with disposition (likely sale)
        return "OPTION_EXERCISE_WITH_SALE"

    return classification


def _safe_text(element: ET.Element | None, tag: str, default: str = "") -> str:
    """Safely extract text from an XML element.

    Args:
        element: Parent XML element
        tag: Child tag name to find
        default: Default value if not found

    Returns:
        Text content or default
    """
    if element is None:
        return default
    child = element.find(tag)
    if child is None:
        return default

    # Check if there's a <value> child (common in Form 4 XML)
    value_elem = child.find("value")
    if value_elem is not None and value_elem.text:
        return value_elem.text.strip()

    # Otherwise use direct text
    return child.text.strip() if child.text else default


def _safe_float(element: ET.Element | None, tag: str) -> float | None:
    """Safely extract float from an XML element.

    Args:
        element: Parent XML element
        tag: Child tag name to find

    Returns:
        Float value or None if not found/invalid
    """
    text = _safe_text(element, tag)
    if not text:
        return None
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def _safe_bool(element: ET.Element | None, tag: str) -> bool:
    """Safely extract boolean from an XML element.

    Args:
        element: Parent XML element
        tag: Child tag name to find

    Returns:
        True if element exists and has text "1", False otherwise
    """
    text = _safe_text(element, tag)
    return text == "1"


def _parse_owner(reporting_owner_elem: ET.Element) -> Form4Owner:
    """Parse a reportingOwner XML element.

    Args:
        reporting_owner_elem: reportingOwner XML element

    Returns:
        Form4Owner dataclass
    """
    owner_id = reporting_owner_elem.find("reportingOwnerId")
    owner_name = _safe_text(owner_id, "rptOwnerName")
    owner_cik = _safe_text(owner_id, "rptOwnerCik")

    relationship = reporting_owner_elem.find("reportingOwnerRelationship")
    is_director = _safe_bool(relationship, "isDirector")
    is_officer = _safe_bool(relationship, "isOfficer")
    is_ten_percent_owner = _safe_bool(relationship, "isTenPercentOwner")
    is_other = _safe_bool(relationship, "isOther")
    officer_title = _safe_text(relationship, "officerTitle")

    return Form4Owner(
        name=owner_name,
        cik=owner_cik if owner_cik else None,
        is_director=is_director,
        is_officer=is_officer,
        is_ten_percent_owner=is_ten_percent_owner,
        is_other=is_other,
        officer_title=officer_title if officer_title else None,
    )


def _parse_non_derivative_transaction(txn_elem: ET.Element) -> Form4Transaction | None:
    """Parse a nonDerivativeTransaction XML element.

    Args:
        txn_elem: nonDerivativeTransaction XML element

    Returns:
        Form4Transaction dataclass or None if parsing fails
    """
    security_title = _safe_text(txn_elem, "securityTitle")
    if not security_title:
        return None

    transaction_date = _safe_text(txn_elem, "transactionDate")
    if not transaction_date:
        return None

    transaction_coding = txn_elem.find("transactionCoding")
    transaction_code = _safe_text(transaction_coding, "transactionCode")
    if not transaction_code:
        return None

    transaction_amounts = txn_elem.find("transactionAmounts")
    if transaction_amounts is None:
        return None

    shares = _safe_float(transaction_amounts, "transactionShares")
    if shares is None:
        return None

    price_per_share = _safe_float(transaction_amounts, "transactionPricePerShare")
    acquired_disposed = _safe_text(transaction_amounts, "transactionAcquiredDisposedCode")

    # Calculate transaction value
    transaction_value = None
    if price_per_share is not None and shares is not None:
        transaction_value = shares * price_per_share

    # Post-transaction ownership
    post_txn = txn_elem.find("postTransactionAmounts")
    shares_owned_following = _safe_float(post_txn, "sharesOwnedFollowingTransaction")

    # Ownership nature
    ownership_nature_elem = txn_elem.find("ownershipNature")
    direct_or_indirect = _safe_text(ownership_nature_elem, "directOrIndirectOwnership", "D")
    ownership_nature = _safe_text(ownership_nature_elem, "natureOfOwnership")

    # Classify transaction
    classification = classify_transaction(transaction_code, acquired_disposed)

    return Form4Transaction(
        transaction_date=transaction_date,
        transaction_code=transaction_code,
        transaction_acquired_disposed=acquired_disposed,
        security_title=security_title,
        shares=shares,
        price_per_share=price_per_share,
        transaction_value=transaction_value,
        shares_owned_following=shares_owned_following,
        direct_or_indirect=direct_or_indirect,
        ownership_nature=ownership_nature if ownership_nature else None,
        classification=classification,
    )


def parse_form4_xml(xml_content: str, accession_number: str, source_url: str) -> Form4FilingDetails:
    """Parse a Form 4 XML document.

    Args:
        xml_content: Form 4 XML content as string
        accession_number: SEC accession number
        source_url: Source URL for reference

    Returns:
        Form4FilingDetails with parsed data or error status
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return Form4FilingDetails(
            issuer_cik="",
            issuer_name="",
            ticker=None,
            accession_number=accession_number,
            filing_date="",
            period_of_report="",
            source_url=source_url,
            parse_status="failed",
            error_type="xml_parse_error",
            error_message=f"Invalid XML: {e}",
        )

    # Extract issuer information
    issuer = root.find("issuer")
    issuer_cik = _safe_text(issuer, "issuerCik")
    issuer_name = _safe_text(issuer, "issuerName")
    issuer_trading_symbol = _safe_text(issuer, "issuerTradingSymbol")

    # Extract filing metadata
    period_of_report = _safe_text(root, "periodOfReport")

    # Note: filing_date is not typically in the XML itself,
    # but we'll need to pass it from the filing index metadata
    filing_date = period_of_report  # Fallback to period of report

    # Extract reporting owners
    owners = []
    for owner_elem in root.findall("reportingOwner"):
        owner = _parse_owner(owner_elem)
        owners.append(owner)

    # Extract non-derivative transactions
    transactions = []
    non_derivative_table = root.find("nonDerivativeTable")
    if non_derivative_table is not None:
        for txn_elem in non_derivative_table.findall("nonDerivativeTransaction"):
            txn = _parse_non_derivative_transaction(txn_elem)
            if txn:
                transactions.append(txn)

    parse_status = "success"
    if not transactions and not owners:
        parse_status = "partial"

    return Form4FilingDetails(
        issuer_cik=issuer_cik.zfill(10) if issuer_cik else "",
        issuer_name=issuer_name,
        ticker=issuer_trading_symbol if issuer_trading_symbol else None,
        accession_number=accession_number,
        filing_date=filing_date,
        period_of_report=period_of_report,
        source_url=source_url,
        owners=owners,
        transactions=transactions,
        parse_status=parse_status,
    )


def _extract_xml_from_submission(submission_text: str) -> str | None:
    """Extract XML ownership document from SEC submission text file.

    SEC Form 4 filings often embed the raw XML ownership document within <XML>...</XML>
    tags in the submission text file (.txt).

    Args:
        submission_text: Content of submission text file

    Returns:
        Extracted XML content or None if not found
    """
    match = re.search(r'<XML>(.*?)</XML>', submission_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def fetch_and_parse_form4(accession_number: str, cik: str, primary_document: str | None = None) -> Form4FilingDetails:
    """Fetch and parse a Form 4 XML document from SEC EDGAR.

    Tries multiple strategies to locate the raw XML ownership document:
    1. Fetch submission text file and extract <XML>...</XML> block
    2. Fallback: Try primary document URL if provided
    3. Fallback: Try accession-based XML path

    Args:
        accession_number: SEC accession number (e.g., "0001878313-26-000012")
        cik: Issuer CIK (zero-padded 10 digits)
        primary_document: Optional primary document path from SEC submissions API (e.g., "xslF345X06/form4.xml")

    Returns:
        Form4FilingDetails with parsed data or error status
    """
    # Clean accession number (remove dashes for path)
    accession_clean = accession_number.replace("-", "")
    cik_clean = cik.lstrip("0")  # Remove leading zeros for URL

    source_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik_clean}&accession_number={accession_clean}&xbrl_type=v"

    # Strategy 1: Try submission text file (most reliable for recent Form 4 filings)
    txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{accession_number}.txt"
    resp = sec_fetch(txt_url, cache_max_age=3600)

    if resp["ok"]:
        xml_content = _extract_xml_from_submission(resp["body"])
        if xml_content:
            # Successfully extracted XML from submission text
            return parse_form4_xml(xml_content, accession_number, source_url)

    # Strategy 2: Try primary document URL if provided
    if primary_document:
        xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{primary_document}"
        resp = sec_fetch(xml_url, cache_max_age=3600, accept="application/xml")
        if resp["ok"]:
            # Check if it's actually XML (not HTML from XSLT transform)
            if resp["body"].strip().startswith("<?xml") or resp["body"].strip().startswith("<ownershipDocument"):
                return parse_form4_xml(resp["body"], accession_number, source_url)

    # Strategy 3: Try standard accession-based XML path
    xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{accession_number}.xml"
    resp = sec_fetch(xml_url, cache_max_age=3600, accept="application/xml")

    if resp["ok"]:
        return parse_form4_xml(resp["body"], accession_number, source_url)

    # All strategies failed
    return Form4FilingDetails(
        issuer_cik=cik,
        issuer_name="",
        ticker=None,
        accession_number=accession_number,
        filing_date="",
        period_of_report="",
        source_url=source_url,
        parse_status="failed",
        error_type="document_not_found",
        error_message=f"Could not locate XML ownership document. Tried: submission text, primary document ({primary_document if primary_document else 'N/A'}), accession-based XML",
    )


def summarize_transactions_for_report(details: Form4FilingDetails) -> dict[str, Any]:
    """Summarize Form 4 transactions for diagnostic reporting.

    Args:
        details: Parsed Form 4 filing details

    Returns:
        Dictionary with summary statistics
    """
    if details.parse_status == "failed":
        return {
            "parse_status": "failed",
            "error": details.error_message,
        }

    # Count transactions by classification
    open_market_purchases = []
    open_market_sales = []
    option_exercises = []
    grants_awards = []
    tax_withholding = []
    other = []

    for txn in details.transactions:
        if txn.classification == "OPEN_MARKET_PURCHASE":
            open_market_purchases.append(txn)
        elif txn.classification == "OPEN_MARKET_SALE":
            open_market_sales.append(txn)
        elif txn.classification in ("OPTION_EXERCISE", "OPTION_EXERCISE_WITH_SALE"):
            option_exercises.append(txn)
        elif txn.classification == "GRANT_AWARD":
            grants_awards.append(txn)
        elif txn.classification == "TAX_WITHHOLDING_OR_DISPOSITION":
            tax_withholding.append(txn)
        else:
            other.append(txn)

    # Calculate total values and shares
    purchase_value = sum(
        txn.transaction_value for txn in open_market_purchases if txn.transaction_value
    )
    purchase_shares = sum(txn.shares for txn in open_market_purchases)

    sale_value = sum(
        txn.transaction_value for txn in open_market_sales if txn.transaction_value
    )
    sale_shares = sum(txn.shares for txn in open_market_sales)

    grant_shares = sum(txn.shares for txn in grants_awards)

    # Build notable owners list
    notable_owners = []
    for owner in details.owners:
        roles = []
        if owner.is_director:
            roles.append("Director")
        if owner.is_officer and owner.officer_title:
            roles.append(owner.officer_title)
        elif owner.is_officer:
            roles.append("Officer")
        if owner.is_ten_percent_owner:
            roles.append("10% Owner")

        if roles:
            notable_owners.append(f"{owner.name} ({', '.join(roles)})")
        else:
            notable_owners.append(owner.name)

    return {
        "parse_status": details.parse_status,
        "total_transactions": len(details.transactions),
        "open_market_purchases": {
            "count": len(open_market_purchases),
            "total_value": purchase_value,
            "total_shares": purchase_shares,
            "transactions": open_market_purchases,
        },
        "open_market_sales": {
            "count": len(open_market_sales),
            "total_value": sale_value,
            "total_shares": sale_shares,
            "transactions": open_market_sales,
        },
        "option_exercises": {
            "count": len(option_exercises),
            "transactions": option_exercises,
        },
        "grants_awards": {
            "count": len(grants_awards),
            "total_shares": grant_shares,
            "transactions": grants_awards,
        },
        "tax_withholding": {
            "count": len(tax_withholding),
            "transactions": tax_withholding,
        },
        "other": {
            "count": len(other),
            "transactions": other,
        },
        "notable_owners": notable_owners,
        "owners": details.owners,
    }
