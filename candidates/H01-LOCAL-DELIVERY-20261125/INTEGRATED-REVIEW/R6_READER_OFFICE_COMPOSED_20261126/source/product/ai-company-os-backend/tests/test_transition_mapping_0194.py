"""D0 SQLite transaction exercise of the candidate SQL mapping, NOT a PG test.
The explicit shim removes schema prefix and FOR UPDATE, translates bind markers.
BEGIN IMMEDIATE serializes SQLite writers; it proves no PostgreSQL locking behavior.
"""
from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import unittest
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from app.core.agent_runtime.lifecycle import Scope, RunState, RunObservation, LeaseObservation, ClockSample
from app.core.agent_runtime.transition_command import transition_digest, commit_transition
from app.core.agent_runtime.scheduler_review import inspect_schedule
from app.core.orchestrator.engine import canonical_plan
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction, CommitOutcomeUnknown
from app.core.transaction.postgres_transition_mapping import D0PostgresTransitionMapping, transaction_ref
from app.core.transaction.transition_reconciliation import reconcile_transition

ROOT = Path(__file__).resolve().parents[3]
SCOPE = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,
              'task','demo-run','demo-agent','demo-principal')
BEFORE = RunObservation(SCOPE, RunState.PLANNING, 4, 1)
TARGET = RunState.RUNNING
LEASE = LeaseObservation(SCOPE,'lease','grant',1,1,7,2,3,20,9)
CLOCK = ClockSample(10,2,3,5)
INTENT = LogicalIntent(SCOPE,Operation.STATE_MUTATION,4,transition_digest(BEFORE,TARGET),
                       'effect','idem','grant','lease',None,2,3)
K = (SCOPE.tenant_id,SCOPE.company_id,SCOPE.environment_id,SCOPE.run_id)
TABLES = ('run_mutations','run_audit','events','outbox','fences')

class SQLiteCursorShim:
    def __init__(self, db): self.c = db.cursor()
    def __enter__(self): return self
    def __exit__(self,*args): self.c.close()
    def execute(self, sql, params=()):
        return self.c.execute(sql.replace('t1_candidate.','').replace(' FOR UPDATE','').replace('%s','?'),params)
    def fetchone(self): return self.c.fetchone()

class SQLiteConnectionShim:
    autocommit = False
    def __init__(self,path,unknown=False):
        self.db = sqlite3.connect(path, timeout=1)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('BEGIN IMMEDIATE')
        self.unknown = unknown
    def cursor(self): return SQLiteCursorShim(self.db)
    def commit(self):
        self.db.commit()
        if self.unknown: raise OSError('simulated lost commit response')
    def rollback(self): self.db.rollback()
    def close(self): self.db.close()

class MappingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'isolated.d0.sqlite'
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('PRAGMA foreign_keys=ON')
            for f in ('0192/candidate_event_outbox_fence.sql','0193/candidate_run_head.sql','0194/candidate_transition_roles.sql'):
                sql = (ROOT/'database'/f).read_text().replace('CREATE SCHEMA t1_candidate;','').replace('t1_candidate.','')
                db.executescript(sql)
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                       (SCOPE.tenant_id,SCOPE.company_id,SCOPE.environment_id,SCOPE.plan_revision,SCOPE.task_id,
                        SCOPE.run_id,SCOPE.agent_instance_id,SCOPE.principal_id,BEFORE.state.value,4,1))
            db.execute('INSERT INTO run_leases VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (*K,SCOPE.plan_revision,SCOPE.task_id,SCOPE.agent_instance_id,SCOPE.principal_id,
                        LEASE.lease_id,LEASE.grant_id,LEASE.lease_version,LEASE.heartbeat_revision,LEASE.fence,
                        LEASE.policy_epoch,LEASE.witness_epoch,LEASE.expires_tick,LEASE.heartbeat_tick))
    def commit(self, intent=INTENT, reference=LEASE, clock=lambda:CLOCK, mapping=None, unknown=False):
        m = mapping or D0PostgresTransitionMapping(reference,clock)
        c = LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnectionShim(self.path,unknown),m))
        return commit_transition(c,BEFORE,TARGET,intent)
    def rows(self):
        with closing(sqlite3.connect(self.path)) as db:
            return (db.execute('SELECT state,version,attempt FROM run_heads').fetchone(),
                    tuple(db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in TABLES))
    def assert_empty(self): self.assertEqual(self.rows(),(('PLANNING',4,1),(0,0,0,0,0)))
    def reconcile(self,reference=LEASE):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            with SQLiteCursorShim(db) as c: return reconcile_transition(c,INTENT,BEFORE,TARGET,reference)
    def update(self,sql,params=()):
        with closing(sqlite3.connect(self.path)) as db,db: db.execute(sql,params)
    def test_persist_and_reopen(self):
        receipt = self.commit()
        self.assertEqual(receipt.transaction_ref,transaction_ref(INTENT))
        self.assertEqual(self.rows(),(('RUNNING',5,1),(1,1,1,1,1)))
        r=self.reconcile(); self.assertTrue(r.exact_sample_match); self.assertFalse(r.committed); self.assertFalse(r.retry_allowed)
    def test_stale_lease(self):
        with self.assertRaisesRegex(ValueError,'LEASE_EXPIRED'): self.commit(clock=lambda:replace(CLOCK,now_tick=20))
        self.assert_empty()
    def test_stale_heartbeat(self):
        with self.assertRaisesRegex(ValueError,'HEARTBEAT_STALE'): self.commit(clock=lambda:replace(CLOCK,now_tick=16))
        self.assert_empty()
    def test_forged_reference(self):
        with self.assertRaisesRegex(ValueError,'REFERENCE_MISMATCH'): self.commit(reference=replace(LEASE,fence=8))
        self.assert_empty()
    def test_revocation_epoch(self):
        with self.assertRaisesRegex(ValueError,'WA_EPOCH_STALE'): self.commit(clock=lambda:replace(CLOCK,witness_epoch=4))
        self.assert_empty()
    def test_expiry_during_write(self):
        clocks=iter((CLOCK,replace(CLOCK,now_tick=20)))
        with self.assertRaisesRegex(ValueError,'LEASE_EXPIRED'): self.commit(clock=lambda:next(clocks))
        self.assert_empty()
    def test_clock_regression(self):
        clocks=iter((CLOCK,replace(CLOCK,now_tick=9)))
        with self.assertRaisesRegex(ValueError,'CLOCK_REGRESSION'): self.commit(clock=lambda:next(clocks))
        self.assert_empty()
    def test_policy_epoch_revocation(self):
        with self.assertRaisesRegex(ValueError,'POLICY_EPOCH_STALE'): self.commit(clock=lambda:replace(CLOCK,policy_epoch=3))
        self.assert_empty()
    def test_two_sqlite_writers_single_winner(self):
        barrier=Barrier(2,timeout=3)
        def compete():
            barrier.wait()
            try:
                self.commit()
                return "COMMIT"
            except ValueError as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(lambda _:compete(),range(2)))
        self.assertCountEqual(result,["COMMIT","D0_HEAD_CAS_HOLD"])
        self.assertEqual(self.rows(),(('RUNNING',5,1),(1,1,1,1,1)))
    def test_wrong_persisted_principal(self):
        self.update("UPDATE run_leases SET principal_id='demo-wrong'")
        with self.assertRaisesRegex(ValueError,'LEASE_SCOPE_HOLD'): self.commit()
        self.assert_empty()
    def test_wrong_grant(self):
        with self.assertRaisesRegex(ValueError,'LEASE_INTENT_HOLD'): self.commit(intent=replace(INTENT,grant_ref='wrong'))
        self.assert_empty()
    def test_rollback_every_role(self):
        for fail in ('HEAD','MUTATION','FENCE','EVENT','OUTBOX','AUDIT'):
            with self.subTest(role=fail):
                class Broken(D0PostgresTransitionMapping):
                    def write_transition_role(self,cursor,role,i,before,target):
                        super().write_transition_role(cursor,role,i,before,target)
                        if role==fail: raise RuntimeError('injected crash')
                with self.assertRaisesRegex(RuntimeError,'crash'): self.commit(mapping=Broken(LEASE,lambda:CLOCK))
                self.assert_empty()
    def test_fence_conflict_rolls_back_head(self):
        self.update('INSERT INTO fences VALUES (?,?,?,?,?,?)',(*K[:3],'effect','other','x'*64))
        with self.assertRaisesRegex(ValueError,'FENCE_CONFLICT'): self.commit()
        self.assertEqual(self.rows(),(('PLANNING',4,1),(0,0,0,0,1)))
    def test_idempotency_collision(self):
        self.update('INSERT INTO fences VALUES (?,?,?,?,?,?)',(*K[:3],'other','idem','x'*64))
        with self.assertRaisesRegex(ValueError,'FENCE_CONFLICT'): self.commit()
        self.assertEqual(self.rows(),(('PLANNING',4,1),(0,0,0,0,1)))
    def test_duplicate_commit_fails_cas(self):
        self.commit()
        with self.assertRaisesRegex(ValueError,'HEAD_CAS_HOLD'): self.commit()
        self.assertEqual(self.rows(),(('RUNNING',5,1),(1,1,1,1,1)))
    def test_unknown_after_commit(self):
        with self.assertRaises(CommitOutcomeUnknown): self.commit(unknown=True)
        self.assertTrue(self.reconcile().exact_sample_match)
        self.assertFalse(self.reconcile().retry_allowed)
    def test_absence_never_authorizes_retry(self):
        r=self.reconcile(); self.assertFalse(r.exact_sample_match); self.assertFalse(r.retry_allowed)
    def test_missing_outbox_readback(self):
        self.commit(); self.update('DELETE FROM outbox')
        self.assertFalse(self.reconcile().exact_sample_match)
    def test_changed_audit_readback(self):
        self.commit(); self.update('UPDATE run_audit SET policy_epoch=99')
        self.assertFalse(self.reconcile().exact_sample_match)
    def test_wrong_fence_readback(self):
        self.commit(); self.assertFalse(self.reconcile(replace(LEASE,fence=8)).exact_sample_match)
    def test_wrong_lease_version_readback(self):
        self.commit(); self.assertFalse(self.reconcile(replace(LEASE,lease_version=2)).exact_sample_match)
    def test_generic_commit_denied(self):
        m=D0PostgresTransitionMapping(LEASE,lambda:CLOCK)
        c=LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnectionShim(self.path),m))
        with self.assertRaisesRegex(PermissionError,'TRANSITION_COMMAND_REQUIRED'): c.commit(INTENT)
        self.assert_empty()
    def test_budget_role_not_mapped(self):
        with self.assertRaisesRegex(PermissionError,'ORDINARY_TRANSITION_ONLY'):
            self.commit(intent=replace(INTENT,lease_or_budget_changes=True,budget_ref='budget'))
        self.assert_empty()
    def test_terminal_denied(self):
        i=replace(INTENT,request_digest=transition_digest(BEFORE,RunState.FAILED))
        with self.assertRaisesRegex(PermissionError,'SPECIAL_TRANSITION_HOLD'):
            commit_transition(None,BEFORE,RunState.FAILED,i)
        self.assert_empty()
    def test_readback_tamper_inside_transaction_rolls_back(self):
        class Broken(D0PostgresTransitionMapping):
            def verify_write_set(self,cursor,i,roles):
                cursor.execute('UPDATE t1_candidate.run_audit SET policy_epoch=99')
                return super().verify_write_set(cursor,i,roles)
        with self.assertRaisesRegex(ValueError,'WRITE_SET_READBACK_HOLD'):
            self.commit(mapping=Broken(LEASE,lambda:CLOCK))
        self.assert_empty()

PLAN={'id':'plan','worktype':'RESEARCH','tasks':[
    {'id':'a','label':'Plan','role':'orchestrator','depends_on':[]},
    {'id':'b','label':'Research','role':'research','depends_on':['a']},
    {'id':'c','label':'Engineer','role':'engineer','depends_on':['a']},
    {'id':'q','label':'QA','role':'qa','depends_on':['b','c']},
    {'id':'v','label':'IV','role':'independent-verifier','depends_on':['q']},
    {'id':'h','label':'H01','role':'human-authority','depends_on':['v']}]}
def obs(task,state=RunState.QUEUED):
    return RunObservation(replace(SCOPE,plan_revision=canonical_plan(PLAN)['revision'],task_id=task,run_id='demo-'+task),state,0,0)
class ScheduleTests(unittest.TestCase):
    def setUp(self): self.rows=tuple(obs(x) for x in 'abcq')
    def test_first_wave(self):
        r=inspect_schedule(PLAN,self.rows); self.assertEqual(r.ready,('a',)); self.assertFalse(r.claim_allowed)
    def test_parallel_wave(self):
        r=inspect_schedule(PLAN,(obs('a',RunState.SUCCEEDED),*self.rows[1:])); self.assertEqual(r.ready,('b','c'))
    def test_independent_gate_stays_out(self):
        r=inspect_schedule(PLAN,tuple(obs(x,RunState.SUCCEEDED) for x in 'abcq')); self.assertEqual(r.ready,()); self.assertFalse(r.dispatch_allowed)
    def test_wrong_plan_revision(self):
        with self.assertRaisesRegex(ValueError,'RUN_BINDING'): inspect_schedule(PLAN,(replace(self.rows[0],scope=SCOPE),*self.rows[1:]))
    def test_duplicate(self):
        with self.assertRaisesRegex(ValueError,'RUN_BINDING'): inspect_schedule(PLAN,(*self.rows,self.rows[0]))
    def test_missing_task(self):
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'): inspect_schedule(PLAN,self.rows[1:])
    def test_forged_iv(self):
        with self.assertRaisesRegex(ValueError,'RUN_BINDING'): inspect_schedule(PLAN,(*self.rows,obs('v',RunState.SUCCEEDED)))
    def test_out_of_order_success(self):
        with self.assertRaisesRegex(ValueError,'CAUSAL_ORDER'): inspect_schedule(PLAN,(self.rows[0],obs('b',RunState.SUCCEEDED),*self.rows[2:]))
    def test_failed_predecessor_not_ready(self):
        r=inspect_schedule(PLAN,(obs('a',RunState.FAILED),*self.rows[1:])); self.assertEqual(r.ready,())
    def test_duplicate_run_id(self):
        with self.assertRaisesRegex(ValueError,'RUN_BINDING'):
            inspect_schedule(PLAN,(self.rows[0],replace(self.rows[1],scope=replace(self.rows[1].scope,run_id=self.rows[0].scope.run_id)),*self.rows[2:]))

if __name__=='__main__': unittest.main()
