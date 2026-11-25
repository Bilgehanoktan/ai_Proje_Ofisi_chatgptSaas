"""Read-only policy snapshot comparison; not a trusted root or grant issuer."""
from dataclasses import dataclass, asdict
from .model import ReviewScope, digest, scope_digest, valid_scope
from .planner import ReviewPlan, valid_plan
from .identity_registry import RegistrySnapshot, inspect_registry
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok

@dataclass(frozen=True)
class PolicySnapshot:
    scope_sha256: str
    plan_sha256: str
    registry_sha256: str
    revision: int
    issuer: str
    custody: str
    policy_epoch: int
    witness_epoch: int
    not_before: int
    expires: int
    revoked: bool


def policy_digest(p: PolicySnapshot) -> str:
    return digest({'profile': 'trusted-policy.v0-D0', 'policy': asdict(p)})


def inspect_policy(p: PolicySnapshot, reference: PolicySnapshot, expected: str,
                   registry: RegistrySnapshot, registry_reference: RegistrySnapshot,
                   scope: ReviewScope, plan: ReviewPlan, now: int,
                   policy_epoch: int, witness_epoch: int, revoked: bool | None) -> str:
    if (type(p) is not PolicySnapshot or type(reference) is not PolicySnapshot
            or not valid_scope(scope) or not valid_plan(plan, scope) or not digest_ok(expected)
            or not all(uint(v) for v in (p.revision, p.policy_epoch, p.witness_epoch, p.not_before,
                                         p.expires, now, policy_epoch, witness_epoch))
            or p.revision == 0 or not token(p.issuer) or not token(p.custody)
            or type(p.revoked) is not bool or p.revoked or revoked is not False):
        return 'POLICY_INVALID_OR_REVOKED'
    if (p != reference or policy_digest(p) != expected or p.scope_sha256 != scope_digest(scope)
            or p.plan_sha256 != plan.plan_sha256 or not p.not_before <= now < p.expires
            or (p.policy_epoch, p.witness_epoch) != (policy_epoch, witness_epoch)
            or (policy_epoch, witness_epoch) != (scope.policy_epoch, scope.witness_epoch)):
        return 'POLICY_PIN_TIME_EPOCH_MISMATCH'
    if not inspect_registry(registry, registry_reference, p.registry_sha256, scope):
        return 'REGISTRY_PIN_HOLD'
    if (registry.roster != plan.roster or p.issuer != registry.issuer or p.custody != registry.issuer_custody):
        return 'POLICY_REGISTRY_SOD_HOLD'
    return 'D0_POLICY_MATCH_ONLY'
