"""
Generic Ticker Synthesis Workflow (CP23C)

Generate comprehensive SEC-only research packets for any manually supplied ticker.

IMPLEMENTATION STATUS:
- Skeleton framework with CLI design ✓
- JSON schema integration ✓
- MAIA validation mode ✓
- TODO: Full SEC EDGAR extraction for arbitrary tickers
- TODO: Automatic CIK lookup
- TODO: Automatic 10-Q/10-K parsing
- TODO: Automatic Form 4 aggregation
- TODO: Clinical trial data extraction for biotech profile

SAFETY:
- SEC EDGAR public filings only
- NO Roger's uploaded MAIA spreadsheet
- NO OpenInsider data
- NO Telegram/email alerts
- NO scheduled task modification
- NO .env access
- NO buy/sell/hold recommendations

Usage:
    python scripts/ticker_synthesis_workflow.py --ticker MAIA --mode validation \\
        --output-dir docs/sample_reports/generic_ticker/MAIA

    python scripts/ticker_synthesis_workflow.py --ticker XYZ --cik 0001234567 \\
        --lookback-days 1460 --profile biotech_clinical \\
        --output-dir docs/sample_reports/generic_ticker/XYZ
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add sources directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sources"))

from ticker_synthesis_utils import (
    get_safety_flags,
    get_source_boundary,
    get_evidence_matrix_template,
    get_ticker_profile_type,
    get_overall_posture,
    load_maia_baseline,
    save_json_output,
    save_markdown_output,
    validate_safety_flags,
    validate_no_recommendation_language,
)


class TickerSynthesisWorkflow:
    """Generic ticker synthesis workflow generator."""

    def __init__(self, ticker: str, cik: str, profile: str, lookback_days: int):
        """
        Initialize workflow.

        Args:
            ticker: Stock ticker symbol
            cik: SEC CIK number
            profile: Ticker profile type
            lookback_days: Insider activity lookback period
        """
        self.ticker = ticker.upper()
        self.cik = cik
        self.profile = profile
        self.lookback_days = lookback_days
        self.project_root = Path(__file__).parent.parent

    def load_maia_validation_data(self) -> dict:
        """
        Load approved MAIA data for validation mode.

        This demonstrates the generic framework by reformatting existing
        MAIA data according to the generic schema.
        """
        # Load approved MAIA synthesis packet
        maia_synthesis_path = (
            self.project_root
            / "docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.json"
        )

        if not maia_synthesis_path.exists():
            raise FileNotFoundError(
                f"MAIA synthesis packet not found: {maia_synthesis_path}"
            )

        with open(maia_synthesis_path, "r", encoding="utf-8") as f:
            maia_data = json.load(f)

        # Reformat to generic schema
        generic_data = {
            "ticker": maia_data["ticker"],
            "cik": maia_data["cik"],
            "company_name": maia_data.get("company_name", ""),
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "checkpoint": "CP23C",
            "ticker_profile": "biotech_clinical",
            "source_boundary": get_source_boundary("MAIA", "CP23C"),
            "modules": {
                "insider_activity": maia_data.get("insider_activity", {}),
                "capital_structure": maia_data.get("capital_structure", {}),
                "cash_runway": {
                    "official_10q_financials": maia_data.get("official_10q_financials", {}),
                    "cash_runway_scenarios": maia_data.get("cash_runway_scenarios", []),
                    "source_checkpoint": "CP23B-Fix3A",
                },
                "ownership_13dg": {
                    "filings_found": maia_data["capital_structure"].get("form_13d_13g_filings", 0),
                    "major_holders": [],
                    "note": "No 13D/13G filings found",
                },
                "ownership_13f": maia_data.get("institutional_visibility", {}),
                "form_144": maia_data.get("form_144", {}),
                "clinical_regulatory": {
                    "clinical_programs": maia_data.get("clinical_programs", []),
                    "milestone_calendar": maia_data.get("milestone_calendar", []),
                    "regulatory_designations": [],
                    "critical_unknowns": ["THIO-104 Phase 3 data timing not disclosed"],
                },
                "business_operations": "not_applicable",
                "market_confirmation": {
                    "reference_price": 1.50,
                    "reference_date": "2026-03-04",
                    "tracking_status": "Manual monitoring framework defined (CP23G)",
                    "note": "Requires manual price/volume entry; no live quote integration",
                },
            },
            "evidence_matrix": maia_data.get("evidence_matrix", []),
            "synthesis_scores": maia_data.get("synthesis_scores", {}),
            "monitoring_plan": maia_data.get("monitoring_plan", []),
            "open_questions": maia_data.get("open_questions", []),
            "limitations": maia_data.get("limitations", []),
            "safety": get_safety_flags(),
        }

        return generic_data

    def extract_sec_data(self, ticker: str, cik: str) -> dict:
        """
        Extract data from SEC EDGAR filings for arbitrary ticker.

        TODO: Implement full SEC extraction pipeline:
        1. Lookup CIK if not provided
        2. Fetch Form 4 filings for lookback period
        3. Parse Form 4 XML for insider transactions
        4. Fetch latest 10-Q for financials
        5. Parse 10-Q XBRL for cash, working capital, burn rate
        6. Fetch Form 13D/13G filings
        7. Fetch Form 144 filings
        8. For biotech profile: extract clinical trial data

        Args:
            ticker: Stock ticker symbol
            cik: SEC CIK number

        Returns:
            Dict with extracted data

        Raises:
            NotImplementedError: Full SEC extraction not yet implemented
        """
        raise NotImplementedError(
            f"Full SEC extraction for arbitrary tickers not yet implemented. "
            f"Use --mode validation with MAIA for framework demonstration."
        )

    def generate_synthesis_packet(self, mode: str) -> dict:
        """
        Generate comprehensive synthesis packet.

        Args:
            mode: 'validation' for MAIA validation, 'live' for SEC extraction

        Returns:
            Synthesis packet dict
        """
        if mode == "validation":
            if self.ticker != "MAIA":
                raise ValueError("Validation mode only supports MAIA ticker")
            return self.load_maia_validation_data()
        else:
            return self.extract_sec_data(self.ticker, self.cik)

    def generate_markdown_report(self, data: dict) -> str:
        """
        Generate markdown synthesis report.

        TODO: Implement full markdown template with Jinja2:
        - Executive summary
        - Insider activity section
        - Capital structure section
        - Cash runway analysis
        - Clinical/business progress
        - Evidence matrix table
        - Synthesis scores
        - Monitoring plan
        - Limitations and open questions

        Args:
            data: Synthesis packet dict

        Returns:
            Markdown content string
        """
        # Simplified markdown for skeleton
        md_content = f"""# {data['ticker']} Comprehensive Synthesis Packet

**Generated:** {data['generated_at']}
**CIK:** {data['cik']}
**Company:** {data.get('company_name', 'N/A')}
**Profile:** {data.get('ticker_profile', 'unknown')}
**Checkpoint:** {data.get('checkpoint', 'N/A')}

## Source Boundary

"""
        for source in data.get("source_boundary", []):
            md_content += f"- {source}\n"

        md_content += "\n## Executive Summary\n\n"
        md_content += f"**Overall Research Posture:** {data['synthesis_scores'].get('overall_research_posture', 'N/A')}\n\n"

        # Insider activity
        if "insider_activity" in data["modules"]:
            ia = data["modules"]["insider_activity"]
            md_content += f"""
## Insider Activity

- **Purchases:** {ia.get('open_market_purchases', 0)}
- **Sales:** {ia.get('open_market_sales', 0)}
- **Purchase Value:** ${ia.get('purchase_value_usd', 0):,.2f}
- **Distinct Buyers:** {ia.get('distinct_buyers', 0)}
- **Latest Purchase:** {ia.get('latest_purchase_date', 'N/A')}
- **Insider Score:** {ia.get('insider_score', 0)}/100
- **Rating:** {ia.get('insider_rating', 'N/A')}

"""

        # TODO: Add remaining sections from template
        md_content += "\n---\n\n*Generated by Generic Ticker Synthesis Workflow (CP23C)*\n"

        return md_content

    def run(self, output_dir: Path, mode: str = "validation") -> None:
        """
        Execute workflow and generate outputs.

        Args:
            output_dir: Output directory path
            mode: 'validation' for MAIA validation, 'live' for full SEC extraction
        """
        print(f"[START] Generic Ticker Synthesis Workflow")
        print(f"  Ticker: {self.ticker}")
        print(f"  CIK: {self.cik}")
        print(f"  Profile: {self.profile}")
        print(f"  Mode: {mode}")
        print(f"  Output: {output_dir}")

        # Create output directories
        synthesis_dir = output_dir / "synthesis"
        synthesis_dir.mkdir(parents=True, exist_ok=True)

        # Generate synthesis packet
        print("\n[STEP 1] Generating synthesis packet...")
        synthesis_data = self.generate_synthesis_packet(mode)

        # Validate safety
        print("\n[STEP 2] Validating safety flags...")
        safety_errors = validate_safety_flags(synthesis_data)
        if safety_errors:
            print("[ERROR] Safety validation failed:")
            for error in safety_errors:
                print(f"  - {error}")
            raise ValueError("Safety validation failed")
        print("[OK] Safety flags validated")

        # Validate no recommendation language
        print("\n[STEP 3] Validating no recommendation language...")
        rec_violations = validate_no_recommendation_language(synthesis_data)
        if rec_violations:
            print("[ERROR] Recommendation language detected:")
            for violation in rec_violations:
                print(f"  - {violation}")
            raise ValueError("Contains forbidden recommendation language")
        print("[OK] No recommendation language detected")

        # Save JSON
        print("\n[STEP 4] Saving JSON output...")
        json_path = synthesis_dir / f"{self.ticker}_synthesis_packet.json"
        save_json_output(synthesis_data, json_path)

        # Generate and save markdown
        print("\n[STEP 5] Generating markdown report...")
        md_content = self.generate_markdown_report(synthesis_data)
        md_path = synthesis_dir / f"{self.ticker}_synthesis_packet.md"
        save_markdown_output(md_content, md_path)

        # Validate MAIA baseline if applicable
        if self.ticker == "MAIA":
            print("\n[STEP 6] Validating MAIA baseline values...")
            baseline = load_maia_baseline()
            ia = synthesis_data["modules"]["insider_activity"]

            checks = {
                "insider_purchases": (ia["open_market_purchases"], baseline["insider_purchases"]),
                "insider_sales": (ia["open_market_sales"], baseline["insider_sales"]),
                "purchase_value_usd": (ia["purchase_value_usd"], baseline["purchase_value_usd"]),
                "distinct_buyers": (ia["distinct_buyers"], baseline["distinct_buyers"]),
            }

            all_valid = True
            for key, (actual, expected) in checks.items():
                if actual == expected:
                    print(f"[OK] {key}: {actual} == {expected}")
                else:
                    print(f"[FAIL] {key}: {actual} != {expected}")
                    all_valid = False

            if not all_valid:
                raise ValueError("MAIA baseline validation failed")
            print("[OK] MAIA baseline values preserved")

        print(f"\n[DONE] Synthesis workflow complete")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generic Ticker Synthesis Workflow"
    )
    parser.add_argument(
        "--ticker",
        required=True,
        help="Stock ticker symbol (e.g., MAIA, AAPL)",
    )
    parser.add_argument(
        "--cik",
        default="",
        help="SEC CIK number (optional for validation mode)",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=1460,
        help="Insider activity lookback period in days (default: 1460 = 4 years)",
    )
    parser.add_argument(
        "--profile",
        choices=[
            "biotech_clinical",
            "small_cap_operating_company",
            "pre_revenue_company",
            "unknown_profile",
        ],
        default="unknown_profile",
        help="Ticker profile type for module activation",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory (e.g., docs/sample_reports/generic_ticker/MAIA)",
    )
    parser.add_argument(
        "--mode",
        choices=["validation", "live"],
        default="validation",
        help="Mode: 'validation' for MAIA validation (uses existing data), 'live' for SEC extraction (not yet implemented)",
    )

    args = parser.parse_args()

    # Validation mode specific checks
    if args.mode == "validation" and args.ticker.upper() != "MAIA":
        print("[ERROR] Validation mode only supports MAIA ticker")
        print("  Use: --ticker MAIA --mode validation")
        sys.exit(1)

    if args.mode == "live":
        print("[ERROR] Live SEC extraction mode not yet implemented")
        print("  Use: --mode validation with --ticker MAIA to demonstrate framework")
        sys.exit(1)

    # Create workflow instance
    workflow = TickerSynthesisWorkflow(
        ticker=args.ticker,
        cik=args.cik or "0001878313",  # MAIA CIK for validation
        profile=args.profile,
        lookback_days=args.lookback_days,
    )

    # Execute workflow
    output_dir = Path(args.output_dir)
    workflow.run(output_dir, mode=args.mode)


if __name__ == "__main__":
    main()
