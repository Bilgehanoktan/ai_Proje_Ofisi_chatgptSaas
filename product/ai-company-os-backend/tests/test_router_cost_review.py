"""Synthetic policy screening and cost estimates. No provider, DB or authorization."""
from dataclasses import replace
import unittest
from app.core.agent_runtime.lifecycle import Scope
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderKind
from app.engines.model_gateway.profile_registry import ModelProfile, profile_digest, catalog_digest
from app.engines.model_gateway.capability_resolver import CapabilityQuery
from app.engines.model_gateway.cost_estimator import CostProfile, cost_digest, estimate_cost
from app.engines.model_gateway.router import RouteMetric, RoutePolicy, metrics_digest, policy_digest, inspect_route

class RouteTests(unittest.TestCase):
    def setUp(self):
        s=Scope("synthetic-tenant","synthetic-company","A0_SAMPLE_ONLY","sha256:"+"a"*64,"task","demo-run","demo-agent","demo-principal")
        a=AdapterPin(s,"demo-model","v1","b"*64,("text",),())
        b=replace(a,adapter_id="demo-fallback")
        self.registry=(a,b)
        p=ModelProfile(a,ProviderKind.SAMPLE,"sample-a","v1",100,20,("synthetic",),("local",),("routine",),"cost-a","latency-a")
        self.profiles=(p,replace(p,adapter=b,model_id="sample-b",cost_profile_ref="cost-b",latency_profile_ref="latency-b"))
        self.keys=tuple(profile_digest(p,self.registry) for p in self.profiles)
        self.query=CapabilityQuery(s,("text",),"synthetic","local","routine",40,10)
        self.cost=CostProfile(self.keys[0],"cost-a","USD",100,10,20,1)
        self.metrics=(RouteMetric(self.keys[0],self.cost,"latency-a",40),
                      RouteMetric(self.keys[1],replace(self.cost,profile_digest=self.keys[1],reference="cost-b",input_minor=20),"latency-b",20))
        self.policy=RoutePolicy(s,"policy-v1",catalog_digest(self.profiles,self.registry,s),self.keys,metrics_digest(self.metrics),"USD",30,100,2,3)

    def route(self, **changes):
        args=dict(query=self.query,profiles=self.profiles,registry=self.registry,policy=self.policy,
                  expected_policy_pin=policy_digest(self.policy),metrics=self.metrics,current_policy_epoch=2,current_witness_epoch=3)
        args.update(changes)
        r=inspect_route(**args)
        self.assertEqual(r.decision,"HOLD")
        self.assertIsNone(r.selected_model)
        self.assertFalse(r.provider_call_allowed or r.spend_allowed or r.dispatch_allowed)
        return r

    def policy_route(self,p,metrics=None):
        metrics=self.metrics if metrics is None else metrics
        p=replace(p,metrics_pin=metrics_digest(metrics))
        return self.route(policy=p,expected_policy_pin=policy_digest(p),metrics=metrics)

    def test_cost_rounding(self):
        p=replace(self.cost,token_unit=100,input_minor=1,output_minor=1,fixed_minor=0)
        r=estimate_cost(p,cost_digest(p),self.keys[0],"cost-a","USD",1,1)
        self.assertEqual(r.estimated_minor,2)
        self.assertIsNone(r.actual_minor)
        self.assertFalse(r.reservation_created or r.spend_allowed)

    def test_cost_reference_and_limits(self):
        for change,reason in [({"expected_digest":"c"*64},"COST_PIN_HOLD"),({"currency":"EUR"},"COST_BINDING_HOLD"),({"input_tokens":True},"COST_TOKEN_HOLD"),({"output_tokens":0},"COST_TOKEN_HOLD")]:
            with self.subTest(change=change):
                args=dict(p=self.cost,expected_digest=cost_digest(self.cost),profile_pin=self.keys[0],reference="cost-a",currency="USD",input_tokens=40,output_tokens=10)
                args.update(change)
                self.assertEqual(estimate_cost(**args).reason,reason)
        p=replace(self.cost,input_minor=2**63-1,token_unit=1)
        self.assertEqual(estimate_cost(p,cost_digest(p),self.keys[0],"cost-a","USD",2,1).reason,"COST_OVERFLOW_HOLD")

    def test_candidates_no_ranking(self):
        r=self.route()
        self.assertEqual(r.reason,"D0_SCREENED_CANDIDATES_ONLY")
        self.assertEqual(tuple(c.profile_digest for c in r.candidates),tuple(sorted(self.keys)))
        self.assertEqual({c.profile_digest:c.estimated_minor for c in r.candidates},{self.keys[0]:7,self.keys[1]:11})

    def test_cost_and_latency_filters(self):
        r=self.policy_route(replace(self.policy,max_cost_minor=7))
        self.assertEqual(tuple(c.profile_digest for c in r.candidates),(self.keys[0],))
        self.assertIn((self.keys[1],"COST_LIMIT_HOLD"),r.excluded)
        r=self.policy_route(replace(self.policy,max_latency_ms=20))
        self.assertEqual(tuple(c.profile_digest for c in r.candidates),(self.keys[1],))
        self.assertIn((self.keys[0],"LATENCY_LIMIT_HOLD"),r.excluded)

    def test_missing_metrics_and_no_fallback(self):
        r=self.policy_route(self.policy,())
        self.assertEqual(r.reason,"NO_ROUTE_CANDIDATE_HOLD")
        self.assertEqual({reason for _,reason in r.excluded},{"METRIC_MISSING"})
        r=self.policy_route(replace(self.policy,max_cost_minor=0))
        self.assertEqual(r.candidates,())

    def test_pin_and_epoch_changes(self):
        self.assertEqual(self.route(expected_policy_pin="d"*64).reason,"ROUTE_POLICY_PIN_HOLD")
        self.assertEqual(self.route(current_policy_epoch=3).reason,"ROUTE_SCOPE_EPOCH_HOLD")
        self.assertEqual(self.route(current_witness_epoch=4).reason,"ROUTE_SCOPE_EPOCH_HOLD")
        self.assertEqual(self.route(metrics=(replace(self.metrics[0],latency_upper_ms=10),self.metrics[1])).reason,"ROUTE_METRIC_PIN_HOLD")

    def test_policy_allowlist_and_capabilities(self):
        self.assertEqual(self.policy_route(replace(self.policy,allowed=())).reason,"NO_ELIGIBLE_PROFILE_HOLD")
        self.assertEqual(self.route(query=replace(self.query,requested=("vision",))).reason,"NO_ELIGIBLE_PROFILE_HOLD")

    def test_metric_reference_binding(self):
        m=replace(self.metrics[0],latency_ref="other")
        self.assertIn((self.keys[0],"LATENCY_REFERENCE_MISMATCH"),self.policy_route(self.policy,(m,self.metrics[1])).excluded)
        m=replace(self.metrics[0],cost=replace(self.cost,reference="other"))
        self.assertIn((self.keys[0],"COST_BINDING_HOLD"),self.policy_route(self.policy,(m,self.metrics[1])).excluded)

    def test_non_sample_provider_never_routes(self):
        p=replace(self.profiles[0],provider=ProviderKind.OLLAMA)
        profiles=(p,self.profiles[1])
        key=profile_digest(p,self.registry)
        metrics=(replace(self.metrics[0],profile_digest=key,cost=replace(self.cost,profile_digest=key)),self.metrics[1])
        policy=replace(self.policy,catalog_pin=catalog_digest(profiles,self.registry,self.query.scope),allowed=(key,self.keys[1]),metrics_pin=metrics_digest(metrics))
        r=self.route(profiles=profiles,policy=policy,expected_policy_pin=policy_digest(policy),metrics=metrics)
        self.assertIn((key,"PROVIDER_EGRESS_HOLD"),r.excluded)

    def test_duplicates_and_order(self):
        self.assertEqual(self.route(metrics=(self.metrics[0],)*2).reason,"ROUTE_REFERENCE_INVALID_HOLD")
        self.assertEqual(metrics_digest(tuple(reversed(self.metrics))),self.policy.metrics_pin)
        self.assertEqual(self.route(metrics=tuple(reversed(self.metrics))),self.route())

if __name__=="__main__":
    unittest.main()
