"""
common.py -- shared foundation for the 7 Insider agents.

Used by Eddie / Maggie / Frank / Maya / Janet (scouts), Sophie (consensus),
and Ross (dispatcher). Provides:

  - get_claude()          Anthropic SDK client, reads ANTHROPIC_API_KEY
  - run_scout()           Run a scout prompt -> parse structured output -> persist
  - read_window()         Read the rolling 7-day window of scout signals
  - record_signal()       Write a scout signal to the state store
  - record_consensus()    Write a consensus event to the state store
  - send_email()          Generic SMTP via provider-neutral config
  - send_telegram()       Optional Telegram bot delivery
  - log()                 Append-only log to .state/logs/

State lives at <repo_root>/.state/state.db (SQLite).
Config lives at <repo_root>/.env (read at startup via python-dotenv).

The agents are intentionally small -- they delegate the heavy lifting to
Claude (web research, parsing) and just orchestrate the data flow.

NOTE: Scout agents (eddie, maggie, frank, maya) send prompts to Claude
asking it to research public sources, but the current implementation does
not attach web search tools to the Anthropic SDK calls. Responses reflect
Claude's training knowledge, not verified real-time data. Live data
grounding requires a future enhancement phase.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "Missing dependency: python-dotenv. "
        "Install with: pip install python-dotenv\n"
    )
    raise

try:
    from anthropic import Anthropic  # type: ignore
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "Missing dependency: anthropic. "
        "Install with: pip install anthropic\n"
    )
    raise


# -- Paths --------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".state"
LOGS = STATE / "logs"
DB_PATH = STATE / "state.db"
ENV_PATH = ROOT / ".env"

# Load env on import -- every agent boots through this module.
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


# -- Models -------------------------------------------------------------------
# NOTE: These model IDs are from the original source prompt and may need
# verification against Anthropic's current model list before real operation.

DEFAULT_MODEL = os.environ.get("INSIDER_MODEL", "claude-sonnet-4-5-20250929")
HAIKU_MODEL = os.environ.get("INSIDER_MODEL_FAST", "claude-haiku-4-5-20251001")
OPUS_MODEL = os.environ.get("INSIDER_MODEL_DEEP", "claude-opus-4-7-20251020")


# -- Direction taxonomy -------------------------------------------------------

BULLISH = "BULLISH"
BEARISH = "BEARISH"
NEUTRAL = "NEUTRAL"
DIRECTIONS = (BULLISH, BEARISH, NEUTRAL)


# -- Dataclasses --------------------------------------------------------------


@dataclass
class Signal:
    """A single scout's structured output."""

    scout: str
    ticker: str  # ticker, asset symbol, or "MACRO"
    direction: str  # BULLISH | BEARISH | NEUTRAL
    confidence: int  # 1-5
    reason: str  # one-line plain-English reason
    raw: str  # full prompt output for audit


@dataclass
class ConsensusEvent:
    """Sophie's output when >=3 scouts agree."""

    ticker: str
    direction: str
    scouts: list[str]
    reasons: list[str]
    timestamp: datetime


# -- State store --------------------------------------------------------------


def _ensure_dirs() -> None:
    """Create state and log directories if they do not exist."""
    STATE.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)


def _conn() -> sqlite3.Connection:
    """Open (and initialize if needed) the SQLite state store."""
    _ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scout TEXT NOT NULL,
            ticker TEXT NOT NULL,
            direction TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            reason TEXT NOT NULL,
            raw TEXT NOT NULL,
            ts TEXT NOT NULL
        )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS consensus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            direction TEXT NOT NULL,
            scouts TEXT NOT NULL,
            reasons TEXT NOT NULL,
            ts TEXT NOT NULL,
            dispatched INTEGER DEFAULT 0
        )""")
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(ts)"""
    )
    return conn


def record_signal(sig: Signal) -> None:
    """Append a scout signal to the state store."""
    with _conn() as c:
        c.execute(
            "INSERT INTO signals "
            "(scout, ticker, direction, confidence, reason, raw, ts) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                sig.scout,
                sig.ticker,
                sig.direction,
                sig.confidence,
                sig.reason,
                sig.raw,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def read_window(days: int = 7) -> list[Signal]:
    """Return all scout signals in the last ``days`` days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with _conn() as c:
        rows = c.execute(
            "SELECT scout, ticker, direction, confidence, reason, raw "
            "FROM signals WHERE ts >= ? ORDER BY ts DESC",
            (cutoff,),
        ).fetchall()
    return [Signal(*r) for r in rows]


def record_consensus(ev: ConsensusEvent) -> int:
    """Write a consensus event. Returns the row id for Ross to track dispatch."""
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO consensus (ticker, direction, scouts, reasons, ts) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                ev.ticker,
                ev.direction,
                json.dumps(ev.scouts),
                json.dumps(ev.reasons),
                ev.timestamp.isoformat(),
            ),
        )
        return int(cur.lastrowid or 0)


def pending_consensus() -> list[tuple[int, ConsensusEvent]]:
    """Ross reads this -- events not yet dispatched."""
    with _conn() as c:
        rows = c.execute(
            "SELECT id, ticker, direction, scouts, reasons, ts "
            "FROM consensus WHERE dispatched = 0"
        ).fetchall()
    out: list[tuple[int, ConsensusEvent]] = []
    for r in rows:
        out.append(
            (
                int(r[0]),
                ConsensusEvent(
                    ticker=r[1],
                    direction=r[2],
                    scouts=json.loads(r[3]),
                    reasons=json.loads(r[4]),
                    timestamp=datetime.fromisoformat(r[5]),
                ),
            )
        )
    return out


def mark_dispatched(row_id: int) -> None:
    """Mark a consensus event as dispatched so Ross does not re-send."""
    with _conn() as c:
        c.execute(
            "UPDATE consensus SET dispatched = 1 WHERE id = ?", (row_id,)
        )


# -- Claude client ------------------------------------------------------------


def get_claude() -> Anthropic:
    """Return an Anthropic client. Raises if ANTHROPIC_API_KEY is not set."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Add it to .env in the repo root."
        )
    return Anthropic(api_key=api_key)


def run_scout(
    scout_name: str,
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 2048,
) -> Signal:
    """Run a scout's prompt against Claude. Parse the structured trailer. Persist.

    Scout prompts MUST end with a strict JSON block of the form:

        {"ticker": "<TICKER>", "direction": "BULLISH|BEARISH|NEUTRAL",
         "confidence": <1-5>, "reason": "<one line>"}

    This module parses the LAST JSON object in the response.

    NOTE: This call does not attach web search tools. Scout outputs
    depend on Claude's training knowledge and are not independently
    verified against live sources.
    """
    client = get_claude()
    msg = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = "\n".join(
        block.text for block in msg.content if hasattr(block, "text")
    ).strip()

    payload = _extract_last_json(raw)
    if payload is None:
        # No usable signal this run -- record a NEUTRAL placeholder.
        sig = Signal(
            scout=scout_name,
            ticker="MACRO",
            direction=NEUTRAL,
            confidence=1,
            reason="no qualifying signal this run",
            raw=raw,
        )
    else:
        sig = Signal(
            scout=scout_name,
            ticker=str(payload.get("ticker", "MACRO")).upper(),
            direction=_normalise_direction(payload.get("direction", NEUTRAL)),
            confidence=int(payload.get("confidence", 1) or 1),
            reason=str(payload.get("reason", "")).strip()[:240],
            raw=raw,
        )
    record_signal(sig)
    log(
        scout_name,
        f"signal: {sig.ticker} {sig.direction} conf={sig.confidence} "
        f":: {sig.reason}",
    )
    return sig


def _extract_last_json(text: str) -> dict[str, Any] | None:
    """Find the last ``{...}`` JSON object in text.

    Tolerant of prose around it.
    """
    depth = 0
    start = -1
    candidates: list[str] = []
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                candidates.append(text[start : i + 1])
                start = -1
    for c in reversed(candidates):
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


def _normalise_direction(d: Any) -> str:
    """Normalize a direction string to one of the valid taxonomy values."""
    s = str(d).upper().strip()
    return s if s in DIRECTIONS else NEUTRAL


# -- Delivery -----------------------------------------------------------------


def is_dry_run() -> bool:
    """Check whether Ross should operate in dry-run mode.

    Dry-run is the default. Set ROSS_DRY_RUN=false in .env to enable
    real email/Telegram delivery.
    """
    val = os.environ.get("ROSS_DRY_RUN", "true").strip().lower()
    return val not in ("false", "0", "no")


def send_email(subject: str, body: str) -> None:
    """Send an email via generic SMTP.

    Uses provider-neutral SMTP configuration from .env:
      SMTP_HOST, SMTP_PORT, SMTP_USE_SSL, SMTP_USERNAME, SMTP_PASSWORD,
      ALERT_EMAIL_FROM, ALERT_EMAIL_TO

    Respects dry-run mode -- logs instead of sending if dry-run is active.

    Raises:
        RuntimeError: If email send fails or configuration is invalid
    """
    if is_dry_run():
        log("ross", f"[DRY-RUN] would send email: {subject}")
        return

    # Import here to avoid circular dependency
    from alerts.smtp_email import send_email as smtp_send

    result = smtp_send(subject, body)
    if not result["success"]:
        raise RuntimeError(f"Email send failed: {result['error']}")


def send_telegram(text: str) -> bool:
    """Optional Telegram delivery. Returns True if delivered, False if skipped.

    Respects dry-run mode.
    """
    if is_dry_run():
        log("ross", "[DRY-RUN] would send telegram message")
        return False

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return False
    import urllib.request
    import urllib.parse

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": chat, "text": text, "parse_mode": "Markdown"}
    ).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


# -- Logging ------------------------------------------------------------------


def log(scope: str, message: str) -> None:
    """Append-only log per scope (= agent name)."""
    _ensure_dirs()
    line = f"{datetime.now(timezone.utc).isoformat()} [{scope}] {message}\n"
    (LOGS / f"{scope.lower()}.log").open("a", encoding="utf-8").write(line)


# -- Pretty-print helpers (for terminal smoke runs) ---------------------------


def render_consensus(ev: ConsensusEvent) -> str:
    """Plain-text body for email + Telegram."""
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
        textwrap.fill(
            "This is informational, not a trade instruction. Ross did not "
            "place a trade. The decision is yours.",
            width=72,
        )
    )
    return "\n".join(body)
