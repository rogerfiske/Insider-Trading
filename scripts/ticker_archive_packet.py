"""
Generic Ticker Archive Packet Generator (CP23C)

Create distributable research archive with checksums.

IMPLEMENTATION STATUS:
- Skeleton framework with CLI design ✓
- MAIA validation mode ✓
- SHA-256 checksum generation ✓
- Archive manifest creation ✓
- TODO: Generic README template
- TODO: Generic archive index generation

SAFETY:
- Archiving only, no alerts
- NO Telegram/email

Usage:
    python scripts/ticker_archive_packet.py --ticker MAIA --mode validation \\
        --input-dir docs/sample_reports/generic_ticker/MAIA \\
        --output-dir docs/sample_reports/generic_ticker/MAIA/archive
"""

import argparse
import hashlib
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


class TickerArchivePacket:
    """Generic ticker archive generator."""

    def __init__(self, ticker: str, cik: str):
        self.ticker = ticker.upper()
        self.cik = cik
        self.project_root = Path(__file__).parent.parent

    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def generate_archive_manifest(self, input_dir: Path) -> dict:
        """Generate archive manifest with checksums."""
        artifacts = []

        # Collect artifacts from input directory
        for subdir in ["synthesis", "monitoring", "market_confirmation"]:
            subdir_path = input_dir / subdir
            if subdir_path.exists():
                for file_path in sorted(subdir_path.glob("*")):
                    if file_path.is_file():
                        artifacts.append({
                            "name": file_path.stem,
                            "type": file_path.suffix[1:],
                            "original_path": f"docs/sample_reports/generic_ticker/{self.ticker}/{subdir}/{file_path.name}",
                            "archive_path": f"{subdir}/{file_path.name}",
                            "purpose": f"{subdir.replace('_', ' ').title()} output",
                            "status": "approved",
                            "sha256": self.calculate_sha256(file_path),
                        })

        manifest = {
            "ticker": self.ticker,
            "cik": self.cik,
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "checkpoint": "CP23C",
            "archive_root": f"docs/sample_reports/generic_ticker/{self.ticker}/archive",
            "artifacts": artifacts,
            "safety": get_safety_flags(),
            "limitations": [
                "Generic framework skeleton - full SEC extraction not yet implemented",
                "Validation mode uses reformatted existing data",
            ],
        }

        return manifest

    def run(self, input_dir: Path, output_dir: Path, mode: str = "validation") -> None:
        """Execute archive packet generation."""
        print(f"[START] Generic Ticker Archive Packet")
        print(f"  Ticker: {self.ticker}")
        print(f"  Mode: {mode}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate manifest
        manifest = self.generate_archive_manifest(input_dir)

        # Save manifest
        manifest_path = output_dir / f"{self.ticker}_archive_manifest.json"
        save_json_output(manifest, manifest_path)

        # TODO: Generate archive index markdown
        index_content = f"# {self.ticker} Research Archive Index\n\nGenerated: {datetime.now(timezone.utc).isoformat()}\n"
        index_path = output_dir / f"{self.ticker}_archive_index.md"
        save_markdown_output(index_content, index_path)

        print(f"[DONE] Archive packet complete")
        print(f"  Total artifacts: {len(manifest['artifacts'])}")


def main():
    parser = argparse.ArgumentParser(description="Generic Ticker Archive Packet")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--cik", default="")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", choices=["validation", "live"], default="validation")

    args = parser.parse_args()

    archive = TickerArchivePacket(args.ticker, args.cik or "0001878313")
    archive.run(Path(args.input_dir), Path(args.output_dir), args.mode)


if __name__ == "__main__":
    main()
