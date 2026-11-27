"""R03/R01: bind logical write-set to explicit synthetic evidence; no physical mapping."""
from dataclasses import dataclass
from app.core.agent_runtime.lifecycle import Scope, LeaseObservation, ClockSample, valid_scope, token, uint
from app.core.transaction.review import LogicalIntent, Operation, RoleObservation, valid_intent, inspect_write_set, digest_ok
from app.engines.budget_engine.reservation_review import BudgetSnapshot, ReservationRequest, inspect_reservation
from app.core.transaction.review import BASE_ROLES, WorkItemRequestDraft, inspect_workitem_request


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


# Direction A: non-executable observation contract. Do not route it into the
# run-scoped writer, install DDL, or derive authority from caller observations.


@dataclass(frozen=True)
class WorkItemReadbackPin:
    """Synthetic expected/observed creation image, not a receipt or FK proof."""
    draft: WorkItemRequestDraft
    request_id: str
    transaction_ref: str
    version: int
    request_digest: str
    worktype_digest: str
    publish_ref: str
    entitlement_ref: str
    issuer_ref: str
    session_ref: str
    authz_revision: str
    policy_epoch: int
    witness_epoch: int


@dataclass(frozen=True)
class WorkItemRoleReadback:
    role: str
    record_id: str
    pin: WorkItemReadbackPin
    event_ref: str | None = None
    dispatchable: bool = False


def _valid_workitem_pin(pin: object) -> bool:
    return (type(pin) is WorkItemReadbackPin
            and inspect_workitem_request(pin.draft).structural_match
            and all(token(v) for v in (pin.request_id, pin.transaction_ref,
                                       pin.publish_ref, pin.entitlement_ref, pin.issuer_ref,
                                       pin.session_ref, pin.authz_revision))
            and uint(pin.version) and pin.version == 1
            and digest_ok(pin.request_digest) and digest_ok(pin.worktype_digest)
            and uint(pin.policy_epoch) and uint(pin.witness_epoch))


def inspect_workitem_readback(draft: WorkItemRequestDraft,
                              expected: WorkItemReadbackPin | None,
                              observed: WorkItemReadbackPin | None,
                              rows: tuple[WorkItemRoleReadback, ...], *,
                              outcome_unknown: bool) -> ReadbackReview:
    """Compare a synthetic creation image and six proposed role observations.

    Both pins are review inputs, never authenticated Project, WorkTypeVersion,
    HUMAN permission or independently verified COMMIT evidence. No digest is
    generated, no ID allocated, no retry or read permission granted. An exact
    match is still HOLD and returns no request identity or durable receipt.
    """
    if type(outcome_unknown) is not bool or outcome_unknown:
        return ReadbackReview('WORKITEM_UNKNOWN_RECONCILIATION_HOLD')
    if not inspect_workitem_request(draft).structural_match:
        return ReadbackReview('WORKITEM_DRAFT_HOLD')
    if not _valid_workitem_pin(expected) or not _valid_workitem_pin(observed):
        return ReadbackReview('WORKITEM_READBACK_REFERENCE_HOLD')
    if expected.draft != draft or observed != expected:
        return ReadbackReview('WORKITEM_READBACK_PIN_MISMATCH_HOLD')
    if type(rows) is not tuple or len(rows) > len(BASE_ROLES):
        return ReadbackReview('WORKITEM_ROLE_SET_HOLD')
    seen, record_ids, event_refs = set(), set(), {}
    for row in rows:
        if (type(row) is not WorkItemRoleReadback or type(row.role) is not str
                or row.role not in BASE_ROLES or not token(row.record_id)
                or row.dispatchable is not False):
            return ReadbackReview('WORKITEM_ROLE_ENVELOPE_HOLD')
        if row.role in seen or row.record_id in record_ids:
            return ReadbackReview('WORKITEM_DUPLICATE_ROLE_HOLD')
        if not _valid_workitem_pin(row.pin) or row.pin != expected:
            return ReadbackReview('WORKITEM_ROLE_PIN_MISMATCH_HOLD')
        if row.role == 'HEAD' and row.record_id != expected.request_id:
            return ReadbackReview('WORKITEM_HEAD_REFERENCE_HOLD')
        if row.role in ('EVENT', 'OUTBOX'):
            if not token(row.event_ref):
                return ReadbackReview('WORKITEM_EVENT_REFERENCE_HOLD')
            event_refs[row.role] = row.event_ref
        elif row.event_ref is not None:
            return ReadbackReview('WORKITEM_EVENT_REFERENCE_HOLD')
        seen.add(row.role)
        record_ids.add(row.record_id)
    if seen != BASE_ROLES:
        return ReadbackReview('WORKITEM_ROLE_SET_HOLD')
    if event_refs['EVENT'] != event_refs['OUTBOX']:
        return ReadbackReview('WORKITEM_EVENT_OUTBOX_LINK_HOLD')
    return ReadbackReview('D0_WORKITEM_READBACK_MATCH_AUTHORITY_UNPROVEN', True)
