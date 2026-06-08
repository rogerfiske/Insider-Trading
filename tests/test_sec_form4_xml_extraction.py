"""Tests for Form 4 XML extraction from submission text files."""

from __future__ import annotations

from sources.sec_form4_details import _extract_xml_from_submission


def test_extract_xml_from_submission_simple():
    """Test extraction of XML from submission text with simple structure."""
    submission_text = """<SEC-DOCUMENT>0001234567-26-000001.txt
<TYPE>4
<SEQUENCE>1
<FILENAME>primary_doc.xml
<DESCRIPTION>FORM 4 SUBMISSION
<TEXT>
<XML>
<?xml version="1.0"?>
<ownershipDocument>
    <schemaVersion>X0609</schemaVersion>
    <documentType>4</documentType>
    <periodOfReport>2026-06-01</periodOfReport>
</ownershipDocument>
</XML>
</TEXT>
</SEC-DOCUMENT>"""

    xml_content = _extract_xml_from_submission(submission_text)

    assert xml_content is not None
    assert "<?xml version=\"1.0\"?>" in xml_content
    assert "<ownershipDocument>" in xml_content
    assert "<periodOfReport>2026-06-01</periodOfReport>" in xml_content


def test_extract_xml_from_submission_case_insensitive():
    """Test that XML extraction is case-insensitive for tags."""
    submission_text = """<TEXT>
<xml>
<?xml version="1.0"?>
<ownershipDocument>
    <documentType>4</documentType>
</ownershipDocument>
</xml>
</TEXT>"""

    xml_content = _extract_xml_from_submission(submission_text)

    assert xml_content is not None
    assert "<ownershipDocument>" in xml_content


def test_extract_xml_from_submission_multiline():
    """Test extraction with multiline XML content."""
    submission_text = """<TEXT>
<XML>
<?xml version="1.0"?>
<ownershipDocument>
    <schemaVersion>X0609</schemaVersion>
    <documentType>4</documentType>
    <periodOfReport>2026-06-01</periodOfReport>
    <issuer>
        <issuerCik>0001878313</issuerCik>
        <issuerName>MAIA Biotechnology, Inc.</issuerName>
    </issuer>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Test Owner</rptOwnerName>
        </reportingOwnerId>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <securityTitle>
                <value>Common Stock</value>
            </securityTitle>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>
</XML>
</TEXT>"""

    xml_content = _extract_xml_from_submission(submission_text)

    assert xml_content is not None
    assert "<?xml version=\"1.0\"?>" in xml_content
    assert "<issuerCik>0001878313</issuerCik>" in xml_content
    assert "<rptOwnerName>Test Owner</rptOwnerName>" in xml_content
    assert "<nonDerivativeTable>" in xml_content


def test_extract_xml_from_submission_no_xml_block():
    """Test that None is returned when no XML block is found."""
    submission_text = """<SEC-DOCUMENT>0001234567-26-000001.txt
<TYPE>4
<SEQUENCE>1
This is plain text with no XML block.
</SEC-DOCUMENT>"""

    xml_content = _extract_xml_from_submission(submission_text)

    assert xml_content is None


def test_extract_xml_from_submission_empty():
    """Test that None is returned for empty submission text."""
    xml_content = _extract_xml_from_submission("")

    assert xml_content is None


def test_extract_xml_from_submission_whitespace_handling():
    """Test that extracted XML is trimmed of surrounding whitespace."""
    submission_text = """<TEXT>
<XML>

    <?xml version="1.0"?>
    <ownershipDocument>
        <documentType>4</documentType>
    </ownershipDocument>

</XML>
</TEXT>"""

    xml_content = _extract_xml_from_submission(submission_text)

    assert xml_content is not None
    # Should be trimmed
    assert xml_content.startswith("<?xml")
    assert xml_content.endswith("</ownershipDocument>")
