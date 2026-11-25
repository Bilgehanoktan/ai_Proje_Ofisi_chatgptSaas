"""D0 plan-wide exact historical evidence. No API, UI, authority or live freshness.
Caller must supply independently retained pins and one consistent read-only snapshot.
"""
from dataclasses import dataclass, field, replace
from app.core.agent_runtime.lifecycle import RunObservation, RunState, valid_scope, uint
from app.core.orchestrator.engine import canonical_plan
from app.core.agent_runtime.scheduler_review import inspect_schedule
from app.core.transaction.postgres_lifecycle_mapping import AdmissionBinding
from app.core.event_store.history_readback import inspect_history, MAX_COMMANDS, LifecyclePin
from app.core.transaction.postgres_admission_mapping import SampleBudget, valid_budget

_AGENT_ROLES = frozenset(('orchestrator', 'research', 'engineer', 'qa'))
_SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
_RUN_KEY = 'tenant_id=%s AND company_id=%s AND environment_id=%s AND run_id=%s'
_POOL_KEY = 'tenant_id=%s AND company_id=%s AND environment_id=%s AND budget_id=%s'
_TABLES = ('run_admissions','run_leases','sample_reservations','run_mutations','events','outbox','run_audit','run_lease_renewals','sample_settlements')
MAX_PLAN_COMMANDS = 5000

@dataclass(frozen=True)
class RunHistoryPin:
    initial: RunObservation
    admission: AdmissionBinding | None = None
    commands: tuple = ()

@dataclass(frozen=True)
class TaskHistory:
    task_id: str
    role: str
    state: str | None
    version: int | None
    event_count: int | None
    dependency_status: str

@dataclass(frozen=True)
class PlanHistoryReview:
    reason: str
    plan_revision: str | None = None
    tasks: tuple[TaskHistory, ...] = ()
    event_count: int | None = None
    structural_match: bool = False
    budget_reconciled: bool = False
    decision: str = field(default='HOLD', init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    release_ready: bool = field(default=False, init=False)
    freshness: str = field(default='HISTORICAL_SAMPLE', init=False)


def _rows(c, sql, params, limit):
    c.execute(sql, params)
    rows=[]
    while (row:=c.fetchone()) is not None:
        if len(rows)>=limit: raise ValueError('D0_PLAN_ROW_LIMIT')
        rows.append(tuple(row))
    return rows


def _validate_unadmitted(c, pin):
    if pin.commands or pin.initial.state!=RunState.QUEUED:
        raise ValueError('D0_PLAN_INITIAL_HOLD')
    for table in _TABLES:
        if _rows(c,'SELECT run_id FROM t1_candidate.'+table+' WHERE '+_RUN_KEY,(*_SCOPE,pin.initial.scope.run_id),1):
            raise ValueError('D0_PLAN_UNADMITTED_ARTIFACT')


def _reconcile_pools(c, anchors, pins):
    """Optional stricter profile: each pinned pool belongs only to these runs.
    Initial balance zero, recognized cost zero; exact revision chain and current row.
    No inference about other pools, external effects or actual financial accounting.
    """
    if not isinstance(anchors,tuple) or not 1<=len(anchors)<=100:
        raise ValueError('D0_PLAN_POOL_ANCHORS_HOLD')
    by_id={}
    for b in anchors:
        if not valid_budget(b) or b.budget_id in by_id or b.outstanding_minor or b.recognized_cost_minor or b.unknown_cost:
            raise ValueError('D0_PLAN_POOL_ANCHOR_HOLD')
        by_id[b.budget_id]=b
    operations={k:[] for k in by_id}; reservations={k:[] for k in by_id}
    for p in pins:
        if p.admission is None: continue
        claim=p.admission.claim; b=claim.budget
        if b.budget_id not in by_id: raise ValueError('D0_PLAN_POOL_UNPINNED')
        operations[b.budget_id].append((b,claim.amount_minor))
        reservations[b.budget_id].append(p.initial.scope.run_id)
        for cmd in p.commands:
            if isinstance(cmd,LifecyclePin):
                s=cmd.spec
                operations[b.budget_id].append((s.budget,0 if s.renewal is not None else -claim.amount_minor))
    for bid,anchor in by_id.items():
        current=anchor
        for before,delta in sorted(operations[bid],key=lambda item:item[0].revision):
            if before!=current: raise ValueError('D0_PLAN_POOL_SEQUENCE_HOLD')
            current=replace(current,revision=current.revision+1,outstanding_minor=current.outstanding_minor+delta)
            if not valid_budget(current): raise ValueError('D0_PLAN_POOL_BALANCE_HOLD')
        rows=_rows(c,'SELECT revision,currency,limit_minor,outstanding_minor,recognized_cost_minor,unknown_cost,policy_epoch,witness_epoch,source_digest FROM t1_candidate.sample_budgets WHERE '+_POOL_KEY,(*_SCOPE,bid),1)
        if len(rows)!=1 or type(rows[0][5]) not in (int,bool) or rows[0][5] not in (0,1):
            raise ValueError('D0_PLAN_POOL_ROW_HOLD')
        row=rows[0]; observed=SampleBudget(bid,*row[:5],bool(row[5]),*row[6:])
        if observed!=current: raise ValueError('D0_PLAN_POOL_POSTIMAGE_HOLD')
        actual=_rows(c,'SELECT run_id FROM t1_candidate.sample_reservations WHERE '+_POOL_KEY+' ORDER BY run_id',(*_SCOPE,bid),100)
        if actual!=[(r,) for r in sorted(reservations[bid])]: raise ValueError('D0_PLAN_POOL_FOREIGN_RESERVATION_HOLD')


def inspect_plan_history(cursor, plan, expected_revision, pins, *, exclusive_budget_anchors=None):
    """Validate exact persisted agent roster and all pinned run histories.
    Unadmitted agents must have exact QUEUED head and no scoped artifacts.
    Human/IV are gates, never agent runs. Current supported replay has no success
    authority: descendants cannot progress on a bare SUCCEEDED head. Optional
    exclusive pool replay verifies all known mutations of pinned sample pools.
    A single consistent snapshot is an explicit caller precondition.
    """
    try:
        projection=canonical_plan(plan)
        if projection['revision']!=expected_revision or not isinstance(pins,tuple) or len(pins)>100:
            raise ValueError('D0_PLAN_PIN_HOLD')
        tasks={t['id']:t for t in projection['tasks']}; ids={k for k,t in tasks.items() if t['role'] in _AGENT_ROLES}
        by_id={}; run_ids=set(); total=0
        for pin in pins:
            if not isinstance(pin,RunHistoryPin): raise ValueError('D0_PLAN_PIN_TYPE_HOLD')
            r=pin.initial
            if (not isinstance(r,RunObservation) or not valid_scope(r.scope) or r.scope.plan_revision!=expected_revision
                or r.scope.task_id not in ids or r.scope.task_id in by_id or r.scope.run_id in run_ids
                or r.state!=RunState.QUEUED or not uint(r.version) or not uint(r.attempt)
                or not isinstance(pin.commands,tuple) or len(pin.commands)>=MAX_COMMANDS):
                raise ValueError('D0_PLAN_RUN_PIN_HOLD')
            by_id[r.scope.task_id]=pin;run_ids.add(r.scope.run_id)
            total+=len(pin.commands)+int(pin.admission is not None)
            if total>MAX_PLAN_COMMANDS: raise ValueError('D0_PLAN_COMMAND_LIMIT')
        if set(by_id)!=ids: raise ValueError('D0_PLAN_ROSTER_HOLD')
        # Exact set of current persisted heads for this plan, including role/identity pins.
        rows=_rows(cursor,'SELECT task_id,run_id,agent_instance_id,principal_id,state,version,attempt FROM t1_candidate.run_heads WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND plan_revision=%s ORDER BY task_id',(*_SCOPE,expected_revision),100)
        heads={}; observed={}
        for k,pin in sorted(by_id.items()):
            r=pin.initial;s=r.scope
            if pin.admission is None:
                _validate_unadmitted(cursor,pin); state=r.state;version=r.version;count=0
            else:
                if not isinstance(pin.admission,AdmissionBinding) or pin.admission.claim.before!=r or pin.admission.claim.plan_digest!=projection['digest']:
                    raise ValueError('D0_PLAN_ADMISSION_PIN_HOLD')
                history=inspect_history(cursor,pin.admission,pin.commands)
                if not history.structural_match: raise ValueError('D0_PLAN_RUN_HISTORY_HOLD')
                state=RunState(history.state);version=history.version;count=len(history.observations)
            heads[k]=(k,s.run_id,s.agent_instance_id,s.principal_id,state.value,version,r.attempt)
            observed[k]=(replace(r,state=state,version=version),count)
        if rows!=[heads[k] for k in sorted(heads)]: raise ValueError('D0_PLAN_HEAD_SET_HOLD')
        # Only supported exact replay may satisfy a dependency. No success path exists yet.
        schedule=inspect_schedule(plan,tuple(observed[k][0] for k in sorted(observed)))
        if exclusive_budget_anchors is not None: _reconcile_pools(cursor,exclusive_budget_anchors,pins)
        result=[]
        for k,t in sorted(tasks.items()):
            if k not in observed:
                result.append(TaskHistory(k,t['role'],None,None,None,'INDEPENDENT_GATE_HOLD'));continue
            r,count=observed[k]
            status=('READY_OBSERVATION_ONLY' if k in schedule.ready else
                    'DEPENDENCY_HOLD' if r.state==RunState.QUEUED else 'HISTORICAL_RUN')
            result.append(TaskHistory(k,t['role'],r.state.value,r.version,count,status))
        return PlanHistoryReview('D0_PLAN_EXACT_REFERENCE_MATCH_ONLY',expected_revision,tuple(result),sum(n for _,n in observed.values()),True,exclusive_budget_anchors is not None)
    except Exception:
        return PlanHistoryReview('D0_PLAN_HISTORY_HOLD')
