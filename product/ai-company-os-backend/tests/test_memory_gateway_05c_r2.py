"""MEM-05C-R2: exercise the real existing readers and original R1 fixtures."""
from dataclasses import replace
from unittest import TestCase, main
from unittest.mock import patch

from app.core.agent_runtime import memory_gateway_review as bridge
from app.core.agent_runtime.joint_context import JointContext, joint_context_digest
from app.core.agent_runtime.memory_witness import witness_sha
from app.engines.memory_engine.snapshot_store import publish_snapshot, _encode, SnapshotPin
from app.engines.model_gateway.durable_receipt_adapter import owner_snapshot_digest
from hashlib import sha256
import test_memory_gateway_05c_r1 as fixture


class MemoryGatewayReviewTests(TestCase):
    def setUp(self):
        self.f = fixture.MemoryGatewayTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.ctx = self.f.ctx
        self.owner = self.f.owner
        self.w = self.f.w
        self.b = self.f.b
        self.j = JointContext(self.b.pin, self.ctx.envelope)

    def review(self, **changes):
        args = dict(context=self.j, expected_joint_pin=joint_context_digest(self.j, self.ctx.registry),
                    ctx=self.ctx, memory_path=self.b.store.path, reader=self.w.reader,
                    expected_witness=self.w.latest, public_key=self.w.pub,
                    snapshot=self.owner, reference=self.owner, budget_reference=self.owner.budget,
                    expected_owner_pin=owner_snapshot_digest(self.owner))
        args.update(changes)
        r = bridge.inspect_memory_gateway(**args)
        self.assertEqual(r.decision, 'HOLD')
        for flag in ('retrieval_allowed', 'release_allowed', 'provider_call_allowed', 'dispatch_allowed',
                     'spend_allowed', 'settlement_allowed', 'transition_allowed', 'retry_allowed',
                     'independent_verified', 'atomicity_verified'):
            self.assertIs(getattr(r, flag), False)
        for attr in ('raw', 'receipt', 'invocation_pin', 'selected_model', 'actual_cost_minor'):
            self.assertFalse(hasattr(r, attr))
        return r

    def rebind(self, ctx, owner):
        j = JointContext(self.b.pin, ctx.envelope)
        return dict(context=j, expected_joint_pin=joint_context_digest(j, ctx.registry), ctx=ctx,
                    snapshot=owner, reference=owner, budget_reference=owner.budget,
                    expected_owner_pin=owner_snapshot_digest(owner))

    def test_exact_match_read_only(self):
        before = self.b.store.path.read_bytes(), self.w.path.read_bytes()
        r = self.review()
        self.assertTrue(r.structural_match)
        self.assertEqual(r.reason, 'D0_MEMORY_GATEWAY_MATCH_ONLY')
        self.assertEqual(before, (self.b.store.path.read_bytes(), self.w.path.read_bytes()))

    def test_two_independent_matches_not_same_invocation(self):
        ctx, owner = self.f.build(key='another-invocation')
        self.assertTrue(self.f.memory().structural_match)
        self.assertEqual(self.f.gateway(ctx, owner).reason, 'D0_PROVIDER_PREFLIGHT_MATCH_ONLY')
        self.assertEqual(self.review(ctx=ctx, snapshot=owner, reference=owner,
                                    budget_reference=owner.budget, expected_owner_pin=owner_snapshot_digest(owner)).reason,
                         'MEMORY_GATEWAY_INVOCATION_BINDING_HOLD')

    def test_rebinding_does_not_prove_authority(self):
        ctx, owner = self.f.build(key='another-invocation')
        self.assertTrue(self.review(**self.rebind(ctx, owner)).structural_match)
        # A new coherent caller-supplied set is still only a diagnostic match.

    def test_exact_span_even_with_recomputed_gateway_pins(self):
        ctx, owner = self.f.build(raw=b'other')
        self.assertEqual(self.f.gateway(ctx, owner).reason, 'D0_PROVIDER_PREFLIGHT_MATCH_ONLY')
        self.assertEqual(self.review(**self.rebind(ctx, owner)).reason, 'MEMORY_GATEWAY_MEMORY_HOLD')

    def test_joint_pin_and_invocation_pin_drift(self):
        for changes in (dict(expected_joint_pin='0'*64), dict(ctx=replace(self.ctx, invocation_pin='0'*64))):
            with self.subTest(changes=changes):
                self.assertEqual(self.review(**changes).reason, 'MEMORY_GATEWAY_INVOCATION_BINDING_HOLD')

    def test_route_and_owner_receipt_drift(self):
        for changes in (dict(ctx=replace(self.ctx, route_pin='0'*64)), dict(reference=None),
                        dict(reference=replace(self.owner, owner_revision=2)), dict(expected_owner_pin='0'*64)):
            with self.subTest(changes=changes):
                self.assertEqual(self.review(**changes).reason, 'MEMORY_GATEWAY_PREFLIGHT_HOLD')

    def test_old_receipt_cannot_follow_new_invocation(self):
        ctx, _ = self.f.build(key='another-invocation')
        j = JointContext(self.b.pin, ctx.envelope)
        self.assertEqual(self.review(context=j, ctx=ctx, expected_joint_pin=joint_context_digest(j, ctx.registry)).reason,
                         'MEMORY_GATEWAY_PREFLIGHT_HOLD')

    def test_unknown_budget(self):
        owner = replace(self.owner, budget=replace(self.owner.budget, unknown_cost=True))
        self.assertEqual(self.review(snapshot=owner, reference=owner, budget_reference=owner.budget,
                                     expected_owner_pin=owner_snapshot_digest(owner)).reason,
                         'MEMORY_GATEWAY_PREFLIGHT_HOLD')

    def test_run_lease_and_clock_drift(self):
        for ctx in (replace(self.ctx, current_run=replace(self.ctx.current_run, attempt=2)),
                    replace(self.ctx, current_lease=replace(self.ctx.current_lease, fence=2)),
                    replace(self.ctx, clock=replace(self.ctx.clock, now_tick=100))):
            self.assertEqual(self.review(ctx=ctx).reason, 'MEMORY_GATEWAY_MEMORY_HOLD')

    def test_unsigned_revocation_interleaved_with_real_preflight(self):
        real = bridge.inspect_provider_preflight
        def interleave(*args):
            result = real(*args)
            self.assertEqual(result.reason, 'D0_PROVIDER_PREFLIGHT_MATCH_ONLY')
            publish_snapshot(self.b.store.path, self.b.store.revoke(), self.b.pin)
            return result
        with patch.object(bridge, 'inspect_provider_preflight', side_effect=interleave):
            self.assertEqual(self.review().reason, 'MEMORY_GATEWAY_MEMORY_RECHECK_HOLD')

    def test_signed_pending_interleaved_with_real_preflight(self):
        real = bridge.inspect_provider_preflight
        def interleave(*args):
            result = real(*args)
            self.assertEqual(result.reason, 'D0_PROVIDER_PREFLIGHT_MATCH_ONLY')
            raw, graph = _encode(self.b.store.revoke())
            future = SnapshotPin(2, sha256(raw.encode('ascii')).hexdigest(), graph)
            pending = replace(self.w.record, sequence=2, previous_sha=witness_sha(self.w.record), pending=future)
            self.w.append(pending, self.w.latest.record_sha)
            return result
        with patch.object(bridge, 'inspect_provider_preflight', side_effect=interleave):
            self.assertEqual(self.review().reason, 'MEMORY_GATEWAY_MEMORY_RECHECK_HOLD')

    def test_wrong_witness_key_or_missing_reference_stops_before_gateway(self):
        with patch.object(bridge, 'inspect_provider_preflight', wraps=bridge.inspect_provider_preflight) as gateway:
            self.assertEqual(self.review(public_key=b'x'*32).reason, 'MEMORY_GATEWAY_MEMORY_HOLD')
            self.assertEqual(self.review(expected_witness=None).reason, 'MEMORY_GATEWAY_MEMORY_HOLD')
            gateway.assert_not_called()

    def test_reader_failure_holds_without_leaking_exception(self):
        with patch.object(bridge, 'inspect_provider_preflight', side_effect=RuntimeError('private fixture detail')):
            self.assertEqual(self.review().reason, 'MEMORY_GATEWAY_REVIEW_ERROR_HOLD')


if __name__ == '__main__':
    main(verbosity=2)
