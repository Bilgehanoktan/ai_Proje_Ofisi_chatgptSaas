"""Opt-in real PostgreSQL integration suite; never default-enabled.
Use a new disposable local database named aicos_d0_0194_<suffix>, non-superuser,
no BYPASSRLS. No production, external host, real data, or canonical acceptance.
AICOS_D0_PG_ACK=0194_DISPOSABLE_LOCAL_ONLY and AICOS_D0_PG_DSN are required.
"""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from dataclasses import replace
import test_transition_mapping_0194 as sample
from app.core.agent_runtime.transition_command import commit_transition
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction
from app.core.transaction.postgres_transition_mapping import D0PostgresTransitionMapping
from app.core.transaction.transition_reconciliation import reconcile_transition

@unittest.skipUnless(os.environ.get('AICOS_D0_PG_ACK') == '0194_DISPOSABLE_LOCAL_ONLY'
                     and os.environ.get('AICOS_D0_PG_DSN'), 'PG_NOT_CONFIGURED_DISPOSABLE_LOCAL_ONLY')
class RealPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from psycopg.conninfo import conninfo_to_dict
        cls.pg = psycopg
        cls.dsn = os.environ['AICOS_D0_PG_DSN']
        info = conninfo_to_dict(cls.dsn)
        if (info.get('host') not in ('127.0.0.1','::1') or info.get('hostaddr')
                or info.get('service') or not info.get('dbname','').startswith('aicos_d0_0194_')):
            raise ValueError('PG_DISPOSABLE_LOCAL_DSN_REQUIRED')
        cls.hostaddr = info['host']
        cls.guard = psycopg.connect(cls.dsn,hostaddr=cls.hostaddr,autocommit=True,connect_timeout=3)
        cls.addClassCleanup(cls.guard.close)
        with cls.guard.cursor() as cur:
            cur.execute('SELECT current_database(),rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user')
            db,superuser,bypass = cur.fetchone()
            if db != info['dbname'] or superuser or bypass:
                raise PermissionError('PG_DISPOSABLE_ROLE_REQUIRED')
            cur.execute('SELECT pg_try_advisory_lock(1940194)')
            if not cur.fetchone()[0]: raise RuntimeError('PG_TEST_GUARD_BUSY')
            cur.execute("SELECT to_regnamespace('t1_candidate') IS NULL")
            if not cur.fetchone()[0]: raise RuntimeError('PG_SCHEMA_EXISTS_NO_TOUCH')
        with cls.guard.transaction():
            with cls.guard.cursor() as cur:
                for f in ('0192/candidate_event_outbox_fence.sql','0193/candidate_run_head.sql','0194/candidate_transition_roles.sql'):
                    cur.execute((sample.ROOT/'database'/f).read_text(),prepare=False)
        # Only drop the schema created in this session, never a pre-existing one.
        cls.addClassCleanup(cls.drop_own_schema)

    @classmethod
    def drop_own_schema(cls):
        with cls.guard.cursor() as cur:
            cur.execute('DROP SCHEMA t1_candidate CASCADE')

    def connect(self):
        db = self.pg.connect(self.dsn,hostaddr=self.hostaddr,connect_timeout=3)
        try:
            db.execute("SET LOCAL lock_timeout = '3s'")
            db.execute("SET LOCAL statement_timeout = '5s'")
            return db
        except BaseException:
            db.close(); raise

    def setUp(self):
        s,l = sample.SCOPE,sample.LEASE
        with self.connect() as db:
            db.execute('TRUNCATE t1_candidate.run_audit,t1_candidate.run_mutations,t1_candidate.outbox,t1_candidate.events,t1_candidate.fences,t1_candidate.run_leases,t1_candidate.run_heads')
            db.execute('INSERT INTO t1_candidate.run_heads VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                       (s.tenant_id,s.company_id,s.environment_id,s.plan_revision,s.task_id,s.run_id,s.agent_instance_id,s.principal_id,sample.BEFORE.state.value,4,1))
            db.execute('INSERT INTO t1_candidate.run_leases VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                       (*sample.K,s.plan_revision,s.task_id,s.agent_instance_id,s.principal_id,l.lease_id,l.grant_id,l.lease_version,l.heartbeat_revision,l.fence,l.policy_epoch,l.witness_epoch,l.expires_tick,l.heartbeat_tick))

    def commit(self,mapping=None,clock=lambda:sample.CLOCK):
        m = mapping or D0PostgresTransitionMapping(sample.LEASE,clock)
        c = LogicalT1Coordinator(lambda:postgres_transaction(self.connect,m))
        return commit_transition(c,sample.BEFORE,sample.TARGET,sample.INTENT)

    def counts(self):
        with self.connect() as db:
            return (db.execute('SELECT state,version,attempt FROM t1_candidate.run_heads').fetchone(),
                    tuple(db.execute('SELECT count(*) FROM t1_candidate.'+t).fetchone()[0] for t in sample.TABLES))

    def test_commit_readback(self):
        self.commit(); self.assertEqual(self.counts(),(('RUNNING',5,1),(1,1,1,1,1)))
        with self.pg.connect(self.dsn,hostaddr=self.hostaddr,connect_timeout=3) as db:
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            with db.cursor() as cur:
                r=reconcile_transition(cur,sample.INTENT,sample.BEFORE,sample.TARGET,sample.LEASE)
                self.assertTrue(r.exact_sample_match); self.assertFalse(r.retry_allowed)

    def test_rollback_all_roles(self):
        for fail in ('HEAD','MUTATION','FENCE','EVENT','OUTBOX','AUDIT'):
            with self.subTest(role=fail):
                class Broken(D0PostgresTransitionMapping):
                    def write_transition_role(self,cursor,role,i,before,target):
                        super().write_transition_role(cursor,role,i,before,target)
                        if role==fail: raise RuntimeError('injected')
                with self.assertRaisesRegex(RuntimeError,'injected'):
                    self.commit(Broken(sample.LEASE,lambda:sample.CLOCK))
                self.assertEqual(self.counts(),(('PLANNING',4,1),(0,0,0,0,0)))

    def test_two_writers(self):
        barrier=Barrier(2,timeout=3)
        def compete():
            barrier.wait()
            try: self.commit(); return 'COMMIT'
            except ValueError as exc: return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(lambda _:compete(),range(2)))
        self.assertCountEqual(result,['COMMIT','D0_HEAD_CAS_HOLD'])
        self.assertEqual(self.counts(),(('RUNNING',5,1),(1,1,1,1,1)))

    def test_row_lock_nowait(self):
        a,b=self.connect(),self.connect()
        try:
            a.execute('SELECT version FROM t1_candidate.run_heads FOR UPDATE')
            with self.assertRaises(self.pg.errors.LockNotAvailable):
                b.execute('SELECT version FROM t1_candidate.run_heads FOR UPDATE NOWAIT')
            b.rollback(); a.rollback()
            self.commit()
        finally:
            a.close(); b.close()

    def test_stale_lease_rollback(self):
        with self.assertRaisesRegex(ValueError,'LEASE_EXPIRED'):
            self.commit(clock=lambda:replace(sample.CLOCK,now_tick=20))
        self.assertEqual(self.counts(),(('PLANNING',4,1),(0,0,0,0,0)))

if __name__=='__main__': unittest.main()
