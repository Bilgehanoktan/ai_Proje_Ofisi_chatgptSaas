"""D30-05A: disabled, immutable D0 model profile metadata; no execution authority."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import Scope, token, uint, valid_scope
from app.core.transaction.review import digest_ok
from .registry import AdapterPin, exact_pin, valid_set
from .provider_contract import ProviderKind

@dataclass(frozen=True)
class ModelProfile:
    adapter: AdapterPin
    provider: ProviderKind
    model_id: str
    model_revision: str
    context_limit: int
    output_limit: int
    data_classes: tuple[str, ...]
    regions: tuple[str, ...]
    complexity_classes: tuple[str, ...]
    cost_profile_ref: str
    latency_profile_ref: str

def valid_profile(p, registry):
    return (type(p) is ModelProfile and type(p.adapter) is AdapterPin
            and exact_pin(p.adapter, registry) and not p.adapter.effect_ceiling
            and type(p.provider) is ProviderKind
            and all(token(v) for v in (p.model_id, p.model_revision,
                    p.cost_profile_ref, p.latency_profile_ref))
            and uint(p.context_limit) and uint(p.output_limit)
            and 0 < p.output_limit <= p.context_limit
            and all(valid_set(v) and bool(v) for v in
                    (p.data_classes, p.regions, p.complexity_classes)))

def profile_digest(p, registry):
    if not valid_profile(p, registry):
        raise ValueError("MODEL_PROFILE_INVALID")
    body = {"version":"D0_MODEL_PROFILE_V1","profile":asdict(p)}
    return sha256(json.dumps(body,sort_keys=True,separators=(",",":"),
                             ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()

def catalog_digest(profiles, registry, scope):
    if (not valid_scope(scope) or type(profiles) is not tuple
            or not 0 < len(profiles) <= 128
            or not all(valid_profile(p,registry) and p.adapter.scope == scope for p in profiles)):
        raise ValueError("MODEL_PROFILE_CATALOG_INVALID")
    keys = [(p.provider,p.model_id,p.model_revision) for p in profiles]
    adapters = [(p.adapter.adapter_id,p.adapter.revision) for p in profiles]
    if len(set(keys)) != len(keys) or len(set(adapters)) != len(adapters):
        raise ValueError("MODEL_PROFILE_DUPLICATE")
    body = {"version":"D0_MODEL_CATALOG_V1","scope":asdict(scope),
            "profiles":sorted(profile_digest(p,registry) for p in profiles)}
    return sha256(json.dumps(body,sort_keys=True,separators=(",",":"),
                             ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()
