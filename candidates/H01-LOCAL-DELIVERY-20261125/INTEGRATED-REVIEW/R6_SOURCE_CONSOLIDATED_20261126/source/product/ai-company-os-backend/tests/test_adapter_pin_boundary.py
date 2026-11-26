"""MI07/09: exact diagnostic pins; never grant or execute a provider."""
from dataclasses import replace
import unittest
from app.core.runtime_preview import Scope
from app.engines.model_gateway.registry import AdapterPin, valid_set, valid_pin, exact_pin
from app.engines.model_gateway.fallback import inspect_fallback
from app.engines.model_gateway.provider_contract import ProviderKind, ProviderRequest, inspect_provider_request

class AliasText(str):
    def __eq__(self, other):
        return True
    __hash__ = str.__hash__

class UnhashableText(str):
    __hash__ = None

class AliasRegistry(tuple):
    def __contains__(self, item):
        return True

class AliasPin(AdapterPin):
    def __eq__(self, other):
        return True
    __hash__ = AdapterPin.__hash__

class DerivedScope(Scope):
    pass

class AdapterBoundary(unittest.TestCase):
    def setUp(self):
        self.s=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,'research','demo-run','demo-agent','demo-principal')
        self.a=AdapterPin(self.s,'demo-model','v1','a'*64,('demo-tool',),())
        self.b=AdapterPin(self.s,'demo-fallback','v1','b'*64,('demo-tool',),())
        self.q=ProviderRequest(self.s,ProviderKind.SAMPLE,'c'*64,('demo-tool',),(),64)
    def test_exact_plain_values(self):
        self.assertTrue(exact_pin(replace(self.a),(self.a,self.b)))
        self.assertFalse(exact_pin(replace(self.a,adapter_digest='b'*64),(self.a,self.b)))
        self.assertFalse(exact_pin(self.a,(self.a,self.b,self.a)))
        self.assertFalse(valid_pin(replace(self.a,enabled=True)))
    def test_plain_set_contract(self):
        self.assertTrue(valid_set(())); self.assertTrue(valid_set(('a','b')))
        self.assertFalse(valid_set(('a','a'))); self.assertFalse(valid_set(['a']))
        self.assertFalse(valid_set(('a',)*129)); self.assertFalse(valid_set(('bad space',)))
    def test_registry_membership_override_rejected(self):
        forged=replace(self.a,adapter_digest='b'*64)
        self.assertFalse(exact_pin(forged,AliasRegistry((self.a,self.b))))
    def test_record_subclass_rejected(self):
        forged=AliasPin(self.s,'demo-model','v1','b'*64,('demo-tool',),())
        self.assertFalse(valid_pin(forged)); self.assertFalse(exact_pin(forged,(self.a,self.b)))
        self.assertFalse(exact_pin(self.a,(forged,self.b)))
    def test_digest_equality_override_rejected(self):
        forged=replace(self.a,adapter_digest=AliasText('b'*64))
        self.assertFalse(exact_pin(forged,(self.a,self.b)))
    def test_scope_fields_rejected(self):
        self.assertFalse(valid_pin(replace(self.a,scope=replace(self.s,tenant_id=AliasText('different-tenant')))))
        sub=DerivedScope(*vars(self.s).values())
        self.assertFalse(valid_pin(replace(self.a,scope=sub)))
    def test_string_subclasses_rejected_without_error(self):
        self.assertFalse(valid_set((AliasText('demo-tool'),)))
        self.assertFalse(valid_set((UnhashableText('demo-tool'),)))
    def test_tuple_subclasses_rejected(self):
        self.assertFalse(valid_set(AliasRegistry(('demo-tool',))))
    def test_fallback_rejects_forged_reference(self):
        forged=replace(self.a,adapter_digest=AliasText('b'*64))
        r=inspect_fallback(forged,self.b,(self.a,self.b),('demo-tool',),())
        self.assertEqual(r.reason,'ADAPTER_PIN_INVALID'); self.assertFalse(r.structural_match)
        self.assertEqual(r.decision,'DENY'); self.assertFalse(r.provider_call_allowed)
    def test_provider_rejects_forged_reference(self):
        forged=replace(self.a,adapter_digest=AliasText('b'*64))
        r=inspect_provider_request(self.q,forged,self.b,(self.a,self.b))
        self.assertEqual(r.reason,'ADAPTER_PIN_INVALID'); self.assertFalse(r.structural_match)
        self.assertEqual(r.decision,'DENY'); self.assertFalse(r.provider_call_allowed)
        self.assertFalse(r.spend_allowed); self.assertFalse(r.dispatch_allowed)
    def test_provider_valid_synthetic_only(self):
        r=inspect_provider_request(self.q,self.a,self.b,(self.a,self.b))
        self.assertTrue(r.structural_match); self.assertEqual(r.decision,'DENY')
        self.assertFalse(r.provider_call_allowed); self.assertFalse(r.spend_allowed)
        self.assertFalse(r.dispatch_allowed); self.assertIsNone(r.selected_model)
        for kind in ProviderKind:
            if kind is not ProviderKind.SAMPLE:
                self.assertEqual(inspect_provider_request(replace(self.q,provider=kind),self.a,self.b,(self.a,self.b)).reason,'PROVIDER_EGRESS_HOLD')

if __name__=='__main__': unittest.main()
