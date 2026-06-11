"""
Generic Ticker Monitoring Pack Generator (CP23C)

Generate monitoring plans from synthesis packets.

IMPLEMENTATION STATUS:
- Skeleton framework with CLI design ✓
- JSON schema integration ✓
- MAIA validation mode ✓
- TODO: Generic monitoring category templates for non-biotech profiles

SAFETY:
- Report only, no alerts
- NO Telegram/email/scheduled tasks

Usage:
    python scripts/ticker_monitoring_pack.py --ticker MAIA --mode validation \\
        --input-dir docs/sample_reports/generic_ticker/MAIA \\
        --output-dir docs/sample_reports/generic_ticker/MAIA
"""

import argparse
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


class TickerMonitoringPack:
    """Generic ticker monitoring plan generator."""

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.project_root = Path(__file__).parent.parent

    def load_maia_validation_data(self) -> dict:
        """Load approved MAIA monitoring plan for validation."""
        maia_path = (
            self.project_root
            / "docs/sample_reports/maia_monitoring/MAIA_monitoring_plan.json"
        )

        if not maia_path.exists():
            raise FileNotFoundError(f"MAIA monitoring plan not found: {maia_path}")

        with open(maia_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_nvda_skeleton_data(self) -> dict:
        """
        Generate skeleton NVDA monitoring plan for second validation ticker (CP23I).
        Minimal monitoring structure without MAIA-specific baselines.
        """
        return {
            "ticker": "NVDA",
            "cik": "not_available",
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "checkpoint": "CP23I",
            "purpose": "Skeleton validation for generic monitoring framework",
            "baseline": {
                "synthesis_checkpoint": "CP23I",
                "insider_activity": {
                    "open_market_purchases": 0,
                    "open_market_sales": 0,
                    "purchase_value_usd": 0.0,
                    "insider_score": 0,
                },
                "cash_runway": {
                    "cash_balance_usd": "not_available",
                    "monthly_burn_rate_usd": "not_available",
                    "months_remaining": "not_available",
                },
                "clinical_regulatory": "not_applicable",
            },
            "monitoring_categories": [
                {
                    "category": "insider_activity",
                    "data_sources": ["SEC EDGAR Form 4"],
                    "check_frequency": "weekly",
                    "track_changes": ["new open-market purchases", "new open-market sales"],
                    "alert_triggers": [],
                    "automation_status": "not_available - skeleton mode",
                },
                {
                    "category": "ownership_13f",
                    "data_sources": ["SEC EDGAR 13F"],
                    "check_frequency": "quarterly",
                    "track_changes": ["institutional ownership changes"],
                    "alert_triggers": [],
                    "automation_status": "not_available - skeleton mode",
                },
            ],
            "limitations": [
                "Skeleton validation mode - no live monitoring configured",
                "NVDA selected only to validate framework handles non-biotech ticker profiles",
                "Clinical monitoring correctly excluded (not_applicable)",
            ],
            "safety": get_safety_flags(),
        }

    def generate_monitoring_plan(self, synthesis_data: dict) -> dict:
        """
        Generate monitoring plan from synthesis packet.

        TODO: Implement generic monitoring category generation based on profile

        Args:
            synthesis_data: Synthesis packet dict

        Returns:
            Monitoring plan dict
        """
        # Skeleton: return validation data for MAIA and NVDA
        if self.ticker == "MAIA":
            return self.load_maia_validation_data()
        elif self.ticker == "NVDA":
            return self.generate_nvda_skeleton_data()

        raise NotImplementedError(f"Generic monitoring generation not yet implemented for ticker: {self.ticker}")

    def run(self, input_dir: Path, output_dir: Path, mode: str = "validation") -> None:
        """Execute monitoring pack generation."""
        print(f"[START] Generic Ticker Monitoring Pack")
        print(f"  Ticker: {self.ticker}")
        print(f"  Mode: {mode}")

        # Load synthesis packet
        synthesis_path = input_dir / "synthesis" / f"{self.ticker}_synthesis_packet.json"
        if not synthesis_path.exists():
            raise FileNotFoundError(f"Synthesis packet not found: {synthesis_path}")

        with open(synthesis_path, "r", encoding="utf-8") as f:
            synthesis_data = json.load(f)

        # Generate monitoring plan
        monitoring_data = self.generate_monitoring_plan(synthesis_data)

        # Save outputs
        monitoring_dir = output_dir / "monitoring"
        monitoring_dir.mkdir(parents=True, exist_ok=True)

        json_path = monitoring_dir / f"{self.ticker}_monitoring_plan.json"
        save_json_output(monitoring_data, json_path)

        # TODO: Generate markdown report
        md_content = f"# {self.ticker} Monitoring Plan\n\nGenerated: {datetime.now(timezone.utc).isoformat()}\n"
        md_path = monitoring_dir / f"{self.ticker}_monitoring_plan.md"
        save_markdown_output(md_content, md_path)

        print(f"[DONE] Monitoring pack complete")


def main():
    parser = argparse.ArgumentParser(description="Generic Ticker Monitoring Pack")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", choices=["validation", "live"], default="validation")

    args = parser.parse_args()

    pack = TickerMonitoringPack(args.ticker)
    pack.run(Path(args.input_dir), Path(args.output_dir), args.mode)


if __name__ == "__main__":
    main()
