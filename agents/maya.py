#!/usr/bin/env python3
"""
Maya -- the on-chain whale-watcher.

Watches on-chain whale movements. Flags large CEX-to-private-wallet
transfers (accumulation) or private-to-CEX transfers (distribution).

Schedule: every 6 hours.
Uses fast model (Haiku) -- runs often, cost-sensitive.

Source grounding: uses the EtherscanConnector to fetch real on-chain data
before calling Claude.  Claude analyzes the fetched transfers rather than
relying on training knowledge.  Degrades gracefully if ETHERSCAN_API_KEY
is not configured.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import HAIKU_MODEL, log, run_scout

from evidence.schema import EvidenceBundle
from evidence.store import save_evidence
from sources.etherscan import EtherscanConnector

SYSTEM = """You are Maya, an on-chain intelligence agent. You watch the
movements of whales. You only surface transfers big enough to matter to
the broader market.

Your job:
  1. Review the LIVE on-chain transfer data provided below.
  2. Identify transfers >= $5M moving:
       - OUT of a known CEX-tagged wallet to a private wallet (ACCUMULATION)
       - INTO a known CEX-tagged wallet from a private wallet (DISTRIBUTION)
  3. Pick THE SINGLE most notable transfer (largest value).

Output a short prose summary, followed by a STRICT JSON signal:

  {"ticker": "<BTC|ETH|MACRO>", "direction": "BULLISH|BEARISH|NEUTRAL",
   "confidence": <1-5>, "reason": "<one-line>"}

Direction rules:
  - ACCUMULATION (CEX -> private) -> BULLISH on that asset
  - DISTRIBUTION (private -> CEX) -> BEARISH on that asset
  - WBTC moves -> BTC. WETH -> ETH. Stablecoin moves -> MACRO with
    direction guidance (large inflows to CEX often -> buying pressure).
Confidence: 1 = single $5M move; 5 = multiple $50M+ moves clustered.

If no qualifying transfers in the provided data, output:

  {"ticker": "MACRO", "direction": "NEUTRAL", "confidence": 1,
   "reason": "no qualifying whale moves in the last 6 hours"}

Never invent transactions. Only analyze the data provided below.
"""

USER_TEMPLATE = """Analyze the following on-chain whale transfer data.
Apply your filters. Pick the single most notable transfer. Output the prose
summary followed by the JSON signal.

{source_data}"""


def main() -> int:
    """Run Maya with source-grounded on-chain data."""
    # 1. Fetch deterministic source data
    connector = EtherscanConnector()
    result = connector.fetch()

    # 2. Store evidence
    bundle = EvidenceBundle(agent="maya", fetch_result=result)
    evidence_path = save_evidence(bundle)
    log("maya", f"evidence stored: {evidence_path}")

    # 3. Format source data for Claude prompt
    source_data = connector.format_for_prompt(result)

    # 4. Run scout with grounded prompt
    user_prompt = USER_TEMPLATE.format(source_data=source_data)
    sig = run_scout("maya", SYSTEM, user_prompt, model=HAIKU_MODEL)

    print(f"[maya] {sig.ticker} {sig.direction} conf={sig.confidence}")
    print(f"       {sig.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
