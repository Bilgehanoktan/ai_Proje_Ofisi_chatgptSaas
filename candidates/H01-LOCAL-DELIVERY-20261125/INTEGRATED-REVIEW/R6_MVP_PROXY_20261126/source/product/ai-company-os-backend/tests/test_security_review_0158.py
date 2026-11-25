"""Synthetic oracle candidates; NOT_RUN. No network, writes, real grants or receipt signing."""
import unittest
from dataclasses import replace
from app.core.runtime_preview import Scope, LeaseObservation, ClockSample
from app.core.witness_review import WitnessSample, RestoreObservation, inspect_witness, inspect_restore
from app.core.policy_gateway_review import EffectScope, GrantSample, inspect_gateway, DisabledToolGateway
from app.core.iv_review import TrustPlane, ArtifactPin, IVObservation, inspect_iv
from app.core.skill_review import SkillManifestSample, inspect_skill


class SecurityReviewTests(unittest.TestCase):
    def setUp(self):
        self.s = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,
                       'research','demo-run','demo-agent','demo-principal')
        self.l = LeaseObservation(self.s,'lease','grant',1,1,4,2,3,60,40)
        self.c = ClockSample(50,2,3,20)
        self.w = WitnessSample(self.s,'wa-root',3,8,'b'*64,45)
        self.e = EffectScope(self.s,'READ','tool','c'*64,'grant','admission','lease','budget',2,3,4)
        self.g = GrantSample(self.s,'grant','admission','lease','budget',('READ',),('tool',),'c'*64,2,3,4,55,False)
        self.pin = ArtifactPin(self.s,'d'*64,4,2,3)
        self.qa = TrustPlane('qa-p','qa-root','qa-admin','qa-recovery')
        self.iv = TrustPlane('iv-p','iv-root','iv-admin','iv-recovery')
        self.rel = TrustPlane('rel-p','rel-root','rel-admin','rel-recovery')
        self.o = IVObservation(self.pin,self.pin,self.qa,self.iv,self.rel,'receipt-demo')
        self.m = SkillManifestSample(self.s,'skill','v1','a'*64,'b'*64,'c'*64,('tool',),'g7','g8')

    def gateway(self,e=None,g=None,w=None,c=None):
        return inspect_gateway(e or self.e,g or self.g,g or self.g,self.l,self.l,c or self.c,w or self.w,w or self.w,10)

    def test_matching_gateway_still_deny(self):
        r=self.gateway();self.assertTrue(r.structural_match);self.assertEqual(r.decision,'DENY');self.assertFalse(r.dispatch_allowed);self.assertFalse(r.provider_called)
        self.assertFalse(DisabledToolGateway().dispatch(self.e).dispatch_allowed)

    def test_revoked_and_expired_grant(self):
        self.assertEqual(self.gateway(g=replace(self.g,revoked=True)).reason,'GRANT_REVOKED')
        self.assertEqual(self.gateway(g=replace(self.g,expires_tick=50)).reason,'GRANT_EXPIRED')

    def test_wrong_effect_and_scope(self):
        self.assertEqual(self.gateway(e=replace(self.e,tool_id='other')).reason,'EFFECT_OUTSIDE_GRANT')
        self.assertEqual(self.gateway(e=replace(self.e,effect_digest='d'*64)).reason,'GRANT_EFFECT_BINDING_MISMATCH')
        self.assertEqual(self.gateway(e=replace(self.e,scope=replace(self.s,company_id='other'))).reason,'EFFECT_SCOPE_INVALID')

    def test_reference_mismatch(self):
        r=inspect_gateway(self.e,self.g,replace(self.g,expires_tick=54),self.l,self.l,self.c,self.w,self.w,10)
        self.assertEqual(r.reason,'GRANT_REFERENCE_MISMATCH')

    def test_lease_epoch(self):
        self.assertEqual(self.gateway(c=replace(self.c,witness_epoch=4)).reason,'ERR_WA_EPOCH_STALE')

    def test_witness_epoch_and_freshness(self):
        self.assertEqual(self.gateway(w=replace(self.w,epoch=2)).reason,'ERR_WA_EPOCH_STALE')
        self.assertEqual(self.gateway(w=replace(self.w,observed_tick=30)).reason,'WA_OBSERVATION_NOT_FRESH')
        self.assertFalse(inspect_witness(self.w,self.w,self.s,3,50,10).authoritative)

    def test_restore_monotonic_and_unknown(self):
        r=RestoreObservation(self.s,'restore','backup',replace(self.w,epoch=2,sequence=7),self.w,('effect',))
        result=inspect_restore(r,self.w,50,10);self.assertEqual(result.reason,'UNKNOWN_RECONCILIATION_REQUIRED');self.assertFalse(result.replay_allowed)
        self.assertEqual(inspect_restore(replace(r,old_witness=self.w),self.w,50,10).reason,'RESTORE_MONOTONIC_FENCE_REQUIRED')
        self.assertFalse(inspect_restore(replace(r,unknown_effect_keys=()),self.w,50,10).reopened)

    def test_iv_shape_never_accepts(self):
        r=inspect_iv(self.o,self.pin);self.assertTrue(r.structural_match);self.assertFalse(r.independent_proven);self.assertFalse(r.release_ready)
        self.assertEqual(inspect_iv(replace(self.o,iv=replace(self.iv,admin_id=self.qa.root_id)),self.pin).reason,'IV_TRUST_PLANE_COLLISION')
        self.assertEqual(inspect_iv(self.o,replace(self.pin,revision=5)).reason,'IV_ARTIFACT_READBACK_CAS_MISMATCH')

    def test_skill_refs_not_authority(self):
        r=inspect_skill(self.m,self.m,self.s);self.assertTrue(r.structural_match);self.assertFalse(r.enabled);self.assertFalse(r.grant_created)
        m=replace(self.m,enabled=True);self.assertEqual(inspect_skill(m,m,self.s).reason,'SKILL_ENABLE_PROHIBITED')
        self.assertEqual(inspect_skill(self.m,replace(self.m,manifest_digest='e'*64),self.s).reason,'SKILL_PIN_SCOPE_MISMATCH')
