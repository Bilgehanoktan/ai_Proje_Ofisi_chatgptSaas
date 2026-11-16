"""0195 D0 first-claim admission: nine roles, one transaction, no real authority.
All references are synthetic. No renew, takeover, terminal, spend or provider call.
"""
from dataclasses import asdict, dataclass, field, replace
from copy import deepcopy
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import (Scope, RunObservation, RunState, LeaseObservation,
    valid_scope, valid_lease, inspect_lease, uint, token)
from app.core.agent_runtime.scheduler_review import inspect_schedule, inspect_pinned_schedule
from app.core.orchestrator.engine import canonical_plan
from app.core.transaction.review import Operation, valid_intent, required_roles, digest_ok
from app.core.transaction.port import CommitReceipt
from app.core.transaction.postgres_transition_mapping import _key, _one, _lease, lease_digest, transaction_ref
from app.core.agent_runtime.postgres_run import PostgresRunRepository, _scope_values, _WHERE
from app.core.event_store.postgres_write import reserve_fence, append_event, insert_outbox

_ROLES = frozenset({'HEAD','ADMISSION','LEASE','BUDGET','MUTATION','FENCE','EVENT','OUTBOX','AUDIT'})
_KEY = 'tenant_id=%s AND company_id=%s AND environment_id=%s AND run_id=%s'
_BKEY = 'tenant_id=%s AND company_id=%s AND environment_id=%s AND budget_id=%s'

@dataclass(frozen=True)
class SampleBudget:
    budget_id: str
    revision: int
    currency: str
    limit_minor: int
    outstanding_minor: int
    recognized_cost_minor: int
    unknown_cost: bool
    policy_epoch: int
    witness_epoch: int
    source_digest: str

@dataclass(frozen=True)
class ClaimSpec:
    before: RunObservation
    admission_id: str
    lease: LeaseObservation
    budget: SampleBudget
    amount_minor: int
    plan_digest: str


def claim_digest(spec):
    return sha256(json.dumps(asdict(spec),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def valid_budget(b):
    return (isinstance(b,SampleBudget) and token(b.budget_id) and isinstance(b.currency,str)
            and len(b.currency)==3 and b.currency.isascii() and b.currency.isalpha() and b.currency.isupper()
            and all(uint(x) for x in (b.revision,b.limit_minor,b.outstanding_minor,b.recognized_cost_minor,b.policy_epoch,b.witness_epoch))
            and b.revision<2**63-1 and type(b.unknown_cost) is bool and digest_ok(b.source_digest)
            and b.outstanding_minor+b.recognized_cost_minor<=b.limit_minor)

class D0PostgresAdmissionMapping:
    """Explicit, single-use mapping for LogicalT1Coordinator.commit(ADMISSION)."""
    def __init__(self, plan, spec, clock, *, history_pins=None):
        self.plan=deepcopy(plan); self.spec=spec; self.clock=clock; self.intent=None
        self.history_pins=history_pins
        self.written=set(); self.verified=False; self.last_tick=None

    def _check_clock(self):
        lease=self.spec.lease; c=self.clock(); review=inspect_lease(lease,lease,c)
        if review.freshness!='FRESH': raise ValueError(review.reason)
        if self.last_tick is not None and c.now_tick<self.last_tick: raise ValueError('D0_CLAIM_CLOCK_REGRESSION')
        self.last_tick=c.now_tick

    def _budget(self,c,i,lock=False):
        row=_one(c,'SELECT revision,currency,limit_minor,outstanding_minor,recognized_cost_minor,unknown_cost,policy_epoch,witness_epoch,source_digest FROM t1_candidate.sample_budgets WHERE '+_BKEY+(' FOR UPDATE' if lock else ''),(*_key(i)[:3],i.budget_ref))
        if row is None: raise ValueError('D0_CLAIM_BUDGET_MISSING')
        # SQLite returns 0/1; PostgreSQL returns bool. Reject every other representation.
        if type(row[5]) not in (bool,int) or row[5] not in (0,1): raise ValueError('D0_CLAIM_BUDGET_INVALID')
        return SampleBudget(i.budget_ref,*row[:5],bool(row[5]),*row[6:])

    def lock_and_validate(self,c,i):
        s=self.spec
        if (self.intent is not None or not valid_intent(i) or i.operation!=Operation.ADMISSION
                or required_roles(i)!=_ROLES or not isinstance(s,ClaimSpec) or not isinstance(s.before,RunObservation)
                or not valid_scope(s.before.scope) or s.before.scope!=i.scope or s.before.state!=RunState.QUEUED
                or not uint(s.before.version) or not uint(s.before.attempt) or s.before.version!=i.expected_version
                or not token(s.admission_id) or not valid_lease(s.lease) or s.lease.scope!=i.scope
                or (s.lease.lease_id,s.lease.grant_id,s.lease.policy_epoch,s.lease.witness_epoch)!=(i.lease_ref,i.grant_ref,i.policy_epoch,i.witness_epoch)
                or (s.lease.lease_version,s.lease.heartbeat_revision,s.lease.fence)!=(1,0,1)
                or not valid_budget(s.budget) or s.budget.budget_id!=i.budget_ref
                or (s.budget.policy_epoch,s.budget.witness_epoch)!=(i.policy_epoch,i.witness_epoch)
                or not uint(s.amount_minor) or s.amount_minor==0 or i.request_digest!=claim_digest(s)):
            raise ValueError('D0_CLAIM_BINDING_HOLD')
        projection=canonical_plan(self.plan)
        if projection['digest']!=s.plan_digest or projection['revision']!=i.scope.plan_revision:
            raise ValueError('D0_CLAIM_PLAN_HOLD')
        # Fixed order across all claim writers; no creation or reassignment of run heads here.
        c.execute('SELECT plan_revision,task_id,run_id,agent_instance_id,principal_id,state,version,attempt FROM t1_candidate.run_heads WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND plan_revision=%s ORDER BY run_id FOR UPDATE',(*_key(i)[:3],i.scope.plan_revision))
        observations=[]
        while (row:=c.fetchone()) is not None:
            if len(observations)>=100: raise ValueError('D0_CLAIM_ROSTER_LIMIT')
            observations.append(RunObservation(Scope(*_key(i)[:3],*row[:5]),RunState(row[5]),row[6],row[7]))
        if self.history_pins is None:
            schedule=inspect_schedule(self.plan,tuple(observations))
        else:
            # Lazy import avoids the existing history -> admission module cycle.
            from app.core.event_store.plan_history_review import RunHistoryPin, inspect_plan_history
            if type(self.history_pins) is not tuple or not all(type(p) is RunHistoryPin for p in self.history_pins):
                raise ValueError('D0_SCHEDULE_HISTORY_PIN_HOLD')
            schedule=inspect_pinned_schedule(self.plan,tuple(observations),tuple(p.initial for p in self.history_pins))
            history=inspect_plan_history(c,self.plan,i.scope.plan_revision,self.history_pins)
            if (not history.structural_match or history.plan_revision!=i.scope.plan_revision
                    or not any(t.task_id==i.scope.task_id and t.dependency_status=='READY_OBSERVATION_ONLY'
                               for t in history.tasks)):
                raise ValueError('D0_SCHEDULE_HISTORY_HOLD')
        if s.before not in observations or i.scope.task_id not in schedule.ready:
            raise ValueError('D0_CLAIM_NOT_READY')
        if _one(c,'SELECT lease_id FROM t1_candidate.run_leases WHERE '+_KEY,_key(i)) is not None:
            raise ValueError('D0_CLAIM_LEASE_EXISTS')
        b=self._budget(c,i,True)
        if b!=s.budget or b.unknown_cost or s.amount_minor>b.limit_minor-b.outstanding_minor-b.recognized_cost_minor:
            raise ValueError('D0_CLAIM_BUDGET_HOLD')
        self._check_clock()
        # No backdated first heartbeat; precommit freshness is rechecked below.
        if s.lease.heartbeat_tick!=self.last_tick: raise ValueError('D0_CLAIM_INITIAL_CLOCK_HOLD')
        self.intent=i

    def write_role(self,c,role,i):
        if self.intent!=i or role not in _ROLES or role in self.written or self.verified: raise ValueError('D0_CLAIM_ROLE_HOLD')
        s=self.spec; k=_key(i); v=i.expected_version+1; tx=transaction_ref(i); l=s.lease; b=s.budget
        if role=='HEAD':
            c.execute('UPDATE t1_candidate.run_heads SET state=%s,version=version+1 WHERE '+_WHERE+' AND state=%s AND version=%s AND attempt=%s RETURNING version',('ADMITTED',*_scope_values(i.scope),'QUEUED',i.expected_version,s.before.attempt))
            if c.fetchone()!=(v,): raise ValueError('D0_CLAIM_HEAD_CAS_HOLD')
        elif role=='ADMISSION':
            c.execute('INSERT INTO t1_candidate.run_admissions VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*k,s.admission_id,tx,i.request_digest,l.lease_id,l.grant_id,b.budget_id))
        elif role=='LEASE':
            c.execute('INSERT INTO t1_candidate.run_leases VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*k,i.scope.plan_revision,i.scope.task_id,i.scope.agent_instance_id,i.scope.principal_id,l.lease_id,l.grant_id,l.lease_version,l.heartbeat_revision,l.fence,l.policy_epoch,l.witness_epoch,l.expires_tick,l.heartbeat_tick))
        elif role=='BUDGET':
            c.execute('UPDATE t1_candidate.sample_budgets SET revision=revision+1,outstanding_minor=outstanding_minor+%s WHERE '+_BKEY+' AND revision=%s AND unknown_cost=false RETURNING revision',(s.amount_minor,*k[:3],b.budget_id,b.revision))
            if c.fetchone()!=(b.revision+1,): raise ValueError('D0_CLAIM_BUDGET_CAS_HOLD')
            c.execute('INSERT INTO t1_candidate.sample_reservations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*k,b.budget_id,b.revision+1,s.amount_minor,b.currency,i.request_digest,tx))
        elif role=='MUTATION':
            c.execute('INSERT INTO t1_candidate.run_mutations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*k,v,tx,i.request_digest,'QUEUED','ADMITTED',s.before.attempt))
        elif role=='FENCE': reserve_fence(c,i)
        elif role=='EVENT': append_event(c,i,tx,'D0_RUN_ADMISSION')
        elif role=='OUTBOX': insert_outbox(c,i,tx)
        elif role=='AUDIT':
            c.execute('INSERT INTO t1_candidate.run_audit VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*k,v,tx,i.request_digest,i.effect_key,i.idempotency_key,i.grant_ref,i.lease_ref,i.policy_epoch,i.witness_epoch,l.fence,lease_digest(l)))
        self.written.add(role)

    def verify_write_set(self,c,i,roles):
        if self.intent!=i or self.written!=_ROLES or roles!=_ROLES or self.verified: raise ValueError('D0_CLAIM_WRITE_SET_HOLD')
        self._check_clock()
        self._verify_rows(c,i)
        self.verified=True
        return CommitReceipt(transaction_ref(i),i.expected_version+1,i.request_digest)

    def _verify_rows(self,c,i):
        s=self.spec; k=_key(i); v=i.expected_version+1; tx=transaction_ref(i); b=s.budget; l=s.lease
        if PostgresRunRepository().read(c,i.scope)!=replace(s.before,state=RunState.ADMITTED,version=v) or _lease(c,i)!=l or self._budget(c,i)!=replace(b,revision=b.revision+1,outstanding_minor=b.outstanding_minor+s.amount_minor):
            raise ValueError('D0_CLAIM_POSTIMAGE_HOLD')
        suffix=' WHERE '+_KEY+' AND version=%s'
        checks=(
            ('SELECT admission_id,transaction_ref,request_digest,lease_id,grant_id,budget_id FROM t1_candidate.run_admissions WHERE '+_KEY,k,(s.admission_id,tx,i.request_digest,l.lease_id,l.grant_id,b.budget_id)),
            ('SELECT budget_id,budget_revision,amount_minor,currency,request_digest,transaction_ref FROM t1_candidate.sample_reservations WHERE '+_KEY,k,(b.budget_id,b.revision+1,s.amount_minor,b.currency,i.request_digest,tx)),
            ('SELECT transaction_ref,request_digest,before_state,after_state,attempt FROM t1_candidate.run_mutations'+suffix,(*k,v),(tx,i.request_digest,'QUEUED','ADMITTED',s.before.attempt)),
            ('SELECT event_id,event_type,request_digest FROM t1_candidate.events'+suffix,(*k,v),(tx,'D0_RUN_ADMISSION',i.request_digest)),
            ('SELECT event_id,request_digest FROM t1_candidate.outbox WHERE '+_KEY+' AND event_id=%s',(*k,tx),(tx,i.request_digest)),
            ('SELECT effect_key,idempotency_key,request_digest FROM t1_candidate.fences WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND (effect_key=%s OR idempotency_key=%s)',(*k[:3],i.effect_key,i.idempotency_key),(i.effect_key,i.idempotency_key,i.request_digest)),
            ('SELECT transaction_ref,request_digest,effect_key,idempotency_key,grant_ref,lease_ref,policy_epoch,witness_epoch,lease_fence,lease_digest FROM t1_candidate.run_audit'+suffix,(*k,v),(tx,i.request_digest,i.effect_key,i.idempotency_key,i.grant_ref,i.lease_ref,i.policy_epoch,i.witness_epoch,l.fence,lease_digest(l))))
        for sql,params,expected in checks:
            row=_one(c,sql,params)
            if row is None or tuple(row)!=expected: raise ValueError('D0_CLAIM_READBACK_HOLD')


@dataclass(frozen=True)
class AdmissionReconciliation:
    reason: str
    exact_sample_match: bool = False
    decision: str = field(default='HOLD',init=False)
    retry_allowed: bool = field(default=False,init=False)
    dispatch_allowed: bool = field(default=False,init=False)
    committed: bool = field(default=False,init=False)

def reconcile_admission(cursor, plan, spec, intent):
    """Independent caller-owned read-only consistent snapshot, never auto-retry.
    Current head/budget advances intentionally yield HOLD until historical proof exists.
    """
    try:
        if (not valid_intent(intent) or intent.operation!=Operation.ADMISSION
                or not isinstance(spec,ClaimSpec) or not valid_lease(spec.lease)
                or not valid_budget(spec.budget) or spec.before.scope!=intent.scope
                or spec.before.version!=intent.expected_version or spec.before.state!=RunState.QUEUED
                or spec.lease.scope!=intent.scope or spec.budget.budget_id!=intent.budget_ref
                or (spec.lease.lease_id,spec.lease.grant_id,spec.lease.policy_epoch,spec.lease.witness_epoch)!=(intent.lease_ref,intent.grant_ref,intent.policy_epoch,intent.witness_epoch)
                or intent.request_digest!=claim_digest(spec)
                or canonical_plan(plan)['digest']!=spec.plan_digest
                or canonical_plan(plan)['revision']!=intent.scope.plan_revision):
            return AdmissionReconciliation('D0_CLAIM_READBACK_BINDING_HOLD')
        D0PostgresAdmissionMapping(plan,spec,None)._verify_rows(cursor,intent)
    except Exception:
        return AdmissionReconciliation('D0_CLAIM_READBACK_INCOMPLETE_OR_UNAVAILABLE')
    return AdmissionReconciliation('D0_CLAIM_EXACT_SAMPLE_AUTHORITY_UNPROVEN',True)


def commit_scheduled_admission(*, connect, plan, spec, intent, clock, members, pool, history, history_pins):
    """Explicit D0 company/plan admission using the existing T1 coordinator.

    Roster and retained pins are caller-pinned fixture inputs, not real identity
    or role authority. The company preimage and plan history are checked inside
    one transaction, before any admission write. No assignment or worker dispatch.
    """
    from app.core.event_store.company_coordination import (
        SCOPE, Pool, CompanyEvent, CompanyCoordinatedMapping, _roster,
    )
    from app.core.event_store.plan_history_review import RunHistoryPin
    from app.core.transaction.port import LogicalT1Coordinator
    from app.core.transaction.postgres_session import postgres_transaction

    if (type(spec) is not ClaimSpec or not valid_intent(intent) or intent.operation is not Operation.ADMISSION
            or not isinstance(spec.before,RunObservation) or spec.before.scope!=intent.scope
            or type(pool) is not Pool or type(history) is not tuple or type(history_pins) is not tuple
            or not all(type(p) is RunHistoryPin and isinstance(p.initial,RunObservation)
                       and valid_scope(p.initial.scope) for p in history_pins)
            or not valid_budget(spec.budget) or spec.budget.budget_id!=pool.budget_id):
        raise ValueError('D0_SCHEDULE_ADMISSION_BINDING_HOLD')
    roster=_roster(members)
    s=intent.scope
    member=roster.get(s.run_id)
    projection=canonical_plan(plan)
    if member is None or (s.tenant_id,s.company_id,s.environment_id)!=SCOPE or projection['revision']!=s.plan_revision:
        raise ValueError('D0_SCHEDULE_MEMBER_HOLD')
    plan_members={m.run_id:m for m in members if m.plan_revision==s.plan_revision}
    pins={p.initial.scope.run_id:p for p in history_pins}
    if len(pins)!=len(history_pins) or set(pins)!=set(plan_members) or s.run_id not in pins:
        raise ValueError('D0_SCHEDULE_MEMBER_HOLD')
    for run_id,p in pins.items():
        r=p.initial; m=plan_members[run_id]; q=r.scope
        if ((q.tenant_id,q.company_id,q.environment_id)!=SCOPE
                or (q.plan_revision,q.task_id,q.run_id,q.agent_instance_id,q.principal_id,r.version)
                   !=(m.plan_revision,m.task_id,m.run_id,m.agent_instance_id,m.principal_id,m.initial_version)
                or m.project_id!=member.project_id):
            raise ValueError('D0_SCHEDULE_MEMBER_HOLD')
    if pins[s.run_id].initial!=spec.before or pins[s.run_id].admission is not None or pins[s.run_id].commands:
        raise ValueError('D0_SCHEDULE_INITIAL_HOLD')
    # Current D0 has no verified success path; only root tasks can be admitted.
    # Derive the event from the existing membership and intent; never invent a
    # predecessor transaction or reinterpret a bare SUCCEEDED head as a receipt.
    task=next((t for t in projection['tasks'] if t['id']==s.task_id),None)
    if task is None or task['depends_on'] or task['role'] not in ('orchestrator','research','engineer','qa'):
        raise ValueError('D0_SCHEDULE_PREDECESSOR_PROOF_HOLD')
    event=CompanyEvent(len(history)+1,member.project_id,s.run_id,intent.expected_version+1,
                       transaction_ref(intent),intent.request_digest,'D0_RUN_ADMISSION',(),
                       spec.budget.revision,spec.amount_minor)
    mapping=CompanyCoordinatedMapping(D0PostgresAdmissionMapping(plan,spec,clock,history_pins=history_pins),
                                      members,pool,history,event)
    return LogicalT1Coordinator(lambda:postgres_transaction(connect,mapping)).commit(intent)
