"""Offline oracle candidates only; NOT_RUN. No real DB or provider."""
import unittest
from dataclasses import replace
from app.core.runtime_preview import Scope, LeaseObservation, ClockSample
from app.core.t1_review import (LogicalIntent, Operation, RoleObservation, required_roles,
                                inspect_write_set, DisabledT1Coordinator)
from app.core.fence_review import FenceObservation, FencePhase, inspect_fence
from app.core.causal_ledger_review import CausalObservation, GENESIS, event_digest, inspect_chain


class T1ReviewTests(unittest.TestCase):
    def setUp(self):
        self.scope = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,
                           'research','demo-run','demo-agent','demo-principal')
        self.lease = LeaseObservation(self.scope,'demo-lease','demo-grant',1,1,1,2,3,60,40)
        self.clock = ClockSample(50,2,3,20)
        self.i = LogicalIntent(self.scope,Operation.ADMISSION,4,'b'*64,'effect-1','idem-1',
                               'demo-grant','demo-lease','budget-1',2,3)
        self.rows = tuple(RoleObservation(role,'row-'+role,self.scope,'b'*64,'tx-1',4,2,3)
                          for role in sorted(required_roles(self.i)))
        self.f = FenceObservation(self.scope,'effect-1','idem-1','b'*64,3,FencePhase.LOCAL_ONLY)
        e = CausalObservation(self.scope,'stream-1','event-1',1,'corr-1',None,'tx-1','b'*64,GENESIS,2,3,'0'*64)
        self.e = replace(e,event_digest=event_digest(e))

    def review(self, rows=None, head=4, i=None, clock=None):
        return inspect_write_set(i or self.i,self.rows if rows is None else rows,head,
                                 self.lease,self.lease,clock or self.clock)

    def test_complete_is_never_commit(self):
        r=self.review();self.assertTrue(r.structural_match);self.assertFalse(r.committed);self.assertFalse(r.commit_allowed)
        self.assertFalse(DisabledT1Coordinator().commit(self.i).committed)

    def test_every_missing_role(self):
        for row in self.rows:
            r=self.review(tuple(x for x in self.rows if x != row));self.assertEqual(r.missing_roles,(row.role,))

    def test_cas_and_budget(self):
        self.assertEqual(self.review(head=5).reason,'CAS_VERSION_MISMATCH')
        self.assertEqual(self.review(i=replace(self.i,budget_ref=None)).reason,'BUDGET_REFERENCE_MISSING')

    def test_duplicate_and_split_transaction(self):
        self.assertEqual(self.review(self.rows[:-1]+(self.rows[0],)).reason,'DUPLICATE_ROLE_OR_RECORD')
        self.assertEqual(self.review(self.rows[:-1]+(replace(self.rows[-1],transaction_ref='tx-2'),)).reason,'TRANSACTION_REFERENCE_MISMATCH')

    def test_epoch_and_scope(self):
        self.assertEqual(self.review(clock=replace(self.clock,witness_epoch=4)).reason,'ERR_WA_EPOCH_STALE')
        self.assertEqual(self.review(self.rows[:-1]+(replace(self.rows[-1],request_digest='c'*64),)).reason,'ROLE_SCOPE_DIGEST_VERSION_EPOCH_MISMATCH')

    def test_idempotent_no_redispatch(self):
        r=inspect_fence(self.f,self.f,3);self.assertFalse(r.retry_allowed);self.assertFalse(r.new_fence_created)
        self.assertEqual(inspect_fence(self.f,replace(self.f,request_digest='c'*64),3).reason,'IDEMPOTENCY_DIGEST_CONFLICT')

    def test_unknown_and_restore(self):
        self.assertEqual(inspect_fence(self.f,replace(self.f,phase=FencePhase.UNKNOWN),3).reason,'NO_BLIND_RETRY')
        self.assertEqual(inspect_fence(self.f,self.f,4).reason,'ERR_WA_EPOCH_STALE')

    def test_chain_and_tamper(self):
        r=inspect_chain((self.e,),self.scope,'stream-1',2,3);self.assertTrue(r.structural_match);self.assertFalse(r.authoritative)
        self.assertEqual(inspect_chain((replace(self.e,request_digest='c'*64),),self.scope,'stream-1',2,3).reason,'EVENT_DIGEST_MISMATCH')

    def test_gap_and_bad_causation(self):
        e=replace(self.e,event_id='event-2',sequence=3,previous_digest=self.e.event_digest,causation_id='event-1')
        e=replace(e,event_digest=event_digest(e))
        self.assertEqual(inspect_chain((self.e,e),self.scope,'stream-1',2,3).reason,'EVENT_SCOPE_SEQUENCE_EPOCH_INVALID')
        e=replace(e,sequence=2,causation_id='missing');e=replace(e,event_digest=event_digest(e))
        self.assertEqual(inspect_chain((self.e,e),self.scope,'stream-1',2,3).reason,'CAUSATION_OR_CORRELATION_INVALID')
