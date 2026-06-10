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
    assert result.error_type == "xml_parse_error"
    assert result.error_message is not None
    assert len(result.holdings) == 0


def test_parse_empty_infotable():
    """Test parsing InfoTable with no holdings returns partial status."""
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

    assert result.parse_status == "partial"
    assert len(result.holdings) == 0


def test_parse_missing_critical_fields():
    """Test parsing skips entries missing critical fields."""
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

    # Should skip entry missing CUSIP
    assert result.parse_status == "partial"
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


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
