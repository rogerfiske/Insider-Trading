"""Tests for MAIA Form 4 XML parsing with submission text extraction.

These tests verify that the Form 4 parser can successfully extract and parse
XML ownership documents from SEC submission text files, which is the primary
method used for recent Form 4 filings.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from sources.sec_form4_details import fetch_and_parse_form4


def test_fetch_and_parse_form4_from_submission_text():
    """Test successful parsing from submission text file with embedded XML."""
    # Mock submission text file response (primary strategy)
    mock_submission_text = """<SEC-DOCUMENT>0001878313-26-000062.txt
<TYPE>4
<SEQUENCE>1
<FILENAME>xslF345X06/form4.xml
<DESCRIPTION>FORM 4 SUBMISSION
<TEXT>
<XML>
<?xml version="1.0"?>
<ownershipDocument>
    <schemaVersion>X0609</schemaVersion>
    <documentType>4</documentType>
    <periodOfReport>2026-06-01</periodOfReport>
    <issuer>
        <issuerCik>0001878313</issuerCik>
        <issuerName>MAIA Biotechnology, Inc.</issuerName>
        <issuerTradingSymbol>MAIA</issuerTradingSymbol>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerCik>0001913257</rptOwnerCik>
            <rptOwnerName>Test Owner</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
            <isOfficer>1</isOfficer>
            <officerTitle>CEO</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
            <transactionDate>
                <value>2026-06-01</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>
                    <value>P</value>
                </transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>72700</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>1.3877</value>
                </transactionPricePerShare>
                <transactionAcquiredDisposedCode>
                    <value>A</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction>
                    <value>1000000</value>
                </sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership>
                    <value>D</value>
                </directOrIndirectOwnership>
            </ownershipNature>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>
</XML>
</TEXT>
</SEC-DOCUMENT>"""

    with patch("sources.sec_form4_details.sec_fetch") as mock_fetch:
        # Mock successful .txt file fetch
        mock_fetch.return_value = {
            "ok": True,
            "body": mock_submission_text,
        }

        details = fetch_and_parse_form4(
            accession_number="0001878313-26-000062",
            cik="0001878313",
            primary_document="xslF345X06/form4.xml",
        )

    assert details.parse_status == "success"
    assert details.issuer_cik == "0001878313"
    assert details.issuer_name == "MAIA Biotechnology, Inc."
    assert details.ticker == "MAIA"
    assert len(details.owners) == 1
    assert details.owners[0].name == "Test Owner"
    assert details.owners[0].is_director is True
    assert details.owners[0].is_officer is True
    assert details.owners[0].officer_title == "CEO"
    assert len(details.transactions) == 1
    assert details.transactions[0].transaction_code == "P"
    assert details.transactions[0].shares == 72700.0
    assert details.transactions[0].price_per_share == 1.3877


def test_fetch_and_parse_form4_no_xml_in_submission():
    """Test fallback when submission text has no XML block."""
    mock_submission_text = """<SEC-DOCUMENT>0001878313-26-000062.txt
<TYPE>4
<SEQUENCE>1
No XML block in this submission.
</SEC-DOCUMENT>"""

    with patch("sources.sec_form4_details.sec_fetch") as mock_fetch:
        # Mock .txt file with no XML, then fail on other attempts
        def side_effect(url, **kwargs):
            if url.endswith(".txt"):
                return {"ok": True, "body": mock_submission_text}
            else:
                return {"ok": False, "error": "HTTP 404: Not Found"}

        mock_fetch.side_effect = side_effect

        details = fetch_and_parse_form4(
            accession_number="0001878313-26-000062",
            cik="0001878313",
            primary_document="xslF345X06/form4.xml",
        )

    assert details.parse_status == "failed"
    assert details.error_type == "document_not_found"


def test_fetch_and_parse_form4_all_strategies_fail():
    """Test error handling when all document retrieval strategies fail."""
    with patch("sources.sec_form4_details.sec_fetch") as mock_fetch:
        # All fetch attempts fail
        mock_fetch.return_value = {
            "ok": False,
            "error": "HTTP 404: Not Found",
        }

        details = fetch_and_parse_form4(
            accession_number="0001878313-26-000062",
            cik="0001878313",
            primary_document="xslF345X06/form4.xml",
        )

    assert details.parse_status == "failed"
    assert details.error_type == "document_not_found"
    assert "Could not locate XML ownership document" in details.error_message


def test_fetch_and_parse_form4_html_not_xml():
    """Test that HTML from XSLT transform is rejected."""
    mock_html = """<!DOCTYPE html>
<html><head><title>SEC FORM 4</title></head>
<body>This is HTML, not XML</body></html>"""

    with patch("sources.sec_form4_details.sec_fetch") as mock_fetch:
        def side_effect(url, **kwargs):
            if url.endswith(".txt"):
                return {"ok": False, "error": "HTTP 404"}
            else:
                return {"ok": True, "body": mock_html}

        mock_fetch.side_effect = side_effect

        details = fetch_and_parse_form4(
            accession_number="0001878313-26-000062",
            cik="0001878313",
            primary_document="xslF345X06/form4.xml",
        )

    # Should not return success status for HTML
    # Parser may return "partial" or "failed" depending on XML structure
    assert details.parse_status != "success"
    assert len(details.transactions) == 0
