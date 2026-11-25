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


def validate_transition(run, target, intent):
    if (not isinstance(run, RunObservation) or not isinstance(run.state, RunState)
            or not isinstance(target, RunState) or not valid_intent(intent)):
        raise ValueError("TRANSITION_INVALID")
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


def commit_transition(coordinator, run, target, intent):
    validate_transition(run, target, intent)
    # No generic-commit fallback: the transaction must check locked pre/postimage.
    return coordinator.commit_transition(intent, run, target)
