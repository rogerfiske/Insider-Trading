"""Etherscan connector -- on-chain whale transfer monitoring via Etherscan API.

Uses the Etherscan API free tier to query recent ERC-20 token transfers
for WBTC, WETH, USDC, USDT.  Filters for large transfers (>= $5M) and
classifies direction based on known CEX addresses.

Requirements:
  - ETHERSCAN_API_KEY in .env (free at etherscan.io)
  - If no key is present, returns a clear failure result (does not crash)

Rate limit: free tier allows 5 calls/second.  This connector enforces
a 250ms delay between requests.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from evidence.schema import SourceEvidence, SourceFetchResult
from sources.base import BaseConnector
from sources.onchain_base import (
    TOKEN_CONTRACTS,
    TOKEN_DECIMALS,
    classify_address,
    estimate_usd_value,
    raw_to_token_amount,
)
from sources.sec_common import utcnow_iso


_API_BASE = "https://api.etherscan.io/api"
_REQUEST_TIMEOUT = 30
_MIN_REQUEST_INTERVAL = 0.25  # 250ms -> max 4 req/sec
_MIN_USD_VALUE = 5_000_000  # $5M threshold

# Module-level rate limiter
_last_request_time: float = 0.0


def _rate_limit() -> None:
    """Enforce minimum interval between Etherscan requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def _get_api_key() -> str | None:
    """Read the Etherscan API key from environment. Never log or print it."""
    return os.environ.get("ETHERSCAN_API_KEY")


class EtherscanConnector(BaseConnector):
    """Fetch recent large ERC-20 token transfers from Etherscan."""

    def __init__(
        self,
        tokens: dict[str, str] | None = None,
        min_usd_value: float = _MIN_USD_VALUE,
        prices: dict[str, float] | None = None,
    ) -> None:
        self.tokens = tokens or TOKEN_CONTRACTS
        self.min_usd_value = min_usd_value
        # Approximate prices for non-stablecoin tokens
        # In production, these would come from a price API
        self.prices = prices or {"WBTC": 100_000.0, "WETH": 3_500.0}

    def fetch(self) -> SourceFetchResult:
        """Fetch recent token transfers for tracked tokens."""
        api_key = _get_api_key()
        if not api_key:
            return SourceFetchResult.failure(
                source_name="etherscan",
                error_type="config_error",
                error_message=(
                    "ETHERSCAN_API_KEY not configured. "
                    "Get a free key at https://etherscan.io/apis"
                ),
            )

        all_evidence: list[SourceEvidence] = []
        errors: list[str] = []

        for symbol, contract in self.tokens.items():
            _rate_limit()

            url = (
                f"{_API_BASE}?module=account&action=tokentx"
                f"&contractaddress={contract}"
                f"&page=1&offset=100&sort=desc"
                f"&apikey={api_key}"
            )

            req = urllib.request.Request(url)
            req.add_header("Accept", "application/json")

            try:
                with urllib.request.urlopen(
                    req, timeout=_REQUEST_TIMEOUT
                ) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                TimeoutError,
            ) as e:
                errors.append(f"{symbol}: {e}")
                continue

            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                errors.append(f"{symbol}: Invalid JSON response")
                continue

            if data.get("status") != "1":
                msg = data.get("message", "Unknown error")
                errors.append(f"{symbol}: API error: {msg}")
                continue

            decimals = TOKEN_DECIMALS.get(symbol, 18)
            transfers = data.get("result", [])

            for tx in transfers:
                raw_value = tx.get("value", "0")
                token_amount = raw_to_token_amount(raw_value, decimals)
                usd_value = estimate_usd_value(
                    symbol, token_amount, self.prices
                )

                if usd_value < self.min_usd_value:
                    continue

                from_addr = tx.get("from", "")
                to_addr = tx.get("to", "")
                from_cex = classify_address(from_addr)
                to_cex = classify_address(to_addr)

                # Classify direction
                if from_cex and not to_cex:
                    direction = "accumulation"
                elif to_cex and not from_cex:
                    direction = "distribution"
                else:
                    direction = "unknown"

                tx_hash = tx.get("hash", "")
                timestamp = tx.get("timeStamp", "")
                try:
                    ts_dt = datetime.fromtimestamp(
                        int(timestamp), tz=timezone.utc
                    )
                    ts_iso = ts_dt.isoformat()
                except (ValueError, OSError):
                    ts_iso = timestamp

                all_evidence.append(
                    SourceEvidence(
                        source_type="etherscan",
                        source_name=f"Etherscan: {symbol}",
                        source_url=f"https://etherscan.io/tx/{tx_hash}",
                        retrieved_at=utcnow_iso(),
                        canonical_id=tx_hash or None,
                        raw_excerpt=json.dumps(
                            {
                                "from": from_addr,
                                "to": to_addr,
                                "value": raw_value,
                                "hash": tx_hash,
                            }
                        )[:2000],
                        normalized={
                            "chain": "ethereum",
                            "token_symbol": symbol,
                            "transaction_hash": tx_hash,
                            "from_address": from_addr,
                            "to_address": to_addr,
                            "amount": token_amount,
                            "usd_estimate": usd_value,
                            "timestamp": ts_iso,
                            "direction": direction,
                            "from_cex": from_cex,
                            "to_cex": to_cex,
                        },
                        metadata={
                            "explorer_url": f"https://etherscan.io/tx/{tx_hash}",
                            "contract_address": contract,
                        },
                    )
                )

        if not all_evidence and errors:
            return SourceFetchResult.failure(
                source_name="etherscan",
                error_type="fetch_error",
                error_message="; ".join(errors),
            )

        result = SourceFetchResult(
            ok=True,
            source_name="etherscan",
            evidence=all_evidence,
        )
        if errors:
            result.error_message = "; ".join(errors)
        return result

    def format_for_prompt(self, result: SourceFetchResult) -> str:
        """Format on-chain evidence as text for Claude's prompt."""
        if not result.ok:
            return (
                f"[Etherscan fetch FAILED: {result.error_message}]\n"
                "No live on-chain data is available for this run. "
                "Output a NEUTRAL signal with confidence 1."
            )

        if not result.evidence:
            return (
                "[Etherscan: No qualifying whale transfers (>= $5M) found.]\n"
                "Output a NEUTRAL signal with confidence 1 and reason "
                "'no qualifying whale moves in the last 6 hours'."
            )

        lines = [
            f"[Etherscan: {len(result.evidence)} large transfers found]",
            "",
        ]
        for i, ev in enumerate(result.evidence, 1):
            n = ev.normalized
            lines.append(
                f"{i}. {n.get('token_symbol', '?')} | "
                f"Amount: {n.get('amount', 0):,.2f} | "
                f"USD: ~${n.get('usd_estimate', 0):,.0f}"
            )
            direction = n.get("direction", "unknown")
            from_cex = n.get("from_cex", "")
            to_cex = n.get("to_cex", "")
            if direction == "accumulation":
                lines.append(
                    f"   Direction: ACCUMULATION (from {from_cex} -> private)"
                )
            elif direction == "distribution":
                lines.append(
                    f"   Direction: DISTRIBUTION (private -> to {to_cex})"
                )
            else:
                lines.append(f"   Direction: unknown")
            lines.append(f"   Tx: {n.get('transaction_hash', '?')}")
            lines.append(f"   Time: {n.get('timestamp', '?')}")
            lines.append("")

        if result.error_message:
            lines.append(f"[Partial errors: {result.error_message}]")
            lines.append("")

        lines.append(
            "Analyze these whale transfers. Pick the single most notable one. "
            "Classify as accumulation (BULLISH) or distribution (BEARISH)."
        )
        return "\n".join(lines)
