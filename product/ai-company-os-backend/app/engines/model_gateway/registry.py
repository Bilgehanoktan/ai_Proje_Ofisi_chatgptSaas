"""D08/D21: exact synthetic model pins. No SDK, credentials or I/O."""
from dataclasses import dataclass
from ...core.runtime_preview import Scope, valid_scope, token
from ...core.t1_review import digest_ok


def valid_set(values: object) -> bool:
    return (isinstance(values, tuple) and len(values) <= 128
            and all(token(v) for v in values) and len(set(values)) == len(values))


@dataclass(frozen=True)
class AdapterPin:
    scope: Scope
    adapter_id: str
    revision: str
    adapter_digest: str
    capabilities: tuple[str, ...]
    effect_ceiling: tuple[str, ...]
    enabled: bool = False


def valid_pin(pin: object) -> bool:
    return (isinstance(pin, AdapterPin) and valid_scope(pin.scope)
            and token(pin.adapter_id) and token(pin.revision)
            and digest_ok(pin.adapter_digest) and valid_set(pin.capabilities)
            and valid_set(pin.effect_ceiling) and pin.enabled is False)


def exact_pin(pin: AdapterPin, registry: tuple[AdapterPin, ...]) -> bool:
    if not valid_pin(pin) or not isinstance(registry, tuple) or len(registry) > 128:
        return False
    if not all(valid_pin(p) for p in registry):
        return False
    keys = [(p.scope, p.adapter_id, p.revision) for p in registry]
    return len(set(keys)) == len(keys) and pin in registry
