"""Shared test fixtures for the Insider Trading test suite."""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to sys.path so tests can import sources/ and evidence/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
