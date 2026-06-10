"""Tests for SEC 13F InfoTable XML parser.

This test suite validates the 13F InfoTable XML parsing functionality
from CP23F 13F InfoTable matching integration.
"""

import json
from pathlib import Path

from sources.sec_13f_parser import (
    Form13FHolding,
    Form13FParseResult,
    parse_13f_info_table_xml,
)


# Minimal 13F InfoTable XML fixture
MINIMAL_13F_XML = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable>
    <infoTable>
        <nameOfIssuer>APPLE INC</nameOfIssuer>
        <titleOfClass>COM</titleOfClass>
        <cusip>037833100</cusip>
        <value>100000</value>
        <shrsOrPrnAmt>
            <sshPrnamt>SH</sshPrnamt>
            <sshPrnamtType>5000</sshPrnamtType>
        </shrsOrPrnAmt>
        <investmentDiscretion>SOLE</investmentDiscretion>
        <votingAuthority>
            <Sole>5000</Sole>
            <Shared>0</Shared>
            <None>0</None>
        </votingAuthority>
    </infoTable>
</informationTable>
"""

# 13F InfoTable XML with multiple holdings
MULTI_HOLDING_13F_XML = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable>
    <infoTable>
        <nameOfIssuer>APPLE INC</nameOfIssuer>
        <titleOfClass>COM</titleOfClass>
        <cusip>037833100</cusip>
        <value>100000</value>
        <shrsOrPrnAmt>
            <sshPrnamt>SH</sshPrnamt>
            <sshPrnamtType>5000</sshPrnamtType>
        </shrsOrPrnAmt>
        <investmentDiscretion>SOLE</investmentDiscretion>
        <votingAuthority>
            <Sole>5000</Sole>
            <Shared>0</Shared>
            <None>0</None>
        </votingAuthority>
    </infoTable>
    <infoTable>
        <nameOfIssuer>MICROSOFT CORP</nameOfIssuer>
        <titleOfClass>COM</titleOfClass>
        <cusip>594918104</cusip>
        <value>50000</value>
        <shrsOrPrnAmt>
            <sshPrnamt>SH</sshPrnamt>
            <sshPrnamtType>2000</sshPrnamtType>
        </shrsOrPrnAmt>
        <putCall>CALL</putCall>
        <investmentDiscretion>SHARED</investmentDiscretion>
        <otherManager>1</otherManager>
        <votingAuthority>
            <Sole>0</Sole>
            <Shared>2000</Shared>
            <None>0</None>
        </votingAuthority>
    </infoTable>
</informationTable>
"""

# MAIA Biotechnology holding fixture
MAIA_HOLDING_13F_XML = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable>
    <infoTable>
        <nameOfIssuer>MAIA BIOTECHNOLOGY INC</nameOfIssuer>
        <titleOfClass>COM</titleOfClass>
        <cusip>596278107</cusip>
        <value>250</value>
        <shrsOrPrnAmt>
            <sshPrnamt>SH</sshPrnamt>
            <sshPrnamtType>100000</sshPrnamtType>
        </shrsOrPrnAmt>
        <investmentDiscretion>SOLE</investmentDiscretion>
        <votingAuthority>
            <Sole>100000</Sole>
            <Shared>0</Shared>
            <None>0</None>
        </votingAuthority>
    </infoTable>
</informationTable>
"""

# Invalid XML fixture
INVALID_XML = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable>
    <infoTable>
        <nameOfIssuer>INCOMPLETE
    </infoTable>
"""


def test_parse_minimal_13f_infotable():
    """Test parsing a minimal 13F InfoTable XML."""
    result = parse_13f_info_table_xml(
        xml_content=MINIMAL_13F_XML,
        manager_name="Test Manager",
        manager_cik="0001234567",
        accession_number="0001234567-24-000001",
        filing_date="2024-05-15",
        report_period="2024-03-31",
    )

    assert result.parse_status == "success"
    assert len(result.holdings) == 1

    holding = result.holdings[0]
    assert holding.issuer_name == "APPLE INC"
    assert holding.cusip == "037833100"
    assert holding.value_usd_thousands == 100000.0
    assert holding.value_usd == 100000000.0  # value_usd property converts from thousands
    assert holding.shares_or_principal_amount == 5000.0
    assert holding.share_type == "SH"
    assert holding.investment_discretion == "SOLE"
    assert holding.voting_authority_sole == 5000.0


def test_parse_multiple_holdings():
    """Test parsing 13F InfoTable with multiple holdings."""
    result = parse_13f_info_table_xml(
        xml_content=MULTI_HOLDING_13F_XML,
        manager_name="Test Manager",
        manager_cik="0001234567",
        accession_number="0001234567-24-000001",
        filing_date="2024-05-15",
        report_period="2024-03-31",
    )

    assert result.parse_status == "success"
    assert len(result.holdings) == 2
    assert result.total_holdings == 2
    assert result.total_value_usd == 150000000.0  # 100M + 50M

    # Check first holding
    apple = result.holdings[0]
    assert apple.issuer_name == "APPLE INC"
    assert apple.cusip == "037833100"

    # Check second holding with put/call
    msft = result.holdings[1]
    assert msft.issuer_name == "MICROSOFT CORP"
    assert msft.cusip == "594918104"
    assert msft.put_call == "CALL"
    assert msft.investment_discretion == "SHARED"
    assert msft.other_manager == 1
    assert msft.voting_authority_shared == 2000.0


def test_parse_maia_holding():
    """Test parsing MAIA Biotechnology holding."""
    result = parse_13f_info_table_xml(
        xml_content=MAIA_HOLDING_13F_XML,
        manager_name="Test Manager",
        manager_cik="0001234567",
        accession_number="0001234567-24-000001",
        filing_date="2024-05-15",
        report_period="2024-03-31",
    )

    assert result.parse_status == "success"
    assert len(result.holdings) == 1

    maia = result.holdings[0]
    assert maia.issuer_name == "MAIA BIOTECHNOLOGY INC"
    assert maia.cusip == "596278107"
    assert maia.value_usd == 250000.0  # 250k
    assert maia.shares_or_principal_amount == 100000.0


def test_parse_invalid_xml():
    """Test parsing invalid XML returns failed status."""
    result = parse_13f_info_table_xml(
        xml_content=INVALID_XML,
        manager_name="Test Manager",
        manager_cik="0001234567",
        accession_number="0001234567-24-000001",
        filing_date="2024-05-15",
        report_period="2024-03-31",
    )

    assert result.parse_status == "failed"
    assert result.error_type == "all_parse_attempts_failed"
    assert result.error_message is not None
    assert len(result.holdings) == 0


def test_parse_empty_infotable():
    """Test parsing InfoTable with no holdings returns failed status."""
    empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable>
</informationTable>
"""

    result = parse_13f_info_table_xml(
        xml_content=empty_xml,
        manager_name="Test Manager",
        manager_cik="0001234567",
        accession_number="0001234567-24-000001",
        filing_date="2024-05-15",
        report_period="2024-03-31",
    )

    assert result.parse_status == "failed"
    assert len(result.holdings) == 0


def test_parse_missing_critical_fields():
    """Test parsing skips entries missing critical fields and returns failed status."""
    missing_cusip_xml = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable>
    <infoTable>
        <nameOfIssuer>APPLE INC</nameOfIssuer>
        <titleOfClass>COM</titleOfClass>
        <value>100000</value>
    </infoTable>
</informationTable>
"""

    result = parse_13f_info_table_xml(
        xml_content=missing_cusip_xml,
        manager_name="Test Manager",
        manager_cik="0001234567",
        accession_number="0001234567-24-000001",
        filing_date="2024-05-15",
        report_period="2024-03-31",
    )

    # Should skip entry missing CUSIP and return failed status (no valid holdings)
    assert result.parse_status == "failed"
    assert len(result.holdings) == 0


def test_parse_optional_fields():
    """Test parsing handles missing optional fields gracefully."""
    minimal_required_xml = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable>
    <infoTable>
        <nameOfIssuer>TEST COMPANY</nameOfIssuer>
        <cusip>000000000</cusip>
        <value>1000</value>
        <shrsOrPrnAmt>
            <sshPrnamt>SH</sshPrnamt>
            <sshPrnamtType>1000</sshPrnamtType>
        </shrsOrPrnAmt>
    </infoTable>
</informationTable>
"""

    result = parse_13f_info_table_xml(
        xml_content=minimal_required_xml,
        manager_name="Test Manager",
        manager_cik="0001234567",
        accession_number="0001234567-24-000001",
        filing_date="2024-05-15",
        report_period="2024-03-31",
    )

    assert result.parse_status == "success"
    assert len(result.holdings) == 1

    holding = result.holdings[0]
    assert holding.put_call == ""
    assert holding.investment_discretion == "SOLE"  # default
    assert holding.other_manager == 0  # default
    assert holding.voting_authority_sole == 0.0  # default


def test_parse_result_metadata():
    """Test parse result includes correct metadata."""
    result = parse_13f_info_table_xml(
        xml_content=MINIMAL_13F_XML,
        manager_name="Berkshire Hathaway",
        manager_cik="0001067983",
        accession_number="0001067983-24-000001",
        filing_date="2024-05-15",
        report_period="2024-03-31",
    )

    assert result.manager_name == "Berkshire Hathaway"
    assert result.manager_cik == "0001067983"
    assert result.accession_number == "0001067983-24-000001"
    assert result.filing_date == "2024-05-15"
    assert result.report_period == "2024-03-31"


# Namespace-aware XML fixtures (CP23F-Fix)

# 13F InfoTable XML with namespace (e.g., Bridgewater, Citadel)
NAMESPACE_13F_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns1:informationTable xmlns:ns1="http://www.sec.gov/edgar/document/thirteenf/informationtable">
    <ns1:infoTable>
        <ns1:nameOfIssuer>APPLE INC</ns1:nameOfIssuer>
        <ns1:titleOfClass>COM</ns1:titleOfClass>
        <ns1:cusip>037833100</ns1:cusip>
        <ns1:value>100000</ns1:value>
        <ns1:shrsOrPrnAmt>
            <ns1:sshPrnamt>SH</ns1:sshPrnamt>
            <ns1:sshPrnamtType>5000</ns1:sshPrnamtType>
        </ns1:shrsOrPrnAmt>
        <ns1:investmentDiscretion>SOLE</ns1:investmentDiscretion>
        <ns1:votingAuthority>
            <ns1:Sole>5000</ns1:Sole>
            <ns1:Shared>0</ns1:Shared>
            <ns1:None>0</ns1:None>
        </ns1:votingAuthority>
    </ns1:infoTable>
</ns1:informationTable>
"""

# 13F InfoTable XML with default namespace
DEFAULT_NAMESPACE_13F_XML = """<?xml version="1.0" encoding="UTF-8"?>
<informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">
    <infoTable>
        <nameOfIssuer>MICROSOFT CORP</nameOfIssuer>
        <titleOfClass>COM</titleOfClass>
        <cusip>594918104</cusip>
        <value>50000</value>
        <shrsOrPrnAmt>
            <sshPrnamt>SH</sshPrnamt>
            <sshPrnamtType>2000</sshPrnamtType>
        </shrsOrPrnAmt>
        <investmentDiscretion>SOLE</investmentDiscretion>
        <votingAuthority>
            <Sole>2000</Sole>
            <Shared>0</Shared>
            <None>0</None>
        </votingAuthority>
    </infoTable>
</informationTable>
"""

# HTML wrapper document (e.g., Berkshire, Renaissance)
HTML_WRAPPER_13F = """<!DOCTYPE html>
<html>
<head>
    <title>FORM 13F INFORMATION TABLE</title>
</head>
<body>
    <div class="FormData">
        <table>
            <tr>
                <td>This is an HTML wrapper, not a data table</td>
            </tr>
        </table>
    </div>
</body>
</html>
"""


def test_parse_namespace_aware_xml():
    """Test parsing 13F InfoTable with namespace prefix."""
    result = parse_13f_info_table_xml(
        xml_content=NAMESPACE_13F_XML,
        manager_name="Bridgewater Associates",
        manager_cik="0001350694",
        accession_number="0001350694-26-000002",
        filing_date="2026-05-15",
        report_period="2026-03-31",
    )

    assert result.parse_status == "fallback_namespace_success"
    assert len(result.holdings) == 1

    holding = result.holdings[0]
    assert holding.issuer_name == "APPLE INC"
    assert holding.cusip == "037833100"
    assert holding.value_usd_thousands == 100000.0
    assert holding.shares_or_principal_amount == 5000.0


def test_parse_default_namespace_xml():
    """Test parsing 13F InfoTable with default namespace."""
    result = parse_13f_info_table_xml(
        xml_content=DEFAULT_NAMESPACE_13F_XML,
        manager_name="Citadel Advisors",
        manager_cik="0001423053",
        accession_number="0001104659-26-062477",
        filing_date="2026-05-15",
        report_period="2026-03-31",
    )

    assert result.parse_status == "fallback_namespace_success"
    assert len(result.holdings) == 1

    holding = result.holdings[0]
    assert holding.issuer_name == "MICROSOFT CORP"
    assert holding.cusip == "594918104"


def test_parse_html_wrapper_fails_gracefully():
    """Test parsing HTML wrapper document fails with appropriate status."""
    result = parse_13f_info_table_xml(
        xml_content=HTML_WRAPPER_13F,
        manager_name="Berkshire Hathaway",
        manager_cik="0001067983",
        accession_number="0001193125-26-226661",
        filing_date="2026-05-15",
        report_period="2026-03-31",
    )

    assert result.parse_status == "failed"
    assert result.error_type == "all_parse_attempts_failed"
    assert len(result.holdings) == 0
    assert result.error_message is not None


def test_parse_result_includes_diagnostics():
    """Test parse result includes diagnostic information."""
    result = parse_13f_info_table_xml(
        xml_content=NAMESPACE_13F_XML,
        manager_name="Test Manager",
        manager_cik="0001234567",
        accession_number="0001234567-26-000001",
        filing_date="2026-05-15",
        report_period="2026-03-31",
    )

    # Check metadata is preserved
    assert result.manager_name == "Test Manager"
    assert result.manager_cik == "0001234567"
    assert result.accession_number == "0001234567-26-000001"
    assert result.filing_date == "2026-05-15"
    assert result.report_period == "2026-03-31"

    # Check parse status is recorded
    assert result.parse_status in ["success", "fallback_namespace_success", "failed"]

    # Check totals are calculated
    if result.parse_status != "failed":
        assert result.total_holdings == len(result.holdings)
        assert result.total_value_usd >= 0


def test_multiple_infotable_blocks_with_namespace():
    """Test parsing multiple infoTable blocks with namespace."""
    multi_namespace_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ns1:informationTable xmlns:ns1="http://www.sec.gov/edgar/document/thirteenf/informationtable">
    <ns1:infoTable>
        <ns1:nameOfIssuer>APPLE INC</ns1:nameOfIssuer>
        <ns1:cusip>037833100</ns1:cusip>
        <ns1:value>100</ns1:value>
        <ns1:shrsOrPrnAmt>
            <ns1:sshPrnamt>SH</ns1:sshPrnamt>
            <ns1:sshPrnamtType>1000</ns1:sshPrnamtType>
        </ns1:shrsOrPrnAmt>
    </ns1:infoTable>
    <ns1:infoTable>
        <ns1:nameOfIssuer>MICROSOFT CORP</ns1:nameOfIssuer>
        <ns1:cusip>594918104</ns1:cusip>
        <ns1:value>200</ns1:value>
        <ns1:shrsOrPrnAmt>
            <ns1:sshPrnamt>SH</ns1:sshPrnamt>
            <ns1:sshPrnamtType>2000</ns1:sshPrnamtType>
        </ns1:shrsOrPrnAmt>
    </ns1:infoTable>
</ns1:informationTable>
"""

    result = parse_13f_info_table_xml(
        xml_content=multi_namespace_xml,
        manager_name="Test Manager",
        manager_cik="0001234567",
        accession_number="0001234567-26-000001",
        filing_date="2026-05-15",
        report_period="2026-03-31",
    )

    assert result.parse_status == "fallback_namespace_success"
    assert len(result.holdings) == 2
    assert result.total_holdings == 2


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
