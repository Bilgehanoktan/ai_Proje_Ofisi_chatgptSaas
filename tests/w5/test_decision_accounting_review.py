"""D0 integration of the real W5 router with immutable evidence/accounting; no IO."""
from dataclasses import FrozenInstanceError, replace
import unittest
import test_router_cost_review as fixture
from app.engines.model_gateway.router import policy_digest, metrics_digest
from app.engines.model_gateway.routing_decision import (
    make_routing_decision, routing_decision_digest, verify_routing_decision,
)
from app.engines.model_gateway.token_accounting import (
    UsageBinding, ReservationEvidence, UsageEvidence, ReconciliationEvidence,
    accounting_evidence_digest, inspect_token_accounting,
)


class DecisionAccountingTests(unittest.TestCase):
    def setUp(self):
        f = fixture.RouteTests()
        f.setUp()
        self.f = f
        self.args = dict(query=f.query,profiles=f.profiles,registry=f.registry,policy=f.policy,
                         expected_policy_pin=policy_digest(f.policy),metrics=f.metrics,
                         current_policy_epoch=2,current_witness_epoch=3)
        self.record = make_routing_decision(**self.args)
        self.pin = routing_decision_digest(self.record)
        self.binding = UsageBinding(f.query.scope,0,self.pin,f.keys[0],"e"*64,"USD",2,3)
        self.reservation = ReservationEvidence(self.binding,"budget","reservation",10,"1"*64)
        self.usage = UsageEvidence(self.binding,35,8,6,"2"*64)
        self.reconciliation = ReconciliationEvidence(self.binding,accounting_evidence_digest(self.reservation),
                                                      accounting_evidence_digest(self.usage),6,4,"3"*64)

    def replay(self, record=None, pin=None, **kw):
        args=dict(profiles=self.f.profiles,registry=self.f.registry,metrics=self.f.metrics,
                  current_policy_epoch=2,current_witness_epoch=3)
        args.update(kw)
        return verify_routing_decision(self.record if record is None else record,
                                       self.pin if pin is None else pin,**args)

    def review(self, **kw):
        args=dict(binding=self.binding,record=self.record,expected_route_pin=self.pin,
                  profiles=self.f.profiles,registry=self.f.registry,metrics=self.f.metrics,
                  current_policy_epoch=2,current_witness_epoch=3)
        args.update(kw)
        r=inspect_token_accounting(**args)
        self.assertEqual(r.decision,"HOLD")
        self.assertFalse(r.spend_allowed or r.provider_call_allowed or r.settlement_allowed or r.dispatch_allowed)
        return r

    def observations(self, reservation=True, usage=True, reconciliation=True):
        result={}
        for name, include in (("reservation",reservation),("usage",usage),("reconciliation",reconciliation)):
            if include:
                e=getattr(self,name)
                result[name]=e
                result[name+"_pin"]=accounting_evidence_digest(e)
        return result

    def test_record_matches_real_router(self):
        self.assertTrue(self.replay())
        route=self.f.route()
        self.assertEqual((self.record.candidates,self.record.excluded,self.record.reason),
                         (route.candidates,route.excluded,route.reason))
        self.assertIsNone(self.record.selected_model)
        self.assertFalse(self.record.provider_call_allowed or self.record.spend_allowed or self.record.dispatch_allowed)

    def test_frozen_record_and_observations(self):
        for obj,name,value in ((self.record,"reason","ALLOW"),(self.reservation,"reserved_minor",999),(self.binding,"attempt",1)):
            with self.subTest(obj=type(obj).__name__), self.assertRaises(FrozenInstanceError):
                setattr(obj,name,value)

    def test_tampered_cost_rejected_even_rehashed(self):
        cs=self.record.candidates
        changed=replace(self.record,candidates=(replace(cs[0],estimated_minor=cs[0].estimated_minor+1),cs[1]))
        self.assertFalse(self.replay(changed))
        self.assertFalse(self.replay(changed,routing_decision_digest(changed)))

    def test_order_independent_replay(self):
        self.assertTrue(self.replay(profiles=tuple(reversed(self.f.profiles)),metrics=tuple(reversed(self.f.metrics))))

    def test_pin_epoch_or_metrics_changes(self):
        for kw in ({"pin":"0"*64},{"current_policy_epoch":3},{"current_witness_epoch":4},
                   {"metrics":(replace(self.f.metrics[0],latency_upper_ms=99),self.f.metrics[1])}):
            with self.subTest(kw=kw): self.assertFalse(self.replay(**kw))

    def test_invalid_references_do_not_create_records(self):
        for kw in ({"expected_policy_pin":"0"*64},{"current_policy_epoch":3},
                   {"query":replace(self.f.query,input_tokens=True)},{"metrics":()}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                make_routing_decision(**(self.args|kw))

    def test_no_candidates_and_exclusions_recorded(self):
        p=replace(self.f.policy,max_cost_minor=0)
        r=make_routing_decision(**(self.args|dict(policy=p,expected_policy_pin=policy_digest(p))))
        self.assertEqual(r.reason,"NO_ROUTE_CANDIDATE_HOLD")
        self.assertEqual(len(r.excluded),2)
        self.assertTrue(self.replay(r,routing_decision_digest(r)))

    def test_duplicate_and_incomplete_records(self):
        c=self.record.candidates[0]
        with self.assertRaises(ValueError): routing_decision_digest(replace(self.record,candidates=(c,c)))
        incomplete=replace(self.record,candidates=(c,))
        self.assertFalse(self.replay(incomplete,routing_decision_digest(incomplete)))

    def test_estimate_not_reservation_or_actual(self):
        r=self.review()
        self.assertEqual((r.estimated_minor,r.reserved_minor,r.actual_minor,r.reconciled_minor),(7,None,None,None))
        self.assertEqual(r.reason,"RESERVATION_MISSING_HOLD")

    def test_reserved_not_actual(self):
        r=self.review(**self.observations(usage=False,reconciliation=False))
        self.assertEqual((r.estimated_minor,r.reserved_minor,r.actual_minor),(7,10,None))
        self.assertEqual(r.reason,"USAGE_MISSING_HOLD")

    def test_unknown_usage_never_zero_filled(self):
        r=self.review(**self.observations(),outcome_unknown=True)
        self.assertEqual(r.reason,"UNKNOWN_USAGE_HOLD")
        self.assertEqual((r.reserved_minor,r.actual_minor,r.reconciled_minor,r.released_minor),(10,None,None,None))

    def test_complete_match_stays_hold(self):
        r=self.review(**self.observations())
        self.assertEqual(r.reason,"D0_RECONCILIATION_MATCH_ONLY")
        self.assertEqual((r.estimated_minor,r.reserved_minor,r.actual_minor,r.reconciled_minor,r.released_minor),(7,10,6,6,4))
        self.assertEqual((r.actual_input_tokens,r.actual_output_tokens),(35,8))

    def test_actual_not_recomputed_from_tokens(self):
        r=self.review(**self.observations(reconciliation=False))
        self.assertEqual(r.actual_minor,6)
        self.assertIsNone(r.reconciled_minor)
        self.assertEqual(r.reason,"RECONCILIATION_MISSING_HOLD")

    def test_zero_usage_explicit_not_unknown(self):
        usage=replace(self.usage,input_tokens=0,output_tokens=0,actual_minor=0)
        r=self.review(**(self.observations(reconciliation=False)|dict(usage=usage,usage_pin=accounting_evidence_digest(usage))))
        self.assertEqual((r.actual_minor,r.actual_input_tokens,r.actual_output_tokens),(0,0,0))
        self.assertIsNone(r.reconciled_minor)

    def test_route_binding_failures(self):
        for change in ({"scope":replace(self.binding.scope,task_id="different-task")},{"currency":"EUR"},
                       {"policy_epoch":3},{"witness_epoch":4},{"route_pin":"f"*64},{"attempt":True}):
            with self.subTest(change=change):
                self.assertEqual(self.review(binding=replace(self.binding,**change)).reason,"ACCOUNTING_ROUTE_BINDING_HOLD")
        self.assertEqual(self.review(binding=replace(self.binding,profile_pin="f"*64)).reason,"ACCOUNTING_PROFILE_HOLD")

    def test_missing_wrong_and_stale_evidence_pins(self):
        for kw in ({"reservation":self.reservation},{"reservation_pin":"1"*64},
                   {"reservation":replace(self.reservation,reserved_minor=9),"reservation_pin":accounting_evidence_digest(self.reservation)}):
            with self.subTest(kw=kw): self.assertIn(self.review(**kw).reason,("ACCOUNTING_EVIDENCE_BINDING_HOLD","ACCOUNTING_EVIDENCE_MISSING_HOLD"))

    def test_attempt_and_invocation_mismatch(self):
        for b in (replace(self.binding,attempt=1),replace(self.binding,invocation_pin="f"*64)):
            r=self.review(binding=b,**self.observations())
            self.assertEqual(r.reason,"ACCOUNTING_EVIDENCE_BINDING_HOLD")

    def test_receipt_alias_rejected(self):
        usage=replace(self.usage,receipt_pin=self.reservation.receipt_pin)
        r=self.review(**(self.observations(reconciliation=False)|dict(usage=usage,usage_pin=accounting_evidence_digest(usage))))
        self.assertEqual(r.reason,"ACCOUNTING_RECEIPT_ALIAS_HOLD")

    def test_insufficient_reservation_and_usage_overrun(self):
        res=replace(self.reservation,reserved_minor=6)
        r=self.review(reservation=res,reservation_pin=accounting_evidence_digest(res))
        self.assertEqual(r.reason,"RESERVATION_INSUFFICIENT_HOLD")
        for change in ({"actual_minor":11},{"output_tokens":11},{"input_tokens":41}):
            usage=replace(self.usage,**change)
            r=self.review(**(self.observations(reconciliation=False)|dict(usage=usage,usage_pin=accounting_evidence_digest(usage))))
            self.assertEqual(r.reason,"USAGE_LIMIT_EXCEEDED_HOLD")
            self.assertEqual(r.actual_minor,usage.actual_minor)
            self.assertIsNone(r.reconciled_minor)

    def test_reconciliation_arithmetic_and_evidence_binding(self):
        for change in ({"recognized_minor":5},{"released_minor":5},{"reservation_pin":"0"*64},{"usage_pin":"0"*64}):
            e=replace(self.reconciliation,**change)
            r=self.review(**(self.observations()|dict(reconciliation=e,reconciliation_pin=accounting_evidence_digest(e))))
            self.assertEqual(r.reason,"RECONCILIATION_MISMATCH_HOLD")
            self.assertIsNone(r.released_minor)

    def test_invalid_money_and_token_types(self):
        for e in (replace(self.usage,actual_minor=True),replace(self.usage,output_tokens=-1),
                  replace(self.reservation,reserved_minor=2**63),replace(self.reconciliation,released_minor=1.0)):
            with self.subTest(e=e), self.assertRaises(ValueError): accounting_evidence_digest(e)


if __name__ == "__main__":
    unittest.main()
