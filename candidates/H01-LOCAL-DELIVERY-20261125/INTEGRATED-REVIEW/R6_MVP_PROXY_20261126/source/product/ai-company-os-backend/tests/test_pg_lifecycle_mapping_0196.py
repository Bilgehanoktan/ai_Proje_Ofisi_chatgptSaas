"""Opt-in local disposable PG integration. No external host, production or default execution.
AICOS_D0_PG_ACK=0196L_DISPOSABLE_LOCAL_ONLY and AICOS_D0_PG_DSN required.
"""
import os
import unittest
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import test_admission_mapping_0195 as base
from test_transition_mapping_0194 import obs, PLAN
import test_lifecycle_mapping_0196 as lifecycle_test
from app.core.agent_runtime.lifecycle import RunState
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction
from app.core.transaction.postgres_admission_mapping import D0PostgresAdmissionMapping
from app.core.transaction.postgres_lifecycle_mapping import (AdmissionBinding,D0PostgresLifecycleMapping,reconcile_lifecycle,FAILURE)

@unittest.skipUnless(os.environ.get('AICOS_D0_PG_ACK')=='0196L_DISPOSABLE_LOCAL_ONLY' and os.environ.get('AICOS_D0_PG_DSN'),'PG_NOT_CONFIGURED_DISPOSABLE_LOCAL_ONLY')
class PgLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from psycopg.conninfo import conninfo_to_dict
        cls.pg=psycopg; cls.dsn=os.environ['AICOS_D0_PG_DSN']; info=conninfo_to_dict(cls.dsn)
        if info.get('host') not in ('127.0.0.1','::1') or info.get('hostaddr') or info.get('service') or not info.get('dbname','').startswith('aicos_d0_0196l_'):
            raise ValueError('PG_DISPOSABLE_LOCAL_DSN_REQUIRED')
        cls.hostaddr=info['host']; cls.guard=psycopg.connect(cls.dsn,hostaddr=cls.hostaddr,autocommit=True,connect_timeout=3)
        cls.addClassCleanup(cls.guard.close)
        with cls.guard.cursor() as c:
            c.execute('SELECT current_database(),rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user')
            db,superuser,bypass=c.fetchone()
            if db!=info['dbname'] or superuser or bypass: raise PermissionError('PG_DISPOSABLE_ROLE_REQUIRED')
            c.execute('SELECT pg_try_advisory_lock(1940194)')
            if not c.fetchone()[0]: raise RuntimeError('PG_TEST_GUARD_BUSY')
            c.execute("SELECT to_regnamespace('t1_candidate') IS NULL")
            if not c.fetchone()[0]: raise RuntimeError('PG_SCHEMA_EXISTS_NO_TOUCH')
        with cls.guard.transaction():
            with cls.guard.cursor() as c:
                for f in ('0192/candidate_event_outbox_fence.sql','0193/candidate_run_head.sql','0194/candidate_transition_roles.sql','0195/candidate_admission_budget.sql','0196L/candidate_lease_settlement.sql'):
                    c.execute((base.ROOT/'database'/f).read_text(),prepare=False)
        cls.addClassCleanup(cls.drop_own_schema)
    @classmethod
    def drop_own_schema(cls):
        cls.guard.execute('DROP SCHEMA t1_candidate CASCADE')
    def connect(self):
        db=self.pg.connect(self.dsn,hostaddr=self.hostaddr,connect_timeout=3)
        try:
            db.execute("SET LOCAL lock_timeout='3s'");db.execute("SET LOCAL statement_timeout='5s'");return db
        except BaseException:
            db.close();raise
    def setUp(self):
        tables=('sample_settlements','run_lease_renewals','sample_reservations','run_admissions','sample_budgets','run_audit','run_mutations','outbox','events','fences','run_leases','run_heads')
        with self.connect() as db:
            db.execute('TRUNCATE '+','.join('t1_candidate.'+t for t in tables))
            for t in 'abcq':
                r=obs(t);s=r.scope
                db.execute('INSERT INTO t1_candidate.run_heads VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(s.tenant_id,s.company_id,s.environment_id,s.plan_revision,s.task_id,s.run_id,s.agent_instance_id,s.principal_id,r.state.value,r.version,r.attempt))
            s=obs('a').scope;b=base.BUDGET
            db.execute('INSERT INTO t1_candidate.sample_budgets VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(s.tenant_id,s.company_id,s.environment_id,b.budget_id,b.revision,b.currency,b.limit_minor,b.outstanding_minor,b.recognized_cost_minor,b.unknown_cost,b.policy_epoch,b.witness_epoch,b.source_digest))
        self.claim=base.spec_for();self.claim_i=base.intent_for(self.claim)
        r=self.coordinator(D0PostgresAdmissionMapping(PLAN,self.claim,lambda:base.CLOCK)).commit(self.claim_i)
        self.binding=AdmissionBinding(self.claim,self.claim_i);self.before=replace(self.claim.before,state=RunState.ADMITTED,version=r.committed_version)
        self.lease=self.claim.lease;self.budget=replace(self.claim.budget,revision=1,outstanding_minor=self.claim.amount_minor);self.clock=replace(base.CLOCK,now_tick=11)
    def coordinator(self,mapping,unknown=False):
        if unknown: raise ValueError('PG_UNKNOWN_INJECTION_NOT_ENABLED')
        return LogicalT1Coordinator(lambda:postgres_transaction(self.connect,mapping))
    ordinary=lifecycle_test.LifecycleTests.ordinary
    renewal=lifecycle_test.LifecycleTests.renewal
    failure=lifecycle_test.LifecycleTests.failure
    intent=lifecycle_test.LifecycleTests.intent
    execute=lifecycle_test.LifecycleTests.execute
    running=lifecycle_test.LifecycleTests.running
    def row(self,sql):
        with self.connect() as db: return db.execute(sql).fetchall()
    def test_chain(self):
        running=self.running();s=self.renewal(running);r=self.execute(s)
        verifying=self.ordinary(replace(running,version=r.committed_version),s.renewal,RunState.VERIFYING)
        terminal=self.failure(replace(running,state=RunState.VERIFYING,version=verifying.committed_version),s.renewal,replace(self.budget,revision=2))
        self.execute(terminal)
        self.assertEqual(self.row('SELECT outstanding_minor,recognized_cost_minor FROM t1_candidate.sample_budgets'),[(0,0)])
        self.assertEqual(self.row('SELECT outcome FROM t1_candidate.sample_settlements'),[(FAILURE,)])
        with self.pg.connect(self.dsn,hostaddr=self.hostaddr,connect_timeout=3) as db:
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            with db.cursor() as c: self.assertTrue(reconcile_lifecycle(c,terminal,self.intent(terminal)).exact_sample_match)
    def test_rollback_all_terminal_roles(self):
        s=self.failure(self.running())
        for fail in ('HEAD','LEASE','BUDGET','MUTATION','FENCE','EVENT','OUTBOX','AUDIT'):
            with self.subTest(role=fail):
                class Broken(D0PostgresLifecycleMapping):
                    def write_role(self,c,r,i):
                        super().write_role(c,r,i)
                        if r==fail: raise RuntimeError('injected')
                with self.assertRaisesRegex(RuntimeError,'injected'): self.execute(s,mapping=Broken(s,lambda:self.clock))
                self.assertEqual(self.row('SELECT outstanding_minor FROM t1_candidate.sample_budgets'),[(20,)])
                self.assertEqual(self.row('SELECT * FROM t1_candidate.sample_settlements'),[])
                self.assertEqual(self.row('SELECT count(*) FROM t1_candidate.run_leases'),[(1,)])
    def test_renewal_vs_terminal(self):
        running=self.running();specs=(self.renewal(running),self.failure(running));barrier=Barrier(2,timeout=3)
        def compete(s):
            barrier.wait()
            try: self.execute(s);return 'COMMIT'
            except ValueError as exc:return str(exc)
        with ThreadPoolExecutor(max_workers=2) as p: results=list(p.map(compete,specs))
        self.assertCountEqual(results,['COMMIT','D0_HEAD_CAS_HOLD'])
    def test_renewal_rollback_expiry(self):
        s=self.renewal();clocks=iter((self.clock,replace(self.clock,now_tick=20)))
        with self.assertRaisesRegex(ValueError,'LEASE_EXPIRED'):self.execute(s,clock=lambda:next(clocks))
        self.assertEqual(self.row('SELECT lease_version FROM t1_candidate.run_leases'),[(1,)])
        self.assertEqual(self.row('SELECT * FROM t1_candidate.run_lease_renewals'),[])
    def test_shared_budget_claim_cas(self):
        # Seed only a synthetic predecessor observation. Not IV/success evidence.
        with self.connect() as db: db.execute("UPDATE t1_candidate.run_heads SET state='SUCCEEDED' WHERE task_id='a'")
        barrier=Barrier(2,timeout=3)
        def compete(t):
            s=base.spec_for(t,budget=self.budget,amount=60);barrier.wait()
            try:self.coordinator(D0PostgresAdmissionMapping(PLAN,s,lambda:base.CLOCK)).commit(base.intent_for(s));return 'COMMIT'
            except ValueError as exc:return str(exc)
        with ThreadPoolExecutor(max_workers=2) as p:results=list(p.map(compete,'bc'))
        self.assertCountEqual(results,['COMMIT','D0_CLAIM_BUDGET_HOLD'])
        self.assertEqual(self.row('SELECT outstanding_minor FROM t1_candidate.sample_budgets'),[(80,)])

if __name__=='__main__':unittest.main()
