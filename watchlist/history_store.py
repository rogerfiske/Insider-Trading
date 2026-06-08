"""Persistent watchlist tracking with SQLite.

This module provides local research history storage for manual ticker watchlist runs.
No network calls. No alerts. No trading advice. Informational research only.

Database: .state/watchlist_history.db (local, gitignored)
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class WatchlistHistoryStore:
    """SQLite store for watchlist run history and ticker result tracking."""

    def __init__(self, db_path: Path | str = ".state/watchlist_history.db"):
        """Initialize history store.

        Args:
            db_path: Path to SQLite database file (default: .state/watchlist_history.db)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # watchlist_runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_runs (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                mode TEXT NOT NULL,
                tickers_requested INTEGER NOT NULL,
                tickers_resolved INTEGER NOT NULL,
                lookback_days INTEGER NOT NULL,
                max_form4_filings INTEGER NOT NULL,
                source_version TEXT,
                git_commit TEXT,
                notes TEXT
            )
        """)

        # watchlist_ticker_results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_ticker_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                cik TEXT,
                company_name TEXT,
                resolution_status TEXT,
                lookback_days INTEGER,
                form4_filings_found INTEGER,
                form4_filings_parsed INTEGER,
                transactions_extracted INTEGER,
                purchase_count INTEGER,
                purchase_shares REAL,
                purchase_value REAL,
                sale_count INTEGER,
                sale_shares REAL,
                sale_value REAL,
                net_purchase_value REAL,
                purchase_to_sale_value_ratio REAL,
                distinct_buyers INTEGER,
                distinct_sellers INTEGER,
                latest_purchase_date TEXT,
                latest_sale_date TEXT,
                eddie_status TEXT,
                eddie_signal TEXT,
                eddie_confidence INTEGER,
                maggie_status TEXT,
                maggie_signal TEXT,
                maggie_confidence INTEGER,
                report_path TEXT,
                json_blob TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES watchlist_runs(run_id)
            )
        """)

        # watchlist_ticker_deltas table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_ticker_deltas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                prior_run_id TEXT,
                purchase_value_delta REAL,
                purchase_count_delta INTEGER,
                sale_value_delta REAL,
                sale_count_delta INTEGER,
                new_transactions_estimate INTEGER,
                signal_changed INTEGER,
                confidence_delta INTEGER,
                summary TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES watchlist_runs(run_id),
                FOREIGN KEY (prior_run_id) REFERENCES watchlist_runs(run_id)
            )
        """)

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticker_results_run_ticker
            ON watchlist_ticker_results(run_id, ticker)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ticker_results_ticker_created
            ON watchlist_ticker_results(ticker, created_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_deltas_run_ticker
            ON watchlist_ticker_deltas(run_id, ticker)
        """)

        conn.commit()
        conn.close()

    def save_run(
        self,
        mode: str,
        tickers_requested: int,
        tickers_resolved: int,
        lookback_days: int,
        max_form4_filings: int,
        source_version: Optional[str] = None,
        git_commit: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Save a watchlist run record.

        Args:
            mode: Run mode (e.g., "manual_watchlist", "dry_run")
            tickers_requested: Number of tickers requested
            tickers_resolved: Number successfully resolved
            lookback_days: Lookback window in days
            max_form4_filings: Form 4 filing limit (0 = unlimited)
            source_version: Optional source version
            git_commit: Optional git commit hash
            notes: Optional notes

        Returns:
            run_id: Unique run identifier (UUID)
        """
        run_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO watchlist_runs (
                run_id, created_at, mode, tickers_requested, tickers_resolved,
                lookback_days, max_form4_filings, source_version, git_commit, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                created_at,
                mode,
                tickers_requested,
                tickers_resolved,
                lookback_days,
                max_form4_filings,
                source_version,
                git_commit,
                notes,
            ),
        )

        conn.commit()
        conn.close()

        return run_id

    def save_ticker_result(
        self,
        run_id: str,
        ticker: str,
        metrics: dict[str, Any],
        json_blob: Optional[dict[str, Any]] = None,
    ) -> int:
        """Save a ticker result for a given run.

        Args:
            run_id: Run identifier
            ticker: Ticker symbol
            metrics: Dict of ticker metrics (from extract_ticker_metrics)
            json_blob: Optional full JSON data for the ticker

        Returns:
            result_id: Auto-incremented result ID
        """
        created_at = datetime.now(timezone.utc).isoformat()

        # Serialize JSON blob if provided
        json_str = json.dumps(json_blob) if json_blob else None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO watchlist_ticker_results (
                run_id, ticker, cik, company_name, resolution_status,
                lookback_days, form4_filings_found, form4_filings_parsed,
                transactions_extracted, purchase_count, purchase_shares,
                purchase_value, sale_count, sale_shares, sale_value,
                net_purchase_value, purchase_to_sale_value_ratio,
                distinct_buyers, distinct_sellers, latest_purchase_date,
                latest_sale_date, eddie_status, eddie_signal, eddie_confidence,
                maggie_status, maggie_signal, maggie_confidence,
                report_path, json_blob, created_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                run_id,
                ticker,
                metrics.get("cik"),
                metrics.get("company_name"),
                metrics.get("resolution_status"),
                metrics.get("lookback_days"),
                metrics.get("form4_filings_found"),
                metrics.get("form4_filings_parsed"),
                metrics.get("transactions_extracted"),
                metrics.get("purchase_count"),
                metrics.get("purchase_shares"),
                metrics.get("purchase_value"),
                metrics.get("sale_count"),
                metrics.get("sale_shares"),
                metrics.get("sale_value"),
                metrics.get("net_purchase_value"),
                metrics.get("purchase_to_sale_value_ratio"),
                metrics.get("distinct_buyers"),
                metrics.get("distinct_sellers"),
                metrics.get("latest_purchase_date"),
                metrics.get("latest_sale_date"),
                metrics.get("eddie_status"),
                metrics.get("eddie_signal"),
                metrics.get("eddie_confidence"),
                metrics.get("maggie_status"),
                metrics.get("maggie_signal"),
                metrics.get("maggie_confidence"),
                metrics.get("report_path"),
                json_str,
                created_at,
            ),
        )

        result_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return result_id

    def get_most_recent_result_for_ticker(
        self, ticker: str, exclude_run_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Get the most recent saved result for a ticker.

        Args:
            ticker: Ticker symbol
            exclude_run_id: Optional run_id to exclude (to find prior run)

        Returns:
            Dict of ticker result, or None if no prior result exists
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if exclude_run_id:
            cursor.execute(
                """
                SELECT * FROM watchlist_ticker_results
                WHERE ticker = ? AND run_id != ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (ticker, exclude_run_id),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM watchlist_ticker_results
                WHERE ticker = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (ticker,),
            )

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def compute_delta(
        self, current_metrics: dict[str, Any], prior_result: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        """Compute delta between current metrics and prior result.

        Args:
            current_metrics: Current ticker metrics
            prior_result: Prior result from database (or None)

        Returns:
            Dict of delta metrics
        """
        if prior_result is None:
            return {
                "has_prior": False,
                "prior_run_id": None,
                "prior_created_at": None,
                "purchase_value_delta": None,
                "purchase_count_delta": None,
                "sale_value_delta": None,
                "sale_count_delta": None,
                "new_transactions_estimate": None,
                "signal_changed": False,
                "confidence_delta": None,
                "summary": "First run - no prior data",
            }

        # Compute deltas
        current_purchase_value = current_metrics.get("purchase_value", 0) or 0
        prior_purchase_value = prior_result.get("purchase_value", 0) or 0
        purchase_value_delta = current_purchase_value - prior_purchase_value

        current_purchase_count = current_metrics.get("purchase_count", 0) or 0
        prior_purchase_count = prior_result.get("purchase_count", 0) or 0
        purchase_count_delta = current_purchase_count - prior_purchase_count

        current_sale_value = current_metrics.get("sale_value", 0) or 0
        prior_sale_value = prior_result.get("sale_value", 0) or 0
        sale_value_delta = current_sale_value - prior_sale_value

        current_sale_count = current_metrics.get("sale_count", 0) or 0
        prior_sale_count = prior_result.get("sale_count", 0) or 0
        sale_count_delta = current_sale_count - prior_sale_count

        current_transactions = current_metrics.get("transactions_extracted", 0) or 0
        prior_transactions = prior_result.get("transactions_extracted", 0) or 0
        new_transactions_estimate = current_transactions - prior_transactions

        current_signal = current_metrics.get("eddie_signal")
        prior_signal = prior_result.get("eddie_signal")
        signal_changed = current_signal != prior_signal

        current_confidence = current_metrics.get("eddie_confidence", 0) or 0
        prior_confidence = prior_result.get("eddie_confidence", 0) or 0
        confidence_delta = current_confidence - prior_confidence

        # Generate summary
        summary_parts = []
        if purchase_value_delta > 0:
            summary_parts.append(f"+${purchase_value_delta:,.2f} purchases")
        elif purchase_value_delta < 0:
            summary_parts.append(f"${purchase_value_delta:,.2f} purchases")
        else:
            summary_parts.append("No purchase value change")

        if sale_value_delta > 0:
            summary_parts.append(f"+${sale_value_delta:,.2f} sales")
        elif sale_value_delta < 0:
            summary_parts.append(f"${sale_value_delta:,.2f} sales")

        if signal_changed:
            summary_parts.append(f"Signal changed: {prior_signal} → {current_signal}")

        summary = "; ".join(summary_parts) if summary_parts else "No significant changes"

        return {
            "has_prior": True,
            "prior_run_id": prior_result.get("run_id"),
            "prior_created_at": prior_result.get("created_at"),
            "purchase_value_delta": purchase_value_delta,
            "purchase_count_delta": purchase_count_delta,
            "sale_value_delta": sale_value_delta,
            "sale_count_delta": sale_count_delta,
            "new_transactions_estimate": new_transactions_estimate,
            "signal_changed": signal_changed,
            "confidence_delta": confidence_delta,
            "summary": summary,
        }

    def save_delta(
        self,
        run_id: str,
        ticker: str,
        delta: dict[str, Any],
    ) -> int:
        """Save a ticker delta record.

        Args:
            run_id: Current run identifier
            ticker: Ticker symbol
            delta: Delta dict from compute_delta

        Returns:
            delta_id: Auto-incremented delta ID
        """
        created_at = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO watchlist_ticker_deltas (
                run_id, ticker, prior_run_id, purchase_value_delta,
                purchase_count_delta, sale_value_delta, sale_count_delta,
                new_transactions_estimate, signal_changed, confidence_delta,
                summary, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                ticker,
                delta.get("prior_run_id"),
                delta.get("purchase_value_delta"),
                delta.get("purchase_count_delta"),
                delta.get("sale_value_delta"),
                delta.get("sale_count_delta"),
                delta.get("new_transactions_estimate"),
                1 if delta.get("signal_changed") else 0,
                delta.get("confidence_delta"),
                delta.get("summary"),
                created_at,
            ),
        )

        delta_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return delta_id

    def get_run_summary(self, run_id: str) -> Optional[dict[str, Any]]:
        """Get summary of a specific run.

        Args:
            run_id: Run identifier

        Returns:
            Dict with run metadata and ticker results
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get run metadata
        cursor.execute("SELECT * FROM watchlist_runs WHERE run_id = ?", (run_id,))
        run_row = cursor.fetchone()
        if not run_row:
            conn.close()
            return None

        run_dict = dict(run_row)

        # Get ticker results
        cursor.execute(
            "SELECT * FROM watchlist_ticker_results WHERE run_id = ? ORDER BY created_at",
            (run_id,),
        )
        ticker_rows = cursor.fetchall()
        run_dict["ticker_results"] = [dict(row) for row in ticker_rows]

        # Get deltas if any
        cursor.execute(
            "SELECT * FROM watchlist_ticker_deltas WHERE run_id = ? ORDER BY created_at",
            (run_id,),
        )
        delta_rows = cursor.fetchall()
        run_dict["deltas"] = [dict(row) for row in delta_rows]

        conn.close()
        return run_dict

    def get_all_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all runs, most recent first.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM watchlist_runs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_ticker_history(
        self, ticker: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get all historical results for a specific ticker.

        Args:
            ticker: Ticker symbol
            limit: Maximum number of results to return

        Returns:
            List of ticker result dicts, most recent first
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM watchlist_ticker_results
            WHERE ticker = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (ticker, limit),
        )
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
