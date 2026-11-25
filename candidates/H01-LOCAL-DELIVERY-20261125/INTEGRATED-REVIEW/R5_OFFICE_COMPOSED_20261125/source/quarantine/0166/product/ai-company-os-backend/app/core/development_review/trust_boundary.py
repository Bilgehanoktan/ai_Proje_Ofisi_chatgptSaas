"""D0 trust-envelope inspection. No signature verifier, key retrieval, clock or grant."""
from dataclasses import dataclass, asdict, field
from .model import ReviewScope, digest, scope_digest, valid_scope
from .planner import ReviewPlan, valid_plan
from .identity_registry import RegistrySnapshot, registry_digest
from .trusted_policy import PolicySnapshot, policy_digest, inspect_policy
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok


@dataclass(frozen=True)
class TrustPin:
    scope_sha: str
    plan_sha: str
    registry_sha: str
    policy_sha: str
    issuer: str
    custody: str
    key_id: str
    key_revision: int
    policy_epoch: int
    witness_epoch: int
    witness_sequence: int
    witness_head: str
    observed_tick: int


@dataclass(frozen=True)
class TrustReview:
    reason: str
    structural_match: bool = False
    decision: str = 'HOLD'
    authenticated: bool = field(default=False, init=False)
    grant_allowed: bool = field(default=False, init=False)


def trust_digest(pin: TrustPin) -> str:
    return digest({'profile': 'trust-boundary.v0-D0', 'pin': asdict(pin)})


def valid_trust(pin: object) -> bool:
    return (type(pin) is TrustPin and all(digest_ok(x) for x in (
        pin.scope_sha, pin.plan_sha, pin.registry_sha, pin.policy_sha, pin.witness_head))
        and all(token(x) for x in (pin.issuer, pin.custody, pin.key_id))
        and all(uint(x) for x in (pin.key_revision, pin.policy_epoch, pin.witness_epoch,
            pin.witness_sequence, pin.observed_tick)) and pin.key_revision > 0 and pin.witness_sequence > 0)


def inspect_trust(pin: TrustPin, reference: TrustPin, expected_sha: str,
                  scope: ReviewScope, plan: ReviewPlan, registry: RegistrySnapshot,
                  registry_reference: RegistrySnapshot, policy: PolicySnapshot,
                  policy_reference: PolicySnapshot, now: int, max_age: int,
                  policy_epoch: int, witness_epoch: int, revoked: bool | None) -> TrustReview:
    if (not valid_trust(pin) or not valid_trust(reference) or not digest_ok(expected_sha)
            or not valid_scope(scope) or not valid_plan(plan, scope)
            or not uint(now) or not uint(max_age) or max_age == 0):
        return TrustReview('TRUST_ENVELOPE_HOLD')
    if pin != reference or trust_digest(pin) != expected_sha:
        return TrustReview('TRUST_REFERENCE_HOLD')
    if not pin.observed_tick <= now or now - pin.observed_tick > max_age:
        return TrustReview('TRUST_FRESHNESS_HOLD')
    if (pin.scope_sha, pin.plan_sha, pin.policy_epoch, pin.witness_epoch) != (
            scope_digest(scope), plan.plan_sha256, scope.policy_epoch, scope.witness_epoch):
        return TrustReview('TRUST_SCOPE_EPOCH_HOLD')
    result = inspect_policy(policy, policy_reference, pin.policy_sha, registry,
                            registry_reference, scope, plan, now, policy_epoch, witness_epoch, revoked)
    if result != 'D0_POLICY_MATCH_ONLY':
        return TrustReview(result)
    if (pin.registry_sha != registry_digest(registry) or pin.policy_sha != policy_digest(policy)
            or pin.issuer != policy.issuer or pin.custody != policy.custody
            or pin.key_id in {p.principal_id for p in plan.roster}):
        return TrustReview('TRUST_ISSUER_REGISTRY_HOLD')
    return TrustReview('TRUST_SIGNATURE_CLOCK_CUSTODY_UNPROVEN', True)
