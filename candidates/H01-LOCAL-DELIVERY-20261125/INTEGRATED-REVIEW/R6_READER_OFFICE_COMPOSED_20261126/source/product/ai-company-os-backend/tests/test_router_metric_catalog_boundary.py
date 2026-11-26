"""D0 regression: catalog membership must hold even when no model is eligible."""
import unittest
from dataclasses import replace
import test_router_cost_review as original
from app.engines.model_gateway.router import metrics_digest, policy_digest
from app.engines.model_gateway.routing_decision import (
    RoutingDecisionRecord, make_routing_decision, routing_decision_digest,
    verify_routing_decision,
)


class MetricCatalogBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = original.RouteTests()
        self.fixture.setUp()
        f = self.fixture
        foreign = "f" * 64
        self.bad_metrics = f.metrics + (replace(f.metrics[0], profile_digest=foreign,
                                   cost=replace(f.cost, profile_digest=foreign)),)

    def test_empty_allowlist_rejects_foreign_metrics(self):
        f = self.fixture
        result = f.policy_route(replace(f.policy, allowed=()), self.bad_metrics)
        self.assertEqual(result.reason, "ROUTE_METRIC_CATALOG_HOLD")
        self.assertEqual(result.candidates, ())
        self.assertEqual(result.excluded, ())

    def test_no_capability_rejects_foreign_metrics(self):
        f = self.fixture
        p = replace(f.policy, metrics_pin=metrics_digest(self.bad_metrics))
        result = f.route(query=replace(f.query, requested=("vision",)), policy=p,
                         expected_policy_pin=policy_digest(p), metrics=self.bad_metrics)
        self.assertEqual(result.reason, "ROUTE_METRIC_CATALOG_HOLD")
        self.assertEqual(result.candidates, ())

    def test_replay_rejects_bad_catalog_even_when_no_candidates(self):
        f = self.fixture
        p = replace(f.policy, allowed=(), metrics_pin=metrics_digest(self.bad_metrics))
        pin = policy_digest(p)
        # A structurally hashable historical record must not be replay-verifiable.
        historical = RoutingDecisionRecord(f.query, p, pin, "NO_ELIGIBLE_PROFILE_HOLD", (),
                                          tuple(sorted((k,"NOT_ALLOWLISTED") for k in f.keys)))
        self.assertFalse(verify_routing_decision(historical, routing_decision_digest(historical),
                         f.profiles, f.registry, self.bad_metrics, 2, 3))
        with self.assertRaises(ValueError):
            make_routing_decision(f.query, f.profiles, f.registry, p, pin, self.bad_metrics, 2, 3)

    def test_valid_no_eligible_and_normal_replay_preserved(self):
        f = self.fixture
        for p in (f.policy, replace(f.policy, allowed=())):
            pin = policy_digest(p)
            record = make_routing_decision(f.query, f.profiles, f.registry, p, pin, f.metrics, 2, 3)
            self.assertEqual(record.reason, "D0_SCREENED_CANDIDATES_ONLY" if p.allowed else "NO_ELIGIBLE_PROFILE_HOLD")
            self.assertTrue(verify_routing_decision(record, routing_decision_digest(record),
                            f.profiles, f.registry, f.metrics, 2, 3))
            self.assertFalse(record.provider_call_allowed or record.spend_allowed or record.dispatch_allowed)
            self.assertIsNone(record.selected_model)

    def test_existing_eligible_case_and_invalid_pin_precedence(self):
        f = self.fixture
        self.assertEqual(f.policy_route(f.policy, self.bad_metrics).reason, "ROUTE_METRIC_CATALOG_HOLD")
        p = replace(f.policy, allowed=(), metrics_pin=metrics_digest(self.bad_metrics))
        self.assertEqual(f.route(policy=p, expected_policy_pin="0"*64, metrics=self.bad_metrics).reason,
                         "ROUTE_POLICY_PIN_HOLD")
        self.assertEqual(f.route(policy=p, expected_policy_pin=policy_digest(p), metrics=f.metrics).reason,
                         "ROUTE_METRIC_PIN_HOLD")
