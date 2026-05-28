"""Base connector interface for all source connectors.

Every connector subclasses BaseConnector and implements fetch() and
format_for_prompt().  The fetch() method returns a SourceFetchResult
containing typed evidence records.  format_for_prompt() converts
the fetched evidence into a text block suitable for injection into
a Claude prompt.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from evidence.schema import SourceFetchResult


class BaseConnector(ABC):
    """Abstract base class for source connectors."""

    @abstractmethod
    def fetch(self) -> SourceFetchResult:
        """Fetch data from the source.

        Must be implemented by each connector subclass.
        Must not raise -- return SourceFetchResult.failure() on error.
        """

    @abstractmethod
    def format_for_prompt(self, result: SourceFetchResult) -> str:
        """Format fetched evidence as text for a Claude prompt.

        Returns a human-readable summary of the evidence suitable for
        insertion into the user prompt.
        """
