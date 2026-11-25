"""D0 oracle candidates; NOT_RUN. No IO, real authority or financial writes."""
import unittest
from dataclasses import replace
from hashlib import sha256
from app.core.agent_runtime.lifecycle import Scope, LeaseObservation, ClockSample
from app.core.transaction.review import LogicalIntent, Operation, RoleObservation, required_roles
from app.core.transaction.readback_review import HeadReadback, AdmissionPin, inspect_admission
from app.engines.budget_engine.reservation_review import BudgetSnapshot, ReservationRequest, inspect_reservation
from app.observability.finance_projection import project_finance
from app.core.policy.iv_review import ArtifactPin, TrustPlane, IVObservation
from app.core.policy.receipt_review import ReceiptPin, inspect_receipt
from app.engines.office_engine.freshness import ProjectionPin, inspect_projection


class Review0161Tests(unittest.TestCase):
    def setUp(self):
        self.s = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,'research','demo-run','demo-agent','demo-principal')
        self.b = BudgetSnapshot(self.s,'budget-1',1,'TRY',100,20,30,False,2,3,'a'*64)
        self.q = ReservationRequest(self.s,'budget-1',1,'TRY',25,'idem-1',2,3)
        self.i = LogicalIntent(self.s,Operation.ADMISSION,4,'b'*64,'effect-1','idem-1','demo-grant','demo-lease','budget-1',2,3)
        self.l = LeaseObservation(self.s,'demo-lease','demo-grant',1,1,1,2,3,60,40)
        self.c = ClockSample(50,2,3,20)
        self.rows = tuple(RoleObservation(r,'row-'+r,self.s,'b'*64,'tx-1',4,2,3) for r in sorted(required_roles(self.i)))
        self.h = HeadReadback(self.s,4,'tx-1','b'*64,2,3)
        self.a = AdmissionPin(self.s,'admission-1','demo-grant','demo-lease','budget-1','b'*64,1,2,3)
        self.raw = b'demo'
        self.pin = ArtifactPin(self.s,sha256(self.raw).hexdigest(),1,2,3)
        qa,iv,rel = (TrustPlane(p+'-principal',p+'-root',p+'-admin',p+'-recovery') for p in ('qa','iv','release'))
        self.o = IVObservation(self.pin,self.pin,qa,iv,rel,'receipt-1')
        self.r = ReceiptPin('receipt-1',self.pin,'iv-principal','iv-root','key-1',1,self.pin.artifact_digest,10,60,False)
        self.p = ProjectionPin('synthetic-tenant','demo-world','A0_SAMPLE_ONLY','layout-d3-demo',1,2,3,'a'*64,40)

    def admission(self, head=None, admission=None, request=None):
        return inspect_admission(self.i,self.rows,head or self.h,self.h,admission or self.a,self.a,self.l,self.l,self.c,request or self.q,self.b,self.b)

    def receipt(self, receipt=None, readback=None, now=50, clear=True):
        r=receipt or self.r
        return inspect_receipt(self.o,self.pin,r,r,self.raw,self.raw if readback is None else readback,now,clear)

    def test_capacity_no_spend(self):
        r=inspect_reservation(self.q,self.b,self.b)
        self.assertEqual(r.remaining_minor,25);self.assertFalse(r.spend_allowed);self.assertFalse(r.reservation_created)
        p=project_finance(r);self.assertIsNone(p.actual_cost_minor);self.assertIsNone(p.authorized_remaining_minor)

    def test_limit_and_currency(self):
        self.assertEqual(inspect_reservation(replace(self.q,amount_minor=51),self.b,self.b).reason,'BUDGET_LIMIT_HOLD')
        self.assertEqual(inspect_reservation(replace(self.q,currency='USD'),self.b,self.b).reason,'BUDGET_SCOPE_CAS_CURRENCY_EPOCH_HOLD')

    def test_unknown_cost(self):
        b=replace(self.b,unknown_cost=True)
        self.assertEqual(inspect_reservation(self.q,b,b).reason,'UNKNOWN_COST_HOLD')

    def test_budget_cas_and_bool(self):
        self.assertEqual(inspect_reservation(self.q,replace(self.b,revision=2),self.b).reason,'BUDGET_REFERENCE_HOLD')
        self.assertEqual(inspect_reservation(replace(self.q,amount_minor=True),self.b,self.b).reason,'BUDGET_REQUEST_INVALID')

    def test_admission_no_commit(self):
        r=self.admission();self.assertTrue(r.structural_match);self.assertFalse(r.committed);self.assertFalse(r.atomicity_proven)

    def test_head_mismatch(self):
        self.assertEqual(self.admission(head=replace(self.h,version=5)).reason,'HEAD_REFERENCE_CAS_HOLD')

    def test_admission_fence(self):
        self.assertEqual(self.admission(admission=replace(self.a,fence=2)).reason,'ADMISSION_REFERENCE_HOLD')

    def test_reservation_binding(self):
        self.assertEqual(self.admission(request=replace(self.q,idempotency_key='other')).reason,'RESERVATION_INTENT_BINDING_HOLD')

    def test_admission_reference_bool(self):
        a=replace(self.a,fence=True)
        r=inspect_admission(self.i,self.rows,self.h,self.h,self.a,a,self.l,self.l,self.c,self.q,self.b,self.b)
        self.assertEqual(r.reason,'ADMISSION_REFERENCE_HOLD')

    def test_head_transaction_binding(self):
        h=replace(self.h,transaction_ref='other-tx')
        r=inspect_admission(self.i,self.rows,h,h,self.a,self.a,self.l,self.l,self.c,self.q,self.b,self.b)
        self.assertEqual(r.reason,'READBACK_TRANSACTION_HOLD')

    def test_receipt_reference_bool(self):
        r=inspect_receipt(self.o,self.pin,self.r,replace(self.r,key_revision=True),self.raw,self.raw,50,True)
        self.assertEqual(r.reason,'IV_RECEIPT_REFERENCE_HOLD')

    def test_receipt_match_never_release(self):
        r=self.receipt();self.assertTrue(r.structural_match);self.assertFalse(r.release_ready);self.assertFalse(r.receipt_issued)

    def test_receipt_revoked_or_expired(self):
        self.assertEqual(self.receipt(replace(self.r,revoked=True)).reason,'IV_KEY_OR_VALIDITY_HOLD')
        self.assertEqual(self.receipt(now=60).reason,'IV_KEY_OR_VALIDITY_HOLD')

    def test_receipt_artifact_swap(self):
        self.assertEqual(self.receipt(readback=b'other').reason,'IV_BYTES_READBACK_HOLD')

    def test_tombstone_unknown(self):
        self.assertEqual(self.receipt(clear=None).reason,'IV_TOMBSTONE_UNKNOWN_HOLD')

    def test_projection_matching_never_live(self):
        r=inspect_projection(self.p,self.p,'layout-d3-demo',50,20)
        self.assertTrue(r.structural_match);self.assertFalse(r.render_live_allowed)

    def test_projection_layout_stale(self):
        self.assertEqual(inspect_projection(self.p,self.p,'draft-hybrid-floor-1',50,20).reason,'LAYOUT_REVISION_HOLD')
        self.assertEqual(inspect_projection(self.p,self.p,'layout-d3-demo',61,20).reason,'PROJECTION_STALE_HOLD')
