"""D30-05A D0 capability filtering, not model selection or authorization."""
from dataclasses import dataclass, field
from app.core.agent_runtime.lifecycle import Scope, token, uint, valid_scope
from app.core.transaction.review import digest_ok
from .registry import valid_set
from .profile_registry import catalog_digest, profile_digest

@dataclass(frozen=True)
class CapabilityQuery:
    scope: Scope
    requested: tuple[str, ...]
    data_class: str
    region: str
    complexity_class: str
    input_tokens: int
    output_tokens: int

@dataclass(frozen=True)
class CapabilityReview:
    reason: str
    candidate_digests: tuple[str, ...] = ()
    excluded: tuple[tuple[str, str], ...] = ()
    decision: str = field(default="HOLD", init=False)
    selected_model: None = field(default=None, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)

def inspect_capabilities(query, profiles, registry, expected_catalog_digest, allowed_profile_digests):
    """Supplied pins/allowlist are D0 references, never authenticated policy.
    Cost, latency, ranking and budget proof remain separate mandatory gates.
    """
    if (type(query) is not CapabilityQuery or not valid_scope(query.scope)
            or not valid_set(query.requested) or not query.requested
            or not all(token(v) for v in (query.data_class, query.region, query.complexity_class))
            or not uint(query.input_tokens) or not uint(query.output_tokens)
            or query.output_tokens == 0):
        return CapabilityReview("CAPABILITY_QUERY_HOLD")
    if (not digest_ok(expected_catalog_digest) or type(allowed_profile_digests) is not tuple
            or len(allowed_profile_digests) > 128
            or not all(digest_ok(v) for v in allowed_profile_digests)
            or len(set(allowed_profile_digests)) != len(allowed_profile_digests)):
        return CapabilityReview("CAPABILITY_POLICY_REFERENCE_HOLD")
    try:
        if catalog_digest(profiles,registry,query.scope) != expected_catalog_digest:
            return CapabilityReview("MODEL_CATALOG_PIN_HOLD")
        pinned = {profile_digest(p,registry):p for p in profiles}
        if not set(allowed_profile_digests) <= set(pinned):
            return CapabilityReview("ALLOWLIST_CATALOG_MISMATCH_HOLD")
        candidates, excluded = [], []
        for key,p in sorted(pinned.items()):
            if key not in allowed_profile_digests:
                reason = "NOT_ALLOWLISTED"
            elif query.data_class not in p.data_classes or query.region not in p.regions:
                reason = "DATA_REGION_MISMATCH"
            elif query.complexity_class not in p.complexity_classes:
                reason = "COMPLEXITY_MISMATCH"
            elif not set(query.requested) <= set(p.adapter.capabilities):
                reason = "CAPABILITY_MISMATCH"
            elif (query.output_tokens > p.output_limit
                    or query.input_tokens + query.output_tokens > p.context_limit):
                reason = "TOKEN_LIMIT_MISMATCH"
            else:
                candidates.append(key)
                continue
            excluded.append((key,reason))
        return CapabilityReview("D0_CANDIDATES_ONLY" if candidates else "NO_ELIGIBLE_PROFILE_HOLD",
                                tuple(candidates),tuple(excluded))
    except (TypeError, ValueError, AttributeError, OverflowError, RecursionError):
        return CapabilityReview("MODEL_CATALOG_INVALID_HOLD")
