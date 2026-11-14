"""R11: integer minor-unit reservation arithmetic, no ledger or spend."""
from dataclasses import dataclass
from app.core.agent_runtime.lifecycle import Scope, valid_scope, token, uint
from app.core.transaction.review import digest_ok


@dataclass(frozen=True)
class BudgetSnapshot:
    scope: Scope
    budget_id: str
    revision: int
    currency: str
    limit_minor: int
    outstanding_minor: int
    recognized_cost_minor: int
    unknown_cost: bool
    policy_epoch: int
    witness_epoch: int
    source_digest: str


@dataclass(frozen=True)
class ReservationRequest:
    scope: Scope
    budget_id: str
    expected_revision: int
    currency: str
    amount_minor: int
    idempotency_key: str
    policy_epoch: int
    witness_epoch: int


@dataclass(frozen=True)
class BudgetReview:
    reason: str
    structural_match: bool = False
    remaining_minor: int | None = None
    reservation_created: bool = False
    spend_allowed: bool = False
    actual_cost_minor: None = None
    revenue_minor: None = None
    collection_minor: None = None


def valid_budget(b: object) -> bool:
    return (isinstance(b, BudgetSnapshot) and valid_scope(b.scope) and token(b.budget_id)
            and isinstance(b.currency, str) and len(b.currency) == 3 and b.currency.isascii()
            and b.currency.isalpha() and b.currency.isupper()
            and all(uint(x) for x in (b.revision, b.limit_minor, b.outstanding_minor,
                                     b.recognized_cost_minor, b.policy_epoch, b.witness_epoch))
            and type(b.unknown_cost) is bool and digest_ok(b.source_digest))


def inspect_reservation(q: ReservationRequest, snapshot: BudgetSnapshot | None,
                        reference: BudgetSnapshot | None) -> BudgetReview:
    if (not isinstance(q, ReservationRequest) or not valid_scope(q.scope)
            or not all(token(x) for x in (q.budget_id, q.idempotency_key, q.currency))
            or not all(uint(x) for x in (q.expected_revision, q.amount_minor, q.policy_epoch, q.witness_epoch))
            or q.amount_minor == 0):
        return BudgetReview('BUDGET_REQUEST_INVALID')
    if not valid_budget(snapshot) or not valid_budget(reference) or snapshot != reference:
        return BudgetReview('BUDGET_REFERENCE_HOLD')
    if (q.scope, q.budget_id, q.expected_revision, q.currency, q.policy_epoch, q.witness_epoch) != (
            snapshot.scope, snapshot.budget_id, snapshot.revision, snapshot.currency,
            snapshot.policy_epoch, snapshot.witness_epoch):
        return BudgetReview('BUDGET_SCOPE_CAS_CURRENCY_EPOCH_HOLD')
    if snapshot.unknown_cost:
        return BudgetReview('UNKNOWN_COST_HOLD')
    used = snapshot.outstanding_minor + snapshot.recognized_cost_minor
    if used > snapshot.limit_minor or q.amount_minor > snapshot.limit_minor - used:
        return BudgetReview('BUDGET_LIMIT_HOLD')
    return BudgetReview('D0_CAPACITY_MATCH_ONLY', True, snapshot.limit_minor - used - q.amount_minor)
