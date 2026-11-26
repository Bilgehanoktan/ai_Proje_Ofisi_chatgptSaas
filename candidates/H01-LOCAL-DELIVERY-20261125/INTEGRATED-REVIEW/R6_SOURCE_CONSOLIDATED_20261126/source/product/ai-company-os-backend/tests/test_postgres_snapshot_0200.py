"""DB-API protocol doubles only; no PostgreSQL execution evidence."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from app.core.event_store.plan_history_review import PlanHistoryReview
from app.core.event_store import postgres_snapshot as subject

GOOD = ('aicos_d0_0200_test','repeatable read','on',False,False)
class Cursor:
    def __init__(self,db):self.db=db;self.rows=[];self.checks=0
    def __enter__(self):return self
    def __exit__(self,*args):
        self.db.calls.append('cursor_close')
        if self.db.fail=='cursor_close':raise RuntimeError('close')
    def execute(self,sql):
        self.db.calls.append(sql)
        if self.db.fail==sql:raise RuntimeError('execute')
        if sql==subject._CHECK:
            self.rows=list(self.db.contexts[min(self.checks,len(self.db.contexts)-1)])
            self.checks+=1
    def fetchone(self):return self.rows.pop(0) if self.rows else None
class DB:
    def __init__(self,contexts=None,fail=None,status=0,autocommit=False):
        self.calls=[];self.info=SimpleNamespace(transaction_status=status);self.autocommit=autocommit
        self.contexts=contexts if contexts is not None else [[GOOD]];self.fail=fail
    def cursor(self):self.calls.append('cursor');return Cursor(self)
    def rollback(self):
        self.calls.append('rollback')
        if self.fail=='rollback':raise RuntimeError('rollback')
    def close(self):
        self.calls.append('close')
        if self.fail=='close':raise RuntimeError('close')
class SnapshotTests(unittest.TestCase):
    def call(self,db,review=None):
        review=review or PlanHistoryReview('match',structural_match=True)
        with patch.object(subject,'inspect_plan_history',return_value=review) as m:
            r=subject.read_plan_snapshot(lambda:db,{},'rev',(),exclusive_budget_anchors=('anchor',))
        return r,m
    def hold(self,r):
        self.assertFalse(r.structural_match);self.assertEqual(r.tasks,());self.assertIsNone(r.event_count)
        self.assertFalse(r.dispatch_allowed);self.assertFalse(r.release_ready)
    def test_exact_sequence(self):
        db=DB();r,m=self.call(db);self.assertTrue(r.structural_match)
        m.assert_called_once();self.assertEqual(m.call_args.kwargs,{'exclusive_budget_anchors':('anchor',)})
        self.assertEqual(db.calls,['cursor',subject._CONFIG,"SET LOCAL statement_timeout='5s'","SET LOCAL lock_timeout='2s'",subject._CHECK,subject._CHECK,'cursor_close','rollback','close'])
    def test_readback_hold_preserved(self):
        r,_=self.call(DB(),PlanHistoryReview('specific hold'));self.hold(r);self.assertEqual(r.reason,'specific hold')
    def test_contexts_fail_closed(self):
        for row in [('production',*GOOD[1:]),(GOOD[0],'read committed',*GOOD[2:]),(GOOD[0],GOOD[1],'off',False,False),(*GOOD[:3],True,False),(*GOOD[:3],False,True),(*GOOD[:3],0,0),None,('x',),GOOD]:
            with self.subTest(row=row):
                db=DB([[row,GOOD]] if row==GOOD else [[row]]);r,m=self.call(db);self.hold(r);m.assert_not_called();self.assertEqual(db.calls[-2:],['rollback','close'])
    def test_context_change_discards_result(self):
        r,m=self.call(DB([[GOOD],[('aicos_d0_other',*GOOD[1:])]]));m.assert_called_once();self.hold(r)
    def test_fresh_status(self):
        for status in [1,2,3,4,None,False,'0',0.0]:
            with self.subTest(status=status):
                db=DB(status=status);r,m=self.call(db);self.hold(r);m.assert_not_called();self.assertNotIn('cursor',db.calls)
    def test_autocommit(self):
        r,m=self.call(DB(autocommit=True));self.hold(r);m.assert_not_called()
    def test_setup_failure(self):
        for step in [subject._CONFIG,"SET LOCAL statement_timeout='5s'","SET LOCAL lock_timeout='2s'",subject._CHECK]:
            with self.subTest(step=step):
                db=DB(fail=step);r,m=self.call(db);self.hold(r);m.assert_not_called();self.assertEqual(db.calls[-2:],['rollback','close'])
    def test_cleanup_failure(self):
        for step in ['cursor_close','rollback','close']:
            with self.subTest(step=step):
                db=DB(fail=step);r,m=self.call(db);self.hold(r);m.assert_called_once();self.assertEqual(db.calls[-2:],['rollback','close'])
    def test_review_exception(self):
        db=DB()
        with patch.object(subject,'inspect_plan_history',side_effect=RuntimeError('read')):self.hold(subject.read_plan_snapshot(lambda:db,{},'rev',()))
        self.assertEqual(db.calls[-2:],['rollback','close'])
    def test_connection_failure(self):
        def fail():raise RuntimeError('connect')
        self.hold(subject.read_plan_snapshot(fail,{},'rev',()))
    def test_no_retry(self):
        calls=[]
        def connect():calls.append(1);return DB(fail=subject._CONFIG)
        self.hold(subject.read_plan_snapshot(connect,{},'rev',()));self.assertEqual(calls,[1])

if __name__=='__main__':unittest.main()
