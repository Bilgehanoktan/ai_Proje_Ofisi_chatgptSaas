"""D0 oracle candidates. NOT_RUN; no real provider, DB or authority."""
import unittest
from dataclasses import replace
from hashlib import sha256
from app.core.runtime_preview import Scope
from app.core.skill_review import SkillManifestSample
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.fallback import inspect_fallback
from app.engines.model_gateway.gateway import DisabledModelGateway
from app.engines.skill_engine.resolver import SourcePin, inspect_capabilities
from app.engines.knowledge_engine.provenance import SourceVersion, ClaimSpan, inspect_span
from app.engines.memory_engine.retrieval import Node, TombstoneView, inspect_retrieval


class EngineReviewTests(unittest.TestCase):
    def setUp(self):
        self.s = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,
                       'research','demo-run','demo-agent','demo-principal')
        self.a = AdapterPin(self.s,'a','v1','a'*64,('read','write'),('READ',))
        self.b = replace(self.a, adapter_id='b', capabilities=('read',))
        self.m = SkillManifestSample(self.s,'skill','v1','a'*64,'b'*64,'c'*64,('read',))
        self.p = SourcePin('source','v1','a'*64,'license','custody')
        self.n = (Node(self.s,'source','v1','a'*64,()),Node(self.s,'cache','v1','b'*64,('source',)))
        self.v = TombstoneView(self.s,1,2,('source',),True)

    def test_matching_fallback_still_denied(self):
        r = inspect_fallback(self.a,self.b,(self.a,self.b),('read',),('READ',))
        self.assertTrue(r.structural_match)
        self.assertFalse(r.provider_call_allowed)

    def test_scope_mismatch(self):
        b = replace(self.b,scope=replace(self.s,principal_id='demo-other'))
        self.assertEqual(inspect_fallback(self.a,b,(self.a,b),('read',),('READ',)).reason,'FALLBACK_SCOPE_MISMATCH')

    def test_effect_ceiling(self):
        b = replace(self.b,effect_ceiling=('READ','WRITE'))
        self.assertEqual(inspect_fallback(self.a,b,(self.a,b),('read',),('READ',)).reason,'FALLBACK_EFFECT_CEILING_MISMATCH')

    def test_capability_expansion(self):
        b = replace(self.b,capabilities=('read','admin'))
        self.assertEqual(inspect_fallback(self.a,b,(self.a,b),('read',),('READ',)).reason,'FALLBACK_CAPABILITY_EXPANSION')

    def test_disabled_port(self):
        self.assertFalse(DisabledModelGateway().invoke(None).provider_call_allowed)

    def test_skill_intersection_not_grant(self):
        r = inspect_capabilities(self.m,self.m,self.s,self.p,self.p,self.a,(self.a,),('read',),('read',))
        self.assertEqual(r.diagnostic_overlap,('read',))
        self.assertEqual(r.effective_tools,())
        self.assertFalse(r.enabled)

    def test_skill_pin_mismatch(self):
        p = replace(self.p,raw_digest='b'*64)
        self.assertEqual(inspect_capabilities(self.m,self.m,self.s,p,p,self.a,(self.a,),('read',),('read',)).reason,'SKILL_SOURCE_PIN_HOLD')

    def test_byte_span(self):
        raw = 'aç'.encode('utf-8')
        s = SourceVersion(self.s,'source','v1',sha256(raw).hexdigest())
        span = ClaimSpan(s,1,3,sha256(raw[1:3]).hexdigest())
        self.assertEqual(inspect_span(span,s,raw),'D0_SPAN_MATCH_ONLY')
        self.assertEqual(inspect_span(replace(span,end=4),s,raw),'SPAN_BOUNDS_HOLD')

    def test_tombstoned_cache(self):
        r = inspect_retrieval(self.s,self.n,'cache',self.v,self.v)
        self.assertEqual(r.reason,'STALE_HOLD')
        self.assertEqual(r.stale_nodes,('cache','source'))
        self.assertFalse(r.retrieval_allowed)

    def test_stale_view(self):
        self.assertEqual(inspect_retrieval(self.s,self.n,'cache',replace(self.v,epoch=0),self.v).reason,'TOMBSTONE_VIEW_UNKNOWN_HOLD')

    def test_cycle(self):
        nodes = (replace(self.n[0],parents=('cache',)),self.n[1])
        self.assertEqual(inspect_retrieval(self.s,nodes,'cache',self.v,self.v).reason,'LINEAGE_CYCLE_HOLD')

    def test_orphan(self):
        self.assertEqual(inspect_retrieval(self.s,(self.n[1],),'cache',self.v,self.v).reason,'LINEAGE_ORPHAN_OR_DUPLICATE_HOLD')
