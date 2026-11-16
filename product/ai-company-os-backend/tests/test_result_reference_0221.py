"""0221 source candidates for archive/result pin + original T1; not live authority."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import sqlite3
from unittest import TestCase
from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.joint_context import JointContext
from app.core.agent_runtime.memory_witness import LatestWitnessPin
from app.core.transaction.fenced_transition import (CompanyTransitionContext, SampleResultPin,
    sample_result_bytes, resolve_result_binding, company_transition_binding)
from app.core.transaction.witnessed_mapping import binding_digest
from app.core.transaction.postgres_transition_mapping import transaction_ref
from app.engines.memory_engine.snapshot_store import SnapshotPin
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderRequest, ProviderKind
from app.engines.model_gateway.runtime_binding import InvocationEnvelope, invocation_digest
from app.core.policy.gateway_review import EffectScope, GrantSample
from app.core.policy.witness_review import WitnessSample
from app.engines.skill_engine.manifest_review import SkillManifestSample
from app.engines.skill_engine.resolver import SourcePin
from app.engines.model_gateway.sample_adapter import SampleCapabilityContext
import test_company_fence_binding_0219 as prior

class ResultReferenceTests(TestCase):
    def setUp(self):
        f=prior.CompanyFenceBindingTests();f.setUp();self.addCleanup(f.doCleanups)
        self.f=f;self.company=f.ctx;self.intent=f.intent;self.clock=f.f.clock
        r,l=f.f.before,f.f.lease;s=r.scope
        self.raw=b'synthetic span'
        a=AdapterPin(s,'demo-model','v1','b'*64,('demo-tool',),())
        b=AdapterPin(s,'demo-fallback','v1','c'*64,('demo-tool',),())
        self.registry=(a,b)
        req=ProviderRequest(s,ProviderKind.SAMPLE,sha256(self.raw).hexdigest(),('demo-tool',),(),64)
        e=InvocationEnvelope(r,l,req,a,b,transaction_ref(self.company.admission.intent),
                             self.intent.idempotency_key,10)
        self.context=JointContext(SnapshotPin(1,'a'*64,'b'*64),e)
        self.witness=LatestWitnessPin('1'*64,'2'*64,1)
        self.wb=binding_digest(self.intent,self.context,self.registry,self.witness)
        self.cp=company_transition_binding(self.intent,self.wb,self.company)
        k=SkillManifestSample(s,'demo-skill','v1','d'*64,'e'*64,'f'*64,('demo-tool',))
        src=SourcePin('demo-source','v1',k.manifest_digest,'license','custody')
        claim=self.company.admission.claim
        eff=EffectScope(s,'MODEL_SAMPLE_REVIEW','demo-tool',invocation_digest(e,self.registry),
                        l.grant_id,claim.admission_id,l.lease_id,claim.budget.budget_id,
                        l.policy_epoch,l.witness_epoch,l.fence)
        g=GrantSample(s,l.grant_id,claim.admission_id,l.lease_id,claim.budget.budget_id,
                      ('MODEL_SAMPLE_REVIEW',),('demo-tool',),eff.effect_digest,l.policy_epoch,l.witness_epoch,l.fence,20,False)
        w=WitnessSample(s,'demo-root',l.witness_epoch,1,self.witness.record_sha,10)
        self.cap=SampleCapabilityContext(k,k,src,src,('demo-tool',),eff,g,g,w,w,5)
        self.store=f.f.archive
    def body(self,cap=None,context=None,wb=None):
        return sample_result_bytes(self.intent,context or self.context,self.registry,self.witness,wb or self.wb,
                                   self.company,cap or self.cap,self.clock,self.raw)
    def resolve(self,result,reader):
        return resolve_result_binding(self.intent,self.context,self.registry,self.witness,self.wb,self.company,
                                      self.cp,result,reader,self.clock,self.raw)
    def test_exact_archive_profile(self):
        body=self.body();key=self.store.put(body);pin=SampleResultPin(self.cap,key)
        self.assertNotEqual(self.resolve(pin,self.store),self.cp)
        self.assertEqual(self.resolve(None,None),self.cp)
        self.assertNotIn(self.raw,body)
    def test_missing_and_wrong_archive(self):
        with self.assertRaises(ValueError):self.resolve(SampleResultPin(self.cap,'0'*64),self.store)
        with self.assertRaises(ValueError):self.resolve(None,self.store)
        with self.assertRaises(ValueError):self.resolve(SampleResultPin(self.cap,self.store.put(b'wrong')),self.store)
    def test_wrong_reservation(self):
        c=replace(self.context,invocation=replace(self.context.invocation,reservation_ref='wrong'))
        with self.assertRaisesRegex(ValueError,'RESERVATION'):
            self.body(context=c,wb=binding_digest(self.intent,c,self.registry,self.witness))
    def test_wrong_ceiling(self):
        c=replace(self.context,invocation=replace(self.context.invocation,sample_cost_ceiling_minor=21))
        with self.assertRaisesRegex(ValueError,'RESERVATION'):
            self.body(context=c,wb=binding_digest(self.intent,c,self.registry,self.witness))
    def test_wrong_witness_digest(self):
        w=replace(self.cap.witness,record_digest='0'*64)
        with self.assertRaisesRegex(ValueError,'EFFECT_OR_WITNESS'):
            self.body(cap=replace(self.cap,witness=w,witness_reference=w))
    def test_wrong_admission(self):
        e=replace(self.cap.effect,admission_id='other')
        with self.assertRaisesRegex(ValueError,'EFFECT_OR_WITNESS'):
            self.body(cap=replace(self.cap,effect=e))
