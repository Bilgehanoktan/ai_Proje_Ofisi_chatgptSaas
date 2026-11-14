"""D12/D14 D0 Policy/ToolGateway diagnostic intersection. Never ALLOW or call a tool."""
from dataclasses import dataclass
from .runtime_preview import (Scope, valid_scope, token, uint, LeaseObservation, ClockSample,
                              valid_lease, inspect_lease)
from .t1_review import digest_ok
from .witness_review import WitnessSample, inspect_witness
from .security import EffectRequest, deny_effect


@dataclass(frozen=True)
class EffectScope:
    scope: Scope
    action: str
    tool_id: str
    effect_digest: str
    grant_id: str
    admission_id: str
    lease_id: str
    budget_id: str
    policy_epoch: int
    witness_epoch: int
    fence: int


@dataclass(frozen=True)
class GrantSample:
    scope: Scope
    grant_id: str
    admission_id: str
    lease_id: str
    budget_id: str
    allowed_actions: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    effect_digest: str
    policy_epoch: int
    witness_epoch: int
    fence: int
    expires_tick: int
    revoked: bool


@dataclass(frozen=True)
class GatewayReview:
    reason: str
    structural_match: bool = False
    decision: str = 'DENY'
    dispatch_allowed: bool = False
    provider_called: bool = False
    release_ready: bool = False
    reasons: tuple[str, ...] = ()


def valid_effect(e: object) -> bool:
    return (isinstance(e, EffectScope) and valid_scope(e.scope) and digest_ok(e.effect_digest)
            and all(token(v) for v in (e.action,e.tool_id,e.grant_id,e.admission_id,e.lease_id,e.budget_id))
            and all(uint(v) for v in (e.policy_epoch,e.witness_epoch,e.fence)) and e.fence > 0)


def _tokens(v: object) -> bool:
    return isinstance(v, tuple) and 0 < len(v) <= 128 and all(token(x) for x in v) and len(set(v)) == len(v)


def valid_grant(g: object) -> bool:
    return (isinstance(g, GrantSample) and valid_scope(g.scope) and digest_ok(g.effect_digest)
            and all(token(v) for v in (g.grant_id,g.admission_id,g.lease_id,g.budget_id))
            and _tokens(g.allowed_actions) and _tokens(g.allowed_tools)
            and all(uint(v) for v in (g.policy_epoch,g.witness_epoch,g.fence,g.expires_tick))
            and g.fence > 0 and type(g.revoked) is bool)


def inspect_gateway(e: EffectScope, grant: GrantSample | None, grant_reference: GrantSample | None,
                    lease: LeaseObservation | None, lease_reference: LeaseObservation | None,
                    clock: ClockSample | None, witness: WitnessSample | None,
                    witness_reference: WitnessSample | None, witness_max_age: int) -> GatewayReview:
    if not valid_effect(e):
        return GatewayReview('EFFECT_SCOPE_INVALID')
    denial = deny_effect(EffectRequest(e.scope.tenant_id,e.scope.environment_id,e.action,e.grant_id,
                                      e.policy_epoch,e.witness_epoch,e.lease_id,e.budget_id))
    def reject(reason: str, match: bool = False) -> GatewayReview:
        return GatewayReview(reason, match, reasons=denial.reasons)
    if not valid_grant(grant) or not valid_grant(grant_reference):
        return reject('GRANT_REFERENCE_MISSING')
    if grant != grant_reference:
        return reject('GRANT_REFERENCE_MISMATCH')
    if grant.revoked:
        return reject('GRANT_REVOKED')
    if (grant.scope,grant.grant_id,grant.admission_id,grant.lease_id,grant.budget_id,grant.effect_digest,
            grant.policy_epoch,grant.witness_epoch,grant.fence) != (e.scope,e.grant_id,e.admission_id,
            e.lease_id,e.budget_id,e.effect_digest,e.policy_epoch,e.witness_epoch,e.fence):
        return reject('GRANT_EFFECT_BINDING_MISMATCH')
    if e.action not in grant.allowed_actions or e.tool_id not in grant.allowed_tools:
        return reject('EFFECT_OUTSIDE_GRANT')
    if not valid_lease(lease) or (lease.scope,lease.grant_id,lease.lease_id,lease.policy_epoch,
            lease.witness_epoch,lease.fence) != (e.scope,e.grant_id,e.lease_id,e.policy_epoch,e.witness_epoch,e.fence):
        return reject('GATEWAY_LEASE_BINDING_MISMATCH')
    fresh = inspect_lease(lease,lease_reference,clock)
    if fresh.freshness != 'FRESH':
        return reject(fresh.reason)
    if clock.now_tick >= grant.expires_tick:
        return reject('GRANT_EXPIRED')
    wa = inspect_witness(witness,witness_reference,e.scope,e.witness_epoch,clock.now_tick,witness_max_age)
    if not wa.structural_match:
        return reject(wa.reason)
    return reject('PEP_ISOLATION_NOT_PROVEN', True)


class DisabledToolGateway:
    """No provider, socket, callback, credentials, allow branch or side effect."""
    def dispatch(self, request: EffectScope) -> GatewayReview:
        return GatewayReview('ERR_F3_EXTERNAL_WRITE_FORBIDDEN')
