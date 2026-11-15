"""Bind a run transition to an immutable T1 request; no runtime grant."""
import hashlib
import json
from dataclasses import asdict
from app.core.agent_runtime.lifecycle import EDGES, RunState, RunObservation, uint
from app.core.transaction.review import LogicalIntent, Operation, valid_intent

def transition_digest(run, target):
    body = {"scope": asdict(run.scope), "from": run.state.value,
            "to": target.value, "version": run.version, "attempt": run.attempt}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def commit_transition(coordinator, run, target, intent):
    if not isinstance(run, RunObservation) or not isinstance(target, RunState) or not valid_intent(intent):
        raise ValueError("TRANSITION_INVALID")
    # Admission, terminal, and human approval transitions require separate authority.
    if target not in (RunState.PLANNING, RunState.RUNNING, RunState.VERIFYING):
        raise PermissionError("SPECIAL_TRANSITION_HOLD")
    if run.state == RunState.WAITING_APPROVAL:
        raise PermissionError("APPROVAL_HOLD")
    if (target not in EDGES.get(run.state, ()) or not uint(run.version)
            or not uint(run.attempt) or intent.scope != run.scope
            or intent.expected_version != run.version
            or intent.operation != Operation.STATE_MUTATION
            or intent.request_digest != transition_digest(run, target)):
        raise ValueError("TRANSITION_BINDING_MISMATCH")
    # Mapping must independently validate persisted state and digest preimage.
    return coordinator.commit(intent)
