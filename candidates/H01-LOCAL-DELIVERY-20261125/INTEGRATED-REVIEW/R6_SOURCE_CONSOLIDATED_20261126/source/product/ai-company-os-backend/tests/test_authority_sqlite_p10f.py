"""P10F diagnostic: original ordinary T1 + 0211 authority. Not witness/journal wrapper or PostgreSQL."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Barrier, Event
from unittest import TestCase
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, LeaseObservation, ClockSample
from app.core.agent_runtime.transition_command import transition_digest, commit_transition
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin
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
from app.core.transaction.review import LogicalIntent, Operation
I = LogicalIntent(SCOPE,Operation.STATE_MUTATION,4,transition_digest(BEFORE,TARGET),'effect','idem','grant','lease',None,2,3)
K = (SCOPE.tenant_id,SCOPE.company_id,SCOPE.environment_id,SCOPE.run_id)
TABLES = ('run_mutations','run_audit','events','outbox','fences')

def digest(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()

class Cursor:
    def __init__(self,db): self.c=db.cursor()
    def __enter__(self): return self
    def __exit__(self,*args): self.c.close()
    def execute(self,sql,params=()):
        return self.c.execute(sql.replace('t1_candidate.','').replace(' FOR UPDATE','').replace('%s','?'),params)
    def fetchone(self): return self.c.fetchone()

class Connection:
    autocommit=False
    def __init__(self,path,unknown=False):
        self.db=sqlite3.connect(path,timeout=2)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('BEGIN IMMEDIATE')
        self.unknown=unknown
    def cursor(self): return Cursor(self.db)
    def commit(self):
        self.db.commit()
        if self.unknown: raise OSError('synthetic lost commit response')
    def rollback(self): self.db.rollback()
    def close(self): self.db.close()

class AuthoritySQLiteP10F(TestCase):
    def setUp(self):
        tmp=TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/'product.d0.sqlite'
        self.root=RootPin('a'*64,'b'*64,1); self.new=RootPin('c'*64,'b'*64,2)
        self.authority=D0IntentAuthority.create(self.path.with_name('root.authority.sqlite'),self.root)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('PRAGMA foreign_keys=ON')
            for f in ('0192/candidate_event_outbox_fence.sql','0193/candidate_run_head.sql','0194/candidate_transition_roles.sql'):
                db.executescript((ROOT/'database'/f).read_text().replace('CREATE SCHEMA t1_candidate;','').replace('t1_candidate.',''))
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',(SCOPE.tenant_id,SCOPE.company_id,SCOPE.environment_id,SCOPE.plan_revision,SCOPE.task_id,SCOPE.run_id,SCOPE.agent_instance_id,SCOPE.principal_id,BEFORE.state.value,4,1))
            db.execute('INSERT INTO run_leases VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(*K,SCOPE.plan_revision,SCOPE.task_id,SCOPE.agent_instance_id,SCOPE.principal_id,LEASE.lease_id,LEASE.grant_id,LEASE.lease_version,LEASE.heartbeat_revision,LEASE.fence,LEASE.policy_epoch,LEASE.witness_epoch,LEASE.expires_tick,LEASE.heartbeat_tick))
    def execute(self,root=None,clock=lambda:CLOCK,connect=None,unknown=False):
        with self.authority.claim_and_fence(root or self.root,digest(asdict(SCOPE)),digest(asdict(I)),transaction_ref(I),I.request_digest):
            c=LogicalT1Coordinator(lambda:postgres_transaction(connect or (lambda:Connection(self.path,unknown)),D0PostgresTransitionMapping(LEASE,clock)))
            return commit_transition(c,BEFORE,TARGET,I)
    def rows(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute('SELECT state,version,attempt FROM run_heads').fetchone(),tuple(db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in TABLES)
    def reconcile(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            with Cursor(db) as c:return reconcile_transition(c,I,BEFORE,TARGET,LEASE)
    def test_real_commit_and_readback(self):
        self.assertEqual(self.execute().transaction_ref,transaction_ref(I))
        self.assertEqual(self.rows(),(('RUNNING',5,1),(1,1,1,1,1)))
        self.assertTrue(self.reconcile().exact_sample_match)
        self.assertFalse(self.reconcile().retry_allowed)
    def test_product_restore_blocked(self):
        before=self.path.read_bytes();self.execute();self.path.write_bytes(before)
        with self.assertRaisesRegex(ValueError,'ALREADY_CLAIMED'): self.execute()
        self.assertEqual(self.rows(),(('PLANNING',4,1),(0,0,0,0,0)))
    def test_unknown_commit_quarantined(self):
        with self.assertRaises(CommitOutcomeUnknown):self.execute(unknown=True)
        self.assertTrue(self.reconcile().exact_sample_match)
        with self.assertRaisesRegex(ValueError,'ALREADY_CLAIMED'):self.execute()
    def test_rollback_still_consumes_claim(self):
        with self.assertRaisesRegex(ValueError,'LEASE_EXPIRED'):self.execute(clock=lambda:replace(CLOCK,now_tick=20))
        self.assertEqual(self.rows(),(('PLANNING',4,1),(0,0,0,0,0)))
        with self.assertRaisesRegex(ValueError,'ALREADY_CLAIMED'):self.execute()
    def test_cooperating_publisher_waits_during_t1_commit(self):
        started,done=Event(),Event();jobs=[];outer=self
        def publish():
            started.set();self.authority.publish(self.root,self.new);done.set()
        with ThreadPoolExecutor(max_workers=1) as pool:
            class DuringCommit(Connection):
                def commit(self):
                    jobs.append(pool.submit(publish));outer.assertTrue(started.wait(1));outer.assertFalse(done.wait(.15))
                    super().commit();outer.assertFalse(done.is_set())
            self.execute(connect=lambda:DuringCommit(self.path));jobs[0].result(timeout=4)
        self.assertTrue(done.is_set());self.assertTrue(self.reconcile().exact_sample_match)
    def test_revocation_before_claim(self):
        self.authority.publish(self.root,self.new)
        with self.assertRaisesRegex(ValueError,'ROOT_HOLD'):self.execute()
        self.assertEqual(self.rows(),(('PLANNING',4,1),(0,0,0,0,0)))
    def test_two_claimants_one_t1(self):
        barrier=Barrier(2,timeout=3)
        def run():
            barrier.wait()
            try:self.execute();return 'COMMIT'
            except ValueError as e:return str(e)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs=[pool.submit(run) for _ in range(2)]
            self.assertCountEqual([j.result(timeout=5) for j in jobs],['COMMIT','D0_AUTHORITY_ALREADY_CLAIMED_HOLD'])
        self.assertEqual(self.rows(),(('RUNNING',5,1),(1,1,1,1,1)))
    def test_residual_both_stores_restored_replay(self):
        # Negative security finding: restoring the authority too removes the durable claim.
        product=self.path.read_bytes();root=self.authority.path.read_bytes()
        first=self.execute();self.path.write_bytes(product);self.authority.path.write_bytes(root)
        second=self.execute();self.assertEqual(first,second)
        self.assertTrue(self.reconcile().exact_sample_match)
