#!/usr/bin/env python3
"""
CP20 .env updater - safely update .env with pilot profile.
"""
import os
import sys
from pathlib import Path

def update_env_for_cp20():
    """Update .env with CP20 pilot profile."""
    env_path = Path(".env")

    if not env_path.exists():
        print("ERROR: .env not found")
        return False

    # Read current .env
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Track what we've updated
    updated_dry_run = False
    has_alert_enable_telegram = False
    has_alert_enable_email = False
    has_alert_min_severity = False
    has_alert_dedup_hours = False
    has_alert_max_per_run = False
    has_alert_require_human_review = False

    # Update existing keys
    new_lines = []
    for line in lines:
        stripped = line.strip()

        # Update ROSS_DRY_RUN (only first occurrence, remove duplicates)
        if stripped.startswith('ROSS_DRY_RUN='):
            if not updated_dry_run:
                new_lines.append('ROSS_DRY_RUN=false\n')
                updated_dry_run = True
                print("Updated: ROSS_DRY_RUN=false")
            else:
                print("Removed duplicate: ROSS_DRY_RUN")
            continue

        # Check for existing alert keys
        if stripped.startswith('ALERT_ENABLE_TELEGRAM='):
            has_alert_enable_telegram = True
            new_lines.append('ALERT_ENABLE_TELEGRAM=true\n')
            print("Updated: ALERT_ENABLE_TELEGRAM=true")
            continue
        if stripped.startswith('ALERT_ENABLE_EMAIL='):
            has_alert_enable_email = True
            new_lines.append('ALERT_ENABLE_EMAIL=false\n')
            print("Updated: ALERT_ENABLE_EMAIL=false")
            continue
        if stripped.startswith('ALERT_MIN_SEVERITY='):
            has_alert_min_severity = True
            new_lines.append('ALERT_MIN_SEVERITY=ACTIONABLE\n')
            print("Updated: ALERT_MIN_SEVERITY=ACTIONABLE")
            continue
        if stripped.startswith('ALERT_DEDUP_HOURS='):
            has_alert_dedup_hours = True
            new_lines.append('ALERT_DEDUP_HOURS=24\n')
            print("Updated: ALERT_DEDUP_HOURS=24")
            continue
        if stripped.startswith('ALERT_MAX_PER_RUN='):
            has_alert_max_per_run = True
            new_lines.append('ALERT_MAX_PER_RUN=1\n')
            print("Updated: ALERT_MAX_PER_RUN=1")
            continue
        if stripped.startswith('ALERT_REQUIRE_HUMAN_REVIEW='):
            has_alert_require_human_review = True
            new_lines.append('ALERT_REQUIRE_HUMAN_REVIEW=false\n')
            print("Updated: ALERT_REQUIRE_HUMAN_REVIEW=false")
            continue

        # Keep all other lines unchanged
        new_lines.append(line)

    # Add missing alert keys at the end
    if not has_alert_enable_telegram:
        new_lines.append('\n# Alert channel enablement (CP20)\n')
        new_lines.append('ALERT_ENABLE_TELEGRAM=true\n')
        print("Added: ALERT_ENABLE_TELEGRAM=true")
    if not has_alert_enable_email:
        new_lines.append('ALERT_ENABLE_EMAIL=false\n')
        print("Added: ALERT_ENABLE_EMAIL=false")
    if not has_alert_min_severity:
        new_lines.append('\n# Alert routing policy (CP20)\n')
        new_lines.append('ALERT_MIN_SEVERITY=ACTIONABLE\n')
        print("Added: ALERT_MIN_SEVERITY=ACTIONABLE")
    if not has_alert_dedup_hours:
        new_lines.append('ALERT_DEDUP_HOURS=24\n')
        print("Added: ALERT_DEDUP_HOURS=24")
    if not has_alert_max_per_run:
        new_lines.append('ALERT_MAX_PER_RUN=1\n')
        print("Added: ALERT_MAX_PER_RUN=1")
    if not has_alert_require_human_review:
        new_lines.append('ALERT_REQUIRE_HUMAN_REVIEW=false\n')
        print("Added: ALERT_REQUIRE_HUMAN_REVIEW=false")

    # Write updated .env
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print("\n.env updated successfully for CP20 pilot")
    return True

if __name__ == '__main__':
    success = update_env_for_cp20()
    sys.exit(0 if success else 1)
