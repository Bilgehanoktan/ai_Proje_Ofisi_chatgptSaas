"""0217 D0 signed consume receipt protocol. Never an execution grant.
The signer/store/clock in this fixture are NOT independently operated.
"""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from .effect_fence_reference import D0EffectFenceReference, Head, Intent, digest, positive


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


def token(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value) is not None


@dataclass(frozen=True)
class Scope:
    tenant: str
    company: str
    environment: str
    project: str
    task: str
    run: str
    effect: str

    def fingerprint(self):
        if not all(token(v) for v in asdict(self).values()):
            raise ValueError('SCOPE_HOLD')
        return sha256(canonical(['aicos-d0-effect-scope-v1', asdict(self)])).hexdigest()


@dataclass(frozen=True)
class ConsumeRequest:
    scope: Scope
    head: Head
    nonce: str
    binding_sha: str
    transaction_ref: str
    request_sha: str
    issued_tick: int
    expires_tick: int

    def intent(self):
        if type(self.scope) is not Scope or type(self.head) is not Head or not digest(self.nonce):
            raise ValueError('REQUEST_SHAPE_HOLD')
        self.head.validate()
        if not (positive(self.issued_tick) and positive(self.expires_tick) and 0 < self.expires_tick-self.issued_tick <= 60):
            raise ValueError('REQUEST_WINDOW_HOLD')
        intent = Intent(self.scope.fingerprint(), self.binding_sha, self.transaction_ref, self.request_sha)
        intent.validate()
        return intent

    def body(self):
        self.intent()
        return canonical(['aicos-d0-consumed-observation-v1', asdict(self)])


@dataclass(frozen=True)
class SignedObservation:
    request: ConsumeRequest
    signature: bytes


@dataclass(frozen=True)
class Review:
    reason: str
    signature_match: bool = False
    decision: str = field(default='HOLD', init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)
    independent_verified: bool = field(default=False, init=False)


def issue_fixture(store, signer, request, now_tick):
    """Consume before signing; a crash/signing failure leaves UNKNOWN, never retry."""
    if type(store) is not D0EffectFenceReference or not isinstance(signer, Ed25519PrivateKey) or type(request) is not ConsumeRequest:
        raise ValueError('ISSUER_HOLD')
    body = request.body()
    if not positive(now_tick) or not request.issued_tick <= now_tick < request.expires_tick:
        raise ValueError('ISSUER_WINDOW_HOLD')
    store.consume_synthetic(request.head, request.intent())
    return SignedObservation(request, signer.sign(body))


def review_observation(observation, expected, public_key, *, expected_key_sha, current_head, now_tick):
    """Expected request/head/key/time must originate outside the restored boundary.
    A signature authenticates an observation, not an effect or independent custody.
    """
    try:
        if type(observation) is not SignedObservation or type(expected) is not ConsumeRequest or type(current_head) is not Head:
            return Review('SHAPE_HOLD')
        body = expected.body()
        current_head.validate()
        if (type(observation.request) is not ConsumeRequest or observation.request.body() != body
                or expected.head != current_head or not positive(now_tick)
                or not expected.issued_tick <= now_tick < expected.expires_tick
                or type(public_key) is not bytes or len(public_key) != 32 or not digest(expected_key_sha)
                or sha256(public_key).hexdigest() != expected_key_sha
                or type(observation.signature) is not bytes or len(observation.signature) != 64):
            return Review('PIN_OR_FRESHNESS_HOLD')
        Ed25519PublicKey.from_public_bytes(public_key).verify(observation.signature, body)
        return Review('SIGNED_CONSUMED_OBSERVATION_HOLD', True)
    except (ValueError, TypeError, AttributeError, OverflowError, InvalidSignature):
        return Review('SIGNATURE_OR_SHAPE_HOLD')
