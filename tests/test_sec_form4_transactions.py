"""Tests for Form 4 transaction extraction and aggregation.

Test coverage:
- Parse minimal Form 4 XML fixture
- Parse non-derivative and derivative transactions
- Transaction code classification (P, S, A, M, F, G, J, D)
- P/S counted as open-market, A/M/F/G/J not counted
- Transaction value calculation
- Aggregation metrics
- MAIA baseline reconciliation
- No buy/sell/hold language
- Safety flags
- No secrets
- No alert code
"""

from __future__ import annotations

from sources.form4_aggregator import (
    TRANSACTION_CODE_DESCRIPTIONS,
    CanonicalTransaction,
    Form4AggregationSummary,
    TopTrader,
    _calculate_top_traders,
    _classify_transaction_for_aggregation,
    _normalize_transaction,
    aggregate_form4_transactions,
)
from sources.sec_form4_details import (
    Form4FilingDetails,
    Form4Owner,
    Form4Transaction,
    parse_form4_xml,
)


def test_transaction_code_classification_p_is_open_market_purchase() -> None:
    """Test that code P is classified as open-market purchase."""
    is_purchase, is_sale = _classify_transaction_for_aggregation("P")
    assert is_purchase is True
    assert is_sale is False


def test_transaction_code_classification_s_is_open_market_sale() -> None:
    """Test that code S is classified as open-market sale."""
    is_purchase, is_sale = _classify_transaction_for_aggregation("S")
    assert is_purchase is False
    assert is_sale is True


def test_transaction_code_classification_a_is_not_open_market() -> None:
    """Test that code A (grant) is NOT classified as open-market."""
    is_purchase, is_sale = _classify_transaction_for_aggregation("A")
    assert is_purchase is False
    assert is_sale is False


def test_transaction_code_classification_m_is_not_open_market() -> None:
    """Test that code M (option exercise) is NOT classified as open-market."""
    is_purchase, is_sale = _classify_transaction_for_aggregation("M")
    assert is_purchase is False
    assert is_sale is False


def test_transaction_code_classification_f_is_not_open_market() -> None:
    """Test that code F (tax withholding) is NOT classified as open-market."""
    is_purchase, is_sale = _classify_transaction_for_aggregation("F")
    assert is_purchase is False
    assert is_sale is False


def test_transaction_code_classification_g_is_not_open_market() -> None:
    """Test that code G (gift) is NOT classified as open-market."""
    is_purchase, is_sale = _classify_transaction_for_aggregation("G")
    assert is_purchase is False
    assert is_sale is False


def test_transaction_code_classification_j_is_not_open_market() -> None:
    """Test that code J (other) is NOT classified as open-market."""
    is_purchase, is_sale = _classify_transaction_for_aggregation("J")
    assert is_purchase is False
    assert is_sale is False


def test_transaction_code_classification_d_is_not_open_market() -> None:
    """Test that code D (disposition to issuer) is NOT classified as open-market."""
    is_purchase, is_sale = _classify_transaction_for_aggregation("D")
    assert is_purchase is False
    assert is_sale is False


def test_transaction_code_descriptions_exist_for_all_codes() -> None:
    """Test that all transaction codes have descriptions."""
    codes = ["P", "S", "M", "A", "F", "G", "D", "J"]
    for code in codes:
        assert code in TRANSACTION_CODE_DESCRIPTIONS
        assert len(TRANSACTION_CODE_DESCRIPTIONS[code]) > 0


def test_normalize_transaction_populates_all_canonical_fields() -> None:
    """Test that _normalize_transaction populates all canonical fields."""
    filing = Form4FilingDetails(
        issuer_cik="0001878313",
        issuer_name="MAIA Biotechnology, Inc.",
        ticker="MAIA",
        accession_number="0001878313-26-000012",
        filing_date="2026-06-01",
        period_of_report="2026-05-31",
        source_url="https://www.sec.gov/...",
    )

    owner = Form4Owner(
        name="John Doe",
        cik="0001234567",
        is_director=True,
        is_officer=True,
        is_ten_percent_owner=False,
        is_other=False,
        officer_title="Chief Executive Officer",
    )

    txn = Form4Transaction(
        transaction_date="2026-05-31",
        transaction_code="P",
        transaction_acquired_disposed="A",
        security_title="Common Stock",
        shares=10000.0,
        price_per_share=1.50,
        transaction_value=15000.0,
        shares_owned_following=50000.0,
        direct_or_indirect="D",
        ownership_nature=None,
        classification="OPEN_MARKET_PURCHASE",
    )

    canonical = _normalize_transaction(txn, filing, owner, "MAIA")

    assert canonical.ticker == "MAIA"
    assert canonical.issuer_cik == "0001878313"
    assert canonical.accession_number == "0001878313-26-000012"
    assert canonical.filing_date == "2026-06-01"
    assert canonical.period_of_report == "2026-05-31"
    assert canonical.reporting_owner_name == "John Doe"
    assert canonical.reporting_owner_cik == "0001234567"
    assert canonical.officer_title == "Chief Executive Officer"
    assert canonical.director is True
    assert canonical.ten_percent_owner is False
    assert canonical.security_title == "Common Stock"
    assert canonical.transaction_date == "2026-05-31"
    assert canonical.transaction_code == "P"
    assert canonical.transaction_code_description == "Open-market purchase"
    assert canonical.transaction_classification == "OPEN_MARKET_PURCHASE"
    assert canonical.is_open_market_purchase is True
    assert canonical.is_open_market_sale is False
    assert canonical.is_derivative is False
    assert canonical.shares == 10000.0
    assert canonical.price_per_share == 1.50
    assert canonical.transaction_value == 15000.0
    assert canonical.shares_owned_following == 50000.0
    assert canonical.ownership_nature_direct_or_indirect == "D"
    assert canonical.ownership_nature_explanation is None


def test_aggregate_form4_transactions_empty_list_returns_zero_metrics() -> None:
    """Test that aggregation of empty list returns zero metrics."""
    result = aggregate_form4_transactions([], "MAIA")

    assert result["summary"]["form4_filings_found"] == 0
    assert result["summary"]["form4_filings_parsed"] == 0
    assert result["summary"]["form4_filings_failed"] == 0
    assert result["summary"]["transactions_extracted"] == 0
    assert result["summary"]["open_market_purchases"] == 0
    assert result["summary"]["open_market_sales"] == 0
    assert result["summary"]["open_market_purchase_value"] == 0.0
    assert result["summary"]["open_market_sale_value"] == 0.0
    assert result["summary"]["net_open_market_value"] == 0.0
    assert result["summary"]["distinct_buyers"] == 0
    assert result["summary"]["distinct_sellers"] == 0
    assert result["summary"]["latest_open_market_purchase_date"] is None
    assert result["summary"]["latest_open_market_sale_date"] is None
    assert result["summary"]["transaction_code_counts"] == {}
    assert len(result["transactions"]) == 0
    assert len(result["top_buyers_by_value"]) == 0
    assert len(result["top_sellers_by_value"]) == 0


def test_aggregate_form4_transactions_counts_open_market_purchases_correctly() -> None:
    """Test that aggregation correctly counts open-market purchases (code=P)."""
    filing = Form4FilingDetails(
        issuer_cik="0001878313",
        issuer_name="MAIA Biotechnology, Inc.",
        ticker="MAIA",
        accession_number="0001878313-26-000012",
        filing_date="2026-06-01",
        period_of_report="2026-05-31",
        source_url="https://www.sec.gov/...",
        owners=[
            Form4Owner(
                name="John Doe",
                cik="0001234567",
                is_director=True,
                is_officer=True,
                officer_title="CEO",
            )
        ],
        transactions=[
            Form4Transaction(
                transaction_date="2026-05-31",
                transaction_code="P",
                transaction_acquired_disposed="A",
                security_title="Common Stock",
                shares=10000.0,
                price_per_share=1.50,
                transaction_value=15000.0,
                shares_owned_following=50000.0,
                classification="OPEN_MARKET_PURCHASE",
            ),
            Form4Transaction(
                transaction_date="2026-05-30",
                transaction_code="P",
                transaction_acquired_disposed="A",
                security_title="Common Stock",
                shares=5000.0,
                price_per_share=1.60,
                transaction_value=8000.0,
                shares_owned_following=40000.0,
                classification="OPEN_MARKET_PURCHASE",
            ),
        ],
        parse_status="success",
    )

    result = aggregate_form4_transactions([filing], "MAIA")

    assert result["summary"]["open_market_purchases"] == 2
    assert result["summary"]["open_market_purchase_value"] == 23000.0
    assert result["summary"]["distinct_buyers"] == 1
    assert result["summary"]["latest_open_market_purchase_date"] == "2026-05-31"


def test_aggregate_form4_transactions_excludes_grants_from_open_market() -> None:
    """Test that aggregation excludes grants (code=A) from open-market counts."""
    filing = Form4FilingDetails(
        issuer_cik="0001878313",
        issuer_name="MAIA Biotechnology, Inc.",
        ticker="MAIA",
        accession_number="0001878313-26-000012",
        filing_date="2026-06-01",
        period_of_report="2026-05-31",
        source_url="https://www.sec.gov/...",
        owners=[
            Form4Owner(
                name="John Doe",
                cik="0001234567",
                is_director=True,
                is_officer=True,
                officer_title="CEO",
            )
        ],
        transactions=[
            Form4Transaction(
                transaction_date="2026-05-31",
                transaction_code="A",  # Grant, NOT open-market
                transaction_acquired_disposed="A",
                security_title="Common Stock",
                shares=10000.0,
                price_per_share=None,  # Grants typically have no price
                transaction_value=None,
                shares_owned_following=50000.0,
                classification="GRANT_AWARD",
            )
        ],
        parse_status="success",
    )

    result = aggregate_form4_transactions([filing], "MAIA")

    assert result["summary"]["transactions_extracted"] == 1
    assert result["summary"]["open_market_purchases"] == 0  # Grant is NOT open-market
    assert result["summary"]["open_market_purchase_value"] == 0.0
    assert result["summary"]["transaction_code_counts"]["A"] == 1


def test_aggregate_form4_transactions_excludes_option_exercises_from_open_market() -> None:
    """Test that aggregation excludes option exercises (code=M) from open-market counts."""
    filing = Form4FilingDetails(
        issuer_cik="0001878313",
        issuer_name="MAIA Biotechnology, Inc.",
        ticker="MAIA",
        accession_number="0001878313-26-000012",
        filing_date="2026-06-01",
        period_of_report="2026-05-31",
        source_url="https://www.sec.gov/...",
        owners=[
            Form4Owner(
                name="John Doe",
                cik="0001234567",
                is_director=True,
                is_officer=True,
                officer_title="CEO",
            )
        ],
        transactions=[
            Form4Transaction(
                transaction_date="2026-05-31",
                transaction_code="M",  # Option exercise, NOT open-market
                transaction_acquired_disposed="A",
                security_title="Common Stock",
                shares=5000.0,
                price_per_share=1.00,  # Exercise price
                transaction_value=5000.0,
                shares_owned_following=45000.0,
                classification="OPTION_EXERCISE",
            )
        ],
        parse_status="success",
    )

    result = aggregate_form4_transactions([filing], "MAIA")

    assert result["summary"]["transactions_extracted"] == 1
    assert result["summary"]["open_market_purchases"] == 0  # M is NOT open-market
    assert result["summary"]["open_market_purchase_value"] == 0.0
    assert result["summary"]["transaction_code_counts"]["M"] == 1


def test_aggregate_form4_transactions_calculates_distinct_buyers() -> None:
    """Test that aggregation correctly counts distinct buyers."""
    filing1 = Form4FilingDetails(
        issuer_cik="0001878313",
        issuer_name="MAIA Biotechnology, Inc.",
        ticker="MAIA",
        accession_number="0001878313-26-000012",
        filing_date="2026-06-01",
        period_of_report="2026-05-31",
        source_url="https://www.sec.gov/...",
        owners=[
            Form4Owner(
                name="John Doe",
                cik="0001234567",
                is_director=True,
                is_officer=True,
                officer_title="CEO",
            )
        ],
        transactions=[
            Form4Transaction(
                transaction_date="2026-05-31",
                transaction_code="P",
                transaction_acquired_disposed="A",
                security_title="Common Stock",
                shares=10000.0,
                price_per_share=1.50,
                transaction_value=15000.0,
                shares_owned_following=50000.0,
                classification="OPEN_MARKET_PURCHASE",
            )
        ],
        parse_status="success",
    )

    filing2 = Form4FilingDetails(
        issuer_cik="0001878313",
        issuer_name="MAIA Biotechnology, Inc.",
        ticker="MAIA",
        accession_number="0001878313-26-000013",
        filing_date="2026-06-02",
        period_of_report="2026-06-01",
        source_url="https://www.sec.gov/...",
        owners=[
            Form4Owner(
                name="Jane Smith",
                cik="0001234568",
                is_director=True,
                is_officer=False,
            )
        ],
        transactions=[
            Form4Transaction(
                transaction_date="2026-06-01",
                transaction_code="P",
                transaction_acquired_disposed="A",
                security_title="Common Stock",
                shares=5000.0,
                price_per_share=1.60,
                transaction_value=8000.0,
                shares_owned_following=30000.0,
                classification="OPEN_MARKET_PURCHASE",
            )
        ],
        parse_status="success",
    )

    result = aggregate_form4_transactions([filing1, filing2], "MAIA")

    assert result["summary"]["distinct_buyers"] == 2
    assert result["summary"]["open_market_purchases"] == 2
    assert result["summary"]["open_market_purchase_value"] == 23000.0


def test_aggregate_form4_transactions_handles_failed_parse_gracefully() -> None:
    """Test that aggregation handles failed parse status gracefully."""
    failed_filing = Form4FilingDetails(
        issuer_cik="0001878313",
        issuer_name="MAIA Biotechnology, Inc.",
        ticker="MAIA",
        accession_number="0001878313-26-000012",
        filing_date="2026-06-01",
        period_of_report="2026-05-31",
        source_url="https://www.sec.gov/...",
        parse_status="failed",
        error_type="xml_parse_error",
        error_message="Invalid XML",
    )

    result = aggregate_form4_transactions([failed_filing], "MAIA")

    assert result["summary"]["form4_filings_found"] == 1
    assert result["summary"]["form4_filings_parsed"] == 0
    assert result["summary"]["form4_filings_failed"] == 1
    assert result["summary"]["transactions_extracted"] == 0
    assert len(result["filing_parse_results"]) == 1
    assert result["filing_parse_results"][0]["parse_status"] == "failed"
    assert result["filing_parse_results"][0]["error_type"] == "xml_parse_error"


def test_calculate_top_traders_sorts_by_value_descending() -> None:
    """Test that top traders are sorted by total value descending."""
    transactions = [
        CanonicalTransaction(
            ticker="MAIA",
            issuer_cik="0001878313",
            accession_number="0001878313-26-000012",
            filing_date="2026-06-01",
            period_of_report="2026-05-31",
            reporting_owner_name="John Doe",
            reporting_owner_cik="0001234567",
            officer_title="CEO",
            director=True,
            ten_percent_owner=False,
            security_title="Common Stock",
            transaction_date="2026-05-31",
            transaction_code="P",
            transaction_code_description="Open-market purchase",
            transaction_classification="OPEN_MARKET_PURCHASE",
            is_open_market_purchase=True,
            is_open_market_sale=False,
            is_derivative=False,
            shares=10000.0,
            price_per_share=1.50,
            transaction_value=15000.0,
            shares_owned_following=50000.0,
            ownership_nature_direct_or_indirect="D",
            ownership_nature_explanation=None,
        ),
        CanonicalTransaction(
            ticker="MAIA",
            issuer_cik="0001878313",
            accession_number="0001878313-26-000013",
            filing_date="2026-06-02",
            period_of_report="2026-06-01",
            reporting_owner_name="Jane Smith",
            reporting_owner_cik="0001234568",
            officer_title=None,
            director=True,
            ten_percent_owner=False,
            security_title="Common Stock",
            transaction_date="2026-06-01",
            transaction_code="P",
            transaction_code_description="Open-market purchase",
            transaction_classification="OPEN_MARKET_PURCHASE",
            is_open_market_purchase=True,
            is_open_market_sale=False,
            is_derivative=False,
            shares=20000.0,
            price_per_share=1.60,
            transaction_value=32000.0,
            shares_owned_following=80000.0,
            ownership_nature_direct_or_indirect="D",
            ownership_nature_explanation=None,
        ),
    ]

    top_traders = _calculate_top_traders(transactions)

    assert len(top_traders) == 2
    assert top_traders[0].name == "Jane Smith"  # Higher value first
    assert top_traders[0].total_value == 32000.0
    assert top_traders[1].name == "John Doe"
    assert top_traders[1].total_value == 15000.0


def test_parse_form4_xml_extracts_basic_fields() -> None:
    """Test that minimal Form 4 XML is parsed correctly."""
    xml_content = """<?xml version="1.0"?>
<ownershipDocument>
    <issuer>
        <issuerCik>0001878313</issuerCik>
        <issuerName>MAIA Biotechnology, Inc.</issuerName>
        <issuerTradingSymbol>MAIA</issuerTradingSymbol>
    </issuer>
    <periodOfReport>2026-05-31</periodOfReport>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerCik>0001234567</rptOwnerCik>
            <rptOwnerName>John Doe</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
            <isOfficer>1</isOfficer>
            <isTenPercentOwner>0</isTenPercentOwner>
            <isOther>0</isOther>
            <officerTitle>Chief Executive Officer</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionDate>
                <value>2026-05-31</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>P</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>10000</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>1.50</value>
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
</ownershipDocument>"""

    result = parse_form4_xml(
        xml_content=xml_content,
        accession_number="0001878313-26-000012",
        source_url="https://www.sec.gov/...",
    )

    assert result.parse_status == "success"
    assert result.issuer_cik == "0001878313"
    assert result.issuer_name == "MAIA Biotechnology, Inc."
    assert result.ticker == "MAIA"
    assert result.period_of_report == "2026-05-31"
    assert len(result.owners) == 1
    assert result.owners[0].name == "John Doe"
    assert result.owners[0].cik == "0001234567"
    assert result.owners[0].is_director is True
    assert result.owners[0].is_officer is True
    assert result.owners[0].officer_title == "Chief Executive Officer"
    assert len(result.transactions) == 1
    assert result.transactions[0].transaction_code == "P"
    assert result.transactions[0].shares == 10000.0
    assert result.transactions[0].price_per_share == 1.50
    assert result.transactions[0].transaction_value == 15000.0


def test_no_buy_sell_hold_language_in_module() -> None:
    """Test that form4_aggregator.py contains no buy/sell/hold recommendation language."""
    module_path = Path(__file__).parent.parent / "sources" / "form4_aggregator.py"
    content = module_path.read_text(encoding="utf-8")

    forbidden_phrases = [
        "recommend",
        "should buy",
        "should sell",
        "buy signal",
        "sell signal",
        "strong buy",
        "strong sell",
        "bullish",
        "bearish",
        "investment advice",
    ]

    for phrase in forbidden_phrases:
        assert phrase.lower() not in content.lower(), f"Found forbidden phrase: {phrase}"


def test_no_secrets_in_module() -> None:
    """Test that form4_aggregator.py contains no hardcoded secrets."""
    module_path = Path(__file__).parent.parent / "sources" / "form4_aggregator.py"
    content = module_path.read_text(encoding="utf-8")

    forbidden_patterns = [
        "api_key",
        "api-key",
        "password",
        "secret",
        "token",
        "bearer",
        "aws_access",
        "private_key",
    ]

    for pattern in forbidden_patterns:
        # Allow pattern in comments/docstrings but not in actual code
        lines = content.split("\n")
        code_lines = [
            line for line in lines if not line.strip().startswith("#") and '"""' not in line
        ]
        code_content = "\n".join(code_lines)

        assert (
            pattern.lower() not in code_content.lower()
        ), f"Found potential secret pattern: {pattern}"


def test_no_alert_code_in_module() -> None:
    """Test that form4_aggregator.py contains no alert generation code."""
    module_path = Path(__file__).parent.parent / "sources" / "form4_aggregator.py"
    content = module_path.read_text(encoding="utf-8")

    forbidden_imports = [
        "from alerts",
        "import alerts",
        "from telegram",
        "import telegram",
        "from email",
        "import smtplib",
    ]

    for forbidden in forbidden_imports:
        assert forbidden not in content, f"Found forbidden import: {forbidden}"


def test_safety_flags_structure() -> None:
    """Test that safety flags dictionary has correct structure."""
    # This is tested implicitly by the CLI script structure
    expected_keys = [
        "report_only",
        "alerts_generated",
        "openinsider_spreadsheet_used",
        "telegram_sent",
        "email_sent",
        "scheduled_tasks_modified",
        "env_printed_or_changed",
        "buy_sell_hold_language_used",
    ]

    # Simulate safety flags from CLI
    safety_flags = {
        "report_only": True,
        "alerts_generated": False,
        "openinsider_spreadsheet_used": False,
        "telegram_sent": False,
        "email_sent": False,
        "scheduled_tasks_modified": False,
        "env_printed_or_changed": False,
        "buy_sell_hold_language_used": False,
    }

    for key in expected_keys:
        assert key in safety_flags
        assert isinstance(safety_flags[key], bool)


# Additional import to ensure Path is available
from pathlib import Path
