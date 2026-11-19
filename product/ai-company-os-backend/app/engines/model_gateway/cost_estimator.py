"""D0 bounded token cost estimate; not a quote, reservation or actual charge."""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import token, uint
from app.core.transaction.review import digest_ok

@dataclass(frozen=True)
class CostProfile:
    profile_digest: str
    reference: str
    currency: str
    token_unit: int
    input_minor: int
    output_minor: int
    fixed_minor: int

@dataclass(frozen=True)
class CostEstimate:
    reason: str
    estimated_minor: int | None = None
    currency: str | None = None
    actual_minor: None = field(default=None, init=False)
    reservation_created: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)

def valid_currency(value):
    return type(value) is str and len(value)==3 and value.isascii() and value.isalpha() and value.isupper()

def cost_digest(p):
    if (type(p) is not CostProfile or not digest_ok(p.profile_digest)
            or not token(p.reference) or not valid_currency(p.currency)
            or not all(uint(v) for v in (p.token_unit,p.input_minor,p.output_minor,p.fixed_minor))
            or p.token_unit==0):
        raise ValueError("COST_PROFILE_INVALID")
    return sha256(json.dumps({"version":"D0_COST_V1","profile":asdict(p)},
        sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()

def estimate_cost(p, expected_digest, profile_pin, reference, currency, input_tokens, output_tokens):
    try:
        if not digest_ok(expected_digest) or cost_digest(p)!=expected_digest:
            return CostEstimate("COST_PIN_HOLD")
        if (p.profile_digest,p.reference,p.currency)!=(profile_pin,reference,currency):
            return CostEstimate("COST_BINDING_HOLD")
        if not uint(input_tokens) or not uint(output_tokens) or output_tokens==0:
            return CostEstimate("COST_TOKEN_HOLD")
        # Round each component upward to integer minor units; no float or FX.
        total = ((input_tokens*p.input_minor+p.token_unit-1)//p.token_unit
                 +(output_tokens*p.output_minor+p.token_unit-1)//p.token_unit+p.fixed_minor)
        if not uint(total):
            return CostEstimate("COST_OVERFLOW_HOLD")
        return CostEstimate("D0_ESTIMATE_ONLY",total,p.currency)
    except (TypeError,ValueError,AttributeError,OverflowError,RecursionError):
        return CostEstimate("COST_PROFILE_HOLD")
