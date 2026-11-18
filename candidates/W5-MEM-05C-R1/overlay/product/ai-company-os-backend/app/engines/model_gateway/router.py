"""D30-05A D0 policy-aware screening; no ranking, winner or executable route."""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import Scope, valid_scope, token, uint
from app.core.transaction.review import digest_ok
from .provider_contract import ProviderKind
from .profile_registry import profile_digest
from .capability_resolver import inspect_capabilities, CapabilityQuery
from .cost_estimator import CostProfile, cost_digest, estimate_cost, valid_currency

@dataclass(frozen=True)
class RouteMetric:
    profile_digest: str
    cost: CostProfile
    latency_ref: str
    latency_upper_ms: int

@dataclass(frozen=True)
class RoutePolicy:
    scope: Scope
    revision: str
    catalog_pin: str
    allowed: tuple[str,...]
    metrics_pin: str
    currency: str
    max_cost_minor: int
    max_latency_ms: int
    policy_epoch: int
    witness_epoch: int

@dataclass(frozen=True)
class RouteCandidate:
    profile_digest: str
    estimated_minor: int
    currency: str
    latency_upper_ms: int

@dataclass(frozen=True)
class RoutingReview:
    reason: str
    candidates: tuple[RouteCandidate,...] = ()
    excluded: tuple[tuple[str,str],...] = ()
    decision: str = field(default="HOLD",init=False)
    selected_model: None = field(default=None,init=False)
    provider_call_allowed: bool = field(default=False,init=False)
    spend_allowed: bool = field(default=False,init=False)
    dispatch_allowed: bool = field(default=False,init=False)

def _digest(version,body):
    return sha256(json.dumps({"version":version,"body":body},sort_keys=True,
        separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()

def metrics_digest(metrics):
    if type(metrics) is not tuple or len(metrics)>128:
        raise ValueError("ROUTE_METRICS_INVALID")
    rows={}
    for m in metrics:
        if (type(m) is not RouteMetric or not digest_ok(m.profile_digest)
                or not token(m.latency_ref) or not uint(m.latency_upper_ms)
                or m.latency_upper_ms==0 or m.profile_digest in rows
                or cost_digest(m.cost) is None or m.cost.profile_digest!=m.profile_digest):
            raise ValueError("ROUTE_METRIC_INVALID")
        rows[m.profile_digest]=asdict(m)
    return _digest("D0_ROUTE_METRICS_V1",[rows[k] for k in sorted(rows)])

def policy_digest(p):
    if (type(p) is not RoutePolicy or not valid_scope(p.scope) or not token(p.revision)
            or not digest_ok(p.catalog_pin) or not digest_ok(p.metrics_pin)
            or type(p.allowed) is not tuple or len(p.allowed)>128
            or not all(digest_ok(x) for x in p.allowed) or len(set(p.allowed))!=len(p.allowed)
            or not valid_currency(p.currency)
            or not all(uint(v) for v in (p.max_cost_minor,p.max_latency_ms,p.policy_epoch,p.witness_epoch))
            or p.max_latency_ms==0):
        raise ValueError("ROUTE_POLICY_INVALID")
    return _digest("D0_ROUTE_POLICY_V1",asdict(p))

def inspect_route(query,profiles,registry,policy,expected_policy_pin,metrics,
                  current_policy_epoch,current_witness_epoch):
    """All inputs are caller-pinned D0 references, not authoritative observations.
    Limits screen candidates; sorted digests are not a score or preference.
    Quota, risk, revocation, reservation and independent authority remain open.
    """
    try:
        if not digest_ok(expected_policy_pin) or policy_digest(policy)!=expected_policy_pin:
            return RoutingReview("ROUTE_POLICY_PIN_HOLD")
        if (type(query) is not CapabilityQuery or query.scope!=policy.scope
                or not uint(current_policy_epoch) or not uint(current_witness_epoch)
                or (current_policy_epoch,current_witness_epoch)!=(policy.policy_epoch,policy.witness_epoch)):
            return RoutingReview("ROUTE_SCOPE_EPOCH_HOLD")
        if metrics_digest(metrics)!=policy.metrics_pin:
            return RoutingReview("ROUTE_METRIC_PIN_HOLD")
        cap=inspect_capabilities(query,profiles,registry,policy.catalog_pin,policy.allowed)
        if cap.reason!="D0_CANDIDATES_ONLY":
            return RoutingReview(cap.reason,excluded=cap.excluded)
        indexed={profile_digest(p,registry):p for p in profiles}
        observed={m.profile_digest:m for m in metrics}
        if not set(observed)<=set(indexed):
            return RoutingReview("ROUTE_METRIC_CATALOG_HOLD")
        eligible=[]; excluded=list(cap.excluded)
        for key in cap.candidate_digests:
            p=indexed[key]; m=observed.get(key)
            if m is None:
                reason="METRIC_MISSING"
            elif p.provider is not ProviderKind.SAMPLE:
                reason="PROVIDER_EGRESS_HOLD"
            elif m.latency_ref!=p.latency_profile_ref:
                reason="LATENCY_REFERENCE_MISMATCH"
            else:
                cost=estimate_cost(m.cost,cost_digest(m.cost),key,p.cost_profile_ref,
                                   policy.currency,query.input_tokens,query.output_tokens)
                if cost.estimated_minor is None:
                    reason=cost.reason
                elif cost.estimated_minor>policy.max_cost_minor:
                    reason="COST_LIMIT_HOLD"
                elif m.latency_upper_ms>policy.max_latency_ms:
                    reason="LATENCY_LIMIT_HOLD"
                else:
                    eligible.append(RouteCandidate(key,cost.estimated_minor,policy.currency,m.latency_upper_ms))
                    continue
            excluded.append((key,reason))
        return RoutingReview("D0_SCREENED_CANDIDATES_ONLY" if eligible else "NO_ROUTE_CANDIDATE_HOLD",
                             tuple(eligible),tuple(sorted(excluded)))
    except (ValueError,TypeError,AttributeError,OverflowError,RecursionError):
        return RoutingReview("ROUTE_REFERENCE_INVALID_HOLD")
