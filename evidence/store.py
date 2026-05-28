"""Evidence store -- file-backed JSON persistence for evidence records.

Writes evidence bundles as individual JSON files under .state/evidence/.
Each file is named: {timestamp}_{agent}_{suffix}.json

The directory is gitignored.  Evidence records must not contain secrets.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence.schema import EvidenceBundle, SourceFetchResult


def _evidence_dir() -> Path:
    """Return the evidence storage directory, creating it if needed."""
    root = Path(__file__).resolve().parents[1]
    evidence_dir = root / ".state" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir


def save_evidence(bundle: EvidenceBundle) -> str:
    """Persist an evidence bundle to disk.

    Returns the file path of the saved evidence file.
    """
    evidence_dir = _evidence_dir()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    filename = f"{ts}_{bundle.agent}_{suffix}.json"
    filepath = evidence_dir / filename

    data = bundle.to_dict()
    filepath.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    bundle.evidence_path = str(filepath)
    return str(filepath)


def load_evidence(filepath: str) -> EvidenceBundle:
    """Load an evidence bundle from a JSON file."""
    data: dict[str, Any] = json.loads(
        Path(filepath).read_text(encoding="utf-8")
    )
    fetch_result = SourceFetchResult.from_dict(data.get("fetch_result", {}))
    return EvidenceBundle(
        agent=str(data.get("agent", "")),
        fetch_result=fetch_result,
        evidence_path=data.get("evidence_path"),
    )


def list_evidence(agent: str | None = None) -> list[str]:
    """List evidence file paths, optionally filtered by agent name."""
    evidence_dir = _evidence_dir()
    files = sorted(evidence_dir.glob("*.json"))
    if agent:
        files = [f for f in files if f"_{agent}_" in f.name]
    return [str(f) for f in files]
