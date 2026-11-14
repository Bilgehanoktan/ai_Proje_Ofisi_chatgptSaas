"""R03/R01: bind logical write-set to explicit synthetic evidence; no physical mapping."""
from dataclasses import dataclass
from app.core.agent_runtime.lifecycle import Scope, LeaseObservation, ClockSample, valid_scope, token, uint
from app.core.transaction.review import LogicalIntent, Operation, RoleObservation, valid_intent, inspect_write_set, digest_ok
from app.engines.budget_engine.reservation_review import BudgetSnapshot, ReservationRequest, inspect_reservation


@dataclass(frozen=True)
class HeadReadback:
    scope: Scope
    version: int
    transaction_ref: str
    request_digest: str
    policy_epoch: int
    witness_epoch: int


@dataclass(frozen=True)
class AdmissionPin:
    scope: Scope
    admission_id: str
    grant_id: str
    lease_id: str
    budget_id: str | None
    request_digest: str
    fence: int
    policy_epoch: int
    witness_epoch: int


@dataclass(frozen=True)
class ReadbackReview:
    reason: str
    structural_match: bool = False
    atomicity_proven: bool = False
    committed: bool = False
    commit_allowed: bool = False
    physical_mapping: str = 'PHYSICAL_MAPPING_HOLD'


def valid_head(h: object) -> bool:
    return (isinstance(h, HeadReadback) and valid_scope(h.scope) and token(h.transaction_ref)
            and digest_ok(h.request_digest) and all(uint(x) for x in (h.version, h.policy_epoch, h.witness_epoch)))


def valid_admission(a: object) -> bool:
    return (isinstance(a, AdmissionPin) and valid_scope(a.scope)
            and all(token(x) for x in (a.admission_id, a.grant_id, a.lease_id))
            and (a.budget_id is None or token(a.budget_id)) and digest_ok(a.request_digest)
            and all(uint(x) for x in (a.fence, a.policy_epoch, a.witness_epoch)) and a.fence > 0)


def inspect_admission(i: LogicalIntent, rows: tuple[RoleObservation, ...],
                      head: HeadReadback, expected_head: HeadReadback,
                      admission: AdmissionPin, expected_admission: AdmissionPin,
                      lease: LeaseObservation, lease_reference: LeaseObservation, clock: ClockSample,
                      request: ReservationRequest, budget: BudgetSnapshot, budget_reference: BudgetSnapshot) -> ReadbackReview:
    if not valid_intent(i) or i.operation != Operation.ADMISSION:
        return ReadbackReview('ADMISSION_INTENT_HOLD')
    if (not valid_head(head) or not valid_head(expected_head) or head != expected_head
            or (head.scope, head.version, head.request_digest, head.policy_epoch, head.witness_epoch) !=
               (i.scope, i.expected_version, i.request_digest, i.policy_epoch, i.witness_epoch)):
        return ReadbackReview('HEAD_REFERENCE_CAS_HOLD')
    t1 = inspect_write_set(i, rows, head.version, lease, lease_reference, clock)
    if not t1.structural_match:
        return ReadbackReview(t1.reason)
    if any(r.transaction_ref != head.transaction_ref for r in rows):
        return ReadbackReview('READBACK_TRANSACTION_HOLD')
    if (not valid_admission(admission) or not valid_admission(expected_admission) or admission != expected_admission
            or (admission.scope, admission.grant_id, admission.lease_id, admission.budget_id,
                admission.request_digest, admission.fence, admission.policy_epoch, admission.witness_epoch) !=
               (i.scope, i.grant_ref, i.lease_ref, i.budget_ref, i.request_digest, lease.fence,
                i.policy_epoch, i.witness_epoch)):
        return ReadbackReview('ADMISSION_REFERENCE_HOLD')
    b = inspect_reservation(request, budget, budget_reference)
    if not b.structural_match:
        return ReadbackReview(b.reason)
    if (request.scope, request.budget_id, request.idempotency_key, request.policy_epoch, request.witness_epoch) != (
            i.scope, i.budget_ref, i.idempotency_key, i.policy_epoch, i.witness_epoch):
        return ReadbackReview('RESERVATION_INTENT_BINDING_HOLD')
    return ReadbackReview('D0_READBACK_MATCH_ATOMICITY_UNPROVEN', True)
