"""0196-L D0 renewal and local-failure closure. No actual grant, cost, provider,
worker dispatch, success receipt, cancellation authority or takeover.
Explicit isolated mapping only; uses existing T1 transport and coordinator.
"""
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
import json
from app.core.agent_runtime.lifecycle import (RunObservation, RunState, EDGES,
    valid_lease, inspect_lease, uint)
from app.core.agent_runtime.postgres_run import PostgresRunRepository, _scope_values, _WHERE
from app.core.transaction.review import Operation, valid_intent, required_roles, BASE_ROLES
from app.core.transaction.port import CommitReceipt
from app.core.transaction.postgres_transition_mapping import (D0PostgresTransitionMapping,
    _key, _one, _lease, lease_digest, transaction_ref, _KEY)
from app.core.transaction.postgres_admission_mapping import (ClaimSpec, SampleBudget,
    claim_digest, valid_budget, _BKEY, D0PostgresAdmissionMapping)
from app.core.event_store.postgres_write import append_event, insert_outbox, reserve_fence

ROLES = BASE_ROLES | {'LEASE','BUDGET'}
ACTIVE = frozenset({RunState.ADMITTED,RunState.PLANNING,RunState.RUNNING,RunState.VERIFYING})
FAILURE = 'D0_LOCAL_FAILURE_NO_EFFECT'
MAX_RENEWAL_TICKS = 60

@dataclass(frozen=True)
class AdmissionBinding:
    claim: ClaimSpec
    intent: object

@dataclass(frozen=True)
class LifecycleSpec:
    before: RunObservation
    lease: object
    binding: AdmissionBinding
    budget: SampleBudget
    renewal: object = None
    outcome: str | None = None


def lifecycle_digest(spec):
    return sha256(json.dumps(asdict(spec),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _expect(c, sql, params, expected):
    row = _one(c,sql,params)
    if row is None or tuple(row)!=expected:
        raise ValueError('D0_LIFECYCLE_READBACK_HOLD')


def verify_admission_binding(c, i, binding, current_lease, *, closed=False):
    """Verify immutable initial claim rows, not the current claim postimage.
    Current lease is pinned to initial claim or latest renewal and its audit.
    Caller must own a single consistent snapshot and lock run head before writes.
    """
    if not isinstance(binding,AdmissionBinding) or not isinstance(binding.claim,ClaimSpec):
        raise ValueError('D0_ADMISSION_BINDING_HOLD')
    s=binding.claim; a=binding.intent; l=s.lease; b=s.budget
    if (not valid_intent(a) or a.operation!=Operation.ADMISSION or a.scope!=i.scope
            or a.expected_version!=s.before.version or s.before.scope!=i.scope
            or s.before.state!=RunState.QUEUED or not valid_lease(l) or not valid_budget(b)
            or not uint(s.amount_minor) or s.amount_minor==0 or a.request_digest!=claim_digest(s)
            or (a.lease_ref,a.grant_ref,a.policy_epoch,a.witness_epoch,a.budget_ref)!=(l.lease_id,l.grant_id,l.policy_epoch,l.witness_epoch,b.budget_id)
            or not valid_lease(current_lease) or current_lease.scope!=i.scope or l.scope!=i.scope
            or (current_lease.lease_id,current_lease.grant_id,current_lease.policy_epoch,current_lease.witness_epoch,current_lease.fence)!=(l.lease_id,l.grant_id,l.policy_epoch,l.witness_epoch,l.fence)
            or (i.lease_ref,i.grant_ref,i.policy_epoch,i.witness_epoch)!=(l.lease_id,l.grant_id,l.policy_epoch,l.witness_epoch)
            or (i.budget_ref is not None and i.budget_ref!=b.budget_id)
            or s.plan_digest!=i.scope.plan_revision.removeprefix('sha256:')):
        raise ValueError('D0_ADMISSION_BINDING_HOLD')
    k=_key(i); tx=transaction_ref(a); v=a.expected_version+1; suffix=' WHERE '+_KEY+' AND version=%s'
    for sql,params,expected in (
        ('SELECT admission_id,transaction_ref,request_digest,lease_id,grant_id,budget_id FROM t1_candidate.run_admissions WHERE '+_KEY,k,(s.admission_id,tx,a.request_digest,l.lease_id,l.grant_id,b.budget_id)),
        ('SELECT budget_id,budget_revision,amount_minor,currency,request_digest,transaction_ref FROM t1_candidate.sample_reservations WHERE '+_KEY,k,(b.budget_id,b.revision+1,s.amount_minor,b.currency,a.request_digest,tx)),
        ('SELECT transaction_ref,request_digest,before_state,after_state,attempt FROM t1_candidate.run_mutations'+suffix,(*k,v),(tx,a.request_digest,'QUEUED','ADMITTED',s.before.attempt)),
        ('SELECT event_id,event_type,request_digest FROM t1_candidate.events'+suffix,(*k,v),(tx,'D0_RUN_ADMISSION',a.request_digest)),
        ('SELECT event_id,request_digest FROM t1_candidate.outbox WHERE '+_KEY+' AND event_id=%s',(*k,tx),(tx,a.request_digest)),
        ('SELECT effect_key,idempotency_key,request_digest FROM t1_candidate.fences WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND (effect_key=%s OR idempotency_key=%s)',(*k[:3],a.effect_key,a.idempotency_key),(a.effect_key,a.idempotency_key,a.request_digest)),
        ('SELECT transaction_ref,request_digest,effect_key,idempotency_key,grant_ref,lease_ref,policy_epoch,witness_epoch,lease_fence,lease_digest FROM t1_candidate.run_audit'+suffix,(*k,v),(tx,a.request_digest,a.effect_key,a.idempotency_key,a.grant_ref,a.lease_ref,a.policy_epoch,a.witness_epoch,l.fence,lease_digest(l)))
    ): _expect(c,sql,params,expected)
    # Walk renewal digest chain in order. Historical rows are not authority signatures.
    c.execute('SELECT version,transaction_ref,request_digest,old_lease_digest,new_lease_digest,lease_version FROM t1_candidate.run_lease_renewals WHERE '+_KEY+' ORDER BY lease_version',k)
    rows=[]
    while (row:=c.fetchone()) is not None:
        if len(rows)>=1000: raise ValueError('D0_RENEWAL_HISTORY_LIMIT')
        rows.append(tuple(row))
    head=PostgresRunRepository().read(c,i.scope)
    if head.version<v or head.attempt!=s.before.attempt: raise ValueError('D0_ADMISSION_HEAD_HOLD')
    prev=lease_digest(l); lv=l.lease_version; last=v
    for rv,rtx,rd,old,new,nv in rows:
        if old!=prev or nv!=lv+1 or rv<=last or rv>head.version:
            raise ValueError('D0_RENEWAL_HISTORY_HOLD')
        audit=_one(c,'SELECT transaction_ref,request_digest,lease_digest,effect_key,idempotency_key,grant_ref,lease_ref,policy_epoch,witness_epoch,lease_fence FROM t1_candidate.run_audit'+suffix,(*k,rv))
        if audit is None or tuple(audit[:3])!=(rtx,rd,new) or tuple(audit[5:])!=(l.grant_id,l.lease_id,l.policy_epoch,l.witness_epoch,l.fence):
            raise ValueError('D0_RENEWAL_HISTORY_HOLD')
        mutation=_one(c,'SELECT transaction_ref,request_digest,before_state,after_state,attempt FROM t1_candidate.run_mutations'+suffix,(*k,rv))
        if mutation is None or tuple(mutation[:2])!=(rtx,rd) or mutation[2]!=mutation[3] or mutation[4]!=s.before.attempt:
            raise ValueError('D0_RENEWAL_HISTORY_HOLD')
        _expect(c,'SELECT event_id,event_type,request_digest FROM t1_candidate.events'+suffix,(*k,rv),(rtx,'D0_LEASE_RENEWAL',rd))
        _expect(c,'SELECT event_id,request_digest FROM t1_candidate.outbox WHERE '+_KEY+' AND event_id=%s',(*k,rtx),(rtx,rd))
        _expect(c,'SELECT effect_key,idempotency_key,request_digest FROM t1_candidate.fences WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND (effect_key=%s OR idempotency_key=%s)',(*k[:3],audit[3],audit[4]),(audit[3],audit[4],rd))
        prev=new;lv=nv;last=rv
    if lease_digest(current_lease)!=prev or current_lease.lease_version!=lv:
        raise ValueError('D0_RENEWAL_HISTORY_HOLD')
    settled=_one(c,'SELECT outcome FROM t1_candidate.sample_settlements WHERE '+_KEY,k)
    if (settled is not None)!=closed or (closed and settled!=(FAILURE,)):
        raise ValueError('D0_SETTLEMENT_STATE_HOLD')


class D0AdmissionBoundTransitionMapping(D0PostgresTransitionMapping):
    """Explicit stronger ordinary-transition path; old 0194 fixture mapping retained."""
    def __init__(self,binding,lease_reference,clock):
        super().__init__(lease_reference,clock); self.binding=binding
    def lock_and_validate(self,c,i):
        super().lock_and_validate(c,i)
        verify_admission_binding(c,i,self.binding,self.reference)
    def verify_write_set(self,c,i,roles):
        verify_admission_binding(c,i,self.binding,self.reference)
        return super().verify_write_set(c,i,roles)


class D0PostgresLifecycleMapping:
    """Eight-role renewal or local failure. Same run, no fence takeover.
    Renewal increments head version and budget revision but changes no balance.
    Terminal only FAILED for an explicit D0 no-effect fixture; not cancellation,
    timeout or success. Active lease removed, reservation history retained.
    """
    def __init__(self,spec,clock):
        self.spec=spec; self.clock=clock; self.intent=None; self.written=set(); self.last_tick=None; self.verified=False
    def _clock(self,lease,t=None):
        t=self.clock() if t is None else t; check=inspect_lease(lease,lease,t)
        if check.freshness!='FRESH': raise ValueError(check.reason)
        if self.last_tick is not None and t.now_tick<self.last_tick: raise ValueError('D0_CLOCK_REGRESSION_HOLD')
        self.last_tick=t.now_tick
        return t
    def _budget(self,c,i,lock=False):
        return D0PostgresAdmissionMapping(None,None,None)._budget(c,i,lock)
    def _validate(self,i):
        s=self.spec
        if (not isinstance(s,LifecycleSpec) or not valid_intent(i) or not isinstance(s.before,RunObservation)
                or s.before.scope!=i.scope or s.before.version!=i.expected_version or not uint(s.before.attempt)
                or s.before.state not in ACTIVE or not valid_lease(s.lease) or s.lease.scope!=i.scope
                or not isinstance(s.binding,AdmissionBinding) or not isinstance(s.binding.claim,ClaimSpec)
                or not valid_budget(s.budget) or s.budget.unknown_cost or s.budget.budget_id!=i.budget_ref
                or (s.budget.policy_epoch,s.budget.witness_epoch)!=(i.policy_epoch,i.witness_epoch)
                or (s.lease.lease_id,s.lease.grant_id,s.lease.policy_epoch,s.lease.witness_epoch)!=(i.lease_ref,i.grant_ref,i.policy_epoch,i.witness_epoch)
                or required_roles(i)!=ROLES or i.request_digest!=lifecycle_digest(s)):
            raise ValueError('D0_LIFECYCLE_BINDING_HOLD')
        if i.operation==Operation.STATE_MUTATION:
            n=s.renewal; l=s.lease
            if (s.outcome is not None or not valid_lease(n) or n!=replace(l,lease_version=l.lease_version+1,heartbeat_revision=l.heartbeat_revision+1,heartbeat_tick=n.heartbeat_tick,expires_tick=n.expires_tick)
                or n.heartbeat_tick<=l.heartbeat_tick or n.expires_tick<=l.expires_tick or n.expires_tick-n.heartbeat_tick>MAX_RENEWAL_TICKS):
                raise ValueError('D0_RENEWAL_BINDING_HOLD')
        elif i.operation==Operation.TERMINAL:
            if s.renewal is not None or s.outcome!=FAILURE or RunState.FAILED not in EDGES.get(s.before.state,()):
                raise PermissionError('D0_TERMINAL_FAILURE_ONLY')
        else: raise PermissionError('D0_LIFECYCLE_OPERATION_HOLD')
    def lock_and_validate(self,c,i):
        if self.intent is not None: raise ValueError('D0_LIFECYCLE_REUSE_HOLD')
        self._validate(i); s=self.spec
        if PostgresRunRepository().lock(c,i.scope)!=s.before: raise ValueError('D0_HEAD_CAS_HOLD')
        if _lease(c,i,True)!=s.lease: raise ValueError('D0_LEASE_CAS_HOLD')
        verify_admission_binding(c,i,s.binding,s.lease)
        b=self._budget(c,i,True)
        initial=s.binding.claim.budget
        if (b!=s.budget or (b.currency,b.limit_minor,b.source_digest,b.recognized_cost_minor)!=(initial.currency,initial.limit_minor,initial.source_digest,initial.recognized_cost_minor)
                or b.revision<initial.revision+1 or b.outstanding_minor<s.binding.claim.amount_minor):
            raise ValueError('D0_LIFECYCLE_BUDGET_HOLD')
        self._clock(s.lease)
        if s.renewal is not None and s.renewal.heartbeat_tick!=self.last_tick: raise ValueError('D0_RENEWAL_CLOCK_HOLD')
        self.intent=i
    def write_role(self,c,role,i):
        if self.intent!=i or role not in ROLES or role in self.written or self.verified: raise ValueError('D0_LIFECYCLE_ROLE_HOLD')
        s=self.spec;k=_key(i);v=i.expected_version+1;tx=transaction_ref(i);l=s.lease;n=s.renewal;b=s.budget
        target=s.before.state if n is not None else RunState.FAILED
        amount=0 if n is not None else s.binding.claim.amount_minor
        if role=='HEAD':
            c.execute('UPDATE t1_candidate.run_heads SET state=%s,version=version+1 WHERE '+_WHERE+' AND state=%s AND version=%s AND attempt=%s RETURNING version',(target.value,*_scope_values(i.scope),s.before.state.value,i.expected_version,s.before.attempt))
            if c.fetchone()!=(v,): raise ValueError('D0_HEAD_CAS_HOLD')
        elif role=='LEASE':
            if n is not None:
                c.execute('UPDATE t1_candidate.run_leases SET lease_version=%s,heartbeat_revision=%s,expires_tick=%s,heartbeat_tick=%s WHERE '+_KEY+' AND lease_version=%s AND heartbeat_revision=%s AND fence=%s RETURNING lease_version',(n.lease_version,n.heartbeat_revision,n.expires_tick,n.heartbeat_tick,*k,l.lease_version,l.heartbeat_revision,l.fence))
                if c.fetchone()!=(n.lease_version,): raise ValueError('D0_LEASE_CAS_HOLD')
                c.execute('INSERT INTO t1_candidate.run_lease_renewals VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*k,v,tx,i.request_digest,lease_digest(l),lease_digest(n),n.lease_version))
            else:
                c.execute('DELETE FROM t1_candidate.run_leases WHERE '+_KEY+' AND lease_version=%s AND fence=%s RETURNING lease_id',(*k,l.lease_version,l.fence))
                if c.fetchone()!=(l.lease_id,): raise ValueError('D0_LEASE_CAS_HOLD')
        elif role=='BUDGET':
            c.execute('UPDATE t1_candidate.sample_budgets SET revision=revision+1,outstanding_minor=outstanding_minor-%s WHERE '+_BKEY+' AND revision=%s AND outstanding_minor>=%s AND unknown_cost=false RETURNING revision',(amount,*k[:3],b.budget_id,b.revision,amount))
            if c.fetchone()!=(b.revision+1,): raise ValueError('D0_LIFECYCLE_BUDGET_CAS_HOLD')
            if n is None:
                c.execute('INSERT INTO t1_candidate.sample_settlements VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*k,v,tx,i.request_digest,s.binding.claim.admission_id,b.budget_id,amount,0,b.revision+1,lease_digest(l),FAILURE))
        elif role=='MUTATION':
            c.execute('INSERT INTO t1_candidate.run_mutations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*k,v,tx,i.request_digest,s.before.state.value,target.value,s.before.attempt))
        elif role=='FENCE': reserve_fence(c,i)
        elif role=='EVENT': append_event(c,i,tx,'D0_LEASE_RENEWAL' if n is not None else 'D0_RUN_FAILURE')
        elif role=='OUTBOX': insert_outbox(c,i,tx)
        elif role=='AUDIT':
            c.execute('INSERT INTO t1_candidate.run_audit VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(*k,v,tx,i.request_digest,i.effect_key,i.idempotency_key,i.grant_ref,i.lease_ref,i.policy_epoch,i.witness_epoch,l.fence,lease_digest(n or l)))
        self.written.add(role)
    def _verify_rows(self,c,i):
        s=self.spec;k=_key(i);v=i.expected_version+1;tx=transaction_ref(i);l=s.lease;n=s.renewal;b=s.budget
        target=s.before.state if n is not None else RunState.FAILED
        amount=0 if n is not None else s.binding.claim.amount_minor
        if PostgresRunRepository().read(c,i.scope)!=replace(s.before,state=target,version=v) or self._budget(c,i)!=replace(b,revision=b.revision+1,outstanding_minor=b.outstanding_minor-amount):
            raise ValueError('D0_LIFECYCLE_POSTIMAGE_HOLD')
        if n is not None:
            if _lease(c,i)!=n: raise ValueError('D0_LEASE_POSTIMAGE_HOLD')
            _expect(c,'SELECT transaction_ref,request_digest,old_lease_digest,new_lease_digest,lease_version FROM t1_candidate.run_lease_renewals WHERE '+_KEY+' AND version=%s',(*k,v),(tx,i.request_digest,lease_digest(l),lease_digest(n),n.lease_version))
        else:
            if _one(c,'SELECT lease_id FROM t1_candidate.run_leases WHERE '+_KEY,k) is not None: raise ValueError('D0_TERMINAL_LEASE_HOLD')
            _expect(c,'SELECT version,transaction_ref,request_digest,admission_id,budget_id,released_minor,recognized_minor,budget_revision,lease_digest,outcome FROM t1_candidate.sample_settlements WHERE '+_KEY,k,(v,tx,i.request_digest,s.binding.claim.admission_id,b.budget_id,amount,0,b.revision+1,lease_digest(l),FAILURE))
        suffix=' WHERE '+_KEY+' AND version=%s'
        for sql,params,expected in (
            ('SELECT transaction_ref,request_digest,before_state,after_state,attempt FROM t1_candidate.run_mutations'+suffix,(*k,v),(tx,i.request_digest,s.before.state.value,target.value,s.before.attempt)),
            ('SELECT event_id,event_type,request_digest FROM t1_candidate.events'+suffix,(*k,v),(tx,'D0_LEASE_RENEWAL' if n is not None else 'D0_RUN_FAILURE',i.request_digest)),
            ('SELECT event_id,request_digest FROM t1_candidate.outbox WHERE '+_KEY+' AND event_id=%s',(*k,tx),(tx,i.request_digest)),
            ('SELECT effect_key,idempotency_key,request_digest FROM t1_candidate.fences WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND (effect_key=%s OR idempotency_key=%s)',(*k[:3],i.effect_key,i.idempotency_key),(i.effect_key,i.idempotency_key,i.request_digest)),
            ('SELECT transaction_ref,request_digest,effect_key,idempotency_key,grant_ref,lease_ref,policy_epoch,witness_epoch,lease_fence,lease_digest FROM t1_candidate.run_audit'+suffix,(*k,v),(tx,i.request_digest,i.effect_key,i.idempotency_key,i.grant_ref,i.lease_ref,i.policy_epoch,i.witness_epoch,l.fence,lease_digest(n or l)))
        ): _expect(c,sql,params,expected)
        verify_admission_binding(c,i,s.binding,n or l,closed=n is None)
    def verify_write_set(self,c,i,roles):
        if self.intent!=i or self.written!=ROLES or roles!=ROLES or self.verified: raise ValueError('D0_LIFECYCLE_WRITE_SET_HOLD')
        # Old lease must still be fresh; a renewal cannot rescue an expired grant.
        tick=self._clock(self.spec.lease)
        if self.spec.renewal is not None: self._clock(self.spec.renewal,tick)
        self._verify_rows(c,i);self.verified=True
        return CommitReceipt(transaction_ref(i),i.expected_version+1,i.request_digest)


@dataclass(frozen=True)
class LifecycleReconciliation:
    reason: str
    exact_sample_match: bool=False
    decision: str=field(default='HOLD',init=False)
    retry_allowed: bool=field(default=False,init=False)
    committed: bool=field(default=False,init=False)
    dispatch_allowed: bool=field(default=False,init=False)


def reconcile_lifecycle(cursor,spec,intent):
    """Independent caller-owned consistent read-only snapshot; no blind retry."""
    try:
        m=D0PostgresLifecycleMapping(spec,None);m._validate(intent);m._verify_rows(cursor,intent)
    except Exception:
        return LifecycleReconciliation('D0_LIFECYCLE_READBACK_HOLD')
    return LifecycleReconciliation('D0_LIFECYCLE_EXACT_SAMPLE_AUTHORITY_UNPROVEN',True)
