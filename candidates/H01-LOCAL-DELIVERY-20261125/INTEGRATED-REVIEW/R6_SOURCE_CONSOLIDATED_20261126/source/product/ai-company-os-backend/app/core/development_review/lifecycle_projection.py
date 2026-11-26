"""W1-0198-P02 fixed 0196-L terminal readback; no writes, no live clock or grant."""
from dataclasses import replace
from app.core.development_review.lifecycle_read_snapshot import lifecycle_snapshot, require_single_head
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, LeaseObservation
from app.core.agent_runtime.transition_command import transition_digest
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.postgres_admission_mapping import SampleBudget, ClaimSpec, claim_digest
from app.core.transaction.postgres_lifecycle_mapping import AdmissionBinding, LifecycleSpec, lifecycle_digest, reconcile_lifecycle, FAILURE
from app.core.transaction.postgres_transition_mapping import transaction_ref, lease_digest, _key, _one, _KEY

PLAN_REVISION = 'sha256:c75ec1070786538f38bdccdcf6a75de62a9e02e9bcb7e4a4bb9df5f7e96638a0'

def fixed_chain():
    scope = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',PLAN_REVISION,'a','demo-a','demo-agent','demo-principal')
    before = RunObservation(scope,RunState.QUEUED,0,0)
    lease = LeaseObservation(scope,'lease-a','grant-a',1,0,1,2,3,20,10)
    budget = SampleBudget('sample-budget',0,'USD',100,0,0,False,2,3,'a'*64)
    claim = ClaimSpec(before,'admission-a',lease,budget,20,PLAN_REVISION.removeprefix('sha256:'))
    admission = LogicalIntent(scope,Operation.ADMISSION,0,claim_digest(claim),'effect-a','idem-a','grant-a','lease-a','sample-budget',2,3)
    binding = AdmissionBinding(claim,admission)
    admitted = replace(before,state=RunState.ADMITTED,version=1)
    running = replace(admitted,state=RunState.RUNNING,version=2)
    renewed = replace(lease,lease_version=2,heartbeat_revision=1,heartbeat_tick=11,expires_tick=31)
    b1 = replace(budget,revision=1,outstanding_minor=20)
    renew = LifecycleSpec(running,lease,binding,b1,renewed)
    ri = LogicalIntent(scope,Operation.STATE_MUTATION,2,lifecycle_digest(renew),'lifecycle-2','lifecycle-idem-2','grant-a','lease-a','sample-budget',2,3,True)
    running3 = replace(running,version=3)
    verifying = replace(running3,state=RunState.VERIFYING,version=4)
    terminal = LifecycleSpec(verifying,renewed,binding,replace(b1,revision=2),outcome=FAILURE)
    ti = LogicalIntent(scope,Operation.TERMINAL,4,lifecycle_digest(terminal),'lifecycle-4','lifecycle-idem-4','grant-a','lease-a','sample-budget',2,3,True)
    def ordinary(b,target):
        return LogicalIntent(scope,Operation.STATE_MUTATION,b.version,transition_digest(b,target),'ordinary-'+str(b.version),'ordinary-idem-'+str(b.version),'grant-a','lease-a',None,2,3)
    return terminal,ti,((admission,'D0_RUN_ADMISSION','QUEUED','ADMITTED',lease),(ordinary(admitted,RunState.RUNNING),'D0_RUN_TRANSITION','ADMITTED','RUNNING',lease),(ri,'D0_LEASE_RENEWAL','RUNNING','RUNNING',renewed),(ordinary(running3,RunState.VERIFYING),'D0_RUN_TRANSITION','RUNNING','VERIFYING',renewed),(ti,'D0_RUN_FAILURE','VERIFYING','FAILED',renewed))

class ReadCursor:
    """Narrow SELECT-only SQLite dialect for the candidate mapping."""
    def __init__(self,db): self.cursor=db.cursor()
    def execute(self,sql,params=()):
        if not sql.startswith('SELECT ') or ';' in sql or 'FOR UPDATE' in sql:
            raise ValueError('D0_LIFECYCLE_SELECT_ONLY')
        return self.cursor.execute(sql.replace('t1_candidate.','').replace('%s','?'),params)
    def fetchone(self): return self.cursor.fetchone()

def _exact(c,sql,params,expected):
    if _one(c,sql,params)!=expected: raise ValueError('D0_LIFECYCLE_PROJECTION_HOLD')

def read_lifecycle_projection(path):
    terminal,ti,chain=fixed_chain()
    k=_key(ti)
    with lifecycle_snapshot(path,'lifecycle.d0.sqlite') as db:
        c=ReadCursor(db)
        require_single_head(c,k)
        if not reconcile_lifecycle(c,terminal,ti).exact_sample_match:
            raise ValueError('D0_LIFECYCLE_PROJECTION_HOLD')
        # Reconciliation checks admission, renewal history and terminal postimage.
        # Pin every ordinary mutation plus each expected transaction against persisted rows.
        for i,kind,before,after,lease in chain:
            tx=transaction_ref(i);v=i.expected_version+1; suffix=' WHERE '+_KEY+' AND version=%s'
            for sql,params,expected in (
                ('SELECT transaction_ref,request_digest,before_state,after_state,attempt FROM t1_candidate.run_mutations'+suffix,(*k,v),(tx,i.request_digest,before,after,0)),
                ('SELECT event_id,event_type,request_digest FROM t1_candidate.events'+suffix,(*k,v),(tx,kind,i.request_digest)),
                ('SELECT event_id,request_digest FROM t1_candidate.outbox WHERE '+_KEY+' AND event_id=%s',(*k,tx),(tx,i.request_digest)),
                ('SELECT effect_key,idempotency_key,request_digest FROM t1_candidate.fences WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND (effect_key=%s OR idempotency_key=%s)',(*k[:3],i.effect_key,i.idempotency_key),(i.effect_key,i.idempotency_key,i.request_digest)),
                ('SELECT transaction_ref,request_digest,effect_key,idempotency_key,grant_ref,lease_ref,policy_epoch,witness_epoch,lease_fence,lease_digest FROM t1_candidate.run_audit'+suffix,(*k,v),(tx,i.request_digest,i.effect_key,i.idempotency_key,i.grant_ref,i.lease_ref,i.policy_epoch,i.witness_epoch,lease.fence,lease_digest(lease)))
            ): _exact(c,sql,params,expected)
        for table,count in (('run_mutations',5),('events',5),('outbox',5),('run_audit',5),('run_lease_renewals',1),('sample_settlements',1),('run_admissions',1),('sample_reservations',1),('run_leases',0)):
            _exact(c,'SELECT count(*) FROM t1_candidate.'+table+' WHERE '+_KEY,k,(count,))
    # Fixed data is emitted only after the complete exact sample readback.
    return {"schema_version":"lifecycle.projection.v1-D0","mode":"D0_LIFECYCLE_0196L_TERMINAL_FIXTURE","tenant":"synthetic-tenant","company":"synthetic-company","environment":"A0_SAMPLE_ONLY","plan_revision":"sha256:c75ec1070786538f38bdccdcf6a75de62a9e02e9bcb7e4a4bb9df5f7e96638a0","task_id":"a","run_id":"demo-a","head_version":5,"attempt":0,"state":"FAILED","timeline":[{"version":1,"kind":"D0_RUN_ADMISSION","state":"ADMITTED"},{"version":2,"kind":"D0_RUN_TRANSITION","state":"RUNNING"},{"version":3,"kind":"D0_LEASE_RENEWAL","state":"RUNNING"},{"version":4,"kind":"D0_RUN_TRANSITION","state":"VERIFYING"},{"version":5,"kind":"D0_RUN_FAILURE","state":"FAILED"}],"lease_version":2,"heartbeat_revision":1,"lease_active":False,"sample_reserved_minor":20,"sample_released_minor":20,"sample_recognized_minor":0,"sample_budget_revision":3,"currency":"USD","freshness":"HISTORICAL_SAMPLE","causality":"EXACT_FIXED_SAMPLE_ONLY","geometry_join":"HOLD","independent_acceptance":"HOLD","decision":"HOLD","dispatch_allowed":False,"provider_called":False,"spend_allowed":False,"release_ready":False,"authoritative":False,"real_run_count":None}
