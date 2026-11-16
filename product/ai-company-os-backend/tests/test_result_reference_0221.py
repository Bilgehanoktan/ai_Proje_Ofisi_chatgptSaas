"""0221 source candidates for archive/result pin + original T1; not live authority."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import sqlite3
from unittest import TestCase
from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.joint_context import JointContext
from app.core.agent_runtime.memory_witness import D0MemoryWitnessStore, MemoryWitness, witness_bytes
from app.core.transaction.fenced_transition import (CompanyTransitionContext, SampleResultPin,
    sample_result_bytes, resolve_result_binding, company_transition_binding, D0IntentJournal, intent_pin)
from app.core.transaction.witnessed_mapping import binding_digest
from app.core.transaction.postgres_transition_mapping import transaction_ref
from app.engines.memory_engine.snapshot_store import Snapshot, create_store, publish_snapshot
from app.engines.memory_engine.retrieval import Node, TombstoneView
from app.engines.memory_engine.runtime_binding import MemoryAclEntry, MemoryAclView
from app.engines.knowledge_engine.provenance import SourceVersion, ClaimSpan
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderRequest, ProviderKind
from app.engines.model_gateway.runtime_binding import InvocationEnvelope, invocation_digest
from app.core.policy.gateway_review import EffectScope, GrantSample
from app.core.policy.witness_review import WitnessSample
from app.engines.skill_engine.manifest_review import SkillManifestSample
from app.engines.skill_engine.resolver import SourcePin
from app.engines.model_gateway.sample_adapter import SampleCapabilityContext
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin, execute_authority_fenced_transition
from app.core.transaction.postgres_session import CommitOutcomeUnknown
from app.core.transaction.review import LogicalIntent, Operation
from app.core.agent_runtime.transition_command import transition_digest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_transition_mapping_0194 import SQLiteConnectionShim
import test_scheduled_admission_0220 as prior

class ResultReferenceTests(TestCase):
    def setUp(self):
        scheduled=prior.ScheduledAdmissionTests();scheduled.setUp();self.addCleanup(scheduled.doCleanups)
        f=scheduled.f;scheduled.invoke()
        f.history+=(f.event(f.admit,'D0_RUN_ADMISSION',0,20),)
        f.before=replace(f.before,state=RunState.ADMITTED,version=1)
        f.budget=replace(f.budget,revision=1,outstanding_minor=20)
        f.ordinary(RunState.RUNNING)
        self.prepare_result_context(f)

    def prepare_result_context(self,f):
        """Reuse the exact 0221 result pins on an already-admitted RUNNING fixture."""
        self.f=f;self.clock=f.clock
        r,l=f.before,f.lease;s=r.scope
        self.intent=LogicalIntent(s,Operation.STATE_MUTATION,r.version,transition_digest(r,RunState.VERIFYING),
            'verify-0221','verify-idem-0221',l.grant_id,l.lease_id,None,l.policy_epoch,l.witness_epoch)
        self.company=CompanyTransitionContext(f.binding,f.members,f.pool,f.history,
            f.event(self.intent,'D0_RUN_TRANSITION'))
        self.raw=b'synthetic span'
        full=b'prefix '+self.raw+b' suffix'
        source=SourceVersion(s,'source','v1',sha256(full).hexdigest())
        span=ClaimSpan(source,7,7+len(self.raw),sha256(self.raw).hexdigest())
        node=Node(s,'source','v1',source.raw_digest,())
        tomb=TombstoneView(s,1,1,(),True)
        acl=MemoryAclView(s,r.version,r.attempt,l.policy_epoch,l.witness_epoch,1,1,1,True,
            (MemoryAclEntry('source','v1',source.raw_digest,'ALLOW_READ'),))
        self.snapshot=Snapshot(r,(node,),'source',tomb,acl,source,span,full)
        self.memory=f.path.with_name('sample.d0.sqlite');create_store(self.memory)
        self.memory_pin=publish_snapshot(self.memory,self.snapshot,None)
        self.wreader=D0MemoryWitnessStore.create(f.path.with_name('sample.witness.sqlite'))
        key=Ed25519PrivateKey.generate();self.pub=key.public_key().public_bytes_raw()
        record=MemoryWitness(s,1,1,l.policy_epoch,l.witness_epoch,self.memory_pin,10,19)
        self.witness=self.wreader.append(record,key.sign(witness_bytes(record)),self.pub,None)
        self.journal=D0IntentJournal.create(f.path.with_name('sample.intent.sqlite'))
        self.authority=D0IntentAuthority.create(f.path.with_name('sample.authority.sqlite'),
            RootPin(self.witness.record_sha,self.witness.key_sha,self.witness.recovery_epoch))
        a=AdapterPin(s,'demo-model','v1','b'*64,('demo-tool',),())
        b=AdapterPin(s,'demo-fallback','v1','c'*64,('demo-tool',),())
        self.registry=(a,b)
        req=ProviderRequest(s,ProviderKind.SAMPLE,sha256(self.raw).hexdigest(),('demo-tool',),(),64)
        e=InvocationEnvelope(r,l,req,a,b,transaction_ref(self.company.admission.intent),
                             self.intent.idempotency_key,10)
        self.context=JointContext(self.memory_pin,e)
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
        w=WitnessSample(s,self.witness.key_sha,l.witness_epoch,1,self.witness.record_sha,10)
        self.cap=SampleCapabilityContext(k,k,src,src,('demo-tool',),eff,g,g,w,w,5)
        self.store=f.archive
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

    def invoke(self,pin,unknown=False):
        return execute_authority_fenced_transition(authority=self.authority,intent=self.intent,
            context=self.context,registry=self.registry,witness=self.witness,expected_binding=self.wb,
            memory_path=self.memory,reader=self.wreader,public_key=self.pub,raw=self.raw,
            journal=self.journal,connect=lambda:SQLiteConnectionShim(self.f.path,unknown),
            clock=lambda:self.clock,company=self.company,expected_company_binding=self.cp,
            result=pin,result_reader=self.store)

    def test_full_0220_admission_0221_result_t1(self):
        pin=SampleResultPin(self.cap,self.store.put(self.body()))
        fence=self.resolve(pin,self.store)
        review=self.invoke(pin)
        self.assertTrue(review.historical_match)
        self.assertFalse(review.dispatch_allowed or review.release_allowed or review.retry_allowed)
        self.f.history+=(self.company.event,)
        self.assertTrue(self.f.company().structural_match)
        self.assertTrue(self.journal.inspect(self.intent,intent_pin(self.intent,fence)).historical_match)

    def test_missing_archive_before_claim(self):
        before=self.f.dump()
        with self.assertRaises(ValueError):
            self.invoke(SampleResultPin(self.cap,'0'*64))
        self.assertEqual(self.f.dump(),before)
        with closing(sqlite3.connect(self.authority.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone(),(0,))

    def test_unknown_after_commit_quarantines(self):
        pin=SampleResultPin(self.cap,self.store.put(self.body()))
        fence=self.resolve(pin,self.store)
        with self.assertRaises(CommitOutcomeUnknown):self.invoke(pin,unknown=True)
        self.f.history+=(self.company.event,)
        self.assertTrue(self.f.company().structural_match)
        self.assertEqual(self.journal.inspect(self.intent,intent_pin(self.intent,fence)).status,'UNKNOWN')
        before=self.f.dump()
        with self.assertRaises(ValueError):self.invoke(pin)
        self.assertEqual(self.f.dump(),before)

    def test_repin_wrong_witness_metadata_rolls_back(self):
        w=replace(self.cap.witness,sequence=2)
        cap=replace(self.cap,witness=w,witness_reference=w)
        pin=SampleResultPin(cap,self.store.put(self.body(cap=cap)))
        before=self.f.dump()
        with self.assertRaisesRegex(ValueError,'WITNESS_METADATA'):
            self.invoke(pin)
        self.assertEqual(self.f.dump(),before)
