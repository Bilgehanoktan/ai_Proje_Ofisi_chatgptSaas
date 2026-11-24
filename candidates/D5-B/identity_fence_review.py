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
from identity_binding import Binding, Review, digest
from intent_identity import review_bound_intent


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
