"""0215 D0 read-only signed claim observation, NOT an effect gate or trust root.
The expected challenge, authority public key pin, head and clock must be acquired
outside ALL restored stores. Local fixtures cannot establish that independence.
A matching unclaimed observation never permits a new claim or retry.
"""
from contextlib import closing
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import sqlite3
from .intent_authority import D0IntentAuthority, RootPin, _digest, _path


@dataclass(frozen=True)
class ClaimObservation:
    scope_sha: str
    binding: str
    tx: str
    request_digest: str
    root_seq: int
    root_sha: str


@dataclass(frozen=True)
class ExternalClaimObservation:
    challenge: str
    root: RootPin
    root_seq: int
    scope_sha: str
    issued_tick: int
    expires_tick: int
    claim: ClaimObservation | None


@dataclass(frozen=True)
class ClaimReview:
    reason: str
    signature_match: bool = False
    local_match: bool = False
    external_consumed: bool | None = None
    decision: str = field(default='HOLD',init=False)
    independent_verified: bool = field(default=False,init=False)
    retry_allowed: bool = field(default=False,init=False)
    dispatch_allowed: bool = field(default=False,init=False)
    release_allowed: bool = field(default=False,init=False)


def _uint(value): return type(value) is int and 0 <= value < 2**63


def _valid_claim(c):
    return (type(c) is ClaimObservation and all(_digest(v) for v in (c.scope_sha,c.binding,c.request_digest,c.root_sha))
            and type(c.tx) is str and 0 < len(c.tx) <= 512 and _uint(c.root_seq) and c.root_seq>0)


def observation_bytes(o):
    if type(o) is not ExternalClaimObservation or type(o.root) is not RootPin:
        raise ValueError('EXTERNAL_CLAIM_SHAPE_HOLD')
    o.root.validate()
    if (not _digest(o.challenge) or not _digest(o.scope_sha) or not _uint(o.root_seq) or not o.root_seq
            or not _uint(o.issued_tick) or not _uint(o.expires_tick) or not 0 < o.expires_tick-o.issued_tick <= 60
            or (o.claim is not None and (not _valid_claim(o.claim) or o.claim.scope_sha!=o.scope_sha
                or o.claim.root_seq>o.root_seq or (o.claim.root_seq==o.root_seq and o.claim.root_sha!=o.root.record_sha)))):
        raise ValueError('EXTERNAL_CLAIM_SHAPE_HOLD')
    return json.dumps(['aicos-d0-external-claim-observation-v1',asdict(o)],sort_keys=True,
        separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')


def _local(path,scope):
    """One read-only SQLite snapshot. Read claim and corresponding root, no mutation."""
    with closing(sqlite3.connect(_path(path).as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
        db.execute('PRAGMA trusted_schema=OFF');db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
        seq,root=D0IntentAuthority._head(db)
        row=db.execute('SELECT scope_sha,binding,tx,request_digest,root_seq,root_sha FROM claims WHERE scope_sha=?',(scope,)).fetchone()
        claim=ClaimObservation(*row) if row else None
        if claim is not None:
            if not _valid_claim(claim) or claim.root_seq>seq:
                raise ValueError('LOCAL_CLAIM_SHAPE_HOLD')
            if db.execute('SELECT record_sha FROM roots WHERE seq=?',(claim.root_seq,)).fetchone()!=(claim.root_sha,):
                raise ValueError('LOCAL_CLAIM_ROOT_HOLD')
        return seq,root,claim


def review_external_claim(path,observation,signature,public_key,*,expected_key_sha,
                          expected_challenge,expected_root,expected_root_seq,scope_sha,now_tick):
    """Check exact signed head/scope/challenge and compare with local consumed row.
    No write to any authority, no grant on absence, and no claim that external
    publication cannot race a future effect. Only diagnostic comparison.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        return ClaimReview('EXTERNAL_CRYPTO_HOLD')
    try:
        body=observation_bytes(observation)
        if (type(public_key) is not bytes or len(public_key)!=32 or not _digest(expected_key_sha)
            or sha256(public_key).hexdigest()!=expected_key_sha or type(signature) is not bytes or len(signature)!=64
            or not _digest(expected_challenge) or observation.challenge!=expected_challenge
            or not _digest(scope_sha) or observation.scope_sha!=scope_sha or type(expected_root) is not RootPin
            or not _uint(expected_root_seq) or observation.root_seq!=expected_root_seq or observation.root!=expected_root
            or not _uint(now_tick) or not observation.issued_tick<=now_tick<observation.expires_tick):
            return ClaimReview('EXTERNAL_PIN_OR_FRESHNESS_HOLD')
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature,body)
    except (ValueError,TypeError,AttributeError,OverflowError,InvalidSignature):
        return ClaimReview('EXTERNAL_SIGNATURE_OR_SHAPE_HOLD')
    consumed=observation.claim is not None
    try:
        match=_local(path,scope_sha)==(observation.root_seq,observation.root,observation.claim)
    except (OSError,sqlite3.Error,ValueError,TypeError,AttributeError,OverflowError):
        return ClaimReview('LOCAL_READ_HOLD',True,False,consumed)
    if not match:
        return ClaimReview('LOCAL_DIVERGENCE_HOLD',True,False,consumed)
    return ClaimReview('EXTERNAL_CONSUMED_HOLD' if consumed else 'UNCLAIMED_OBSERVATION_HOLD',True,True,consumed)
