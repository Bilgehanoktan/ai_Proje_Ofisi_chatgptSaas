"""D21: model fallback review cannot widen scope, capability or effects."""
from dataclasses import dataclass
from .registry import AdapterPin, exact_pin, valid_set


@dataclass(frozen=True)
class ModelReview:
    reason: str
    structural_match: bool = False
    decision: str = 'DENY'
    provider_call_allowed: bool = False
    selected_model: str | None = None


def inspect_fallback(primary: AdapterPin, alternate: AdapterPin,
                     registry: tuple[AdapterPin, ...], requested: tuple[str, ...],
                     effects: tuple[str, ...]) -> ModelReview:
    if not exact_pin(primary, registry) or not exact_pin(alternate, registry):
        return ModelReview('ADAPTER_PIN_INVALID')
    if primary.scope != alternate.scope:
        return ModelReview('FALLBACK_SCOPE_MISMATCH')
    if not valid_set(requested) or not valid_set(effects):
        return ModelReview('CAPABILITY_REQUEST_INVALID')
    if set(alternate.effect_ceiling) != set(primary.effect_ceiling):
        return ModelReview('FALLBACK_EFFECT_CEILING_MISMATCH')
    if not set(alternate.capabilities) <= set(primary.capabilities):
        return ModelReview('FALLBACK_CAPABILITY_EXPANSION')
    if not set(requested) <= set(alternate.capabilities) or not set(effects) <= set(primary.effect_ceiling):
        return ModelReview('CAPABILITY_HOLD')
    return ModelReview('D0_REFERENCE_MATCH_ONLY', True)
