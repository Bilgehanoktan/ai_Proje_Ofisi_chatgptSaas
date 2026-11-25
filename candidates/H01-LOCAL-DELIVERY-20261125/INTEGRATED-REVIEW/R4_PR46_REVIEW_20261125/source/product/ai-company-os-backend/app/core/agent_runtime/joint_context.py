"""0208 D0 joint memory/model inspection; never a grant or effect boundary."""
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json

from app.core.agent_runtime.lifecycle import valid_scope
from app.core.t1_review import digest_ok
from app.engines.memory_engine.snapshot_store import (
    SnapshotPin, _pin_ok, inspect_stored_memory_input,
)
from app.engines.model_gateway.runtime_binding import (
    InvocationEnvelope, invocation_digest, inspect_invocation,
)


@dataclass(frozen=True)
class JointContext:
    memory_pin: SnapshotPin
    invocation: InvocationEnvelope


@dataclass(frozen=True)
class JointReview:
    reason: str
    structural_match: bool = False
    decision: str = field(default='DENY', init=False)
    retrieval_allowed: bool = field(default=False, init=False)
    release_allowed: bool = field(default=False, init=False)
    provider_call_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    spend_allowed: bool = field(default=False, init=False)


def joint_context_digest(context, registry):
    """Bind the exact memory generation/graph and full model envelope/registry.

    The model input must equal the approved source span, not arbitrary prompt text.
    A digest is a synthetic reference, not proof of trusted acquisition.
    """
    if (not isinstance(context, JointContext) or not _pin_ok(context.memory_pin)
            or not isinstance(context.invocation, InvocationEnvelope)):
        raise ValueError('JOINT_CONTEXT_SHAPE_HOLD')
    model_pin = invocation_digest(context.invocation, registry)
    body = dict(profile='D0_JOINT_CONTEXT_V1', memory=asdict(context.memory_pin),
                model_digest=model_pin)
    return sha256(json.dumps(body, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


def inspect_joint_context(context, registry, expected_digest, path, current_run,
                          current_lease, clock, raw, expected_history=None):
    """Fail closed on drift; two observations bracket the model inspection.

    The second read detects an intervening committed revocation. This is not
    atomic with a future provider effect; an independent effect gate is required.
    If supplied by the witnessed path, committed history pins are checked in
    both memory read transactions. No bytes, receipt, model or authority are returned.
    """
    if not digest_ok(expected_digest) or type(raw) is not bytes or len(raw) > 1024*1024:
        return JointReview('JOINT_CONTEXT_SHAPE_HOLD')
    try:
        if joint_context_digest(context, registry) != expected_digest:
            return JointReview('JOINT_CONTEXT_DIGEST_HOLD')
    except (ValueError, TypeError, AttributeError, OverflowError, RecursionError):
        return JointReview('JOINT_CONTEXT_SHAPE_HOLD')
    envelope = context.invocation
    if not valid_scope(getattr(current_run, 'scope', None)):
        return JointReview('JOINT_RUN_SCOPE_HOLD')
    first = inspect_stored_memory_input(path, context.memory_pin, current_run, current_lease, envelope.lease, clock, raw, expected_history)
    if first != 'D0_MEMORY_INPUT_MATCH_ONLY':
        return JointReview(first)
    model = inspect_invocation(envelope, registry, invocation_digest(envelope, registry),
                               current_run, current_lease, clock, raw)
    if not model.structural_match or model.reason != 'D0_MODEL_INVOCATION_MATCH_ONLY':
        return JointReview(model.reason)
    second = inspect_stored_memory_input(path, context.memory_pin, current_run, current_lease, envelope.lease, clock, raw, expected_history)
    if second != 'D0_MEMORY_INPUT_MATCH_ONLY':
        return JointReview(second)
    return JointReview('D0_JOINT_CONTEXT_MATCH_ONLY', True)
