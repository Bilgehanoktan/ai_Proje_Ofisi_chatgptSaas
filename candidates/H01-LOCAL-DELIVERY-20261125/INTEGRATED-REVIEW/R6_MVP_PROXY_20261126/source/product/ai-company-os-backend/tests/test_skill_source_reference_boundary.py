"""NW06: independent source-reference shape checks; no grants or provider calls."""
from dataclasses import replace
from unittest import TestCase
from unittest.mock import ANY

from app.engines.skill_engine.resolver import inspect_capabilities
import test_engines_0159b as original


class SkillSourceReferenceTests(TestCase):
    def setUp(self):
        self.f = original.EngineReviewTests()
        self.f.setUp()

    def review(self, expected_source, **changes):
        f = self.f
        args = dict(skill=f.m, reference=f.m, scope=f.s, source=f.p,
                    expected_source=expected_source, adapter=f.a,
                    registry=(f.a,), requested=('read',), policy_tools=('read',))
        args.update(changes)
        result = inspect_capabilities(**args)
        self.assertEqual(result.effective_tools, ())
        self.assertIs(result.enabled, False)
        self.assertEqual(result.status, 'QUARANTINED')
        return result

    def test_foreign_equality_object_is_not_a_source_reference(self):
        result = self.review(ANY)
        self.assertEqual(result.reason, 'SKILL_SOURCE_PIN_HOLD')
        self.assertEqual(result.diagnostic_overlap, ())

    def test_invalid_reference_is_rejected_before_comparison(self):
        class UnvalidatedReference:
            def __eq__(self, other):
                raise AssertionError('Invalid reference was compared')
            def __ne__(self, other):
                raise AssertionError('Invalid reference was compared')
        self.assertEqual(self.review(UnvalidatedReference()).reason, 'SKILL_SOURCE_PIN_HOLD')

    def test_missing_or_malformed_reference_holds(self):
        for ref in (None, {}, replace(self.f.p, license_ref=''),
                    replace(self.f.p, custody_ref='invalid space'),
                    replace(self.f.p, raw_digest='x'*64)):
            with self.subTest(ref=ref):
                self.assertEqual(self.review(ref).reason, 'SKILL_SOURCE_PIN_HOLD')

    def test_valid_but_different_reference_holds(self):
        for field in ('source_id', 'revision', 'license_ref', 'custody_ref'):
            with self.subTest(field=field):
                self.assertEqual(self.review(replace(self.f.p, **{field:'other'})).reason,
                                 'SKILL_SOURCE_PIN_HOLD')

    def test_exact_reference_preserves_diagnostic_overlap_only(self):
        result = self.review(replace(self.f.p))
        self.assertEqual(result.reason, 'INDEPENDENT_RECEIPTS_ABSENT')
        self.assertEqual(result.diagnostic_overlap, ('read',))

    def test_exact_reference_cannot_expand_capability(self):
        result = self.review(self.f.p, requested=('read','write'))
        self.assertEqual(result.reason, 'CAPABILITY_HOLD')
        self.assertEqual(result.diagnostic_overlap, ('read',))
