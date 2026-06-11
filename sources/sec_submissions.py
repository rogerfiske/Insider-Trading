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


def build_submissions_inventory(
    cik: str, lookback_days: int = 1460, max_recent: int = 100
) -> dict[str, any]:
    """Build comprehensive SEC submissions inventory for a CIK.

    Fetches SEC submissions data and builds an inventory of filing counts by form type,
    latest relevant filings, recent filings list, coverage flags, and evidence provenance.

    Args:
        cik: SEC Central Index Key (with or without leading zeros)
        lookback_days: Number of days to look back for coverage analysis (default 1460 = ~4 years)
        max_recent: Maximum number of recent filings to include in list (default 100)

    Returns:
        dict with keys:
            status: "retrieved" | "failed" | "degraded"
            data: dict with inventory fields (if retrieved)
            error: str | None (if failed)

    Example:
        >>> result = build_submissions_inventory("0001878313")
        >>> result["status"]
        "retrieved"
        >>> result["data"]["filing_counts_by_form"]["4"]
        12
    """
    from sources.sec_common import utcnow_iso

    # Fetch submissions data
    fetch_result = fetch_company_submissions(cik)

    if not fetch_result["ok"]:
        return {
            "status": "failed",
            "data": None,
            "error": fetch_result.get("error", "Unknown error fetching submissions"),
        }

    body = fetch_result["body"]
    source_url = fetch_result["url"]
    retrieved_at = utcnow_iso()

    # Extract filings.recent parallel arrays
    filings_recent = body.get("filings", {}).get("recent", {})

    if not filings_recent:
        return {
            "status": "degraded",
            "data": {
                "filing_counts_by_form": {},
                "latest_10k": None,
                "latest_10q": None,
                "latest_8k": None,
                "latest_form4": None,
                "latest_form144": None,
                "latest_13d_or_13g": None,
                "latest_13f_hr": None,
                "recent_filings": [],
                "coverage_flags": {
                    "has_form4": False,
                    "has_form144": False,
                    "has_13d_13g": False,
                    "has_10q": False,
                    "has_10k": False,
                    "has_8k": False,
                    "has_s3_or_offering_filing": False,
                    "has_13f_hr": False,
                },
                "source_url": source_url,
                "retrieved_at": retrieved_at,
            },
            "error": "No recent filings found in submissions data",
        }

    # Extract parallel arrays
    accession_numbers = filings_recent.get("accessionNumber", [])
    filing_dates = filings_recent.get("filingDate", [])
    report_dates = filings_recent.get("reportDate", [])
    forms = filings_recent.get("form", [])
    primary_documents = filings_recent.get("primaryDocument", [])
    file_numbers = filings_recent.get("fileNumber", [])
    film_numbers = filings_recent.get("filmNumber", [])

    # Calculate lookback cutoff date
    now = datetime.now(timezone.utc)
    cutoff_date = (now - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    # Extract CIK without leading zeros for URLs
    cik_padded = cik.zfill(10)
    cik_no_leading_zeros = str(int(cik))

    # Build filing counts by form type (within lookback window)
    filing_counts_by_form: dict[str, int] = {}

    # Track latest filings for key forms
    latest_10k = None
    latest_10q = None
    latest_8k = None
    latest_form4 = None
    latest_form144 = None
    latest_13d_or_13g = None
    latest_13f_hr = None

    # Build recent filings list
    recent_filings = []

    # Process filings
    for i in range(len(accession_numbers)):
        if i >= len(forms):
            break

        form = forms[i]
        filing_date = filing_dates[i] if i < len(filing_dates) else ""
        accession_number = accession_numbers[i]
        report_date = report_dates[i] if i < len(report_dates) else ""
        primary_document = primary_documents[i] if i < len(primary_documents) else ""
        file_number = file_numbers[i] if i < len(file_numbers) else ""
        film_number = film_numbers[i] if i < len(film_numbers) else ""

        # Count within lookback window
        if filing_date >= cutoff_date:
            filing_counts_by_form[form] = filing_counts_by_form.get(form, 0) + 1

        # Build filing entry for recent list (up to max_recent)
        if len(recent_filings) < max_recent:
            accession_no_dashes = accession_number.replace("-", "")
            archive_directory_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik_no_leading_zeros}/{accession_no_dashes}/"
            )

            filing_entry = {
                "accession_number": accession_number,
                "filing_date": filing_date,
                "report_date": report_date,
                "form": form,
                "primary_document": primary_document,
                "file_number": file_number,
                "film_number": film_number,
                "archive_url": archive_directory_url,
            }

            recent_filings.append(filing_entry)

        # Track latest filings for key forms
        if form == "10-K" and latest_10k is None:
            latest_10k = {
                "accession_number": accession_number,
                "filing_date": filing_date,
                "form": form,
                "primary_document": primary_document,
            }
        elif form == "10-Q" and latest_10q is None:
            latest_10q = {
                "accession_number": accession_number,
                "filing_date": filing_date,
                "form": form,
                "primary_document": primary_document,
            }
        elif form == "8-K" and latest_8k is None:
            latest_8k = {
                "accession_number": accession_number,
                "filing_date": filing_date,
                "form": form,
                "primary_document": primary_document,
            }
        elif form == "4" and latest_form4 is None:
            latest_form4 = {
                "accession_number": accession_number,
                "filing_date": filing_date,
                "form": form,
                "primary_document": primary_document,
            }
        elif form == "144" and latest_form144 is None:
            latest_form144 = {
                "accession_number": accession_number,
                "filing_date": filing_date,
                "form": form,
                "primary_document": primary_document,
            }
        elif form in ("SC 13D", "SC 13G", "SC 13D/A", "SC 13G/A") and latest_13d_or_13g is None:
            latest_13d_or_13g = {
                "accession_number": accession_number,
                "filing_date": filing_date,
                "form": form,
                "primary_document": primary_document,
            }
        elif form in ("13F-HR", "13F-HR/A") and latest_13f_hr is None:
            latest_13f_hr = {
                "accession_number": accession_number,
                "filing_date": filing_date,
                "form": form,
                "primary_document": primary_document,
            }

    # Build coverage flags
    coverage_flags = {
        "has_form4": filing_counts_by_form.get("4", 0) > 0,
        "has_form144": filing_counts_by_form.get("144", 0) > 0,
        "has_13d_13g": any(
            filing_counts_by_form.get(f, 0) > 0
            for f in ("SC 13D", "SC 13G", "SC 13D/A", "SC 13G/A")
        ),
        "has_10q": filing_counts_by_form.get("10-Q", 0) > 0,
        "has_10k": filing_counts_by_form.get("10-K", 0) > 0,
        "has_8k": filing_counts_by_form.get("8-K", 0) > 0,
        "has_s3_or_offering_filing": any(
            filing_counts_by_form.get(f, 0) > 0
            for f in ("S-3", "S-1", "S-4", "S-8", "S-3/A", "S-1/A", "S-4/A", "S-8/A")
        ),
        "has_13f_hr": any(
            filing_counts_by_form.get(f, 0) > 0 for f in ("13F-HR", "13F-HR/A")
        ),
    }

    # Build inventory data
    inventory_data = {
        "filing_counts_by_form": filing_counts_by_form,
        "latest_10k": latest_10k,
        "latest_10q": latest_10q,
        "latest_8k": latest_8k,
        "latest_form4": latest_form4,
        "latest_form144": latest_form144,
        "latest_13d_or_13g": latest_13d_or_13g,
        "latest_13f_hr": latest_13f_hr,
        "recent_filings": recent_filings,
        "coverage_flags": coverage_flags,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
    }

    return {"status": "retrieved", "data": inventory_data, "error": None}
