"""W5 isolated source tests; run with backend on PYTHONPATH."""
import unittest
from app.engines.model_gateway.effect_budget_review import EffectBudgetReview, inspect_effect_budget

class EffectBudgetReviewTests(unittest.TestCase):
    def test_default_is_hold(self):
        r = EffectBudgetReview("test")
        self.assertEqual(r.decision, "HOLD")
        self.assertFalse(r.provider_call_allowed or r.spend_allowed or r.dispatch_allowed)

    def test_structural_match_is_not_authority(self):
        r = EffectBudgetReview("test", True)
        self.assertTrue(r.structural_match)
        self.assertEqual(r.decision, "HOLD")
        self.assertFalse(r.provider_call_allowed or r.spend_allowed or r.dispatch_allowed)

    def test_invalid_envelope(self):
        r = inspect_effect_budget(*([None] * 12))
        self.assertEqual(r.reason, "MODEL_ENVELOPE_HOLD")
        self.assertFalse(r.structural_match)

if __name__ == "__main__":
    unittest.main()
