"""SEC 13F-HR information table XML parser.

Parses 13F-HR information table XML documents to extract individual security holdings
including CUSIP, issuer name, title of class, value, shares, and voting authority.

Example:
    holdings = parse_13f_info_table_xml(
        xml_content=xml_data,
        manager_name="Berkshire Hathaway",
        manager_cik="0001067983",
        accession_number="0001067983-24-000001",
        filing_date="2024-02-14",
        report_period="2023-12-31"
    )

    for holding in holdings:
        print(f"{holding.issuer_name}: {holding.shares:,} shares, ${holding.value_usd:,}")
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

from sources.sec_common import sec_fetch, utcnow_iso


@dataclass
class Form13FHolding:
    """Represents a single holding row from a 13F information table.

    Attributes:
        manager_name: Institutional manager name
        manager_cik: Manager CIK (10-digit padded)
        filing_accession: SEC accession number
        filing_date: Filing date (YYYY-MM-DD)
        report_period: Report period date (YYYY-MM-DD)
        issuer_name: Issuer/company name
        title_of_class: Security class title
        cusip: CUSIP identifier (9 characters)
        value_usd_thousands: Position value in thousands of USD
        shares_or_principal_amount: Share count or principal amount
        share_type: SH (shares) or PRN (principal amount)
        put_call: PUT, CALL, or empty
        investment_discretion: SOLE, SHARED, or OTHER
        other_manager: Other manager count
        voting_authority_sole: Sole voting authority share count
        voting_authority_shared: Shared voting authority share count
        voting_authority_none: No voting authority share count
        source_url: SEC filing source URL
        retrieved_at: ISO 8601 UTC timestamp
    """

    manager_name: str
    manager_cik: str
    filing_accession: str
    filing_date: str
    report_period: str
    issuer_name: str
    title_of_class: str
    cusip: str
    value_usd_thousands: float
    shares_or_principal_amount: float
    share_type: str  # SH or PRN
    put_call: str = ""
    investment_discretion: str = "SOLE"
    other_manager: int = 0
    voting_authority_sole: float = 0.0
    voting_authority_shared: float = 0.0
    voting_authority_none: float = 0.0
    source_url: str = ""
    retrieved_at: str = ""

    def __post_init__(self) -> None:
        if not self.retrieved_at:
            self.retrieved_at = utcnow_iso()

    @property
    def value_usd(self) -> float:
        """Position value in USD (converted from thousands)."""
        return self.value_usd_thousands * 1000


@dataclass
class Form13FParseResult:
    """Result of parsing a 13F information table.

    Attributes:
        manager_name: Manager name
        manager_cik: Manager CIK
        accession_number: Filing accession
        filing_date: Filing date
        report_period: Report period
        holdings: List of parsed holdings
        parse_status: success, partial, or failed
        total_holdings: Total number of holdings parsed
        total_value_usd: Total portfolio value in USD
        error_type: Error category if parsing failed
        error_message: Human-readable error description
    """

    manager_name: str
    manager_cik: str
    accession_number: str
    filing_date: str
    report_period: str
    holdings: list[Form13FHolding] = field(default_factory=list)
    parse_status: str = "success"  # success, partial, failed
    total_holdings: int = 0
    total_value_usd: float = 0.0
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.holdings:
            self.total_holdings = len(self.holdings)
            self.total_value_usd = sum(h.value_usd for h in self.holdings)


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
    return child.text.strip() if child.text else default


def _safe_float(element: ET.Element | None, tag: str, default: float = 0.0) -> float:
    """Safely extract float from an XML element.

    Args:
        element: Parent XML element
        tag: Child tag name to find
        default: Default value if not found

    Returns:
        Float value or default if not found/invalid
    """
    text = _safe_text(element, tag)
    if not text:
        return default
    try:
        return float(text)
    except (ValueError, TypeError):
        return default


def _safe_int(element: ET.Element | None, tag: str, default: int = 0) -> int:
    """Safely extract int from an XML element.

    Args:
        element: Parent XML element
        tag: Child tag name to find
        default: Default value if not found

    Returns:
        Int value or default if not found/invalid
    """
    text = _safe_text(element, tag)
    if not text:
        return default
    try:
        return int(text)
    except (ValueError, TypeError):
        return default


def parse_13f_info_table_xml(
    xml_content: str,
    manager_name: str,
    manager_cik: str,
    accession_number: str,
    filing_date: str,
    report_period: str,
    source_url: str = "",
) -> Form13FParseResult:
    """Parse a 13F-HR information table XML document.

    Args:
        xml_content: 13F information table XML content as string
        manager_name: Institutional manager name
        manager_cik: Manager CIK
        accession_number: SEC accession number
        filing_date: Filing date (YYYY-MM-DD)
        report_period: Report period date (YYYY-MM-DD)
        source_url: Source URL for reference

    Returns:
        Form13FParseResult with parsed holdings or error status
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        return Form13FParseResult(
            manager_name=manager_name,
            manager_cik=manager_cik,
            accession_number=accession_number,
            filing_date=filing_date,
            report_period=report_period,
            parse_status="failed",
            error_type="xml_parse_error",
            error_message=f"Invalid XML: {e}",
        )

    holdings = []

    # 13F information table uses <infoTable> root with multiple <infoTable> children
    # Find all infoTable entries
    for info_table_elem in root.findall(".//infoTable"):
        # Extract issuer name and title
        name_of_issuer = _safe_text(info_table_elem, "nameOfIssuer")
        title_of_class = _safe_text(info_table_elem, "titleOfClass")
        cusip = _safe_text(info_table_elem, "cusip")

        if not name_of_issuer or not cusip:
            # Skip entries missing critical fields
            continue

        # Extract share/principal amount info
        shrs_or_prn_amt = info_table_elem.find("shrsOrPrnAmt")
        if shrs_or_prn_amt is None:
            continue

        share_type = _safe_text(shrs_or_prn_amt, "sshPrnamt")  # SH or PRN
        shares_or_principal = _safe_float(shrs_or_prn_amt, "sshPrnamtType")

        # Extract value (in thousands of USD)
        value_usd_thousands = _safe_float(info_table_elem, "value")

        # Extract put/call
        put_call = _safe_text(info_table_elem, "putCall")

        # Extract investment discretion
        investment_discretion = _safe_text(info_table_elem, "investmentDiscretion", "SOLE")

        # Extract other manager
        other_manager = _safe_int(info_table_elem, "otherManager", 0)

        # Extract voting authority
        voting_authority = info_table_elem.find("votingAuthority")
        voting_sole = _safe_float(voting_authority, "Sole", 0.0)
        voting_shared = _safe_float(voting_authority, "Shared", 0.0)
        voting_none = _safe_float(voting_authority, "None", 0.0)

        holding = Form13FHolding(
            manager_name=manager_name,
            manager_cik=manager_cik,
            filing_accession=accession_number,
            filing_date=filing_date,
            report_period=report_period,
            issuer_name=name_of_issuer,
            title_of_class=title_of_class,
            cusip=cusip,
            value_usd_thousands=value_usd_thousands,
            shares_or_principal_amount=shares_or_principal,
            share_type=share_type,
            put_call=put_call,
            investment_discretion=investment_discretion,
            other_manager=other_manager,
            voting_authority_sole=voting_sole,
            voting_authority_shared=voting_shared,
            voting_authority_none=voting_none,
            source_url=source_url,
        )
        holdings.append(holding)

    parse_status = "success" if holdings else "partial"

    return Form13FParseResult(
        manager_name=manager_name,
        manager_cik=manager_cik,
        accession_number=accession_number,
        filing_date=filing_date,
        report_period=report_period,
        holdings=holdings,
        parse_status=parse_status,
    )


def fetch_and_parse_13f_info_table(
    accession_number: str,
    cik: str,
    manager_name: str,
    filing_date: str,
    report_period: str,
    primary_document: str,
) -> Form13FParseResult:
    """Fetch and parse a 13F-HR information table XML document from SEC EDGAR.

    Args:
        accession_number: SEC accession number (e.g., "0001067983-24-000001")
        cik: Manager CIK (zero-padded 10 digits)
        manager_name: Manager name
        filing_date: Filing date (YYYY-MM-DD)
        report_period: Report period date (YYYY-MM-DD)
        primary_document: Primary document filename

    Returns:
        Form13FParseResult with parsed holdings or error status
    """
    # Build 13F information table XML URL
    # Format: https://www.sec.gov/Archives/edgar/data/CIK/ACCESSION_NO_DIGITS/PRIMARY_DOC
    # But we need to find the info table XML, which is usually infotable.xml or similar

    # Clean accession number (remove dashes for path)
    accession_clean = accession_number.replace("-", "")
    cik_clean = cik.lstrip("0")  # Remove leading zeros for URL

    # Try common 13F info table filenames
    # Most 13F filings have the info table as a separate XML file
    possible_filenames = [
        "infotable.xml",
        "information_table.xml",
        "form13fInfoTable.xml",
        primary_document.replace(".txt", ".xml") if primary_document else None,
    ]

    xml_url = None
    resp = None

    for filename in possible_filenames:
        if not filename:
            continue

        test_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{accession_clean}/{filename}"

        # Fetch with 1-week cache (13F filings don't change)
        test_resp = sec_fetch(test_url, cache_max_age=604800, accept="application/xml")

        if test_resp["ok"]:
            xml_url = test_url
            resp = test_resp
            break

    if not resp or not resp["ok"]:
        return Form13FParseResult(
            manager_name=manager_name,
            manager_cik=cik,
            accession_number=accession_number,
            filing_date=filing_date,
            report_period=report_period,
            parse_status="failed",
            error_type="fetch_failed",
            error_message="Failed to fetch 13F information table XML (tried common filenames)",
        )

    source_url = xml_url or f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik_clean}&accession_number={accession_clean}&xbrl_type=v"

    # Parse the XML
    return parse_13f_info_table_xml(
        resp["body"],
        manager_name,
        cik,
        accession_number,
        filing_date,
        report_period,
        source_url,
    )
