"""Actual disposable SQLite via 0194 dialect shim; no PostgreSQL or provider."""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import sqlite3
import tempfile
import unittest
from test_transition_mapping_0194 import PLAN, obs, SQLiteConnectionShim, SQLiteCursorShim
from app.core.agent_runtime.lifecycle import LeaseObservation, ClockSample, RunState
from app.core.agent_runtime.transition_command import commit_transition, transition_digest
from app.core.orchestrator.engine import canonical_plan
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction, CommitOutcomeUnknown
from app.core.transaction.postgres_admission_mapping import D0PostgresAdmissionMapping, SampleBudget, ClaimSpec, claim_digest, reconcile_admission
from app.core.transaction.postgres_transition_mapping import D0PostgresTransitionMapping

ROOT=Path(__file__).resolve().parents[3]
CLOCK=ClockSample(10,2,3,5)
BUDGET=SampleBudget('sample-budget',0,'USD',100,0,0,False,2,3,'a'*64)

def spec_for(task='a',budget=BUDGET,amount=20):
    before=obs(task); lease=LeaseObservation(before.scope,'lease-'+task,'grant-'+task,1,0,1,2,3,20,10)
    return ClaimSpec(before,'admission-'+task,lease,budget,amount,canonical_plan(PLAN)['digest'])

def intent_for(s):
    return LogicalIntent(s.before.scope,Operation.ADMISSION,s.before.version,claim_digest(s),'effect-'+s.before.scope.task_id,'idem-'+s.before.scope.task_id,s.lease.grant_id,s.lease.lease_id,s.budget.budget_id,2,3)

class ClaimTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'test.d0.sqlite'
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('PRAGMA foreign_keys=ON')
            for f in ('0192/candidate_event_outbox_fence.sql','0193/candidate_run_head.sql','0194/candidate_transition_roles.sql','0195/candidate_admission_budget.sql'):
                db.executescript((ROOT/'database'/f).read_text().replace('CREATE SCHEMA t1_candidate;','').replace('t1_candidate.',''))
            for t in 'abcq':
                r=obs(t); s=r.scope
                db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',(s.tenant_id,s.company_id,s.environment_id,s.plan_revision,s.task_id,s.run_id,s.agent_instance_id,s.principal_id,r.state.value,r.version,r.attempt))
            s=obs('a').scope; b=BUDGET
            db.execute('INSERT INTO sample_budgets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(s.tenant_id,s.company_id,s.environment_id,b.budget_id,b.revision,b.currency,b.limit_minor,b.outstanding_minor,b.recognized_cost_minor,b.unknown_cost,b.policy_epoch,b.witness_epoch,b.source_digest))
    def claim(self,s=None,i=None,clock=lambda:CLOCK,mapping=None,unknown=False):
        s=s or spec_for(); i=i or intent_for(s)
        m=mapping or D0PostgresAdmissionMapping(PLAN,s,clock)
        return LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnectionShim(self.path,unknown),m)).commit(i)
    def state(self):
        with closing(sqlite3.connect(self.path)) as db:
            return (db.execute('SELECT task_id,state,version FROM run_heads ORDER BY task_id').fetchall(),db.execute('SELECT revision,outstanding_minor FROM sample_budgets').fetchall(),tuple(db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('run_admissions','run_leases','sample_reservations','run_mutations','fences','events','outbox','run_audit')))
    def update(self,sql):
        with closing(sqlite3.connect(self.path)) as db,db: db.execute(sql)
    def test_claim_then_ordinary_transition(self):
        s=spec_for(); receipt=self.claim(s); self.assertEqual(receipt.committed_version,s.before.version+1)
        before=replace(s.before,state=RunState.ADMITTED,version=receipt.committed_version)
        i=LogicalIntent(before.scope,Operation.STATE_MUTATION,before.version,transition_digest(before,RunState.RUNNING),'run-effect','run-idem',s.lease.grant_id,s.lease.lease_id,None,2,3)
        c=LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnectionShim(self.path),D0PostgresTransitionMapping(s.lease,lambda:CLOCK)))
        commit_transition(c,before,RunState.RUNNING,i)
        rows,budget,counts=self.state(); self.assertEqual(rows[0],('a','RUNNING',before.version+1)); self.assertEqual(budget,[(1,20)]); self.assertEqual(counts,(1,1,1,2,2,2,2,2))
    def test_all_nine_rollback(self):
        old=self.state(); s=spec_for()
        for fail in ('HEAD','ADMISSION','LEASE','BUDGET','MUTATION','FENCE','EVENT','OUTBOX','AUDIT'):
            with self.subTest(role=fail):
                class Broken(D0PostgresAdmissionMapping):
                    def write_role(self,c,r,i):
                        super().write_role(c,r,i)
                        if r==fail: raise RuntimeError('crash')
                with self.assertRaisesRegex(RuntimeError,'crash'): self.claim(s,mapping=Broken(PLAN,s,lambda:CLOCK))
                self.assertEqual(self.state(),old)
    def test_not_ready(self):
        old=self.state()
        with self.assertRaisesRegex(ValueError,'NOT_READY'): self.claim(spec_for('b'))
        self.assertEqual(self.state(),old)
    def test_budget_limit(self):
        old=self.state()
        with self.assertRaisesRegex(ValueError,'BUDGET_HOLD'): self.claim(spec_for(amount=101))
        self.assertEqual(self.state(),old)
    def test_stale_budget_revision(self):
        old=self.state()
        with self.assertRaisesRegex(ValueError,'BUDGET_HOLD'): self.claim(spec_for(budget=replace(BUDGET,revision=1)))
        self.assertEqual(self.state(),old)
    def test_unknown_cost(self):
        self.update('UPDATE sample_budgets SET unknown_cost=true'); old=self.state()
        with self.assertRaisesRegex(ValueError,'BUDGET_HOLD'): self.claim(spec_for(budget=replace(BUDGET,unknown_cost=True)))
        self.assertEqual(self.state(),old)
    def test_digest_tamper(self):
        old=self.state()
        with self.assertRaisesRegex(ValueError,'BINDING_HOLD'): self.claim(spec_for(amount=21),intent_for(spec_for()))
        self.assertEqual(self.state(),old)
    def test_wrong_plan_digest(self):
        with self.assertRaisesRegex(ValueError,'PLAN_HOLD'): self.claim(replace(spec_for(),plan_digest='b'*64))
    def test_expiry_precommit(self):
        old=self.state(); clocks=iter((CLOCK,replace(CLOCK,now_tick=20)))
        with self.assertRaisesRegex(ValueError,'LEASE_EXPIRED'): self.claim(clock=lambda:next(clocks))
        self.assertEqual(self.state(),old)
    def test_revocation_precommit(self):
        old=self.state(); clocks=iter((CLOCK,replace(CLOCK,witness_epoch=4)))
        with self.assertRaisesRegex(ValueError,'WA_EPOCH_STALE'): self.claim(clock=lambda:next(clocks))
        self.assertEqual(self.state(),old)
    def test_no_initial_backdate(self):
        s=spec_for(); s=replace(s,lease=replace(s.lease,heartbeat_tick=9))
        with self.assertRaisesRegex(ValueError,'INITIAL_CLOCK'): self.claim(s)
    def test_no_takeover(self):
        s=spec_for(); s=replace(s,lease=replace(s.lease,fence=2))
        with self.assertRaisesRegex(ValueError,'BINDING_HOLD'): self.claim(s)
    def test_duplicate_claim(self):
        self.claim(); old=self.state()
        with self.assertRaisesRegex(ValueError,'NOT_READY'): self.claim()
        self.assertEqual(self.state(),old)
    def test_unknown_commit_no_duplicate(self):
        with self.assertRaises(CommitOutcomeUnknown): self.claim(unknown=True)
        old=self.state()
        with self.assertRaisesRegex(ValueError,'NOT_READY'): self.claim()
        self.assertEqual(self.state(),old)
    def test_unknown_reconcile_read_only(self):
        s=spec_for()
        with self.assertRaises(CommitOutcomeUnknown): self.claim(s,unknown=True)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            with SQLiteCursorShim(db) as c: r=reconcile_admission(c,PLAN,s,intent_for(s))
        self.assertTrue(r.exact_sample_match); self.assertFalse(r.retry_allowed); self.assertFalse(r.committed); self.assertFalse(r.dispatch_allowed)
        self.update("UPDATE sample_reservations SET amount_minor=19")
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            with SQLiteCursorShim(db) as c: r=reconcile_admission(c,PLAN,s,intent_for(s))
        self.assertFalse(r.exact_sample_match); self.assertFalse(r.retry_allowed)
    def test_parallel_claim_one_winner(self):
        barrier=Barrier(2,timeout=3)
        def compete(_):
            barrier.wait()
            try: self.claim(); return 'COMMIT'
            except ValueError as e: return str(e)
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(compete,range(2)))
        self.assertCountEqual(results,['COMMIT','D0_CLAIM_NOT_READY'])
        self.assertEqual(self.state()[1],[(1,20)])
    def test_parallel_tasks_budget_cas(self):
        # Seed success as synthetic fixture only, not a real terminal receipt.
        self.update("UPDATE run_heads SET state='SUCCEEDED' WHERE task_id='a'")
        barrier=Barrier(2,timeout=3)
        def compete(t):
            barrier.wait()
            try: self.claim(spec_for(t,amount=60)); return 'COMMIT'
            except ValueError as e: return str(e)
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(compete,'bc'))
        self.assertCountEqual(results,['COMMIT','D0_CLAIM_BUDGET_HOLD']); self.assertEqual(self.state()[1],[(1,60)])
    def test_missing_roster(self):
        self.update("DELETE FROM run_heads WHERE task_id='q'")
        with self.assertRaisesRegex(ValueError,'INCOMPLETE_RUN_SET'): self.claim()
    def test_postimage_mismatch_rolls_back(self):
        old=self.state(); s=spec_for()
        class Tamper(D0PostgresAdmissionMapping):
            def write_role(self,c,r,i):
                super().write_role(c,r,i)
                if r=='AUDIT': c.execute('UPDATE t1_candidate.run_audit SET lease_digest=%s',('bad',))
        with self.assertRaisesRegex(ValueError,'READBACK_HOLD'): self.claim(s,mapping=Tamper(PLAN,s,lambda:CLOCK))
        self.assertEqual(self.state(),old)

if __name__=='__main__': unittest.main()
