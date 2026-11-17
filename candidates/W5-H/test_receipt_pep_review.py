"""W5-H local synthetic tests, exact Core sources; no actual owner/IV or provider."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, LeaseObservation, ClockSample
from app.core.policy.gateway_review import EffectScope, GrantSample
from app.core.policy.witness_review import WitnessSample
from app.core.transaction.effect_fence_reference import D0EffectFenceReference, Head
from app.core.transaction.signed_consume_reference import ConsumeRequest, SignedObservation, issue_fixture
from receipt_pep_review import ReceiptEffectPin, receipt_effect_digest, consume_scope, inspect_receipt_pep, inspect_replay, replay_keys


class W5HTests(unittest.TestCase):
    def setUp(self):
        self.s=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,
                     'task','demo-run','demo-agent','demo-principal')
        self.run=RunObservation(self.s,RunState.RUNNING,2,0)
        self.lease=LeaseObservation(self.s,'lease','grant',1,0,1,3,4,200,90)
        self.clock=ClockSample(100,3,4,20)
        self.e=EffectScope(self.s,'MODEL_SAMPLE_REVIEW','adapter','b'*64,'grant','admission','lease','budget',3,4,1)
        self.grant=GrantSample(self.s,'grant','admission','lease','budget',('MODEL_SAMPLE_REVIEW',),
                               ('adapter',),'b'*64,3,4,1,180,False)
        self.w=WitnessSample(self.s,'root',4,5,'c'*64,95)
        self.p=ReceiptEffectPin(self.run,self.lease,self.e,'project','effect','b'*64,'d'*64,'e'*64,
                                'reservation','invocation-idem','f'*64,'1'*64,'2'*64,'tx','USD')
        self.pin=receipt_effect_digest(self.p)
        self.head=Head(1,'3'*64,4)
        self.req=ConsumeRequest(consume_scope(self.p),self.head,'4'*64,self.pin,'tx','b'*64,99,120)
        self.key=Ed25519PrivateKey.generate()
        self.pub=self.key.public_key().public_bytes_raw()
        self.keypin=sha256(self.pub).hexdigest()
        # Actual existing consume fixture: isolated SQLite and real Ed25519 signature.
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.store=D0EffectFenceReference.create(Path(tmp.name)/'unit.effect-reference.sqlite',self.head)
        self.obs=issue_fixture(self.store,self.key,self.req,100)

    def review(self, **kw):
        args=dict(p=self.p,reference=self.p,expected_binding_pin=self.pin,observation=self.obs,
                  expected_consume=self.req,public_key=self.pub,expected_key_sha=self.keypin,current_head=self.head,
                  current_run=self.run,current_lease=self.lease,clock=self.clock,grant=self.grant,
                  grant_reference=self.grant,witness=self.w,witness_reference=self.w,witness_max_age=20,
                  outcome_unknown=False)
        result=inspect_receipt_pep(**(args|kw))
        self.assertEqual((result.decision,result.pep_decision),('HOLD','DENY'))
        for f in ('independent_verified','provider_call_allowed','spend_allowed','retry_allowed',
                  'dispatch_allowed','settlement_allowed','release_allowed'):
            self.assertIs(getattr(result,f),False)
        return result

    def test_valid_signature_remains_consumed_hold(self):
        r=self.review();self.assertTrue(r.signature_match);self.assertTrue(r.pep_reference_match)
        self.assertEqual(r.reason,'SIGNED_CONSUMED_NO_RETRY_CUSTODY_UNPROVEN_HOLD')

    def test_missing_observation(self):
        self.assertFalse(self.review(observation=None).signature_match)

    def test_signature_tamper(self):
        sig=bytes([self.obs.signature[0]^1])+self.obs.signature[1:]
        self.assertFalse(self.review(observation=replace(self.obs,signature=sig)).signature_match)

    def test_wrong_key_and_key_pin(self):
        pub=Ed25519PrivateKey.generate().public_key().public_bytes_raw()
        self.assertFalse(self.review(public_key=pub).signature_match)
        self.assertFalse(self.review(public_key=pub,expected_key_sha=sha256(pub).hexdigest()).signature_match)

    def test_missing_or_wrong_reference(self):
        for x in (None,replace(self.p,reservation_id='other')):
            self.assertFalse(self.review(reference=x).signature_match)

    def test_every_binding_field_pinned(self):
        fields={'project_id':'other','effect_id':'other','invocation_pin':'0'*64,'route_pin':'0'*64,
                'profile_pin':'0'*64,'reservation_id':'other','invocation_idempotency_key':'other',
                'owner_snapshot_pin':'0'*64,'reservation_pin':'0'*64,'membership_pin':'0'*64,
                'transaction_ref':'other','currency':'EUR','run':replace(self.run,attempt=1),
                'lease':replace(self.lease,lease_version=2),'effect':replace(self.e,tool_id='other')}
        for k,v in fields.items():
            with self.subTest(k=k):self.assertFalse(self.review(p=replace(self.p,**{k:v})).signature_match)

    def test_run_level_missing_membership_not_receipt(self):
        self.assertFalse(self.review(p=replace(self.p,membership_pin=None)).signature_match)

    def test_scope_crosswalk(self):
        for k in ('tenant','company','environment','project','task','run','effect'):
            q=replace(self.req,scope=replace(self.req.scope,**{k:'wrong'}))
            self.assertEqual(self.review(expected_consume=q).reason,'CONSUME_EFFECT_BINDING_HOLD')

    def test_consumed_request_fields(self):
        for k,v in {'binding_sha':'0'*64,'request_sha':'0'*64,'transaction_ref':'other'}.items():
            self.assertEqual(self.review(expected_consume=replace(self.req,**{k:v})).reason,'CONSUME_EFFECT_BINDING_HOLD')

    def test_nonce_substitution(self):
        self.assertFalse(self.review(expected_consume=replace(self.req,nonce='0'*64)).signature_match)

    def test_expired_consume(self):
        self.assertFalse(self.review(clock=replace(self.clock,now_tick=120,max_heartbeat_age=40),witness_max_age=40).signature_match)

    def test_old_head(self):
        self.assertFalse(self.review(current_head=Head(2,'5'*64,4)).signature_match)

    def test_witness_epoch(self):
        self.assertEqual(self.review(current_head=Head(2,'5'*64,5)).reason,'CONSUME_WITNESS_EPOCH_HOLD')
        self.assertEqual(self.review(clock=replace(self.clock,witness_epoch=5)).reason,'ERR_WA_EPOCH_STALE')

    def test_policy_epoch(self):
        self.assertEqual(self.review(clock=replace(self.clock,policy_epoch=4)).reason,'ERR_POLICY_EPOCH_STALE')

    def test_revoked_grant(self):
        g=replace(self.grant,revoked=True)
        self.assertEqual(self.review(grant=g,grant_reference=g).reason,'GRANT_REVOKED')

    def test_missing_and_different_grant(self):
        self.assertEqual(self.review(grant=None).reason,'GRANT_REFERENCE_MISSING')
        self.assertEqual(self.review(grant_reference=replace(self.grant,expires_tick=179)).reason,'GRANT_REFERENCE_MISMATCH')

    def test_expired_grant(self):
        g=replace(self.grant,expires_tick=100)
        self.assertEqual(self.review(grant=g,grant_reference=g).reason,'GRANT_EXPIRED')

    def test_wrong_tool_grant(self):
        g=replace(self.grant,allowed_tools=('different',))
        self.assertEqual(self.review(grant=g,grant_reference=g).reason,'EFFECT_OUTSIDE_GRANT')

    def test_runtime_drift(self):
        for arg,v in [('current_run',replace(self.run,attempt=1)),('current_lease',replace(self.lease,fence=2))]:
            self.assertEqual(self.review(**{arg:v}).reason,'RUNTIME_REFERENCE_DRIFT_HOLD')

    def test_bool_attempt_not_integer(self):
        self.assertEqual(self.review(current_run=replace(self.run,attempt=False)).reason,'RUNTIME_REFERENCE_DRIFT_HOLD')

    def test_stale_witness(self):
        w=replace(self.w,observed_tick=1)
        self.assertEqual(self.review(witness=w,witness_reference=w).reason,'WA_OBSERVATION_NOT_FRESH')

    def test_unknown_never_retries_or_settles(self):
        self.assertEqual(self.review(outcome_unknown=True).reason,'UNKNOWN_RECONCILIATION_REQUIRED_HOLD')
        self.assertEqual(self.review(outcome_unknown=1).reason,'OUTCOME_SHAPE_HOLD')

    def test_existing_fence_denies_second_consume(self):
        with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED_HOLD'):
            issue_fixture(self.store,self.key,self.req,100)
        self.assertTrue(self.review().signature_match)

    def test_stable_reservation_key_across_effect_and_attempt(self):
        other=replace(self.p,run=replace(self.run,attempt=1),effect_id='other',transaction_ref='other',
                      invocation_idempotency_key='other',invocation_pin='0'*64,effect=replace(self.e,effect_digest='0'*64))
        self.assertEqual(replay_keys(self.p)[0],replay_keys(other)[0])
        self.assertEqual(inspect_replay(other,(self.p,)).reason,'REPLAY_IDENTITY_MATCH_HOLD')

    def test_idempotency_and_invocation_aliases(self):
        other=replace(self.p,reservation_id='other',effect_id='other',transaction_ref='other')
        self.assertEqual(inspect_replay(other,(self.p,)).reason,'REPLAY_IDENTITY_MATCH_HOLD')
        other=replace(other,invocation_idempotency_key='other')
        self.assertEqual(inspect_replay(other,(self.p,)).reason,'REPLAY_IDENTITY_MATCH_HOLD')

    def test_no_history_never_allows(self):
        r=inspect_replay(self.p,())
        self.assertEqual(r.reason,'REPLAY_ABSENCE_UNPROVEN_HOLD');self.assertFalse(r.retry_allowed)
        self.assertEqual(inspect_replay(self.p,[]).reason,'REPLAY_HISTORY_SHAPE_HOLD')

    def test_distinct_history_is_not_freshness(self):
        other=replace(self.p,reservation_id='other',invocation_idempotency_key='other',invocation_pin='0'*64,
                      effect=replace(self.e,effect_digest='0'*64))
        self.assertEqual(inspect_replay(self.p,(other,)).reason,'REPLAY_ABSENCE_UNPROVEN_HOLD')

    def test_legacy_fence_scope_alias_gap_stays_hold(self):
        # Existing fence scopes and binding/tx can all differ; do NOT claim it enforces reservation uniqueness.
        other=replace(self.p,effect_id='other',transaction_ref='other',route_pin='0'*64)
        req=replace(self.req,scope=consume_scope(other),binding_sha=receipt_effect_digest(other),transaction_ref='other')
        obs=issue_fixture(self.store,self.key,req,100)
        r=self.review(p=other,reference=other,expected_binding_pin=req.binding_sha,expected_consume=req,observation=obs)
        self.assertTrue(r.signature_match)
        self.assertEqual(inspect_replay(other,(self.p,)).reason,'REPLAY_IDENTITY_MATCH_HOLD')


if __name__=='__main__':
    unittest.main(verbosity=2)
