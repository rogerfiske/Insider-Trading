"""
MAIA Monitoring Packet Archive Generator (CP23H)

This script generates the MAIA archive manifest with SHA-256 checksums.

SAFETY:
- Archive packaging only
- NO Telegram messages
- NO email alerts
- NO scheduled task modification
- NO .env access
- NO OpenInsider spreadsheet access
- NO new research conclusions

Usage:
    python scripts/maia_archive_packet.py --generate-manifest
    python scripts/maia_archive_packet.py --validate

"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


class MAIAArchivePacket:
    """MAIA monitoring packet archive generator - packaging/export only."""

    TICKER = "MAIA"
    CIK = "0001878313"
    CHECKPOINT_RANGE = "CP23D-CP23G"
    APPROVED_COMMITS = ["0fbff09", "b2c0ade", "fb2075f", "b72cda0"]

    def __init__(self):
        """Initialize archive generator."""
        self.project_root = Path(__file__).parent.parent
        self.archive_root = self.project_root / "docs" / "sample_reports" / "maia_archive"
        self.manifest_path = self.archive_root / "MAIA_archive_manifest.json"

    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_artifact_metadata(self, file_path: Path, archive_root: Path) -> dict:
        """Get artifact metadata with checksum."""
        relative_path = file_path.relative_to(archive_root)
        relative_path_str = str(relative_path).replace("\\", "/")

        # Determine original path based on archive path
        if relative_path_str.startswith("md/"):
            if "CP23" in file_path.name:
                original_path = f"docs/checkpoints/reports/{file_path.name}"
            elif "13F" in file_path.name:
                original_path = f"docs/sample_reports/maia_13f/{file_path.name}"
            elif "monitoring_checklist" in file_path.name or "monitoring_baseline" in file_path.name:
                original_path = f"docs/sample_reports/maia_monitoring/{file_path.name}"
            elif "market_confirmation" in file_path.name:
                original_path = f"docs/sample_reports/maia_market_confirmation/{file_path.name}"
            else:
                original_path = f"docs/sample_reports/maia_synthesis/{file_path.name}"
        elif relative_path_str.startswith("json/"):
            if "13F" in file_path.name:
                original_path = f"docs/sample_reports/maia_13f/{file_path.name}"
            elif "monitoring_plan" in file_path.name:
                original_path = f"docs/sample_reports/maia_monitoring/{file_path.name}"
            elif "market_confirmation" in file_path.name:
                original_path = f"docs/sample_reports/maia_market_confirmation/{file_path.name}"
            else:
                original_path = f"docs/sample_reports/maia_synthesis/{file_path.name}"
        elif relative_path_str.startswith("csv/"):
            original_path = f"docs/sample_reports/maia_market_confirmation/{file_path.name}"
        else:
            original_path = relative_path_str

        # Determine artifact type and status
        file_type = file_path.suffix[1:]  # Remove leading dot
        if file_type == "md":
            file_type = "markdown"

        if "CP23" in file_path.name:
            status = "checkpoint_report"
            purpose = f"{file_path.stem.replace('_', ' ').title()} checkpoint execution report"
        elif "observation_template" in file_path.name:
            status = "manual_template"
            purpose = "Weekly price/volume manual observation template"
        elif "13F" in file_path.name:
            status = "approved_with_limitation"
            purpose = "13F institutional holdings parsing results (60% parser success rate; no MAIA matches found)"
        else:
            status = "approved"
            if "synthesis" in file_path.name:
                purpose = "Comprehensive insider activity, capital structure, clinical programs, cash runway, and evidence matrix analysis"
            elif "monitoring" in file_path.name:
                if "checklist" in file_path.name:
                    purpose = "Structured monitoring workflow for tracking Form 4, Form 144, 13D/G, 13F, clinical updates, financing, and financial filings"
                elif "plan" in file_path.name:
                    purpose = "Machine-readable monitoring plan data"
                else:
                    purpose = "Current monitoring baseline and approval status"
            elif "market_confirmation" in file_path.name:
                if "checklist" in file_path.name:
                    purpose = "Manual price/volume monitoring framework relative to $1.50 March 2026 offering price"
                elif "plan" in file_path.name:
                    purpose = "Machine-readable market confirmation plan with baseline, triggers, status labels"
                else:
                    purpose = "Current market confirmation baseline and automation gaps"
            else:
                purpose = file_path.stem.replace("_", " ").title()

        return {
            "name": file_path.stem,
            "type": file_type,
            "original_path": original_path,
            "archive_path": relative_path_str,
            "purpose": purpose,
            "status": status,
            "sha256": self.calculate_sha256(file_path),
        }

    def generate_manifest(self) -> dict:
        """Generate archive manifest with checksums."""
        artifacts = []

        # Collect all archived files (exclude manifest itself and README/index)
        for subdir in ["md", "json", "csv", "pdf"]:
            subdir_path = self.archive_root / subdir
            if subdir_path.exists():
                for file_path in sorted(subdir_path.glob("*")):
                    if file_path.is_file():
                        artifacts.append(self.get_artifact_metadata(file_path, self.archive_root))

        manifest = {
            "ticker": self.TICKER,
            "cik": self.CIK,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "approved_checkpoint_range": self.CHECKPOINT_RANGE,
            "approved_commits": self.APPROVED_COMMITS,
            "archive_root": "docs/sample_reports/maia_archive",
            "artifacts": artifacts,
            "safety": {
                "report_only": True,
                "alerts_generated": False,
                "openinsider_spreadsheet_used": False,
                "telegram_sent": False,
                "email_sent": False,
                "scheduled_tasks_modified": False,
                "env_printed_or_changed": False,
                "secrets_included": False,
            },
            "limitations": [
                "13F parser success rate is 60%; no-match conclusion scoped to successfully parsed filings only",
                "Price/volume data is manual-entry only; no live market quote source integrated",
                "THIO-104 Phase 3 data timing is not disclosed (critical unknown)",
                "PDF export unavailable (pandoc/wkhtmltopdf not installed); markdown/JSON/CSV archive only",
            ],
        }

        return manifest

    def save_manifest(self):
        """Generate and save manifest to JSON file."""
        manifest = self.generate_manifest()

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print(f"[OK] Manifest saved to: {self.manifest_path}")
        print(f"     Total artifacts: {len(manifest['artifacts'])}")
        print(f"     Approved commits: {', '.join(manifest['approved_commits'])}")

    def validate_manifest(self) -> bool:
        """Validate manifest has required keys and checksums."""
        if not self.manifest_path.exists():
            print(f"[ERROR] Manifest file not found: {self.manifest_path}")
            return False

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Check required keys
        required_keys = [
            "ticker",
            "cik",
            "generated_at",
            "approved_checkpoint_range",
            "approved_commits",
            "archive_root",
            "artifacts",
            "safety",
            "limitations",
        ]

        missing_keys = [key for key in required_keys if key not in manifest]
        if missing_keys:
            print(f"[ERROR] Missing required keys: {missing_keys}")
            return False

        # Check safety flags
        safety = manifest.get("safety", {})
        expected_safety = {
            "report_only": True,
            "alerts_generated": False,
            "openinsider_spreadsheet_used": False,
            "telegram_sent": False,
            "email_sent": False,
            "scheduled_tasks_modified": False,
            "env_printed_or_changed": False,
            "secrets_included": False,
        }

        for flag, expected_value in expected_safety.items():
            actual_value = safety.get(flag)
            if actual_value != expected_value:
                print(f"[ERROR] Safety flag '{flag}': expected {expected_value}, got {actual_value}")
                return False

        # Check artifacts have checksums
        artifacts = manifest.get("artifacts", [])
        if not artifacts:
            print("[ERROR] No artifacts in manifest")
            return False

        for artifact in artifacts:
            if "sha256" not in artifact:
                print(f"[ERROR] Missing checksum for artifact: {artifact.get('name')}")
                return False

        print("[OK] Manifest validation passed")
        print(f"     Total artifacts: {len(artifacts)}")
        return True


def main():
    """Main entry point."""
    import sys

    archive = MAIAArchivePacket()

    if "--generate-manifest" in sys.argv:
        archive.save_manifest()
    elif "--validate" in sys.argv:
        success = archive.validate_manifest()
        sys.exit(0 if success else 1)
    else:
        print("Usage:")
        print("  python scripts/maia_archive_packet.py --generate-manifest")
        print("  python scripts/maia_archive_packet.py --validate")
        sys.exit(1)


if __name__ == "__main__":
    main()
