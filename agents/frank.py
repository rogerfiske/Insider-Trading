#!/usr/bin/env python3
"""
Frank -- the Fed-speech reader.

Reads Federal Reserve speeches and FOMC commentary from the last 7 days.
Aggregates hawkish vs dovish tilt. Emits a single MACRO signal.

Schedule: weekly, Monday 08:00 local time.

Source grounding: uses the FedSpeechesConnector to fetch real speech data
from federalreserve.gov before calling Claude.  Claude analyzes the
fetched speech excerpts rather than relying on training knowledge.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import log, run_scout

from evidence.schema import EvidenceBundle
from evidence.store import save_evidence
from sources.fed_speeches import FedSpeechesConnector

SYSTEM = """You are Frank, a macro intelligence agent. You read every
Federal Reserve speech and FOMC statement published in the last 7 days,
weigh the language, and pronounce the net tilt.

Your job:
  1. Review the LIVE Federal Reserve speech data provided below.
  2. For each speech, extract speaker, one-line stance, and classify
     hawkish / dovish / neutral. Pull one supporting quote (<=25 words).
  3. Aggregate into a net tilt (e.g. "3 hawkish, 1 dovish, 2 neutral -> net
     hawkish").

Output a short prose summary, followed by a STRICT JSON signal:

  {"ticker": "MACRO", "direction": "BULLISH|BEARISH|NEUTRAL",
   "confidence": <1-5>, "reason": "<one-line>"}

Direction rules (for risk assets -- equity / crypto):
  - Net DOVISH -> BULLISH (cuts coming, liquidity -> risk assets up)
  - Net HAWKISH -> BEARISH (cuts paused / hikes -> risk assets down)
  - Mixed -> NEUTRAL
Confidence: 1 = single speech, mixed signals; 5 = unanimous Powell + 2+
governors aligned, clear policy language.

If no qualifying speeches in the provided data, output:

  {"ticker": "MACRO", "direction": "NEUTRAL", "confidence": 1,
   "reason": "no Fed speeches this week"}

Never speculate beyond the speeches provided below.
"""

USER_TEMPLATE = """Analyze the following Federal Reserve speech data from the
last 7 days. Classify each one. Aggregate. Output the prose summary followed
by the JSON signal.

{source_data}"""


def main() -> int:
    """Run Frank with source-grounded Fed speech data."""
    # 1. Fetch deterministic source data
    connector = FedSpeechesConnector(lookback_days=7)
    result = connector.fetch()

    # 2. Store evidence
    bundle = EvidenceBundle(agent="frank", fetch_result=result)
    evidence_path = save_evidence(bundle)
    log("frank", f"evidence stored: {evidence_path}")

    # 3. Format source data for Claude prompt
    source_data = connector.format_for_prompt(result)

    # 4. Run scout with grounded prompt
    user_prompt = USER_TEMPLATE.format(source_data=source_data)
    sig = run_scout("frank", SYSTEM, user_prompt)

    print(f"[frank] {sig.ticker} {sig.direction} conf={sig.confidence}")
    print(f"        {sig.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
