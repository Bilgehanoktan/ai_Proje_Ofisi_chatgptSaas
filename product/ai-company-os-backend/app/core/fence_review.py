"""R02 D0 idempotency classification. No storage, retry, or reservation creation."""
from dataclasses import dataclass
from enum import Enum
from .runtime_preview import Scope, valid_scope, token, uint
from .t1_review import digest_ok


class FencePhase(str, Enum):
    LOCAL_ONLY = 'LOCAL_ONLY'
    SEND_INTENT = 'SEND_INTENT'
    UNKNOWN = 'UNKNOWN'
    OUTCOME_OBSERVED = 'OUTCOME_OBSERVED'


@dataclass(frozen=True)
class FenceObservation:
    scope: Scope
    effect_key: str
    idempotency_key: str
    request_digest: str
    witness_epoch: int
    phase: FencePhase


@dataclass(frozen=True)
class FenceReview:
    classification: str
    reason: str
    retry_allowed: bool = False
    effect_allowed: bool = False
    new_fence_created: bool = False


def valid_fence(f: object) -> bool:
    return (isinstance(f, FenceObservation) and valid_scope(f.scope) and token(f.effect_key)
            and token(f.idempotency_key) and digest_ok(f.request_digest) and uint(f.witness_epoch)
            and isinstance(f.phase, FencePhase))


def inspect_fence(request: FenceObservation, stored: FenceObservation | None, current_witness: int) -> FenceReview:
    if not valid_fence(request) or not uint(current_witness):
        return FenceReview('UNKNOWN_HOLD', 'FENCE_ENVELOPE_INVALID')
    if request.phase != FencePhase.LOCAL_ONLY:
        return FenceReview('UNKNOWN_HOLD', 'NO_BLIND_RETRY')
    if request.witness_epoch != current_witness:
        return FenceReview('FENCED', 'ERR_WA_EPOCH_STALE')
    if stored is None:
        return FenceReview('LOCAL_HOLD', 'AUTHORITATIVE_LOOKUP_AND_T1_REQUIRED')
    if not valid_fence(stored):
        return FenceReview('UNKNOWN_HOLD', 'STORED_FENCE_INVALID')
    if stored.witness_epoch != current_witness:
        return FenceReview('FENCED', 'ERR_WA_EPOCH_STALE')
    if stored.scope != request.scope or stored.effect_key != request.effect_key or stored.idempotency_key != request.idempotency_key:
        return FenceReview('CONFLICT_HOLD', 'FENCE_IDENTITY_MISMATCH')
    if stored.request_digest != request.request_digest:
        return FenceReview('CONFLICT_HOLD', 'IDEMPOTENCY_DIGEST_CONFLICT')
    if stored.phase != FencePhase.LOCAL_ONLY:
        return FenceReview('UNKNOWN_HOLD', 'NO_BLIND_RETRY')
    return FenceReview('LOCAL_HOLD', 'SAME_REQUEST_OBSERVED_NO_REDISPATCH')
