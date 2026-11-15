"""Local fixed-output adapter; no prompt, SDK, credentials, provider or tool call."""
from dataclasses import dataclass
from .registry import AdapterPin, exact_pin
from .fallback import inspect_fallback


@dataclass(frozen=True)
class SampleOutput:
    reason: str
    output: str | None = None
    provider_called: bool = False
    spend_allowed: bool = False
    dispatch_allowed: bool = False


def sample_model(primary: AdapterPin, alternate: AdapterPin, registry: tuple[AdapterPin, ...]) -> SampleOutput:
    if not exact_pin(primary, registry) or not exact_pin(alternate, registry):
        return SampleOutput('ADAPTER_PIN_INVALID')
    if (primary.adapter_id, alternate.adapter_id) != ('demo-model', 'demo-fallback'):
        return SampleOutput('SAMPLE_ADAPTER_ONLY')
    review = inspect_fallback(primary, alternate, registry, ('demo-tool',), ())
    if not review.structural_match or review.provider_call_allowed or review.decision != 'DENY':
        return SampleOutput('SAMPLE_ADAPTER_HOLD')
    return SampleOutput('FIXED_SAMPLE_ONLY', 'Synthetic adapter review output; not a model response.')
