"""R02/D15/D21: read-only classification. Never dispatch, reconcile, or persist."""
from dataclasses import dataclass
from enum import Enum
import re
from app.core.agent_runtime.lifecycle import Scope, valid_scope, token, uint, LeaseObservation, ClockSample, inspect_lease


class Phase(str, Enum):
    PRE_COMMIT = 'PRE_COMMIT'
    COMMITTED = 'COMMITTED'
    CLAIMED = 'CLAIMED'
    SEND_INTENT_RECORDED = 'SEND_INTENT_RECORDED'
    ACK_LOST = 'ACK_LOST'
    ACK_UNCOMMITTED = 'ACK_UNCOMMITTED'
    OUTCOME_UNKNOWN = 'OUTCOME_UNKNOWN'
    OUTCOME_RECORDED = 'OUTCOME_RECORDED'


@dataclass(frozen=True)
class OutboxObservation:
    scope: Scope
    effect_key: str
    request_digest: str
    event_id: str
    outbox_id: str
    commit_ref: str | None
    phase: Phase
    claim_generation: int
    claim_owner: str | None
    lease_id: str | None
    fence: int
    policy_epoch: int
    witness_epoch: int
    send_intent_ref: str | None = None
    provider_correlation: str | None = None
    reconciliation_ref: str | None = None


@dataclass(frozen=True)
class OutboxReview:
    classification: str
    reason: str
    effect_allowed: bool = False
    retry_allowed: bool = False
    reconciled: bool = False
    decision: str = 'HOLD'


def valid_outbox(o: object) -> bool:
    return (isinstance(o, OutboxObservation) and valid_scope(o.scope)
            and all(token(v) for v in (o.effect_key, o.event_id, o.outbox_id))
            and isinstance(o.request_digest, str) and re.fullmatch(r'[0-9a-f]{64}', o.request_digest) is not None
            and isinstance(o.phase, Phase)
            and all(uint(v) for v in (o.claim_generation, o.fence, o.policy_epoch, o.witness_epoch))
            and all(v is None or token(v) for v in (o.commit_ref, o.claim_owner, o.lease_id,
                    o.send_intent_ref, o.provider_correlation, o.reconciliation_ref)))


def inspect_outbox(sample: OutboxObservation, expected: OutboxObservation | None,
                   lease: LeaseObservation | None, lease_reference: LeaseObservation | None,
                   clock: ClockSample | None) -> OutboxReview:
    # Any observed send marker or uncertain post-send phase is conservative UNKNOWN.
    if not valid_outbox(sample):
        return OutboxReview('UNKNOWN_HOLD', 'OUTBOX_ENVELOPE_INVALID')
    uncertain = (sample.send_intent_ref is not None or sample.provider_correlation is not None
                 or sample.reconciliation_ref is not None or sample.phase in {
                    Phase.SEND_INTENT_RECORDED, Phase.ACK_LOST, Phase.ACK_UNCOMMITTED,
                    Phase.OUTCOME_UNKNOWN, Phase.OUTCOME_RECORDED})
    if uncertain:
        return OutboxReview('UNKNOWN_HOLD', 'NO_BLIND_RETRY_INDEPENDENT_READBACK_REQUIRED')
    if not valid_outbox(expected) or sample != expected:
        return OutboxReview('UNKNOWN_HOLD', 'OUTBOX_REFERENCE_MISMATCH')
    if sample.phase == Phase.PRE_COMMIT:
        return OutboxReview('LOCAL_HOLD', 'T1_COMMIT_UNPROVEN')
    if not sample.commit_ref:
        return OutboxReview('UNKNOWN_HOLD', 'T1_COMMIT_UNPROVEN')
    if sample.phase == Phase.COMMITTED:
        return OutboxReview('LOCAL_HOLD', 'CLAIM_AND_LIVE_PEP_REQUIRED')
    if sample.phase != Phase.CLAIMED or sample.claim_generation == 0 or not sample.claim_owner:
        return OutboxReview('UNKNOWN_HOLD', 'CLAIM_INVALID')
    if (not isinstance(lease, LeaseObservation) or lease.scope != sample.scope
            or sample.claim_owner != lease.scope.principal_id or sample.lease_id != lease.lease_id
            or (sample.fence, sample.policy_epoch, sample.witness_epoch) != (lease.fence, lease.policy_epoch, lease.witness_epoch)):
        return OutboxReview('UNKNOWN_HOLD', 'CLAIM_LEASE_BINDING_MISMATCH')
    check = inspect_lease(lease, lease_reference, clock)
    if check.freshness != 'FRESH':
        return OutboxReview('UNKNOWN_HOLD', check.reason, decision=check.decision)
    return OutboxReview('LOCAL_HOLD', 'ERR_F3_EXTERNAL_WRITE_FORBIDDEN', decision='DENY')


@dataclass(frozen=True)
class CommitPortResult:
    reason: str = 'T1_ATOMICITY_NOT_PROVEN'
    committed: bool = False
    event_id: str | None = None
    outbox_id: str | None = None


class DisabledRuntimeCommitPort:
    """Intentional negative adapter; not the existing T1 port, never writes."""
    def propose_commit(self, observation: OutboxObservation) -> CommitPortResult:
        return CommitPortResult()
