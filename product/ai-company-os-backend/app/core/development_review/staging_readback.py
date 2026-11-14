"""Typed D0 staging readback. Caller snapshots do not prove database or witness custody."""
from dataclasses import dataclass, asdict, field
from hashlib import sha256
import json
from .model import ReviewScope, digest, scope_digest, valid_scope
from .planner import ReviewPlan
from .evidence import Observation, inspect_evidence
from .trust_boundary import TrustPin, valid_trust, trust_digest
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok

GENESIS = '0' * 64


@dataclass(frozen=True)
class StagedRow:
    plan_sha: str
    seq: int
    evidence_id: str
    previous_sha: str
    entry_sha: str
    body: str


@dataclass(frozen=True)
class ReplayPin:
    evidence_id: str
    scope_sha: str
    evidence_sha: str


@dataclass(frozen=True)
class BatchPin:
    trust_sha: str
    scope_sha: str
    plan_sha: str
    policy_sha: str
    schema_sha: str
    witness_epoch: int
    previous_sequence: int
    previous_head: str
    sequence: int
    row_head: str
    replay_sha: str


@dataclass(frozen=True)
class StagingReview:
    reason: str
    structural_match: bool = False
    batch_sha: str | None = None
    authoritative: bool = field(default=False, init=False)
    write_allowed: bool = field(default=False, init=False)
    decision: str = 'HOLD'


def expected_rows(scope: ReviewScope, plan: ReviewPlan, observations: tuple[Observation, ...]) -> tuple[StagedRow, ...]:
    stream, previous, rows = scope_digest(scope), GENESIS, []
    for seq, o in enumerate(observations, 1):
        body = json.dumps(asdict(o), sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
        entry = digest({'scope': stream, 'plan': plan.plan_sha256, 'seq': seq, 'previous': previous, 'body': body})
        rows.append(StagedRow(plan.plan_sha256, seq, o.evidence_id, previous, entry, body))
        previous = entry
    return tuple(rows)


def batch_digest(pin: BatchPin) -> str:
    return digest({'profile': 'staging-batch.v0-D0', 'pin': asdict(pin)})


def inspect_batch(scope: ReviewScope, reference: ReviewScope, plan: ReviewPlan,
                  observations: tuple[Observation, ...], reference_observations: tuple[Observation, ...],
                  outputs: tuple[bytes, ...], trust: TrustPin, pin: BatchPin, expected_pin: BatchPin,
                  rows: tuple[StagedRow, ...], schema_bytes: bytes, schema_expected_sha: str,
                  replay: tuple[ReplayPin, ...], replay_reference: tuple[ReplayPin, ...],
                  policy_epoch: int, witness_epoch: int, revoked: bool | None) -> StagingReview:
    e = inspect_evidence(scope, reference, plan, observations, reference_observations,
                         policy_epoch, witness_epoch, revoked, outputs)
    if not e.structural_match:
        return StagingReview(e.reason)
    if not valid_trust(trust) or type(pin) is not BatchPin or type(expected_pin) is not BatchPin or pin != expected_pin:
        return StagingReview('BATCH_REFERENCE_HOLD')
    if (not all(digest_ok(x) for x in (pin.trust_sha, pin.scope_sha, pin.plan_sha, pin.policy_sha,
            pin.schema_sha, pin.previous_head, pin.row_head, pin.replay_sha))
            or not all(uint(x) for x in (pin.witness_epoch, pin.previous_sequence, pin.sequence))):
        return StagingReview('BATCH_PIN_INVALID')
    if (pin.trust_sha, pin.scope_sha, pin.plan_sha, pin.policy_sha, pin.witness_epoch) != (
            trust_digest(trust), scope_digest(scope), plan.plan_sha256, trust.policy_sha, witness_epoch):
        return StagingReview('BATCH_SCOPE_EPOCH_HOLD')
    if (trust.scope_sha, trust.plan_sha, trust.policy_epoch, trust.witness_epoch) != (
            pin.scope_sha, pin.plan_sha, policy_epoch, witness_epoch):
        return StagingReview('BATCH_TRUST_SCOPE_HOLD')
    if (pin.previous_sequence != trust.witness_sequence or pin.previous_head != trust.witness_head
            or pin.sequence != pin.previous_sequence + 1):
        return StagingReview('BATCH_RESTORE_OR_SEQUENCE_HOLD')
    if (type(schema_bytes) is not bytes or len(schema_bytes) > 65536 or not digest_ok(schema_expected_sha)
            or sha256(schema_bytes).hexdigest() != schema_expected_sha or pin.schema_sha != schema_expected_sha):
        return StagingReview('BATCH_SCHEMA_HOLD')
    expected = expected_rows(scope, plan, observations)
    if (type(rows) is not tuple or len(rows) != len(expected)
            or any(type(r) is not StagedRow or type(r.seq) is not int for r in rows)
            or rows != expected or pin.row_head != expected[-1].entry_sha):
        return StagingReview('BATCH_ROW_READBACK_HOLD')
    wanted = tuple(sorted((ReplayPin(o.evidence_id, pin.scope_sha, o.evidence_sha256)
                           for o in observations), key=lambda r: r.evidence_id))
    if (type(replay) is not tuple or type(replay_reference) is not tuple or len(replay) != len(wanted)
            or len(replay_reference) != len(wanted) or any(type(r) is not ReplayPin for r in replay + replay_reference)
            or replay != replay_reference or replay != wanted
            or digest([asdict(r) for r in wanted]) != pin.replay_sha):
        return StagingReview('BATCH_REPLAY_INDEX_HOLD')
    return StagingReview('BATCH_MATCH_CUSTODY_CAS_UNPROVEN', True, batch_digest(pin))
