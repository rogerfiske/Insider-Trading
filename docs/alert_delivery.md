# Alert Delivery Channels

This document describes the validated alert delivery channels and their configuration.

## Overview

The Insider-Trading system supports two alert delivery channels:

1. **Telegram** - Instant messaging via Telegram Bot API
2. **Email** - SMTP email delivery (currently configured for 4SecureMail)

Both channels are controlled independently and route through the alert routing policy layer (CP15).

## Telegram Delivery

### Status

✅ **Fully validated** (CP12B, CP16, CP17)

### Configuration

Required `.env` variables:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
ALERT_ENABLE_TELEGRAM=true  # Default: false
```

### Features

- **Message Format:** Markdown formatting supported
- **Delivery Speed:** Instant (< 1 second typically)
- **Rate Limits:** Telegram Bot API standard limits (30 messages/second per bot)
- **Retry Logic:** None currently implemented
- **Error Handling:** Returns boolean success/failure

### Implementation

- **Module:** `agents/common.py` - `send_telegram()` function
- **Dependencies:** Python `urllib` (stdlib), Telegram Bot API
- **Validation:** CP12B (initial test), CP16 (routing layer), CP17 (dual-channel)

### Current Limitations

- Message ID not captured from API response (enhancement opportunity)
- No exponential backoff retry on failure
- No delivery confirmation beyond HTTP 200 response

## Email Delivery

### Status

✅ **Fully validated** (CP13B, CP17)

### Configuration

Required `.env` variables:

```env
SMTP_HOST=mail.4securemail.com  # Or your SMTP provider
SMTP_PORT=465  # 465 for SSL, 587 for STARTTLS
SMTP_USE_SSL=true  # true for port 465, false for port 587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
ALERT_EMAIL_FROM=your_from_address@domain.com
ALERT_EMAIL_TO=your_to_address@domain.com
ALERT_ENABLE_EMAIL=true  # Default: false
```

### Features

- **Message Format:** Plain text
- **Delivery Speed:** Typically 1-30 seconds
- **Provider:** Currently configured for 4SecureMail (provider-neutral implementation supports any SMTP provider)
- **Retry Logic:** None currently implemented
- **Error Handling:** Raises `RuntimeError` on failure

### Implementation

- **Module:** `alerts/smtp_email.py` - `send_email()` function
- **Wrapper:** `agents/common.py` - `send_email()` wrapper with dry-run support
- **Dependencies:** Python `smtplib` and `ssl` (stdlib)
- **Validation:** CP13B (initial 4SecureMail test), CP17 (dual-channel)

### Current Limitations

- SMTP message ID not captured from server response
- No exponential backoff retry on failure
- No delivery status notification (DSN) support
- Plain text only (no HTML formatting)

## Routing Integration

Both channels are integrated with the alert routing policy (CP15):

- **Severity Classification:** Channels selected based on severity (INFO, WATCH, ACTIONABLE, URGENT)
- **Alert Classes:** Determines channel routing (TELEGRAM_ONLY, EMAIL_ONLY, TELEGRAM_AND_EMAIL, etc.)
- **Independent Control:** Channels can be enabled/disabled independently via `.env`
- **Deduplication:** Time-bucketed keys prevent duplicate alerts across all channels
- **Rate Limiting:** `ALERT_MAX_PER_RUN` limits total alerts per Ross execution
- **Audit Trail:** All delivery attempts recorded in `alert_history` SQLite table

See [alert_routing_policy.md](alert_routing_policy.md) for complete routing policy documentation.

## Testing Tools

### Telegram Test

```powershell
# Check Telegram configuration
python scripts\telegram_setup_check.py

# Dry-run preview (no message sent)
python scripts\telegram_routing_test.py

# Send one controlled test message
python scripts\telegram_routing_test.py --send-once
```

### Email Test

```powershell
# Check SMTP configuration
python scripts\smtp_test.py

# Send one controlled test email
python scripts\smtp_test.py --send-test
```

### Dual-Channel Test

```powershell
# Dry-run preview (no messages sent)
python scripts\dual_channel_routing_test.py

# Send one controlled Telegram + email test
python scripts\dual_channel_routing_test.py --send-once
```

## Production Enablement

See [production_alert_enablement_plan.md](production_alert_enablement_plan.md) for the staged rollout plan.

**Current Status (CP18):** All channels validated in controlled tests. Production live alerts not yet enabled. Awaiting PM approval for CP19 (manual Telegram-only production test).

## Emergency Disable

To immediately disable all alert delivery:

**Option 1: Disable channels**

```env
ALERT_ENABLE_TELEGRAM=false
ALERT_ENABLE_EMAIL=false
```

**Option 2: Enable master dry-run**

```env
ROSS_DRY_RUN=true
```

**Option 3: Disable scheduled Ross task**

```powershell
Disable-ScheduledTask -TaskPath "\InsiderRoutines\" -TaskName "Insider-ross"
```

See [production_alert_enablement_plan.md](production_alert_enablement_plan.md) for complete emergency procedures.

## Future Enhancements

### High Priority

1. **Capture message IDs:** Both Telegram and email should capture and record message IDs in audit trail
2. **Retry logic:** Implement exponential backoff retry for transient delivery failures
3. **Delivery confirmation:** Capture Telegram message ID and email SMTP message ID

### Medium Priority

4. **HTML email support:** Add rich formatting for email alerts
5. **Email DSN support:** Request delivery status notifications from SMTP provider
6. **Alternative SMTP providers:** Test Gmail, SendGrid, AWS SES as backup providers
7. **Telegram inline buttons:** Add interactive buttons for alert acknowledgment/actions

### Low Priority

8. **SMS delivery:** Add SMS channel for critical URGENT alerts
9. **Slack integration:** Add Slack webhook delivery option
10. **Discord integration:** Add Discord webhook delivery option
