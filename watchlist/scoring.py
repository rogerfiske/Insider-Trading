"""Insider evidence scoring for manual ticker watchlist ranking.

This module provides transparent, auditable scoring of insider buying evidence
based on SEC Form 4 transaction data. Scores are for research/ranking purposes
only and are not trading recommendations.

Score Range: 0-100 points
Rating Labels: Very Strong / Strong / Moderate / Weak / Little or No Evidence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class InsiderEvidenceScore:
    """Insider evidence score with component breakdown and explanations.

    Attributes:
        ticker: Stock ticker symbol
        total_score: Total score (0-100)
        rating_label: Human-readable rating label
        component_scores: Dict of component name to score
        component_explanations: Dict of component name to explanation
        warnings: List of warnings about missing/incomplete data
    """

    ticker: str
    total_score: float
    rating_label: str
    component_scores: dict[str, float] = field(default_factory=dict)
    component_explanations: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dict representation of the score
        """
        return {
            "ticker": self.ticker,
            "total_score": round(self.total_score, 2),
            "rating_label": self.rating_label,
            "component_scores": {k: round(v, 2) for k, v in self.component_scores.items()},
            "component_explanations": self.component_explanations,
            "warnings": self.warnings,
        }


def compute_net_buying_value_score(
    purchase_value: float | None, sale_value: float | None
) -> tuple[float, str]:
    """Compute net insider buying value score (0-25 points).

    Args:
        purchase_value: Total purchase value in dollars
        sale_value: Total sale value in dollars

    Returns:
        Tuple of (score, explanation)
    """
    if purchase_value is None:
        purchase_value = 0.0
    if sale_value is None:
        sale_value = 0.0

    net_value = purchase_value - sale_value

    if net_value <= 0:
        return 0.0, f"Net value ${net_value:,.2f} (no net buying)"
    elif net_value < 25000:
        return 5.0, f"Net value ${net_value:,.2f} ($1-$25k tier)"
    elif net_value < 100000:
        return 10.0, f"Net value ${net_value:,.2f} ($25k-$100k tier)"
    elif net_value < 500000:
        return 15.0, f"Net value ${net_value:,.2f} ($100k-$500k tier)"
    elif net_value < 1000000:
        return 20.0, f"Net value ${net_value:,.2f} ($500k-$1M tier)"
    else:
        return 25.0, f"Net value ${net_value:,.2f} (>$1M tier)"


def compute_buy_sell_imbalance_score(
    purchase_value: float | None,
    sale_value: float | None,
    purchase_count: int | None,
    sale_count: int | None,
) -> tuple[float, str]:
    """Compute buy/sell imbalance score (0-20 points).

    Rewards strong buying with little/no selling.

    Args:
        purchase_value: Total purchase value
        sale_value: Total sale value
        purchase_count: Number of purchase transactions
        sale_count: Number of sale transactions

    Returns:
        Tuple of (score, explanation)
    """
    if purchase_value is None:
        purchase_value = 0.0
    if sale_value is None:
        sale_value = 0.0
    if purchase_count is None:
        purchase_count = 0
    if sale_count is None:
        sale_count = 0

    if purchase_count > 0 and sale_count == 0:
        return 20.0, f"{purchase_count} purchases, no sales (perfect buying pattern)"
    elif purchase_value > 0 and sale_value > 0:
        if purchase_value > sale_value * 5:
            return 15.0, f"Purchases ${purchase_value:,.0f} vs sales ${sale_value:,.0f} (5:1+ ratio)"
        elif purchase_value > sale_value:
            return 10.0, f"Purchases ${purchase_value:,.0f} vs sales ${sale_value:,.0f} (net buying)"
        else:
            return 0.0, f"Purchases ${purchase_value:,.0f} vs sales ${sale_value:,.0f} (sales >= purchases)"
    elif purchase_count == 0 and sale_count == 0:
        return 0.0, "No transactions"
    elif purchase_value == 0.0 and sale_value > 0:
        return 0.0, f"Only sales detected (${sale_value:,.0f})"
    else:
        return 0.0, "Insufficient imbalance data"


def compute_distinct_buyer_breadth_score(
    distinct_buyers: int | None,
) -> tuple[float, str]:
    """Compute distinct buyer breadth score (0-15 points).

    Rewards more distinct insider buyers.

    Args:
        distinct_buyers: Number of distinct buyers

    Returns:
        Tuple of (score, explanation)
    """
    if distinct_buyers is None or distinct_buyers == 0:
        return 0.0, "No distinct buyers detected"
    elif distinct_buyers == 1:
        return 5.0, "1 distinct buyer"
    elif distinct_buyers == 2:
        return 8.0, "2 distinct buyers"
    elif distinct_buyers in (3, 4):
        return 12.0, f"{distinct_buyers} distinct buyers"
    else:
        return 15.0, f"{distinct_buyers} distinct buyers (broad participation)"


def compute_recency_score(latest_purchase_date: str | None) -> tuple[float, str]:
    """Compute recency score (0-15 points).

    Rewards recent purchases.

    Args:
        latest_purchase_date: ISO date string of latest purchase

    Returns:
        Tuple of (score, explanation)
    """
    if not latest_purchase_date:
        return 0.0, "No purchase date available"

    try:
        latest_date = datetime.fromisoformat(latest_purchase_date.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_ago = (now - latest_date).days

        if days_ago <= 30:
            return 15.0, f"Latest purchase {days_ago} days ago (<= 30 days)"
        elif days_ago <= 90:
            return 12.0, f"Latest purchase {days_ago} days ago (31-90 days)"
        elif days_ago <= 180:
            return 8.0, f"Latest purchase {days_ago} days ago (91-180 days)"
        elif days_ago <= 365:
            return 5.0, f"Latest purchase {days_ago} days ago (181-365 days)"
        else:
            return 0.0, f"Latest purchase {days_ago} days ago (> 365 days)"
    except (ValueError, TypeError) as e:
        return 0.0, f"Invalid purchase date format: {e}"


def compute_role_quality_score(buyer_roles: list[str] | None) -> tuple[float, str]:
    """Compute role quality score (0-10 points).

    Rewards purchases by high-signal insiders (CEO, CFO, Directors, 10% owners).

    Args:
        buyer_roles: List of buyer role/title strings

    Returns:
        Tuple of (score, explanation)
    """
    if not buyer_roles:
        return 0.0, "No buyer role evidence"

    # Normalize roles to lowercase for matching
    roles_lower = [r.lower() for r in buyer_roles if r]

    # Check for high-signal roles (use highest)
    # Note: Check for "vice" to exclude Vice President from executive tier
    has_executive = False
    for role in roles_lower:
        # Exclude Vice President/Vice Chairman/etc from executive tier
        if "vice" not in role:
            if any(keyword in role for keyword in ["ceo", "cfo", "chief executive", "chief financial", "president"]):
                has_executive = True
                break

    has_director = any("director" in role for role in roles_lower)
    has_owner = any(keyword in role for role in roles_lower for keyword in ["10%", "ten percent owner"])

    if has_executive:
        return 10.0, "Executive purchase detected (CEO/CFO/President)"
    elif has_director or has_owner:
        return 7.0, "Director or 10% owner purchase detected"
    else:
        return 3.0, "Other insider purchase detected"


def compute_persistence_score(purchase_months: list[str] | None) -> tuple[float, str]:
    """Compute persistence score (0-10 points).

    Rewards repeated buying across multiple months.

    Args:
        purchase_months: List of YYYY-MM month strings when purchases occurred

    Returns:
        Tuple of (score, explanation)
    """
    if not purchase_months:
        return 0.0, "No purchase month data"

    distinct_months = len(set(purchase_months))

    if distinct_months >= 3:
        return 10.0, f"Purchases in {distinct_months} distinct months (persistent buying)"
    elif distinct_months == 2:
        return 6.0, f"Purchases in {distinct_months} distinct months"
    elif distinct_months == 1:
        return 3.0, "Purchases in 1 month only"
    else:
        return 0.0, "No purchases"


def compute_data_quality_score(
    form4_filings_found: int | None, form4_filings_parsed: int | None
) -> tuple[float, str]:
    """Compute data quality score (0-5 points).

    Rewards completeness of Form 4 parsing.

    Args:
        form4_filings_found: Number of Form 4 filings found
        form4_filings_parsed: Number successfully parsed

    Returns:
        Tuple of (score, explanation)
    """
    if form4_filings_found is None or form4_filings_found == 0:
        return 0.0, "No Form 4 filings found"

    if form4_filings_parsed is None:
        form4_filings_parsed = 0

    parse_rate = form4_filings_parsed / form4_filings_found

    if parse_rate >= 0.95:
        return 5.0, f"{form4_filings_parsed}/{form4_filings_found} filings parsed (>= 95%)"
    elif parse_rate >= 0.80:
        return 3.0, f"{form4_filings_parsed}/{form4_filings_found} filings parsed (80-94%)"
    elif parse_rate >= 0.50:
        return 1.0, f"{form4_filings_parsed}/{form4_filings_found} filings parsed (50-79%)"
    else:
        return 0.0, f"{form4_filings_parsed}/{form4_filings_found} filings parsed (< 50%)"


def get_rating_label(total_score: float) -> str:
    """Map total score to rating label.

    Args:
        total_score: Total score (0-100)

    Returns:
        Human-readable rating label
    """
    if total_score >= 80:
        return "Very Strong Insider Buying Evidence"
    elif total_score >= 60:
        return "Strong Insider Buying Evidence"
    elif total_score >= 40:
        return "Moderate Insider Buying Evidence"
    elif total_score >= 20:
        return "Weak Insider Buying Evidence"
    else:
        return "Little/No Insider Buying Evidence"


def compute_insider_evidence_score(
    ticker: str, metrics: dict[str, Any]
) -> InsiderEvidenceScore:
    """Compute comprehensive insider evidence score for a ticker.

    Args:
        ticker: Stock ticker symbol
        metrics: Dict of ticker metrics (from extract_ticker_metrics)

    Returns:
        InsiderEvidenceScore with component breakdown
    """
    warnings = []

    # Component 1: Net Insider Buying Value (0-25 points)
    net_buying_score, net_buying_exp = compute_net_buying_value_score(
        metrics.get("purchase_value"), metrics.get("sale_value")
    )

    # Component 2: Buy/Sell Imbalance (0-20 points)
    imbalance_score, imbalance_exp = compute_buy_sell_imbalance_score(
        metrics.get("purchase_value"),
        metrics.get("sale_value"),
        metrics.get("purchase_count"),
        metrics.get("sale_count"),
    )

    # Component 3: Distinct Buyer Breadth (0-15 points)
    breadth_score, breadth_exp = compute_distinct_buyer_breadth_score(
        metrics.get("distinct_buyers")
    )
    if metrics.get("distinct_buyers") is None:
        warnings.append("distinct_buyers field missing")

    # Component 4: Recency (0-15 points)
    recency_score, recency_exp = compute_recency_score(
        metrics.get("latest_purchase_date")
    )
    if not metrics.get("latest_purchase_date"):
        warnings.append("latest_purchase_date field missing")

    # Component 5: Role Quality (0-10 points)
    role_score, role_exp = compute_role_quality_score(metrics.get("buyer_roles"))
    if not metrics.get("buyer_roles"):
        warnings.append("buyer_roles field missing")

    # Component 6: Persistence (0-10 points)
    persistence_score, persistence_exp = compute_persistence_score(
        metrics.get("purchase_months")
    )
    if not metrics.get("purchase_months"):
        warnings.append("purchase_months field missing")

    # Component 7: Data Quality (0-5 points)
    quality_score, quality_exp = compute_data_quality_score(
        metrics.get("form4_filings_found"), metrics.get("form4_filings_parsed")
    )

    # Compute total score
    total_score = (
        net_buying_score
        + imbalance_score
        + breadth_score
        + recency_score
        + role_score
        + persistence_score
        + quality_score
    )

    # Get rating label
    rating_label = get_rating_label(total_score)

    # Build component maps
    component_scores = {
        "net_buying_value": net_buying_score,
        "buy_sell_imbalance": imbalance_score,
        "buyer_breadth": breadth_score,
        "recency": recency_score,
        "role_quality": role_score,
        "persistence": persistence_score,
        "data_quality": quality_score,
    }

    component_explanations = {
        "net_buying_value": net_buying_exp,
        "buy_sell_imbalance": imbalance_exp,
        "buyer_breadth": breadth_exp,
        "recency": recency_exp,
        "role_quality": role_exp,
        "persistence": persistence_exp,
        "data_quality": quality_exp,
    }

    return InsiderEvidenceScore(
        ticker=ticker,
        total_score=total_score,
        rating_label=rating_label,
        component_scores=component_scores,
        component_explanations=component_explanations,
        warnings=warnings,
    )
