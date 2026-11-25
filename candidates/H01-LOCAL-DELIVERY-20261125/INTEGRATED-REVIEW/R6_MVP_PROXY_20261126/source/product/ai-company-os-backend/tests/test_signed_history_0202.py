"""Real Ed25519 fixture signatures, real local archive; snapshot dependency mocked."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.core.event_store.retained_history import ReferenceStore, ReferenceReader, history_reference, RetainedReview
from app.core.event_store.signed_history import (Checkpoint, ExternalPin, TerminalClaim, checkpoint_bytes,
    terminal_bytes, verify_checkpoint, review_signed_snapshot)


class SignatureTests(TestCase):
    def setUp(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.store=ReferenceStore(Path(tmp.name)/'pins.db')
        self.reader=ReferenceReader(self.store.path)
        self.plan={'id':'p'};self.rev='sha256:'+'1'*64
        self.h=self.store.put(history_reference(self.plan,self.rev,()))
        self.key=Ed25519PrivateKey.generate();self.pub=self.key.public_key().public_bytes_raw()
        self.claim=TerminalClaim('demo-run','a'*64,'d0-tx-'+'2'*64,'D0_LOCAL_FAILURE_NO_EFFECT')
        self.c=Checkpoint('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',self.rev,self.h,
                          'demo-iv','iv-key',1,2,3,4,10,20,(self.claim,))
        self.pin=self.anchor(self.c)

    def anchor(self,c):
        return ExternalPin(sha256(checkpoint_bytes(c)).hexdigest(),sha256(self.pub).hexdigest(),
            c.issuer,c.key_id,c.key_revision,c.policy_epoch,c.witness_epoch,c.sequence,c.plan_revision,False,('demo-worker',))

    def sig(self,c): return self.key.sign(checkpoint_bytes(c))
    def terminals(self,c): return tuple((t.run_id,self.key.sign(terminal_bytes(c,t))) for t in c.terminal_claims)
    def verify(self,c=None,pin=None,pub=None,sig=None,ts=None,now=15):
        c=self.c if c is None else c
        return verify_checkpoint(c,self.pin if pin is None else pin,self.pub if pub is None else pub,
            self.sig(c) if sig is None else sig,self.terminals(c) if ts is None else ts,now)
    def hold(self,r):
        self.assertEqual(r.decision,'HOLD');self.assertFalse(r.signature_match or r.independent_verified or r.dispatch_allowed or r.release_ready or r.replay_allowed);self.assertIsNone(r.history)

    def test_valid_signatures_not_authority(self):
        r=self.verify();self.assertTrue(r.signature_match);self.assertEqual(r.decision,'HOLD')
        self.assertFalse(r.independent_verified or r.dispatch_allowed or r.release_ready or r.replay_allowed)
    def test_tampered_checkpoint(self): self.hold(self.verify(c=replace(self.c,history_sha='b'*64)))
    def test_signature_tamper(self): self.hold(self.verify(sig=b'x'*64))
    def test_key_substitution(self): self.hold(self.verify(pub=Ed25519PrivateKey.generate().public_key().public_bytes_raw()))
    def test_revoked(self): self.hold(self.verify(pin=replace(self.pin,revoked=True)))
    def test_unknown_revocation(self): self.hold(self.verify(pin=replace(self.pin,revoked=None)))
    def test_expired_and_future(self):
        for now in (9,20,21,True): self.hold(self.verify(now=now))
    def test_restore_old_checkpoint(self):
        for pin in (replace(self.pin,sequence=5),replace(self.pin,witness_epoch=4),replace(self.pin,policy_epoch=3)):
            self.hold(self.verify(pin=pin))
    def test_other_plan(self): self.hold(self.verify(pin=replace(self.pin,plan_revision='sha256:'+'2'*64)))
    def test_actor_separation(self): self.hold(self.verify(pin=replace(self.pin,excluded_principals=('demo-iv',))))
    def test_missing_terminal(self): self.hold(self.verify(ts=()))
    def test_bad_terminal_signature(self): self.hold(self.verify(ts=(('demo-run',b'x'*64),)))
    def test_terminal_domain_separation(self): self.hold(self.verify(ts=(('demo-run',self.sig(self.c)),)))
    def test_terminal_cross_checkpoint(self):
        old=self.terminals(self.c);c=replace(self.c,sequence=5)
        self.hold(self.verify(c=c,pin=self.anchor(c),ts=old))
    def test_reject_success_claim(self):
        c=replace(self.c,terminal_claims=(replace(self.claim,outcome='SUCCEEDED'),))
        self.hold(verify_checkpoint(c,self.pin,self.pub,b'x'*64,(),15))
    def test_duplicate_claim(self):
        c=replace(self.c,terminal_claims=(self.claim,self.claim))
        self.hold(verify_checkpoint(c,self.pin,self.pub,b'x'*64,(),15))
    def test_bad_transaction_format(self):
        c=replace(self.c,terminal_claims=(replace(self.claim,transaction_ref='arbitrary'),))
        self.hold(verify_checkpoint(c,self.pin,self.pub,b'x'*64,(),15))
    def test_no_terminal_claims(self):
        c=replace(self.c,terminal_claims=());self.assertTrue(self.verify(c=c,pin=self.anchor(c)).signature_match)
    def test_missing_backend_fails_closed(self):
        with patch.dict('sys.modules',{'cryptography.hazmat.primitives.asymmetric.ed25519':None}): self.hold(self.verify())

    def snapshot(self,**kw):
        args=dict(store=self.reader,connect=None,plan=self.plan,revision=self.rev,pins=(),checkpoint=self.c,
                  external_pin=self.pin,public_key=self.pub,signature=self.sig(self.c),terminal_signatures=self.terminals(self.c),now=15)
        args.update(kw);return review_signed_snapshot(**args)
    def test_signed_readback_binding(self):
        def reader(store,connect,plan,rev,pins,expected,**kw):
            self.assertEqual(store.read(expected),history_reference(plan,rev,pins));self.assertEqual(kw['terminal_refs'],(('demo-run','a'*64),))
            return RetainedReview('D0',SimpleNamespace(event_count=1),(('demo-run','a'*64,'d0-tx-'+'2'*64),),True)
        with patch('app.core.event_store.signed_history.review_retained_snapshot',side_effect=reader):
            r=self.snapshot();self.assertTrue(r.signature_match);self.assertEqual(r.history.event_count,1);self.assertFalse(r.independent_verified)
    def test_bad_signature_no_readback(self):
        with patch('app.core.event_store.signed_history.review_retained_snapshot') as p:
            self.hold(self.snapshot(signature=b'x'*64));p.assert_not_called()
    def test_tx_mismatch(self):
        with patch('app.core.event_store.signed_history.review_retained_snapshot',return_value=RetainedReview('D0',object(),(('demo-run','a'*64,'d0-tx-'+'3'*64),),True)):
            self.hold(self.snapshot())
    def test_missing_archive_no_projection(self):
        with patch('app.core.event_store.signed_history.review_retained_snapshot',return_value=RetainedReview('D0_HOLD')):
            self.hold(self.snapshot())
    def test_actual_principal_not_excluded(self):
        p=SimpleNamespace(initial=SimpleNamespace(scope=SimpleNamespace(principal_id='demo-other')))
        with patch('app.core.event_store.signed_history.review_retained_snapshot') as reader:
            self.hold(self.snapshot(pins=(p,)));reader.assert_not_called()
    def test_wrong_revision_no_readback(self):
        with patch('app.core.event_store.signed_history.review_retained_snapshot') as p:
            self.hold(self.snapshot(revision='sha256:'+'0'*64));p.assert_not_called()


if __name__=='__main__': main()
