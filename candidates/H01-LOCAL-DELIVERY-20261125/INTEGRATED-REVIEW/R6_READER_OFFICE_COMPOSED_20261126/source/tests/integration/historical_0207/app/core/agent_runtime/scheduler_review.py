"""Canonical plan-bound D0 scheduling review. No worker claim or dispatch.
This is an observation of dependency readiness, not admission or lease issuance.
"""
from dataclasses import dataclass, field
from app.core.agent_runtime.lifecycle import RunObservation, RunState, valid_scope, uint
from app.core.orchestrator.engine import canonical_plan
from app.core.orchestrator.readiness import ready_tasks

_AGENT_ROLES = frozenset({'orchestrator','research','engineer','qa'})

@dataclass(frozen=True)
class SchedulerReview:
    reason: str
    ready: tuple[str,...] = ()
    decision: str = field(default='HOLD', init=False)
    claim_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)

def inspect_schedule(plan, observations):
    projection = canonical_plan(plan)
    if not isinstance(observations, tuple):
        raise ValueError('SCHEDULER_OBSERVATIONS_INVALID')
    tasks = {t['id']:t for t in projection['tasks']}
    agent_ids = {k for k,t in tasks.items() if t['role'] in _AGENT_ROLES}
    by_id = {}
    run_ids = set()
    for run in observations:
        if (not isinstance(run, RunObservation) or not valid_scope(run.scope)
                or run.scope.plan_revision != projection['revision']
                or not isinstance(run.state, RunState) or not uint(run.version) or not uint(run.attempt)
                or run.scope.task_id not in agent_ids or run.scope.task_id in by_id
                or run.scope.run_id in run_ids):
            raise ValueError('SCHEDULER_RUN_BINDING_HOLD')
        by_id[run.scope.task_id] = run
        run_ids.add(run.scope.run_id)
    if set(by_id) != agent_ids:
        raise ValueError('SCHEDULER_INCOMPLETE_RUN_SET')
    states = {k:by_id[k].state if k in by_id else RunState.WAITING_APPROVAL for k in tasks}
    # No forged terminal predecessor may bypass a still-unfinished dependency.
    for k,run in by_id.items():
        if run.state not in (RunState.CREATED, RunState.QUEUED, RunState.CANCELLED, RunState.TIMED_OUT):
            if any(states[d] != RunState.SUCCEEDED for d in tasks[k]['depends_on']):
                raise ValueError('SCHEDULER_CAUSAL_ORDER_HOLD')
    return SchedulerReview('D0_READY_ONLY_ADMISSION_AND_LEASE_REQUIRED', ready_tasks(plan, states))
