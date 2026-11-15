"""0202-S: D0 signed history readback, not a trust root or execution authority."""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import re
from app.core.event_store.retained_history import review_retained_snapshot

_SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
_FAILURE = 'D0_LOCAL_FAILURE_NO_EFFECT'


def _token(v):
    return type(v) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', v) is not None


def _sha(v):
    return type(v) is str and re.fullmatch(r'[0-9a-f]{64}', v) is not None


def _uint(v):
    return type(v) is int and 0 <= v < 2**63


def _bytes(profile, obj):
    return json.dumps([profile, asdict(obj)], sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


@dataclass(frozen=True)
class TerminalClaim:
    run_id: str
    command_sha: str
    transaction_ref: str
    outcome: str


@dataclass(frozen=True)
class Checkpoint:
    tenant_id: str
    company_id: str
    environment_id: str
    plan_revision: str
    history_sha: str
    issuer: str
    key_id: str
    key_revision: int
    policy_epoch: int
    witness_epoch: int
    sequence: int
    valid_from: int
    valid_until: int
    terminal_claims: tuple[TerminalClaim, ...]


@dataclass(frozen=True)
class ExternalPin:
    """Expected latest values from outside the restored archive; custody unproven here."""
    checkpoint_sha: str
    public_key_sha: str
    issuer: str
    key_id: str
    key_revision: int
    policy_epoch: int
    witness_epoch: int
    sequence: int
    plan_revision: str
    revoked: bool
    excluded_principals: tuple[str, ...]


@dataclass(frozen=True)
class SignedReview:
    reason: str
    signature_match: bool = False
    history: object = None
    atomic_anchor_match: bool = False
    decision: str = field(default='HOLD', init=False)
    independent_verified: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    release_ready: bool = field(default=False, init=False)
    replay_allowed: bool = field(default=False, init=False)


def _valid_claim(c):
    return (type(c) is TerminalClaim and _token(c.run_id) and c.run_id.startswith('demo-')
            and _sha(c.command_sha) and type(c.transaction_ref) is str
            and re.fullmatch(r'd0-tx-[0-9a-f]{64}', c.transaction_ref) is not None
            and type(c.outcome) is str and c.outcome == _FAILURE)


def checkpoint_bytes(c):
    if (type(c) is not Checkpoint or (c.tenant_id,c.company_id,c.environment_id) != _SCOPE
            or type(c.plan_revision) is not str or not c.plan_revision.startswith('sha256:')
            or not _sha(c.plan_revision[7:]) or not _sha(c.history_sha)
            or not all(_token(v) for v in (c.issuer,c.key_id))
            or not all(_uint(v) for v in (c.key_revision,c.policy_epoch,c.witness_epoch,c.sequence,c.valid_from,c.valid_until))
            or min(c.key_revision,c.sequence) == 0 or c.valid_from >= c.valid_until
            or type(c.terminal_claims) is not tuple or len(c.terminal_claims)>100
            or not all(_valid_claim(t) for t in c.terminal_claims)):
        raise ValueError('D0_SIGNED_CHECKPOINT_FORMAT_HOLD')
    ids = tuple(t.run_id for t in c.terminal_claims)
    if ids != tuple(sorted(set(ids))):
        raise ValueError('D0_SIGNED_TERMINAL_SET_HOLD')
    return _bytes('aicos-d0-history-checkpoint-v1',c)


def terminal_bytes(c, claim):
    body = checkpoint_bytes(c)
    if not _valid_claim(claim) or claim not in c.terminal_claims:
        raise ValueError('D0_SIGNED_TERMINAL_SET_HOLD')
    return json.dumps(['aicos-d0-terminal-receipt-v1',sha256(body).hexdigest(),asdict(claim)],
                      sort_keys=True,separators=(',', ':'),ensure_ascii=True,allow_nan=False).encode('ascii')


def verify_checkpoint(c, pin, public_key, signature, terminal_signatures, now):
    """Cryptographic match to a pinned D0 key; no key enrollment, signing or trust issuance."""
    try:
        body = checkpoint_bytes(c)
        if (type(pin) is not ExternalPin or not _sha(pin.checkpoint_sha) or not _sha(pin.public_key_sha)
                or type(pin.revoked) is not bool or pin.revoked or not _uint(now)
                or not all(_uint(v) for v in (pin.key_revision,pin.policy_epoch,pin.witness_epoch,pin.sequence))
                or type(pin.excluded_principals) is not tuple or not 1<=len(pin.excluded_principals)<=100
                or not all(_token(v) for v in pin.excluded_principals)
                or c.issuer in pin.excluded_principals or c.key_id in pin.excluded_principals
                or not c.valid_from <= now < c.valid_until
                or (c.issuer,c.key_id,c.key_revision,c.policy_epoch,c.witness_epoch,c.sequence,c.plan_revision) !=
                   (pin.issuer,pin.key_id,pin.key_revision,pin.policy_epoch,pin.witness_epoch,pin.sequence,pin.plan_revision)
                or sha256(body).hexdigest() != pin.checkpoint_sha
                or type(public_key) is not bytes or len(public_key)!=32
                or sha256(public_key).hexdigest()!=pin.public_key_sha
                or type(signature) is not bytes or len(signature)!=64
                or type(terminal_signatures) is not tuple or len(terminal_signatures)!=len(c.terminal_claims)):
            return SignedReview('D0_SIGNED_PIN_OR_FRESHNESS_HOLD')
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key = Ed25519PublicKey.from_public_bytes(public_key)
        key.verify(signature, body)
        for claim, item in zip(c.terminal_claims,terminal_signatures):
            if (type(item) is not tuple or len(item)!=2 or item[0]!=claim.run_id
                    or type(item[1]) is not bytes or len(item[1])!=64):
                return SignedReview('D0_SIGNED_TERMINAL_SET_HOLD')
            key.verify(item[1],terminal_bytes(c,claim))
        return SignedReview('D0_SIGNATURE_MATCH_CUSTODY_UNPROVEN', True)
    except Exception:
        return SignedReview('D0_SIGNATURE_OR_BACKEND_HOLD')


def review_signed_snapshot(store, connect, plan, revision, pins, checkpoint, external_pin,
                           public_key, signature, terminal_signatures, now, *, anchors=None, require_terminal_anchors=False):
    """Require signed latest pin plus existing exact history; no success or replay permission."""
    if type(require_terminal_anchors) is not bool:
        return SignedReview("D0_ANCHOR_MODE_HOLD")
    check = verify_checkpoint(checkpoint,external_pin,public_key,signature,terminal_signatures,now)
    if not check.signature_match:
        return check
    try:
        if revision != checkpoint.plan_revision or type(pins) is not tuple or len(pins)>100:
            return SignedReview('D0_SIGNED_PLAN_SCOPE_HOLD')
        # The supplied separation roster must cover the actual run principals.
        principals = {p.initial.scope.principal_id for p in pins}
        if not all(_token(v) for v in principals) or not principals.issubset(external_pin.excluded_principals):
            return SignedReview('D0_SIGNED_PRINCIPAL_SET_HOLD')
        refs = tuple((c.run_id,c.command_sha) for c in checkpoint.terminal_claims)
        mode = {"require_terminal_anchors": True} if require_terminal_anchors else {}
        result = review_retained_snapshot(store,connect,plan,revision,pins,checkpoint.history_sha,
                                          anchors=anchors,terminal_refs=refs,**mode)
        expected = tuple((c.run_id,c.command_sha,c.transaction_ref) for c in checkpoint.terminal_claims)
        if not result.reference_match or result.failure_commands != expected or result.history is None or (require_terminal_anchors and result.atomic_anchor_match is not True):
            return SignedReview('D0_SIGNED_READBACK_HOLD')
        return SignedReview('D0_SIGNED_READBACK_MATCH_ONLY',True,result.history,require_terminal_anchors)
    except Exception:
        return SignedReview('D0_SIGNED_READBACK_HOLD')
