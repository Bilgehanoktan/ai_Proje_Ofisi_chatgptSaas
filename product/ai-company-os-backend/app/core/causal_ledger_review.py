"""D15 synthetic audit chain review. Not the existing UI event ledger or a writer."""
from dataclasses import dataclass, asdict
import hashlib
import json
from .runtime_preview import Scope, valid_scope, token, uint
from .t1_review import digest_ok

GENESIS = '0' * 64


@dataclass(frozen=True)
class CausalObservation:
    scope: Scope
    stream_id: str
    event_id: str
    sequence: int
    correlation_id: str
    causation_id: str | None
    transaction_ref: str
    request_digest: str
    previous_digest: str
    policy_epoch: int
    witness_epoch: int
    event_digest: str


@dataclass(frozen=True)
class LedgerReview:
    reason: str
    structural_match: bool = False
    observed_count: int = 0
    authoritative: bool = False
    persistent: bool = False
    dispatch_allowed: bool = False


def event_digest(e: CausalObservation) -> str:
    body = asdict(e); body.pop('event_digest')
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def inspect_chain(events: tuple[CausalObservation, ...], scope: Scope, stream_id: str,
                  policy_epoch: int, witness_epoch: int) -> LedgerReview:
    """Full synthetic chain from genesis; no snapshot/compaction or committed-time authority."""
    if not isinstance(events, tuple) or not 1 <= len(events) <= 1000 or not valid_scope(scope) or not token(stream_id) or not uint(policy_epoch) or not uint(witness_epoch):
        return LedgerReview('CHAIN_ENVELOPE_INVALID')
    previous, seen, correlations = GENESIS, set(), {}
    for idx, e in enumerate(events, 1):
        if (not isinstance(e, CausalObservation) or e.scope != scope or e.stream_id != stream_id
                or not all(token(v) for v in (e.event_id, e.correlation_id, e.transaction_ref))
                or not uint(e.sequence) or e.sequence != idx or not uint(e.policy_epoch) or not uint(e.witness_epoch)
                or (e.policy_epoch, e.witness_epoch) != (policy_epoch, witness_epoch)
                or not all(digest_ok(v) for v in (e.request_digest, e.previous_digest, e.event_digest))):
            return LedgerReview('EVENT_SCOPE_SEQUENCE_EPOCH_INVALID', observed_count=idx-1)
        if e.event_id in seen or e.previous_digest != previous:
            return LedgerReview('EVENT_ID_OR_CHAIN_CONFLICT', observed_count=idx-1)
        if e.causation_id is not None and (not token(e.causation_id) or e.causation_id not in seen or correlations[e.causation_id] != e.correlation_id):
            return LedgerReview('CAUSATION_OR_CORRELATION_INVALID', observed_count=idx-1)
        if e.causation_id is None and idx != 1:
            return LedgerReview('CAUSAL_PARENT_MISSING', observed_count=idx-1)
        if event_digest(e) != e.event_digest:
            return LedgerReview('EVENT_DIGEST_MISMATCH', observed_count=idx-1)
        seen.add(e.event_id); correlations[e.event_id] = e.correlation_id; previous = e.event_digest
    return LedgerReview('D0_CHAIN_MATCH_NO_COMMIT_PROOF', True, len(events))
