"""SEC 13F-HR connector -- deterministic retrieval of institutional holdings filings.

Uses data.sec.gov/submissions/ to find the most recent 13F-HR filing for
each configured manager CIK, then fetches the filing index to extract
basic metadata.

Limitations:
  - This connector fetches the filing index and metadata but does not fully
    parse the 13F InfoTable XML.  Full holdings parsing can be added in a
    future iteration.
  - Prior-period comparison requires cached data from a previous run.
    On first run, the connector returns current-period data only.
"""

from __future__ import annotations

import json

from evidence.schema import SourceEvidence, SourceFetchResult
from sources.base import BaseConnector
from sources.sec_common import sec_fetch, utcnow_iso


# Manager CIKs from the original prompt (maggie.py)
DEFAULT_MANAGERS: list[tuple[str, str]] = [
    ("Berkshire Hathaway", "0001067983"),
    ("Bridgewater Associates", "0001350694"),
    ("Renaissance Technologies", "0001037389"),
    ("Citadel Advisors", "0001423053"),
    ("Two Sigma Investments", "0001179392"),
]

_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


class Sec13FConnector(BaseConnector):
    """Fetch recent 13F-HR filings for configured institutional managers."""

    def __init__(
        self,
        managers: list[tuple[str, str]] | None = None,
    ) -> None:
        self.managers = managers or DEFAULT_MANAGERS

    def fetch(self) -> SourceFetchResult:
        """Fetch the latest 13F-HR filing metadata for each manager."""
        all_evidence: list[SourceEvidence] = []
        errors: list[str] = []

        for name, cik in self.managers:
            url = _SUBMISSIONS_URL.format(cik=cik)
            resp = sec_fetch(url, cache_max_age=86400)  # 24h cache

            if not resp["ok"]:
                errors.append(f"{name} (CIK {cik}): {resp['error']}")
                continue

            try:
                data = json.loads(resp["body"])
            except json.JSONDecodeError as e:
                errors.append(f"{name} (CIK {cik}): JSON parse error: {e}")
                continue

            # Find the most recent 13F-HR in recent filings
            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            accessions = recent.get("accessionNumber", [])
            dates = recent.get("filingDate", [])
            primary_docs = recent.get("primaryDocument", [])
            report_dates = recent.get("reportDate", [])

            filing_found = False
            for idx, form in enumerate(forms):
                if form in ("13F-HR", "13F-HR/A"):
                    accession = accessions[idx] if idx < len(accessions) else ""
                    filing_date = dates[idx] if idx < len(dates) else ""
                    report_date = (
                        report_dates[idx] if idx < len(report_dates) else ""
                    )
                    primary_doc = (
                        primary_docs[idx] if idx < len(primary_docs) else ""
                    )

                    accession_clean = accession.replace("-", "")
                    source_url = (
                        f"https://www.sec.gov/Archives/edgar/data/"
                        f"{cik.lstrip('0')}/{accession_clean}/"
                        f"{accession}-index.htm"
                    )

                    all_evidence.append(
                        SourceEvidence(
                            source_type="sec_13f",
                            source_name=f"SEC 13F-HR: {name}",
                            source_url=source_url,
                            retrieved_at=utcnow_iso(),
                            canonical_id=accession or None,
                            raw_excerpt=json.dumps(
                                {
                                    "form": form,
                                    "accession": accession,
                                    "filingDate": filing_date,
                                    "reportDate": report_date,
                                }
                            ),
                            normalized={
                                "manager_name": name,
                                "manager_cik": cik,
                                "accession_number": accession,
                                "form_type": form,
                                "filing_date": filing_date,
                                "report_period": report_date,
                                "primary_document": primary_doc,
                            },
                            metadata={
                                "submissions_url": url,
                                "from_cache": resp["from_cache"],
                            },
                        )
                    )
                    filing_found = True
                    break  # Only need the most recent 13F

            if not filing_found:
                errors.append(f"{name} (CIK {cik}): No 13F-HR filing found")

        if not all_evidence and errors:
            return SourceFetchResult.failure(
                source_name="sec_13f",
                error_type="fetch_error",
                error_message="; ".join(errors),
            )

        result = SourceFetchResult(
            ok=True,
            source_name="sec_13f",
            evidence=all_evidence,
        )
        if errors:
            result.error_message = "; ".join(errors)
        return result

    def format_for_prompt(self, result: SourceFetchResult) -> str:
        """Format 13F evidence as text for Claude's prompt."""
        if not result.ok:
            return (
                f"[SEC EDGAR 13F-HR fetch FAILED: {result.error_message}]\n"
                "No live filing data is available for this run. "
                "Output a NEUTRAL signal with confidence 1."
            )

        if not result.evidence:
            return (
                "[SEC EDGAR 13F-HR: No recent filings found for tracked "
                "managers.]\nOutput a NEUTRAL signal with confidence 1."
            )

        lines = [
            f"[SEC EDGAR 13F-HR: {len(result.evidence)} manager filings found]",
            "",
        ]
        for i, ev in enumerate(result.evidence, 1):
            n = ev.normalized
            lines.append(
                f"{i}. {n.get('manager_name', '?')} (CIK {n.get('manager_cik', '?')})"
            )
            lines.append(
                f"   Form: {n.get('form_type', '?')} | "
                f"Filed: {n.get('filing_date', '?')} | "
                f"Period: {n.get('report_period', '?')}"
            )
            lines.append(f"   Accession: {n.get('accession_number', '?')}")
            if ev.source_url:
                lines.append(f"   URL: {ev.source_url}")
            lines.append("")

        if result.error_message:
            lines.append(f"[Partial errors: {result.error_message}]")
            lines.append("")

        lines.append(
            "Analyze these 13F-HR filings. Identify notable position changes "
            ">= $50M: NEW POSITION, INCREASED >= 25%, or EXITED. "
            "Pick the single most notable move."
        )
        return "\n".join(lines)
