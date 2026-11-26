"""0221 fixed-output model/skill/gateway composition: no actual model or tool."""
from dataclasses import replace
from hashlib import sha256
from unittest import TestCase
from app.core.agent_runtime.lifecycle import Scope, RunState, RunObservation, LeaseObservation, ClockSample
from app.core.policy.gateway_review import EffectScope, GrantSample
from app.core.policy.witness_review import WitnessSample
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderKind, ProviderRequest
from app.engines.model_gateway.runtime_binding import InvocationEnvelope, invocation_digest
from app.engines.model_gateway.sample_adapter import SampleCapabilityContext, sample_task_output
from app.engines.skill_engine.manifest_review import SkillManifestSample
from app.engines.skill_engine.resolver import SourcePin

class SampleTaskTests(TestCase):
    def setUp(self):
        s=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,
                'research','demo-run','demo-agent','demo-principal')
        r=RunObservation(s,RunState.RUNNING,2,0)
        l=LeaseObservation(s,'lease','grant',1,0,1,2,3,20,10)
        self.clock=ClockSample(11,2,3,5)
        self.raw=b'synthetic span'
        a=AdapterPin(s,'demo-model','v1','b'*64,('demo-tool',),())
        b=AdapterPin(s,'demo-fallback','v1','c'*64,('demo-tool',),())
        self.registry=(a,b)
        req=ProviderRequest(s,ProviderKind.SAMPLE,sha256(self.raw).hexdigest(),('demo-tool',),(),64)
        self.env=InvocationEnvelope(r,l,req,a,b,'reserve','idem',10)
        skill=SkillManifestSample(s,'demo-skill','v1','d'*64,'e'*64,'f'*64,('demo-tool',))
        src=SourcePin('demo-source','v1',skill.manifest_digest,'license','custody')
        effect=EffectScope(s,'MODEL_SAMPLE_REVIEW','demo-tool',invocation_digest(self.env,self.registry),
                           'grant','admission','lease','budget',2,3,1)
        grant=GrantSample(s,'grant','admission','lease','budget',('MODEL_SAMPLE_REVIEW',),('demo-tool',),
                          effect.effect_digest,2,3,1,20,False)
        w=WitnessSample(s,'demo-root',3,1,'1'*64,10)
        self.cap=SampleCapabilityContext(skill,skill,src,src,('demo-tool',),effect,grant,grant,w,w,5)
    def check(self,env=None,cap=None,clock=None,raw=None):
        out=sample_task_output(env or self.env,self.registry,cap or self.cap,clock or self.clock,
                               self.raw if raw is None else raw)
        self.assertFalse(out.provider_called or out.spend_allowed or out.dispatch_allowed)
        return out
    def hold(self,**kw):
        self.assertIsNone(self.check(**kw).output)
    def test_fixed_output(self):
        r=self.check();self.assertEqual(r.reason,'FIXED_SAMPLE_ONLY');self.assertIsNotNone(r.output)
        self.assertEqual(r,self.check());self.assertNotIn(self.raw.decode(),r.output)
    def test_raw_digest_mismatch(self):self.hold(raw=b'wrong')
    def test_live_provider(self):
        self.hold(env=replace(self.env,request=replace(self.env.request,provider=ProviderKind.OPENAI)))
    def test_enabled_skill(self):
        k=replace(self.cap.skill,enabled=True)
        self.hold(cap=replace(self.cap,skill=k,skill_reference=k))
    def test_skill_source_drift(self):
        self.hold(cap=replace(self.cap,source=replace(self.cap.source,raw_digest='0'*64)))
    def test_policy_capability_missing(self):self.hold(cap=replace(self.cap,policy_tools=()))
    def test_wrong_effect_digest(self):
        self.hold(cap=replace(self.cap,effect=replace(self.cap.effect,effect_digest='0'*64)))
    def test_revoked_grant(self):
        g=replace(self.cap.grant,revoked=True)
        self.hold(cap=replace(self.cap,grant=g,grant_reference=g))
    def test_wrong_witness(self):
        self.hold(cap=replace(self.cap,witness=replace(self.cap.witness,record_digest='0'*64)))
    def test_expired_lease(self):self.hold(clock=replace(self.clock,now_tick=20))
    def test_wrong_scope(self):
        e=replace(self.cap.effect,scope=replace(self.env.run.scope,principal_id='demo-other'))
        self.hold(cap=replace(self.cap,effect=e))
    def test_effectful_request(self):
        self.hold(env=replace(self.env,request=replace(self.env.request,effects=('write',))))
