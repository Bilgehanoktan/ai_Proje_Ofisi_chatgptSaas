import sqlite3
import tempfile
import unittest
import threading
from hashlib import sha256
from pathlib import Path
from allocation_fixture import AllocationFixture, Hold, LostAck
from test_membership_review import fixture
from membership_review import review_membership


def pin(s): return sha256(s.encode()).hexdigest()


def binding(i=1,*,run=1,amount=20,revision=3,**overrides):
    e,_,_=fixture()
    e.update(run_id='demo-run-'+str(run),task_id='task-'+str(run),admission_id='admit-'+str(run),
             admission_tx='admission-'+str(run),admission_request_digest=pin('admit-'+str(run)),
             effect_id='effect-'+str(i),invocation_pin=pin('invocation-'+str(i)),
             reservation_id='reservation-'+str(i),invocation_idempotency_key='invoke-'+str(i),
             reservation_tx='reserve-'+str(i),reservation_budget_revision=revision,
             reserved_minor=amount,membership_pin=pin('membership-'+str(i)),reservation_pin=pin('reserve-'+str(i)))
    e.update(overrides);return e


class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.f=AllocationFixture(Path(self.tmp.name)/'db.sqlite');self.b='budget-1'
        self.f.seed(((binding(run=1),60),(binding(run=2),40)))
    def read(self): return self.f.readback(self.b)
    def alloc(self,i=1,*,run=1,amount=20,rev=None,fault=None,ceiling=None,**kw):
        rev=self.read()['budget'][0] if rev is None else rev
        e=binding(i,run=run,amount=amount,revision=rev+1,**kw)
        self.f.allocate(e,rev,ceiling=amount if ceiling is None else ceiling,max_input=10,max_output=10,fault=fault);return e
    def step(self,i,action,*,rev=None,tx=None,**kw):
        rev=self.read()['budget'][0] if rev is None else rev
        return self.f.advance(self.b,pin('membership-'+str(i)),rev,tx or action.lower()+'-'+str(i),action,**kw)
    def consume(self,i=1,**kw): return self.step(i,'CONSUME',receipt=pin('consume-'+str(i)),**kw)
    def usage(self,i=1,actual=12,**kw): return self.step(i,'USAGE',receipt=pin('usage-'+str(i)),consume_pin=pin('consume-'+str(i)),actual=actual,input_tokens=4,output_tokens=5,**kw)
    def settle(self,i=1,**kw): return self.step(i,'RECONCILE',receipt=pin('settle-'+str(i)),consume_pin=pin('consume-'+str(i)),usage_pin=pin('usage-'+str(i)),**kw)
    def unchanged(self,fn,exc=Hold):
        before=self.read()
        with self.assertRaises(exc): fn()
        self.assertEqual(self.read(),before)
    def test_allocation_no_double_debit(self):
        self.alloc();r=self.read();self.assertEqual(r['budget'],(3,200,100,0,0));self.assertEqual(r['pools'][0][2],40)
    def test_multiple_invocations_same_run(self):
        self.alloc(1,amount=20);self.alloc(2,amount=40);r=self.read();self.assertEqual(r['pools'][0][2],0);self.assertEqual(len(r['members']),2);self.assertEqual(r['budget'][2],100)
    def test_other_run_independent_pool(self):
        self.alloc(1,amount=60);self.alloc(2,run=2,amount=40);self.assertEqual([x[2] for x in self.read()['pools']],[0,0])
    def test_no_borrow_from_other_run(self): self.unchanged(lambda:self.alloc(amount=61))
    def test_overallocation_after_partial(self): self.alloc(amount=50);self.unchanged(lambda:self.alloc(2,amount=11))
    def test_stale_cas(self): self.alloc();self.unchanged(lambda:self.alloc(2,rev=2))
    def test_admission_alias(self): self.unchanged(lambda:self.alloc(admission_tx='reserve-1'))
    def test_scope_identity_mismatch(self):
        for k,v in [('tenant_id','other'),('project_id','other'),('fence',4),('attempt',2),('policy_epoch',99),('witness_epoch',99),('principal_id','demo-other'),('currency','EUR'),('admission_request_digest',pin('wrong'))]:
            with self.subTest(k=k): self.unchanged(lambda:self.alloc(**{k:v}))
    def test_duplicate_reservation(self): self.alloc();self.unchanged(lambda:self.alloc(2,reservation_id='reservation-1'),sqlite3.IntegrityError)
    def test_duplicate_key(self): self.alloc();self.unchanged(lambda:self.alloc(2,invocation_idempotency_key='invoke-1'),sqlite3.IntegrityError)
    def test_duplicate_invocation(self): self.alloc();self.unchanged(lambda:self.alloc(2,invocation_pin=pin('invocation-1')),sqlite3.IntegrityError)
    def test_duplicate_membership(self): self.alloc();self.unchanged(lambda:self.alloc(2,membership_pin=pin('membership-1')),sqlite3.IntegrityError)
    def test_duplicate_receipt_cross_member(self): self.alloc();self.unchanged(lambda:self.alloc(2,reservation_pin=pin('reserve-1')),sqlite3.IntegrityError)
    def test_tx_alias(self): self.alloc();self.unchanged(lambda:self.alloc(2,reservation_tx='reserve-1'))
    def test_cross_role_pin_alias(self): self.alloc();self.unchanged(lambda:self.step(1,'CONSUME',receipt=pin('reserve-1')))
    def test_wrong_consume_pin(self): self.alloc();self.consume();self.unchanged(lambda:self.step(1,'USAGE',receipt=pin('u'),consume_pin=pin('wrong'),actual=1,input_tokens=1,output_tokens=1))
    def test_cannot_usage_without_consume(self): self.alloc();self.unchanged(lambda:self.usage())
    def test_cannot_consume_twice(self): self.alloc();self.consume();self.unchanged(lambda:self.consume(tx='new-tx'))
    def test_unknown_before_ack(self):
        self.alloc();self.step(1,'UNKNOWN');r=self.read();self.assertEqual(r['budget'],(4,200,100,0,1));self.assertIsNone(r['members'][0]['actual_minor']);self.unchanged(lambda:self.consume());self.unchanged(lambda:self.alloc(2,run=2))
    def test_unknown_after_consume(self): self.alloc();self.consume();self.step(1,'UNKNOWN');r=self.read();self.assertEqual(r['members'][0]['consume_receipt_pin'],pin('consume-1'));self.unchanged(lambda:self.usage(actual=0));self.unchanged(lambda:self.settle())
    def test_unknown_cannot_zero_fill(self): self.alloc();self.unchanged(lambda:self.step(1,'UNKNOWN',actual=0))
    def test_multiple_unknowns(self): self.alloc();self.alloc(2);self.step(1,'UNKNOWN');self.step(2,'UNKNOWN');self.assertEqual(sum(x['state']=='UNKNOWN' for x in self.read()['members']),2)
    def test_usage_ceiling(self): self.alloc(ceiling=15);self.consume();self.unchanged(lambda:self.usage(actual=16))
    def test_token_ceiling(self): self.alloc();self.consume();self.unchanged(lambda:self.step(1,'USAGE',receipt=pin('u'),consume_pin=pin('consume-1'),actual=1,input_tokens=11,output_tokens=1))
    def test_bool_not_cost(self): self.alloc();self.consume();self.unchanged(lambda:self.usage(actual=True))
    def test_reconcile_once(self):
        self.alloc();self.consume();self.usage();self.settle();r=self.read();self.assertEqual(r['budget'],(6,200,80,12,0));self.assertEqual(r['members'][0]['released_minor'],8);self.unchanged(lambda:self.settle(tx='again'))
    def test_known_zero_distinct_from_unknown(self): self.alloc();self.consume();self.usage(actual=0);self.settle();self.assertEqual(self.read()['budget'],(6,200,80,0,0))
    def test_reconcile_wrong_usage_pin(self): self.alloc();self.consume();self.usage();self.unchanged(lambda:self.step(1,'RECONCILE',receipt=pin('q'),consume_pin=pin('consume-1'),usage_pin=pin('wrong')))
    def test_terminal_release_blocked_for_member(self): self.alloc();self.unchanged(lambda:self.f.close_unused(self.b,'demo-run-1',3,'close-1'))
    def test_terminal_no_effect_release_reconciled_blocked(self): self.alloc();self.consume();self.usage();self.settle();self.unchanged(lambda:self.f.close_unused(self.b,'demo-run-1',6,'close-1'))
    def test_unused_release_once(self):
        self.f.close_unused(self.b,'demo-run-2',2,'close-2');self.assertEqual(self.read()['budget'],(3,200,60,0,0));self.unchanged(lambda:self.f.close_unused(self.b,'demo-run-2',3,'close-2b'));self.unchanged(lambda:self.alloc(run=2))
    def test_release_while_unknown(self): self.alloc();self.step(1,'UNKNOWN');self.unchanged(lambda:self.f.close_unused(self.b,'demo-run-2',4,'close-2'))
    def test_allocate_fault_all_stages(self):
        for fault in ('after_member','after_receipt','before_budget','after_budget','after_event','after_outbox','after_audit'):
            with self.subTest(fault=fault): self.unchanged(lambda:self.alloc(fault=fault),RuntimeError)
    def test_reconcile_fault_all_stages(self):
        self.alloc();self.consume();self.usage()
        for fault in ('after_member','after_receipt','before_budget','after_budget','after_event','after_outbox','after_audit'):
            with self.subTest(fault=fault): self.unchanged(lambda:self.settle(fault=fault),RuntimeError)
    def test_lost_ack_after_commit(self):
        with self.assertRaises(LostAck): self.alloc(fault='lost_ack')
        r=self.read();self.assertEqual(len(r['members']),1);self.assertEqual(len(r['journal']),3);self.assertEqual(r['budget'],(3,200,100,0,0));self.unchanged(lambda:self.alloc(rev=2))
    def test_lost_ack_reconcile(self):
        self.alloc();self.consume();self.usage()
        with self.assertRaises(LostAck): self.settle(fault='lost_ack')
        self.assertEqual(self.read()['budget'],(6,200,80,12,0));self.unchanged(lambda:self.settle(tx='new-settle'))
    def test_before_commit_no_record(self): self.unchanged(lambda:self.alloc(fault='after_audit'),RuntimeError)
    def test_writer_lock_and_stale_retry(self):
        db=self.f.connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            with self.assertRaises(sqlite3.OperationalError): self.f.allocate(binding(),2,ceiling=20,max_input=10,max_output=10)
            db.rollback()
        finally: db.close()
        self.alloc(amount=50);self.unchanged(lambda:self.alloc(2,rev=2));self.unchanged(lambda:self.alloc(2,amount=20))
    def test_no_dirty_read(self):
        db=self.f.connect()
        try:
            db.execute('BEGIN IMMEDIATE');db.execute('UPDATE b SET revision=3');self.assertEqual(self.read()['budget'][0],2);db.rollback()
        finally: db.close()
    def test_receipt_drift_detected(self):
        self.alloc();db=self.f.connect()
        try: db.execute('DELETE FROM receipt')
        finally: db.close()
        with self.assertRaises(Hold): self.read()
    def test_r1_crosswalk_reuse(self):
        e=self.alloc();self.consume();self.usage();self.settle();r=self.read();row=r['members'][0];_,_,b=fixture();rev,limit,outstanding,recognized,unknown=r['budget'];b.update(revision=rev,limit_minor=limit,outstanding_minor=outstanding,recognized_cost_minor=recognized,unknown_cost=bool(unknown));result=review_membership(e,(row,),b,dict(b));self.assertTrue(result.structural_match);self.assertEqual(result.decision,'HOLD');self.assertFalse(result.settlement_allowed)

    def test_journal_missing_role_detected(self):
        self.alloc();db=self.f.connect()
        try: db.execute("DELETE FROM journal WHERE role='OUTBOX'")
        finally: db.close()
        with self.assertRaises(Hold): self.read()
    def test_journal_role_target_drift(self):
        self.alloc();db=self.f.connect()
        try: db.execute("UPDATE journal SET target='other' WHERE role='AUDIT'")
        finally: db.close()
        with self.assertRaises(Hold): self.read()
    def test_admission_tx_other_run_alias(self): self.unchanged(lambda:self.alloc(reservation_tx='admission-2'))
    def test_true_two_writer_allocation_contention(self):
        entered=threading.Event();release=threading.Event();errors=[]
        class Paused(AllocationFixture):
            @staticmethod
            def _fault(fault,stage):
                if stage=='after_member':
                    entered.set()
                    if not release.wait(5): raise RuntimeError('test synchronization timeout')
                AllocationFixture._fault(fault,stage)
        first=Paused(self.f.path)
        def writer():
            try: first.allocate(binding(amount=50),2,ceiling=50,max_input=10,max_output=10)
            except BaseException as e: errors.append(e)
        t=threading.Thread(target=writer);t.start()
        try:
            self.assertTrue(entered.wait(5))
            with self.assertRaises(sqlite3.OperationalError): self.f.allocate(binding(2,amount=20),2,ceiling=20,max_input=10,max_output=10)
            self.assertEqual(self.read()['budget'][0],2)
        finally: release.set();t.join(5)
        self.assertFalse(t.is_alive());self.assertEqual(errors,[]);self.assertEqual(len(self.read()['members']),1)
        self.unchanged(lambda:self.alloc(2,rev=2));self.unchanged(lambda:self.alloc(2,amount=20))
    def test_mixed_budget_currency_seed_rejected(self):
        f=AllocationFixture(Path(self.tmp.name)/'mixed.sqlite')
        with self.assertRaises(Hold): f.seed(((binding(run=1),60),(binding(run=2,currency='EUR'),40)))
        self.assertFalse(f.path.exists())

    def test_index_body_drift(self):
        self.alloc();db=self.f.connect()
        try: db.execute("UPDATE member SET idem='tampered'")
        finally: db.close()
        with self.assertRaises(Hold): self.read()
    def test_released_capacity_not_reallocated_in_same_run(self):
        self.alloc(amount=60);self.consume();self.usage();self.settle();self.unchanged(lambda:self.alloc(2,amount=1))

if __name__=='__main__': unittest.main(verbosity=2)
