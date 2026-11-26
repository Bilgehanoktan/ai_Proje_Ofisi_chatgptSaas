from dataclasses import replace
from hashlib import sha256
import unittest
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, LeaseObservation, ClockSample
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderRequest, ProviderKind
from app.engines.model_gateway.runtime_binding import InvocationEnvelope, invocation_digest, inspect_invocation


class ModelInvocationTests(unittest.TestCase):
    def setUp(self):
        scope = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,
                      'research','demo-run','demo-agent','demo-principal')
        self.run = RunObservation(scope, RunState.RUNNING, 3, 1)
        self.lease = LeaseObservation(scope, 'lease', 'grant', 1, 1, 1, 2, 4, 100, 80)
        self.clock = ClockSample(85, 2, 4, 10)
        self.raw = b'D0 fixture only'
        self.a = AdapterPin(scope,'demo-model','v1','a'*64,('demo-tool',),())
        self.b = AdapterPin(scope,'demo-fallback','v1','b'*64,('demo-tool',),())
        self.registry = (self.a, self.b)
        q = ProviderRequest(scope, ProviderKind.SAMPLE, sha256(self.raw).hexdigest(), ('demo-tool',), (), 64)
        self.e = InvocationEnvelope(self.run, self.lease, q, self.a, self.b, 'reserve-1', 'invoke-1', 100)
        self.pin = invocation_digest(self.e, self.registry)

    def review(self, **changes):
        kwargs = dict(envelope=self.e, registry=self.registry, expected_digest=self.pin,
                      current_run=self.run, current_lease=self.lease, clock=self.clock, raw=self.raw)
        kwargs.update(changes)
        r = inspect_invocation(**kwargs)
        self.assertEqual(r.decision, 'DENY')
        for name in ('provider_call_allowed', 'spend_allowed', 'dispatch_allowed'):
            self.assertIs(getattr(r, name), False)
        for name in ('actual_tokens', 'actual_cost_minor', 'selected_model'):
            self.assertIsNone(getattr(r, name))
        return r

    def test_matching_request_still_denied(self):
        self.assertEqual(self.review().reason, 'D0_MODEL_INVOCATION_MATCH_ONLY')
        self.assertTrue(self.review().structural_match)

    def test_run_drift(self):
        for change in (dict(version=4), dict(attempt=True), dict(state=RunState.SUCCEEDED)):
            self.assertEqual(self.review(current_run=replace(self.run, **change)).reason, 'MODEL_RUN_REFERENCE_HOLD')

    def test_lease_expiry_and_fence(self):
        self.assertEqual(self.review(clock=replace(self.clock, now_tick=100)).reason, 'MODEL_LEASE_HOLD')
        self.assertEqual(self.review(current_lease=replace(self.lease, fence=2)).reason, 'MODEL_LEASE_HOLD')

    def test_input_hash_and_size(self):
        for raw in (b'changed', bytearray(self.raw), b'x'*(1024*1024+1)):
            self.assertEqual(self.review(raw=raw).reason, 'MODEL_INPUT_DIGEST_HOLD')

    def test_reservation_and_idempotency_pins(self):
        for changes in (dict(reservation_ref='reserve-2'), dict(idempotency_key='invoke-2'),
                        dict(sample_cost_ceiling_minor=101)):
            self.assertEqual(self.review(envelope=replace(self.e, **changes)).reason, 'MODEL_INVOCATION_DIGEST_HOLD')

    def test_output_budget_pin(self):
        e = replace(self.e, request=replace(self.e.request, max_output_tokens=65))
        self.assertEqual(self.review(envelope=e).reason, 'MODEL_INVOCATION_DIGEST_HOLD')

    def test_adapter_and_registry_pin(self):
        a = replace(self.a, adapter_digest='d'*64)
        e = replace(self.e, primary=a)
        self.assertEqual(self.review(envelope=e, registry=(a,self.b)).reason, 'MODEL_INVOCATION_DIGEST_HOLD')
        self.assertEqual(self.review(registry=(self.b,self.a)).reason, 'MODEL_INVOCATION_DIGEST_HOLD')

    def test_real_providers_never_call(self):
        for provider in ProviderKind:
            if provider is ProviderKind.SAMPLE: continue
            e = replace(self.e, request=replace(self.e.request, provider=provider))
            self.assertEqual(self.review(envelope=e).reason, 'PROVIDER_EGRESS_HOLD')
            with self.assertRaisesRegex(ValueError, 'PROVIDER_EGRESS_HOLD'): invocation_digest(e,self.registry)

    def test_effects_and_invalid_ceiling(self):
        e = replace(self.e, request=replace(self.e.request, effects=('send',)))
        self.assertEqual(self.review(envelope=e).reason, 'PROVIDER_EFFECT_HOLD')
        for cap in (True, 0, -1):
            self.assertEqual(self.review(envelope=replace(self.e, sample_cost_ceiling_minor=cap)).reason,
                             'MODEL_INVOCATION_SHAPE_HOLD')


if __name__ == '__main__': unittest.main()
