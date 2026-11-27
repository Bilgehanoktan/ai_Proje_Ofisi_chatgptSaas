"""Consumer tests with a disposable signed witness and a doubled recovery review."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.core.agent_runtime.lifecycle import Scope, RunState, RunObservation, LeaseObservation, ClockSample
from app.core.policy.gateway_review import EffectScope, GrantSample
from app.core.policy.witness_review import WitnessSample
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.provider_contract import ProviderKind, ProviderRequest
from app.engines.model_gateway.runtime_binding import InvocationEnvelope, invocation_digest
from app.engines.model_gateway import sample_adapter as sample
from app.engines.skill_engine.manifest_review import SkillManifestSample
from app.engines.skill_engine.resolver import SourcePin
from app.core.agent_runtime.memory_witness import D0MemoryWitnessStore, MemoryWitness, MemoryWitnessReader, witness_bytes
from app.engines.memory_engine.snapshot_store import SnapshotPin
from app.core.agent_runtime.memory_gateway_review import MemoryGatewayReview
from app.engines.model_gateway.invocation_route_binding import InvocationRouteContext

class RecoveredSampleTests(TestCase):
    def setUp(self):
        s=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,
                'research','demo-run','demo-agent','demo-principal')
        run=RunObservation(s,RunState.RUNNING,2,0)
        lease=LeaseObservation(s,'lease','grant',1,0,1,2,3,20,10)
        self.clock=ClockSample(11,2,3,5)
        raw=b'synthetic span'
        a=AdapterPin(s,'demo-model','v1','b'*64,('demo-tool',),())
        b=AdapterPin(s,'demo-fallback','v1','c'*64,('demo-tool',),())
        reg=(a,b)
        req=ProviderRequest(s,ProviderKind.SAMPLE,sha256(raw).hexdigest(),('demo-tool',),(),64)
        env=InvocationEnvelope(run,lease,req,a,b,'reserve','idem',10)
        pin=invocation_digest(env,reg)
        self.ctx=InvocationRouteContext(env,reg,pin,run,lease,self.clock,raw,None,None,None,None,None,None)
        skill=SkillManifestSample(s,'demo-skill','v1','d'*64,'e'*64,'f'*64,('demo-tool',))
        src=SourcePin('demo-source','v1',skill.manifest_digest,'license','custody')
        effect=EffectScope(s,'MODEL_SAMPLE_REVIEW','demo-tool',pin,'grant','admission','lease','budget',2,3,1)
        grant=GrantSample(s,'grant','admission','lease','budget',('MODEL_SAMPLE_REVIEW',),('demo-tool',),pin,2,3,1,20,False)
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name).resolve() / 'consumer.witness.sqlite'
        store = D0MemoryWitnessStore.create(path)
        key = Ed25519PrivateKey.generate()
        self.public_key = key.public_key().public_bytes_raw()
        snapshot = SnapshotPin(1, 'a' * 64, 'b' * 64)
        signed = MemoryWitness(s, 1, 1, 2, 3, snapshot, 10, 20)
        self.wpin = store.append(signed, key.sign(witness_bytes(signed)), self.public_key, None)
        w=WitnessSample(s,self.wpin.key_sha,3,1,self.wpin.record_sha,10)
        self.cap=sample.SampleCapabilityContext(skill,skill,src,src,('demo-tool',),effect,grant,grant,w,w,5)
        self.reader = MemoryWitnessReader(path)
        self.owner=NS(budget=NS(budget_id='budget'))
        p=patch('app.core.agent_runtime.memory_gateway_review.inspect_recovered_memory_gateway',
                return_value=MemoryGatewayReview('D0_RECOVERED_MEMORY_GATEWAY_MATCH_ONLY',True))
        self.gate=p.start(); self.addCleanup(p.stop)
    def review(self, **changes):
        args=dict(ctx=self.ctx,current_run=self.ctx.current_run,current_lease=self.ctx.current_lease,
                  clock=self.clock,context=None,expected_joint_pin='a'*64,memory_path=None,
                  reader=self.reader,expected_witness=self.wpin,public_key=self.public_key,
                  snapshot=self.owner,reference=self.owner,budget_reference=self.owner.budget,
                  expected_owner_pin='b'*64,capabilities=self.cap,checkpoint_body=b'checkpoint',
                  checkpoint_signature=b's'*64,checkpoint_sha='c'*64)
        args.update(changes); out=sample.sample_task_output_with_recovered_memory(**args)
        self.assertFalse(out.provider_called or out.spend_allowed or out.dispatch_allowed)
        return out
    def test_actual_fixed_output_consumer(self):
        r=self.review(); self.assertEqual(r.reason,'FIXED_SAMPLE_ONLY'); self.assertIsNotNone(r.output)
        self.assertNotIn(self.ctx.raw.decode(),r.output); self.gate.assert_called_once()
    def test_runtime_denied_no_output(self):
        self.gate.return_value=MemoryGatewayReview('HOLD'); self.assertIsNone(self.review().output)
    def test_run_drift_before_signed_review(self):
        r=self.review(current_run=replace(self.ctx.current_run,version=3)); self.assertIsNone(r.output); self.gate.assert_not_called()
    def test_lease_drift_before_signed_review(self):
        r=self.review(current_lease=replace(self.ctx.current_lease,fence=2)); self.assertIsNone(r.output); self.gate.assert_not_called()
    def test_different_budget_no_output(self):
        r=self.review(snapshot=NS(budget=NS(budget_id='other'))); self.assertEqual(r.reason,'D0_RECOVERED_SAMPLE_BUDGET_HOLD')
    def test_different_witness_no_output(self):
        w=replace(self.cap.witness,sequence=2); r=self.review(capabilities=replace(self.cap,witness=w,witness_reference=w)); self.assertEqual(r.reason,'D0_RECOVERED_SAMPLE_WITNESS_HOLD')
    def test_revoked_grant_real_policy(self):
        g=replace(self.cap.grant,revoked=True); r=self.review(capabilities=replace(self.cap,grant=g,grant_reference=g)); self.assertEqual(r.reason,'GRANT_REVOKED'); self.assertIsNone(r.output)
    def test_missing_skill_capability_real_resolver(self):
        self.assertEqual(self.review(capabilities=replace(self.cap,policy_tools=())).reason,'D0_SAMPLE_SKILL_HOLD')
    def test_latest_clock_rejects_expiry(self):
        self.assertIsNone(self.review(clock=replace(self.clock,now_tick=20)).output)
    def test_reader_exception_no_output(self):
        with patch.object(MemoryWitnessReader,'read_latest',side_effect=RuntimeError('private detail')):
            r=self.review(); self.assertIsNone(r.output); self.assertEqual(r.reason,'D0_RECOVERED_SAMPLE_REVIEW_ERROR_HOLD')
    def test_gateway_exception_no_fallback(self):
        self.gate.side_effect=RuntimeError('private detail')
        with patch.object(sample,'sample_task_output',wraps=sample.sample_task_output) as fallback:
            self.assertIsNone(self.review().output); fallback.assert_not_called()
    def test_wrong_input_real_invocation(self):
        self.assertEqual(self.review(ctx=replace(self.ctx,raw=b'wrong')).reason,'MODEL_INPUT_DIGEST_HOLD')
