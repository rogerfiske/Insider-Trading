#!/usr/bin/env python3
"""
Eddie -- the SEC Form 4 watcher.

Reads SEC Form 4 filings published in the last 24 hours, filters for
open-market insider buys >= $100,000 by C-suite officers / directors,
and emits a single structured signal for Sophie's consensus engine.

Schedule: daily, 06:00 local time.

Source grounding: uses the SecForm4Connector to fetch real EDGAR data
before calling Claude.  Claude analyzes the fetched filings rather than
relying on training knowledge.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Add repo root for sources/ and evidence/ imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import log, run_scout

from evidence.schema import EvidenceBundle
from evidence.store import save_evidence
from sources.sec_form4 import SecForm4Connector

SYSTEM = """You are Eddie, a financial intelligence agent. Your job is to
watch every Form 4 insider filing published by the SEC in the last 24
hours. You only surface buys that matter.

Your job:
  1. Review the LIVE SEC EDGAR Form 4 data provided below.
  2. Identify filings where:
       - Transaction code = P (open-market purchase)
       - Total value >= $100,000
       - Filer role of CEO, CFO, President, Chairman, or Director
  3. Group multiple buys by the same insider on the same day.
  4. Pick THE SINGLE most notable buy (highest value, then highest seniority).

Then output a short prose summary (one paragraph), followed by a STRICT
JSON object on its own line, exactly in this shape:

  {"ticker": "<TICKER>", "direction": "BULLISH",
   "confidence": <1-5>, "reason": "<one-line plain English>"}

Confidence scale: 1 = small buy, sub-CEO; 5 = CEO buying >$1M of own stock.

If no qualifying filings exist in the provided data, output:

  {"ticker": "MACRO", "direction": "NEUTRAL", "confidence": 1,
   "reason": "no qualifying Form 4 insider buys in the last 24 hours"}

Never invent filings. Only analyze the data provided below.
"""

USER_TEMPLATE = """Analyze the following SEC EDGAR Form 4 data and apply your
filters. Pick the single most notable buy. Output the prose summary followed
by the JSON signal.

{source_data}"""


def main() -> int:
    """Run Eddie with source-grounded EDGAR data."""
    # 1. Fetch deterministic source data
    connector = SecForm4Connector()
    result = connector.fetch()

    # 2. Store evidence
    bundle = EvidenceBundle(agent="eddie", fetch_result=result)
    evidence_path = save_evidence(bundle)
    log("eddie", f"evidence stored: {evidence_path}")

    # 3. Format source data for Claude prompt
    source_data = connector.format_for_prompt(result)

    # 4. Run scout with grounded prompt
    user_prompt = USER_TEMPLATE.format(source_data=source_data)
    sig = run_scout("eddie", SYSTEM, user_prompt)

    print(f"[eddie] {sig.ticker} {sig.direction} conf={sig.confidence}")
    print(f"        {sig.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
