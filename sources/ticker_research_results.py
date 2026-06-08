"""Structured result classes for ticker research operations.

These dataclasses provide structured output from Eddie and Maggie ticker research,
enabling downstream agents (Sophie, Ross) to process results programmatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EddieTickerResult:
    """Structured result from Eddie's SEC Form 4 insider transaction research.

    Attributes:
        ticker: Stock ticker symbol
        cik: SEC CIK (10-digit padded)
        company_name: Issuer company name
        lookback_days: Lookback window in days
        status: Eddie applicability status (APPLICABLE_WITH_EVIDENCE, etc.)
        signal: Signal type (BULLISH_EVIDENCE, BEARISH_EVIDENCE, NEUTRAL)
        confidence: Confidence level (1-5)
        reason: Human-readable reason for status/signal
        filings_found: Total Form 4 filings found in lookback window
        filings_attempted: Number of filings attempted to parse
        filings_parsed: Number of filings successfully parsed
        filings_failed: Number of filings that failed to parse
        transactions_extracted: Total transactions extracted
        purchase_count: Number of open-market purchase transactions
        purchase_value: Total value of open-market purchases (USD)
        sale_count: Number of open-market sale transactions
        sale_value: Total value of open-market sales (USD)
        option_exercise_count: Number of option exercise transactions
        grant_award_count: Number of grant/award transactions
        reporting_owners: List of notable reporting owners
        source_accessions: List of Form 4 accession numbers
        error_message: Error message if failed, None otherwise
    """

    ticker: str
    cik: str
    company_name: str
    lookback_days: int
    status: str
    signal: str
    confidence: int
    reason: str
    filings_found: int
    filings_attempted: int
    filings_parsed: int
    filings_failed: int
    transactions_extracted: int
    purchase_count: int
    purchase_value: float
    sale_count: int
    sale_value: float
    option_exercise_count: int
    grant_award_count: int
    reporting_owners: list[str] = field(default_factory=list)
    source_accessions: list[str] = field(default_factory=list)
    error_message: str | None = None


@dataclass
class MaggieTickerResult:
    """Structured result from Maggie's SEC 13F institutional holdings research.

    Attributes:
        ticker: Stock ticker symbol
        cik: SEC CIK (10-digit padded) for the issuer
        company_name: Issuer company name
        status: Maggie applicability status
        signal: Signal type (BULLISH_EVIDENCE, BEARISH_EVIDENCE, NEUTRAL)
        confidence: Confidence level (1-5)
        reason: Human-readable reason for status/signal
        managers_reviewed: Number of institutional managers reviewed
        filings_found: Total 13F filings found
        filings_parsed: Number of 13F filings successfully parsed
        holdings_found: Number of holdings matched to this ticker
        match_method: Method used to match holdings (CUSIP, issuer_name, etc.)
        total_shares: Total shares held by matched institutions
        total_value: Total market value of matched holdings (USD)
        limitations: List of limitations or data quality issues
        source_urls: List of 13F filing source URLs
        error_message: Error message if failed, None otherwise
    """

    ticker: str
    cik: str
    company_name: str
    status: str
    signal: str
    confidence: int
    reason: str
    managers_reviewed: int
    filings_found: int
    filings_parsed: int
    holdings_found: int
    match_method: str
    total_shares: int
    total_value: float
    limitations: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)
    error_message: str | None = None


@dataclass
class TickerResearchReport:
    """Combined structured report from ticker research workflow.

    Attributes:
        ticker: Stock ticker symbol
        generated_at: ISO 8601 UTC timestamp of report generation
        eddie_result: Structured Eddie result
        maggie_result: Structured Maggie result
        markdown_report: Full markdown report content
    """

    ticker: str
    generated_at: str
    eddie_result: EddieTickerResult
    maggie_result: MaggieTickerResult
    markdown_report: str
