"""D0 joint context: genuine SQLite fixture, no external calls."""
from dataclasses import replace
from hashlib import sha256
from unittest import TestCase
from unittest.mock import patch
from contextlib import closing
import sqlite3

from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime import joint_context as joint
from app.engines.memory_engine.snapshot_store import publish_snapshot
from app.engines.model_gateway.provider_contract import ProviderKind
import test_runtime_memory_model_0207 as fixture


class JointContextTests(TestCase):
    def setUp(self):
        self.base = fixture.RuntimeMemoryModelTests()
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        b = self.base
        self.raw = b.f.raw[b.f.span.start:b.f.span.end]
        self.envelope = replace(b.envelope, request=replace(b.envelope.request,
                                input_digest=sha256(self.raw).hexdigest()))
        self.context = joint.JointContext(b.pin, self.envelope)
        self.pin = joint.joint_context_digest(self.context, b.registry)

    def review(self, **changes):
        b = self.base
        args = dict(context=self.context, registry=b.registry, expected_digest=self.pin,
                    path=b.store.path, current_run=b.f.run, current_lease=b.f.lease,
                    clock=b.f.clock, raw=self.raw)
        args.update(changes)
        r = joint.inspect_joint_context(**args)
        self.assertEqual(r.decision, 'DENY')
        for flag in ('retrieval_allowed', 'release_allowed', 'provider_call_allowed',
                     'dispatch_allowed', 'spend_allowed'):
            self.assertIs(getattr(r, flag), False)
        self.assertFalse(hasattr(r, 'raw'))
        return r

    def repin(self, context):
        return dict(context=context, expected_digest=joint.joint_context_digest(context, self.base.registry))

    def test_exact_span_matches_without_authority(self):
        self.assertTrue(self.review().structural_match)
        self.assertEqual(self.review().reason, 'D0_JOINT_CONTEXT_MATCH_ONLY')

    def test_full_source_not_authorized_span(self):
        b = self.base
        c = replace(self.context, invocation=b.envelope)
        self.assertEqual(self.review(raw=b.f.raw, **self.repin(c)).reason, 'JOINT_INPUT_SPAN_HOLD')

    def test_repin_arbitrary_input_does_not_bypass_span(self):
        raw = b'other'
        c = replace(self.context, invocation=replace(self.envelope,
                    request=replace(self.envelope.request, input_digest=sha256(raw).hexdigest())))
        self.assertEqual(self.review(raw=raw, **self.repin(c)).reason, 'JOINT_INPUT_SPAN_HOLD')

    def test_old_pin_after_revocation(self):
        b = self.base
        publish_snapshot(b.store.path, b.store.revoke(), b.pin)
        self.assertEqual(self.review().reason, 'MEMORY_SNAPSHOT_CAS_HOLD')

    def test_new_revoked_pin(self):
        b = self.base
        new = publish_snapshot(b.store.path, b.store.revoke(), b.pin)
        c = replace(self.context, memory_pin=new)
        self.assertEqual(self.review(**self.repin(c)).reason, 'STALE_HOLD')

    def test_revocation_between_reads(self):
        b = self.base
        real = joint.inspect_invocation
        def interleave(*args):
            result = real(*args)
            publish_snapshot(b.store.path, b.store.revoke(), b.pin)
            return result
        with patch.object(joint, 'inspect_invocation', side_effect=interleave):
            self.assertEqual(self.review().reason, 'MEMORY_SNAPSHOT_CAS_HOLD')

    def test_run_drift(self):
        self.assertEqual(self.review(current_run=replace(self.base.f.run, version=4)).reason, 'RUN_REFERENCE_HOLD')

    def test_terminal(self):
        self.assertEqual(self.review(current_run=replace(self.base.f.run, state=RunState.FAILED)).reason, 'RUN_REFERENCE_HOLD')

    def test_cross_principal(self):
        f = self.base.f
        run = replace(f.run, scope=replace(f.scope, principal_id='demo-other'))
        self.assertEqual(self.review(current_run=run).reason, 'RUN_REFERENCE_HOLD')

    def test_expired_lease(self):
        self.assertEqual(self.review(clock=replace(self.base.f.clock, now_tick=100)).reason, 'MEMORY_LEASE_HOLD')

    def test_fence_drift(self):
        self.assertEqual(self.review(current_lease=replace(self.base.f.lease, fence=2)).reason, 'MEMORY_LEASE_HOLD')

    def test_witness_drift(self):
        self.assertEqual(self.review(clock=replace(self.base.f.clock, witness_epoch=5)).reason, 'MEMORY_LEASE_HOLD')

    def test_acl_deny_after_new_pin(self):
        b = self.base
        a = b.store.snapshot.acl
        snap = replace(b.store.snapshot, acl=replace(a, acl_revision=8,
                       entries=(replace(a.entries[0], decision='DENY_READ'), a.entries[1])))
        c = replace(self.context, memory_pin=publish_snapshot(b.store.path, snap, b.pin))
        self.assertEqual(self.review(**self.repin(c)).reason, 'MEMORY_ACL_DENY')

    def test_changed_pin_without_joint_digest(self):
        c = replace(self.context, memory_pin=replace(self.context.memory_pin, generation=2))
        self.assertEqual(self.review(context=c).reason, 'JOINT_CONTEXT_DIGEST_HOLD')

    def test_changed_model_without_joint_digest(self):
        c = replace(self.context, invocation=replace(self.envelope, reservation_ref='reserve-2'))
        self.assertEqual(self.review(context=c).reason, 'JOINT_CONTEXT_DIGEST_HOLD')

    def test_real_provider_cannot_be_pinned(self):
        c = replace(self.context, invocation=replace(self.envelope,
                    request=replace(self.envelope.request, provider=ProviderKind.OPENAI)))
        with self.assertRaisesRegex(ValueError, 'PROVIDER_EGRESS_HOLD'):
            joint.joint_context_digest(c, self.base.registry)
        self.assertEqual(self.review(context=c).reason, 'JOINT_CONTEXT_SHAPE_HOLD')

    def test_effect_cannot_be_pinned(self):
        c = replace(self.context, invocation=replace(self.envelope,
                    request=replace(self.envelope.request, effects=('send',))))
        with self.assertRaisesRegex(ValueError, 'PROVIDER_EFFECT_HOLD'):
            joint.joint_context_digest(c, self.base.registry)
        self.assertFalse(self.review(context=c).structural_match)

    def test_missing_store_and_tampered_raw(self):
        b = self.base
        path = b.store.path.with_name('absent.d0.sqlite')
        self.assertEqual(self.review(path=path).reason, 'MEMORY_SNAPSHOT_READ_HOLD')
        self.assertFalse(path.exists())
        with closing(sqlite3.connect(b.store.path)) as db, db:
            db.execute('UPDATE snapshots SET raw=?', (b'bad',))
        self.assertEqual(self.review().reason, 'MEMORY_SNAPSHOT_READ_HOLD')

    def test_read_only_preserves_store(self):
        path = self.base.store.path
        before = path.read_bytes()
        self.assertTrue(self.review().structural_match)
        self.assertEqual(path.read_bytes(), before)

    def test_policy_drift(self):
        self.assertEqual(self.review(clock=replace(self.base.f.clock, policy_epoch=3)).reason, 'MEMORY_LEASE_HOLD')

    def test_registry_order_is_bound(self):
        self.assertEqual(self.review(registry=tuple(reversed(self.base.registry))).reason, 'JOINT_CONTEXT_DIGEST_HOLD')

    def test_graph_pin_tampering_cannot_be_repinned(self):
        c = replace(self.context, memory_pin=replace(self.context.memory_pin, graph_digest='d'*64))
        self.assertEqual(self.review(**self.repin(c)).reason, 'MEMORY_SNAPSHOT_CAS_HOLD')

    def test_model_input_hash_must_match_even_with_exact_span(self):
        c = replace(self.context, invocation=replace(self.envelope,
                    request=replace(self.envelope.request, input_digest='d'*64)))
        self.assertEqual(self.review(**self.repin(c)).reason, 'MODEL_INPUT_DIGEST_HOLD')

    def test_invalid_input_and_pin_shape(self):
        for raw in (bytearray(self.raw), None, b'x'*(1024*1024+1)):
            self.assertEqual(self.review(raw=raw).reason, 'JOINT_CONTEXT_SHAPE_HOLD')
        c = replace(self.context, memory_pin=replace(self.context.memory_pin, generation=True))
        self.assertEqual(self.review(context=c).reason, 'JOINT_CONTEXT_SHAPE_HOLD')

    def test_failed_revocation_transaction_preserves_pin(self):
        b = self.base
        with closing(sqlite3.connect(b.store.path)) as db, db:
            db.execute("CREATE TRIGGER refuse BEFORE INSERT ON snapshots BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            publish_snapshot(b.store.path, b.store.revoke(), b.pin)
        self.assertTrue(self.review().structural_match)

    def test_restore_external_witness_still_required(self):
        b = self.base
        copy = b.store.path.with_name('restore.d0.sqlite')
        copy.write_bytes(b.store.path.read_bytes())
        publish_snapshot(b.store.path, b.store.revoke(), b.pin)
        self.assertEqual(self.review().reason, 'MEMORY_SNAPSHOT_CAS_HOLD')
        # A copied pre-revocation snapshot can match an old caller pin. No grant.
        self.assertTrue(self.review(path=copy).structural_match)
