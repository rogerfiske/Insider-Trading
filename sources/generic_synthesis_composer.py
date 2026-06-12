"""
Generic SEC-Only Synthesis Composer

Composes a comprehensive synthesis packet from CP24B-CP24G extraction layers:
- CP24B: Ticker/CIK/submissions inventory
- CP24C: Form 4 insider transactions
- CP24D: Form 144 and 13D/G ownership filings
- CP24E: XBRL financials
- CP24F: Capital structure and dilution
- CP24G: 13F institutional ownership visibility

This module produces report-only synthesis outputs with no alert/notification code paths.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone


# Allowed scoring posture labels
ALLOWED_POSTURES = {
    "Strong insider-evidence / high uncertainty profile",
    "Strong insider-evidence / improving confirmation profile",
    "Mixed evidence / high uncertainty profile",
    "Weak insider-evidence / incomplete data profile",
    "Incomplete evidence",
    "High uncertainty",
    "Large operating company / institutional visibility profile"
}

# Allowed evidence directions
ALLOWED_DIRECTIONS = {"positive", "negative", "neutral", "unknown", "not_applicable"}

# Allowed evidence strengths
ALLOWED_STRENGTHS = {"high", "medium", "low", "not_applicable"}

# Allowed evidence confidence levels
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


class GenericSynthesisComposer:
    """
    Composes generic SEC-only synthesis packets from CP24B-CP24G outputs.

    This composer integrates multiple SEC extraction modules into a unified
    research packet with evidence matrix, scoring framework, and limitations.
    """

    def __init__(self, input_root: Path = Path("docs/sample_reports")):
        """
        Initialize the synthesis composer.

        Args:
            input_root: Root directory for CP24B-CP24G JSON outputs
        """
        self.input_root = input_root
        self.generated_at = datetime.now(timezone.utc).isoformat()

    def load_module_inputs(self, ticker: str) -> Dict[str, Any]:
        """
        Load all CP24B-CP24G JSON inputs for a ticker.

        Args:
            ticker: Ticker symbol

        Returns:
            Dictionary with module name -> parsed JSON content
        """
        modules = {}

        # CP24B: Ticker/CIK/submissions inventory
        inventory_path = self.input_root / "sec_inventory" / ticker / f"{ticker}_sec_inventory.json"
        modules["sec_inventory"] = self._load_json(inventory_path, required=True)

        # CP24C: Form 4 transactions
        form4_path = self.input_root / "form4_transactions" / ticker / f"{ticker}_form4_transactions.json"
        modules["form4_transactions"] = self._load_json(form4_path, required=True)

        # CP24D: Form 144 and 13D/G ownership filings
        ownership_path = self.input_root / "ownership_filings" / ticker / f"{ticker}_ownership_filings.json"
        modules["ownership_filings"] = self._load_json(ownership_path, required=True)

        # CP24E: XBRL financials
        # Try both standard path and batch path
        xbrl_path = self.input_root / "xbrl_financials" / ticker / f"{ticker}_xbrl_financials.json"
        xbrl_batch_path = self.input_root / "xbrl_financials" / "batch_maia_nvda" / ticker / f"{ticker}_xbrl_financials.json"

        if xbrl_path.exists():
            modules["xbrl_financials"] = self._load_json(xbrl_path, required=True)
        elif xbrl_batch_path.exists():
            modules["xbrl_financials"] = self._load_json(xbrl_batch_path, required=True)
        else:
            modules["xbrl_financials"] = {"status": "error", "error_type": "file_not_found"}

        # CP24F: Capital structure
        capital_path = self.input_root / "capital_structure" / ticker / f"{ticker}_capital_structure.json"
        modules["capital_structure"] = self._load_json(capital_path, required=True)

        # CP24G: 13F institutional ownership
        inst_path = self.input_root / "13f_institutional_ownership" / ticker / f"{ticker}_13f_institutional_ownership.json"
        modules["institutional_13f"] = self._load_json(inst_path, required=True)

        return modules

    def _load_json(self, path: Path, required: bool = False) -> Dict[str, Any]:
        """Load JSON file with error handling."""
        try:
            if not path.exists():
                if required:
                    return {"status": "error", "error_type": "file_not_found", "path": str(path)}
                return {}

            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            return {"status": "error", "error_type": "json_decode_error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error_type": "unknown_error", "error": str(e)}

    def validate_module_inputs(self, modules: Dict[str, Any]) -> Tuple[Dict[str, str], bool, List[str]]:
        """
        Validate module inputs and safety flags.

        Returns:
            (module_status dict, is_degraded boolean, degraded_reasons list)
        """
        module_status = {}
        is_degraded = False
        degraded_reasons = []

        for module_name, module_data in modules.items():
            if isinstance(module_data, dict):
                # Check for top-level status field
                status = module_data.get("status")

                # If no top-level status, check if it has ticker (indicates valid module)
                if status is None:
                    if "ticker" in module_data or "cik" in module_data:
                        # Valid module with data
                        status = "success"
                    else:
                        # Empty or invalid module
                        status = "unknown"

                if status == "success":
                    module_status[module_name] = "success"
                elif status == "error":
                    module_status[module_name] = f"error: {module_data.get('error_type', 'unknown')}"
                    is_degraded = True
                    degraded_reasons.append(f"{module_name}: {module_data.get('error_type', 'unknown')}")
                else:
                    module_status[module_name] = status
            else:
                module_status[module_name] = "unknown"
                is_degraded = True
                degraded_reasons.append(f"{module_name}: invalid format")

        return module_status, is_degraded, degraded_reasons

    def _is_module_valid(self, module_data: Dict[str, Any]) -> bool:
        """Check if a module has valid data."""
        if not isinstance(module_data, dict):
            return False

        # Check for error status
        if module_data.get("status") == "error":
            return False

        # Check if it has expected fields
        return "ticker" in module_data or "cik" in module_data or module_data.get("status") == "success"

    def build_evidence_matrix(self, ticker: str, modules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build evidence matrix from all modules.

        Returns:
            List of evidence rows with category, evidence, direction, strength, confidence, source
        """
        evidence = []

        # Ticker/CIK resolution
        inv = modules.get("sec_inventory", {})
        if self._is_module_valid(inv):
            evidence.append({
                "category": "Identity",
                "evidence": f"Ticker {ticker} resolved to CIK {inv.get('cik', 'unknown')}",
                "direction": "positive",
                "strength": "high",
                "confidence": "high",
                "source_module": "sec_inventory",
                "source_path": f"sec_inventory/{ticker}",
                "comment": "SEC EDGAR confirmation"
            })

        # SEC filing coverage
        if self._is_module_valid(inv):
            filing_stats = inv.get("filing_stats", {})
            total_filings = sum(filing_stats.get(ft, 0) for ft in ["4", "144", "13D", "13G", "10-Q", "10-K", "S-1", "S-3", "S-8", "8-K"])
            form4_count = filing_stats.get("4", 0)
            form10q_count = filing_stats.get("10-Q", 0)
            form10k_count = filing_stats.get("10-K", 0)

            evidence.append({
                "category": "Data Coverage",
                "evidence": f"{total_filings} SEC filings found across multiple form types",
                "direction": "positive",
                "strength": "high",
                "confidence": "high",
                "source_module": "sec_inventory",
                "source_path": f"sec_inventory/{ticker}",
                "comment": "Filing inventory completeness"
            })

            # Detailed Form 4 coverage
            if form4_count > 0:
                evidence.append({
                    "category": "Data Coverage",
                    "evidence": f"{form4_count} Form 4 insider transaction filings on record",
                    "direction": "positive",
                    "strength": "medium",
                    "confidence": "high",
                    "source_module": "sec_inventory",
                    "source_path": f"sec_inventory/{ticker}",
                    "comment": "Insider transaction filing coverage"
                })

            # Financial reporting coverage
            if form10q_count > 0 or form10k_count > 0:
                evidence.append({
                    "category": "Data Coverage",
                    "evidence": f"{form10q_count} quarterly (10-Q) and {form10k_count} annual (10-K) financial reports",
                    "direction": "positive",
                    "strength": "medium",
                    "confidence": "high",
                    "source_module": "sec_inventory",
                    "source_path": f"sec_inventory/{ticker}",
                    "comment": "Financial reporting coverage"
                })

        # Form 4 open-market activity
        form4 = modules.get("form4_transactions", {})
        if self._is_module_valid(form4):
            agg = form4.get("summary", {})
            open_purchases = agg.get("open_market_purchases", 0)
            open_sales = agg.get("open_market_sales", 0)
            purchase_value = agg.get("open_market_purchase_value", 0.0)

            if open_purchases > 0:
                evidence.append({
                    "category": "Insider Activity",
                    "evidence": f"{open_purchases} open-market insider purchases totaling ${purchase_value:,.2f}",
                    "direction": "positive",
                    "strength": "high",
                    "confidence": "high",
                    "source_module": "form4_transactions",
                    "source_path": f"form4_transactions/{ticker}",
                    "comment": "Open-market buying activity"
                })

            if open_sales > 0:
                sale_value = agg.get("open_market_sale_value", 0.0)
                evidence.append({
                    "category": "Insider Activity",
                    "evidence": f"{open_sales} open-market insider sales totaling ${sale_value:,.2f}",
                    "direction": "negative",
                    "strength": "medium",
                    "confidence": "high",
                    "source_module": "form4_transactions",
                    "source_path": f"form4_transactions/{ticker}",
                    "comment": "Open-market selling activity"
                })

            if open_purchases == 0 and open_sales == 0:
                evidence.append({
                    "category": "Insider Activity",
                    "evidence": "No open-market insider purchases or sales found",
                    "direction": "neutral",
                    "strength": "not_applicable",
                    "confidence": "high",
                    "source_module": "form4_transactions",
                    "source_path": f"form4_transactions/{ticker}",
                    "comment": "No open-market activity detected"
                })

            # Insider breadth
            distinct_buyers = agg.get("distinct_buyers", 0)
            if distinct_buyers > 0:
                evidence.append({
                    "category": "Insider Activity",
                    "evidence": f"{distinct_buyers} distinct insider(s) made open-market purchases",
                    "direction": "positive",
                    "strength": "medium",
                    "confidence": "high",
                    "source_module": "form4_transactions",
                    "source_path": f"form4_transactions/{ticker}",
                    "comment": "Breadth of insider buying interest"
                })

        # Form 144 sale-intent notices
        ownership = modules.get("ownership_filings", {})
        if self._is_module_valid(ownership):
            form144_summary = ownership.get("form144_summary", {})
            form144_count = form144_summary.get("total_filings", 0)
            if form144_count > 0:
                evidence.append({
                    "category": "Ownership Filings",
                    "evidence": f"{form144_count} Form 144 sale-intent notice(s) filed",
                    "direction": "neutral",
                    "strength": "medium",
                    "confidence": "high",
                    "source_module": "ownership_filings",
                    "source_path": f"ownership_filings/{ticker}",
                    "comment": "Form 144 is notice of proposed sale, not actual sale"
                })

        # 13D/G beneficial ownership
        if self._is_module_valid(ownership):
            dg_summary = ownership.get("ownership_13dg_summary", {})
            dg_count = dg_summary.get("total_filings", 0)
            active_13d = dg_summary.get("active_13d_count", 0)
            passive_13g = dg_summary.get("passive_13g_count", 0)
            if dg_count > 0:
                evidence.append({
                    "category": "Ownership Filings",
                    "evidence": f"{dg_count} Schedule 13D/G beneficial ownership filing(s) ({active_13d} active 13D, {passive_13g} passive 13G)",
                    "direction": "positive",
                    "strength": "medium",
                    "confidence": "high",
                    "source_module": "ownership_filings",
                    "source_path": f"ownership_filings/{ticker}",
                    "comment": "Large shareholder disclosure"
                })

        # 13F institutional visibility
        inst = modules.get("institutional_13f", {})
        if self._is_module_valid(inst):
            agg = inst.get("aggregate_stats", {})
            match_count = agg.get("match_count", 0)
            managers_parsed = agg.get("total_managers_parsed_successfully", 0)
            managers_total = agg.get("total_managers_reviewed", 0)

            if match_count > 0:
                total_value = agg.get("total_value_usd", 0.0)
                evidence.append({
                    "category": "Institutional Ownership",
                    "evidence": f"{match_count} institutional holdings matched (${total_value:,.0f} total value)",
                    "direction": "positive",
                    "strength": "medium",
                    "confidence": "medium",
                    "source_module": "institutional_13f",
                    "source_path": f"13f_institutional_ownership/{ticker}",
                    "comment": f"Partial visibility: {managers_parsed}/{managers_total} managers parsed"
                })
            else:
                evidence.append({
                    "category": "Institutional Ownership",
                    "evidence": f"No matches among {managers_parsed}/{managers_total} reviewed managers",
                    "direction": "neutral",
                    "strength": "not_applicable",
                    "confidence": "medium",
                    "source_module": "institutional_13f",
                    "source_path": f"13f_institutional_ownership/{ticker}",
                    "comment": "Institutional visibility is partial"
                })

        # Financial liquidity
        xbrl = modules.get("xbrl_financials", {})
        if self._is_module_valid(xbrl):
            # Get quarterly metrics (latest values are at top level of each metric)
            quarterly_metrics = xbrl.get("quarterly_metrics", {})
            cash_metric = quarterly_metrics.get("cash_and_cash_equivalents", {})
            cash = cash_metric.get("value")

            # Get derived metrics (at top level of XBRL JSON)
            derived = xbrl.get("derived_metrics", {})
            working_capital_obj = derived.get("working_capital", {})
            working_capital = working_capital_obj.get("value") if isinstance(working_capital_obj, dict) else working_capital_obj

            runway_obj = derived.get("cash_runway_months", {})
            runway = runway_obj.get("value") if isinstance(runway_obj, dict) else runway_obj

            if cash is not None:
                evidence.append({
                    "category": "Financial Liquidity",
                    "evidence": f"Cash and equivalents: ${cash:,.0f}",
                    "direction": "positive" if cash > 10_000_000 else "neutral",
                    "strength": "high",
                    "confidence": "high",
                    "source_module": "xbrl_financials",
                    "source_path": f"xbrl_financials/{ticker}",
                    "comment": "XBRL companyfacts API"
                })

            if working_capital is not None:
                evidence.append({
                    "category": "Financial Liquidity",
                    "evidence": f"Working capital: ${working_capital:,.0f}",
                    "direction": "positive" if working_capital > 0 else "negative",
                    "strength": "high",
                    "confidence": "high",
                    "source_module": "xbrl_financials",
                    "source_path": f"xbrl_financials/{ticker}",
                    "comment": "Current assets - current liabilities"
                })

            if runway is not None and runway != "not_meaningful":
                evidence.append({
                    "category": "Financial Liquidity",
                    "evidence": f"Cash runway: {runway:.1f} months",
                    "direction": "positive" if runway > 12 else "negative",
                    "strength": "high",
                    "confidence": "medium",
                    "source_module": "xbrl_financials",
                    "source_path": f"xbrl_financials/{ticker}",
                    "comment": "Based on trailing burn rate"
                })

            # Current ratio
            current_ratio_obj = derived.get("current_ratio", {})
            current_ratio = current_ratio_obj.get("value") if isinstance(current_ratio_obj, dict) else current_ratio_obj
            if current_ratio is not None:
                evidence.append({
                    "category": "Financial Liquidity",
                    "evidence": f"Current ratio: {current_ratio:.2f}",
                    "direction": "positive" if current_ratio > 1.0 else "negative",
                    "strength": "medium",
                    "confidence": "high",
                    "source_module": "xbrl_financials",
                    "source_path": f"xbrl_financials/{ticker}",
                    "comment": "Current assets / current liabilities"
                })

        # Capital structure and dilution
        capital = modules.get("capital_structure", {})
        if self._is_module_valid(capital):
            share_counts = capital.get("share_counts", {})
            common_shares = share_counts.get("common_shares_outstanding")

            dilution_metrics = capital.get("derived_dilution_metrics", {})
            dilution_low = dilution_metrics.get("dilution_overhang_percent_low")
            dilution_high = dilution_metrics.get("dilution_overhang_percent_high")

            if common_shares is not None:
                evidence.append({
                    "category": "Capital Structure",
                    "evidence": f"Common shares outstanding: {common_shares:,}",
                    "direction": "neutral",
                    "strength": "high",
                    "confidence": "high",
                    "source_module": "capital_structure",
                    "source_path": f"capital_structure/{ticker}",
                    "comment": "XBRL-sourced share count"
                })

            if dilution_low is not None and dilution_high is not None:
                evidence.append({
                    "category": "Capital Structure",
                    "evidence": f"Dilution overhang: {dilution_low:.1f}% - {dilution_high:.1f}%",
                    "direction": "negative" if dilution_high > 40 else "neutral",
                    "strength": "medium",
                    "confidence": "medium",
                    "source_module": "capital_structure",
                    "source_path": f"capital_structure/{ticker}",
                    "comment": "Fully diluted share estimate / current shares"
                })

        return evidence

    def calculate_scores(self, evidence: List[Dict[str, Any]], modules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate synthesis scores from evidence matrix.

        Returns:
            Dictionary with scoring components and overall posture
        """
        # Insider evidence score
        insider_score = self._calculate_insider_evidence_score(modules.get("form4_transactions", {}))

        # Capital structure risk score
        capital_score = self._calculate_capital_structure_risk_score(modules.get("capital_structure", {}))

        # Financial liquidity score
        liquidity_score = self._calculate_financial_liquidity_score(modules.get("xbrl_financials", {}))

        # Ownership visibility score
        ownership_score = self._calculate_ownership_visibility_score(modules.get("institutional_13f", {}))

        # Data quality score
        data_quality_score = self._calculate_data_quality_score(modules)

        # Overall posture
        overall_posture = self._determine_overall_posture(
            insider_score, capital_score, liquidity_score, ownership_score, data_quality_score, modules
        )

        return {
            "insider_evidence_score": insider_score,
            "capital_structure_risk_score": capital_score,
            "financial_liquidity_score": liquidity_score,
            "ownership_visibility_score": ownership_score,
            "data_quality_score": data_quality_score,
            "overall_research_posture": overall_posture
        }

    def _calculate_insider_evidence_score(self, form4_data: Dict[str, Any]) -> Optional[int]:
        """Calculate insider evidence score (0-100) based on Form 4 activity."""
        if not self._is_module_valid(form4_data):
            return None

        agg = form4_data.get("summary", {})
        open_purchases = agg.get("open_market_purchases", 0)
        open_sales = agg.get("open_market_sales", 0)
        distinct_buyers = agg.get("distinct_buyers", 0)

        if open_purchases == 0:
            return 0  # No insider buying activity

        # Base score from purchase count
        score = min(40, open_purchases * 2)  # Cap at 40

        # Bonus for multiple buyers
        if distinct_buyers > 1:
            score += min(30, distinct_buyers * 5)  # Cap at 30

        # Penalty for selling activity
        if open_sales > 0:
            score -= min(20, open_sales)  # Max penalty 20

        return max(0, min(100, score))

    def _calculate_capital_structure_risk_score(self, capital_data: Dict[str, Any]) -> Optional[int]:
        """Calculate capital structure risk score (0-100, lower is less risky)."""
        if not self._is_module_valid(capital_data):
            return None

        dilution_metrics = capital_data.get("derived_dilution_metrics", {})
        dilution_high = dilution_metrics.get("dilution_overhang_percent_high")

        if dilution_high is None:
            return None

        # 0% dilution = 0 risk, 100% dilution = 100 risk
        risk_score = min(100, int(dilution_high))

        return risk_score

    def _calculate_financial_liquidity_score(self, xbrl_data: Dict[str, Any]) -> Optional[int]:
        """Calculate financial liquidity score (0-100)."""
        if not self._is_module_valid(xbrl_data):
            return None

        derived = xbrl_data.get("derived_metrics", {})
        runway_obj = derived.get("cash_runway_months", {})
        runway = runway_obj.get("value") if isinstance(runway_obj, dict) else runway_obj

        if runway is None or runway == "not_meaningful":
            # Profitable companies get max score
            return 100

        # Convert runway to score: 0 months = 0, 24+ months = 100
        score = min(100, int((runway / 24) * 100))

        return score

    def _calculate_ownership_visibility_score(self, inst_data: Dict[str, Any]) -> Optional[int]:
        """Calculate ownership visibility score (0-100)."""
        if not self._is_module_valid(inst_data):
            return None

        agg = inst_data.get("aggregate_stats", {})
        managers_parsed = agg.get("total_managers_parsed_successfully", 0)
        managers_total = agg.get("total_managers_reviewed", 0)
        match_count = agg.get("match_count", 0)

        if managers_total == 0:
            return 0

        # Base score from parse success rate
        parse_rate = managers_parsed / managers_total
        score = int(parse_rate * 50)  # Max 50 points

        # Bonus for finding institutional holdings
        if match_count > 0:
            score += 50

        return min(100, score)

    def _calculate_data_quality_score(self, modules: Dict[str, Any]) -> int:
        """Calculate overall data quality score based on module success rates."""
        total_modules = len(modules)
        successful_modules = sum(1 for m in modules.values() if self._is_module_valid(m))

        if total_modules == 0:
            return 0

        return int((successful_modules / total_modules) * 100)

    def _determine_overall_posture(
        self,
        insider_score: Optional[int],
        capital_score: Optional[int],
        liquidity_score: Optional[int],
        ownership_score: Optional[int],
        data_quality_score: int,
        modules: Dict[str, Any]
    ) -> str:
        """Determine overall research posture label."""

        # Check if this is a large operating company (NVDA-like)
        # Use liquidity score as proxy: score of 100 with no meaningful runway = profitable
        is_profitable = (liquidity_score == 100)

        # Large profitable company with institutional visibility
        if is_profitable and ownership_score and ownership_score >= 50:
            return "Large operating company / institutional visibility profile"

        # Incomplete data
        if data_quality_score < 50:
            return "Incomplete evidence"

        # Strong insider evidence
        if insider_score and insider_score >= 70:
            if ownership_score and ownership_score >= 50:
                return "Strong insider-evidence / improving confirmation profile"
            else:
                return "Strong insider-evidence / high uncertainty profile"

        # Weak insider evidence
        if insider_score is not None and insider_score < 30:
            return "Weak insider-evidence / incomplete data profile"

        # Mixed evidence
        if insider_score and 30 <= insider_score < 70:
            return "Mixed evidence / high uncertainty profile"

        # Default
        return "High uncertainty"

    def build_key_findings(self, evidence: List[Dict[str, Any]], modules: Dict[str, Any]) -> List[str]:
        """Extract key findings from evidence matrix."""
        findings = []

        # Insider activity findings
        form4 = modules.get("form4_transactions", {})
        if self._is_module_valid(form4):
            agg = form4.get("summary", {})
            open_purchases = agg.get("open_market_purchases", 0)
            if open_purchases > 0:
                findings.append(
                    f"{open_purchases} open-market insider purchases detected "
                    f"totaling ${agg.get('open_market_purchase_value', 0):,.2f}"
                )

        # Financial findings
        xbrl = modules.get("xbrl_financials", {})
        if self._is_module_valid(xbrl):
            derived = xbrl.get("derived_metrics", {})
            runway_obj = derived.get("cash_runway_months", {})
            runway = runway_obj.get("value") if isinstance(runway_obj, dict) else runway_obj
            if runway and runway != "not_meaningful":
                findings.append(f"Estimated cash runway: {runway:.1f} months based on trailing burn")

        # Dilution findings
        capital = modules.get("capital_structure", {})
        if self._is_module_valid(capital):
            dilution_metrics = capital.get("derived_dilution_metrics", {})
            overhang_high = dilution_metrics.get("dilution_overhang_percent_high")
            if overhang_high and overhang_high > 40:
                findings.append(f"Significant dilution overhang: {overhang_high:.1f}% (high estimate)")

        return findings

    def build_critical_unknowns(self, modules: Dict[str, Any]) -> List[str]:
        """Identify critical unknowns and data gaps."""
        unknowns = []

        # Institutional ownership coverage limitation
        inst = modules.get("institutional_13f", {})
        if self._is_module_valid(inst):
            agg = inst.get("aggregate_stats", {})
            managers_failed = agg.get("total_managers_parse_failed", 0)
            if managers_failed > 0:
                unknowns.append(
                    f"Institutional visibility partial: {managers_failed} manager(s) failed to parse"
                )

        # Missing module data
        for module_name, module_data in modules.items():
            if module_data.get("status") == "error":
                unknowns.append(f"{module_name} data unavailable: {module_data.get('error_type', 'unknown')}")

        return unknowns

    def build_monitoring_triggers(self, modules: Dict[str, Any]) -> List[str]:
        """Identify monitoring triggers for future updates."""
        triggers = []

        # Form 4 monitoring
        form4 = modules.get("form4_transactions", {})
        if self._is_module_valid(form4):
            agg = form4.get("summary", {})
            if agg.get("open_market_purchases", 0) > 0:
                triggers.append("Monitor for additional insider buying activity (Form 4 filings)")

        # Financial monitoring
        xbrl = modules.get("xbrl_financials", {})
        if self._is_module_valid(xbrl):
            derived = xbrl.get("derived_metrics", {})
            runway_obj = derived.get("cash_runway_months", {})
            runway = runway_obj.get("value") if isinstance(runway_obj, dict) else runway_obj
            if runway and runway != "not_meaningful" and runway < 12:
                triggers.append("Monitor for capital raises or burn rate improvements (10-Q filings)")

        return triggers

    def build_limitations(self, modules: Dict[str, Any]) -> List[str]:
        """Build comprehensive limitations list."""
        limitations = [
            "SEC-sourced data only; no live market data",
            "13F institutional ownership coverage limited to reviewed managers",
            "Form 144 indicates proposed sale intent, not actual sale execution",
            "XBRL financial data reflects most recent filing, not real-time status",
            "Capital structure estimates include disclosed instruments only",
            "No clinical/regulatory live catalyst extraction",
            "This is a research synthesis, not investment advice"
        ]

        return limitations

    def compose_synthesis(self, ticker: str) -> Dict[str, Any]:
        """
        Compose complete synthesis packet for a ticker.

        Args:
            ticker: Ticker symbol

        Returns:
            Complete synthesis JSON structure
        """
        # Load all module inputs
        modules = self.load_module_inputs(ticker)

        # Validate inputs
        module_status, is_degraded, degraded_reasons = self.validate_module_inputs(modules)

        # Extract basic ticker info
        inv = modules.get("sec_inventory", {})
        cik = inv.get("cik", "unknown")
        company_name = inv.get("company_name", "unknown")

        # Build evidence matrix
        evidence = self.build_evidence_matrix(ticker, modules)

        # Calculate scores
        scores = self.calculate_scores(evidence, modules)

        # Build findings and unknowns
        key_findings = self.build_key_findings(evidence, modules)
        critical_unknowns = self.build_critical_unknowns(modules)
        monitoring_triggers = self.build_monitoring_triggers(modules)
        limitations = self.build_limitations(modules)

        # Build evidence provenance
        evidence_provenance = self._build_evidence_provenance(modules)

        # Compose synthesis packet
        synthesis = {
            "ticker": ticker,
            "cik": cik,
            "company_name": company_name,
            "generated_at": self.generated_at,
            "source_modules": {
                "sec_inventory": {
                    "path": f"sec_inventory/{ticker}",
                    "status": modules["sec_inventory"].get("status", "unknown")
                },
                "form4_transactions": {
                    "path": f"form4_transactions/{ticker}",
                    "status": modules["form4_transactions"].get("status", "unknown")
                },
                "ownership_filings": {
                    "path": f"ownership_filings/{ticker}",
                    "status": modules["ownership_filings"].get("status", "unknown")
                },
                "xbrl_financials": {
                    "path": f"xbrl_financials/{ticker}",
                    "status": modules["xbrl_financials"].get("status", "unknown")
                },
                "capital_structure": {
                    "path": f"capital_structure/{ticker}",
                    "status": modules["capital_structure"].get("status", "unknown")
                },
                "institutional_13f": {
                    "path": f"13f_institutional_ownership/{ticker}",
                    "status": modules["institutional_13f"].get("status", "unknown")
                }
            },
            "module_status": module_status,
            "evidence_matrix": evidence,
            "synthesis_scores": scores,
            "key_findings": key_findings,
            "critical_unknowns": critical_unknowns,
            "monitoring_triggers": monitoring_triggers,
            "limitations": limitations,
            "degraded_mode": {
                "is_degraded": is_degraded,
                "reasons": degraded_reasons
            },
            "evidence_provenance": evidence_provenance,
            "safety": {
                "report_only": True,
                "alerts_generated": False,
                "external_spreadsheet_used": False,
                "telegram_sent": False,
                "email_sent": False,
                "scheduled_tasks_modified": False,
                "env_printed_or_changed": False,
                "buy_sell_hold_language_used": False
            }
        }

        return synthesis

    def _build_evidence_provenance(self, modules: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build evidence provenance list."""
        provenance = []

        for module_name, module_data in modules.items():
            if self._is_module_valid(module_data):
                provenance.append({
                    "module": module_name,
                    "source": "SEC EDGAR public filings",
                    "timestamp": module_data.get("generated_at", "unknown")
                })

        return provenance

    def write_synthesis_outputs(
        self,
        ticker: str,
        synthesis: Dict[str, Any],
        output_dir: Path
    ) -> None:
        """
        Write synthesis JSON, Markdown, and evidence CSV outputs.

        Args:
            ticker: Ticker symbol
            synthesis: Synthesis packet
            output_dir: Output directory
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON
        json_path = output_dir / f"{ticker}_generic_sec_synthesis.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(synthesis, f, indent=2, ensure_ascii=False)

        # Write Markdown
        md_path = output_dir / f"{ticker}_generic_sec_synthesis.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._generate_markdown_report(ticker, synthesis))

        # Write evidence CSV
        csv_path = output_dir / f"{ticker}_evidence_matrix.csv"
        self._write_evidence_csv(synthesis["evidence_matrix"], csv_path)

    def _generate_markdown_report(self, ticker: str, synthesis: Dict[str, Any]) -> str:
        """Generate comprehensive Markdown synthesis report."""
        lines = []

        # Header
        lines.append(f"# {ticker} — Generic SEC Synthesis Packet")
        lines.append("")
        lines.append(f"**Company:** {synthesis['company_name']}")
        lines.append(f"**CIK:** {synthesis['cik']}")
        lines.append(f"**Generated:** {synthesis['generated_at']}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Purpose and source boundary
        lines.append("## Purpose and Source Boundary")
        lines.append("")
        lines.append("This synthesis composes SEC EDGAR public filing data from CP24B-CP24G extraction layers:")
        lines.append("")
        lines.append("- CP24B: Ticker/CIK/submissions inventory")
        lines.append("- CP24C: Form 4 insider transactions")
        lines.append("- CP24D: Form 144 and 13D/G ownership filings")
        lines.append("- CP24E: XBRL financials")
        lines.append("- CP24F: Capital structure and dilution")
        lines.append("- CP24G: 13F institutional ownership visibility")
        lines.append("")
        lines.append("**This is a research synthesis, not investment advice.**")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Input module status
        lines.append("## Input Module Status")
        lines.append("")
        lines.append("| Module | Status |")
        lines.append("|--------|--------|")
        for module, status in synthesis["module_status"].items():
            lines.append(f"| {module} | {status} |")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive research posture
        scores = synthesis["synthesis_scores"]
        lines.append("## Executive Research Posture")
        lines.append("")
        lines.append(f"**Overall Posture:** {scores['overall_research_posture']}")
        lines.append("")
        lines.append("**Scoring Components:**")
        lines.append("")
        lines.append("| Component | Score | Comment |")
        lines.append("|-----------|-------|---------|")

        if scores["insider_evidence_score"] is not None:
            lines.append(f"| Insider Evidence | {scores['insider_evidence_score']}/100 | Form 4 activity strength |")
        else:
            lines.append("| Insider Evidence | N/A | Data unavailable |")

        if scores["capital_structure_risk_score"] is not None:
            lines.append(f"| Capital Structure Risk | {scores['capital_structure_risk_score']}/100 | Lower is less risky |")
        else:
            lines.append("| Capital Structure Risk | N/A | Data unavailable |")

        if scores["financial_liquidity_score"] is not None:
            lines.append(f"| Financial Liquidity | {scores['financial_liquidity_score']}/100 | Higher is better |")
        else:
            lines.append("| Financial Liquidity | N/A | Data unavailable |")

        if scores["ownership_visibility_score"] is not None:
            lines.append(f"| Ownership Visibility | {scores['ownership_visibility_score']}/100 | Institutional coverage |")
        else:
            lines.append("| Ownership Visibility | N/A | Data unavailable |")

        lines.append(f"| Data Quality | {scores['data_quality_score']}/100 | Module success rate |")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Evidence matrix (top 10 rows)
        lines.append("## Evidence Matrix (Top 10)")
        lines.append("")
        lines.append("| Category | Evidence | Direction | Strength | Confidence | Source |")
        lines.append("|----------|----------|-----------|----------|------------|--------|")

        for row in synthesis["evidence_matrix"][:10]:
            lines.append(
                f"| {row['category']} | {row['evidence']} | "
                f"{row['direction']} | {row['strength']} | "
                f"{row['confidence']} | {row['source_module']} |"
            )

        total_evidence = len(synthesis["evidence_matrix"])
        if total_evidence > 10:
            lines.append("")
            lines.append(f"*Showing 10 of {total_evidence} evidence rows. See {ticker}_evidence_matrix.csv for complete matrix.*")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Key findings
        lines.append("## Key Findings")
        lines.append("")
        if synthesis["key_findings"]:
            for finding in synthesis["key_findings"]:
                lines.append(f"- {finding}")
        else:
            lines.append("*No key findings identified.*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Critical unknowns
        lines.append("## Critical Unknowns")
        lines.append("")
        if synthesis["critical_unknowns"]:
            for unknown in synthesis["critical_unknowns"]:
                lines.append(f"- {unknown}")
        else:
            lines.append("*No critical unknowns identified.*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Monitoring triggers
        lines.append("## Monitoring Triggers")
        lines.append("")
        if synthesis["monitoring_triggers"]:
            for trigger in synthesis["monitoring_triggers"]:
                lines.append(f"- {trigger}")
        else:
            lines.append("*No specific monitoring triggers identified.*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Limitations
        lines.append("## Limitations")
        lines.append("")
        for limitation in synthesis["limitations"]:
            lines.append(f"- {limitation}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Degraded mode
        if synthesis["degraded_mode"]["is_degraded"]:
            lines.append("## Degraded Mode")
            lines.append("")
            lines.append("**This synthesis is operating in degraded mode due to:**")
            lines.append("")
            for reason in synthesis["degraded_mode"]["reasons"]:
                lines.append(f"- {reason}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Evidence provenance
        lines.append("## Evidence Provenance")
        lines.append("")
        lines.append("| Module | Source | Timestamp |")
        lines.append("|--------|--------|-----------|")
        for prov in synthesis["evidence_provenance"]:
            lines.append(f"| {prov['module']} | {prov['source']} | {prov['timestamp']} |")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Safety confirmations
        lines.append("## Safety Confirmations")
        lines.append("")
        safety = synthesis["safety"]
        lines.append("| Flag | Value |")
        lines.append("|------|-------|")
        lines.append(f"| Report only | {safety['report_only']} |")
        lines.append(f"| Alerts generated | {safety['alerts_generated']} |")
        lines.append(f"| External spreadsheet used | {safety['external_spreadsheet_used']} |")
        lines.append(f"| Telegram sent | {safety['telegram_sent']} |")
        lines.append(f"| Email sent | {safety['email_sent']} |")
        lines.append(f"| Scheduled tasks modified | {safety['scheduled_tasks_modified']} |")
        lines.append(f"| Env printed or changed | {safety['env_printed_or_changed']} |")
        lines.append(f"| Buy/sell/hold language used | {safety['buy_sell_hold_language_used']} |")
        lines.append("")
        lines.append("---")
        lines.append("")

        # No-recommendation statement
        lines.append("## No-Recommendation Statement")
        lines.append("")
        lines.append("This document is a research synthesis of SEC public filing data.")
        lines.append("It does not constitute investment advice, a recommendation to buy or sell securities,")
        lines.append("or a price target. All SEC data is presented as-is for research purposes only.")
        lines.append("")

        return "\n".join(lines)

    def _write_evidence_csv(self, evidence: List[Dict[str, Any]], csv_path: Path) -> None:
        """Write evidence matrix to CSV."""
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["category", "evidence", "direction", "strength", "confidence", "source_module", "source_path", "comment"]
            )
            writer.writeheader()
            writer.writerows(evidence)

    def compose_batch_summary(
        self,
        tickers: List[str],
        syntheses: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compose batch summary for multiple tickers.

        Args:
            tickers: List of ticker symbols
            syntheses: Dict mapping ticker -> synthesis packet

        Returns:
            Batch summary JSON structure
        """
        summary = {
            "generated_at": self.generated_at,
            "tickers_requested": tickers,
            "tickers_success": [t for t, s in syntheses.items() if s.get("module_status")],
            "tickers_failed": [t for t in tickers if t not in syntheses],
            "per_ticker_summary": [],
            "safety": {
                "report_only": True,
                "alerts_generated": False,
                "external_spreadsheet_used": False,
                "telegram_sent": False,
                "email_sent": False,
                "scheduled_tasks_modified": False,
                "env_printed_or_changed": False,
                "buy_sell_hold_language_used": False
            }
        }

        for ticker in tickers:
            if ticker in syntheses:
                syn = syntheses[ticker]
                summary["per_ticker_summary"].append({
                    "ticker": ticker,
                    "company_name": syn.get("company_name", "unknown"),
                    "overall_posture": syn["synthesis_scores"]["overall_research_posture"],
                    "data_quality_score": syn["synthesis_scores"]["data_quality_score"],
                    "is_degraded": syn["degraded_mode"]["is_degraded"]
                })

        return summary

    def write_batch_summary_outputs(
        self,
        summary: Dict[str, Any],
        output_dir: Path
    ) -> None:
        """Write batch summary JSON and Markdown."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON
        json_path = output_dir / "batch_generic_sec_synthesis_summary.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Write Markdown
        md_path = output_dir / "batch_generic_sec_synthesis_summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self._generate_batch_markdown(summary))

    def _generate_batch_markdown(self, summary: Dict[str, Any]) -> str:
        """Generate batch summary Markdown report."""
        lines = []

        lines.append("# Batch Generic SEC Synthesis Summary")
        lines.append("")
        lines.append(f"**Generated:** {summary['generated_at']}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Tickers requested
        lines.append("## Tickers Requested")
        lines.append("")
        lines.append(", ".join(summary["tickers_requested"]))
        lines.append("")
        lines.append("---")
        lines.append("")

        # Per-ticker status
        lines.append("## Per-Ticker Status")
        lines.append("")
        lines.append("| Ticker | Company | Overall Posture | Data Quality | Degraded |")
        lines.append("|--------|---------|-----------------|--------------|----------|")

        for t in summary["per_ticker_summary"]:
            lines.append(
                f"| {t['ticker']} | {t['company_name']} | {t['overall_posture']} | "
                f"{t['data_quality_score']}/100 | {t['is_degraded']} |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")

        # Safety confirmations
        lines.append("## Safety Confirmations")
        lines.append("")
        safety = summary["safety"]
        lines.append("| Flag | Value |")
        lines.append("|------|-------|")
        lines.append(f"| Report only | {safety['report_only']} |")
        lines.append(f"| Alerts generated | {safety['alerts_generated']} |")
        lines.append(f"| External spreadsheet used | {safety['external_spreadsheet_used']} |")
        lines.append(f"| Telegram sent | {safety['telegram_sent']} |")
        lines.append(f"| Email sent | {safety['email_sent']} |")
        lines.append(f"| Scheduled tasks modified | {safety['scheduled_tasks_modified']} |")
        lines.append(f"| Env printed or changed | {safety['env_printed_or_changed']} |")
        lines.append(f"| Buy/sell/hold language used | {safety['buy_sell_hold_language_used']} |")
        lines.append("")

        return "\n".join(lines)
