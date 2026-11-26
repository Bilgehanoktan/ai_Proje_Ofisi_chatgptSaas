"""D5-B D0 readback composition; not an authentication or commit boundary.
Call only inside the existing authority fence in a reviewed owner integration.
This module cannot establish that a lock is held and never claims or writes.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from app.core.agent_runtime.lifecycle import uint
from app.core.event_store.company_coordination import Member
from app.core.transaction.intent_authority import RootPin
from app.core.transaction.identity_binding import Binding, Review, digest
from app.core.transaction.intent_identity import review_bound_intent


@dataclass(frozen=True)
class IdentityReadback:
    member: Member
    scope: tuple[str, str, str]
    principal: str
    binding: Binding
    root: RootPin
    tick: int


def _review(intent, sample):
    if type(sample) is not IdentityReadback or type(sample.root) is not RootPin or not uint(sample.tick):
        return Review('D5B_READBACK_SHAPE_HOLD')
    try:
        sample.root.validate()
        return review_bound_intent(intent, sample.member, sample.member, sample.scope,
                                   sample.scope, sample.principal, sample.binding,
                                   sample.binding, sample.tick)
    except Exception:
        return Review('D5B_READBACK_HOLD')


def readback_digest(intent, sample):
    """Pin the initial owner observation; never replace witness or T1 digest."""
    if not _review(intent, sample).structural_match:
        raise ValueError('D5B_REFERENCE_HOLD')
    return sha256(json.dumps(['aicos-d5b-readback-v1', asdict(sample)], sort_keys=True,
                             separators=(',', ':'), ensure_ascii=True,
                             allow_nan=False).encode('ascii')).hexdigest()


def inspect_at_fence(intent, initial, expected_sha, expected_root, read_latest):
    """Internal diagnostic, intended to run within the existing claim/fence.

    read_latest is a reviewed server-owned read port, NOT HTTP or a grant. The
    supplied root and reference must come from independent retained observations.
    No lock proof, trusted reader implementation, or authority is inferred here.
    """
    try:
        if type(expected_root) is not RootPin or not digest(expected_sha):
            return Review('D5B_REFERENCE_HOLD')
        expected_root.validate()
        if readback_digest(intent, initial) != expected_sha or initial.root != expected_root:
            return Review('D5B_REFERENCE_HOLD')
        latest = read_latest()
        result = _review(intent, latest)
        if not result.structural_match:
            return result
        if latest.root != expected_root:
            return Review('D5B_ROOT_DRIFT_HOLD')
        if latest.tick < initial.tick:
            return Review('D5B_CLOCK_REGRESSION_HOLD')
        if latest.principal != initial.principal:
            return Review('D5B_PRINCIPAL_DRIFT_HOLD')
        return review_bound_intent(intent, initial.member, latest.member, initial.scope,
                                   latest.scope, latest.principal, initial.binding,
                                   latest.binding, latest.tick)
    except Exception:
        return Review('D5B_READBACK_UNAVAILABLE_HOLD')


# D5-G4: exact IAM session reference composition. Inspection only.
from contextlib import closing
from dataclasses import field
from app.core.iam_session import D0SessionResolver, SessionObservation, SessionClaimCheck
from app.core.transaction.intent_authority import D0IntentAuthority
from app.core.transaction.identity_binding import Request
from app.core.transaction.intent_identity import derive_request


@dataclass(frozen=True)
class SessionReference:
    request: Request
    observation: SessionObservation
    root: RootPin
    owner_pin: str
    clock_domain: str
    readback_sha: str
    session_sha: str
    decision: str = field(default='HOLD', init=False)
    commit_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)


def session_reference_digest(reference):
    """Separate review pin; never a T1 claim, witness hash or publication version."""
    if type(reference) is not SessionReference:
        raise ValueError('D5G4_REFERENCE_HOLD')
    return sha256(json.dumps(['aicos-d5g4-session-reference-v1',asdict(reference)],
                  sort_keys=True,separators=(',',':'),ensure_ascii=True,
                  allow_nan=False).encode('ascii')).hexdigest()


def _require_resolver(resolver, root, owner_pin, domain):
    if (type(resolver) is not D0SessionResolver or type(resolver._authority) is not D0IntentAuthority
            or type(root) is not RootPin or not digest(owner_pin)
            or type(domain) is not str or resolver._root != root
            or resolver.durable_pin != owner_pin or resolver._domain != domain):
        raise ValueError('D5G4_RESOLVER_HOLD')
    root.validate()
    return resolver._authority


def _sample_session(db, authority, resolver, credential, intent, sample, root, owner_pin, domain):
    if type(sample) is not IdentityReadback or sample.root != root:
        raise ValueError('D5G4_ROOT_HOLD')
    _require_resolver(resolver,root,owner_pin,domain)
    observation = resolver._read_durable(db,credential,sample.scope,persist_clock=False)
    if type(observation) is not SessionObservation:
        raise ValueError('D5G4_SESSION_HOLD')
    request = derive_request(intent,sample.member,sample.scope,observation.principal_id)
    if (sample.principal != observation.principal_id or sample.binding.request != request
            or observation.kind != 'AGENT' or observation.agent_instance_id != request.agent):
        raise ValueError('D5G4_REQUEST_HOLD')
    check = SessionClaimCheck(resolver,credential,observation,request.scope,request.principal,request.agent)
    session_sha = check.inspect(authority,db)
    _require_resolver(resolver,root,owner_pin,domain)
    return SessionReference(request,observation,root,owner_pin,domain,readback_digest(intent,sample),session_sha)


def capture_session_reference(resolver, credential, intent, initial, *, root, owner_pin, domain):
    """Capture exact D0 session and derived request under existing SQLite write lock.

    Owner inputs are not authenticated ORG provenance. No claim is inserted.
    IAM and D4 ticks are not compared across domains. Returns HOLD reference only.
    """
    authority = _require_resolver(resolver,root,owner_pin,domain)
    with closing(authority._db()) as db:
        db.execute('BEGIN IMMEDIATE')
        try:
            return _sample_session(db,authority,resolver,credential,intent,initial,root,owner_pin,domain)
        finally:
            db.execute('ROLLBACK')


def inspect_session_reference(resolver, credential, intent, initial, reference, expected_sha,
                              read_latest, *, root, owner_pin, domain):
    """Re-read under same authority lock, without T1 claim or execution.

    Structural match alone is always HOLD. The current ORG/role read port,
    independent pin custody and strict COMMIT expiry are not provided here.
    """
    try:
        if (type(reference) is not SessionReference or not digest(expected_sha)
                or session_reference_digest(reference) != expected_sha
                or reference.root != root or reference.owner_pin != owner_pin
                or reference.clock_domain != domain or not callable(read_latest)):
            return Review('D5G4_REFERENCE_HOLD')
        authority = _require_resolver(resolver,root,owner_pin,domain)
        with closing(authority._db()) as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                actual_initial = _sample_session(db,authority,resolver,credential,intent,initial,root,owner_pin,domain)
                if actual_initial != reference:
                    return Review('D5G4_SESSION_DRIFT_HOLD')
                latest = read_latest()
                reviewed = inspect_at_fence(intent,initial,reference.readback_sha,root,lambda: latest)
                if not reviewed.structural_match:
                    return reviewed
                actual_latest = _sample_session(db,authority,resolver,credential,intent,latest,root,owner_pin,domain)
                if (actual_latest.request != reference.request
                        or actual_latest.observation != reference.observation
                        or actual_latest.session_sha != reference.session_sha):
                    return Review('D5G4_SESSION_DRIFT_HOLD')
                return Review('D5G4_SESSION_REQUEST_MATCH_ONLY',True,reviewed.binding_sha)
            finally:
                db.execute('ROLLBACK')
    except Exception:
        return Review('D5G4_READBACK_HOLD')
