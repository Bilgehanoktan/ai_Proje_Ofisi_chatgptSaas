"""Content-pinned, dependency-bound review observations; not signed receipts or persisted audit."""
from dataclasses import dataclass, asdict, field
from hashlib import sha256
from .model import PROFILE, ReviewScope, PrincipalPin, digest, scope_digest, valid_principal, valid_scope
from .planner import ReviewPlan, valid_plan
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok


@dataclass(frozen=True)
class Observation:
    evidence_id: str
    scope_sha256: str
    plan_sha256: str
    task_id: str
    actor: PrincipalPin
    subject_sha256: str
    input_digests: tuple[str, ...]
    output_sha256: str
    policy_epoch: int
    witness_epoch: int
    verdict: str
    evidence_sha256: str


@dataclass(frozen=True)
class EvidenceReview:
    reason: str
    structural_match: bool = False
    observed_tasks: int = 0
    decision: str = 'HOLD'
    authoritative: bool = field(default=False, init=False)
    write_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)


def observation_digest(o: Observation) -> str:
    body = asdict(o)
    body.pop('evidence_sha256')
    return digest({'profile': PROFILE, 'observation': body})


def subject_digest(scope: ReviewScope) -> str:
    if not valid_scope(scope):
        raise ValueError('REVIEW_SCOPE_INVALID')
    return digest({'profile': PROFILE, 'files': [asdict(f) for f in scope.files]})


def valid_observation(o: object) -> bool:
    return (type(o) is Observation and token(o.evidence_id) and token(o.task_id)
            and valid_principal(o.actor) and all(digest_ok(v) for v in (o.scope_sha256, o.plan_sha256,
                o.subject_sha256, o.output_sha256, o.evidence_sha256))
            and type(o.input_digests) is tuple and len(o.input_digests) <= 2
            and all(digest_ok(v) for v in o.input_digests)
            and all(uint(v) for v in (o.policy_epoch, o.witness_epoch))
            and type(o.verdict) is str and o.verdict in ('MATCH', 'REJECT', 'UNKNOWN'))


def inspect_evidence(scope: ReviewScope, reference: ReviewScope, plan: ReviewPlan,
                     observations: tuple[Observation, ...], reference_observations: tuple[Observation, ...],
                     current_policy_epoch: int, current_witness_epoch: int,
                     revoked: bool | None, output_readbacks: tuple[bytes, ...]) -> EvidenceReview:
    if not valid_scope(scope) or not valid_scope(reference) or scope != reference or not valid_plan(plan, scope):
        return EvidenceReview('EVIDENCE_SCOPE_OR_PLAN_HOLD')
    if revoked is not False or not all(uint(v) for v in (current_policy_epoch, current_witness_epoch)) or (
            current_policy_epoch, current_witness_epoch) != (scope.policy_epoch, scope.witness_epoch):
        return EvidenceReview('EVIDENCE_EPOCH_OR_REVOCATION_HOLD')
    if (type(observations) is not tuple or type(reference_observations) is not tuple
            or len(observations) != len(plan.tasks) or len(reference_observations) != len(plan.tasks)
            or not all(valid_observation(o) for o in observations + reference_observations)):
        return EvidenceReview('EVIDENCE_SET_INCOMPLETE_OR_INVALID')
    if (type(output_readbacks) is not tuple or len(output_readbacks) != len(plan.tasks)
            or any(type(b) is not bytes or len(b) > 1024 * 1024 for b in output_readbacks)):
        return EvidenceReview('EVIDENCE_OUTPUT_READBACK_INVALID')
    if observations != reference_observations:
        return EvidenceReview('EVIDENCE_REFERENCE_MISMATCH')
    seen, ids, hashes = {}, set(), set()
    subject = subject_digest(scope)
    roster = {p.role: p for p in plan.roster}
    for o, task, raw in zip(observations, plan.tasks, output_readbacks):
        if (o.task_id != task.id or o.actor != roster[task.role] or o.evidence_id in ids
                or o.evidence_sha256 in hashes or o.scope_sha256 != scope_digest(scope)
                or o.plan_sha256 != plan.plan_sha256 or o.subject_sha256 != subject
                or (o.policy_epoch, o.witness_epoch) != (scope.policy_epoch, scope.witness_epoch)):
            return EvidenceReview('EVIDENCE_BINDING_OR_REPLAY_HOLD', observed_tasks=len(seen))
        if (o.input_digests != tuple(seen[d] for d in task.depends_on)
                or observation_digest(o) != o.evidence_sha256):
            return EvidenceReview('EVIDENCE_CAUSAL_DIGEST_HOLD', observed_tasks=len(seen))
        if sha256(raw).hexdigest() != o.output_sha256:
            return EvidenceReview('EVIDENCE_OUTPUT_BYTES_HOLD', observed_tasks=len(seen))
        if o.verdict != 'MATCH':
            return EvidenceReview('EVIDENCE_REJECT_OR_UNKNOWN_HOLD', observed_tasks=len(seen))
        seen[o.task_id] = o.evidence_sha256
        ids.add(o.evidence_id); hashes.add(o.evidence_sha256)
    return EvidenceReview('D0_CHAIN_MATCH_SIGNATURE_CUSTODY_UNPROVEN', True, len(seen))
