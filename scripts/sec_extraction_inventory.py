"""
SEC Extraction Inventory Script

A lightweight read-only script that validates architecture documents exist
and reports on existing SEC extraction capabilities.

NO LIVE EXTRACTION - Just file checks and module inventory.

Usage:
    python scripts/sec_extraction_inventory.py
    python scripts/sec_extraction_inventory.py --output-json inventory_report.json
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import json
from datetime import datetime
import importlib.util

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))


class SECExtractionInventory:
    """Inventory checker for SEC extraction architecture and capabilities."""

    def __init__(self):
        self.project_root = project_root
        self.sources_dir = self.project_root / "sources"
        self.scripts_dir = self.project_root / "scripts"
        self.tests_dir = self.project_root / "tests"
        self.docs_dir = self.project_root / "docs"

    def check_architecture_documents(self) -> Dict[str, Any]:
        """Check that architecture documents exist."""
        docs_to_check = [
            "docs/workflows/full_sec_extraction_architecture.md",
            "docs/workflows/full_sec_extraction_implementation_plan.md",
            "docs/workflows/full_sec_extraction_schema.md",
            "docs/workflows/full_sec_extraction_test_plan.md",
        ]

        results = {
            "total_docs": len(docs_to_check),
            "found_docs": 0,
            "missing_docs": [],
            "found_docs_list": [],
        }

        for doc_path in docs_to_check:
            full_path = self.project_root / doc_path
            if full_path.exists():
                results["found_docs"] += 1
                results["found_docs_list"].append({
                    "path": doc_path,
                    "size_bytes": full_path.stat().st_size,
                    "modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat()
                })
            else:
                results["missing_docs"].append(doc_path)

        return results

    def check_sec_modules(self) -> Dict[str, Any]:
        """Check existing SEC extraction modules."""
        sec_modules = [
            "sources/sec_common.py",
            "sources/sec_ticker.py",
            "sources/sec_submissions.py",
            "sources/sec_form4.py",
            "sources/sec_form4_details.py",
            "sources/sec_13f.py",
            "sources/sec_13f_parser.py",
            "sources/sec_13f_matcher.py",
        ]

        planned_modules = [
            "sources/sec_form144.py",
            "sources/sec_13dg.py",
            "sources/sec_xbrl_financials.py",
            "sources/sec_capital_structure.py",
            "sources/sec_clinical_classifier.py",
            "sources/synthesis_composer.py",
        ]

        results = {
            "existing_modules": [],
            "planned_modules": [],
            "total_existing": 0,
            "total_planned": 0,
            "total_lines_of_code": 0,
        }

        # Check existing modules
        for module_path in sec_modules:
            full_path = self.project_root / module_path
            if full_path.exists():
                line_count = self._count_lines(full_path)
                results["existing_modules"].append({
                    "path": module_path,
                    "lines_of_code": line_count,
                    "status": "production_ready"
                })
                results["total_existing"] += 1
                results["total_lines_of_code"] += line_count

        # Check planned modules
        for module_path in planned_modules:
            full_path = self.project_root / module_path
            if full_path.exists():
                line_count = self._count_lines(full_path)
                results["existing_modules"].append({
                    "path": module_path,
                    "lines_of_code": line_count,
                    "status": "implemented"
                })
                results["total_existing"] += 1
                results["total_lines_of_code"] += line_count
            else:
                results["planned_modules"].append({
                    "path": module_path,
                    "status": "not_yet_implemented"
                })
                results["total_planned"] += 1

        return results

    def check_test_files(self) -> Dict[str, Any]:
        """Check existing test files."""
        test_files = list(self.tests_dir.glob("test_*.py"))
        sec_test_files = [f for f in test_files if "sec" in f.name.lower()]

        results = {
            "total_test_files": len(test_files),
            "sec_test_files": len(sec_test_files),
            "sec_test_list": [],
            "total_test_lines": 0,
        }

        for test_file in sec_test_files:
            line_count = self._count_lines(test_file)
            results["sec_test_list"].append({
                "file": test_file.name,
                "lines_of_code": line_count,
            })
            results["total_test_lines"] += line_count

        return results

    def check_cli_scripts(self) -> Dict[str, Any]:
        """Check existing CLI extraction scripts."""
        extraction_scripts = [
            "scripts/ticker_synthesis_workflow.py",
            "scripts/ticker_monitoring_pack.py",
            "scripts/ticker_market_confirmation_checklist.py",
            "scripts/ticker_archive_packet.py",
        ]

        planned_scripts = [
            "scripts/ticker_submissions_inventory.py",
            "scripts/ticker_form4_extractor.py",
            "scripts/ticker_form144_extractor.py",
            "scripts/ticker_13dg_extractor.py",
            "scripts/ticker_xbrl_extractor.py",
            "scripts/ticker_capital_structure_extractor.py",
            "scripts/ticker_13f_matcher.py",
            "scripts/ticker_batch_validator.py",
        ]

        results = {
            "existing_scripts": [],
            "planned_scripts": [],
            "total_existing": 0,
            "total_planned": 0,
        }

        for script_path in extraction_scripts:
            full_path = self.project_root / script_path
            if full_path.exists():
                results["existing_scripts"].append({
                    "path": script_path,
                    "lines_of_code": self._count_lines(full_path),
                    "status": "production_ready"
                })
                results["total_existing"] += 1

        for script_path in planned_scripts:
            full_path = self.project_root / script_path
            if full_path.exists():
                results["existing_scripts"].append({
                    "path": script_path,
                    "lines_of_code": self._count_lines(full_path),
                    "status": "implemented"
                })
                results["total_existing"] += 1
            else:
                results["planned_scripts"].append({
                    "path": script_path,
                    "status": "not_yet_implemented"
                })
                results["total_planned"] += 1

        return results

    def check_checkpoint_progress(self) -> Dict[str, Any]:
        """Check checkpoint implementation progress."""
        checkpoints = {
            "CP24A": {
                "name": "Architecture Design",
                "status": "complete",
                "deliverables": [
                    "docs/workflows/full_sec_extraction_architecture.md",
                    "docs/workflows/full_sec_extraction_implementation_plan.md",
                    "docs/workflows/full_sec_extraction_schema.md",
                    "docs/workflows/full_sec_extraction_test_plan.md",
                ]
            },
            "CP24B": {
                "name": "Ticker/CIK Resolver and Submissions Inventory",
                "status": "planned",
                "deliverables": [
                    "scripts/ticker_submissions_inventory.py",
                    "tests/test_ticker_submissions_inventory.py",
                ]
            },
            "CP24C": {
                "name": "Form 4 Extraction and Aggregation",
                "status": "planned",
                "deliverables": [
                    "sources/form4_aggregator.py",
                    "scripts/ticker_form4_extractor.py",
                    "tests/test_form4_aggregator.py",
                ]
            },
            "CP24D": {
                "name": "Form 144 and 13D/G Extraction",
                "status": "planned",
                "deliverables": [
                    "sources/sec_form144.py",
                    "sources/sec_13dg.py",
                    "scripts/ticker_form144_extractor.py",
                    "scripts/ticker_13dg_extractor.py",
                ]
            },
            "CP24E": {
                "name": "XBRL Financial Extraction",
                "status": "planned",
                "deliverables": [
                    "sources/sec_xbrl_financials.py",
                    "scripts/ticker_xbrl_extractor.py",
                ]
            },
            "CP24F": {
                "name": "Capital Structure Extraction",
                "status": "planned",
                "deliverables": [
                    "sources/sec_capital_structure.py",
                    "scripts/ticker_capital_structure_extractor.py",
                ]
            },
            "CP24G": {
                "name": "13F InfoTable Integration",
                "status": "planned",
                "deliverables": [
                    "scripts/ticker_13f_matcher.py",
                ]
            },
            "CP24H": {
                "name": "Full Synthesis Composition",
                "status": "planned",
                "deliverables": [
                    "sources/synthesis_composer.py",
                ]
            },
            "CP24I": {
                "name": "Multi-Ticker Validation Batch",
                "status": "planned",
                "deliverables": [
                    "scripts/ticker_batch_validator.py",
                    "tests/test_multi_ticker_validation.py",
                ]
            },
            "CP24J": {
                "name": "Documentation/Archive Hardening",
                "status": "planned",
                "deliverables": []
            },
        }

        results = {
            "total_checkpoints": len(checkpoints),
            "completed_checkpoints": 0,
            "planned_checkpoints": 0,
            "checkpoints": []
        }

        for cp_id, cp_data in checkpoints.items():
            cp_result = {
                "checkpoint": cp_id,
                "name": cp_data["name"],
                "status": cp_data["status"],
                "deliverables_found": 0,
                "deliverables_total": len(cp_data["deliverables"]),
                "deliverables": []
            }

            for deliverable in cp_data["deliverables"]:
                full_path = self.project_root / deliverable
                exists = full_path.exists()
                if exists:
                    cp_result["deliverables_found"] += 1
                cp_result["deliverables"].append({
                    "path": deliverable,
                    "exists": exists
                })

            # Update status based on deliverables
            if cp_result["deliverables_total"] > 0:
                if cp_result["deliverables_found"] == cp_result["deliverables_total"]:
                    cp_result["status"] = "complete"
                    results["completed_checkpoints"] += 1
                elif cp_result["deliverables_found"] > 0:
                    cp_result["status"] = "in_progress"
                    results["planned_checkpoints"] += 1
                else:
                    results["planned_checkpoints"] += 1
            else:
                if cp_data["status"] == "complete":
                    results["completed_checkpoints"] += 1
                else:
                    results["planned_checkpoints"] += 1

            results["checkpoints"].append(cp_result)

        return results

    def _count_lines(self, file_path: Path) -> int:
        """Count lines of code in a file (excluding blank lines and comments)."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                code_lines = [
                    line for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
                return len(code_lines)
        except Exception:
            return 0

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive inventory report."""
        print("Generating SEC Extraction Inventory Report...")
        print()

        report = {
            "report_date": datetime.now().isoformat(),
            "architecture_documents": self.check_architecture_documents(),
            "sec_modules": self.check_sec_modules(),
            "test_files": self.check_test_files(),
            "cli_scripts": self.check_cli_scripts(),
            "checkpoint_progress": self.check_checkpoint_progress(),
        }

        # Add summary
        report["summary"] = {
            "architecture_complete": report["architecture_documents"]["found_docs"] == report["architecture_documents"]["total_docs"],
            "existing_modules_count": report["sec_modules"]["total_existing"],
            "planned_modules_count": report["sec_modules"]["total_planned"],
            "total_lines_of_code": report["sec_modules"]["total_lines_of_code"],
            "sec_test_files_count": report["test_files"]["sec_test_files"],
            "existing_scripts_count": report["cli_scripts"]["total_existing"],
            "planned_scripts_count": report["cli_scripts"]["total_planned"],
            "completed_checkpoints": report["checkpoint_progress"]["completed_checkpoints"],
            "total_checkpoints": report["checkpoint_progress"]["total_checkpoints"],
        }

        return report

    def print_report(self, report: Dict[str, Any]):
        """Print human-readable inventory report."""
        print("=" * 80)
        print("SEC EXTRACTION INVENTORY REPORT")
        print("=" * 80)
        print()

        # Architecture Documents
        print("ARCHITECTURE DOCUMENTS")
        print("-" * 80)
        docs = report["architecture_documents"]
        print(f"Found: {docs['found_docs']}/{docs['total_docs']}")
        for doc in docs["found_docs_list"]:
            print(f"  [OK] {doc['path']}")
            print(f"       Size: {doc['size_bytes']:,} bytes, Modified: {doc['modified']}")
        if docs["missing_docs"]:
            for doc in docs["missing_docs"]:
                print(f"  [MISSING] {doc}")
        print()

        # SEC Modules
        print("SEC EXTRACTION MODULES")
        print("-" * 80)
        modules = report["sec_modules"]
        print(f"Existing: {modules['total_existing']}")
        print(f"Planned: {modules['total_planned']}")
        print(f"Total Lines of Code: {modules['total_lines_of_code']:,}")
        print()
        print("Existing Modules:")
        for module in modules["existing_modules"]:
            print(f"  [OK] {module['path']} ({module['lines_of_code']:,} LOC) - {module['status']}")
        if modules["planned_modules"]:
            print()
            print("Planned Modules:")
            for module in modules["planned_modules"]:
                print(f"  [PLANNED] {module['path']} - {module['status']}")
        print()

        # Test Files
        print("TEST FILES")
        print("-" * 80)
        tests = report["test_files"]
        print(f"Total Test Files: {tests['total_test_files']}")
        print(f"SEC-Focused Tests: {tests['sec_test_files']}")
        print(f"Total Test Lines: {tests['total_test_lines']:,}")
        print()
        print("SEC Test Files:")
        for test in tests["sec_test_list"]:
            print(f"  [OK] {test['file']} ({test['lines_of_code']:,} LOC)")
        print()

        # CLI Scripts
        print("CLI EXTRACTION SCRIPTS")
        print("-" * 80)
        scripts = report["cli_scripts"]
        print(f"Existing: {scripts['total_existing']}")
        print(f"Planned: {scripts['total_planned']}")
        print()
        print("Existing Scripts:")
        for script in scripts["existing_scripts"]:
            print(f"  [OK] {script['path']} ({script['lines_of_code']:,} LOC) - {script['status']}")
        if scripts["planned_scripts"]:
            print()
            print("Planned Scripts:")
            for script in scripts["planned_scripts"]:
                print(f"  [PLANNED] {script['path']} - {script['status']}")
        print()

        # Checkpoint Progress
        print("CHECKPOINT PROGRESS")
        print("-" * 80)
        progress = report["checkpoint_progress"]
        print(f"Completed: {progress['completed_checkpoints']}/{progress['total_checkpoints']}")
        print()
        for cp in progress["checkpoints"]:
            status_icon = "[DONE]" if cp["status"] == "complete" else "[WIP]" if cp["status"] == "in_progress" else "[TODO]"
            print(f"{status_icon} {cp['checkpoint']}: {cp['name']} ({cp['status']})")
            if cp["deliverables_total"] > 0:
                print(f"        Deliverables: {cp['deliverables_found']}/{cp['deliverables_total']}")
                for deliverable in cp["deliverables"]:
                    icon = "[OK]" if deliverable["exists"] else "[NO]"
                    print(f"          {icon} {deliverable['path']}")
        print()

        # Summary
        print("SUMMARY")
        print("-" * 80)
        summary = report["summary"]
        print(f"Architecture Complete: {'Yes' if summary['architecture_complete'] else 'No'}")
        print(f"Existing SEC Modules: {summary['existing_modules_count']}")
        print(f"Planned SEC Modules: {summary['planned_modules_count']}")
        print(f"Total Lines of Code: {summary['total_lines_of_code']:,}")
        print(f"SEC Test Files: {summary['sec_test_files_count']}")
        print(f"Existing CLI Scripts: {summary['existing_scripts_count']}")
        print(f"Planned CLI Scripts: {summary['planned_scripts_count']}")
        print(f"Completed Checkpoints: {summary['completed_checkpoints']}/{summary['total_checkpoints']}")
        print()
        print("=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="SEC Extraction Inventory Report")
    parser.add_argument(
        "--output-json",
        type=str,
        help="Output JSON file path (optional)"
    )

    args = parser.parse_args()

    # Generate inventory
    inventory = SECExtractionInventory()
    report = inventory.generate_report()

    # Print report
    inventory.print_report(report)

    # Save JSON if requested
    if args.output_json:
        output_path = Path(args.output_json)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"JSON report saved to: {output_path}")


if __name__ == "__main__":
    main()
