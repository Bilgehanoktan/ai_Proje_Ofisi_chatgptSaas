"""R10 D0 exact byte-provenance boundary; no authority or retrieval."""
import unittest
from dataclasses import replace
from hashlib import sha256
from app.core.runtime_preview import Scope
from app.engines.knowledge_engine.provenance import SourceVersion, ClaimSpan, inspect_span

class EqualSource(SourceVersion):
    def __eq__(self, other): return True
    def __ne__(self, other): return False

class EqualText(str):
    def __eq__(self, other): return True
    def __ne__(self, other): return False

class EqualScope(Scope):
    def __eq__(self, other): return True
    def __ne__(self, other): return False

class DerivedSpan(ClaimSpan):
    pass

class ExactValueTests(unittest.TestCase):
    def setUp(self):
        self.raw = 'aç'.encode('utf-8')
        self.scope = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,'research','demo-run','demo-agent','demo-principal')
        self.source = SourceVersion(self.scope,'source','v1',sha256(self.raw).hexdigest())
        self.span = ClaimSpan(self.source,1,3,sha256(self.raw[1:3]).hexdigest())
    def test_exact_byte_span(self):
        self.assertEqual(inspect_span(self.span,self.source,self.raw),'D0_SPAN_MATCH_ONLY')
    def test_different_plain_source(self):
        self.assertEqual(inspect_span(replace(self.span,source=replace(self.source,source_id='other')),self.source,self.raw),'SOURCE_PIN_HOLD')
    def test_source_subclass_cannot_match_other_source(self):
        forged=EqualSource(self.scope,'other','v1',self.source.raw_digest)
        self.assertEqual(inspect_span(replace(self.span,source=forged),self.source,self.raw),'SOURCE_PIN_HOLD')
    def test_digest_subclass_cannot_match_wrong_bytes(self):
        forged=replace(self.source,raw_digest=EqualText('0'*64))
        self.assertEqual(inspect_span(replace(self.span,source=forged),forged,self.raw),'SOURCE_PIN_HOLD')
    def test_scope_subclass_cannot_match_other_run(self):
        forged=EqualScope(**{**self.scope.__dict__,'run_id':'demo-other'})
        self.assertEqual(inspect_span(replace(self.span,source=replace(self.source,scope=forged)),self.source,self.raw),'SOURCE_PIN_HOLD')
    def test_scope_field_subclass_cannot_match_other_run(self):
        forged=replace(self.scope,run_id=EqualText('demo-other'))
        self.assertEqual(inspect_span(replace(self.span,source=replace(self.source,scope=forged)),self.source,self.raw),'SOURCE_PIN_HOLD')
    def test_span_subclass_is_not_value_record(self):
        forged=DerivedSpan(self.source,1,3,self.span.span_digest)
        self.assertEqual(inspect_span(forged,self.source,self.raw),'SOURCE_PIN_HOLD')
    def test_span_digest_subclass_cannot_match_wrong_bytes(self):
        self.assertEqual(inspect_span(replace(self.span,span_digest=EqualText('0'*64)),self.source,self.raw),'SPAN_DIGEST_HOLD')
    def test_bounds_and_wrong_plain_digest(self):
        self.assertEqual(inspect_span(replace(self.span,end=4),self.source,self.raw),'SPAN_BOUNDS_HOLD')
        self.assertEqual(inspect_span(replace(self.span,span_digest='0'*64),self.source,self.raw),'SPAN_DIGEST_HOLD')

if __name__ == '__main__': unittest.main()
