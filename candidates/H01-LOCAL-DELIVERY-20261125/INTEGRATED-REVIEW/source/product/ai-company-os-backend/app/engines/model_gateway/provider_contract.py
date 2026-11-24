"""D0 typed provider review. No adapter execution, credentials, SDK, network or spend."""
from dataclasses import dataclass, field
from enum import Enum
from app.core.agent_runtime.lifecycle import Scope, valid_scope, uint
from app.core.transaction.review import digest_ok
from .registry import AdapterPin, exact_pin, valid_set
from .fallback import inspect_fallback


class ProviderKind(str, Enum):
    SAMPLE = 'SAMPLE'
    OPENAI = 'OPENAI'
    ANTHROPIC = 'ANTHROPIC'
    GOOGLE = 'GOOGLE'
    OLLAMA = 'OLLAMA'


@dataclass(frozen=True)
class ProviderRequest:
    scope: Scope
    provider: ProviderKind
    input_digest: str
    requested: tuple[str, ...]
    effects: tuple[str, ...]
    max_output_tokens: int


@dataclass(frozen=True)
class ProviderReview:
    reason: str
    structural_match: bool = False
    decision: str = field(default='DENY', init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    selected_model: None = field(default=None, init=False)
    actual_tokens: None = field(default=None, init=False)
    actual_cost_minor: None = field(default=None, init=False)


def inspect_provider_request(request: ProviderRequest, primary: AdapterPin,
                             alternate: AdapterPin, registry: tuple[AdapterPin, ...]) -> ProviderReview:
    if (not isinstance(request, ProviderRequest) or not valid_scope(request.scope)
            or not isinstance(request.provider, ProviderKind) or not digest_ok(request.input_digest)
            or not valid_set(request.requested) or not valid_set(request.effects)
            or not uint(request.max_output_tokens) or not 1 <= request.max_output_tokens <= 32768):
        return ProviderReview('PROVIDER_REQUEST_INVALID')
    if not exact_pin(primary, registry) or not exact_pin(alternate, registry):
        return ProviderReview('ADAPTER_PIN_INVALID')
    if request.scope != primary.scope or request.scope != alternate.scope:
        return ProviderReview('PROVIDER_SCOPE_MISMATCH')
    if request.effects or primary.effect_ceiling or alternate.effect_ceiling:
        return ProviderReview('PROVIDER_EFFECT_HOLD')
    if primary == alternate:
        return ProviderReview('PROVIDER_FALLBACK_ALIAS_HOLD')
    review = inspect_fallback(primary, alternate, registry, request.requested, request.effects)
    if not review.structural_match or review.provider_call_allowed or review.decision != 'DENY':
        return ProviderReview(review.reason)
    if request.provider is not ProviderKind.SAMPLE:
        # There is deliberately no binding from caller-supplied provider names to executable adapters.
        return ProviderReview('PROVIDER_EGRESS_HOLD')
    if (primary.adapter_id, alternate.adapter_id) != ('demo-model', 'demo-fallback'):
        return ProviderReview('SAMPLE_ADAPTER_ONLY')
    return ProviderReview('D0_PROVIDER_REFERENCE_MATCH_ONLY', True)
