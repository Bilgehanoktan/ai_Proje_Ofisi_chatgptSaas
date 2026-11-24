"""Opt-in real PostgreSQL tests, using the existing guarded disposable 0196-L fixture.
No production, remote DSN, automatic database creation or default execution.
"""
import os
import unittest
from unittest.mock import patch
import test_pg_lifecycle_mapping_0196 as pgfixture
import test_admission_mapping_0195 as admission
from test_transition_mapping_0194 import obs, PLAN
from app.core.orchestrator.engine import canonical_plan
from app.core.event_store import postgres_snapshot as subject
from app.core.event_store.plan_history_review import RunHistoryPin

@unittest.skipUnless(os.environ.get('AICOS_D0_PG_ACK')=='0196L_DISPOSABLE_LOCAL_ONLY' and os.environ.get('AICOS_D0_PG_DSN'),'PG_NOT_CONFIGURED_DISPOSABLE_LOCAL_ONLY')
class PgSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture=pgfixture.PgLifecycleTests
        cls.addClassCleanup(fixture.doClassCleanups)
        fixture.setUpClass()
    def setUp(self):
        self.fixture=pgfixture.PgLifecycleTests('test_chain')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.rev=canonical_plan(PLAN)['revision']
        self.pins=tuple(RunHistoryPin(obs(t),self.fixture.binding if t=='a' else None) for t in 'abcq')
    def connect(self):
        f=self.fixture
        return f.pg.connect(f.dsn,hostaddr=f.hostaddr,connect_timeout=3)
    def review(self):
        return subject.read_plan_snapshot(self.connect,PLAN,self.rev,self.pins,exclusive_budget_anchors=(admission.BUDGET,))
    def test_actual_admission_snapshot(self):
        r=self.review();self.assertTrue(r.structural_match);self.assertTrue(r.budget_reconciled);self.assertEqual(r.event_count,1)
    def test_actual_concurrent_commit_not_visible_until_fresh_snapshot(self):
        original=subject.inspect_plan_history
        def race(cursor,*args,**kwargs):
            with self.fixture.connect() as db:
                db.execute("UPDATE t1_candidate.run_heads SET state='RUNNING' WHERE task_id='b'")
            return original(cursor,*args,**kwargs)
        with patch.object(subject,'inspect_plan_history',side_effect=race):
            self.assertTrue(self.review().structural_match)
        self.assertFalse(self.review().structural_match)
    def test_actual_transaction_rejects_write(self):
        rejected=[]
        def write(cursor,*args,**kwargs):
            try:
                cursor.execute("UPDATE t1_candidate.run_heads SET state='RUNNING' WHERE task_id='b'")
            except self.fixture.pg.errors.ReadOnlySqlTransaction:
                rejected.append(True)
                raise
            return subject.PlanHistoryReview('unexpected write',structural_match=True)
        with patch.object(subject,'inspect_plan_history',side_effect=write):
            self.assertFalse(self.review().structural_match)
        self.assertEqual(rejected,[True])
        self.assertTrue(self.review().structural_match)

if __name__=='__main__':unittest.main()
