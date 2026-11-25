"""Deterministic dependency readiness; no worker dispatch or authority."""
from app.core.orchestrator.engine import parse_plan
from app.core.agent_runtime.lifecycle import RunState

def ready_tasks(plan, states):
    tasks = parse_plan(plan)
    ids = {t.id for t in tasks}
    if set(states) != ids or any(not isinstance(s, RunState) for s in states.values()):
        raise ValueError("TASK_STATE_SET_MISMATCH")
    return tuple(sorted(t.id for t in tasks
                        if t.role not in ("human-authority", "independent-verifier")
                        and states[t.id] == RunState.QUEUED
                        and all(states[d] == RunState.SUCCEEDED for d in t.depends_on)))
