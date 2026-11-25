"""D0 SQLite actual transaction tests; no PostgreSQL or live execution."""
import unittest
import sqlite3
from contextlib import closing
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import test_admission_mapping_0195 as base
from test_transition_mapping_0194 import SQLiteConnectionShim, SQLiteCursorShim
from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.transition_command import commit_transition, transition_digest
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction, CommitOutcomeUnknown
from app.core.transaction.postgres_lifecycle_mapping import (AdmissionBinding,LifecycleSpec,
    D0AdmissionBoundTransitionMapping,D0PostgresLifecycleMapping,lifecycle_digest,reconcile_lifecycle,FAILURE)

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        # Reuse 0195 fixture without inheriting its test methods.
        fixture=base.ClaimTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        self.f=fixture; self.path=fixture.path
        with closing(sqlite3.connect(self.path)) as db,db:
            db.executescript((base.ROOT/'database/0196L/candidate_lease_settlement.sql').read_text().replace('t1_candidate.',''))
        self.claim=base.spec_for(); self.claim_i=base.intent_for(self.claim)
        receipt=fixture.claim(self.claim); self.binding=AdmissionBinding(self.claim,self.claim_i)
        self.before=replace(self.claim.before,state=RunState.ADMITTED,version=receipt.committed_version)
        self.lease=self.claim.lease; self.budget=replace(self.claim.budget,revision=1,outstanding_minor=self.claim.amount_minor)
        self.clock=replace(base.CLOCK,now_tick=11)
    def coordinator(self,mapping,unknown=False):
        return LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnectionShim(self.path,unknown),mapping))
    def ordinary(self,before=None,lease=None,target=RunState.RUNNING,clock=None,binding=None):
        before=before or self.before;lease=lease or self.lease;clock=clock or self.clock
        i=LogicalIntent(before.scope,Operation.STATE_MUTATION,before.version,transition_digest(before,target),'ordinary-'+str(before.version),'ordinary-idem-'+str(before.version),lease.grant_id,lease.lease_id,None,lease.policy_epoch,lease.witness_epoch)
        return commit_transition(self.coordinator(D0AdmissionBoundTransitionMapping(binding or self.binding,lease,lambda:clock)),before,target,i)
    def renewal(self,before=None,lease=None,budget=None,clock=None):
        before=before or self.before;lease=lease or self.lease;budget=budget or self.budget;clock=clock or self.clock
        n=replace(lease,lease_version=lease.lease_version+1,heartbeat_revision=lease.heartbeat_revision+1,heartbeat_tick=clock.now_tick,expires_tick=clock.now_tick+20)
        return LifecycleSpec(before,lease,self.binding,budget,n)
    def failure(self,before=None,lease=None,budget=None):
        return LifecycleSpec(before or self.before,lease or self.lease,self.binding,budget or self.budget,outcome=FAILURE)
    def intent(self,s,operation=None):
        l=s.lease; v=s.before.version
        op=operation or (Operation.STATE_MUTATION if s.renewal else Operation.TERMINAL)
        return LogicalIntent(s.before.scope,op,v,lifecycle_digest(s),'lifecycle-'+str(v),'lifecycle-idem-'+str(v),l.grant_id,l.lease_id,s.budget.budget_id,l.policy_epoch,l.witness_epoch,True)
    def execute(self,s,i=None,clock=None,mapping=None,unknown=False):
        return self.coordinator(mapping or D0PostgresLifecycleMapping(s,clock or (lambda:self.clock)),unknown).commit(i or self.intent(s))
    def dump(self):
        with closing(sqlite3.connect(self.path)) as db:
            return tuple((t,tuple(db.execute('SELECT * FROM '+t+' ORDER BY 1,2,3,4').fetchall())) for t in ('run_heads','run_leases','run_admissions','sample_budgets','sample_reservations','run_mutations','fences','events','outbox','run_audit','run_lease_renewals','sample_settlements'))
    def row(self,sql):
        with closing(sqlite3.connect(self.path)) as db: return db.execute(sql).fetchall()
    def running(self):
        r=self.ordinary();return replace(self.before,state=RunState.RUNNING,version=r.committed_version)
    def reconcile(self,s,i=None):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            with SQLiteCursorShim(db) as c: return reconcile_lifecycle(c,s,i or self.intent(s))
    def test_full_chain(self):
        running=self.running();s=self.renewal(running);r=self.execute(s)
        self.assertEqual(self.row('SELECT lease_version,heartbeat_revision,fence,heartbeat_tick FROM run_leases'),[(2,1,1,11)])
        self.assertEqual(self.row('SELECT revision,outstanding_minor FROM sample_budgets'),[(2,20)])
        running=replace(running,version=r.committed_version);b=replace(self.budget,revision=2)
        verifying=self.ordinary(running,s.renewal,RunState.VERIFYING)
        terminal=self.failure(replace(running,state=RunState.VERIFYING,version=verifying.committed_version),s.renewal,b)
        self.execute(terminal)
        self.assertEqual(self.row("SELECT state FROM run_heads WHERE task_id='a'"),[('FAILED',)])
        self.assertEqual(self.row('SELECT * FROM run_leases'),[])
        self.assertEqual(self.row('SELECT revision,outstanding_minor,recognized_cost_minor FROM sample_budgets'),[(3,0,0)])
        self.assertEqual(self.row('SELECT released_minor,recognized_minor,outcome FROM sample_settlements'),[(20,0,FAILURE)])
        self.assertEqual(self.row('SELECT amount_minor FROM sample_reservations'),[(20,)])
        self.assertTrue(self.reconcile(terminal).exact_sample_match)
    def test_renewal_history_two(self):
        first=self.renewal();r=self.execute(first);nextclock=replace(self.clock,now_tick=12)
        second=self.renewal(replace(self.before,version=r.committed_version),first.renewal,replace(self.budget,revision=2),nextclock)
        rr=self.execute(second,clock=lambda:nextclock)
        self.assertEqual(self.row('SELECT lease_version FROM run_lease_renewals ORDER BY lease_version'),[(2,),(3,)])
        self.ordinary(replace(self.before,version=rr.committed_version),second.renewal,clock=nextclock)
    def test_renewal_rollback_each_role(self):
        s=self.renewal();old=self.dump()
        for fail in ('HEAD','LEASE','BUDGET','MUTATION','FENCE','EVENT','OUTBOX','AUDIT'):
            with self.subTest(role=fail):
                class Broken(D0PostgresLifecycleMapping):
                    def write_role(self,c,r,i):
                        super().write_role(c,r,i)
                        if r==fail:raise RuntimeError('injected')
                with self.assertRaisesRegex(RuntimeError,'injected'):self.execute(s,mapping=Broken(s,lambda:self.clock))
                self.assertEqual(self.dump(),old)
    def test_terminal_rollback_each_role(self):
        s=self.failure(self.running());old=self.dump()
        for fail in ('HEAD','LEASE','BUDGET','MUTATION','FENCE','EVENT','OUTBOX','AUDIT'):
            with self.subTest(role=fail):
                class Broken(D0PostgresLifecycleMapping):
                    def write_role(self,c,r,i):
                        super().write_role(c,r,i)
                        if r==fail:raise RuntimeError('injected')
                with self.assertRaisesRegex(RuntimeError,'injected'):self.execute(s,mapping=Broken(s,lambda:self.clock))
                self.assertEqual(self.dump(),old)
    def test_renewal_fence_change(self):
        s=self.renewal();old=self.dump();s=replace(s,renewal=replace(s.renewal,fence=2))
        with self.assertRaisesRegex(ValueError,'RENEWAL_BINDING'):self.execute(s)
        self.assertEqual(self.dump(),old)
    def test_renewal_expired_precommit(self):
        s=self.renewal();old=self.dump();clocks=iter((self.clock,replace(self.clock,now_tick=20)))
        with self.assertRaisesRegex(ValueError,'LEASE_EXPIRED'):self.execute(s,clock=lambda:next(clocks))
        self.assertEqual(self.dump(),old)
    def test_renewal_wa_change(self):
        s=self.renewal();old=self.dump();clocks=iter((self.clock,replace(self.clock,witness_epoch=4)))
        with self.assertRaisesRegex(ValueError,'WA_EPOCH_STALE'):self.execute(s,clock=lambda:next(clocks))
        self.assertEqual(self.dump(),old)
    def test_renewal_bounded(self):
        s=self.renewal();s=replace(s,renewal=replace(s.renewal,expires_tick=1000))
        with self.assertRaisesRegex(ValueError,'RENEWAL_BINDING'):self.execute(s)
    def test_renewal_not_backdated(self):
        s=self.renewal();s=replace(s,renewal=replace(s.renewal,heartbeat_tick=12))
        with self.assertRaisesRegex(ValueError,'RENEWAL_CLOCK'):self.execute(s)
    def test_terminal_unknown_cost(self):
        running=self.running();self.f.update('UPDATE sample_budgets SET unknown_cost=true');old=self.dump()
        with self.assertRaisesRegex(ValueError,'BINDING_HOLD'):self.execute(self.failure(running,budget=replace(self.budget,unknown_cost=True)))
        self.assertEqual(self.dump(),old)
    def test_terminal_no_success(self):
        s=replace(self.failure(self.running()),outcome='SUCCEEDED');old=self.dump()
        with self.assertRaisesRegex(PermissionError,'FAILURE_ONLY'):self.execute(s)
        self.assertEqual(self.dump(),old)
    def test_terminal_no_unknown(self):
        s=replace(self.failure(self.running()),outcome='UNKNOWN');old=self.dump()
        with self.assertRaisesRegex(PermissionError,'FAILURE_ONLY'):self.execute(s)
        self.assertEqual(self.dump(),old)
    def test_terminal_no_cancel(self):
        s=replace(self.failure(self.running()),outcome='CANCELLED');old=self.dump()
        with self.assertRaisesRegex(PermissionError,'FAILURE_ONLY'):self.execute(s)
        self.assertEqual(self.dump(),old)
    def test_ordinary_missing_admission_binding(self):
        self.f.update("UPDATE run_admissions SET grant_id='wrong'");old=self.dump()
        with self.assertRaisesRegex(ValueError,'READBACK_HOLD'):self.ordinary()
        self.assertEqual(self.dump(),old)
    def test_ordinary_tampered_initial_audit(self):
        self.f.update("UPDATE run_audit SET lease_digest='wrong'");old=self.dump()
        with self.assertRaisesRegex(ValueError,'READBACK_HOLD'):self.ordinary()
        self.assertEqual(self.dump(),old)
    def test_ordinary_tampered_renewal_history(self):
        s=self.renewal();r=self.execute(s);self.f.update("UPDATE run_lease_renewals SET old_lease_digest='wrong'");old=self.dump()
        with self.assertRaisesRegex(ValueError,'HISTORY_HOLD'):self.ordinary(replace(self.before,version=r.committed_version),s.renewal)
        self.assertEqual(self.dump(),old)
    def test_ordinary_renewal_outbox_missing(self):
        s=self.renewal();r=self.execute(s);self.f.update("DELETE FROM outbox WHERE event_id IN (SELECT event_id FROM events WHERE event_type='D0_LEASE_RENEWAL')")
        with self.assertRaisesRegex(ValueError,'READBACK_HOLD'):self.ordinary(replace(self.before,version=r.committed_version),s.renewal)
    def test_terminal_budget_source_changed(self):
        running=self.running();self.f.update("UPDATE sample_budgets SET source_digest='"+'b'*64+"'");old=self.dump()
        with self.assertRaisesRegex(ValueError,'BUDGET_HOLD'):self.execute(self.failure(running,budget=replace(self.budget,source_digest='b'*64)))
        self.assertEqual(self.dump(),old)
    def test_terminal_wrong_reservation(self):
        running=self.running();self.f.update('UPDATE sample_reservations SET amount_minor=19');old=self.dump()
        with self.assertRaisesRegex(ValueError,'READBACK_HOLD'):self.execute(self.failure(running))
        self.assertEqual(self.dump(),old)
    def test_terminal_duplicate(self):
        s=self.failure(self.running());self.execute(s);old=self.dump()
        with self.assertRaisesRegex(ValueError,'HEAD_CAS_HOLD'):self.execute(s)
        self.assertEqual(self.dump(),old)
    def test_unknown_terminal_readback(self):
        s=self.failure(self.running())
        with self.assertRaises(CommitOutcomeUnknown):self.execute(s,unknown=True)
        r=self.reconcile(s);self.assertTrue(r.exact_sample_match);self.assertFalse(r.retry_allowed);self.assertFalse(r.committed);self.assertFalse(r.dispatch_allowed)
        self.f.update("UPDATE sample_settlements SET lease_digest='wrong'");self.assertFalse(self.reconcile(s).exact_sample_match)
    def test_unknown_renewal_readback(self):
        s=self.renewal()
        with self.assertRaises(CommitOutcomeUnknown):self.execute(s,unknown=True)
        r=self.reconcile(s);self.assertTrue(r.exact_sample_match);self.assertFalse(r.retry_allowed)
    def test_parallel_renewal_one_winner(self):
        s=self.renewal();barrier=Barrier(2,timeout=3)
        def compete(_):
            barrier.wait()
            try:self.execute(s);return 'COMMIT'
            except ValueError as e:return str(e)
        with ThreadPoolExecutor(max_workers=2) as p:result=list(p.map(compete,range(2)))
        self.assertCountEqual(result,['COMMIT','D0_HEAD_CAS_HOLD'])
    def test_parallel_renew_vs_failure(self):
        running=self.running();specs=(self.renewal(running),self.failure(running));barrier=Barrier(2,timeout=3)
        def compete(s):
            barrier.wait()
            try:self.execute(s);return 'COMMIT'
            except ValueError as e:return str(e)
        with ThreadPoolExecutor(max_workers=2) as p:result=list(p.map(compete,specs))
        self.assertCountEqual(result,['COMMIT','D0_HEAD_CAS_HOLD'])
    def test_terminal_budget_cas(self):
        s=self.failure(self.running());self.f.update('UPDATE sample_budgets SET revision=revision+1');old=self.dump()
        with self.assertRaisesRegex(ValueError,'BUDGET_HOLD'):self.execute(s)
        self.assertEqual(self.dump(),old)
    def test_renewal_stale_clock(self):
        s=self.renewal();old=self.dump();clocks=iter((self.clock,replace(self.clock,now_tick=10)))
        with self.assertRaisesRegex(ValueError,'CLOCK_REGRESSION'):self.execute(s,clock=lambda:next(clocks))
        self.assertEqual(self.dump(),old)

if __name__=='__main__': unittest.main()
