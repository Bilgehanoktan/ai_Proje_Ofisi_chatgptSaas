"""Real W5 modules, synthetic references only; no provider or DB calls."""
from dataclasses import replace
from hashlib import sha256
import unittest
import test_router_cost_review as fixtures
from app.core.agent_runtime.lifecycle import RunState, RunObservation, LeaseObservation, ClockSample
from app.engines.model_gateway.provider_contract import ProviderRequest, ProviderKind
from app.engines.model_gateway.runtime_binding import InvocationEnvelope, invocation_digest
from app.engines.model_gateway.routing_decision import make_routing_decision, routing_decision_digest
from app.engines.model_gateway.router import policy_digest
from app.engines.model_gateway.invocation_route_binding import InvocationRouteContext, inspect_invocation_route
from app.engines.model_gateway.reservation_usage_receipt import (ReceiptReadback, make_receipt_lookup,
    receipt_readback_digest, inspect_receipt_readback)
from app.engines.model_gateway.token_accounting import (ReservationEvidence, UsageEvidence,
    ReconciliationEvidence, accounting_evidence_digest)
from app.engines.budget_engine.reservation_review import BudgetSnapshot


class InvocationReceiptTests(unittest.TestCase):
    def setUp(self):
        f=fixtures.RouteTests(); f.setUp(); self.f=f
        self.record=make_routing_decision(f.query,f.profiles,f.registry,f.policy,policy_digest(f.policy),f.metrics,2,3)
        s=f.query.scope
        run=RunObservation(s,RunState.RUNNING,3,1)
        lease=LeaseObservation(s,"lease","grant",1,0,1,2,3,100,10)
        raw=b"synthetic input"
        req=ProviderRequest(s,ProviderKind.SAMPLE,sha256(raw).hexdigest(),f.query.requested,(),f.query.output_tokens)
        env=InvocationEnvelope(run,lease,req,*f.registry,"per-call-reservation","invocation-key",15)
        self.ctx=InvocationRouteContext(env,f.registry,invocation_digest(env,f.registry),run,lease,ClockSample(11,2,3,10),raw,
            self.record,routing_decision_digest(self.record),f.profiles,f.metrics,f.keys[0],f.query.input_tokens)
        lookup=make_receipt_lookup(self.ctx,"budget")
        b=lookup.binding
        self.r=ReservationEvidence(b,"budget",env.reservation_ref,15,"1"*64)
        self.u=UsageEvidence(b,35,8,6,"2"*64)
        self.c=ReconciliationEvidence(b,accounting_evidence_digest(self.r),accounting_evidence_digest(self.u),6,9,"3"*64)
        self.budget=BudgetSnapshot(s,"budget",4,"USD",100,15,6,False,2,3,"d"*64)
        self.rb=ReceiptReadback(lookup,4,"d"*64,self.r,self.u,self.c)

    def invocation(self,ctx=None):
        a=inspect_invocation_route(self.ctx if ctx is None else ctx)
        self.assertEqual(a.decision,"HOLD")
        self.assertFalse(a.provider_call_allowed or a.spend_allowed or a.dispatch_allowed)
        return a

    def with_env(self,**kw):
        e=replace(self.ctx.envelope,**kw)
        return replace(self.ctx,envelope=e,invocation_pin=invocation_digest(e,self.ctx.registry))

    def receipts(self,rb=None,budget=None,**kw):
        rb=self.rb if rb is None else rb
        budget=self.budget if budget is None else budget
        args=dict(ctx=self.ctx,budget=budget,budget_reference=budget,readback=rb,
                  expected_readback_pin=receipt_readback_digest(rb))
        for name in ("reservation","usage","reconciliation"):
            obj=getattr(rb,name)
            args[name+"_pin"]=accounting_evidence_digest(obj) if obj is not None else None
        args.update(kw)
        a=inspect_receipt_readback(**args)
        self.assertEqual(a.decision,"HOLD")
        self.assertFalse(a.provider_call_allowed or a.spend_allowed or a.settlement_allowed or a.dispatch_allowed)
        return a

    def test_route_and_envelope_match(self):
        a=self.invocation(); self.assertEqual(a.reason,"D0_INVOCATION_ROUTE_MATCH_ONLY")
        self.assertEqual(a.binding,self.rb.lookup.binding)

    def test_wrong_run_or_attempt(self):
        for change in (dict(version=4),dict(attempt=2),dict(attempt=True),dict(state=RunState.VERIFYING)):
            with self.subTest(change=change):
                self.assertIsNone(self.invocation(replace(self.ctx,current_run=replace(self.ctx.current_run,**change))).binding)

    def test_lease_fence_and_clock(self):
        for c in (replace(self.ctx,current_lease=replace(self.ctx.current_lease,fence=2)),
                  replace(self.ctx,clock=replace(self.ctx.clock,now_tick=100)),
                  replace(self.ctx,clock=replace(self.ctx.clock,policy_epoch=4)),
                  replace(self.ctx,clock=replace(self.ctx.clock,witness_epoch=4))):
            self.assertIsNone(self.invocation(c).binding)

    def test_raw_and_invocation_pin(self):
        self.assertEqual(self.invocation(replace(self.ctx,raw=b"changed")).reason,"MODEL_INPUT_DIGEST_HOLD")
        self.assertEqual(self.invocation(replace(self.ctx,invocation_pin="b"*64)).reason,"MODEL_INVOCATION_DIGEST_HOLD")

    def test_exact_query_token_and_capability_binding(self):
        for c in (replace(self.ctx,input_tokens=39),replace(self.ctx,input_tokens=True),
                  self.with_env(request=replace(self.ctx.envelope.request,max_output_tokens=9))):
            self.assertIsNone(self.invocation(c).binding)

    def test_profile_not_selected_or_swapped(self):
        self.assertEqual(self.invocation(replace(self.ctx,profile_pin=self.f.keys[1])).reason,"INVOCATION_PRIMARY_PROFILE_HOLD")
        self.assertIsNone(self.record.selected_model)

    def test_route_replay_pin_and_metric(self):
        for c in (replace(self.ctx,route_pin="0"*64),replace(self.ctx,metrics=())):
            self.assertEqual(self.invocation(c).reason,"INVOCATION_ROUTE_REPLAY_HOLD")

    def test_alternate_excluded(self):
        f=self.f; p=replace(f.policy,allowed=(f.keys[0],))
        record=make_routing_decision(f.query,f.profiles,f.registry,p,policy_digest(p),f.metrics,2,3)
        c=replace(self.ctx,record=record,route_pin=routing_decision_digest(record))
        self.assertEqual(self.invocation(c).reason,"INVOCATION_ALTERNATE_PROFILE_HOLD")

    def test_cost_ceiling_both_bounds(self):
        for ceiling in (6,10,31):
            self.assertEqual(self.invocation(self.with_env(sample_cost_ceiling_minor=ceiling)).reason,"INVOCATION_COST_CEILING_HOLD")

    def test_receipt_lookup_idempotency_and_reservation(self):
        for change in (dict(reservation_ref="other"),dict(idempotency_key="other")):
            c=self.with_env(**change)
            self.assertNotEqual(make_receipt_lookup(c,"budget"),self.rb.lookup)
            self.assertEqual(self.receipts(ctx=c).reason,"RECEIPT_READBACK_PIN_OR_SCOPE_HOLD")

    def test_complete_receipt_match_still_hold(self):
        a=self.receipts(budget=replace(self.budget,outstanding_minor=0)); self.assertEqual(a.reason,"D0_RECEIPT_MATCH_ONLY_OWNER_CUSTODY_HOLD")
        self.assertEqual((a.accounting.estimated_minor,a.accounting.reserved_minor,a.accounting.actual_minor,a.accounting.released_minor),(7,15,6,9))

    def test_missing_readback_or_wrong_type(self):
        self.assertEqual(self.receipts(readback=None).reason,"INVOCATION_RECEIPT_MISSING_HOLD")
        self.assertEqual(self.receipts(readback=self.r).reason,"RECEIPT_REFERENCE_INVALID_HOLD")

    def test_budget_reference_unknown_and_scope(self):
        for b in (replace(self.budget,revision=3),replace(self.budget,currency="EUR"),replace(self.budget,policy_epoch=4)):
            self.assertEqual(self.receipts(budget_reference=b).reason,"RECEIPT_BUDGET_REFERENCE_HOLD")
        self.assertEqual(self.receipts(budget=replace(self.budget,unknown_cost=True)).reason,"UNKNOWN_COST_HOLD")

    def test_budget_revision_source_pin(self):
        for change in (dict(budget_revision=3),dict(budget_source_pin="e"*64)):
            self.assertEqual(self.receipts(replace(self.rb,**change)).reason,"RECEIPT_READBACK_PIN_OR_SCOPE_HOLD")
        self.assertEqual(self.receipts(expected_readback_pin="e"*64).reason,"RECEIPT_READBACK_PIN_OR_SCOPE_HOLD")

    def test_reservation_identity_and_ceiling(self):
        for change in (dict(budget_id="other"),dict(reservation_id="other"),dict(reserved_minor=14)):
            self.assertEqual(self.receipts(replace(self.rb,reservation=replace(self.r,**change))).reason,"RECEIPT_RESERVATION_ID_OR_CEILING_HOLD")

    def test_unknown_is_not_zero(self):
        a=self.receipts(replace(self.rb,outcome_unknown=True)); self.assertEqual(a.reason,"UNKNOWN_USAGE_HOLD")
        self.assertIsNone(a.accounting.actual_minor); self.assertIsNone(a.accounting.released_minor)

    def test_missing_usage_and_reconciliation(self):
        self.assertEqual(self.receipts(replace(self.rb,usage=None,reconciliation=None)).reason,"USAGE_MISSING_HOLD")
        self.assertEqual(self.receipts(replace(self.rb,reconciliation=None)).reason,"RECONCILIATION_MISSING_HOLD")

    def test_independent_evidence_pins_required(self):
        for name in ("reservation_pin","usage_pin","reconciliation_pin"):
            self.assertEqual(self.receipts(**{name:None}).reason,"ACCOUNTING_EVIDENCE_BINDING_HOLD")

    def test_budget_aggregate_sanity_not_membership(self):
        self.assertEqual(self.receipts(budget=replace(self.budget,limit_minor=10)).reason,"RECEIPT_BUDGET_LIMIT_HOLD")
        self.assertEqual(self.receipts(budget=replace(self.budget,recognized_cost_minor=5)).reason,"RECEIPT_RECOGNIZED_BALANCE_HOLD")
        self.assertEqual(self.receipts(replace(self.rb,reconciliation=None),budget=replace(self.budget,outstanding_minor=14)).reason,"RECEIPT_OUTSTANDING_BALANCE_HOLD")

    def test_actual_over_invocation_ceiling(self):
        r=replace(self.r,reserved_minor=20); u=replace(self.u,actual_minor=16)
        a=self.receipts(replace(self.rb,reservation=r,usage=u,reconciliation=None),budget=replace(self.budget,outstanding_minor=20))
        self.assertEqual(a.reason,"RECEIPT_INVOCATION_COST_OVERRUN_HOLD")
        self.assertFalse(a.settlement_allowed)

    def test_reconciliation_tamper_and_alias(self):
        self.assertEqual(self.receipts(replace(self.rb,reconciliation=replace(self.c,released_minor=8))).reason,"RECONCILIATION_MISMATCH_HOLD")
        self.assertEqual(self.receipts(replace(self.rb,usage=replace(self.u,receipt_pin=self.r.receipt_pin))).reason,"ACCOUNTING_RECEIPT_ALIAS_HOLD")

if __name__=="__main__": unittest.main()
