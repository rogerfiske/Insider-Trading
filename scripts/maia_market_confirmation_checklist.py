"""
MAIA Market Confirmation Manual Price/Volume Checklist Generator (CP23G)

This script generates the MAIA market confirmation checklist and baseline status reports.

SAFETY:
- Report generation only
- NO Telegram messages
- NO email alerts
- NO scheduled task modification
- NO .env access
- NO OpenInsider spreadsheet access
- NO trading signals or recommendations

Source boundary:
- SEC EDGAR filings only
- Project-approved reports: CP21G/H/I/J, CP23A-Fix, CP23B-Fix3A, CP23D, CP23F-Fix
- NO Roger's uploaded MAIA spreadsheet
- NO OpenInsider data

Usage:
    python scripts/maia_market_confirmation_checklist.py --validate
    python scripts/maia_market_confirmation_checklist.py --generate

"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class MAIAMarketConfirmationChecklist:
    """MAIA market confirmation checklist generator - manual monitoring tool only."""

    TICKER = "MAIA"
    CIK = "0001878313"
    CHECKPOINT = "CP23G"

    # Approved baseline values (CP21G/H/I/J, CP23A-Fix, CP23B-Fix3A, CP23D, CP23F-Fix)
    BASELINE = {
        "insider_score": 100,
        "open_market_purchases": 134,
        "open_market_sales": 0,
        "purchase_value_usd": 4921437.58,
        "distinct_buyers": 10,
        "latest_purchase_date": "2026-06-01",
        "march_2026_offering_price": 1.50,
        "common_shares_outstanding": 60671491,
        "approximate_fully_diluted_shares": 86860000,
        "cash_balance_usd": 34413110,
        "quarterly_operating_cash_burn": 5311328,
        "base_runway_months": 19.4,
        "form_13d_13g_filings": 0,
        "form_144_filings": 0,
        "form_13f_parser_success_rate": 0.60,
        "form_13f_maia_matches_found": 0,
        "thio_104_data_timing": "Not disclosed",
    }

    # PM review triggers (must include these at minimum per CP23G instruction)
    PM_REVIEW_TRIGGERS = [
        "Price closes below $1.50 for 5 consecutive trading days",
        "Price reclaims $1.50 and holds for 5 consecutive trading days on elevated volume",
        "Single-day volume spike >3x recent average",
        "Price declines >25% in one week without company explanation",
        "Price declines >50% from $1.50 offering price",
        "First Form 4 open-market sale",
        "First Form 144 filing",
        "New 13D/G filing",
        "New reliable 13F institutional match",
        "THIO-104 data timing disclosed",
        "THIO-104 topline data released",
        "New financing filing",
        "Cash runway drops below 12 months",
    ]

    def __init__(self):
        """Initialize checklist generator."""
        self.project_root = Path(__file__).parent.parent
        self.output_dir = self.project_root / "docs" / "sample_reports" / "maia_market_confirmation"
        self.json_path = self.output_dir / "MAIA_market_confirmation_plan.json"
        self.csv_path = self.output_dir / "MAIA_market_observation_template.csv"

    def validate_json_schema(self) -> bool:
        """Validate JSON schema has required keys."""
        if not self.json_path.exists():
            print(f"❌ JSON file not found: {self.json_path}")
            return False

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_keys = [
            "ticker",
            "cik",
            "baseline",
            "reference_levels",
            "weekly_checklist",
            "event_driven_checks",
            "pm_review_triggers",
            "manual_observation_template",
            "status_labels",
            "limitations",
            "future_automation",
            "safety",
        ]

        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            print(f"❌ Missing required keys: {missing_keys}")
            return False

        print("✅ JSON schema validated")
        return True

    def validate_baseline_values(self) -> bool:
        """Validate baseline values match approved research."""
        if not self.json_path.exists():
            print(f"❌ JSON file not found: {self.json_path}")
            return False

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        baseline = data.get("baseline", {}).get("insider_activity", {})

        # Check critical baseline values
        checks = [
            (baseline.get("open_market_purchases") == self.BASELINE["open_market_purchases"],
             f"Open market purchases: expected {self.BASELINE['open_market_purchases']}, got {baseline.get('open_market_purchases')}"),
            (baseline.get("open_market_sales") == self.BASELINE["open_market_sales"],
             f"Open market sales: expected {self.BASELINE['open_market_sales']}, got {baseline.get('open_market_sales')}"),
            (data.get("baseline", {}).get("capital_structure", {}).get("march_2026_offering_price") == self.BASELINE["march_2026_offering_price"],
             f"Offering price: expected {self.BASELINE['march_2026_offering_price']}, got {data.get('baseline', {}).get('capital_structure', {}).get('march_2026_offering_price')}"),
        ]

        all_passed = True
        for passed, message in checks:
            if not passed:
                print(f"❌ {message}")
                all_passed = False

        if all_passed:
            print("✅ Baseline values validated")
        return all_passed

    def validate_pm_review_triggers(self) -> bool:
        """Validate PM review triggers include required conditions."""
        if not self.json_path.exists():
            print(f"❌ JSON file not found: {self.json_path}")
            return False

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pm_triggers = data.get("pm_review_triggers", [])
        trigger_names = [t.get("trigger_name", "") for t in pm_triggers]

        # Required triggers per CP23G instruction
        required_triggers = [
            "below $1.50 for 5",  # Price closes below $1.50 for 5 consecutive trading days
            "reclaims $1.50",  # Price reclaims $1.50 and holds for 5 consecutive trading days
            ">3x",  # Single-day volume spike >3x recent average
            "First Form 4",  # First Form 4 open-market sale
            "Form 144",  # First Form 144 filing
            "13D/G",  # New 13D/G filing
            "13F",  # New reliable 13F institutional match
            "financing",  # New financing filing
            "THIO-104",  # THIO-104 data timing disclosed
            "runway",  # Cash runway drops below 12 months
        ]

        all_triggers_found = True
        for required_substring in required_triggers:
            found = any(required_substring.lower() in trigger.lower() for trigger in trigger_names)
            if not found:
                print(f"❌ Missing required PM review trigger containing: '{required_substring}'")
                all_triggers_found = False

        if all_triggers_found:
            print("✅ PM review triggers validated")
        return all_triggers_found

    def validate_csv_template(self) -> bool:
        """Validate CSV template has required columns."""
        if not self.csv_path.exists():
            print(f"❌ CSV file not found: {self.csv_path}")
            return False

        with open(self.csv_path, "r", encoding="utf-8") as f:
            header = f.readline().strip()

        required_columns = [
            "date",
            "closing_price",
            "weekly_high",
            "weekly_low",
            "weekly_volume",
            "avg_volume_reference",
            "days_above_1_50",
            "days_below_1_50",
            "major_news",
            "sec_filings",
            "form4_activity",
            "form144_activity",
            "clinical_updates",
            "financing_updates",
            "price_volume_read",
            "pm_review_triggered",
            "notes",
        ]

        missing_columns = [col for col in required_columns if col not in header]
        if missing_columns:
            print(f"❌ Missing required CSV columns: {missing_columns}")
            return False

        print("✅ CSV template validated")
        return True

    def validate_no_recommendation_language(self) -> bool:
        """Validate report/JSON do not contain buy/sell/hold recommendation language."""
        if not self.json_path.exists():
            print(f"❌ JSON file not found: {self.json_path}")
            return False

        with open(self.json_path, "r", encoding="utf-8") as f:
            json_content = f.read().lower()

        # Check for forbidden recommendation language
        forbidden_phrases = ["buy recommendation", "sell recommendation", "hold recommendation", "strong buy", "strong sell"]
        found_forbidden = [phrase for phrase in forbidden_phrases if phrase in json_content]

        if found_forbidden:
            print(f"❌ Found forbidden recommendation language: {found_forbidden}")
            return False

        print("✅ No buy/sell/hold recommendation language found")
        return True

    def validate_no_secrets(self) -> bool:
        """Validate report/JSON contain no secrets."""
        if not self.json_path.exists():
            print(f"❌ JSON file not found: {self.json_path}")
            return False

        with open(self.json_path, "r", encoding="utf-8") as f:
            json_content = f.read()

        # Check for secret patterns
        secret_patterns = [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "SMTP_PASSWORD",
            "sk-ant-",
            "ETHERSCAN_API_KEY",
        ]

        found_secrets = [pattern for pattern in secret_patterns if pattern in json_content]

        if found_secrets:
            print(f"❌ Found secrets in JSON: {found_secrets}")
            return False

        print("✅ No secrets found in JSON")
        return True

    def validate_safety_flags(self) -> bool:
        """Validate safety flags are correct."""
        if not self.json_path.exists():
            print(f"❌ JSON file not found: {self.json_path}")
            return False

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        safety = data.get("safety", {})

        expected_safety_flags = {
            "report_only": True,
            "alerts_generated": False,
            "openinsider_spreadsheet_used": False,
            "telegram_sent": False,
            "email_sent": False,
            "scheduled_tasks_modified": False,
            "env_printed_or_changed": False,
            "buy_sell_hold_language_used": False,
        }

        all_flags_correct = True
        for flag, expected_value in expected_safety_flags.items():
            actual_value = safety.get(flag)
            if actual_value != expected_value:
                print(f"❌ Safety flag '{flag}': expected {expected_value}, got {actual_value}")
                all_flags_correct = False

        if all_flags_correct:
            print("✅ Safety flags validated")
        return all_flags_correct

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("\n=== MAIA Market Confirmation Checklist Validation (CP23G) ===\n")

        validations = [
            ("JSON schema", self.validate_json_schema),
            ("Baseline values", self.validate_baseline_values),
            ("PM review triggers", self.validate_pm_review_triggers),
            ("CSV template", self.validate_csv_template),
            ("No recommendation language", self.validate_no_recommendation_language),
            ("No secrets", self.validate_no_secrets),
            ("Safety flags", self.validate_safety_flags),
        ]

        all_passed = True
        for name, validation_func in validations:
            print(f"\n--- {name} ---")
            if not validation_func():
                all_passed = False

        print("\n" + "=" * 60)
        if all_passed:
            print("✅ ALL VALIDATIONS PASSED")
        else:
            print("❌ SOME VALIDATIONS FAILED")
        print("=" * 60 + "\n")

        return all_passed


def main():
    """Main entry point."""
    import sys

    checklist = MAIAMarketConfirmationChecklist()

    if "--validate" in sys.argv:
        success = checklist.validate_all()
        sys.exit(0 if success else 1)
    elif "--generate" in sys.argv:
        print("Generate mode not implemented - files already created during CP23G")
        print("Use --validate to validate existing files")
        sys.exit(0)
    else:
        print("Usage:")
        print("  python scripts/maia_market_confirmation_checklist.py --validate")
        print("  python scripts/maia_market_confirmation_checklist.py --generate")
        sys.exit(1)


if __name__ == "__main__":
    main()
