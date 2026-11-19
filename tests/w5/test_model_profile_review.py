"""D0 model profile and capability review tests. No calls, DB or cost."""
from dataclasses import replace
import unittest
from app.core.agent_runtime.lifecycle import Scope
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderKind
from app.engines.model_gateway.profile_registry import ModelProfile, valid_profile, profile_digest, catalog_digest
from app.engines.model_gateway.capability_resolver import CapabilityQuery, inspect_capabilities

class ModelProfileTests(unittest.TestCase):
    def setUp(self):
        s=Scope("synthetic-tenant","synthetic-company","A0_SAMPLE_ONLY","sha256:"+"a"*64,"task","demo-run","demo-agent","demo-principal")
        a=AdapterPin(s,"demo-model","v1","b"*64,("text","code"),())
        b=replace(a,adapter_id="demo-fallback",capabilities=("text",))
        self.registry=(a,b)
        p=ModelProfile(a,ProviderKind.SAMPLE,"sample-a","v1",100,20,("synthetic",),("local",),("routine",),"cost-a","latency-a")
        self.profiles=(p,replace(p,adapter=b,model_id="sample-b"))
        self.query=CapabilityQuery(s,("text",),"synthetic","local","routine",40,10)
        self.pin=catalog_digest(self.profiles,self.registry,s)
        self.allowed=tuple(profile_digest(p,self.registry) for p in self.profiles)

    def review(self,**changes):
        args=dict(query=self.query,profiles=self.profiles,registry=self.registry,
                  expected_catalog_digest=self.pin,allowed_profile_digests=self.allowed)
        args.update(changes)
        r=inspect_capabilities(**args)
        self.assertEqual(r.decision,"HOLD")
        self.assertIsNone(r.selected_model)
        self.assertFalse(r.provider_call_allowed or r.spend_allowed or r.dispatch_allowed)
        return r

    def test_matching_candidates_never_authorize(self):
        r=self.review()
        self.assertEqual(r.candidate_digests,tuple(sorted(self.allowed)))
        self.assertEqual(r.reason,"D0_CANDIDATES_ONLY")

    def test_capability_filter(self):
        r=self.review(query=replace(self.query,requested=("code",)))
        self.assertEqual(r.candidate_digests,(self.allowed[0],))
        self.assertEqual(r.excluded,((self.allowed[1],"CAPABILITY_MISMATCH"),))

    def test_allowlist(self):
        r=self.review(allowed_profile_digests=(self.allowed[1],))
        self.assertEqual(r.candidate_digests,(self.allowed[1],))
        self.assertEqual(self.review(allowed_profile_digests=()).reason,"NO_ELIGIBLE_PROFILE_HOLD")
        self.assertEqual(self.review(allowed_profile_digests=("c"*64,)).reason,"ALLOWLIST_CATALOG_MISMATCH_HOLD")

    def test_rejection_matrix(self):
        for field,value,reason in [
            ("data_class","private","DATA_REGION_MISMATCH"),
            ("region","remote","DATA_REGION_MISMATCH"),
            ("complexity_class","advanced","COMPLEXITY_MISMATCH"),
            ("output_tokens",21,"TOKEN_LIMIT_MISMATCH"),
            ("input_tokens",91,"TOKEN_LIMIT_MISMATCH"),
            ("requested",("vision",),"CAPABILITY_MISMATCH")]:
            with self.subTest(field=field):
                r=self.review(query=replace(self.query,**{field:value}))
                self.assertEqual(r.reason,"NO_ELIGIBLE_PROFILE_HOLD")
                self.assertEqual({v for _,v in r.excluded},{reason})

    def test_invalid_query(self):
        for field,value in [("input_tokens",True),("output_tokens",0),("requested",()),("data_class",""),("scope",None)]:
            with self.subTest(field=field):
                self.assertEqual(self.review(query=replace(self.query,**{field:value})).reason,"CAPABILITY_QUERY_HOLD")

    def test_pin_and_scope(self):
        self.assertEqual(self.review(expected_catalog_digest="d"*64).reason,"MODEL_CATALOG_PIN_HOLD")
        self.assertEqual(self.review(query=replace(self.query,scope=replace(self.query.scope,run_id="demo-other"))).reason,"MODEL_CATALOG_INVALID_HOLD")

    def test_profile_metadata_mutation(self):
        p=self.profiles[0]
        for field,value in [("model_revision","v2"),("context_limit",101),("cost_profile_ref","other"),("provider",ProviderKind.OLLAMA)]:
            with self.subTest(field=field):
                new=(replace(p,**{field:value}),self.profiles[1])
                self.assertEqual(self.review(profiles=new).reason,"MODEL_CATALOG_PIN_HOLD")

    def test_invalid_profile(self):
        p=self.profiles[0]
        for field,value in [("context_limit",0),("output_limit",101),("regions",()),("data_classes",("synthetic","synthetic")),("provider","SAMPLE"),("adapter",replace(p.adapter,enabled=True))]:
            with self.subTest(field=field):
                self.assertFalse(valid_profile(replace(p,**{field:value}),self.registry))
                self.assertEqual(self.review(profiles=(replace(p,**{field:value}),)).reason,"MODEL_CATALOG_INVALID_HOLD")

    def test_duplicates(self):
        self.assertEqual(self.review(profiles=(self.profiles[0],)*2).reason,"MODEL_CATALOG_INVALID_HOLD")
        self.assertEqual(self.review(registry=self.registry+(self.registry[0],)).reason,"MODEL_CATALOG_INVALID_HOLD")
        self.assertEqual(self.review(allowed_profile_digests=(self.allowed[0],)*2).reason,"CAPABILITY_POLICY_REFERENCE_HOLD")

    def test_order_independence_and_boundary(self):
        self.assertEqual(catalog_digest(tuple(reversed(self.profiles)),self.registry,self.query.scope),self.pin)
        self.assertEqual(self.review(query=replace(self.query,input_tokens=80,output_tokens=20)).candidate_digests,tuple(sorted(self.allowed)))

if __name__=="__main__":
    unittest.main()
