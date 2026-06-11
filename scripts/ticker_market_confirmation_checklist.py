"""
Generic Ticker Market Confirmation Checklist Generator (CP23C)

Generate market confirmation tracking frameworks.

IMPLEMENTATION STATUS:
- Skeleton framework with CLI design ✓
- JSON schema integration ✓
- MAIA validation mode ✓
- CSV observation template generation ✓
- TODO: Generic checklist adaptation for different market cap/liquidity profiles

SAFETY:
- Manual tracking only, no live market data integration
- NO Telegram/email/alerts

Usage:
    python scripts/ticker_market_confirmation_checklist.py --ticker MAIA \\
        --mode validation \\
        --input-dir docs/sample_reports/generic_ticker/MAIA \\
        --output-dir docs/sample_reports/generic_ticker/MAIA
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "sources"))

from ticker_synthesis_utils import (
    get_safety_flags,
    save_json_output,
    save_markdown_output,
)


class TickerMarketConfirmationChecklist:
    """Generic ticker market confirmation framework generator."""

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.project_root = Path(__file__).parent.parent

    def load_maia_validation_data(self) -> dict:
        """Load approved MAIA market confirmation plan."""
        maia_path = (
            self.project_root
            / "docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_plan.json"
        )

        if not maia_path.exists():
            raise FileNotFoundError(f"MAIA market confirmation plan not found: {maia_path}")

        with open(maia_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_nvda_skeleton_data(self) -> dict:
        """
        Generate skeleton NVDA market confirmation plan for second validation ticker (CP23I).
        Minimal market confirmation structure without MAIA-specific price levels.
        """
        return {
            "ticker": "NVDA",
            "cik": "not_available",
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "checkpoint": "CP23I",
            "purpose": "Skeleton validation for generic market confirmation framework",
            "baseline": {
                "synthesis_checkpoint": "CP23I",
                "reference_price_source": "not_available - skeleton validation mode",
                "baseline_date": "not_available",
            },
            "reference_levels": [
                {
                    "level_type": "skeleton_placeholder",
                    "price_usd": "not_available",
                    "significance": "Placeholder for validation testing only",
                    "source": "not_available - skeleton mode",
                }
            ],
            "weekly_checklist": [
                "Review closing price and daily volume",
                "Note any significant price or volume deviations",
                "Check for material SEC filings or news events",
            ],
            "observation_frequency": "weekly",
            "manual_entry_required": True,
            "automation_gaps": [
                "Price/volume data collection requires manual CSV entry",
                "No automated market data integration in skeleton mode",
            ],
            "limitations": [
                "Skeleton validation mode - no live market data",
                "NVDA selected only to validate framework handles non-biotech ticker profiles",
                "No MAIA-specific $1.50 offering price reference",
            ],
            "safety": get_safety_flags(),
        }

    def generate_observation_template_csv(self, output_path: Path) -> None:
        """Generate CSV template for manual price/volume observations."""
        headers = [
            "Date",
            "Closing_Price_USD",
            "Daily_Volume",
            "Intraday_High_USD",
            "Intraday_Low_USD",
            "Notes",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            # Add one sample row
            writer.writerow(["2026-06-10", "", "", "", "", "Manual entry required"])

        print(f"[OK] Created observation template CSV: {output_path}")

    def run(self, input_dir: Path, output_dir: Path, mode: str = "validation") -> None:
        """Execute market confirmation checklist generation."""
        print(f"[START] Generic Ticker Market Confirmation Checklist")
        print(f"  Ticker: {self.ticker}")
        print(f"  Mode: {mode}")

        # Load synthesis packet
        synthesis_path = input_dir / "synthesis" / f"{self.ticker}_synthesis_packet.json"
        if not synthesis_path.exists():
            raise FileNotFoundError(f"Synthesis packet not found: {synthesis_path}")

        # Generate market confirmation plan
        if mode == "validation":
            if self.ticker == "MAIA":
                mc_data = self.load_maia_validation_data()
            elif self.ticker == "NVDA":
                mc_data = self.generate_nvda_skeleton_data()
            else:
                raise ValueError(f"Validation mode only supports MAIA and NVDA tickers, got: {self.ticker}")
        else:
            raise NotImplementedError("Generic market confirmation not yet implemented for live mode")

        # Save outputs
        mc_dir = output_dir / "market_confirmation"
        mc_dir.mkdir(parents=True, exist_ok=True)

        json_path = mc_dir / f"{self.ticker}_market_confirmation_plan.json"
        save_json_output(mc_data, json_path)

        # Generate observation CSV template
        csv_path = mc_dir / f"{self.ticker}_market_observation_template.csv"
        self.generate_observation_template_csv(csv_path)

        # TODO: Generate markdown checklist
        md_content = f"# {self.ticker} Market Confirmation Checklist\n\nGenerated: {datetime.now(timezone.utc).isoformat()}\n"
        md_path = mc_dir / f"{self.ticker}_market_confirmation_checklist.md"
        save_markdown_output(md_content, md_path)

        print(f"[DONE] Market confirmation checklist complete")


def main():
    parser = argparse.ArgumentParser(description="Generic Ticker Market Confirmation")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", choices=["validation", "live"], default="validation")

    args = parser.parse_args()

    checklist = TickerMarketConfirmationChecklist(args.ticker)
    checklist.run(Path(args.input_dir), Path(args.output_dir), args.mode)


if __name__ == "__main__":
    main()
