"""Actual D0 SQLite T1 writes on the canonical Research roster.
Uses original admission/ordinary mappings and company decorator, not the 0220
pinned-history admission wrapper or 0221 result/authority fence. No PG acceptance.
"""
from contextlib import closing
from dataclasses import replace
import sqlite3
import unittest
import test_research_company_snapshot_0224 as prior
from app.core.agent_runtime.lifecycle import RunState, LeaseObservation, ClockSample
from app.core.agent_runtime.postgres_run import PostgresRunRepository
from app.core.agent_runtime.transition_command import transition_digest
from app.core.orchestrator.engine import canonical_plan
from app.core.development_review.research_slice import RESEARCH_REVISION, review_research_roster
from app.core.event_store.company_coordination import CompanyEvent, CompanyCoordinatedMapping
from app.core.transaction.postgres_admission_mapping import (SampleBudget, ClaimSpec, claim_digest,
    D0PostgresAdmissionMapping, reconcile_admission)
from app.core.transaction.postgres_transition_mapping import D0PostgresTransitionMapping, transaction_ref
from app.core.transaction.transition_reconciliation import reconcile_transition
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction, CommitOutcomeUnknown
from app.core.transaction.review import LogicalIntent, Operation


class SQLiteCursor:
    def __init__(self, db): self.cursor=db.cursor()
    def __enter__(self): return self
    def __exit__(self,*args): self.cursor.close()
    def execute(self,sql,params=()):
        return self.cursor.execute(sql.replace('t1_candidate.','').replace(' FOR UPDATE','').replace('%s','?'),params)
    def fetchone(self): return self.cursor.fetchone()


class SQLiteConnection:
    autocommit=False
    def __init__(self,path,unknown=False):
        self.db=sqlite3.connect(path,timeout=1); self.unknown=unknown
        self.db.execute('PRAGMA foreign_keys=ON'); self.db.execute('BEGIN IMMEDIATE')
    def cursor(self): return SQLiteCursor(self.db)
    def commit(self):
        self.db.commit()
        if self.unknown: raise OSError('simulated lost response after commit')
    def rollback(self): self.db.rollback()
    def close(self): self.db.close()


class ResearchT1IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.f=prior.ResearchCompanySnapshotTests(); self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.root=next(r for r in self.f.initial if r.scope.task_id=='plan')
        self.budget=SampleBudget('sample-budget',0,'USD',100,0,0,False,2,3,'a'*64)
        self.clock=ClockSample(10,2,3,5)
        self.spec=self.spec_for(self.root)
        self.intent=self.admit_intent(self.spec)

    def spec_for(self,run):
        t=run.scope.task_id
        lease=LeaseObservation(run.scope,'lease-'+t,'grant-'+t,1,0,1,2,3,20,10)
        return ClaimSpec(run,'admission-'+t,lease,self.budget,20,canonical_plan(self.f.plan)['digest'])
    def admit_intent(self,spec):
        t=spec.before.scope.task_id; l=spec.lease
        return LogicalIntent(spec.before.scope,Operation.ADMISSION,spec.before.version,claim_digest(spec),
            'admit-'+t,'idem-admit-'+t,l.grant_id,l.lease_id,spec.budget.budget_id,2,3)
    def event(self,i,kind,budget_revision=None,amount=0):
        return CompanyEvent(len(self.f.events)+1,self.f.project,i.scope.run_id,i.expected_version+1,
            transaction_ref(i),i.request_digest,kind,() if not self.f.events else (self.f.events[-1].transaction_ref,),budget_revision,amount)
    def coordinator(self,mapping,event,unknown=False):
        wrapper=CompanyCoordinatedMapping(mapping,self.f.members,self.f.pool,self.f.events,event)
        return LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnection(self.f.path,unknown),wrapper))
    def dump(self):
        with closing(sqlite3.connect(self.f.path)) as db:
            return tuple((t,tuple(db.execute('SELECT * FROM '+t+' ORDER BY 1,2,3').fetchall()))
                for t, in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall())
    def read(self,fn):
        with closing(sqlite3.connect(self.f.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            with SQLiteCursor(db) as c: return fn(c)
    def observe(self):
        runs=self.read(lambda c:tuple(PostgresRunRepository().read(c,r.scope) for r in self.f.initial))
        return review_research_roster(self.f.plan,RESEARCH_REVISION,self.f.project,self.f.initial,runs)
    def admit(self,spec=None,intent=None,mapping=None,unknown=False):
        spec=spec or self.spec; intent=intent or self.admit_intent(spec)
        e=self.event(intent,'D0_RUN_ADMISSION',spec.budget.revision,spec.amount_minor)
        m=mapping or D0PostgresAdmissionMapping(self.f.plan,spec,lambda:self.clock)
        receipt=self.coordinator(m,e,unknown).commit(intent)
        self.f.events+=(e,)
        return receipt
    def ordinary(self,before,target,*,mapping=None,unknown=False):
        l=self.spec.lease
        i=LogicalIntent(before.scope,Operation.STATE_MUTATION,before.version,transition_digest(before,target),
            'step-'+str(before.version),'idem-step-'+str(before.version),l.grant_id,l.lease_id,None,2,3)
        e=self.event(i,'D0_RUN_TRANSITION'); m=mapping or D0PostgresTransitionMapping(l,lambda:replace(self.clock,now_tick=11))
        receipt=self.coordinator(m,e,unknown).commit_transition(i,before,target)
        self.f.events+=(e,)
        return i,receipt,replace(before,state=target,version=receipt.committed_version)
    def test_actual_admission_nine_roles_company_readback(self):
        self.assertEqual(self.observe().ready,('plan',)); receipt=self.admit()
        self.assertEqual(receipt.committed_version,1)
        r=self.f.read(); self.assertTrue(r.structural_match); self.assertEqual((r.event_count,r.outstanding_minor),(1,20))
        a=self.read(lambda c:reconcile_admission(c,self.f.plan,self.spec,self.intent))
        self.assertTrue(a.exact_sample_match); self.assertFalse(a.retry_allowed or a.dispatch_allowed or a.committed)
        self.assertEqual(self.observe().root_state,'ADMITTED'); self.assertEqual(self.observe().ready,())
    def test_actual_three_step_prefix_and_reopen(self):
        self.admit(); admitted=replace(self.root,state=RunState.ADMITTED,version=1)
        _,_,running=self.ordinary(admitted,RunState.RUNNING)
        i,receipt,verifying=self.ordinary(running,RunState.VERIFYING)
        self.assertEqual((receipt.committed_version,verifying.state),(3,RunState.VERIFYING))
        self.assertEqual((self.observe().root_state,self.observe().ready),('VERIFYING',()))
        self.assertTrue(self.f.read().structural_match); self.assertEqual(self.f.read().event_count,3)
        r=self.read(lambda c:reconcile_transition(c,i,running,RunState.VERIFYING,self.spec.lease))
        self.assertTrue(r.exact_sample_match); self.assertFalse(r.retry_allowed or r.committed)
        counts=self.read(lambda c:tuple((c.execute('SELECT count(*) FROM t1_candidate.'+t),c.fetchone()[0])[1]
            for t in ('run_mutations','events','outbox','fences','run_audit','company_event_order')))
        self.assertEqual(counts,(3,3,3,3,3,3))
    def test_admission_rollback_every_role(self):
        before=self.dump()
        for fail in ('HEAD','ADMISSION','LEASE','BUDGET','MUTATION','FENCE','EVENT','OUTBOX','AUDIT'):
            with self.subTest(role=fail):
                class Broken(D0PostgresAdmissionMapping):
                    def write_role(self,c,r,i):
                        super().write_role(c,r,i)
                        if r==fail: raise RuntimeError('injected rollback')
                with self.assertRaisesRegex(RuntimeError,'injected rollback'):
                    self.admit(mapping=Broken(self.f.plan,self.spec,lambda:self.clock))
                self.assertEqual(self.dump(),before)
    def test_ordinary_rollback_every_role(self):
        self.admit(); before=self.dump(); admitted=replace(self.root,state=RunState.ADMITTED,version=1)
        for fail in ('HEAD','MUTATION','FENCE','EVENT','OUTBOX','AUDIT'):
            with self.subTest(role=fail):
                class Broken(D0PostgresTransitionMapping):
                    def write_transition_role(self,c,r,i,b,t):
                        super().write_transition_role(c,r,i,b,t)
                        if r==fail: raise RuntimeError('injected rollback')
                with self.assertRaisesRegex(RuntimeError,'injected rollback'):
                    self.ordinary(admitted,RunState.RUNNING,mapping=Broken(self.spec.lease,lambda:self.clock))
                self.assertEqual(self.dump(),before)
    def test_dependency_rejected_no_write(self):
        child=next(r for r in self.f.initial if r.scope.task_id=='research'); before=self.dump()
        with self.assertRaisesRegex(ValueError,'NOT_READY'): self.admit(spec=self.spec_for(child))
        self.assertEqual(self.dump(),before)
    def test_budget_rejected_no_write(self):
        before=self.dump()
        with self.assertRaises(ValueError): self.admit(spec=replace(self.spec,amount_minor=101))
        self.assertEqual(self.dump(),before)
    def test_wrong_digest_no_write(self):
        before=self.dump()
        with self.assertRaisesRegex(ValueError,'BINDING_HOLD'): self.admit(intent=replace(self.intent,request_digest='0'*64))
        self.assertEqual(self.dump(),before)
    def test_company_member_drift_no_write(self):
        self.f.change("UPDATE company_run_membership SET principal_id='demo-forged' WHERE task_id='plan'")
        before=self.dump()
        with self.assertRaisesRegex(ValueError,'PREIMAGE_HOLD'): self.admit()
        self.assertEqual(self.dump(),before)
    def test_unknown_commit_no_automatic_retry(self):
        e=self.event(self.intent,'D0_RUN_ADMISSION',0,20)
        with self.assertRaises(CommitOutcomeUnknown): self.admit(unknown=True)
        self.f.events+=(e,); before=self.dump()
        self.assertTrue(self.f.read().structural_match)
        r=self.read(lambda c:reconcile_admission(c,self.f.plan,self.spec,self.intent))
        self.assertTrue(r.exact_sample_match); self.assertFalse(r.retry_allowed)
        with self.assertRaises(ValueError): self.admit()
        self.assertEqual(self.dump(),before)
    def test_expired_lease_no_write(self):
        self.admit(); before=self.dump(); admitted=replace(self.root,state=RunState.ADMITTED,version=1)
        with self.assertRaisesRegex(ValueError,'LEASE_EXPIRED'):
            self.ordinary(admitted,RunState.RUNNING,mapping=D0PostgresTransitionMapping(self.spec.lease,lambda:replace(self.clock,now_tick=20)))
        self.assertEqual(self.dump(),before)
    def test_success_transition_blocked(self):
        self.admit(); admitted=replace(self.root,state=RunState.ADMITTED,version=1)
        _,_,running=self.ordinary(admitted,RunState.RUNNING); _,_,verifying=self.ordinary(running,RunState.VERIFYING)
        before=self.dump()
        with self.assertRaisesRegex(PermissionError,'SPECIAL_TRANSITION_HOLD'): self.ordinary(verifying,RunState.SUCCEEDED)
        self.assertEqual(self.dump(),before)
    def test_audit_tamper_reconciliation_hold(self):
        self.admit(); admitted=replace(self.root,state=RunState.ADMITTED,version=1)
        i,_,_=self.ordinary(admitted,RunState.RUNNING)
        self.f.change("UPDATE run_audit SET lease_digest='forged' WHERE version=2")
        r=self.read(lambda c:reconcile_transition(c,i,admitted,RunState.RUNNING,self.spec.lease))
        self.assertFalse(r.exact_sample_match or r.retry_allowed)
