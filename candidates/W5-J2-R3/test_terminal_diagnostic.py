import copy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from allocation_fixture import AllocationFixture
from test_allocation_fixture import binding,pin
from terminal_diagnostic import inspect_terminal_projection

class TerminalDiagnosticTests(unittest.TestCase):
    def setUp(self):
        d=TemporaryDirectory();self.addCleanup(d.cleanup)
        self.f=AllocationFixture(Path(d.name)/'test.sqlite');self.b='budget-1'
        self.f.seed(((binding(run=1),60),(binding(run=2),40)))
    def read(self):return self.f.readback(self.b)
    def review(self,run='demo-run-1',s=None):
        before=self.read();r=inspect_terminal_projection(before if s is None else s,run)
        self.assertEqual(self.read(),before)
        self.assertEqual(r.decision,'HOLD');self.assertFalse(r.release_allowed or r.settlement_allowed or r.retry_allowed)
        return r
    def alloc(self,i=1,amount=20,run=1):
        v=self.read()['budget'][0];self.f.allocate(binding(i,run=run,amount=amount,revision=v+1),v,ceiling=amount,max_input=10,max_output=10)
    def step(self,i,action,**kw):
        self.f.advance(self.b,pin('membership-'+str(i)),self.read()['budget'][0],action.lower()+'-'+str(i),action,**kw)
    def settle(self,i=1,actual=12):
        c=pin('consume-'+str(i));u=pin('usage-'+str(i));self.step(i,'CONSUME',receipt=c)
        self.step(i,'USAGE',receipt=u,consume_pin=c,actual=actual,input_tokens=2,output_tokens=3)
        self.step(i,'RECONCILE',receipt=pin('reconcile-'+str(i)),consume_pin=c,usage_pin=u)
    def test_untouched(self):
        r=self.review();self.assertEqual((r.reason,r.original_release,r.unused_run_capacity),('UNTOUCHED_POOL_ARITHMETIC_ONLY_HOLD',60,60))
    def test_partial_full_release_steals_other_run_capacity(self):
        self.alloc();self.settle();r=self.review()
        self.assertEqual((r.reason,r.original_release,r.unused_run_capacity,r.hypothetical_outstanding_after_original,r.hypothetical_outstanding_after_unused),('LEGACY_FULL_RELEASE_INCOMPATIBLE_HOLD',60,40,20,40))
    def test_zero_cost_still_historical_allocation(self):
        self.alloc();self.settle(actual=0);self.assertEqual(self.review().reason,'LEGACY_FULL_RELEASE_INCOMPATIBLE_HOLD')
    def test_fully_allocated(self):
        self.alloc(amount=60);self.settle();r=self.review();self.assertEqual((r.unused_run_capacity,r.hypothetical_outstanding_after_original,r.hypothetical_outstanding_after_unused),(0,None,40))
    def test_multiple_reconciled(self):
        self.alloc();self.settle();self.alloc(2,10);self.settle(2,actual=3);r=self.review();self.assertEqual((r.historical_allocations,r.unused_run_capacity),(30,30))
    def test_reserved(self):self.alloc();self.assertEqual(self.review().reason,'UNRESOLVED_MEMBERSHIP_HOLD')
    def test_consumed(self):self.alloc();self.step(1,'CONSUME',receipt=pin('c'));self.assertEqual(self.review().reason,'UNRESOLVED_MEMBERSHIP_HOLD')
    def test_usage_known(self):
        self.alloc();self.step(1,'CONSUME',receipt=pin('c'));self.step(1,'USAGE',receipt=pin('u'),consume_pin=pin('c'),actual=0,input_tokens=0,output_tokens=0);self.assertEqual(self.review().reason,'UNRESOLVED_MEMBERSHIP_HOLD')
    def test_unknown_other_run(self):self.alloc(run=2);self.step(1,'UNKNOWN');self.assertEqual(self.review().reason,'UNKNOWN_COST_HOLD')
    def test_closed(self):self.f.close_unused(self.b,'demo-run-1',2,'close');self.assertEqual(self.review().reason,'ALREADY_CLOSED_HOLD')
    def test_missing_run(self):self.assertEqual(self.review('demo-missing').reason,'RUN_MISSING_HOLD')
    def test_tampered_balance(self):
        s=self.read();s['budget']=(2,200,99,0,0);self.assertEqual(self.review(s=s).reason,'PROJECTION_INVALID_HOLD')
    def test_tampered_pool(self):
        s=self.read();s['pools'][0]=('demo-run-1',60,59,0,0);self.assertEqual(self.review(s=s).reason,'PROJECTION_INVALID_HOLD')
    def test_duplicate_member(self):
        self.alloc();s=self.read();s['members']+=s['members'];self.assertEqual(self.review(s=s).reason,'PROJECTION_INVALID_HOLD')
    def test_bool_cost(self):
        s=self.read();s['budget']=(2,200,100,False,0);self.assertEqual(self.review(s=s).reason,'PROJECTION_INVALID_HOLD')
    def test_other_run_unaffected(self):
        self.alloc();self.settle();r=self.review('demo-run-2');self.assertEqual((r.reason,r.unused_run_capacity),('UNTOUCHED_POOL_ARITHMETIC_ONLY_HOLD',40))
