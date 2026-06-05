#!/usr/bin/env python3
"""
Ross -- the dispatcher with alert routing policy.

Reads pending consensus events from the state store, applies alert routing
policy (severity classification, deduplication, channel routing), and
dispatches via email/Telegram based on policy and channel enablement.

NEVER places trades. Output is informational. The human decides.

Dry-run mode is ON by default (ROSS_DRY_RUN=true in .env.example).
Channel delivery is OFF by default (ALERT_ENABLE_TELEGRAM=false, ALERT_ENABLE_EMAIL=false).
Ross does NOT call Claude. He is pure local logic + delivery + routing.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add both agents/ and project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alerts import (
    AlertClass,
    check_daily_guard,
    check_duplicate,
    detect_trigger_source,
    make_dedup_key,
    make_routing_decision,
    record_daily_run,
    record_routing_decision,
    should_bypass_guard,
)
from common import (
    is_dry_run,
    log,
    mark_dispatched,
    pending_consensus,
    read_window,
    render_consensus,
    send_email,
    send_telegram,
)


def main() -> int:
    """Dispatch pending consensus events via alert routing policy."""
    run_started_at = datetime.now(timezone.utc)
    local_date = datetime.now().date().isoformat()
    trigger_source = detect_trigger_source()

    # Log operational mode
    dry_run_mode = is_dry_run()
    if dry_run_mode:
        print("[ross] DRY-RUN mode is active (set ROSS_DRY_RUN=false to send)")

    telegram_enabled = (
        os.environ.get("ALERT_ENABLE_TELEGRAM", "false").strip().lower()
        in ("true", "1", "yes")
    )
    email_enabled = (
        os.environ.get("ALERT_ENABLE_EMAIL", "false").strip().lower()
        in ("true", "1", "yes")
    )
    max_per_run = int(os.environ.get("ALERT_MAX_PER_RUN", "3"))

    print(f"[ross] Channels: telegram={telegram_enabled}, email={email_enabled}")
    print(f"[ross] Rate limit: {max_per_run} alerts/run")

    # Check once-daily guard for production alert runs
    # Guard only applies to production mode (not dry-run)
    # Dry-run/preview modes don't consume the daily production run
    is_production_mode = not dry_run_mode and telegram_enabled
    force_run = should_bypass_guard()

    if is_production_mode and not force_run:
        can_run, reason = check_daily_guard()
        if not can_run:
            log("ross", f"Daily guard blocked run: {reason}")
            print(f"[ross] SKIPPED: {reason}")
            print("[ross] Use ROSS_FORCE_RUN=true to override (supervised only)")
            # Record skipped run in guard
            record_daily_run(
                local_date=local_date,
                run_started_at=run_started_at,
                run_finished_at=datetime.now(timezone.utc),
                status="skipped_already_ran",
                alerts_sent_count=0,
                trigger_source=trigger_source,
                dry_run=False,
                exit_code=0,
            )
            return 0
    elif force_run:
        print("[ross] FORCED RUN - bypassing daily guard (ROSS_FORCE_RUN=true)")
        log("ross", "FORCED RUN - bypassing daily guard")

    # Read pending consensus events
    pending = pending_consensus()
    if not pending:
        log("ross", "no pending consensus events")
        print("[ross] nothing to dispatch")
        return 0

    print(f"[ross] {len(pending)} pending consensus events")

    # Read signal window for severity calculation
    scout_signals = read_window(days=14)
    print(f"[ross] {len(scout_signals)} signals in 14-day window")

    # Process each pending consensus with routing policy
    delivered = 0
    for row_id, ev in pending:
        # Rate limit check
        if delivered >= max_per_run:
            log(
                "ross",
                f"rate limit reached ({max_per_run}/run), skipping remaining events",
            )
            print(
                f"[ross] rate limit reached ({max_per_run}/run), skipping remaining"
            )
            break

        # Create dedup key and check for duplicates
        dedup_hours = int(os.environ.get("ALERT_DEDUP_HOURS", "24"))
        dedup_key = make_dedup_key(ev.ticker, ev.direction, hours=dedup_hours)
        is_duplicate = check_duplicate(dedup_key, hours=dedup_hours)

        # Make routing decision
        decision = make_routing_decision(
            consensus_id=row_id,
            ev=ev,
            scout_signals=scout_signals,
            is_duplicate=is_duplicate,
            dedup_key=dedup_key,
        )

        # Log routing decision
        log(
            "ross",
            f"[{row_id}] {ev.ticker} {ev.direction}: {decision.severity.value} "
            f"→ {decision.alert_class.value} (dedup={is_duplicate})",
        )
        print(f"[ross] [{row_id}] {ev.ticker}: {decision.reason}")

        # Handle based on alert class
        email_status = "skipped"
        telegram_status = "skipped"
        error_message = None

        if decision.alert_class == AlertClass.SUPPRESS_DUPLICATE:
            # Log duplicate, record audit, mark dispatched
            log("ross", f"[{row_id}] duplicate suppressed: {dedup_key}")
            print(f"[ross] [{row_id}] duplicate suppressed")
            record_routing_decision(
                decision, email_status="duplicate", telegram_status="duplicate"
            )
            mark_dispatched(row_id)
            delivered += 1
            continue

        if decision.alert_class == AlertClass.LOG_ONLY:
            # Log only, no delivery
            log("ross", f"[{row_id}] log only: {decision.reason}")
            print(f"[ross] [{row_id}] log only (no delivery)")
            record_routing_decision(
                decision, email_status="log_only", telegram_status="log_only"
            )
            mark_dispatched(row_id)
            delivered += 1
            continue

        # Prepare message content
        body = render_consensus(ev)
        subject = f"[INSIDER] {decision.severity.value} {ev.direction} on {ev.ticker}"

        # Attempt delivery based on routing decision
        delivery_success = False

        # Email delivery
        if decision.should_send_email:
            try:
                send_email(subject, body)
                email_status = "sent"
                log("ross", f"[{row_id}] email sent")
                delivery_success = True
            except Exception as exc:  # noqa: BLE001
                email_status = "failed"
                error_message = str(exc)
                log("ross", f"[{row_id}] email FAILED: {exc}")
                print(f"[ross] [{row_id}] email FAILED: {exc}")
                # Do not mark dispatched on email failure for non-LOG_ONLY alerts
                record_routing_decision(
                    decision,
                    email_status=email_status,
                    telegram_status=telegram_status,
                    error_message=error_message,
                )
                continue  # Retry next run

        # Telegram delivery
        if decision.should_send_telegram:
            try:
                if send_telegram(f"*{subject}*\n\n```\n{body}\n```"):
                    telegram_status = "sent"
                    log("ross", f"[{row_id}] telegram sent")
                    delivery_success = True
                else:
                    telegram_status = "failed"
                    log("ross", f"[{row_id}] telegram send returned False")
            except Exception as exc:  # noqa: BLE001
                telegram_status = "failed"
                log("ross", f"[{row_id}] telegram error: {exc}")

        # In dry-run mode, consider it delivered for audit purposes
        if is_dry_run():
            email_status = "dry_run"
            telegram_status = "dry_run"
            delivery_success = True

        # Record audit and mark dispatched
        record_routing_decision(
            decision,
            email_status=email_status,
            telegram_status=telegram_status,
            error_message=error_message,
        )

        if delivery_success or decision.alert_class == AlertClass.LOG_ONLY:
            mark_dispatched(row_id)
            delivered += 1
            print(f"[ross] [{row_id}] dispatched {ev.ticker}")

    log("ross", f"delivered {delivered}/{len(pending)} pending events")
    print(f"[ross] delivered {delivered}/{len(pending)} events")

    # Record completion in daily guard (production mode only)
    if is_production_mode:
        record_daily_run(
            local_date=local_date,
            run_started_at=run_started_at,
            run_finished_at=datetime.now(timezone.utc),
            status="forced" if force_run else "completed",
            alerts_sent_count=delivered,
            trigger_source=trigger_source,
            dry_run=False,
            exit_code=0,
            override_reason="ROSS_FORCE_RUN=true" if force_run else None,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
