"""R11: keep diagnostic capacity separate from evidence-backed finance metrics."""
from dataclasses import dataclass
from app.engines.budget_engine.reservation_review import BudgetReview


@dataclass(frozen=True)
class FinanceProjection:
    status: str = 'UNVERIFIED'
    authorized_remaining_minor: None = None
    actual_cost_minor: None = None
    revenue_minor: None = None
    collection_minor: None = None
    diagnostic_remaining_minor: int | None = None


def project_finance(review: BudgetReview) -> FinanceProjection:
    if not isinstance(review, BudgetReview) or not review.structural_match or review.reason != 'D0_CAPACITY_MATCH_ONLY':
        return FinanceProjection()
    if type(review.remaining_minor) is not int or not 0 <= review.remaining_minor <= 2**63-1:
        return FinanceProjection()
    return FinanceProjection(diagnostic_remaining_minor=review.remaining_minor)
