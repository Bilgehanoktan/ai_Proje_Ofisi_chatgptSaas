"""Signed synthetic observation against real disposable original Authority DB."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase,main
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.core.transaction.intent_authority import RootPin,D0IntentAuthority
from app.core.transaction.external_claim_review import ClaimObservation,ExternalClaimObservation,observation_bytes,review_external_claim

class ExternalClaimTests(TestCase):
    def setUp(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/'claim.authority.sqlite'
        self.key=Ed25519PrivateKey.generate();self.pub=self.key.public_key().public_bytes_raw()
        self.root=RootPin('a'*64,'b'*64,1)
        self.authority=D0IntentAuthority.create(self.path,self.root)
        self.claim=ClaimObservation('c'*64,'d'*64,'tx-demo','e'*64,1,self.root.record_sha)
        self.obs=ExternalClaimObservation('f'*64,self.root,1,self.claim.scope_sha,10,20,None)
        self.pre=self.path.read_bytes()
    def consume(self):
        c=self.claim
        with self.authority.claim_and_fence(self.root,c.scope_sha,c.binding,c.tx,c.request_digest):pass
    def review(self,o=None,**changes):
        o=o or self.obs
        args=dict(expected_key_sha=sha256(self.pub).hexdigest(),expected_challenge=self.obs.challenge,
            expected_root=self.root,expected_root_seq=1,scope_sha=self.claim.scope_sha,now_tick=15)
        pub=changes.pop('public_key',self.pub);sig=changes.pop('signature',self.key.sign(observation_bytes(o)))
        args.update(changes)
        r=review_external_claim(self.path,o,sig,pub,**args)
        self.assertEqual(r.decision,'HOLD');self.assertFalse(r.independent_verified or r.retry_allowed or r.dispatch_allowed or r.release_allowed)
        return r
    def test_unclaimed_matching_never_grants(self):
        r=self.review();self.assertTrue(r.signature_match and r.local_match);self.assertIs(r.external_consumed,False);self.assertEqual(self.path.read_bytes(),self.pre)
    def test_consumed_matching_no_replay(self):
        self.consume();r=self.review(replace(self.obs,claim=self.claim));self.assertTrue(r.local_match and r.external_consumed);self.assertEqual(r.reason,'EXTERNAL_CONSUMED_HOLD')
    def test_actual_authority_restore_detected(self):
        self.consume();o=replace(self.obs,claim=self.claim);self.path.write_bytes(self.pre)
        r=self.review(o);self.assertTrue(r.signature_match and r.external_consumed);self.assertFalse(r.local_match);self.assertEqual(r.reason,'LOCAL_DIVERGENCE_HOLD');self.assertEqual(self.path.read_bytes(),self.pre)
    def test_external_absent_local_consumed_divergence(self):
        self.consume();r=self.review();self.assertFalse(r.local_match);self.assertEqual(r.reason,'LOCAL_DIVERGENCE_HOLD')
    def test_binding_drift(self):
        self.consume();r=self.review(replace(self.obs,claim=replace(self.claim,binding='0'*64)));self.assertFalse(r.local_match)
    def test_wrong_key_rejected(self):
        r=self.review(public_key=Ed25519PrivateKey.generate().public_key().public_bytes_raw());self.assertFalse(r.signature_match)
    def test_signature_rejected(self):self.assertFalse(self.review(signature=b'x'*64).signature_match)
    def test_stale_challenge_rejected(self):self.assertFalse(self.review(expected_challenge='0'*64).signature_match)
    def test_wrong_scope_rejected(self):self.assertFalse(self.review(scope_sha='0'*64).signature_match)
    def test_expiry_and_future_rejected(self):
        for n in (9,20):self.assertFalse(self.review(now_tick=n).signature_match)
    def test_wrong_head_and_epoch_rejected(self):
        self.assertFalse(self.review(expected_root_seq=2).signature_match)
        self.assertFalse(self.review(expected_root=replace(self.root,recovery_epoch=2)).signature_match)
    def test_missing_local_file_not_recreated(self):
        self.path.unlink();r=self.review();self.assertEqual(r.reason,'LOCAL_READ_HOLD');self.assertFalse(self.path.exists())
    def test_root_advanced_local_only(self):
        self.authority.publish(self.root,replace(self.root,record_sha='0'*64,recovery_epoch=2));r=self.review();self.assertFalse(r.local_match)
    def test_claim_prior_root_remains_consumed(self):
        self.consume();new=replace(self.root,record_sha='0'*64,recovery_epoch=2);self.authority.publish(self.root,new)
        r=self.review(replace(self.obs,root=new,root_seq=2,claim=self.claim),expected_root=new,expected_root_seq=2);self.assertTrue(r.local_match and r.external_consumed)
    def test_bad_observation_shape(self):
        with self.assertRaises(ValueError):observation_bytes(replace(self.obs,expires_tick=100))

if __name__=='__main__':main()
