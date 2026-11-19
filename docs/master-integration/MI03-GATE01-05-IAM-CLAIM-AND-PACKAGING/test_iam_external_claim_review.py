"""Supplemental synthetic IAM/0215 readback; no protected execution or real issuer."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
import secrets
import sqlite3
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.core.iam_session import D0_SCOPE, D0SessionResolver, SessionRecord, SessionClaimCheck, credential_digest
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin
from app.core.transaction.external_claim_review import ClaimObservation, ExternalClaimObservation, observation_bytes, review_external_claim


class IAMExternalClaimTests(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / 'synthetic.authority.sqlite'
        self.tick = 100
        self.credential = secrets.token_urlsafe(32)
        self.key = Ed25519PrivateKey.generate()
        self.pub = self.key.public_key().public_bytes_raw()
        self.root = RootPin('a'*64, sha256(self.pub).hexdigest(), 1)
        record = SessionRecord('demo-session', credential_digest(self.credential), 'demo-principal', 'AGENT', D0_SCOPE, 'demo-agent', 100, 200)
        self.resolver = D0SessionResolver.bootstrap_durable(self.path, self.root, (record,), domain='demo-clock', clock=lambda: self.tick)
        self.authority = self.resolver._authority
        self.observation = self.resolver.resolve(self.credential, expected_scope=D0_SCOPE)
        self.check = SessionClaimCheck(self.resolver, self.credential, self.observation, D0_SCOPE, 'demo-principal', 'demo-agent')
        self.claim = ClaimObservation('c'*64, 'd'*64, 'demo-tx', 'e'*64, 1, self.root.record_sha)
        self.external = ExternalClaimObservation('f'*64, self.root, 1, self.claim.scope_sha, 100, 120, None)

    def rows(self):
        with closing(sqlite3.connect(self.path.as_uri()+'?mode=ro', uri=True)) as db:
            return tuple(db.execute('SELECT * FROM '+t+' ORDER BY 1').fetchall() for t in ('roots','claims','iam_claim_pins','iam_revocations'))

    def claim_once(self, check):
        c = self.claim
        with self.authority.claim_and_fence(self.root, c.scope_sha, c.binding, c.tx, c.request_digest, session_check=check):
            pass

    def review(self, claim):
        before = self.path.read_bytes()
        o = replace(self.external, claim=claim)
        r = review_external_claim(self.path, o, self.key.sign(observation_bytes(o)), self.pub,
             expected_key_sha=sha256(self.pub).hexdigest(), expected_challenge=o.challenge,
             expected_root=self.root, expected_root_seq=1, scope_sha=o.scope_sha, now_tick=110)
        self.assertEqual(r.decision, 'HOLD')
        self.assertFalse(r.independent_verified or r.dispatch_allowed or r.release_allowed or r.retry_allowed)
        self.assertEqual(before, self.path.read_bytes())
        return r

    def test_unclaimed_iam_readback_never_grants(self):
        r = self.review(None)
        self.assertTrue(r.signature_match and r.local_match)
        self.assertFalse(r.external_consumed)
        self.assertEqual(self.rows()[1:3], ([], []))

    def test_bound_iam_claim_is_readable_without_new_write(self):
        self.claim_once(self.check)
        roots, claims, pins, revocations = self.rows()
        self.assertEqual(len(claims), 1)
        self.assertEqual(len(pins), 1)
        self.assertEqual(pins[0][0], self.claim.scope_sha)
        self.assertEqual(len(pins[0][1]), 64)
        r = self.review(self.claim)
        self.assertTrue(r.local_match and r.external_consumed)
        self.assertEqual(r.reason, 'EXTERNAL_CONSUMED_HOLD')

    def test_revocation_preserves_consumed_claim_and_no_replay(self):
        self.claim_once(self.check)
        before = self.rows()
        self.assertTrue(self.resolver.revoke_local('demo-session', expected_revision=1))
        self.assertIsNone(self.resolver.resolve(self.credential, expected_scope=D0_SCOPE))
        after = self.rows()
        self.assertEqual(before[:3], after[:3])
        self.assertEqual(len(after[3]), 1)
        self.assertTrue(self.review(self.claim).local_match)
        with self.assertRaises(ValueError):
            self.claim_once(self.check)
        self.assertEqual(after, self.rows())

    def test_revoked_observation_cannot_consume_new_claim(self):
        self.assertTrue(self.resolver.revoke_local('demo-session', expected_revision=1))
        before = self.rows()
        with self.assertRaisesRegex(ValueError, 'IAM_CLAIM_HOLD'):
            self.claim_once(self.check)
        self.assertEqual(self.rows(), before)
        self.assertTrue(self.review(None).local_match)

    def test_external_retained_consumed_observation_detects_restore(self):
        old = self.path.read_bytes()
        self.claim_once(self.check)
        self.path.write_bytes(old)  # disposable fixture; no real restore operation
        r = self.review(self.claim)
        self.assertTrue(r.signature_match and r.external_consumed)
        self.assertFalse(r.local_match)
        self.assertEqual(r.reason, 'LOCAL_DIVERGENCE_HOLD')
        self.assertEqual(self.rows()[1:3], ([], []))

    def test_iam_root_publication_remains_hold(self):
        before = self.rows()
        with self.assertRaisesRegex(ValueError, 'D0_JOINT_PUBLICATION_HOLD'):
            self.authority.publish(self.root, replace(self.root, record_sha='0'*64))
        self.assertEqual(self.rows(), before)
        self.assertTrue(self.review(None).local_match)
