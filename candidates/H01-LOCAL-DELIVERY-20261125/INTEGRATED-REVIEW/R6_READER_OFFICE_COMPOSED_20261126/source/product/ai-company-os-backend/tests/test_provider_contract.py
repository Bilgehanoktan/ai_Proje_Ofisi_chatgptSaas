from dataclasses import replace
import unittest
from app.core.agent_runtime.lifecycle import Scope
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderKind, ProviderRequest, inspect_provider_request
from app.engines.model_gateway.sample_adapter import sample_model
from app.engines.model_gateway.gateway import DisabledModelGateway


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.scope = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,'research','demo-run','demo-agent','demo-principal')
        self.a = AdapterPin(self.scope,'demo-model','v1','a'*64,('demo-tool',),())
        self.b = AdapterPin(self.scope,'demo-fallback','v1','b'*64,('demo-tool',),())
        self.q = ProviderRequest(self.scope,ProviderKind.SAMPLE,'c'*64,('demo-tool',),(),64)

    def review(self,q=None,a=None,b=None,registry=None):
        a=self.a if a is None else a; b=self.b if b is None else b
        return inspect_provider_request(self.q if q is None else q,a,b,(a,b) if registry is None else registry)

    def test_match_never_authorizes(self):
        r=self.review(); self.assertTrue(r.structural_match)
        self.assertEqual(r.decision,'DENY')
        for k in ('provider_call_allowed','spend_allowed','dispatch_allowed'): self.assertIs(getattr(r,k),False)
        for k in ('actual_tokens','actual_cost_minor','selected_model'): self.assertIsNone(getattr(r,k))

    def test_all_real_provider_kinds_denied(self):
        for p in ProviderKind:
            if p is not ProviderKind.SAMPLE:
                r=self.review(replace(self.q,provider=p)); self.assertFalse(r.structural_match); self.assertEqual(r.reason,'PROVIDER_EGRESS_HOLD')

    def test_bad_request(self):
        for q in (replace(self.q,provider='SAMPLE'),replace(self.q,input_digest='x'),replace(self.q,max_output_tokens=True),replace(self.q,max_output_tokens=32769),replace(self.q,requested=('demo-tool','demo-tool'))):
            self.assertEqual(self.review(q).reason,'PROVIDER_REQUEST_INVALID')

    def test_scope_mismatch(self):
        self.assertEqual(self.review(replace(self.q,scope=replace(self.scope,task_id='other'))).reason,'PROVIDER_SCOPE_MISMATCH')

    def test_registry_exact(self):
        self.assertEqual(self.review(registry=(self.a,)).reason,'ADAPTER_PIN_INVALID')
        self.assertEqual(self.review(registry=(self.a,self.b,self.b)).reason,'ADAPTER_PIN_INVALID')
        self.assertEqual(self.review(a=replace(self.a,enabled=True)).reason,'ADAPTER_PIN_INVALID')

    def test_effect_hold(self):
        self.assertEqual(self.review(replace(self.q,effects=('send',))).reason,'PROVIDER_EFFECT_HOLD')
        self.assertEqual(self.review(a=replace(self.a,effect_ceiling=('send',)),b=replace(self.b,effect_ceiling=('send',))).reason,'PROVIDER_EFFECT_HOLD')

    def test_no_capability_widening(self):
        self.assertEqual(self.review(b=replace(self.b,capabilities=('demo-tool','other'))).reason,'FALLBACK_CAPABILITY_EXPANSION')
        self.assertEqual(self.review(replace(self.q,requested=('other',))).reason,'CAPABILITY_HOLD')

    def test_fallback_alias(self):
        self.assertEqual(self.review(b=self.a,registry=(self.a,)).reason,'PROVIDER_FALLBACK_ALIAS_HOLD')

    def test_sample_ids(self):
        self.assertEqual(self.review(a=replace(self.a,adapter_id='other')).reason,'SAMPLE_ADAPTER_ONLY')

    def test_existing_sample_adapter(self):
        r=sample_model(self.a,self.b,(self.a,self.b)); self.assertEqual(r.reason,'FIXED_SAMPLE_ONLY'); self.assertIsNotNone(r.output)
        self.assertFalse(r.provider_called)
        a=replace(self.a,effect_ceiling=('send',)); b=replace(self.b,effect_ceiling=('send',))
        self.assertIsNone(sample_model(a,b,(a,b)).output)

    def test_disabled_gateway_unchanged(self):
        r=DisabledModelGateway().invoke(self.q); self.assertEqual(r.reason,'MODEL_EGRESS_DISABLED'); self.assertFalse(r.provider_call_allowed)
