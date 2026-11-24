"""0198-E: historical D0 run readback against separately retained command pins.
Caller owns a consistent read-only snapshot. No provider, worker, release or freshness authority.
"""
from dataclasses import dataclass, field, replace
from app.core.agent_runtime.lifecycle import RunState, RunObservation, valid_lease, uint
from app.core.agent_runtime.postgres_run import PostgresRunRepository
from app.core.agent_runtime.transition_command import validate_transition
from app.core.transaction.review import valid_intent, Operation, required_roles, BASE_ROLES
from app.core.transaction.postgres_transition_mapping import _key, _KEY, _one, _lease, lease_digest, transaction_ref
from app.core.transaction.postgres_admission_mapping import claim_digest, valid_budget
from app.core.transaction.postgres_lifecycle_mapping import (AdmissionBinding, LifecycleSpec,
    D0PostgresLifecycleMapping, verify_admission_binding, FAILURE)

MAX_COMMANDS = 1000

@dataclass(frozen=True)
class OrdinaryPin:
    intent: object
    before: RunObservation
    target: RunState
    lease: object

@dataclass(frozen=True)
class LifecyclePin:
    intent: object
    spec: LifecycleSpec

@dataclass(frozen=True)
class HistoryReview:
    reason: str
    state: str | None = None
    version: int | None = None
    observations: tuple[tuple[int, str, str], ...] = ()
    structural_match: bool = False
    decision: str = field(default='HOLD', init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    release_ready: bool = field(default=False, init=False)
    freshness: str = field(default='HISTORICAL_SAMPLE', init=False)


def _same_lease_intent(i, l):
    return (valid_lease(l) and l.scope == i.scope and
            (i.lease_ref,i.grant_ref,i.policy_epoch,i.witness_epoch)==
            (l.lease_id,l.grant_id,l.policy_epoch,l.witness_epoch))


def _exact_rows(c, sql, params, expected):
    c.execute(sql, params)
    for item in expected:
        row = c.fetchone()
        if row is None or tuple(row) != item:
            raise ValueError('D0_HISTORY_ROW_MISMATCH')
    if c.fetchone() is not None:
        raise ValueError('D0_HISTORY_EXTRA_ROW')


def inspect_history(cursor, binding, commands):
    """Exact complete per-run history; independent expected pins are a caller precondition.
    Only accepts the initial QUEUED head plus admission and ordinary/renewal/failure pins.
    Global budget balance, foreign runs, independent signatures and anti-restore are not proven.
    """
    try:
        if not isinstance(binding, AdmissionBinding) or not isinstance(commands, tuple) or len(commands)>MAX_COMMANDS-1:
            raise ValueError('D0_HISTORY_INPUT_HOLD')
        s, a = binding.claim, binding.intent
        l, b = s.lease, s.budget
        if (not valid_intent(a) or a.operation != Operation.ADMISSION or s.before.scope != a.scope
                or s.before.state != RunState.QUEUED or not uint(s.before.attempt)
                or s.before.version != a.expected_version or claim_digest(s) != a.request_digest
                or not _same_lease_intent(a,l) or (l.lease_version,l.heartbeat_revision,l.fence)!=(1,0,1)
                or not valid_budget(b) or b.unknown_cost or not uint(s.amount_minor) or s.amount_minor == 0
                or s.amount_minor > b.limit_minor-b.outstanding_minor-b.recognized_cost_minor
                or (a.budget_ref,a.policy_epoch,a.witness_epoch)!=(b.budget_id,b.policy_epoch,b.witness_epoch)):
            raise ValueError('D0_HISTORY_INITIAL_HOLD')
        k = _key(a); head = s.before; current = l; closed = False
        mutations=[]; events=[]; audits=[]; outbox=[]; renewals=[]; settlements=[]; observations=[]
        effects=set(); idems=set()
        def record(i,target,event,lease):
            nonlocal head
            if i.effect_key in effects or i.idempotency_key in idems:
                raise ValueError('D0_HISTORY_DUPLICATE_COMMAND')
            effects.add(i.effect_key); idems.add(i.idempotency_key)
            v=head.version+1; tx=transaction_ref(i); d=i.request_digest
            mutations.append((v,tx,d,head.state.value,target.value,head.attempt))
            events.append((v,tx,event,d)); outbox.append((tx,d))
            audits.append((v,tx,d,i.effect_key,i.idempotency_key,i.grant_ref,i.lease_ref,i.policy_epoch,i.witness_epoch,lease.fence,lease_digest(lease)))
            _exact_rows(cursor,'SELECT effect_key,idempotency_key,request_digest FROM t1_candidate.fences WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND (effect_key=%s OR idempotency_key=%s)',(*k[:3],i.effect_key,i.idempotency_key),[(i.effect_key,i.idempotency_key,d)])
            head=replace(head,state=target,version=v)
            observations.append((v,event,target.value))
        record(a,RunState.ADMITTED,'D0_RUN_ADMISSION',current)
        budget_floor=b.revision+1
        for pin in commands:
            if closed or not isinstance(pin,(OrdinaryPin,LifecyclePin)):
                raise ValueError('D0_HISTORY_COMMAND_HOLD')
            i=pin.intent
            if not valid_intent(i) or i.scope!=head.scope or i.expected_version!=head.version or not _same_lease_intent(i,current):
                raise ValueError('D0_HISTORY_SEQUENCE_HOLD')
            if isinstance(pin,OrdinaryPin):
                if pin.before!=head or pin.lease!=current or required_roles(i)!=BASE_ROLES or i.budget_ref is not None:
                    raise ValueError('D0_HISTORY_ORDINARY_HOLD')
                validate_transition(head,pin.target,i)
                record(i,pin.target,'D0_RUN_TRANSITION',current)
            else:
                spec=pin.spec
                if not isinstance(spec,LifecycleSpec) or spec.before!=head or spec.lease!=current or spec.binding!=binding:
                    raise ValueError('D0_HISTORY_LIFECYCLE_HOLD')
                # Pure existing validation; never call lock/write methods.
                D0PostgresLifecycleMapping(spec,None)._validate(i)
                pool=spec.budget
                if (pool.revision<budget_floor or pool.outstanding_minor<s.amount_minor or
                    (pool.budget_id,pool.currency,pool.limit_minor,pool.source_digest,pool.recognized_cost_minor)!=
                    (b.budget_id,b.currency,b.limit_minor,b.source_digest,b.recognized_cost_minor)):
                    raise ValueError('D0_HISTORY_BUDGET_HOLD')
                budget_floor=pool.revision+1
                v=head.version+1; tx=transaction_ref(i)
                if spec.renewal is not None:
                    renewals.append((v,tx,i.request_digest,lease_digest(current),lease_digest(spec.renewal),spec.renewal.lease_version))
                    current=spec.renewal
                    record(i,head.state,'D0_LEASE_RENEWAL',current)
                else:
                    settlements.append((v,tx,i.request_digest,s.admission_id,b.budget_id,s.amount_minor,0,budget_floor,lease_digest(current),FAILURE))
                    record(i,RunState.FAILED,'D0_RUN_FAILURE',current); closed=True
        suffix=' WHERE '+_KEY
        for table,columns,order,expected in (
            ('run_mutations','version,transaction_ref,request_digest,before_state,after_state,attempt','version',mutations),
            ('events','version,event_id,event_type,request_digest','version',events),
            ('run_audit','version,transaction_ref,request_digest,effect_key,idempotency_key,grant_ref,lease_ref,policy_epoch,witness_epoch,lease_fence,lease_digest','version',audits),
            ('outbox','event_id,request_digest','event_id',sorted(outbox)),
            ('run_lease_renewals','version,transaction_ref,request_digest,old_lease_digest,new_lease_digest,lease_version','version',renewals),
            ('sample_settlements','version,transaction_ref,request_digest,admission_id,budget_id,released_minor,recognized_minor,budget_revision,lease_digest,outcome','version',settlements),
        ):
            _exact_rows(cursor,'SELECT '+columns+' FROM t1_candidate.'+table+suffix+' ORDER BY '+order,k,expected)
        if PostgresRunRepository().read(cursor,a.scope)!=head:
            raise ValueError('D0_HISTORY_HEAD_HOLD')
        if closed:
            if _one(cursor,'SELECT lease_id FROM t1_candidate.run_leases'+suffix,k) is not None:
                raise ValueError('D0_HISTORY_CLOSED_LEASE_HOLD')
        elif _lease(cursor,a)!=current:
            raise ValueError('D0_HISTORY_CURRENT_LEASE_HOLD')
        verify_admission_binding(cursor,a,binding,current,closed=closed)
        return HistoryReview('D0_HISTORY_EXACT_REFERENCE_MATCH_ONLY',head.state.value,head.version,tuple(observations),True)
    except Exception:
        # Never return partially verified state or raw DB exception details.
        return HistoryReview('D0_HISTORY_READBACK_HOLD')


def office_history_projection(review):
    """Internal projection only, not an OfficeV0 schema or trusted live snapshot."""
    if not isinstance(review,HistoryReview) or not review.structural_match:
        return {'mode':'D0_HISTORY_HOLD','state':None,'version':None,'event_count':None,
                'freshness':'UNKNOWN','dispatch_allowed':False,'release_ready':False}
    return {'mode':'D0_HISTORY_SAMPLE','state':review.state,'version':review.version,
            'event_count':len(review.observations),'freshness':'HISTORICAL_SAMPLE',
            'dispatch_allowed':False,'release_ready':False}
