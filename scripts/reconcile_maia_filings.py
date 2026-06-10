"""Manual MAIA SEC filing reconciliation script.

Downloads and extracts specific data points from MAIA March 2026 filings
to correct the CP23A capital structure report.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# SAFETY: Force dry-run mode
os.environ["ROSS_DRY_RUN"] = "true"
os.environ["ALERT_ENABLE_TELEGRAM"] = "false"
os.environ["ALERT_ENABLE_EMAIL"] = "false"

from sources.sec_common import sec_fetch


def fetch_and_save_filing(url: str, output_file: Path) -> dict:
    """Fetch a SEC filing and save to file for manual review."""
    print(f"Fetching: {url}")
    result = sec_fetch(url, cache_max_age=86400)

    if result["ok"]:
        output_file.write_text(result["body"], encoding="utf-8")
        print(f"  Saved to: {output_file}")
        print(f"  Length: {len(result['body'])} chars")
        return {"ok": True, "body": result["body"], "file": str(output_file)}
    else:
        print(f"  ERROR: {result.get('error', 'Unknown error')}")
        return {"ok": False, "error": result.get("error", "Unknown")}


def extract_424b5_march_2_data(text: str) -> dict:
    """Extract offering details from March 2 424B5."""
    data = {}

    # Look for offering table or key terms
    # Common patterns in 424B5 filings

    # Gross proceeds pattern
    gross_match = re.search(
        r"[Gg]ross\s+[Pp]roceeds.*?\$\s*([0-9,]+(?:\.[0-9]+)?)\s*million",
        text,
        re.IGNORECASE
    )
    if gross_match:
        data["gross_proceeds_million"] = gross_match.group(1).replace(",", "")

    # Net proceeds pattern
    net_match = re.search(
        r"[Nn]et\s+[Pp]roceeds.*?\$\s*([0-9,]+(?:\.[0-9]+)?)\s*million",
        text,
        re.IGNORECASE
    )
    if net_match:
        data["net_proceeds_million"] = net_match.group(1).replace(",", "")

    # Share count
    shares_match = re.search(
        r"([0-9,]+)\s+shares?\s+of\s+[Cc]ommon\s+[Ss]tock",
        text
    )
    if shares_match:
        data["common_shares"] = shares_match.group(1).replace(",", "")

    # Pre-funded warrants
    prefunded_match = re.search(
        r"([0-9,]+)\s+[Pp]re-[Ff]unded\s+[Ww]arrants",
        text
    )
    if prefunded_match:
        data["prefunded_warrants"] = prefunded_match.group(1).replace(",", "")

    # Common warrants
    warrant_match = re.search(
        r"([0-9,]+)\s+[Cc]ommon\s+[Ww]arrants",
        text
    )
    if warrant_match:
        data["common_warrants"] = warrant_match.group(1).replace(",", "")

    # Price per share
    price_match = re.search(
        r"[Pp]rice\s+[Pp]er\s+[Ss]hare.*?\$\s*([0-9]+(?:\.[0-9]+)?)",
        text
    )
    if price_match:
        data["price_per_share"] = price_match.group(1)

    # Warrant exercise price
    exercise_match = re.search(
        r"[Ee]xercise\s+[Pp]rice.*?\$\s*([0-9]+(?:\.[0-9]+)?)",
        text
    )
    if exercise_match:
        data["warrant_exercise_price"] = exercise_match.group(1)

    # Beneficial ownership blocker
    if "4.99%" in text or "9.99%" in text:
        if "beneficial ownership" in text.lower() or "blocker" in text.lower():
            data["blocker"] = "4.99% or 9.99% beneficial ownership limitation"

    return data


def extract_form_144_data(text: str) -> dict:
    """Extract details from Form 144 filing."""
    data = {}

    # Form 144 XML patterns
    # Issuer name
    issuer_match = re.search(r"<issuerName>([^<]+)</issuerName>", text, re.IGNORECASE)
    if issuer_match:
        data["issuer_name"] = issuer_match.group(1).strip()

    # Person reporting (seller)
    person_match = re.search(r"<rptOwnerName>([^<]+)</rptOwnerName>", text, re.IGNORECASE)
    if person_match:
        data["seller"] = person_match.group(1).strip()

    # Relationship to issuer
    relationship_match = re.search(r"<relationship>([^<]+)</relationship>", text, re.IGNORECASE)
    if relationship_match:
        data["relationship"] = relationship_match.group(1).strip()

    # Shares to be sold
    shares_match = re.search(r"<sharesToBeSold>([0-9,]+)</sharesToBeSold>", text, re.IGNORECASE)
    if shares_match:
        data["shares"] = shares_match.group(1).replace(",", "")

    # Date of proposed sale
    date_match = re.search(r"<dateOfProposedSale>([0-9-]+)</dateOfProposedSale>", text, re.IGNORECASE)
    if date_match:
        data["proposed_sale_date"] = date_match.group(1)

    # Approximate sale date (text field)
    approx_date_match = re.search(r"[Aa]pproximate.*?[Dd]ate.*?([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})", text)
    if approx_date_match:
        data["approximate_sale_date"] = approx_date_match.group(1)

    # Aggregate market value
    value_match = re.search(r"<aggregateMarketValue>([0-9,]+(?:\.[0-9]+)?)</aggregateMarketValue>", text, re.IGNORECASE)
    if value_match:
        data["market_value"] = value_match.group(1).replace(",", "")

    # Broker
    broker_match = re.search(r"<brokerName>([^<]+)</brokerName>", text, re.IGNORECASE)
    if broker_match:
        data["broker"] = broker_match.group(1).strip()

    return data


def main():
    """Main reconciliation execution."""

    # Create output directory
    output_dir = Path(__file__).parent.parent / "docs" / "sample_reports" / "maia_capital_structure" / "filings"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("MAIA SEC Filing Reconciliation")
    print("=" * 60)
    print()

    # Key filings to fetch
    filings = [
        {
            "name": "March 2 424B5",
            "url": "https://www.sec.gov/Archives/edgar/data/1878313/000149315226008571/form424b5.htm",
            "file": output_dir / "2026-03-02_424B5.html"
        },
        {
            "name": "March 4 424B5",
            "url": "https://www.sec.gov/Archives/edgar/data/1878313/000149315226008784/form424b5.htm",
            "file": output_dir / "2026-03-04_424B5.html"
        },
        {
            "name": "March 4 8-K",
            "url": "https://www.sec.gov/Archives/edgar/data/1878313/000149315226008897/form8-k.htm",
            "file": output_dir / "2026-03-04_8K.html"
        },
        {
            "name": "May 11 10-Q",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001878313&type=10-Q&dateb=&owner=exclude&count=1",
            "file": output_dir / "2026-05-11_10Q_search.html"
        },
        {
            "name": "Form 144 (2024-01-19)",
            "url": "https://www.sec.gov/cgi-bin/viewer?action=view&cik=1959173&accession_number=0001959173-24-000374&xbrl_type=v",
            "file": output_dir / "2024-01-19_Form144.html"
        },
    ]

    results = {}

    for filing in filings:
        result = fetch_and_save_filing(filing["url"], filing["file"])
        results[filing["name"]] = result
        print()

    # Extract data from March 2 424B5
    if results.get("March 2 424B5", {}).get("ok"):
        print("Extracting data from March 2 424B5...")
        text = results["March 2 424B5"]["body"]
        data = extract_424b5_march_2_data(text)

        print("Extracted data:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        print()

        # Save extracted data
        data_file = output_dir / "march_2_424b5_extracted.json"
        data_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Saved extracted data to: {data_file}")

    # Extract data from Form 144
    if results.get("Form 144 (2024-01-19)", {}).get("ok"):
        print("Extracting data from Form 144 (2024-01-19)...")
        text = results["Form 144 (2024-01-19)"]["body"]
        data = extract_form_144_data(text)

        print("Extracted data:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        print()

        # Save extracted data
        data_file = output_dir / "form_144_extracted.json"
        data_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Saved extracted data to: {data_file}")

    print()
    print("Reconciliation complete!")
    print(f"Review files in: {output_dir}")


if __name__ == "__main__":
    main()
