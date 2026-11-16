"""Cross-boundary D0 checks; test orchestrates both readers, no runtime dispatch."""
from dataclasses import replace
from hashlib import sha256
import unittest

from app.core.agent_runtime.lifecycle import RunState
from app.engines.memory_engine.snapshot_store import publish_snapshot
from app.engines.model_gateway.provider_contract import ProviderKind, ProviderRequest
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.runtime_binding import InvocationEnvelope, invocation_digest, inspect_invocation
import test_memory_store_0196 as fixture


class RuntimeMemoryModelTests(unittest.TestCase):
    def setUp(self):
        self.store = fixture.SnapshotStoreTests()
        self.store.setUp()
        self.addCleanup(self.store.doCleanups)
        self.f = self.store.f
        self.pin = publish_snapshot(self.store.path, self.store.snapshot, None)
        s = self.f.scope
        a = AdapterPin(s, 'demo-model', 'v1', 'a'*64, ('demo-tool',), ())
        b = AdapterPin(s, 'demo-fallback', 'v1', 'b'*64, ('demo-tool',), ())
        self.registry = (a, b)
        request = ProviderRequest(s, ProviderKind.SAMPLE, sha256(self.f.raw).hexdigest(), ('demo-tool',), (), 64)
        self.envelope = InvocationEnvelope(self.f.run, self.f.lease, request, a, b, 'reserve-1', 'invoke-1', 100)
        self.digest = invocation_digest(self.envelope, self.registry)

    def review(self, run=None, lease=None, clock=None, pin=None, raw=None, envelope=None):
        f = self.f
        run = f.run if run is None else run
        lease = f.lease if lease is None else lease
        clock = f.clock if clock is None else clock
        pin = self.pin if pin is None else pin
        raw = f.raw if raw is None else raw
        envelope = self.envelope if envelope is None else envelope
        memory = self.store.inspect(pin, run=run, lease=lease, lease_reference=f.lease, clock=clock)
        model = inspect_invocation(envelope, self.registry, self.digest, run, lease, clock, raw)
        self.assertFalse(memory.retrieval_allowed)
        self.assertFalse(memory.release_allowed)
        self.assertEqual(model.decision, 'DENY')
        self.assertFalse(model.provider_call_allowed)
        self.assertFalse(model.spend_allowed)
        self.assertFalse(model.dispatch_allowed)
        self.assertIsNone(model.actual_cost_minor)
        return memory, model

    def test_same_run_lease_and_fixture_input_never_grant(self):
        memory, model = self.review()
        self.assertTrue(memory.structural_match)
        self.assertTrue(model.structural_match)
        self.assertFalse(hasattr(memory, 'raw'))

    def test_run_version_drift_denied_by_both(self):
        memory, model = self.review(run=replace(self.f.run, version=4))
        self.assertEqual(memory.reason, 'RUN_REFERENCE_HOLD')
        self.assertEqual(model.reason, 'MODEL_RUN_REFERENCE_HOLD')

    def test_terminal_run_denied_by_both(self):
        memory, model = self.review(run=replace(self.f.run, state=RunState.FAILED))
        self.assertEqual(memory.reason, 'RUN_REFERENCE_HOLD')
        self.assertEqual(model.reason, 'MODEL_RUN_REFERENCE_HOLD')

    def test_lease_expiry_denied_by_both(self):
        memory, model = self.review(clock=replace(self.f.clock, now_tick=100))
        self.assertEqual(memory.reason, 'MEMORY_LEASE_HOLD')
        self.assertEqual(model.reason, 'MODEL_LEASE_HOLD')

    def test_witness_epoch_drift_denied_by_both(self):
        memory, model = self.review(clock=replace(self.f.clock, witness_epoch=5))
        self.assertEqual(memory.reason, 'MEMORY_LEASE_HOLD')
        self.assertEqual(model.reason, 'MODEL_LEASE_HOLD')

    def test_revocation_exposes_independent_gate_gap(self):
        newer = publish_snapshot(self.store.path, self.store.revoke(), self.pin)
        memory, model = self.review(pin=newer)
        self.assertEqual(memory.reason, 'STALE_HOLD')
        self.assertTrue(model.structural_match)  # Model has no memory pin in its envelope.
        self.assertEqual(model.reason, 'D0_MODEL_INVOCATION_MATCH_ONLY')
        old, _ = self.review()
        self.assertEqual(old.reason, 'MEMORY_SNAPSHOT_CAS_HOLD')

    def test_input_digest_and_provider_gate_independent_of_memory(self):
        memory, model = self.review(raw=b'changed')
        self.assertTrue(memory.structural_match)
        self.assertEqual(model.reason, 'MODEL_INPUT_DIGEST_HOLD')
        request = replace(self.envelope.request, provider=ProviderKind.OPENAI)
        _, model = self.review(envelope=replace(self.envelope, request=request))
        self.assertEqual(model.reason, 'PROVIDER_EGRESS_HOLD')
