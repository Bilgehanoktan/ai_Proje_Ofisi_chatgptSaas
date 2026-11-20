"""D0 routing decision evidence: content identity, not authorization or storage."""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import Scope, token, uint, valid_scope
from app.core.transaction.review import digest_ok
from .capability_resolver import CapabilityQuery
from .cost_estimator import valid_currency
from .profile_registry import catalog_digest
from .registry import valid_set
from .router import RouteCandidate, RoutePolicy, inspect_route, metrics_digest, policy_digest


@dataclass(frozen=True)
class RoutingDecisionRecord:
    query: CapabilityQuery
    policy: RoutePolicy
    policy_pin: str
    reason: str
    candidates: tuple[RouteCandidate, ...]
    excluded: tuple[tuple[str, str], ...]
    decision: str = field(default="HOLD", init=False)
    selected_model: None = field(default=None, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)


def _valid_query(q):
    return (type(q) is CapabilityQuery and type(q.scope) is Scope and valid_scope(q.scope)
            and type(q.requested) is tuple and valid_set(q.requested) and bool(q.requested)
            and all(type(x) is str and token(x) for x in (*q.requested, q.data_class, q.region, q.complexity_class))
            and uint(q.input_tokens) and uint(q.output_tokens) and q.output_tokens > 0)


def routing_decision_digest(record):
    """Structural content hash only. Full replay is required to check provenance."""
    if (type(record) is not RoutingDecisionRecord or not _valid_query(record.query)
            or type(record.policy) is not RoutePolicy or type(record.policy.scope) is not Scope
            or record.policy.scope != record.query.scope
            or not digest_ok(record.policy_pin) or policy_digest(record.policy) != record.policy_pin
            or record.decision != "HOLD" or record.selected_model is not None
            or any(v is not False for v in (record.provider_call_allowed, record.spend_allowed, record.dispatch_allowed))
            or type(record.candidates) is not tuple or type(record.excluded) is not tuple
            or len(record.candidates) + len(record.excluded) > 128):
        raise ValueError("ROUTING_RECORD_INVALID")
    candidates = []
    for c in record.candidates:
        if (type(c) is not RouteCandidate or not digest_ok(c.profile_digest)
                or c.profile_digest not in record.policy.allowed or not uint(c.estimated_minor)
                or c.estimated_minor > record.policy.max_cost_minor or not valid_currency(c.currency)
                or c.currency != record.policy.currency or not uint(c.latency_upper_ms)
                or not 0 < c.latency_upper_ms <= record.policy.max_latency_ms):
            raise ValueError("ROUTING_CANDIDATE_INVALID")
        candidates.append(c.profile_digest)
    excluded = []
    for pair in record.excluded:
        if (type(pair) is not tuple or len(pair) != 2 or not digest_ok(pair[0])
                or type(pair[1]) is not str or not token(pair[1])):
            raise ValueError("ROUTING_EXCLUSION_INVALID")
        excluded.append(pair[0])
    keys = candidates + excluded
    if (len(keys) != len(set(keys)) or candidates != sorted(candidates)
            or record.excluded != tuple(sorted(record.excluded))
            or record.reason not in ("D0_SCREENED_CANDIDATES_ONLY", "NO_ROUTE_CANDIDATE_HOLD", "NO_ELIGIBLE_PROFILE_HOLD")
            or bool(candidates) != (record.reason == "D0_SCREENED_CANDIDATES_ONLY")):
        raise ValueError("ROUTING_OUTCOME_INVALID")
    return sha256(json.dumps({"version":"D0_ROUTING_DECISION_V1","record":asdict(record)},
        sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()


def make_routing_decision(query, profiles, registry, policy, expected_policy_pin, metrics,
                          current_policy_epoch, current_witness_epoch):
    """Replay existing router with exact supplied references; invalid pins are not records."""
    if (not _valid_query(query) or type(policy) is not RoutePolicy or type(policy.scope) is not Scope
            or query.scope != policy.scope or policy_digest(policy) != expected_policy_pin
            or not uint(current_policy_epoch) or not uint(current_witness_epoch)
            or (current_policy_epoch,current_witness_epoch) != (policy.policy_epoch,policy.witness_epoch)
            or catalog_digest(profiles,registry,query.scope) != policy.catalog_pin
            or metrics_digest(metrics) != policy.metrics_pin):
        raise ValueError("ROUTING_REFERENCES_HOLD")
    result = inspect_route(query, profiles, registry, policy, expected_policy_pin, metrics,
                           current_policy_epoch, current_witness_epoch)
    record = RoutingDecisionRecord(query,policy,expected_policy_pin,result.reason,result.candidates,result.excluded)
    routing_decision_digest(record)
    if len(record.candidates) + len(record.excluded) != len(profiles):
        raise ValueError("ROUTING_CATALOG_COVERAGE_HOLD")
    return record


def verify_routing_decision(record, expected_record_pin, profiles, registry, metrics,
                            current_policy_epoch, current_witness_epoch):
    """Exact replay of pinned D0 references; no trusted clock, signature or grant."""
    try:
        if not digest_ok(expected_record_pin) or routing_decision_digest(record) != expected_record_pin:
            return False
        replay = make_routing_decision(record.query,profiles,registry,record.policy,record.policy_pin,
                                       metrics,current_policy_epoch,current_witness_epoch)
        return record == replay
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        return False
