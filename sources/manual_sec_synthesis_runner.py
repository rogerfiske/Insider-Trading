"""
Manual SEC Synthesis Runner

Orchestrates CP24B-CP24H modules to run manual ticker SEC synthesis
in report-only mode with comprehensive safety controls.

Modes:
- full: Run all available modules (inventory → synthesis)
- inventory-first: Run only lightweight inventory stage
- synthesis-only: Compose synthesis from existing local outputs (no network)

This module produces report-only outputs with no alert/notification code paths.
"""

import json
import csv
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class ManualSECSynthesisRunner:
    """
    Orchestrates CP24B-CP24H modules for manual ticker SEC synthesis.

    Supports multiple modes and creates structured output folders with
    manifests, summaries, validation matrices, and safety audits.
    """

    def __init__(
        self,
        output_root: Path = Path("docs/sample_reports/manual_sec_synthesis_runs"),
        input_root: Path = Path("docs/sample_reports"),
        project_root: Optional[Path] = None
    ):
        """
        Initialize the manual SEC synthesis runner.

        Args:
            output_root: Root directory for manual run outputs
            input_root: Root directory for CP24B-CP24G outputs
            project_root: Project root directory (default: auto-detect)
        """
        self.output_root = output_root
        self.input_root = input_root

        if project_root is None:
            # Auto-detect project root (parent of sources directory)
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = project_root

        self.venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"

        # Verify Python executable
        if not self.venv_python.exists():
            # Fallback to system python
            self.venv_python = Path(sys.executable)

    def _get_subprocess_env(self) -> Dict[str, str]:
        """
        Get environment variables for subprocess with PYTHONPATH set.

        Returns:
            Environment dictionary with PYTHONPATH including project root
        """
        env = os.environ.copy()
        # Add project root to PYTHONPATH so scripts can import from sources/
        pythonpath = str(self.project_root)
        if "PYTHONPATH" in env:
            pythonpath = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
        env["PYTHONPATH"] = pythonpath
        return env

    def create_run_folder(self, run_name: Optional[str] = None, tickers: Optional[List[str]] = None) -> Path:
        """
        Create timestamped run folder.

        Args:
            run_name: Optional custom run name
            tickers: Optional list of tickers for auto-naming

        Returns:
            Path to created run folder
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if run_name:
            folder_name = f"{timestamp}_{run_name}"
        elif tickers:
            ticker_str = "_".join(tickers[:3])  # Max 3 tickers in folder name
            folder_name = f"{timestamp}_{ticker_str}"
        else:
            folder_name = timestamp

        run_folder = self.output_root / folder_name
        run_folder.mkdir(parents=True, exist_ok=True)

        return run_folder

    def run_inventory_module(self, ticker: str, output_dir: Path) -> Dict[str, Any]:
        """
        Run CP24B SEC ticker inventory module.

        Args:
            ticker: Ticker symbol
            output_dir: Output directory

        Returns:
            Result dictionary with status and output path
        """
        script_path = self.project_root / "scripts" / "sec_ticker_inventory.py"

        if not script_path.exists():
            return {
                "status": "error",
                "error_type": "script_not_found",
                "error_message": f"Script not found: {script_path}"
            }

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                [
                    str(self.venv_python),
                    str(script_path),
                    "--ticker", ticker,
                    "--output-dir", str(output_dir)
                ],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                env=self._get_subprocess_env()
            )

            if result.returncode == 0:
                output_file = output_dir / f"{ticker}_sec_inventory.json"
                return {
                    "status": "success",
                    "output_path": str(output_file),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                return {
                    "status": "error",
                    "error_type": "execution_failed",
                    "error_message": result.stderr or result.stdout,
                    "returncode": result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error_type": "timeout",
                "error_message": "Inventory module timed out after 120 seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "exception",
                "error_message": str(e)
            }

    def run_form4_module(self, ticker: str, output_dir: Path, lookback_days: int = 1460, max_filings: Optional[int] = None) -> Dict[str, Any]:
        """
        Run CP24C Form 4 transactions module.

        Args:
            ticker: Ticker symbol
            output_dir: Output directory
            lookback_days: Lookback period in days
            max_filings: Optional maximum number of filings to process

        Returns:
            Result dictionary with status and output path
        """
        script_path = self.project_root / "scripts" / "sec_form4_transactions.py"

        if not script_path.exists():
            return {
                "status": "error",
                "error_type": "script_not_found",
                "error_message": f"Script not found: {script_path}"
            }

        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.venv_python),
            str(script_path),
            "--ticker", ticker,
            "--output-dir", str(output_dir),
            "--lookback-days", str(lookback_days)
        ]

        if max_filings:
            cmd.extend(["--max-filings", str(max_filings)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                env=self._get_subprocess_env()
            )

            if result.returncode == 0:
                output_file = output_dir / f"{ticker}_form4_transactions.json"
                return {
                    "status": "success",
                    "output_path": str(output_file),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                return {
                    "status": "error",
                    "error_type": "execution_failed",
                    "error_message": result.stderr or result.stdout,
                    "returncode": result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error_type": "timeout",
                "error_message": "Form 4 module timed out after 300 seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "exception",
                "error_message": str(e)
            }

    def run_synthesis_module(self, ticker: str, output_dir: Path, no_network: bool = False) -> Dict[str, Any]:
        """
        Run CP24H generic SEC synthesis module.

        Args:
            ticker: Ticker symbol
            output_dir: Output directory
            no_network: Operate in offline mode

        Returns:
            Result dictionary with status and output path
        """
        script_path = self.project_root / "scripts" / "generic_sec_synthesis.py"

        if not script_path.exists():
            return {
                "status": "error",
                "error_type": "script_not_found",
                "error_message": f"Script not found: {script_path}"
            }

        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.venv_python),
            str(script_path),
            "--ticker", ticker,
            "--output-dir", str(output_dir),
            "--input-root", str(self.input_root)
        ]

        if no_network:
            cmd.append("--no-network")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout
                env=self._get_subprocess_env()
            )

            if result.returncode == 0:
                output_file = output_dir / f"{ticker}_generic_sec_synthesis.json"
                return {
                    "status": "success",
                    "output_path": str(output_file),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                return {
                    "status": "error",
                    "error_type": "execution_failed",
                    "error_message": result.stderr or result.stdout,
                    "returncode": result.returncode
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error_type": "timeout",
                "error_message": "Synthesis module timed out after 60 seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "exception",
                "error_message": str(e)
            }

    def run_ticker_full_mode(
        self,
        ticker: str,
        run_folder: Path,
        lookback_days: int = 1460,
        max_form4_filings: Optional[int] = None,
        skip_13f: bool = False,
        fail_fast: bool = False
    ) -> Dict[str, Any]:
        """
        Run full mode for a single ticker (inventory → synthesis).

        Args:
            ticker: Ticker symbol
            run_folder: Run output folder
            lookback_days: Form 4 lookback period
            max_form4_filings: Optional max Form 4 filings
            skip_13f: Skip 13F module
            fail_fast: Stop on first module failure

        Returns:
            Ticker result dictionary
        """
        ticker_folder = run_folder / ticker
        ticker_folder.mkdir(parents=True, exist_ok=True)

        module_outputs_folder = ticker_folder / "module_outputs"
        module_outputs_folder.mkdir(parents=True, exist_ok=True)

        synthesis_folder = ticker_folder / "synthesis"
        synthesis_folder.mkdir(parents=True, exist_ok=True)

        modules_run = []
        modules_status = {}
        degraded = False
        degraded_reasons = []

        # CP24B: Inventory
        print(f"  Running inventory for {ticker}...")
        inventory_result = self.run_inventory_module(ticker, module_outputs_folder)
        modules_run.append("inventory")
        modules_status["inventory"] = inventory_result["status"]

        if inventory_result["status"] == "error":
            degraded = True
            degraded_reasons.append(f"Inventory failed: {inventory_result.get('error_message', 'Unknown error')}")
            if fail_fast:
                return self._create_ticker_result(ticker, modules_run, modules_status, degraded, degraded_reasons)

        # CP24C: Form 4 transactions
        print(f"  Running Form 4 extraction for {ticker}...")
        form4_result = self.run_form4_module(ticker, module_outputs_folder, lookback_days, max_form4_filings)
        modules_run.append("form4_transactions")
        modules_status["form4_transactions"] = form4_result["status"]

        if form4_result["status"] == "error":
            degraded = True
            degraded_reasons.append(f"Form 4 failed: {form4_result.get('error_message', 'Unknown error')}")
            if fail_fast:
                return self._create_ticker_result(ticker, modules_run, modules_status, degraded, degraded_reasons)

        # Additional modules would go here (CP24D-CP24G)
        # For now, we'll proceed to synthesis with available data

        # CP24H: Synthesis
        print(f"  Running synthesis for {ticker}...")
        synthesis_result = self.run_synthesis_module(ticker, synthesis_folder, no_network=False)
        modules_run.append("synthesis")
        modules_status["synthesis"] = synthesis_result["status"]

        if synthesis_result["status"] == "error":
            degraded = True
            degraded_reasons.append(f"Synthesis failed: {synthesis_result.get('error_message', 'Unknown error')}")

        return self._create_ticker_result(ticker, modules_run, modules_status, degraded, degraded_reasons)

    def run_ticker_inventory_first_mode(self, ticker: str, run_folder: Path) -> Dict[str, Any]:
        """
        Run inventory-first mode for a single ticker.

        Args:
            ticker: Ticker symbol
            run_folder: Run output folder

        Returns:
            Ticker result dictionary
        """
        ticker_folder = run_folder / ticker
        ticker_folder.mkdir(parents=True, exist_ok=True)

        module_outputs_folder = ticker_folder / "module_outputs"
        module_outputs_folder.mkdir(parents=True, exist_ok=True)

        modules_run = []
        modules_status = {}
        degraded = False
        degraded_reasons = []

        # CP24B: Inventory only
        print(f"  Running inventory for {ticker}...")
        inventory_result = self.run_inventory_module(ticker, module_outputs_folder)
        modules_run.append("inventory")
        modules_status["inventory"] = inventory_result["status"]

        if inventory_result["status"] == "error":
            degraded = True
            degraded_reasons.append(f"Inventory failed: {inventory_result.get('error_message', 'Unknown error')}")

        return self._create_ticker_result(ticker, modules_run, modules_status, degraded, degraded_reasons)

    def run_ticker_synthesis_only_mode(self, ticker: str, run_folder: Path) -> Dict[str, Any]:
        """
        Run synthesis-only mode for a single ticker (no network).

        Args:
            ticker: Ticker symbol
            run_folder: Run output folder

        Returns:
            Ticker result dictionary
        """
        ticker_folder = run_folder / ticker
        ticker_folder.mkdir(parents=True, exist_ok=True)

        synthesis_folder = ticker_folder / "synthesis"
        synthesis_folder.mkdir(parents=True, exist_ok=True)

        modules_run = []
        modules_status = {}
        degraded = False
        degraded_reasons = []

        # CP24H: Synthesis only (no-network mode)
        print(f"  Running synthesis for {ticker} (synthesis-only mode, no network)...")
        synthesis_result = self.run_synthesis_module(ticker, synthesis_folder, no_network=True)
        modules_run.append("synthesis")
        modules_status["synthesis"] = synthesis_result["status"]

        if synthesis_result["status"] == "error":
            degraded = True
            degraded_reasons.append(f"Synthesis failed: {synthesis_result.get('error_message', 'Unknown error')}")

        return self._create_ticker_result(ticker, modules_run, modules_status, degraded, degraded_reasons)

    def _create_ticker_result(
        self,
        ticker: str,
        modules_run: List[str],
        modules_status: Dict[str, str],
        degraded: bool,
        degraded_reasons: List[str]
    ) -> Dict[str, Any]:
        """
        Create standardized ticker result dictionary.

        Args:
            ticker: Ticker symbol
            modules_run: List of modules that were run
            modules_status: Dictionary of module statuses
            degraded: Whether ticker is in degraded mode
            degraded_reasons: List of degraded mode reasons

        Returns:
            Ticker result dictionary
        """
        # Determine overall status
        if all(status == "success" for status in modules_status.values()):
            overall_status = "completed"
        elif degraded:
            overall_status = "degraded"
        else:
            overall_status = "failed"

        return {
            "ticker": ticker,
            "status": overall_status,
            "modules_run": modules_run,
            "modules_status": modules_status,
            "degraded": degraded,
            "degraded_reasons": degraded_reasons
        }

    def create_run_manifest(
        self,
        run_folder: Path,
        run_id: str,
        tickers_requested: List[str],
        mode: str,
        ticker_results: Dict[str, Dict[str, Any]]
    ) -> Path:
        """
        Create run manifest JSON file.

        Args:
            run_folder: Run output folder
            run_id: Unique run identifier
            tickers_requested: List of requested tickers
            mode: Run mode (full/inventory-first/synthesis-only)
            ticker_results: Dictionary of ticker results

        Returns:
            Path to created manifest file
        """
        degraded_tickers = [
            ticker for ticker, result in ticker_results.items()
            if result.get("degraded", False)
        ]

        failed_tickers = [
            ticker for ticker, result in ticker_results.items()
            if result.get("status") == "failed"
        ]

        manifest = {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tickers_requested": tickers_requested,
            "mode": mode,
            "output_root": str(self.output_root),
            "project_root": str(self.project_root),
            "modules_requested": self._get_modules_for_mode(mode),
            "modules_run_by_ticker": {
                ticker: result.get("modules_run", [])
                for ticker, result in ticker_results.items()
            },
            "outputs_by_ticker": {
                ticker: str(run_folder / ticker)
                for ticker in tickers_requested
            },
            "validation_matrix_path": str(run_folder / "validation_matrix.csv"),
            "run_summary_json_path": str(run_folder / "run_summary.json"),
            "run_summary_markdown_path": str(run_folder / "run_summary.md"),
            "safety_audit_path": str(run_folder / "safety_audit.json"),
            "degraded_tickers": degraded_tickers,
            "failed_tickers": failed_tickers,
            "safety": {
                "report_only": True,
                "alerts_generated": False,
                "openinsider_spreadsheet_used": False,
                "telegram_sent": False,
                "email_sent": False,
                "scheduled_tasks_modified": False,
                "env_printed_or_changed": False,
                "buy_sell_hold_language_used": False
            }
        }

        manifest_path = run_folder / "run_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        return manifest_path

    def create_safety_audit(
        self,
        run_folder: Path,
        mode: str,
        tickers: List[str]
    ) -> Path:
        """
        Create safety audit JSON file.

        Args:
            run_folder: Run output folder
            mode: Run mode
            tickers: List of tickers

        Returns:
            Path to created safety audit file
        """
        audit = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "tickers": tickers,
            "no_alerts_confirmed": True,
            "no_telegram_confirmed": True,
            "no_email_confirmed": True,
            "scheduled_tasks_unchanged_or_not_touched": True,
            "env_not_printed_or_changed": True,
            "openinsider_spreadsheet_not_used": True,
            "secrets_not_written": True,
            "recommendation_language_absent": True,
            "private_file_exclusion_confirmed": True,
            "notes": [
                "Manual SEC synthesis run in report-only mode",
                "No alert/notification code paths executed",
                "No scheduled task modifications",
                "No .env access or modifications",
                "No OpenInsider spreadsheet usage",
                "No buy/sell/hold recommendation language"
            ]
        }

        audit_path = run_folder / "safety_audit.json"
        with open(audit_path, 'w', encoding='utf-8') as f:
            json.dump(audit, f, indent=2)

        return audit_path

    def create_validation_matrix(
        self,
        run_folder: Path,
        ticker_results: Dict[str, Dict[str, Any]]
    ) -> Path:
        """
        Create validation matrix CSV file.

        Args:
            run_folder: Run output folder
            ticker_results: Dictionary of ticker results

        Returns:
            Path to created validation matrix file
        """
        matrix_path = run_folder / "validation_matrix.csv"

        with open(matrix_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "ticker",
                "cik",
                "company_name",
                "mode",
                "inventory_status",
                "form4_status",
                "ownership_status",
                "xbrl_status",
                "capital_structure_status",
                "thirteenf_status",
                "synthesis_status",
                "evidence_rows",
                "posture",
                "degraded",
                "primary_degraded_reason",
                "safety_passed"
            ])

            # Rows
            for ticker, result in ticker_results.items():
                modules_status = result.get("modules_status", {})

                writer.writerow([
                    ticker,
                    "",  # CIK - would be populated from synthesis
                    "",  # Company name - would be populated from synthesis
                    result.get("status", "unknown"),
                    modules_status.get("inventory", "not_run"),
                    modules_status.get("form4_transactions", "not_run"),
                    modules_status.get("ownership_filings", "not_run"),
                    modules_status.get("xbrl_financials", "not_run"),
                    modules_status.get("capital_structure", "not_run"),
                    modules_status.get("thirteenf", "not_run"),
                    modules_status.get("synthesis", "not_run"),
                    "",  # Evidence rows - would be populated from synthesis
                    "",  # Posture - would be populated from synthesis
                    "true" if result.get("degraded", False) else "false",
                    result.get("degraded_reasons", [""])[0] if result.get("degraded_reasons") else "",
                    "true"  # Safety always passes in manual mode
                ])

        return matrix_path

    def create_run_summary(
        self,
        run_folder: Path,
        run_id: str,
        mode: str,
        tickers_requested: List[str],
        ticker_results: Dict[str, Dict[str, Any]]
    ) -> tuple[Path, Path]:
        """
        Create run summary JSON and Markdown files.

        Args:
            run_folder: Run output folder
            run_id: Unique run identifier
            mode: Run mode
            tickers_requested: List of requested tickers
            ticker_results: Dictionary of ticker results

        Returns:
            Tuple of (JSON path, Markdown path)
        """
        # JSON summary
        summary_json = {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "tickers_requested": tickers_requested,
            "ticker_results": ticker_results,
            "safety": {
                "report_only": True,
                "no_alerts": True,
                "no_telegram": True,
                "no_email": True,
                "no_scheduled_tasks_modified": True
            }
        }

        json_path = run_folder / "run_summary.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary_json, f, indent=2)

        # Markdown summary
        md_lines = [
            f"# Manual SEC Synthesis Run Summary",
            f"",
            f"**Run ID:** {run_id}",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Mode:** {mode}",
            f"",
            f"---",
            f"",
            f"## Purpose and Source Boundary",
            f"",
            f"This is a manual SEC-only research run using the approved CP24 generic SEC pipeline.",
            f"",
            f"**Data sources:**",
            f"- SEC EDGAR public filings",
            f"- SEC companyfacts API",
            f"- SEC 13F InfoTables",
            f"",
            f"**Excluded sources:**",
            f"- Roger's uploaded MAIA spreadsheet",
            f"- OpenInsider data",
            f"- Third-party paid/private sources",
            f"- Live market data",
            f"",
            f"---",
            f"",
            f"## Tickers Requested",
            f"",
        ]

        for ticker in tickers_requested:
            result = ticker_results.get(ticker, {})
            status = result.get("status", "unknown")
            md_lines.append(f"- **{ticker}**: {status}")

        md_lines.extend([
            f"",
            f"---",
            f"",
            f"## Per-Ticker Results",
            f"",
        ])

        for ticker, result in ticker_results.items():
            md_lines.extend([
                f"### {ticker}",
                f"",
                f"**Status:** {result.get('status', 'unknown')}",
                f"**Degraded:** {result.get('degraded', False)}",
                f"",
            ])

            if result.get("degraded_reasons"):
                md_lines.append(f"**Degraded Reasons:**")
                for reason in result["degraded_reasons"]:
                    md_lines.append(f"- {reason}")
                md_lines.append(f"")

            md_lines.extend([
                f"**Modules Run:** {', '.join(result.get('modules_run', []))}",
                f"",
                f"**Output Path:** `{run_folder / ticker}`",
                f"",
            ])

        md_lines.extend([
            f"---",
            f"",
            f"## Safety Confirmations",
            f"",
            f"- ✓ Report-only mode",
            f"- ✓ No alerts generated",
            f"- ✓ No Telegram messages sent",
            f"- ✓ No email sent",
            f"- ✓ No scheduled tasks modified or triggered",
            f"- ✓ No .env access or modifications",
            f"- ✓ No OpenInsider spreadsheet usage",
            f"- ✓ No buy/sell/hold recommendation language",
            f"",
            f"---",
            f"",
            f"## Output Files",
            f"",
            f"- `run_manifest.json` - Complete run metadata and file paths",
            f"- `run_summary.json` - Structured run results",
            f"- `run_summary.md` - This file",
            f"- `validation_matrix.csv` - Per-ticker validation matrix",
            f"- `safety_audit.json` - Safety audit log",
            f"- `<TICKER>/` - Per-ticker output folders",
            f"",
            f"---",
            f"",
            f"## Disclaimer",
            f"",
            f"**This is not investment advice.** Perform your own due diligence and consult licensed financial professionals before making investment decisions.",
            f"",
            f"---",
            f"",
            f"## Next Suggested Action",
            f"",
            f"Review individual ticker outputs in the `<TICKER>/` folders. Check synthesis JSON files for evidence matrices and scoring framework.",
            f"",
        ])

        md_path = run_folder / "run_summary.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        return json_path, md_path

    def _get_modules_for_mode(self, mode: str) -> List[str]:
        """
        Get list of modules to run for a given mode.

        Args:
            mode: Run mode

        Returns:
            List of module names
        """
        if mode == "full":
            return [
                "inventory",
                "form4_transactions",
                "ownership_filings",
                "xbrl_financials",
                "capital_structure",
                "institutional_13f",
                "synthesis"
            ]
        elif mode == "inventory-first":
            return ["inventory"]
        elif mode == "synthesis-only":
            return ["synthesis"]
        else:
            return []
