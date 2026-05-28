"""Evidence schema -- typed models for auditable source-grounding records.

Every piece of data fetched by a source connector is wrapped in a
SourceEvidence record that carries provenance (URL, timestamp, canonical ID).
A SourceFetchResult groups one connector invocation's evidence list with
success/failure metadata.  An EvidenceBundle ties a fetch result to the
agent that requested it.

No third-party dependencies required -- stdlib only.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SourceEvidence:
    """A single piece of auditable evidence from a source connector."""

    source_type: str
    source_name: str
    source_url: str
    retrieved_at: str
    canonical_id: str | None = None
    raw_excerpt: str | None = None
    normalized: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceEvidence:
        """Deserialize from a plain dict."""
        return cls(
            source_type=str(data.get("source_type", "")),
            source_name=str(data.get("source_name", "")),
            source_url=str(data.get("source_url", "")),
            retrieved_at=str(data.get("retrieved_at", "")),
            canonical_id=data.get("canonical_id"),
            raw_excerpt=data.get("raw_excerpt"),
            normalized=data.get("normalized") or {},
            metadata=data.get("metadata") or {},
        )


@dataclass
class SourceFetchResult:
    """Result of a single connector invocation."""

    ok: bool
    source_name: str
    evidence: list[SourceEvidence] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None
    retrieved_at: str = ""

    def __post_init__(self) -> None:
        if not self.retrieved_at:
            self.retrieved_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON."""
        d = asdict(self)
        d["evidence"] = [e.to_dict() for e in self.evidence]
        return d

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SourceFetchResult:
        """Deserialize from a plain dict."""
        evidence = [
            SourceEvidence.from_dict(e) for e in data.get("evidence", [])
        ]
        return cls(
            ok=bool(data.get("ok", False)),
            source_name=str(data.get("source_name", "")),
            evidence=evidence,
            error_type=data.get("error_type"),
            error_message=data.get("error_message"),
            retrieved_at=str(data.get("retrieved_at", "")),
        )

    @classmethod
    def failure(
        cls,
        source_name: str,
        error_type: str,
        error_message: str,
    ) -> SourceFetchResult:
        """Create a failure result with no evidence."""
        return cls(
            ok=False,
            source_name=source_name,
            error_type=error_type,
            error_message=error_message,
        )


@dataclass
class EvidenceBundle:
    """Ties a fetch result to the agent that requested it."""

    agent: str
    fetch_result: SourceFetchResult
    evidence_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict suitable for JSON."""
        return {
            "agent": self.agent,
            "fetch_result": self.fetch_result.to_dict(),
            "evidence_path": self.evidence_path,
        }

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
