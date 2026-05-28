#!/usr/bin/env python3
"""
Maggie -- the smart-money tracker.

Reads the latest 13F-HR filings from the world's biggest institutional
funds. Compares against the prior quarter. Surfaces new positions, large
increases, and complete exits >= $50M. Emits one structured signal.

Schedule: weekly, Sunday 19:00 local time.

Source grounding: uses the Sec13FConnector to fetch real EDGAR data
before calling Claude.  Claude analyzes the fetched filings rather than
relying on training knowledge.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import log, run_scout

from evidence.schema import EvidenceBundle
from evidence.store import save_evidence
from sources.sec_13f import Sec13FConnector

FUNDS = [
    ("Berkshire Hathaway", "0001067983"),
    ("Bridgewater Associates", "0001350694"),
    ("Renaissance Technologies", "0001037389"),
    ("Citadel Advisors", "0001423053"),
    ("Two Sigma Investments", "0001179392"),
]

SYSTEM = """You are Maggie, a smart-money tracker. You watch the world's
biggest institutional funds. You only surface moves big enough to matter.

Your job:
  1. Review the LIVE SEC EDGAR 13F-HR data provided below.
  2. For each fund, analyze the most recent filing metadata.
  3. Classify each holding's change as:
       - NEW POSITION (held now, not prior quarter)
       - INCREASED (>= 25% larger position)
       - EXITED (held prior quarter, not now)
  4. Filter to value >= $50M.
  5. Pick THE SINGLE most notable move across all funds (largest value,
     bias toward NEW POSITION > INCREASED > EXITED for direction strength).

Output a short prose summary (one paragraph), followed by a STRICT JSON
signal on its own line:

  {"ticker": "<TICKER>", "direction": "BULLISH|BEARISH",
   "confidence": <1-5>, "reason": "<one-line>"}

Direction rules:
  - NEW POSITION or INCREASED -> BULLISH
  - EXITED -> BEARISH
Confidence: 1 = single fund, marginal size; 5 = multi-fund alignment or
$1B+ position from a top-tier fund.

If no fund has filed a new 13F since last run, output:

  {"ticker": "MACRO", "direction": "NEUTRAL", "confidence": 1,
   "reason": "no new 13F filings this week"}

Never invent positions. Only analyze the data provided below.
"""

USER_TEMPLATE = (
    "Analyze the following SEC EDGAR 13F-HR data for these institutional "
    "managers. Apply your filters. Pick the single most notable move. "
    "Output the prose summary followed by the JSON signal.\n\n"
    "{source_data}"
)


def main() -> int:
    """Run Maggie with source-grounded EDGAR 13F data."""
    # 1. Fetch deterministic source data
    connector = Sec13FConnector(managers=FUNDS)
    result = connector.fetch()

    # 2. Store evidence
    bundle = EvidenceBundle(agent="maggie", fetch_result=result)
    evidence_path = save_evidence(bundle)
    log("maggie", f"evidence stored: {evidence_path}")

    # 3. Format source data for Claude prompt
    source_data = connector.format_for_prompt(result)

    # 4. Run scout with grounded prompt
    user_prompt = USER_TEMPLATE.format(source_data=source_data)
    sig = run_scout("maggie", SYSTEM, user_prompt)

    print(f"[maggie] {sig.ticker} {sig.direction} conf={sig.confidence}")
    print(f"         {sig.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
