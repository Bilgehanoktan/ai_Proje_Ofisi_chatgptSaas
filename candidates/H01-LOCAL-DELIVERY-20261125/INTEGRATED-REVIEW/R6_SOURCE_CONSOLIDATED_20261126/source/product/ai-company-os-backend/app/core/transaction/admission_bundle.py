"""D0 cross-engine admission review; never a transaction writer or authority grant."""
from dataclasses import dataclass, field
from app.core.agent_runtime.lifecycle import ClockSample, LeaseObservation, uint
from app.core.policy.witness_review import WitnessSample, inspect_witness
from app.core.transaction.review import LogicalIntent, RoleObservation
from app.core.transaction.readback_review import HeadReadback, AdmissionPin, inspect_admission
from app.engines.budget_engine.reservation_review import BudgetSnapshot, ReservationRequest


@dataclass(frozen=True)
class AdmissionBundle:
    intent: LogicalIntent
    rows: tuple[RoleObservation, ...]
    head: HeadReadback
    expected_head: HeadReadback
    admission: AdmissionPin
    expected_admission: AdmissionPin
    lease: LeaseObservation
    lease_reference: LeaseObservation
    clock: ClockSample
    request: ReservationRequest
    budget: BudgetSnapshot
    budget_reference: BudgetSnapshot
    witness: WitnessSample
    witness_reference: WitnessSample
    witness_max_age: int


@dataclass(frozen=True)
class BundleReview:
    reason: str
    matched: tuple[str, ...] = ()
    decision: str = field(default='HOLD', init=False)
    commit_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    authoritative: bool = field(default=False, init=False)
    physical_mapping: str = field(default='PHYSICAL_MAPPING_HOLD', init=False)


def inspect_admission_bundle(b: AdmissionBundle) -> BundleReview:
    if not isinstance(b, AdmissionBundle) or not uint(b.witness_max_age) or b.witness_max_age == 0:
        return BundleReview('ADMISSION_BUNDLE_INVALID')
    review = inspect_admission(b.intent, b.rows, b.head, b.expected_head, b.admission,
                               b.expected_admission, b.lease, b.lease_reference, b.clock,
                               b.request, b.budget, b.budget_reference)
    if not review.structural_match or review.atomicity_proven or review.committed or review.commit_allowed:
        return BundleReview(review.reason)
    # Explicit D0 record convention, not a ratified physical mapping. Budget is the budget
    # snapshot ID, not a reservation receipt; admission and lease are reference IDs only.
    ids = {row.role: row.record_id for row in b.rows}
    if (ids.get('ADMISSION'), ids.get('LEASE'), ids.get('BUDGET')) != (
            b.admission.admission_id, b.lease.lease_id, b.budget.budget_id):
        return BundleReview('ADMISSION_ROLE_REFERENCE_HOLD')
    matched = ('admission-shape', 'role-reference-shape', 'budget-shape', 'lease-shape')
    witness = inspect_witness(b.witness, b.witness_reference, b.intent.scope,
                              b.intent.witness_epoch, b.clock.now_tick, b.witness_max_age)
    if not witness.structural_match or witness.authoritative or witness.dispatch_allowed:
        return BundleReview(witness.reason, matched)
    return BundleReview('D0_BUNDLE_MATCH_AUTHORITY_UNPROVEN', matched + ('witness-shape',))
