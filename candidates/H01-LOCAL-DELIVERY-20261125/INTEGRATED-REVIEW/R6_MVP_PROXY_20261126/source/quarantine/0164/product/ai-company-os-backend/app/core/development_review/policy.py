"""Pure diagnostic evaluator. No ALLOW branch, write API, grant issuer or gateway connection."""
from dataclasses import dataclass, field
from .model import ReviewScope, PrincipalPin, FilePin, valid_scope, valid_file, valid_principal, scope_digest
from .planner import ReviewPlan, valid_plan
from app.core.agent_runtime.lifecycle import uint

ACTIONS = {'orchestrator': 'PLAN_REVIEW', 'research': 'REQUIREMENT_REVIEW',
           'engineer': 'CANDIDATE_PROPOSAL', 'qa': 'QUALITY_REVIEW', 'security': 'SECURITY_REVIEW',
           'independent-verifier': 'EVIDENCE_REVIEW', 'policy-review': 'GATE_REVIEW'}


@dataclass(frozen=True)
class ReviewRequest:
    scope_sha256: str
    plan_sha256: str
    task_id: str
    actor: PrincipalPin
    action: str
    files: tuple[FilePin, ...]
    policy_epoch: int
    witness_epoch: int


@dataclass(frozen=True)
class PolicyReview:
    reason: str
    structural_match: bool = False
    decision: str = 'HOLD'
    source_write_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)


def inspect_request(r: ReviewRequest, scope: ReviewScope, reference: ReviewScope,
                    plan: ReviewPlan, revoked: bool | None,
                    current_policy_epoch: int, current_witness_epoch: int) -> PolicyReview:
    def deny(reason: str) -> PolicyReview:
        return PolicyReview(reason, decision='DENY')
    if not valid_scope(scope) or not valid_scope(reference) or scope != reference:
        return deny('SCOPE_REFERENCE_MISMATCH')
    if revoked is not False:
        return deny('REVOCATION_UNKNOWN_OR_REVOKED')
    if not all(uint(v) for v in (current_policy_epoch, current_witness_epoch)) or (
            current_policy_epoch, current_witness_epoch) != (scope.policy_epoch, scope.witness_epoch):
        return deny('EPOCH_STALE_OR_INVALID')
    if not valid_plan(plan, scope) or type(r) is not ReviewRequest or not valid_principal(r.actor):
        return deny('PLAN_OR_REQUEST_INVALID')
    if (r.scope_sha256, r.plan_sha256) != (scope_digest(scope), plan.plan_sha256):
        return deny('REQUEST_DIGEST_MISMATCH')
    if not all(uint(v) for v in (r.policy_epoch, r.witness_epoch)) or (
            r.policy_epoch, r.witness_epoch) != (scope.policy_epoch, scope.witness_epoch):
        return deny('REQUEST_EPOCH_MISMATCH')
    task = next((t for t in plan.tasks if t.id == r.task_id), None)
    if task is None or task.role != r.actor.role or r.actor not in plan.roster:
        return deny('TASK_ACTOR_MISMATCH')
    if type(r.action) is not str or r.action != ACTIONS[task.role]:
        return deny('ACTION_FORBIDDEN')
    if type(r.files) is not tuple or not all(valid_file(f) for f in r.files) or r.files != scope.files:
        return deny('FILE_PIN_MISMATCH')
    return PolicyReview('D0_SCOPE_MATCH_NO_AUTHORITY', structural_match=True)


@dataclass(frozen=True)
class FileReadback:
    path: str
    before: bytes | None
    after: bytes


def inspect_patch_bytes(scope: ReviewScope, reference: ReviewScope,
                        parent_manifest: bytes, files: tuple[FileReadback, ...]) -> PolicyReview:
    """No filesystem access. Caller bytes are observations, not a trusted checkout."""
    from hashlib import sha256
    limit = 1024 * 1024
    if not valid_scope(scope) or not valid_scope(reference) or scope != reference:
        return PolicyReview('SCOPE_REFERENCE_MISMATCH', decision='DENY')
    if (type(parent_manifest) is not bytes or len(parent_manifest) > 8 * limit
            or sha256(parent_manifest).hexdigest() != scope.parent_manifest_sha256):
        return PolicyReview('PARENT_MANIFEST_BYTES_MISMATCH', decision='DENY')
    if type(files) is not tuple or len(files) != len(scope.files):
        return PolicyReview('PATCH_SET_MISMATCH', decision='DENY')
    for f, pin in zip(files, scope.files):
        if (type(f) is not FileReadback or f.path != pin.path or type(f.after) is not bytes
                or len(f.after) > limit or sha256(f.after).hexdigest() != pin.new_sha256):
            return PolicyReview('PATCH_AFTER_BYTES_MISMATCH', decision='DENY')
        if pin.old_sha256 is None:
            if f.before is not None:
                return PolicyReview('PATCH_ADD_COLLISION', decision='DENY')
        elif (type(f.before) is not bytes or len(f.before) > limit
                or sha256(f.before).hexdigest() != pin.old_sha256):
            return PolicyReview('PATCH_BEFORE_BYTES_MISMATCH', decision='DENY')
    return PolicyReview('D0_BYTES_MATCH_NO_CHECKOUT_AUTHORITY', structural_match=True)
