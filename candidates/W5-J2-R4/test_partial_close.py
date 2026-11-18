import importlib.util
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from fixture_patch import write_fixture, build_fixture
from test_allocation_fixture import binding,pin

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'W5-J2-R2'/'allocation_fixture.py'

class PartialCloseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        path=self.root/'allocation_fixture_r4.py';write_fixture(SOURCE,path)
        spec=importlib.util.spec_from_file_location('allocation_fixture_r4',path);self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
        self.f=self.mod.AllocationFixture(self.root/'test.sqlite');self.f.seed(((binding(run=1),60),(binding(run=2),40)));self.b='budget-1'
    def read(self):return self.f.readback(self.b)
    def alloc(self,i=1,run=1,amount=20):
        rev=self.read()['budget'][0];self.f.allocate(binding(i,run=run,amount=amount,revision=rev+1),rev,ceiling=amount,max_input=10,max_output=10)
    def step(self,i,phase,**kw):
        self.f.advance(self.b,pin('membership-'+str(i)),self.read()['budget'][0],phase.lower()+'-'+str(i),phase,**kw)
    def settle(self,i=1,actual=12):
        self.step(i,'CONSUME',receipt=pin('consume-'+str(i)))
        self.step(i,'USAGE',receipt=pin('usage-'+str(i)),consume_pin=pin('consume-'+str(i)),actual=actual,input_tokens=4,output_tokens=5)
        self.step(i,'RECONCILE',receipt=pin('reconcile-'+str(i)),consume_pin=pin('consume-'+str(i)),usage_pin=pin('usage-'+str(i)))
    def close(self,run=1,rev=None,tx='terminal-1',**kw):
        self.f.close_partial(self.b,'demo-run-'+str(run),self.read()['budget'][0] if rev is None else rev,tx,**kw)
    def rejects(self,fn,exc=None):
        old=self.read()
        with self.assertRaises(exc or self.mod.Hold):fn()
        self.assertEqual(self.read(),old)
    def test_two_run_partial_close(self):
        self.alloc();self.settle();self.close();r=self.read()
        self.assertEqual(r['budget'],(7,200,40,12,0));self.assertEqual(r['pools'],[('demo-run-1',60,0,1,40),('demo-run-2',40,40,0,0)])
        self.assertEqual(len(r['members']),1);self.assertEqual(len(r['receipts']),4)
        self.assertEqual({x[1] for x in r['journal'] if x[0]=='terminal-1'},{'EVENT','OUTBOX','AUDIT'})
    def test_two_members_same_run(self):
        self.alloc(1,amount=20);self.alloc(2,amount=15);self.settle(1,12);self.settle(2,8);self.close();r=self.read()
        self.assertEqual(r['budget'][2:5],(40,20,0));self.assertEqual(r['pools'][0][-1],25);self.assertEqual(len(r['members']),2)
    def test_full_allocation_zero_remainder(self):
        self.alloc(amount=60);self.settle(actual=12);self.close();r=self.read();self.assertEqual(r['budget'][2:5],(40,12,0));self.assertEqual(r['pools'][0][-1],0)
    def test_zero_cost_known_not_unknown(self):
        self.alloc();self.settle(actual=0);self.close();self.assertEqual(self.read()['budget'][2:5],(40,0,0))
    def test_unused_legacy_still_works(self):
        self.rejects(self.close);self.f.close_unused(self.b,'demo-run-1',2,'unused-1');self.assertEqual(self.read()['budget'][2],40)
    def test_legacy_close_after_usage_rejected(self):
        self.alloc();self.settle();self.rejects(lambda:self.f.close_unused(self.b,'demo-run-1',self.read()['budget'][0],'legacy'))
    def test_reserved_blocks_close(self):self.alloc();self.rejects(self.close)
    def test_consumed_blocks_close(self):
        self.alloc();self.step(1,'CONSUME',receipt=pin('consume-1'));self.rejects(self.close)
    def test_usage_known_blocks_close(self):
        self.alloc();self.step(1,'CONSUME',receipt=pin('consume-1'));self.step(1,'USAGE',receipt=pin('usage-1'),consume_pin=pin('consume-1'),actual=12,input_tokens=4,output_tokens=5);self.rejects(self.close)
    def test_unknown_blocks_close(self):
        self.alloc();self.step(1,'UNKNOWN');self.rejects(self.close);self.assertEqual(self.read()['budget'][2:5],(100,0,1))
    def test_unknown_other_run_blocks_close(self):
        self.alloc();self.settle();self.alloc(2,run=2);self.step(2,'UNKNOWN');self.rejects(self.close)
    def test_other_run_pending_does_not_block_known_close(self):
        self.alloc();self.settle();self.alloc(2,run=2);self.close();self.assertEqual(self.read()['budget'][2],40)
    def test_stale_revision(self):self.alloc();self.settle();self.rejects(lambda:self.close(rev=2))
    def test_double_close(self):self.alloc();self.settle();self.close();self.rejects(lambda:self.close(tx='terminal-2'))
    def test_reallocate_closed(self):self.alloc();self.settle();self.close();self.rejects(lambda:self.alloc(2,amount=1))
    def test_transaction_alias(self):self.alloc();self.settle();self.rejects(lambda:self.close(tx='reserve-1'))
    def test_admission_alias(self):self.alloc();self.settle();self.rejects(lambda:self.close(tx='admission-1'))
    def test_fault_rollback_all(self):
        self.alloc();self.settle()
        for stage in ('after_pool','after_release','before_budget','after_budget','after_event','after_outbox','after_audit'):
            with self.subTest(stage=stage):self.rejects(lambda:self.close(fault=stage),RuntimeError)
    def test_lost_ack_no_double_release(self):
        self.alloc();self.settle()
        with self.assertRaises(self.mod.LostAck):self.close(fault='lost_ack')
        self.assertEqual(self.read()['budget'][2],40);self.rejects(lambda:self.close(tx='terminal-replay'))
    def test_competing_writer(self):
        self.alloc();self.settle();rev=self.read()['budget'][0]; entered=threading.Event(); release=threading.Event(); errors=[]
        base=self.mod.AllocationFixture
        class Paused(base):
            @staticmethod
            def _fault(fault,stage):
                if stage=='after_pool':
                    entered.set()
                    if not release.wait(5):raise RuntimeError('synchronization timeout')
                base._fault(fault,stage)
        def writer():
            try:Paused(self.f.path).close_partial(self.b,'demo-run-1',rev,'winner')
            except BaseException as e:errors.append(e)
        t=threading.Thread(target=writer);t.start()
        try:
            self.assertTrue(entered.wait(5));self.assertEqual(self.read()['budget'][2],80)
            with self.assertRaises(sqlite3.OperationalError):self.close(rev=rev,tx='loser')
        finally:release.set();t.join(5)
        self.assertFalse(t.is_alive());self.assertEqual(errors,[]);self.assertEqual(self.read()['budget'][2],40);self.rejects(lambda:self.close(rev=rev,tx='loser'))
    def test_closed_release_drift(self):
        self.alloc();self.settle();self.close();db=self.f.connect()
        try:db.execute("UPDATE pool SET released=39 WHERE run='demo-run-1'")
        finally:db.close()
        with self.assertRaises(self.mod.Hold):self.read()
    def test_journal_kind_drift(self):
        self.alloc();self.settle();self.close();db=self.f.connect()
        try:db.execute("UPDATE journal SET kind='CLOSE_UNUSED' WHERE tx='terminal-1'")
        finally:db.close()
        with self.assertRaises(self.mod.Hold):self.read()
    def test_reconciled_receipt_history_retained(self):
        self.alloc();self.settle();before=self.read();self.close();after=self.read();self.assertEqual(before['members'],after['members']);self.assertEqual(before['receipts'],after['receipts'])
    def test_patch_exact_and_no_overwrite(self):
        raw=SOURCE.read_bytes();self.assertEqual(build_fixture(raw),build_fixture(raw));self.assertNotEqual(build_fixture(raw),raw)
        with self.assertRaises(ValueError):build_fixture(raw+b'\n')
        with self.assertRaises(ValueError):write_fixture(SOURCE,SOURCE)
    def test_second_run_unused_after_partial(self):
        self.alloc();self.settle();self.close();self.f.close_unused(self.b,'demo-run-2',self.read()['budget'][0],'unused-2')
        self.assertEqual(self.read()['budget'][2:5],(0,12,0))
    def test_both_runs_partial(self):
        self.alloc(1,run=1);self.settle(1,12);self.close(1);self.alloc(2,run=2,amount=15);self.settle(2,8);self.close(2,tx='terminal-2')
        self.assertEqual(self.read()['budget'][2:5],(0,20,0));self.assertEqual([x[-1] for x in self.read()['pools']],[40,25])
    def test_r3_projection_remains_fail_closed(self):
        from terminal_diagnostic import inspect_terminal_projection
        self.alloc();self.settle();self.close();result=inspect_terminal_projection(self.read(),'demo-run-1')
        self.assertEqual(result.reason,'PROJECTION_INVALID_HOLD');self.assertFalse(result.release_allowed)
