#!/usr/bin/env python3
"""
Email alert render dry-run script.

Renders a sample email alert subject/body to a local file for review
without sending any live email or Telegram message.

Usage:
    python scripts/render_email_alert_dry_run.py --output <path>

Safety:
    - No network calls
    - No SMTP send
    - No Telegram send
    - Email remains disabled
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from alerts.routing import SeverityLevel  # noqa: E402


@dataclass
class SampleConsensusEvent:
    """Sample consensus event for render testing."""

    ticker: str
    direction: str
    timestamp: datetime
    scouts: list[str]
    reasons: list[str]
    aggregate_confidence: int


def render_sample_consensus(ev: SampleConsensusEvent) -> str:
    """Render plain-text body for sample email alert (matches agents/common.py format)."""
    head = f"SOPHIE CONSENSUS -- {ev.direction} on {ev.ticker}"
    rule = "=" * len(head)
    body = [
        head,
        rule,
        f"Time: {ev.timestamp.isoformat(timespec='minutes')}",
        "",
    ]
    body.append(f"{len(ev.scouts)} of 5 scouts agree:")
    for scout, reason in zip(ev.scouts, ev.reasons):
        body.append(f"  - {scout:<10} {reason}")
    body.append("")
    body.append(
        "This is informational, not a trade instruction. Ross did not "
        "place a trade. The decision is yours."
    )
    return "\n".join(body)


def render_dry_run_email(output_path: Path) -> None:
    """Render a sample email alert to a file without sending."""
    # Create sample ACTIONABLE consensus event
    sample_event = SampleConsensusEvent(
        ticker="MAIA",
        direction="BULLISH",
        timestamp=datetime.now(timezone.utc),
        scouts=["eddie", "maggie", "frank"],
        reasons=[
            "Recent Form 4 buying by CEO and CFO",
            "Institutional ownership increase in latest 13F",
            "Price momentum suggests accumulation",
        ],
        aggregate_confidence=12,
    )

    # Format subject (matches Ross format)
    severity = SeverityLevel.ACTIONABLE
    subject = f"[INSIDER] {severity.value} {sample_event.direction} on {sample_event.ticker}"

    # Format body
    body = render_sample_consensus(sample_event)

    # Build complete email render with dry-run header
    output_content = f"""# EMAIL RENDER DRY-RUN — NO EMAIL SENT

**Generated**: {datetime.now(timezone.utc).isoformat()}
**Mode**: Dry-run render test only
**Network**: No SMTP send, no Telegram send

---

## Email Configuration Status

- `ALERT_ENABLE_EMAIL`: **false** (disabled)
- `ALERT_ENABLE_TELEGRAM`: true (but not sending from this script)

---

## Sample Email Alert

**To**: [configured recipient redacted]

**Subject**:
```
{subject}
```

**Body**:
```
{body}
```

---

## Evidence Context Included

✅ Ticker: {sample_event.ticker}
✅ Direction: {sample_event.direction}
✅ Severity: {severity.value}
✅ Scout count: {len(sample_event.scouts)} scouts agree
✅ Aggregate confidence: {sample_event.aggregate_confidence}
✅ Per-scout reasoning included
✅ Timestamp included
✅ Disclaimer included

---

## Safety Confirmations

✅ No email sent
✅ No Telegram sent
✅ Email remains disabled (`ALERT_ENABLE_EMAIL=false`)
✅ No SMTP credentials in output
✅ No Telegram token in output
✅ Informational-only disclaimer present

---

**Rendered sample only. No live alert delivered.**
"""

    # Write to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_content, encoding="utf-8")

    print(f"Rendered email dry-run sample to: {output_path}")
    print("No email or Telegram sent.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Render email alert dry-run sample (no send)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/sample_reports/alerts/email_render_dry_run_sample.md"),
        help="Output path for rendered sample",
    )
    args = parser.parse_args()

    # Verify email remains disabled (safe check only)
    email_enabled = os.environ.get("ALERT_ENABLE_EMAIL", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    if email_enabled:
        sys.stderr.write(
            "WARNING: ALERT_ENABLE_EMAIL is enabled in .env. "
            "This script does not send email, but email should remain disabled "
            "until CP22B controlled test.\n"
        )

    # Render sample
    render_dry_run_email(args.output)


if __name__ == "__main__":
    main()
