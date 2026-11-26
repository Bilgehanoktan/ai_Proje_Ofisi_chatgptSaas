"""MI-09 review candidate: D0 exact source-reference boundary only."""
from dataclasses import replace
from unittest import TestCase
from app.core.runtime_preview import Scope
from app.core.skill_review import SkillManifestSample
from app.engines.model_gateway.registry import AdapterPin
from app.engines.skill_engine.resolver import SourcePin, inspect_capabilities


class EqualPin(SourcePin):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


class EqualText(str):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


class RejectComparisonPin(SourcePin):
    def __eq__(self, other):
        raise AssertionError('Unexpected reference comparison')

    def __ne__(self, other):
        raise AssertionError('Unexpected reference comparison')


class SkillExactSourceTypeTests(TestCase):
    def setUp(self):
        self.s = Scope('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY',
                       'sha256:'+'a'*64, 'research', 'demo-run', 'demo-agent', 'demo-principal')
        self.a = AdapterPin(self.s, 'a', 'v1', 'a'*64, ('read', 'write'), ('READ',))
        self.m = SkillManifestSample(self.s, 'skill', 'v1', 'a'*64, 'b'*64, 'c'*64, ('read',))
        self.p = SourcePin('source', 'v1', 'a'*64, 'license', 'custody')

    def review(self, source, expected, requested=('read',)):
        result = inspect_capabilities(self.m, self.m, self.s, source, expected, self.a,
                                      (self.a,), requested, ('read',))
        self.assertEqual(result.effective_tools, ())
        self.assertIs(result.enabled, False)
        self.assertEqual(result.status, 'QUARANTINED')
        return result

    def assert_held(self, source, expected):
        result = self.review(source, expected)
        self.assertEqual(result.reason, 'SKILL_SOURCE_PIN_HOLD')
        self.assertEqual(result.diagnostic_overlap, ())

    def test_expected_pin_subclass_mismatch(self):
        self.assert_held(self.p, EqualPin('other', 'v2', 'b'*64, 'other', 'other'))

    def test_source_pin_subclass_mismatch(self):
        self.assert_held(EqualPin('other', 'v2', 'a'*64, 'other', 'other'), self.p)

    def test_subclass_comparison_not_invoked(self):
        self.assert_held(self.p, RejectComparisonPin('source', 'v1', 'a'*64, 'license', 'custody'))

    def test_expected_text_subclass(self):
        self.assert_held(self.p, replace(self.p, revision=EqualText('v2')))

    def test_source_text_subclass(self):
        self.assert_held(replace(self.p, custody_ref=EqualText('other')), self.p)

    def test_digest_text_subclass(self):
        self.assert_held(replace(self.p, raw_digest=EqualText('b'*64)), self.p)

    def test_plain_exact_match_keeps_diagnostic_only(self):
        r = self.review(self.p, replace(self.p))
        self.assertEqual(r.reason, 'INDEPENDENT_RECEIPTS_ABSENT')
        self.assertEqual(r.diagnostic_overlap, ('read',))

    def test_plain_mismatch(self):
        self.assert_held(self.p, replace(self.p, revision='v2'))

    def test_plain_match_does_not_expand_capability(self):
        r = self.review(self.p, self.p, ('read', 'write'))
        self.assertEqual(r.reason, 'CAPABILITY_HOLD')
        self.assertEqual(r.diagnostic_overlap, ('read',))
