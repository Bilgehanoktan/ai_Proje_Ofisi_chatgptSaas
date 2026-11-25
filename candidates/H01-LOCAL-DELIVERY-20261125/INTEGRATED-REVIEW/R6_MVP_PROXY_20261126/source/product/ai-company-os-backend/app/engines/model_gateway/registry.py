"""D08/D21: exact synthetic model pins. No SDK, credentials or I/O."""
from dataclasses import dataclass
from ...core.runtime_preview import Scope, valid_scope, token
from ...core.t1_review import digest_ok


def valid_set(values: object) -> bool:
    return (type(values) is tuple and len(values) <= 128
            and all(type(v) is str and token(v) for v in values) and len(set(values)) == len(values))


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
    # Validate plain value records before any equality, membership or hashing.
    return (type(pin) is AdapterPin and type(pin.scope) is Scope
            and all(type(v) is str for v in (
                pin.scope.tenant_id, pin.scope.company_id, pin.scope.environment_id,
                pin.scope.plan_revision, pin.scope.task_id, pin.scope.run_id,
                pin.scope.agent_instance_id, pin.scope.principal_id))
            and valid_scope(pin.scope)
            and type(pin.adapter_id) is str and token(pin.adapter_id)
            and type(pin.revision) is str and token(pin.revision)
            and type(pin.adapter_digest) is str and digest_ok(pin.adapter_digest) and valid_set(pin.capabilities)
            and valid_set(pin.effect_ceiling) and pin.enabled is False)


def exact_pin(pin: AdapterPin, registry: tuple[AdapterPin, ...]) -> bool:
    if not valid_pin(pin) or type(registry) is not tuple or len(registry) > 128:
        return False
    if not all(valid_pin(p) for p in registry):
        return False
    keys = [(p.scope, p.adapter_id, p.revision) for p in registry]
    return len(set(keys)) == len(keys) and pin in registry
