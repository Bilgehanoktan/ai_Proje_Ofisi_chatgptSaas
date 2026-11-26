from dataclasses import replace
import unittest
from app.core.agent_runtime.lifecycle import Scope, LeaseObservation, ClockSample
from app.core.transaction.review import LogicalIntent, Operation, RoleObservation, required_roles
from app.core.transaction.readback_review import HeadReadback, AdmissionPin
from app.core.policy.witness_review import WitnessSample
from app.engines.budget_engine.reservation_review import BudgetSnapshot, ReservationRequest
from app.core.transaction.admission_bundle import AdmissionBundle, inspect_admission_bundle


class AdmissionBundleTests(unittest.TestCase):
    def setUp(self):
        s=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,'research','demo-run','demo-agent','demo-principal')
        i=LogicalIntent(s,Operation.ADMISSION,2,'b'*64,'effect','idem','grant','lease','budget',3,4)
        h=HeadReadback(s,2,'tx','b'*64,3,4)
        a=AdmissionPin(s,'admission','grant','lease','budget','b'*64,1,3,4)
        l=LeaseObservation(s,'lease','grant',1,1,1,3,4,15,7)
        c=ClockSample(8,3,4,3)
        q=ReservationRequest(s,'budget',1,'TRY',100,'idem',3,4)
        budget=BudgetSnapshot(s,'budget',1,'TRY',1000,100,100,False,3,4,'c'*64)
        w=WitnessSample(s,'root',4,1,'d'*64,7)
        refs={'ADMISSION':'admission','LEASE':'lease','BUDGET':'budget'}
        rows=tuple(RoleObservation(k,refs.get(k,k.lower()),s,'b'*64,'tx',2,3,4) for k in sorted(required_roles(i)))
        self.b=AdmissionBundle(i,rows,h,h,a,a,l,l,c,q,budget,budget,w,w,3)

    def check(self,**kw): return inspect_admission_bundle(replace(self.b,**kw))

    def test_shape_match_stays_hold(self):
        r=self.check(); self.assertEqual(r.reason,'D0_BUNDLE_MATCH_AUTHORITY_UNPROVEN'); self.assertEqual(len(r.matched),5)
        self.assertEqual(r.decision,'HOLD'); self.assertEqual(r.physical_mapping,'PHYSICAL_MAPPING_HOLD')
        for k in ('commit_allowed','dispatch_allowed','spend_allowed','authoritative'): self.assertIs(getattr(r,k),False)

    def test_missing_role(self): self.assertEqual(self.check(rows=self.b.rows[1:]).reason,'WRITE_SET_INCOMPLETE')

    def test_role_id_binding(self):
        rows=tuple(replace(r,record_id='alien') if r.role=='ADMISSION' else r for r in self.b.rows)
        self.assertEqual(self.check(rows=rows).reason,'ADMISSION_ROLE_REFERENCE_HOLD')

    def test_head_cas(self): self.assertEqual(self.check(head=replace(self.b.head,version=3)).reason,'HEAD_REFERENCE_CAS_HOLD')

    def test_lease_expiry(self): self.assertEqual(self.check(clock=replace(self.b.clock,now_tick=15)).reason,'LEASE_EXPIRED')

    def test_unknown_budget(self):
        b=replace(self.b.budget,unknown_cost=True)
        self.assertEqual(self.check(budget=b,budget_reference=b).reason,'UNKNOWN_COST_HOLD')

    def test_budget_idempotency(self): self.assertEqual(self.check(request=replace(self.b.request,idempotency_key='other')).reason,'RESERVATION_INTENT_BINDING_HOLD')

    def test_witness_epoch(self):
        w=replace(self.b.witness,epoch=3)
        self.assertEqual(self.check(witness=w,witness_reference=w).reason,'ERR_WA_EPOCH_STALE')

    def test_witness_age(self):
        w=replace(self.b.witness,observed_tick=1)
        self.assertEqual(self.check(witness=w,witness_reference=w).reason,'WA_OBSERVATION_NOT_FRESH')

    def test_witness_scope(self):
        w=replace(self.b.witness,scope=replace(self.b.witness.scope,task_id='other'))
        self.assertEqual(self.check(witness=w,witness_reference=w).reason,'WA_SCOPE_MISMATCH')

    def test_witness_reference_missing(self): self.assertEqual(self.check(witness_reference=None).reason,'WA_REFERENCE_MISSING')
