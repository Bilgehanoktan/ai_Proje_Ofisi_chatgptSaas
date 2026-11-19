"""MEM-05E: actual original SQLite/Ed25519 fixtures; no protected owner grant."""
from dataclasses import replace
from hashlib import sha256
from unittest import TestCase, main
from unittest.mock import patch

from app.core.agent_runtime import memory_checkpoint as c, memory_gateway_review as bridge
from app.core.agent_runtime.joint_context import JointContext, joint_context_digest
from app.engines.memory_engine import snapshot_store as s
from app.engines.model_gateway.durable_receipt_adapter import owner_snapshot_digest
import test_memory_gateway_05c_r1 as fixture


class RecoveredMemoryGatewayTests(TestCase):
    def setUp(self):
        self.g = fixture.MemoryGatewayTests()
        self.g.setUp()
        self.addCleanup(self.g.doCleanups)
        self.w, self.b, self.ctx, self.owner = self.g.w, self.g.b, self.g.ctx, self.g.owner
        self.j = JointContext(self.b.pin, self.ctx.envelope)
        self.body = c.prepare_checkpoint(self.b.store.path, self.w.reader, self.w.latest, self.w.pub)
        self.signature = self.w.key.sign(self.body)
        self.pin = sha256(self.body).hexdigest()

    def review(self, **changes):
        args = dict(context=self.j, expected_joint_pin=joint_context_digest(self.j, self.ctx.registry),
                    ctx=self.ctx, memory_path=self.b.store.path, reader=self.w.reader,
                    expected_witness=self.w.latest, public_key=self.w.pub, snapshot=self.owner,
                    reference=self.owner, budget_reference=self.owner.budget,
                    expected_owner_pin=owner_snapshot_digest(self.owner), checkpoint_body=self.body,
                    checkpoint_signature=self.signature, checkpoint_sha=self.pin)
        args.update(changes)
        r = bridge.inspect_recovered_memory_gateway(**args)
        self.assertEqual(r.decision, 'HOLD')
        for name in ('retrieval_allowed', 'release_allowed', 'provider_call_allowed', 'dispatch_allowed',
                     'spend_allowed', 'settlement_allowed', 'transition_allowed', 'retry_allowed',
                     'independent_verified', 'atomicity_verified'):
            self.assertIs(getattr(r, name), False)
        return r

    def stage(self, publish=False):
        snapshot = self.b.store.revoke()
        metadata, graph = s._encode(snapshot)
        target = s.SnapshotPin(2, sha256(metadata.encode('ascii')).hexdigest(), graph)
        pending = replace(self.w.record, sequence=2, previous_sha=self.w.latest.record_sha, pending=target)
        latest = self.w.append(pending, self.w.latest.record_sha)
        if publish:
            self.assertEqual(s.publish_snapshot(self.b.store.path, snapshot, self.b.pin), target)
        return latest

    def test_clean_exact_match_read_only(self):
        before = self.b.store.path.read_bytes(), self.w.path.read_bytes()
        r = self.review()
        self.assertTrue(r.structural_match)
        self.assertEqual(r.reason, 'D0_RECOVERED_MEMORY_GATEWAY_MATCH_ONLY')
        self.assertEqual(before, (self.b.store.path.read_bytes(), self.w.path.read_bytes()))

    def test_bad_checkpoint_stops_before_gateway(self):
        with patch.object(bridge, 'inspect_memory_gateway', wraps=bridge.inspect_memory_gateway) as g:
            for changes in (dict(checkpoint_signature=b'x'*64), dict(checkpoint_sha='0'*64),
                            dict(public_key=b'x'*32)):
                self.assertEqual(self.review(**changes).reason, 'MEMORY_GATEWAY_RECOVERY_HOLD')
            g.assert_not_called()

    def test_pending_base_stops_before_gateway(self):
        latest = self.stage()
        with patch.object(bridge, 'inspect_memory_gateway', wraps=bridge.inspect_memory_gateway) as g:
            self.assertEqual(self.review(expected_witness=latest).reason, 'MEMORY_GATEWAY_RECOVERY_HOLD')
            g.assert_not_called()

    def test_pending_target_stops_before_gateway(self):
        latest = self.stage(publish=True)
        before = self.b.store.path.read_bytes(), self.w.path.read_bytes()
        with patch.object(bridge, 'inspect_memory_gateway', wraps=bridge.inspect_memory_gateway) as g:
            self.assertEqual(self.review(expected_witness=latest).reason, 'MEMORY_GATEWAY_RECOVERY_HOLD')
            g.assert_not_called()
        self.assertEqual(before, (self.b.store.path.read_bytes(), self.w.path.read_bytes()))

    def test_pending_after_gateway_rejected_by_recovery_recheck(self):
        real = bridge.inspect_memory_gateway
        def interleave(*args):
            result = real(*args)
            self.assertTrue(result.structural_match)
            self.stage()
            return result
        with patch.object(bridge, 'inspect_memory_gateway', side_effect=interleave):
            self.assertEqual(self.review().reason, 'MEMORY_GATEWAY_RECOVERY_RECHECK_HOLD')

    def test_unknown_budget_never_matches(self):
        owner = replace(self.owner, budget=replace(self.owner.budget, unknown_cost=True))
        r = self.review(snapshot=owner, reference=owner, budget_reference=owner.budget,
                        expected_owner_pin=owner_snapshot_digest(owner))
        self.assertFalse(r.structural_match)
        self.assertEqual(r.reason, 'MEMORY_GATEWAY_RECOVERY_PREFLIGHT_HOLD')

    def test_runtime_lease_fence_drift_rejected(self):
        ctx = replace(self.ctx, current_lease=replace(self.ctx.current_lease, fence=2))
        self.assertEqual(self.review(ctx=ctx).reason, 'MEMORY_GATEWAY_RECOVERY_HOLD')

    def test_joint_mismatch_stops_before_recovery(self):
        ctx, owner = self.g.build(key='another-invocation')
        with patch.object(bridge, 'inspect_memory_recovery', wraps=bridge.inspect_memory_recovery) as r:
            self.assertEqual(self.review(ctx=ctx).reason, 'MEMORY_GATEWAY_RECOVERY_INPUT_HOLD')
            r.assert_not_called()

    def test_invalid_joint_pin_rejected(self):
        self.assertEqual(self.review(expected_joint_pin='0'*64).reason,
                         'MEMORY_GATEWAY_RECOVERY_PREFLIGHT_HOLD')

    def test_reader_error_does_not_leak_exception(self):
        with patch.object(bridge, 'inspect_memory_recovery', side_effect=RuntimeError('private detail')):
            self.assertEqual(self.review().reason, 'MEMORY_GATEWAY_RECOVERY_ERROR_HOLD')


if __name__ == '__main__':
    main(verbosity=2)
