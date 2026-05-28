"""SEC Form 4 connector -- deterministic retrieval of recent insider-trading filings.

Uses the EDGAR full-text search system (EFTS) at efts.sec.gov to find
Form 4 filings published in the last 24 hours.  For each filing, fetches
the filing index page from sec.gov to extract basic metadata.

Limitations:
  - EFTS returns filing metadata but not full XML parsing of every field.
    The connector extracts what is available from the search results and
    filing index pages.  Full XML parsing of individual Form 4 documents
    can be added in a future iteration.
  - Results are limited to the first page of EFTS results (typically 10-40
    filings).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from evidence.schema import SourceEvidence, SourceFetchResult
from sources.base import BaseConnector
from sources.sec_common import sec_fetch, utcnow_iso


_EFTS_SEARCH_URL = (
    "https://efts.sec.gov/LATEST/search-index"
    "?q=%22&forms=4&dateRange=custom"
    "&startdt={start}&enddt={end}"
)


class SecForm4Connector(BaseConnector):
    """Fetch recent Form 4 insider-trading filings from SEC EDGAR."""

    def fetch(self) -> SourceFetchResult:
        """Query EFTS for Form 4 filings from the last 24 hours."""
        now = datetime.now(timezone.utc)
        end_date = now.strftime("%Y-%m-%d")
        start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")

        url = _EFTS_SEARCH_URL.format(start=start_date, end=end_date)

        resp = sec_fetch(url, cache_max_age=3600)

        if not resp["ok"]:
            return SourceFetchResult.failure(
                source_name="sec_form4",
                error_type="http_error",
                error_message=resp["error"] or "Unknown error",
            )

        try:
            data = json.loads(resp["body"])
        except json.JSONDecodeError as e:
            return SourceFetchResult.failure(
                source_name="sec_form4",
                error_type="parse_error",
                error_message=f"Invalid JSON from EFTS: {e}",
            )

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return SourceFetchResult(
                ok=True,
                source_name="sec_form4",
                evidence=[],
            )

        evidence_list: list[SourceEvidence] = []
        for hit in hits[:20]:  # Limit to first 20 results
            source = hit.get("_source", {})
            filing_id = hit.get("_id", "")

            # Extract available fields from EFTS hit
            file_date = source.get("file_date", "")
            display_names = source.get("display_names", [])
            entity_name = source.get("entity_name", "")
            file_num = source.get("file_num", "")
            period_of_report = source.get("period_of_report", "")

            # Build the EDGAR filing URL from the filing ID
            # EFTS _id is typically the accession number
            accession_clean = filing_id.replace("-", "")
            cik_match = re.search(r"/(\d+)/", source.get("file_path", ""))
            cik = cik_match.group(1) if cik_match else ""

            source_url = ""
            if cik and filing_id:
                source_url = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{cik}/{accession_clean}/{filing_id}-index.htm"
                )

            evidence_list.append(
                SourceEvidence(
                    source_type="sec_form4",
                    source_name="SEC EDGAR Form 4",
                    source_url=source_url or url,
                    retrieved_at=utcnow_iso(),
                    canonical_id=filing_id or None,
                    raw_excerpt=json.dumps(source)[:2000],
                    normalized={
                        "accession_number": filing_id,
                        "cik": cik,
                        "entity_name": entity_name,
                        "display_names": display_names,
                        "filing_date": file_date,
                        "period_of_report": period_of_report,
                        "file_num": file_num,
                    },
                    metadata={
                        "search_url": url,
                        "from_cache": resp["from_cache"],
                    },
                )
            )

        return SourceFetchResult(
            ok=True,
            source_name="sec_form4",
            evidence=evidence_list,
        )

    def format_for_prompt(self, result: SourceFetchResult) -> str:
        """Format Form 4 evidence as text for Claude's prompt."""
        if not result.ok:
            return (
                f"[SEC EDGAR Form 4 fetch FAILED: {result.error_message}]\n"
                "No live filing data is available for this run. "
                "Output a NEUTRAL signal with confidence 1."
            )

        if not result.evidence:
            return (
                "[SEC EDGAR Form 4: No filings found in the last 24 hours.]\n"
                "Output a NEUTRAL signal with confidence 1 and reason "
                "'no qualifying Form 4 insider buys in the last 24 hours'."
            )

        lines = [
            f"[SEC EDGAR Form 4: {len(result.evidence)} filings found "
            f"in the last 24 hours]",
            "",
        ]
        for i, ev in enumerate(result.evidence, 1):
            n = ev.normalized
            names = ", ".join(n.get("display_names", []))
            lines.append(
                f"{i}. {n.get('entity_name', '?')} | "
                f"Filed: {n.get('filing_date', '?')} | "
                f"Filers: {names or '?'} | "
                f"Accession: {n.get('accession_number', '?')}"
            )
            if ev.source_url:
                lines.append(f"   URL: {ev.source_url}")
            lines.append("")

        lines.append(
            "Analyze these filings. Filter to open-market purchases (code P) "
            ">= $100k by C-suite/directors. Pick the single most notable buy."
        )
        return "\n".join(lines)
