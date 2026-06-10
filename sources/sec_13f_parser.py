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

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any
from html.parser import HTMLParser

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


def _strip_namespace(tag: str) -> str:
    """Strip namespace from XML tag.

    Args:
        tag: XML tag with or without namespace

    Returns:
        Tag without namespace
    """
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_all_infotables(root: ET.Element) -> list[ET.Element]:
    """Find all infoTable elements regardless of namespace.

    Args:
        root: XML root element

    Returns:
        List of infoTable elements
    """
    infotables = []

    # Try direct findall first (no namespace)
    infotables = root.findall(".//infoTable")
    if infotables:
        return infotables

    # Try with any namespace
    for elem in root.iter():
        if _strip_namespace(elem.tag).lower() == "infotable":
            infotables.append(elem)

    return infotables


def _safe_text_ns(element: ET.Element | None, tag: str, default: str = "") -> str:
    """Safely extract text from an XML element with namespace tolerance.

    Args:
        element: Parent XML element
        tag: Child tag name to find (without namespace)
        default: Default value if not found

    Returns:
        Text content or default
    """
    if element is None:
        return default

    # Try without namespace first
    child = element.find(tag)
    if child is not None:
        return child.text.strip() if child.text else default

    # Try with any namespace
    tag_lower = tag.lower()
    for child_elem in element:
        if _strip_namespace(child_elem.tag).lower() == tag_lower:
            return child_elem.text.strip() if child_elem.text else default

    return default


def _safe_float_ns(element: ET.Element | None, tag: str, default: float = 0.0) -> float:
    """Safely extract float from an XML element with namespace tolerance.

    Args:
        element: Parent XML element
        tag: Child tag name to find (without namespace)
        default: Default value if not found

    Returns:
        Float value or default if not found/invalid
    """
    text = _safe_text_ns(element, tag)
    if not text:
        return default
    try:
        return float(text)
    except (ValueError, TypeError):
        return default


def _safe_int_ns(element: ET.Element | None, tag: str, default: int = 0) -> int:
    """Safely extract int from an XML element with namespace tolerance.

    Args:
        element: Parent XML element
        tag: Child tag name to find (without namespace)
        default: Default value if not found

    Returns:
        Int value or default if not found/invalid
    """
    text = _safe_text_ns(element, tag)
    if not text:
        return default
    try:
        return int(text)
    except (ValueError, TypeError):
        return default


def _find_child_ns(element: ET.Element | None, tag: str) -> ET.Element | None:
    """Find child element with namespace tolerance.

    Args:
        element: Parent XML element
        tag: Child tag name to find (without namespace)

    Returns:
        Child element or None
    """
    if element is None:
        return None

    # Try without namespace first
    child = element.find(tag)
    if child is not None:
        return child

    # Try with any namespace
    tag_lower = tag.lower()
    for child_elem in element:
        if _strip_namespace(child_elem.tag).lower() == tag_lower:
            return child_elem

    return None


class _13FHTMLTableParser(HTMLParser):
    """HTML parser for extracting 13F holdings from HTML table format.

    This parser handles the HTML rendering of 13F forms that some managers
    submit instead of clean XML.
    """

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_row = []
        self.rows = []
        self.cell_data = ""

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag == "td" and self.in_row:
            self.in_cell = True
            self.cell_data = ""

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        elif tag == "tr":
            if self.current_row:
                self.rows.append(self.current_row)
            self.in_row = False
        elif tag == "td":
            if self.in_cell:
                self.current_row.append(self.cell_data.strip())
            self.in_cell = False

    def handle_data(self, data):
        if self.in_cell:
            self.cell_data += data


def _parse_13f_html_table(
    html_content: str,
    manager_name: str,
    manager_cik: str,
    accession_number: str,
    filing_date: str,
    report_period: str,
    source_url: str = "",
) -> Form13FParseResult:
    """Parse 13F holdings from HTML table format.

    Args:
        html_content: HTML content with 13F table
        manager_name: Manager name
        manager_cik: Manager CIK
        accession_number: Filing accession
        filing_date: Filing date
        report_period: Report period
        source_url: Source URL

    Returns:
        Form13FParseResult with holdings or error
    """
    try:
        parser = _13FHTMLTableParser()
        parser.feed(html_content)

        holdings = []
        header_found = False
        name_idx = -1
        cusip_idx = -1
        value_idx = -1
        shares_idx = -1

        # Find header row and column indices
        for row in parser.rows:
            if not header_found:
                # Look for header row
                row_lower = [cell.lower() for cell in row]
                if "name of issuer" in " ".join(row_lower) or "issuer" in " ".join(row_lower):
                    # Found header row
                    for i, cell in enumerate(row_lower):
                        if "name" in cell and ("issuer" in cell or "company" in cell):
                            name_idx = i
                        elif "cusip" in cell:
                            cusip_idx = i
                        elif "value" in cell and "000" in cell:  # "value (x$1000)"
                            value_idx = i
                        elif "shares" in cell or "principal" in cell or "sh/prn" in cell:
                            shares_idx = i
                    header_found = True
                continue

            # Parse data rows
            if name_idx >= 0 and cusip_idx >= 0 and len(row) > max(name_idx, cusip_idx):
                name_of_issuer = row[name_idx] if name_idx < len(row) else ""
                cusip = row[cusip_idx] if cusip_idx < len(row) else ""

                # Skip if missing critical fields
                if not name_of_issuer or not cusip or len(cusip) != 9:
                    continue

                # Extract value
                value_usd_thousands = 0.0
                if value_idx >= 0 and value_idx < len(row):
                    try:
                        value_usd_thousands = float(row[value_idx].replace(",", ""))
                    except (ValueError, AttributeError):
                        pass

                # Extract shares
                shares_or_principal = 0.0
                if shares_idx >= 0 and shares_idx < len(row):
                    try:
                        shares_or_principal = float(row[shares_idx].replace(",", ""))
                    except (ValueError, AttributeError):
                        pass

                holding = Form13FHolding(
                    manager_name=manager_name,
                    manager_cik=manager_cik,
                    filing_accession=accession_number,
                    filing_date=filing_date,
                    report_period=report_period,
                    issuer_name=name_of_issuer,
                    title_of_class="",
                    cusip=cusip,
                    value_usd_thousands=value_usd_thousands,
                    shares_or_principal_amount=shares_or_principal,
                    share_type="SH",
                    source_url=source_url,
                )
                holdings.append(holding)

        if not header_found or not holdings:
            return Form13FParseResult(
                manager_name=manager_name,
                manager_cik=manager_cik,
                accession_number=accession_number,
                filing_date=filing_date,
                report_period=report_period,
                parse_status="failed",
                error_type="html_table_parse_failed",
                error_message="HTML table found but could not extract holdings (header not found or no data rows)",
            )

        return Form13FParseResult(
            manager_name=manager_name,
            manager_cik=manager_cik,
            accession_number=accession_number,
            filing_date=filing_date,
            report_period=report_period,
            holdings=holdings,
            parse_status="fallback_html_success",
        )

    except Exception as e:
        return Form13FParseResult(
            manager_name=manager_name,
            manager_cik=manager_cik,
            accession_number=accession_number,
            filing_date=filing_date,
            report_period=report_period,
            parse_status="failed",
            error_type="html_parse_exception",
            error_message=f"HTML table parsing failed: {type(e).__name__}: {e}",
        )


def parse_13f_info_table_xml(
    xml_content: str,
    manager_name: str,
    manager_cik: str,
    accession_number: str,
    filing_date: str,
    report_period: str,
    source_url: str = "",
) -> Form13FParseResult:
    """Parse a 13F-HR information table with multiple fallback strategies.

    Attempts parsing in this order:
    1. Strict XML parse (no namespace)
    2. Namespace-aware XML parse
    3. HTML table extraction
    4. Return failure with diagnostics

    Args:
        xml_content: 13F information table content (XML or HTML)
        manager_name: Institutional manager name
        manager_cik: Manager CIK
        accession_number: SEC accession number
        filing_date: Filing date (YYYY-MM-DD)
        report_period: Report period date (YYYY-MM-DD)
        source_url: Source URL for reference

    Returns:
        Form13FParseResult with parsed holdings or error status
    """
    # Attempt 1: Try strict XML parse
    xml_parse_error = None
    try:
        root = ET.fromstring(xml_content)

        # Try to find infoTable elements without namespace
        infotables = root.findall(".//infoTable")

        if infotables:
            # Success - parse holdings
            holdings = _parse_holdings_from_infotables(
                infotables,
                manager_name,
                manager_cik,
                accession_number,
                filing_date,
                report_period,
                source_url,
                use_namespace=False,
            )

            if holdings:
                return Form13FParseResult(
                    manager_name=manager_name,
                    manager_cik=manager_cik,
                    accession_number=accession_number,
                    filing_date=filing_date,
                    report_period=report_period,
                    holdings=holdings,
                    parse_status="success",
                )

    except ET.ParseError as e:
        xml_parse_error = e

    # Attempt 2: Namespace-aware XML parse
    if xml_parse_error is None:
        try:
            root = ET.fromstring(xml_content)

            # Try namespace-aware search
            infotables = _find_all_infotables(root)

            if infotables:
                holdings = _parse_holdings_from_infotables(
                    infotables,
                    manager_name,
                    manager_cik,
                    accession_number,
                    filing_date,
                    report_period,
                    source_url,
                    use_namespace=True,
                )

                if holdings:
                    return Form13FParseResult(
                        manager_name=manager_name,
                        manager_cik=manager_cik,
                        accession_number=accession_number,
                        filing_date=filing_date,
                        report_period=report_period,
                        holdings=holdings,
                        parse_status="fallback_namespace_success",
                    )

        except Exception:
            pass  # Try HTML fallback

    # Attempt 3: HTML table extraction
    if xml_parse_error is not None or "<!DOCTYPE html" in xml_content[:200].lower() or "<html" in xml_content[:200].lower():
        result = _parse_13f_html_table(
            xml_content,
            manager_name,
            manager_cik,
            accession_number,
            filing_date,
            report_period,
            source_url,
        )

        if result.parse_status != "failed":
            return result

    # All attempts failed
    error_msg = f"XML parse error: {xml_parse_error}" if xml_parse_error else "No infoTable elements found in XML"
    return Form13FParseResult(
        manager_name=manager_name,
        manager_cik=manager_cik,
        accession_number=accession_number,
        filing_date=filing_date,
        report_period=report_period,
        parse_status="failed",
        error_type="all_parse_attempts_failed",
        error_message=f"All parsing attempts failed. {error_msg}",
    )


def _parse_holdings_from_infotables(
    infotables: list[ET.Element],
    manager_name: str,
    manager_cik: str,
    accession_number: str,
    filing_date: str,
    report_period: str,
    source_url: str,
    use_namespace: bool = False,
) -> list[Form13FHolding]:
    """Parse holdings from infoTable elements.

    Args:
        infotables: List of infoTable XML elements
        manager_name: Manager name
        manager_cik: Manager CIK
        accession_number: Filing accession
        filing_date: Filing date
        report_period: Report period
        source_url: Source URL
        use_namespace: If True, use namespace-aware extraction

    Returns:
        List of parsed holdings
    """
    holdings = []

    for info_table_elem in infotables:
        # Extract fields with namespace tolerance
        if use_namespace:
            name_of_issuer = _safe_text_ns(info_table_elem, "nameOfIssuer")
            title_of_class = _safe_text_ns(info_table_elem, "titleOfClass")
            cusip = _safe_text_ns(info_table_elem, "cusip")
            value_usd_thousands = _safe_float_ns(info_table_elem, "value")
            put_call = _safe_text_ns(info_table_elem, "putCall")
            investment_discretion = _safe_text_ns(info_table_elem, "investmentDiscretion", "SOLE")
            other_manager = _safe_int_ns(info_table_elem, "otherManager", 0)

            shrs_or_prn_amt = _find_child_ns(info_table_elem, "shrsOrPrnAmt")
            if shrs_or_prn_amt is not None:
                share_type = _safe_text_ns(shrs_or_prn_amt, "sshPrnamt")
                shares_or_principal = _safe_float_ns(shrs_or_prn_amt, "sshPrnamtType")
            else:
                share_type = ""
                shares_or_principal = 0.0

            voting_authority = _find_child_ns(info_table_elem, "votingAuthority")
            if voting_authority is not None:
                voting_sole = _safe_float_ns(voting_authority, "Sole", 0.0)
                voting_shared = _safe_float_ns(voting_authority, "Shared", 0.0)
                voting_none = _safe_float_ns(voting_authority, "None", 0.0)
            else:
                voting_sole = voting_shared = voting_none = 0.0

        else:
            name_of_issuer = _safe_text(info_table_elem, "nameOfIssuer")
            title_of_class = _safe_text(info_table_elem, "titleOfClass")
            cusip = _safe_text(info_table_elem, "cusip")
            value_usd_thousands = _safe_float(info_table_elem, "value")
            put_call = _safe_text(info_table_elem, "putCall")
            investment_discretion = _safe_text(info_table_elem, "investmentDiscretion", "SOLE")
            other_manager = _safe_int(info_table_elem, "otherManager", 0)

            shrs_or_prn_amt = info_table_elem.find("shrsOrPrnAmt")
            if shrs_or_prn_amt is not None:
                share_type = _safe_text(shrs_or_prn_amt, "sshPrnamt")
                shares_or_principal = _safe_float(shrs_or_prn_amt, "sshPrnamtType")
            else:
                share_type = ""
                shares_or_principal = 0.0

            voting_authority = info_table_elem.find("votingAuthority")
            if voting_authority is not None:
                voting_sole = _safe_float(voting_authority, "Sole", 0.0)
                voting_shared = _safe_float(voting_authority, "Shared", 0.0)
                voting_none = _safe_float(voting_authority, "None", 0.0)
            else:
                voting_sole = voting_shared = voting_none = 0.0

        # Skip if missing critical fields
        if not name_of_issuer or not cusip:
            continue

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

    return holdings


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
        "informationtable.xml",  # Lowercase, no underscore variant (e.g., Two Sigma)
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
