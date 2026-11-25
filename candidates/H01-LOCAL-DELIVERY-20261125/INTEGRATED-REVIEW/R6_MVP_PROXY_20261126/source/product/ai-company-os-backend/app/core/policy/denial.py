"""D0 deny-only boundary. Not production PEP/PDP, grant or witness validation."""
from dataclasses import dataclass

@dataclass(frozen=True)
class EffectRequest:
    tenant_id: str
    environment_id: str
    action: str
    grant_ref: str | None = None
    policy_epoch: int | None = None
    witness_epoch: int | None = None
    lease_ref: str | None = None
    budget_ref: str | None = None

@dataclass(frozen=True)
class Denial:
    decision: str
    reasons: tuple[str, ...]
    dispatch_allowed: bool = False
    provider_called: bool = False
    release_ready: bool = False

# No allow branch, even if caller supplies plausible or forged refs.
def deny_effect(request: EffectRequest) -> Denial:
    reasons = ["OFFICIAL_IMPLEMENTATION_HOLD", "INDEPENDENT_ACCEPTANCE_MISSING",
               "F0_F3_NOT_ACCEPTED", "WA_UNPROVEN", "NO_EXTERNAL_EFFECT"]
    if request.tenant_id != "synthetic-tenant" or request.environment_id != "A0_SAMPLE_ONLY":
        reasons.append("SCOPE_MISMATCH")
    if request.grant_ref is None:
        reasons.append("GRANT_MISSING")
    if request.policy_epoch is None or request.witness_epoch is None:
        reasons.append("EPOCH_UNKNOWN")
    if request.lease_ref is None or request.budget_ref is None:
        reasons.append("ADMISSION_EVIDENCE_MISSING")
    return Denial("DENY", tuple(reasons))
