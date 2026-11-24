import concurrent.futures
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.core.transaction.effect_fence_reference import D0EffectFenceReference, Head
from app.core.transaction.signed_consume_reference import Scope, ConsumeRequest, SignedObservation, issue_fixture, review_observation


class SignedTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.head = Head(1, 'a'*64, 1)
        self.path = Path(tmp.name)/'test.effect-reference.sqlite'
        self.store = D0EffectFenceReference.create(self.path, self.head)
        self.key = Ed25519PrivateKey.generate()
        self.pub = self.key.public_key().public_bytes_raw()
        self.pin = sha256(self.pub).hexdigest()
        self.req = ConsumeRequest(Scope('tenant','company','D0','p1','task','run','effect'), self.head, 'b'*64, 'c'*64, 'tx1', 'd'*64, 10, 20)

    def issue(self, req=None):
        return issue_fixture(self.store,self.key,req or self.req,11)

    def review(self, obs, **kw):
        opts=dict(expected=self.req,public_key=self.pub,expected_key_sha=self.pin,current_head=self.head,now_tick=11)
        opts.update(kw)
        return review_observation(obs,**opts)

    def test_signed_receipt_only_hold(self):
        r=self.review(self.issue())
        self.assertTrue(r.signature_match)
        self.assertEqual(r.decision,'HOLD')
        self.assertFalse(r.dispatch_allowed or r.retry_allowed or r.independent_verified)

    def test_nonce_mismatch(self):
        self.assertFalse(self.review(self.issue(),expected=replace(self.req,nonce='e'*64)).signature_match)

    def test_scope_mismatch(self):
        obs=self.issue()
        for name in ('tenant','company','environment','project','task','run','effect'):
            req=replace(self.req,scope=replace(self.req.scope,**{name:'other'}))
            self.assertFalse(self.review(obs,expected=req).signature_match)

    def test_binding_and_request_mismatch(self):
        obs=self.issue()
        for req in (replace(self.req,binding_sha='e'*64),replace(self.req,request_sha='e'*64),replace(self.req,transaction_ref='tx2')):
            self.assertFalse(self.review(obs,expected=req).signature_match)

    def test_stale_head(self):
        obs=self.issue()
        new=Head(2,'f'*64,2)
        self.store.advance(self.head,new)
        self.assertFalse(self.review(obs,current_head=new).signature_match)

    def test_time_bounds(self):
        obs=self.issue()
        for now in (9,20,True):
            self.assertFalse(self.review(obs,now_tick=now).signature_match)

    def test_wrong_key(self):
        self.assertFalse(self.review(self.issue(),public_key=Ed25519PrivateKey.generate().public_key().public_bytes_raw()).signature_match)

    def test_tampered_signature(self):
        obs=self.issue()
        sig=bytes([obs.signature[0]^1])+obs.signature[1:]
        self.assertFalse(self.review(SignedObservation(self.req,sig)).signature_match)

    def test_forged_request(self):
        obs=self.issue()
        req=replace(self.req,nonce='e'*64)
        self.assertFalse(self.review(SignedObservation(req,obs.signature),expected=req).signature_match)

    def test_duplicate_after_reopen(self):
        self.issue()
        self.store=D0EffectFenceReference(self.path)
        with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED'):
            self.issue(replace(self.req,nonce='e'*64))

    def test_invalid_window_not_consumed(self):
        with self.assertRaises(ValueError): self.issue(replace(self.req,expires_tick=100))
        self.assertTrue(self.review(self.issue()).signature_match)

    def test_parallel_projects_persist(self):
        req2=replace(self.req,scope=replace(self.req.scope,project='p2'),binding_sha='e'*64,transaction_ref='tx2')
        with concurrent.futures.ThreadPoolExecutor(2) as ex:
            results=list(ex.map(self.issue,[self.req,req2]))
        self.assertTrue(self.review(results[0]).signature_match)
        self.assertTrue(self.review(results[1],expected=req2).signature_match)
        self.store=D0EffectFenceReference(self.path)
        for req in (self.req,req2):
            with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED'): self.issue(req)

    def test_missing_receipt_after_consume(self):
        self.store.consume_synthetic(self.head,self.req.intent())
        self.assertFalse(self.review(None).dispatch_allowed)
        with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED'): self.issue()

    def test_malformed_shape(self):
        self.assertFalse(self.review({'signature':'fake'}).signature_match)
        with self.assertRaises(ValueError): self.issue(replace(self.req,scope=replace(self.req.scope,tenant='')))
