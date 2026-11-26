"""Review coordination only. No dispatch, storage write, or integration effect."""
from dataclasses import dataclass, field
from .model import ReviewScope
from .planner import ReviewPlan
from .identity_registry import RegistrySnapshot
from .trusted_policy import PolicySnapshot, inspect_policy
from .policy import FileReadback, inspect_patch_bytes
from .evidence import Observation, inspect_evidence

@dataclass(frozen=True)
class CoordinationReview:
    reason: str
    matched_steps: tuple[str, ...] = ()
    decision: str = 'HOLD'
    source_write_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)


def inspect_coordination(scope: ReviewScope, scope_reference: ReviewScope, plan: ReviewPlan,
                         registry: RegistrySnapshot, registry_reference: RegistrySnapshot,
                         policy: PolicySnapshot, policy_reference: PolicySnapshot, policy_sha256: str,
                         now: int, policy_epoch: int, witness_epoch: int, revoked: bool | None,
                         parent_manifest: bytes, files: tuple[FileReadback, ...],
                         observations: tuple[Observation, ...], evidence_reference: tuple[Observation, ...],
                         outputs: tuple[bytes, ...]) -> CoordinationReview:
    p = inspect_policy(policy, policy_reference, policy_sha256, registry, registry_reference,
                       scope, plan, now, policy_epoch, witness_epoch, revoked)
    if p != 'D0_POLICY_MATCH_ONLY':
        return CoordinationReview(p)
    patch = inspect_patch_bytes(scope, scope_reference, parent_manifest, files)
    if not patch.structural_match:
        return CoordinationReview(patch.reason, ('policy',))
    e = inspect_evidence(scope, scope_reference, plan, observations, evidence_reference,
                         policy_epoch, witness_epoch, revoked, outputs)
    if not e.structural_match:
        return CoordinationReview(e.reason, ('policy', 'patch'))
    return CoordinationReview('D0_REVIEW_MATCH_NO_AUTHORITY', ('policy', 'patch', 'evidence'))
