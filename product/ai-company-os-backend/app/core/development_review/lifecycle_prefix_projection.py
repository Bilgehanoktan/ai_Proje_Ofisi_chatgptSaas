"""Read-only exact fixed-chain prefix profile; no general active runtime API."""
from dataclasses import replace
from app.core.development_review.d0_snapshot import open_d0_snapshot
from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.postgres_run import PostgresRunRepository
from app.core.transaction.postgres_admission_mapping import D0PostgresAdmissionMapping
from app.core.transaction.postgres_lifecycle_mapping import verify_admission_binding
from app.core.transaction.postgres_transition_mapping import transaction_ref, lease_digest, _key, _lease, _KEY
from app.core.development_review.lifecycle_projection import fixed_chain, _exact
from app.core.development_review.lifecycle_prefix_wire import prefix_wire, PLAN_REVISION

def read_lifecycle_prefix(path):
    terminal,ti,chain=fixed_chain()
    binding=terminal.binding; admission=chain[0][0]; k=_key(admission)
    if admission.scope.plan_revision!=PLAN_REVISION: raise ValueError('D0_PREFIX_PLAN_HOLD')
    with open_d0_snapshot(path,'lifecycle-prefix.d0.sqlite') as c:
        head=PostgresRunRepository().read(c,admission.scope)
        wire=prefix_wire(head.version)
        if head!=replace(binding.claim.before,state=RunState(wire['state']),version=wire['head_version']):
            raise ValueError('D0_PREFIX_HEAD_HOLD')
        selected=chain[:head.version]; lease=selected[-1][4]
        if _lease(c,admission)!=lease:
            raise ValueError('D0_PREFIX_LEASE_HOLD')
        verify_admission_binding(c,admission,binding,lease)
        expected_budget=replace(binding.claim.budget,revision=wire['sample_budget_revision'],outstanding_minor=wire['sample_outstanding_minor'])
        if D0PostgresAdmissionMapping(None,None,None)._budget(c,admission)!=expected_budget:
            raise ValueError('D0_PREFIX_BUDGET_HOLD')
        for i,kind,before,after,l in selected:
            tx=transaction_ref(i);v=i.expected_version+1;suffix=' WHERE '+_KEY+' AND version=%s'
            for sql,params,expected in (
                ('SELECT transaction_ref,request_digest,before_state,after_state,attempt FROM t1_candidate.run_mutations'+suffix,(*k,v),(tx,i.request_digest,before,after,0)),
                ('SELECT event_id,event_type,request_digest FROM t1_candidate.events'+suffix,(*k,v),(tx,kind,i.request_digest)),
                ('SELECT event_id,request_digest FROM t1_candidate.outbox WHERE '+_KEY+' AND event_id=%s',(*k,tx),(tx,i.request_digest)),
                ('SELECT effect_key,idempotency_key,request_digest FROM t1_candidate.fences WHERE tenant_id=%s AND company_id=%s AND environment_id=%s AND (effect_key=%s OR idempotency_key=%s)',(*k[:3],i.effect_key,i.idempotency_key),(i.effect_key,i.idempotency_key,i.request_digest)),
                ('SELECT transaction_ref,request_digest,effect_key,idempotency_key,grant_ref,lease_ref,policy_epoch,witness_epoch,lease_fence,lease_digest FROM t1_candidate.run_audit'+suffix,(*k,v),(tx,i.request_digest,i.effect_key,i.idempotency_key,i.grant_ref,i.lease_ref,i.policy_epoch,i.witness_epoch,l.fence,lease_digest(l)))
            ): _exact(c,sql,params,expected)
        for table,count in (('run_mutations',head.version),('events',head.version),('outbox',head.version),('run_audit',head.version),('run_lease_renewals',int(head.version>=3)),('sample_settlements',0),('run_admissions',1),('sample_reservations',1),('run_leases',1)):
            _exact(c,'SELECT count(*) FROM t1_candidate.'+table+' WHERE '+_KEY,k,(count,))
    return wire
