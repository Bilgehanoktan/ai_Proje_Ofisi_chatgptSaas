"""Existing archived PR55-R2 resolver + exact shared registry, no tool execution."""
from dataclasses import replace
import unittest
from app.core.runtime_preview import Scope
from app.engines.model_gateway.registry import AdapterPin
from app.engines.skill_engine.manifest_review import SkillManifestSample
from app.engines.skill_engine.resolver import SourcePin, inspect_capabilities
from test_adapter_pin_boundary import AliasText, AliasRegistry, UnhashableText

class AdapterSkillIntegration(unittest.TestCase):
    def setUp(self):
        self.s=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,'research','demo-run','demo-agent','demo-principal')
        self.a=AdapterPin(self.s,'demo-model','v1','a'*64,('demo-tool',),())
        self.m=SkillManifestSample(self.s,'demo-skill','v1','b'*64,'c'*64,'d'*64,('demo-tool',))
        self.src=SourcePin('demo-source','v1','b'*64,'license-ref','custody-ref')
    def check(self,adapter=None,registry=None,requested=('demo-tool',)):
        return inspect_capabilities(self.m,self.m,self.s,self.src,self.src,
            self.a if adapter is None else adapter,(self.a,) if registry is None else registry,requested,('demo-tool',))
    def assert_quarantined(self,r):
        self.assertEqual(r.status,'QUARANTINED'); self.assertFalse(r.enabled); self.assertEqual(r.effective_tools,())
    def test_valid_r2_overlap_is_diagnostic_only(self):
        r=self.check(); self.assertEqual(r.reason,'INDEPENDENT_RECEIPTS_ABSENT'); self.assertEqual(r.diagnostic_overlap,('demo-tool',)); self.assert_quarantined(r)
    def test_forged_adapter_reference_stops_before_overlap(self):
        r=self.check(adapter=replace(self.a,adapter_digest=AliasText('e'*64)))
        self.assertEqual(r.reason,'ADAPTER_SCOPE_HOLD'); self.assertEqual(r.diagnostic_overlap,()); self.assert_quarantined(r)
    def test_forged_membership_stops_before_overlap(self):
        r=self.check(adapter=replace(self.a,adapter_digest='e'*64),registry=AliasRegistry((self.a,)))
        self.assertEqual(r.reason,'ADAPTER_SCOPE_HOLD'); self.assertEqual(r.diagnostic_overlap,()); self.assert_quarantined(r)
    def test_invalid_tool_record_returns_hold_not_error(self):
        r=self.check(requested=(UnhashableText('demo-tool'),)); self.assertEqual(r.reason,'CAPABILITY_REQUEST_INVALID'); self.assert_quarantined(r)

if __name__=='__main__': unittest.main()
