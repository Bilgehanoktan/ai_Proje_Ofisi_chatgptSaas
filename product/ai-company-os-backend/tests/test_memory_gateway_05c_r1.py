"""MEM-05C: exact-source cross-owner diagnostic; no provider, grant or product write."""
from dataclasses import replace
from hashlib import sha256
import unittest

from app.core.agent_runtime.joint_context import JointContext, joint_context_digest
from app.core.agent_runtime.memory_witness import inspect_witnessed_context
from app.engines.memory_engine.snapshot_store import publish_snapshot
from app.engines.model_gateway.provider_contract import ProviderKind
from app.engines.model_gateway.runtime_binding import invocation_digest
from app.engines.model_gateway.profile_registry import profile_digest, catalog_digest
from app.engines.model_gateway.router import metrics_digest, policy_digest
from app.engines.model_gateway.routing_decision import make_routing_decision, routing_decision_digest
from app.engines.model_gateway.invocation_route_binding import InvocationRouteContext
from app.engines.model_gateway.reservation_usage_receipt import ReceiptReadback, make_receipt_lookup
from app.engines.model_gateway.token_accounting import ReservationEvidence, accounting_evidence_digest
from app.engines.model_gateway.durable_receipt_adapter import OwnerReceiptSnapshot, owner_snapshot_digest
from app.engines.model_gateway.provider_preflight import inspect_provider_preflight
from app.engines.model_gateway.runtime_model_review import inspect_runtime_model
from app.engines.budget_engine.reservation_review import BudgetSnapshot
import test_memory_witness_0209 as memory_fixture
import test_router_cost_review as route_fixture


class MemoryGatewayTests(unittest.TestCase):
    def setUp(self):
        self.w = memory_fixture.MemoryWitnessTests()
        self.w.setUp()
        self.addCleanup(self.w.doCleanups)
        self.b = self.w.b
        self.f = self.b.f
        self.raw = self.w.j.raw
        self.route = route_fixture.RouteTests()
        self.route.setUp()
        self.ctx, self.owner = self.build()

    def build(self, raw=None, key="mem-gateway-invocation"):
        raw = self.raw if raw is None else raw
        f, t, reg = self.f, self.route, self.b.registry
        profiles = tuple(replace(p, adapter=a) for p,a in zip(t.profiles,reg))
        keys = tuple(profile_digest(p,reg) for p in profiles)
        metrics = tuple(replace(m,profile_digest=k,cost=replace(m.cost,profile_digest=k))
                        for m,k in zip(t.metrics,keys))
        q = replace(t.query,scope=f.scope,requested=reg[0].capabilities)
        p = replace(t.policy,scope=f.scope,catalog_pin=catalog_digest(profiles,reg,f.scope),
                    allowed=keys,metrics_pin=metrics_digest(metrics),
                    policy_epoch=f.clock.policy_epoch,witness_epoch=f.clock.witness_epoch)
        record = make_routing_decision(q,profiles,reg,p,policy_digest(p),metrics,
                                       f.clock.policy_epoch,f.clock.witness_epoch)
        req = replace(self.b.envelope.request,provider=ProviderKind.SAMPLE,
                      requested=q.requested,max_output_tokens=q.output_tokens,
                      input_digest=sha256(raw).hexdigest())
        e = replace(self.b.envelope,request=req,idempotency_key=key,
                    reservation_ref="mem-gateway-reservation",sample_cost_ceiling_minor=15)
        ctx = InvocationRouteContext(e,reg,invocation_digest(e,reg),f.run,f.lease,f.clock,
                    raw,record,routing_decision_digest(record),profiles,metrics,keys[0],q.input_tokens)
        lookup = make_receipt_lookup(ctx,"budget")
        reserve = ReservationEvidence(lookup.binding,"budget",e.reservation_ref,15,"1"*64)
        budget = BudgetSnapshot(f.scope,"budget",4,"USD",100,15,0,False,
                                f.clock.policy_epoch,f.clock.witness_epoch,"d"*64)
        rb = ReceiptReadback(lookup,4,"d"*64,reserve)
        owner = OwnerReceiptSnapshot("snapshot-1","owner-tx-1",1,budget,rb,
                                     accounting_evidence_digest(reserve),None,None)
        return ctx,owner

    def memory(self, ctx=None):
        ctx = self.ctx if ctx is None else ctx
        j = JointContext(self.b.pin,ctx.envelope)
        r = inspect_witnessed_context(j,ctx.registry,joint_context_digest(j,ctx.registry),
                self.b.store.path,ctx.current_run,ctx.current_lease,ctx.clock,ctx.raw,
                self.w.reader,self.w.latest,self.w.pub)
        self.assertEqual(r.decision,"DENY")
        for flag in ("retrieval_allowed","release_allowed","provider_call_allowed",
                     "dispatch_allowed","spend_allowed","independent_verified","retry_allowed"):
            self.assertIs(getattr(r,flag),False)
        return r

    def gateway(self, ctx=None, owner=None, **changes):
        ctx = self.ctx if ctx is None else ctx
        owner = self.owner if owner is None else owner
        args = dict(ctx=ctx,snapshot=owner,reference=owner,budget_reference=owner.budget,
                    expected_pin=owner_snapshot_digest(owner))
        args.update(changes)
        r = inspect_provider_preflight(**args)
        self.assertEqual(r.decision,"HOLD")
        for flag in ("provider_call_allowed","spend_allowed","dispatch_allowed"):
            self.assertIs(getattr(r,flag),False)
        self.assertIsNone(r.actual_cost_minor)
        self.assertIsNone(r.selected_model)
        return r

    def test_same_span_same_invocation_both_match_only(self):
        before = self.b.store.path.read_bytes(),self.w.path.read_bytes()
        self.assertEqual(self.memory().reason,"D0_WITNESSED_CONTEXT_MATCH_ONLY")
        self.assertEqual(self.gateway().reason,"D0_PROVIDER_PREFLIGHT_MATCH_ONLY")
        self.assertEqual(self.gateway().invocation_pin,self.ctx.invocation_pin)
        self.assertEqual(self.memory().reason,"D0_WITNESSED_CONTEXT_MATCH_ONLY")
        self.assertEqual(before,(self.b.store.path.read_bytes(),self.w.path.read_bytes()))

    def test_gateway_match_does_not_prove_source_span(self):
        ctx, owner = self.build(raw=b"other")
        self.assertEqual(self.gateway(ctx,owner).reason,"D0_PROVIDER_PREFLIGHT_MATCH_ONLY")
        self.assertFalse(self.memory(ctx).structural_match)

    def test_independent_matches_can_reference_different_invocations(self):
        ctx, owner = self.build(key="different-invocation")
        self.assertTrue(self.memory().structural_match)
        self.assertEqual(self.gateway(ctx,owner).reason,"D0_PROVIDER_PREFLIGHT_MATCH_ONLY")
        self.assertNotEqual(ctx.invocation_pin,self.ctx.invocation_pin)

    def test_signed_memory_head_is_not_invocation_authority(self):
        ctx, owner = self.build(key="different-invocation")
        self.assertTrue(self.memory(ctx).structural_match)
        self.assertNotEqual(ctx.invocation_pin,self.ctx.invocation_pin)
        self.assertEqual(self.gateway(ctx,owner).reason,"D0_PROVIDER_PREFLIGHT_MATCH_ONLY")

    def test_old_owner_receipt_not_reusable_for_new_invocation(self):
        ctx, _ = self.build(key="different-invocation")
        self.assertTrue(self.memory(ctx).structural_match)
        self.assertIsNone(self.gateway(ctx).invocation_pin)

    def test_missing_owner_reference_and_unknown_budget_hold(self):
        self.assertTrue(self.memory().structural_match)
        self.assertIsNone(self.gateway(reference=None).invocation_pin)
        owner=replace(self.owner,budget=replace(self.owner.budget,unknown_cost=True))
        self.assertIsNone(self.gateway(owner=owner).invocation_pin)

    def test_route_drift_cannot_use_memory_match(self):
        self.assertTrue(self.memory().structural_match)
        self.assertIsNone(self.gateway(replace(self.ctx,route_pin="0"*64)).invocation_pin)

    def test_owner_revision_drift_holds(self):
        self.assertTrue(self.memory().structural_match)
        self.assertIsNone(self.gateway(reference=replace(self.owner,owner_revision=2)).invocation_pin)

    def test_memory_revocation_after_gateway_match_requires_recheck(self):
        self.assertTrue(self.memory().structural_match)
        self.assertEqual(self.gateway().reason,"D0_PROVIDER_PREFLIGHT_MATCH_ONLY")
        publish_snapshot(self.b.store.path,self.b.store.revoke(),self.b.pin)
        self.assertFalse(self.memory().structural_match)
        self.assertEqual(self.gateway().reason,"D0_PROVIDER_PREFLIGHT_MATCH_ONLY")
        # Disposable unsigned snapshot update: old witness cannot certify new memory.
        # No effect is dispatched.

    def test_runtime_drift_still_holds(self):
        self.assertTrue(self.memory().structural_match)
        r=inspect_runtime_model(self.ctx,replace(self.f.run,attempt=2),self.f.lease,
                                self.f.clock,self.owner,self.owner,self.owner.budget,
                                owner_snapshot_digest(self.owner))
        self.assertEqual(r.reason,"RUNTIME_MODEL_DRIFT_HOLD")
        self.assertFalse(r.provider_call_allowed or r.spend_allowed or r.dispatch_allowed)


if __name__=="__main__":
    unittest.main(verbosity=2)
