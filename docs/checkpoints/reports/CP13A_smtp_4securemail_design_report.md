# CP13A Report -- Generic SMTP / 4SecureMail Alert Design

**Checkpoint**: CP13A (Design/Planning Only)
**Status**: Completed successfully
**Date**: 2026-05-29
**Executor**: Claude Code (Opus 4.6)
**Commit**: (none -- planning-only checkpoint)
**Push**: (none)

---

## 1. Summary

CP13A analyzed the current Gmail-specific email implementation and designed a
provider-neutral SMTP alert delivery system suitable for Roger's 4SecureMail
account (`fiske1945@4securemail.com`). The design replaces hardcoded Gmail
SMTP with generic SMTP configuration, proposes new `.env` placeholders, and
outlines a safe CP13B implementation plan.

This is a planning-only checkpoint. No code was implemented, no email was sent,
and no configuration changes were made.

## 2. Files inspected

| File | Purpose |
|------|---------|
| `agents/ross.py` | Dispatcher logic |
| `agents/common.py` | `send_email()` and `send_telegram()` functions (lines 358-407) |
| `.env.example` | Current email placeholders |
| `docs/install_notes_windows.md` | Configuration documentation |

## 3. Current Ross email/alert implementation analysis

### Current Architecture

**Ross Dispatcher (`agents/ross.py`)**:
- Reads pending consensus events from state store
- Dispatches via email (always) and Telegram (optional)
- Marks events as dispatched after successful delivery
- Respects `ROSS_DRY_RUN` mode

**Email Delivery (`agents/common.py:358-385`)**:
```python
def send_email(subject: str, body: str) -> None:
    """Send an email via Gmail SMTP."""
    if is_dry_run():
        log("ross", f"[DRY-RUN] would send email: {subject}")
        return

    user = os.environ.get("GMAIL_USER")
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    to = os.environ.get("GMAIL_TO", user)
    if not user or not pw:
        raise RuntimeError("GMAIL_USER / GMAIL_APP_PASSWORD not set...")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.send_message(msg)
```

**Telegram Delivery (`agents/common.py:387-407`)**:
- Already provider-neutral
- Uses `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Returns `True` if sent, `False` if skipped
- Respects dry-run mode

### Current `.env` Keys

```env
GMAIL_USER=
GMAIL_APP_PASSWORD=
GMAIL_TO=

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## 4. Current Gmail-specific assumptions

**Hardcoded Gmail SMTP**:
1. **Host**: `smtp.gmail.com` (line 382 in `common.py`)
2. **Port**: `465` (line 382)
3. **SSL/TLS**: `SMTP_SSL` assumed (line 382)
4. **Environment Variables**: `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `GMAIL_TO`

**Limitations**:
- Cannot use with 4SecureMail (`mail.4securemail.com`) without code change
- Cannot use with other SMTP providers (Outlook, FastMail, etc.)
- No fallback if Gmail-specific auth fails
- Variable names mislead users into thinking Gmail is required

**Current Comment** (line 359):
```python
"""Send an email via Gmail SMTP."""
```

**Implication**: The function is explicitly Gmail-only by design.

## 5. Proposed provider-neutral SMTP `.env` design

### New Environment Variables

Replace Gmail-specific variables with provider-neutral SMTP configuration:

```env
# Generic SMTP alert delivery (replaces Gmail-specific config)
SMTP_HOST=
SMTP_PORT=
SMTP_USE_SSL=
SMTP_USERNAME=
SMTP_PASSWORD=
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=
```

### Variable Descriptions

| Variable | Purpose | Example |
|----------|---------|---------|
| `SMTP_HOST` | SMTP server hostname | `mail.4securemail.com` |
| `SMTP_PORT` | SMTP server port | `465` (SSL) or `587` (STARTTLS) |
| `SMTP_USE_SSL` | Use SSL (port 465) vs STARTTLS (port 587) | `true` or `false` |
| `SMTP_USERNAME` | SMTP authentication username | `fiske1945@4securemail.com` |
| `SMTP_PASSWORD` | SMTP authentication password | `<password or app password>` |
| `ALERT_EMAIL_FROM` | Email "From" address | `fiske1945@4securemail.com` |
| `ALERT_EMAIL_TO` | Email "To" address | `fiske1945@4securemail.com` |

### Migration Strategy

**Option A: Replace Gmail variables (recommended)**
- Remove `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `GMAIL_TO` from `.env.example`
- Add new `SMTP_*` and `ALERT_EMAIL_*` variables
- Update `send_email()` to use new variables
- Document migration in upgrade notes

**Option B: Support both (backward compatible)**
- Keep `GMAIL_*` variables for backward compatibility
- Add new `SMTP_*` variables
- `send_email()` checks for `SMTP_HOST` first, falls back to Gmail variables
- Deprecate Gmail variables in documentation

**Recommendation**: Option A (replace) -- simplifies code and clarifies that any
SMTP provider is supported. Gmail users can still use Gmail by configuring
`SMTP_HOST=smtp.gmail.com`.

## 6. 4SecureMail recommended local values

Roger should configure these values in local `.env` (not `.env.example`) for
4SecureMail:

```env
SMTP_HOST=mail.4securemail.com
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USERNAME=fiske1945@4securemail.com
SMTP_PASSWORD=<Roger's 4SecureMail password or app password>
ALERT_EMAIL_FROM=fiske1945@4securemail.com
ALERT_EMAIL_TO=fiske1945@4securemail.com
```

**Notes**:
- `SMTP_PASSWORD` is managed by Roger in his password manager and placed in local `.env` only
- Never commit `SMTP_PASSWORD` to `.env.example` or any tracked file
- If 4SecureMail supports app passwords, use an app password instead of the main account password

**Verification Source**:
- SMTP host: `mail.4securemail.com` (assumed based on domain, Roger should verify)
- SMTP port: `465` (SSL) is standard for secure SMTP
- If Roger has documentation from 4SecureMail, verify host/port before CP13B

## 7. Proposed alert module/refactor design

### Option A: Refactor `common.py` (minimal change)

**Advantages**:
- Minimal code change
- No new module structure
- Existing imports work

**Disadvantages**:
- `common.py` continues to grow
- No clear separation of concerns

**Implementation**:
Replace `send_email()` function in `agents/common.py` (lines 358-385):

```python
def send_email(subject: str, body: str) -> None:
    """Send an email via generic SMTP.

    Requires SMTP_HOST, SMTP_PORT, SMTP_USE_SSL, SMTP_USERNAME, SMTP_PASSWORD,
    ALERT_EMAIL_FROM, and ALERT_EMAIL_TO in .env.

    Respects dry-run mode -- logs instead of sending if dry-run is active.
    """
    if is_dry_run():
        log("ross", f"[DRY-RUN] would send email: {subject}")
        return

    host = os.environ.get("SMTP_HOST")
    port_str = os.environ.get("SMTP_PORT", "465")
    use_ssl = os.environ.get("SMTP_USE_SSL", "true").lower() == "true"
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    from_addr = os.environ.get("ALERT_EMAIL_FROM")
    to_addr = os.environ.get("ALERT_EMAIL_TO")

    if not all([host, username, password, from_addr, to_addr]):
        raise RuntimeError(
            "SMTP configuration incomplete. Set SMTP_HOST, SMTP_USERNAME, "
            "SMTP_PASSWORD, ALERT_EMAIL_FROM, ALERT_EMAIL_TO in .env"
        )

    try:
        port = int(port_str)
    except ValueError:
        raise RuntimeError(f"SMTP_PORT must be an integer, got: {port_str}")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    if use_ssl:
        with smtplib.SMTP_SSL(host, port) as s:
            s.login(username, password)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(username, password)
            s.send_message(msg)
```

### Option B: Create `alerts/` module (structured)

**Advantages**:
- Clear separation of concerns
- Easier to test independently
- Scalable for future alert channels (SMS, Slack, etc.)

**Disadvantages**:
- More files to create and maintain
- More complex import structure

**Proposed Module Structure**:

```
alerts/
  __init__.py         # Public API: send_email(), send_telegram()
  smtp_email.py       # SMTP email implementation
  telegram.py         # Telegram implementation (move from common.py)
  common.py           # Shared utilities (dry-run check, logging)

tests/
  test_alerts_smtp_email.py   # SMTP email tests (mocked)
  test_alerts_telegram.py     # Telegram tests (mocked)
```

**Recommendation**: Option A (refactor `common.py`) for CP13B. Option B can be
deferred to a later cleanup checkpoint if the alert surface area grows.

## 8. Proposed tests

### Test Coverage Requirements

| Test | Purpose | Implementation |
|------|---------|----------------|
| `test_send_email_dry_run` | Verify dry-run mode prevents SMTP connection | Mock `is_dry_run()` to return `True`, assert no SMTP call |
| `test_send_email_missing_config` | Verify error if SMTP_* vars missing | Set partial env vars, assert `RuntimeError` raised |
| `test_send_email_success` | Verify SMTP connection and message send | Mock `smtplib.SMTP_SSL`, assert login and send called |
| `test_send_email_starttls` | Verify STARTTLS mode (port 587) works | Mock `smtplib.SMTP`, assert starttls() called |
| `test_send_email_password_not_logged` | Verify password redaction in logs/errors | Trigger error, assert password not in traceback |

### Test Implementation Strategy

**Mock SMTP Connections**:
```python
from unittest.mock import patch, MagicMock

def test_send_email_success():
    with patch("smtplib.SMTP_SSL") as mock_smtp:
        mock_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_instance

        send_email("Test Subject", "Test Body")

        mock_smtp.assert_called_once_with("mail.4securemail.com", 465)
        mock_instance.login.assert_called_once()
        mock_instance.send_message.assert_called_once()
```

**No Live SMTP Calls**:
- All tests must mock `smtplib.SMTP` and `smtplib.SMTP_SSL`
- No real email should be sent during `pytest` runs
- Single controlled live test reserved for CP13B or CP13C after PM approval

## 9. Proposed CP13B implementation steps

### Phase 1: Preparation (no code change)

1. **Roger configures local `.env`**:
   - Obtain 4SecureMail SMTP credentials (host, port, username, password)
   - Add new `SMTP_*` and `ALERT_EMAIL_*` variables to local `.env`
   - Keep `ROSS_DRY_RUN=true`

2. **Verify 4SecureMail SMTP settings**:
   - Confirm `mail.4securemail.com` is the correct host
   - Confirm port `465` (SSL) or `587` (STARTTLS)
   - Confirm whether app passwords are supported

### Phase 2: Implementation (CP13B)

1. **Update `.env.example`**:
   - Replace `GMAIL_*` section with `SMTP_*` and `ALERT_EMAIL_*` placeholders
   - Add comments explaining generic SMTP config
   - Document 4SecureMail example values (without password)

2. **Refactor `send_email()` in `agents/common.py`**:
   - Replace Gmail-specific implementation with provider-neutral SMTP
   - Support both SSL (port 465) and STARTTLS (port 587) modes
   - Use new environment variables
   - Maintain dry-run mode behavior

3. **Add unit tests**:
   - Create `tests/test_email_smtp.py` (or add to existing test file)
   - Mock all SMTP connections
   - Test dry-run, missing config, SSL, STARTTLS, error handling

4. **Update documentation**:
   - `docs/install_notes_windows.md`: Add CP13B section
   - `README.md`: Update email configuration section if needed

5. **Run validation**:
   - `py_compile` all files
   - `pytest` (all tests pass, no live email sent)
   - Smoke test

6. **Commit and push**:
   - Stage: `.env.example`, `agents/common.py`, `tests/*.py`, docs
   - Commit: "Implement generic SMTP email delivery"
   - Push to origin/main

### Phase 3: Controlled Live Test (CP13B or CP13C)

After PM approval:

1. **Single controlled test email**:
   - Use a dedicated test script (similar to CP12B Telegram test)
   - Send one non-trading test message
   - Message content: "Insider-Trading CP13B SMTP test: 4SecureMail delivery verified. Ross remains in dry-run mode."
   - Verify delivery in Roger's 4SecureMail inbox

2. **Test script path**:
   ```
   scripts/smtp_test.py
   ```

3. **No actual alerts**:
   - Do not trigger Ross
   - Keep `ROSS_DRY_RUN=true` during CP13B
   - Scheduled tasks remain unchanged

## 10. Safety and dry-run plan

### Dry-Run Mode Enforcement

**Current Behavior** (maintained):
```python
if is_dry_run():
    log("ross", f"[DRY-RUN] would send email: {subject}")
    return
```

**Requirement**: Both `send_email()` and `send_telegram()` must respect `ROSS_DRY_RUN=true`.

### Password Safety

1. **Never print or log SMTP password**:
   - Error messages must not contain password
   - Log messages must not contain password
   - Test output must not contain password

2. **Redaction example**:
   ```python
   try:
       s.login(username, password)
   except Exception as e:
       # Redact password from error message
       error_msg = str(e).replace(password, "***REDACTED***")
       raise RuntimeError(f"SMTP login failed: {error_msg}")
   ```

3. **Secret scan before commit**:
   - Verify no `SMTP_PASSWORD=<real value>` in tracked files
   - Verify no password in test fixtures
   - Verify no password in documentation

### Test Isolation

1. **Mock all SMTP connections** in unit tests
2. **No live network calls** during `pytest` runs
3. **Single controlled live test** only after PM approval in CP13B/CP13C

### Rollback Plan

If SMTP fails during CP13B:

1. **Immediate**: Revert `agents/common.py` to previous Gmail-specific version
2. **Restore**: `git revert <commit-hash>` or `git reset --hard HEAD~1`
3. **Fallback**: Gmail configuration still works if Roger has Gmail credentials
4. **Report**: Document failure mode (auth error, connection timeout, etc.)
5. **Retry**: Fix configuration and retry with PM approval

## 11. Single controlled email test plan (CP13B or CP13C)

### Test Message Specification

**Subject**: `[INSIDER-TEST] 4SecureMail SMTP Validation`

**Body**:
```
Insider-Trading CP13B SMTP test

This is a controlled test message to verify 4SecureMail SMTP delivery.

Roger Fiske's 4SecureMail account (fiske1945@4securemail.com) is now
configured for alert delivery via generic SMTP.

Ross dispatcher remains in dry-run mode (ROSS_DRY_RUN=true). No actual
trading alerts will be sent until dry-run is explicitly disabled.

Next step: CP14 planning for full production alert-delivery enablement.
```

### Test Script

Create `scripts/smtp_test.py`:

```python
#!/usr/bin/env python3
"""Send one controlled SMTP test message for CP13B validation."""

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

# Load .env
env_path = Path(".env")
if not env_path.exists():
    print("ERROR: .env not found")
    exit(1)

env_vars = {}
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    if "=" in line:
        key, value = line.split("=", 1)
        env_vars[key.strip()] = value.strip()

host = env_vars.get("SMTP_HOST")
port = int(env_vars.get("SMTP_PORT", "465"))
use_ssl = env_vars.get("SMTP_USE_SSL", "true").lower() == "true"
username = env_vars.get("SMTP_USERNAME")
password = env_vars.get("SMTP_PASSWORD")
from_addr = env_vars.get("ALERT_EMAIL_FROM")
to_addr = env_vars.get("ALERT_EMAIL_TO")

if not all([host, username, password, from_addr, to_addr]):
    print("ERROR: SMTP configuration incomplete in .env")
    exit(1)

subject = "[INSIDER-TEST] 4SecureMail SMTP Validation"
body = """Insider-Trading CP13B SMTP test

This is a controlled test message to verify 4SecureMail SMTP delivery.

Roger Fiske's 4SecureMail account (fiske1945@4securemail.com) is now
configured for alert delivery via generic SMTP.

Ross dispatcher remains in dry-run mode (ROSS_DRY_RUN=true). No actual
trading alerts will be sent until dry-run is explicitly disabled.

Next step: CP14 planning for full production alert-delivery enablement.
"""

msg = EmailMessage()
msg["Subject"] = subject
msg["From"] = from_addr
msg["To"] = to_addr
msg.set_content(body)

try:
    if use_ssl:
        with smtplib.SMTP_SSL(host, port) as s:
            s.login(username, password)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(username, password)
            s.send_message(msg)
    print("SUCCESS: SMTP test message sent")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
```

### Test Execution

```powershell
.\.venv\Scripts\python.exe scripts\smtp_test.py
```

Expected output:
```
SUCCESS: SMTP test message sent
```

Roger should verify the message arrived in his 4SecureMail inbox.

## 12. Validation command results

```
Python: 3.11.9
Branch: main
ross.py: compiles OK
pytest: 64/64 passed in 0.11s
smoke test: 31/31 checks PASS
```

All validation checks passed.

## 13. Confirmation: no `.env` contents printed

✅ **CONFIRMED** - The `.env` file was never printed, read, or displayed during
CP13A. Only `.env.example` placeholders were inspected.

## 14. Confirmation: no email sent

✅ **CONFIRMED** - No email was sent during CP13A. This is a design-only
checkpoint. Email sending will occur in CP13B controlled test only (after PM approval).

## 15. Confirmation: no Telegram message sent

✅ **CONFIRMED** - No Telegram messages were sent during CP13A. This is a
design-only checkpoint.

## 16. Confirmation: no scheduled tasks changed or triggered

✅ **CONFIRMED** - Windows Task Scheduler tasks were verified to be in Ready
state. None were modified or triggered:

```
TaskName       State
--------       -----
Insider-eddie  Ready
Insider-frank  Ready
Insider-janet  Ready
Insider-maggie Ready
Insider-maya   Ready
Insider-ross   Ready
Insider-sophie Ready
```

## 17. Commit hash

None. CP13A is a planning-only checkpoint. No code or configuration changes
were made. The report documents the design but does not implement it.

## 18. Push result

None. No commit was made.

## 19. Risks / blockers

| Risk | Severity | Mitigation |
|------|----------|------------|
| 4SecureMail SMTP host/port unknown | MEDIUM | Roger must verify `mail.4securemail.com:465` with provider docs |
| SMTP auth failure during CP13B test | MEDIUM | Test with dummy credentials first, rollback plan ready |
| Password redaction incomplete | LOW | Add explicit password masking in error handlers |
| Breaking change for existing Gmail users | LOW | This project is Roger-only; no breaking change impact |

## 20. Recommendation

**Proceed to CP13B implementation.**

The design is sound and addresses the key requirement: replacing Gmail-specific
email delivery with provider-neutral SMTP suitable for 4SecureMail.

**Prerequisites for CP13B**:
1. Roger verifies 4SecureMail SMTP settings (host, port, SSL/STARTTLS)
2. Roger adds 4SecureMail credentials to local `.env`
3. PM approves CP13B implementation plan

**Do not proceed** if:
- 4SecureMail SMTP settings are unavailable
- Roger does not have SMTP access credentials
- PM requires design revision

## 21. Awaiting PM Approval

This report documents the design for generic SMTP alert delivery. No code was
implemented in CP13A. Awaiting PM approval to proceed to CP13B implementation
and controlled SMTP test.
