"""W5 D/E/F synthetic comparisons; no calls or state changes."""
from dataclasses import replace
import unittest
import test_invocation_receipt_review as fixtures
from app.core.agent_runtime.lifecycle import RunState
from app.engines.model_gateway.provider_contract import ProviderKind
from app.engines.model_gateway.durable_receipt_adapter import (OwnerReceiptSnapshot,
    owner_snapshot_digest, inspect_owner_snapshot)
from app.engines.model_gateway.provider_preflight import inspect_provider_preflight
from app.engines.model_gateway.runtime_model_review import inspect_runtime_model
from app.engines.model_gateway.token_accounting import accounting_evidence_digest


class DurableProviderRuntimeTests(unittest.TestCase):
    def setUp(self):
        f=fixtures.InvocationReceiptTests(); f.setUp(); self.f=f
        self.ctx=f.ctx
        rb=replace(f.rb,usage=None,reconciliation=None)
        self.s=OwnerReceiptSnapshot("snapshot-1","owner-tx-1",1,f.budget,rb,
            accounting_evidence_digest(f.r),None,None)

    def args(self,s=None,**kw):
        s=self.s if s is None else s
        result=dict(ctx=self.ctx,snapshot=s,reference=s,budget_reference=s.budget,
                    expected_pin=owner_snapshot_digest(s))
        result.update(kw)
        return result

    def held(self,r):
        self.assertEqual(r.decision,"HOLD")
        self.assertFalse(r.provider_call_allowed or r.spend_allowed or r.dispatch_allowed)
        for field in ("settlement_allowed","custody_verified","transition_allowed","retry_allowed"):
            self.assertFalse(getattr(r,field,False))
        return r

    def owner(self,s=None,**kw):
        return self.held(inspect_owner_snapshot(**self.args(s,**kw)))

    def preflight(self,s=None,**kw):
        return self.held(inspect_provider_preflight(**self.args(s,**kw)))

    def runtime(self,**kw):
        args=self.args(); args.update(current_run=self.ctx.current_run,current_lease=self.ctx.current_lease,clock=self.ctx.clock)
        args.update(kw)
        return self.held(inspect_runtime_model(**args))

    def test_owner_readback_match_is_not_custody(self):
        r=self.owner(); self.assertEqual(r.reason,"D0_OWNER_SNAPSHOT_MATCH_ONLY")
        self.assertEqual(r.receipt.reason,"USAGE_MISSING_HOLD")
        self.assertIsNone(r.receipt.accounting.actual_minor)

    def test_missing_owner_readback(self):
        self.assertEqual(self.owner(snapshot=None).reason,"OWNER_READBACK_MISSING_HOLD")
        self.assertEqual(self.owner(reference=None).reason,"OWNER_READBACK_MISSING_HOLD")

    def test_owner_pin_and_independent_reference(self):
        for changes in (dict(expected_pin="b"*64),dict(reference=replace(self.s,owner_revision=2)),
                        dict(reference=replace(self.s,transaction_ref="other"))):
            self.assertEqual(self.owner(**changes).reason,"OWNER_SNAPSHOT_REFERENCE_HOLD")

    def test_bad_evidence_pins(self):
        for s in (replace(self.s,reservation_pin="b"*64),replace(self.s,usage_pin="c"*64),
                  replace(self.s,owner_revision=True),replace(self.s,transaction_ref="")):
            with self.assertRaises(ValueError): owner_snapshot_digest(s)

    def test_orphan_reconciliation(self):
        s=replace(self.s,readback=replace(self.s.readback,reconciliation=self.f.c),
                  reconciliation_pin=accounting_evidence_digest(self.f.c))
        with self.assertRaises(ValueError): owner_snapshot_digest(s)

    def test_budget_reference_drift(self):
        self.assertEqual(self.owner(budget_reference=replace(self.s.budget,revision=5)).reason,
                         "RECEIPT_BUDGET_REFERENCE_HOLD")

    def test_budget_binding_mismatch(self):
        with self.assertRaises(ValueError): owner_snapshot_digest(replace(self.s,budget=replace(self.s.budget,revision=5)))

    def test_missing_reservation_not_synthesized(self):
        s=replace(self.s,readback=replace(self.s.readback,reservation=None),reservation_pin=None)
        self.assertEqual(self.owner(s).reason,"RESERVATION_MISSING_HOLD")
        self.assertIsNone(self.preflight(s).invocation_pin)

    def test_unknown_outcome_not_zero(self):
        s=replace(self.s,readback=replace(self.s.readback,outcome_unknown=True))
        r=self.owner(s); self.assertEqual(r.reason,"UNKNOWN_USAGE_HOLD")
        self.assertIsNone(r.receipt.accounting.actual_minor)
        self.assertIsNone(self.preflight(s).invocation_pin)

    def test_unknown_budget(self):
        s=replace(self.s,budget=replace(self.s.budget,unknown_cost=True))
        self.assertEqual(self.owner(s).reason,"UNKNOWN_COST_HOLD")

    def test_lookup_cannot_be_aliased(self):
        rb=replace(self.s.readback,lookup=replace(self.s.readback.lookup,invocation_idempotency_key="other"))
        self.assertEqual(self.owner(replace(self.s,readback=rb)).reason,"OWNER_INVOCATION_BINDING_HOLD")

    def test_preflight_returns_only_reference(self):
        r=self.preflight(); self.assertEqual(r.reason,"D0_PROVIDER_PREFLIGHT_MATCH_ONLY")
        self.assertEqual(r.invocation_pin,self.ctx.invocation_pin)
        self.assertIsNone(r.selected_model); self.assertIsNone(r.actual_cost_minor); self.assertIsNone(r.actual_tokens)

    def test_settled_snapshot_is_not_reusable(self):
        s=replace(self.s,readback=self.f.rb,usage_pin=accounting_evidence_digest(self.f.u),
                  reconciliation_pin=accounting_evidence_digest(self.f.c))
        self.assertEqual(self.owner(s).reason,"D0_OWNER_SNAPSHOT_MATCH_ONLY")
        self.assertEqual(self.preflight(s).reason,"PROVIDER_REPLAY_OR_OUTCOME_HOLD")

    def test_usage_without_reconciliation_is_not_retryable(self):
        s=replace(self.s,readback=replace(self.s.readback,usage=self.f.u),usage_pin=accounting_evidence_digest(self.f.u))
        self.assertIsNone(self.preflight(s).invocation_pin)

    def test_non_sample_provider_blocked(self):
        for kind in ProviderKind:
            if kind is ProviderKind.SAMPLE: continue
            e=replace(self.ctx.envelope,request=replace(self.ctx.envelope.request,provider=kind))
            self.assertIsNone(self.preflight(ctx=replace(self.ctx,envelope=e)).invocation_pin)

    def test_runtime_match_no_transition(self):
        self.assertEqual(self.runtime().reason,"D0_RUNTIME_MODEL_MATCH_ONLY")

    def test_runtime_drift(self):
        for run in (replace(self.ctx.current_run,attempt=2),replace(self.ctx.current_run,version=4),
                    replace(self.ctx.current_run,state=RunState.CANCELLED)):
            self.assertEqual(self.runtime(current_run=run).reason,"RUNTIME_MODEL_DRIFT_HOLD")
        self.assertEqual(self.runtime(current_lease=replace(self.ctx.current_lease,fence=2)).reason,"RUNTIME_MODEL_DRIFT_HOLD")

    def test_runtime_latest_clock(self):
        for clock in (replace(self.ctx.clock,now_tick=100),replace(self.ctx.clock,policy_epoch=4),
                      replace(self.ctx.clock,witness_epoch=4)):
            self.assertIsNone(self.runtime(clock=clock).invocation_pin)

    def test_runtime_invalid_references(self):
        self.assertEqual(self.runtime(current_run=None).reason,"RUNTIME_MODEL_REFERENCE_HOLD")
        self.assertIsNone(self.runtime(snapshot=None).invocation_pin)

if __name__=="__main__": unittest.main()
