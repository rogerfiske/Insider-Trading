"""Tests for SEC Form 4 XML detail extraction."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sources.sec_form4_details import (
    Form4Owner,
    Form4Transaction,
    Form4FilingDetails,
    classify_transaction,
    parse_form4_xml,
    summarize_transactions_for_report,
)


def test_classify_transaction_purchase():
    """Test classification of purchase transactions."""
    assert classify_transaction("P", "A") == "OPEN_MARKET_PURCHASE"


def test_classify_transaction_sale():
    """Test classification of sale transactions."""
    assert classify_transaction("S", "D") == "OPEN_MARKET_SALE"


def test_classify_transaction_option_exercise():
    """Test classification of option exercise transactions."""
    assert classify_transaction("M", "A") == "OPTION_EXERCISE"


def test_classify_transaction_option_exercise_with_sale():
    """Test classification of option exercise with immediate sale."""
    assert classify_transaction("M", "D") == "OPTION_EXERCISE_WITH_SALE"


def test_classify_transaction_grant():
    """Test classification of grant/award transactions."""
    assert classify_transaction("A", "A") == "GRANT_AWARD"


def test_classify_transaction_tax_withholding():
    """Test classification of tax withholding transactions."""
    assert classify_transaction("F", "D") == "TAX_WITHHOLDING_OR_DISPOSITION"


def test_classify_transaction_unknown():
    """Test classification of unknown transaction codes."""
    assert classify_transaction("X", "A") == "OTHER_OR_UNCLASSIFIED"


def test_parse_form4_xml_with_purchase():
    """Test parsing Form 4 XML with an open-market purchase."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <schemaVersion>X0306</schemaVersion>
    <issuer>
        <issuerCik>0001878313</issuerCik>
        <issuerName>MAIA Biotechnology, Inc.</issuerName>
        <issuerTradingSymbol>MAIA</issuerTradingSymbol>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerCik>0001234567</rptOwnerCik>
            <rptOwnerName>Smith John</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerAddress>
            <rptOwnerStreet1>123 Main St</rptOwnerStreet1>
            <rptOwnerCity>Anywhere</rptOwnerCity>
            <rptOwnerState>CA</rptOwnerState>
            <rptOwnerZipCode>90210</rptOwnerZipCode>
        </reportingOwnerAddress>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
            <isOfficer>1</isOfficer>
            <officerTitle>Chief Executive Officer</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionDate>
                <value>2024-01-15</value>
            </transactionDate>
            <transactionCoding>
                <transactionFormType>4</transactionFormType>
                <transactionCode>P</transactionCode>
                <equitySwapInvolved>0</equitySwapInvolved>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>10000</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>5.50</value>
                </transactionPricePerShare>
                <transactionAcquiredDisposedCode>
                    <value>A</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction>
                    <value>50000</value>
                </sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership>
                    <value>D</value>
                </directOrIndirectOwnership>
            </ownershipNature>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
    <periodOfReport>2024-01-15</periodOfReport>
</ownershipDocument>"""

    result = parse_form4_xml(
        xml_content,
        "0001878313-24-000001",
        "https://www.sec.gov/Archives/edgar/data/1878313/000187831324000001/0001878313-24-000001.xml",
    )

    # Check filing details
    assert result.issuer_cik == "0001878313"
    assert result.issuer_name == "MAIA Biotechnology, Inc."
    assert result.ticker == "MAIA"
    assert result.accession_number == "0001878313-24-000001"
    assert result.period_of_report == "2024-01-15"
    assert result.parse_status == "success"

    # Check owner
    assert len(result.owners) == 1
    owner = result.owners[0]
    assert owner.name == "Smith John"
    assert owner.cik == "0001234567"
    assert owner.is_director is True
    assert owner.is_officer is True
    assert owner.officer_title == "Chief Executive Officer"

    # Check transaction
    assert len(result.transactions) == 1
    txn = result.transactions[0]
    assert txn.transaction_date == "2024-01-15"
    assert txn.transaction_code == "P"
    assert txn.classification == "OPEN_MARKET_PURCHASE"
    assert txn.security_title == "Common Stock"
    assert txn.shares == 10000.0
    assert txn.price_per_share == 5.50
    assert txn.transaction_value == 55000.0
    assert txn.shares_owned_following == 50000.0
    assert txn.direct_or_indirect == "D"
    assert txn.transaction_acquired_disposed == "A"


def test_parse_form4_xml_with_sale():
    """Test parsing Form 4 XML with an open-market sale."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <issuer>
        <issuerCik>0001878313</issuerCik>
        <issuerName>MAIA Biotechnology, Inc.</issuerName>
        <issuerTradingSymbol>MAIA</issuerTradingSymbol>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerCik>0001234567</rptOwnerCik>
            <rptOwnerName>Johnson Jane</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>0</isDirector>
            <isOfficer>1</isOfficer>
            <officerTitle>Chief Financial Officer</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionDate>
                <value>2024-02-20</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>S</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>5000</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>6.25</value>
                </transactionPricePerShare>
                <transactionAcquiredDisposedCode>
                    <value>D</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction>
                    <value>25000</value>
                </sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership>
                    <value>D</value>
                </directOrIndirectOwnership>
            </ownershipNature>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
    <periodOfReport>2024-02-20</periodOfReport>
</ownershipDocument>"""

    result = parse_form4_xml(xml_content, "0001878313-24-000002", "https://test.sec.gov")

    assert result.parse_status == "success"
    assert len(result.transactions) == 1
    txn = result.transactions[0]
    assert txn.transaction_code == "S"
    assert txn.classification == "OPEN_MARKET_SALE"
    assert txn.shares == 5000.0
    assert txn.price_per_share == 6.25
    assert txn.transaction_value == 31250.0
    assert txn.transaction_acquired_disposed == "D"


def test_parse_form4_xml_with_grant():
    """Test parsing Form 4 XML with grant/award."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <issuer>
        <issuerCik>0001878313</issuerCik>
        <issuerName>MAIA Biotechnology, Inc.</issuerName>
        <issuerTradingSymbol>MAIA</issuerTradingSymbol>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerCik>0001234567</rptOwnerCik>
            <rptOwnerName>Director Bob</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionDate>
                <value>2024-03-01</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>A</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>2000</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>0</value>
                </transactionPricePerShare>
                <transactionAcquiredDisposedCode>
                    <value>A</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction>
                    <value>12000</value>
                </sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership>
                    <value>D</value>
                </directOrIndirectOwnership>
            </ownershipNature>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
    <periodOfReport>2024-03-01</periodOfReport>
</ownershipDocument>"""

    result = parse_form4_xml(xml_content, "0001878313-24-000003", "https://test.sec.gov")

    assert result.parse_status == "success"
    assert len(result.transactions) == 1
    txn = result.transactions[0]
    assert txn.transaction_code == "A"
    assert txn.classification == "GRANT_AWARD"
    assert txn.shares == 2000.0
    assert txn.price_per_share == 0.0
    assert txn.transaction_value == 0.0


def test_parse_form4_xml_missing_optional_fields():
    """Test parsing Form 4 XML with missing optional fields."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <issuer>
        <issuerCik>0001878313</issuerCik>
        <issuerName>MAIA Biotechnology, Inc.</issuerName>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Anonymous Owner</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionDate>
                <value>2024-04-01</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>P</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>1000</value>
                </transactionShares>
                <transactionAcquiredDisposedCode>
                    <value>A</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
    <periodOfReport>2024-04-01</periodOfReport>
</ownershipDocument>"""

    result = parse_form4_xml(xml_content, "0001878313-24-000004", "https://test.sec.gov")

    # Should parse successfully even with missing optional fields
    assert result.parse_status == "success"
    assert result.ticker is None  # Missing issuerTradingSymbol

    owner = result.owners[0]
    assert owner.cik is None  # Missing rptOwnerCik
    assert owner.officer_title is None  # Not an officer

    txn = result.transactions[0]
    assert txn.price_per_share is None  # Missing price
    assert txn.transaction_value is None  # Cannot calculate without price
    assert txn.shares_owned_following is None  # Missing post-transaction amount


def test_parse_form4_xml_invalid_xml():
    """Test graceful failure on invalid XML."""
    xml_content = "This is not valid XML"

    result = parse_form4_xml(xml_content, "0001878313-24-000005", "https://test.sec.gov")

    assert result.parse_status == "failed"
    assert result.error_type == "xml_parse_error"
    assert result.error_message is not None
    assert len(result.transactions) == 0
    assert len(result.owners) == 0


def test_parse_form4_xml_missing_required_fields():
    """Test graceful failure on missing required fields."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <issuer>
    </issuer>
</ownershipDocument>"""

    result = parse_form4_xml(xml_content, "0001878313-24-000006", "https://test.sec.gov")

    # Should be partial or failed due to missing critical issuer information
    assert result.parse_status in ("partial", "failed")


def test_transaction_value_calculation():
    """Test transaction value calculation from shares × price."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <issuer>
        <issuerCik>0001878313</issuerCik>
        <issuerName>Test Corp</issuerName>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Test Owner</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionDate>
                <value>2024-01-01</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>P</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>1234</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>12.34</value>
                </transactionPricePerShare>
                <transactionAcquiredDisposedCode>
                    <value>A</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
    <periodOfReport>2024-01-01</periodOfReport>
</ownershipDocument>"""

    result = parse_form4_xml(xml_content, "test-accession", "https://test.sec.gov")

    txn = result.transactions[0]
    expected_value = 1234 * 12.34
    assert txn.transaction_value == expected_value
    assert abs(txn.transaction_value - 15227.56) < 0.01


def test_no_secrets_in_parsed_output():
    """Test that parsed output does not contain secrets."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <issuer>
        <issuerCik>0001878313</issuerCik>
        <issuerName>MAIA Biotechnology, Inc.</issuerName>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Test Owner</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionDate>
                <value>2024-01-01</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>P</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>1000</value>
                </transactionShares>
                <transactionAcquiredDisposedCode>
                    <value>A</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
    <periodOfReport>2024-01-01</periodOfReport>
</ownershipDocument>"""

    result = parse_form4_xml(xml_content, "test-accession", "https://test.sec.gov")

    # Convert result to string representation and check for common secret patterns
    result_str = str(result.__dict__)

    # Should not contain common secret patterns
    assert "TELEGRAM_BOT_TOKEN" not in result_str
    assert "SMTP_PASSWORD" not in result_str
    assert "sk-ant-" not in result_str
    assert "API_KEY" not in result_str


def test_summarize_transactions_for_report():
    """Test transaction summary for reporting."""
    # Create a mock Form4FilingDetails with various transactions
    details = Form4FilingDetails(
        issuer_cik="0001878313",
        issuer_name="MAIA Biotechnology, Inc.",
        ticker="MAIA",
        accession_number="test-accession",
        filing_date="2024-01-15",
        period_of_report="2024-01-15",
        source_url="https://test.sec.gov",
        owners=[
            Form4Owner(name="John Smith", is_director=True, is_officer=True, officer_title="CEO")
        ],
        transactions=[
            Form4Transaction(
                transaction_date="2024-01-15",
                transaction_code="P",
                classification="OPEN_MARKET_PURCHASE",
                transaction_acquired_disposed="A",
                security_title="Common Stock",
                shares=10000.0,
                price_per_share=5.50,
                transaction_value=55000.0,
            ),
            Form4Transaction(
                transaction_date="2024-01-15",
                transaction_code="S",
                classification="OPEN_MARKET_SALE",
                transaction_acquired_disposed="D",
                security_title="Common Stock",
                shares=5000.0,
                price_per_share=6.00,
                transaction_value=30000.0,
            ),
            Form4Transaction(
                transaction_date="2024-01-15",
                transaction_code="A",
                classification="GRANT_AWARD",
                transaction_acquired_disposed="A",
                security_title="Common Stock",
                shares=2000.0,
                price_per_share=0.0,
                transaction_value=0.0,
            ),
        ],
    )

    summary = summarize_transactions_for_report(details)

    # Check open market purchases
    assert "open_market_purchases" in summary
    purchases = summary["open_market_purchases"]
    assert purchases["count"] == 1
    assert purchases["total_shares"] == 10000.0
    assert purchases["total_value"] == 55000.0

    # Check open market sales
    assert "open_market_sales" in summary
    sales = summary["open_market_sales"]
    assert sales["count"] == 1
    assert sales["total_shares"] == 5000.0
    assert sales["total_value"] == 30000.0

    # Check grants
    assert "grants_awards" in summary
    grants = summary["grants_awards"]
    assert grants["count"] == 1
    assert grants["total_shares"] == 2000.0

    # Check notable owners
    assert "notable_owners" in summary
    assert len(summary["notable_owners"]) == 1
    assert "CEO" in summary["notable_owners"][0]
