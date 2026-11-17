"""W5 D0 diagnostic binding; never a reservation receipt or execution authority."""
from dataclasses import dataclass, field
from .runtime_binding import InvocationEnvelope, inspect_invocation
from app.core.transaction.review import LogicalIntent, Operation, valid_intent
from app.core.transaction.postgres_admission_mapping import ClaimSpec, claim_digest, valid_budget
from app.core.transaction.postgres_transition_mapping import transaction_ref
from app.core.agent_runtime.lifecycle import RunState, uint, token
from app.engines.budget_engine.reservation_review import BudgetSnapshot, valid_budget as valid_snapshot
from app.core.policy.gateway_review import EffectScope, valid_effect

@dataclass(frozen=True)
class ReservationObservation:
    """Exact existing sample_reservations row, with scope supplied by its read boundary."""
    scope: object
    budget_id: str
    budget_revision: int
    amount_minor: int
    currency: str
    request_digest: str
    transaction_ref: str

@dataclass(frozen=True)
class EffectBudgetReview:
    reason: str
    structural_match: bool = False
    decision: str = field(default="HOLD", init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)

def inspect_effect_budget(envelope, registry, invocation_pin, current_run, current_lease,
                          clock, raw, admission, claim, reservation, budget, effect):
    """Compare D0 observations only. Caller inputs are not independent readback.
    Admission digest/idempotency and model invocation digest/idempotency are distinct.
    The current schema has no per-invocation reservation receipt; never grant.
    """
    try:
        if type(envelope) is not InvocationEnvelope:
            return EffectBudgetReview("MODEL_ENVELOPE_HOLD")
        review = inspect_invocation(envelope, registry, invocation_pin, current_run,
                                    current_lease, clock, raw)
        if not review.structural_match:
            return EffectBudgetReview(review.reason)
        if (type(admission) is not LogicalIntent or not valid_intent(admission)
                or admission.operation is not Operation.ADMISSION
                or type(claim) is not ClaimSpec or not valid_budget(claim.budget)
                or claim.before.state is not RunState.QUEUED
                or claim.before.scope != admission.scope
                or claim.before.version != admission.expected_version
                or admission.request_digest != claim_digest(claim)):
            return EffectBudgetReview("ADMISSION_BINDING_HOLD")
        if (admission.scope != envelope.run.scope or claim.lease.scope != admission.scope
                or claim.lease.lease_id != admission.lease_ref
                or claim.lease.grant_id != admission.grant_ref
                or claim.budget.budget_id != admission.budget_ref
                or not token(claim.admission_id) or not uint(claim.amount_minor)
                or claim.amount_minor == 0
                or envelope.run.version <= admission.expected_version + 1):
            return EffectBudgetReview("ADMISSION_SCOPE_HOLD")
        if type(reservation) is not ReservationObservation:
            return EffectBudgetReview("RESERVATION_MISSING_HOLD")
        expected = ReservationObservation(admission.scope, claim.budget.budget_id,
            claim.budget.revision + 1, claim.amount_minor, claim.budget.currency,
            admission.request_digest, transaction_ref(admission))
        if reservation != expected:
            return EffectBudgetReview("RESERVATION_ROW_MISMATCH_HOLD")
        # Existing row has no reservation_id. Do not invent an alias for reservation_ref.
        if type(budget) is not BudgetSnapshot or not valid_snapshot(budget):
            return EffectBudgetReview("CURRENT_BUDGET_MISSING_HOLD")
        if (budget.scope, budget.budget_id, budget.currency, budget.policy_epoch,
                budget.witness_epoch) != (admission.scope, reservation.budget_id,
                reservation.currency, current_lease.policy_epoch, current_lease.witness_epoch):
            return EffectBudgetReview("CURRENT_BUDGET_SCOPE_HOLD")
        if budget.unknown_cost:
            return EffectBudgetReview("UNKNOWN_COST_HOLD")
        if (budget.revision < reservation.budget_revision
                or budget.outstanding_minor < reservation.amount_minor
                or budget.outstanding_minor + budget.recognized_cost_minor > budget.limit_minor
                or envelope.sample_cost_ceiling_minor > reservation.amount_minor):
            return EffectBudgetReview("BUDGET_CAPACITY_HOLD")
        if type(effect) is not EffectScope or not valid_effect(effect):
            return EffectBudgetReview("MODEL_EFFECT_MISSING_HOLD")
        if (effect.scope, effect.action, effect.effect_digest, effect.admission_id,
                effect.budget_id, effect.lease_id, effect.grant_id, effect.policy_epoch,
                effect.witness_epoch, effect.fence) != (admission.scope, "MODEL_SAMPLE_REVIEW",
                invocation_pin, claim.admission_id, reservation.budget_id,
                current_lease.lease_id, current_lease.grant_id, current_lease.policy_epoch,
                current_lease.witness_epoch, current_lease.fence):
            return EffectBudgetReview("MODEL_EFFECT_BINDING_HOLD")
        return EffectBudgetReview("D0_MATCH_ONLY_INVOCATION_RECEIPT_AND_AUTHORITY_ABSENT", True)
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        return EffectBudgetReview("MODEL_EFFECT_BUDGET_SHAPE_HOLD")
