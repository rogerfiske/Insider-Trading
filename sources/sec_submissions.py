"""SEC issuer-specific submissions retrieval -- fetch filing history for a specific CIK.

Uses SEC EDGAR submissions JSON API to retrieve the complete filing history
for a specific issuer, filtered by form type and date range.

Example:
    https://data.sec.gov/submissions/CIK0001878313.json

This provides issuer-specific filings instead of global recent filing feeds.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sources.sec_common import sec_fetch


@dataclass
class SecSubmissionFiling:
    """Represents one filing entry from an issuer's SEC submissions history.

    Attributes:
        cik: Issuer CIK (with leading zeros preserved)
        cik_no_leading_zeros: Issuer CIK as integer string
        accession_number: Full accession number with dashes (e.g., "0001234567-23-000123")
        accession_no_dashes: Accession number without dashes (for URLs)
        form: Form type (e.g., "4", "13F-HR", "10-K")
        filing_date: Filing date (YYYY-MM-DD)
        report_date: Report date/period of report (YYYY-MM-DD or empty)
        acceptance_datetime: Acceptance datetime (ISO format or empty)
        primary_document: Primary document filename (e.g., "form4.xml")
        primary_doc_description: Description of primary document
        source_url: SEC data.sec.gov submissions JSON URL
        archive_directory_url: SEC Archives directory URL for this filing
        primary_document_url: Full URL to primary document
    """

    cik: str
    cik_no_leading_zeros: str
    accession_number: str
    accession_no_dashes: str
    form: str
    filing_date: str
    report_date: str
    acceptance_datetime: str
    primary_document: str
    primary_doc_description: str
    source_url: str
    archive_directory_url: str
    primary_document_url: str


def fetch_company_submissions(cik: str) -> dict[str, any]:
    """Fetch issuer-specific SEC submissions JSON for a CIK.

    Args:
        cik: SEC Central Index Key (with or without leading zeros)

    Returns:
        Parsed JSON response from SEC data.sec.gov/submissions/CIK{cik}.json

    Example:
        >>> result = fetch_company_submissions("0001878313")
        >>> result["ok"]
        True
        >>> result["body"]["cik"]
        "1878313"
    """
    # Ensure CIK is padded to 10 digits for SEC API
    cik_padded = cik.zfill(10)

    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

    # Use 24-hour cache for submissions data (relatively static)
    resp = sec_fetch(url, cache_max_age=86400)

    if not resp["ok"]:
        return {
            "ok": False,
            "error": resp.get("error", "Unknown error"),
            "url": url,
        }

    try:
        data = json.loads(resp["body"])
        return {
            "ok": True,
            "body": data,
            "url": url,
            "from_cache": resp.get("from_cache", False),
        }
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "error": f"Invalid JSON from SEC submissions: {e}",
            "url": url,
        }


def get_form4_filings_for_cik(cik: str, lookback_days: int) -> list[SecSubmissionFiling]:
    """Return issuer-specific Form 4 filings within a lookback window.

    Args:
        cik: SEC Central Index Key (with or without leading zeros)
        lookback_days: Number of days to look back from today

    Returns:
        List of SecSubmissionFiling objects for Form 4 filings within the lookback window,
        sorted by filing date (most recent first)

    Example:
        >>> filings = get_form4_filings_for_cik("0001878313", 365)
        >>> len(filings)
        3
        >>> filings[0].form
        "4"
    """
    result = fetch_company_submissions(cik)

    if not result["ok"]:
        # Return empty list on fetch failure (caller should check for this)
        return []

    body = result["body"]

    # Extract filings.recent parallel arrays
    filings_recent = body.get("filings", {}).get("recent", {})

    if not filings_recent:
        return []

    # Parallel arrays (all same length)
    accession_numbers = filings_recent.get("accessionNumber", [])
    filing_dates = filings_recent.get("filingDate", [])
    report_dates = filings_recent.get("reportDate", [])
    acceptance_datetimes = filings_recent.get("acceptanceDateTime", [])
    forms = filings_recent.get("form", [])
    primary_documents = filings_recent.get("primaryDocument", [])
    primary_doc_descriptions = filings_recent.get("primaryDocDescription", [])

    # Calculate lookback cutoff date
    now = datetime.now(timezone.utc)
    cutoff_date = (now - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    # Extract CIK without leading zeros for URLs
    cik_padded = cik.zfill(10)
    cik_no_leading_zeros = str(int(cik))

    # Build list of Form 4 filings within lookback window
    form4_filings = []

    for i in range(len(accession_numbers)):
        form = forms[i] if i < len(forms) else ""
        filing_date = filing_dates[i] if i < len(filing_dates) else ""

        # Filter: must be Form 4 and within lookback window
        if form != "4":
            continue

        if filing_date < cutoff_date:
            continue

        # Extract filing details
        accession_number = accession_numbers[i]
        accession_no_dashes = accession_number.replace("-", "")
        report_date = report_dates[i] if i < len(report_dates) else ""
        acceptance_datetime = acceptance_datetimes[i] if i < len(acceptance_datetimes) else ""
        primary_document = primary_documents[i] if i < len(primary_documents) else ""
        primary_doc_description = primary_doc_descriptions[i] if i < len(primary_doc_descriptions) else ""

        # Construct SEC Archives URLs
        archive_directory_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_no_leading_zeros}/{accession_no_dashes}/"
        )

        primary_document_url = ""
        if primary_document:
            primary_document_url = archive_directory_url + primary_document

        # Build filing object
        filing = SecSubmissionFiling(
            cik=cik_padded,
            cik_no_leading_zeros=cik_no_leading_zeros,
            accession_number=accession_number,
            accession_no_dashes=accession_no_dashes,
            form=form,
            filing_date=filing_date,
            report_date=report_date,
            acceptance_datetime=acceptance_datetime,
            primary_document=primary_document,
            primary_doc_description=primary_doc_description,
            source_url=result["url"],
            archive_directory_url=archive_directory_url,
            primary_document_url=primary_document_url,
        )

        form4_filings.append(filing)

    # Sort by filing date (most recent first)
    form4_filings.sort(key=lambda f: f.filing_date, reverse=True)

    return form4_filings
