"""Actual isolated SQLite IAM/authority component integration; no T1 writer."""
import secrets
import sqlite3
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from app.core.iam_session import D0_SCOPE, D0SessionResolver, SessionRecord, SessionClaimCheck, credential_digest
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin


class DurableTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'd0.authority.sqlite'
        self.root = RootPin('a'*64,'b'*64,1)
        self.now = 100
        self.clock = lambda: self.now
        self.secret = secrets.token_urlsafe(32)
        self.other = secrets.token_urlsafe(32)
        self.human = secrets.token_urlsafe(32)
        self.records = (
            SessionRecord('demo-session',credential_digest(self.secret),'demo-principal','AGENT',D0_SCOPE,'demo-agent',100,200),
            SessionRecord('demo-other',credential_digest(self.other),'demo-principal','AGENT',D0_SCOPE,'demo-other-agent',100,200),
            SessionRecord('demo-human',credential_digest(self.human),'demo-principal','HUMAN',D0_SCOPE,None,100,200))
        self.r = D0SessionResolver.bootstrap_durable(self.path,self.root,self.records,domain='demo-clock',clock=self.clock)
        self.a = self.r._authority
        self.pin = self.r.durable_pin

    def reopen(self,pin=None,domain='demo-clock'):
        return D0SessionResolver.open_durable(D0IntentAuthority(self.path),self.root,expected_pin=pin or self.r.durable_pin,domain=domain,clock=self.clock)

    def read(self,secret=None):
        return self.r.resolve(secret or self.secret,expected_scope=D0_SCOPE)

    def check(self,secret=None,obs=None,agent='demo-agent'):
        return SessionClaimCheck(self.r,secret or self.secret,obs or self.read(),D0_SCOPE,'demo-principal',agent)

    def claim(self,check=None):
        return self.a.claim_and_fence(self.root,'1'*64,'2'*64,'demo-tx','3'*64,session_check=check)

    def count(self,table):
        with closing(self.a._db()) as db:
            return db.execute('SELECT count(*) FROM '+table).fetchone()[0]

    def test_reopen_preserves_exact_session_and_revocation(self):
        before=self.read()
        self.assertEqual(self.reopen().resolve(self.secret,expected_scope=D0_SCOPE),before)
        self.assertTrue(self.r.revoke_local('demo-session',expected_revision=1))
        fresh=self.reopen()
        self.assertIsNone(fresh.resolve(self.secret,expected_scope=D0_SCOPE))
        self.assertEqual(fresh.resolve(self.other,expected_scope=D0_SCOPE).revision,2)
        with self.assertRaisesRegex(ValueError,'IAM_PIN_HOLD'):
            self.reopen(self.pin)

    def test_stale_resolver_and_cas(self):
        stale=self.reopen()
        self.assertTrue(self.r.revoke_local('demo-session',expected_revision=1))
        self.assertIsNone(stale.resolve(self.other,expected_scope=D0_SCOPE))
        self.assertFalse(stale.revoke_local('demo-other',expected_revision=1))
        self.assertFalse(self.r.revoke_local('demo-other',expected_revision=1))
        self.assertTrue(self.r.revoke_local('demo-other',expected_revision=2))

    def test_exclusive_bootstrap_and_domain(self):
        with self.assertRaises(FileExistsError):
            D0SessionResolver.bootstrap_durable(self.path,self.root,self.records,domain='demo-clock',clock=self.clock)
        with self.assertRaisesRegex(ValueError,'IAM_DOMAIN_HOLD'):
            self.reopen(domain='demo-new-clock')

    def test_clock_rollback_survives_reopen(self):
        self.now=150
        self.assertIsNotNone(self.read())
        self.now=149
        self.assertIsNone(self.read())
        self.now=151
        with self.assertRaisesRegex(ValueError,'IAM_CLOCK_HOLD'):
            self.reopen()

    def test_expiry(self):
        self.now=200
        self.assertIsNone(self.read())
        self.assertIsNone(self.reopen().resolve(self.secret,expected_scope=D0_SCOPE))

    def test_forged_credential_and_scope(self):
        self.assertIsNone(self.read(secrets.token_urlsafe(32)))
        self.assertIsNone(self.r.resolve(self.secret,expected_scope=('other',*D0_SCOPE[1:])))

    def test_legacy_claim_and_root_publish_blocked_on_iam_store(self):
        with self.assertRaisesRegex(ValueError,'D0_IAM_CHECK_REQUIRED_HOLD'):
            with self.claim(): self.fail('legacy bypass')
        self.assertEqual(self.count('claims'),0)
        with self.assertRaisesRegex(ValueError,'D0_JOINT_PUBLICATION_HOLD'):
            self.a.publish(self.root,RootPin('c'*64,'b'*64,1))

    def test_exact_claim_pin_and_duplicate(self):
        check=self.check()
        with self.claim(check):
            self.assertFalse(check.observation.grant_allowed)
        self.assertEqual(self.count('claims'),1)
        self.assertEqual(self.count('iam_claim_pins'),1)
        with self.assertRaisesRegex(ValueError,'ALREADY_CLAIMED'):
            with self.claim(check): self.fail('duplicate')

    def test_other_session_substitution(self):
        check=self.check(self.other,obs=self.read())
        with self.assertRaisesRegex(ValueError,'IAM_CLAIM_HOLD'):
            with self.claim(check): self.fail('different session')
        self.assertEqual(self.count('claims'),0)

    def test_human_to_agent_rejected(self):
        check=self.check(self.human,obs=self.read(self.human))
        with self.assertRaisesRegex(ValueError,'IAM_CLAIM_HOLD'):
            with self.claim(check): self.fail('human')

    def test_agent_mismatch_rejected(self):
        check=self.check(agent='demo-other-agent')
        with self.assertRaisesRegex(ValueError,'IAM_CLAIM_HOLD'):
            with self.claim(check): self.fail('wrong agent')

    def test_revoked_observation_rejected_before_claim(self):
        check=self.check()
        self.assertTrue(self.r.revoke_local('demo-session',expected_revision=1))
        with self.assertRaisesRegex(ValueError,'IAM_CLAIM_HOLD'):
            with self.claim(check): self.fail('revoked')
        self.assertEqual(self.count('claims'),0)

    def test_revoke_serializes_behind_original_fence(self):
        result=[]; started=threading.Event(); done=threading.Event()
        other=self.reopen()
        def revoke():
            started.set()
            result.append(other.revoke_local('demo-session',expected_revision=1))
            done.set()
        t=threading.Thread(target=revoke)
        with self.claim(self.check()):
            t.start(); self.assertTrue(started.wait(1))
            self.assertFalse(done.wait(.15))
        t.join(3)
        self.assertEqual(result,[True]); self.assertIsNone(self.read())
        self.assertEqual(self.count('claims'),1)

    def test_revoke_in_claim_fence_gap_consumes_claim(self):
        check=self.check(); publisher=self.reopen(); original=self.a._db
        class GapConnection:
            def __init__(self): self.db=original(); self.begins=0
            def __getattr__(self,name): return getattr(self.db,name)
            def execute(self,sql,*args):
                if sql=='BEGIN IMMEDIATE':
                    self.begins+=1
                    if self.begins==2:
                        if not publisher.revoke_local('demo-session',expected_revision=1):
                            raise AssertionError('publisher did not commit')
                return self.db.execute(sql,*args)
        with patch.object(self.a,'_db',GapConnection):
            with self.assertRaisesRegex(ValueError,'IAM_CLAIM_HOLD'):
                with self.claim(check): self.fail('stale after claim')
        self.assertEqual(self.count('claims'),1)
        self.assertEqual(self.count('iam_claim_pins'),1)
        self.assertIsNone(self.read())

    def test_expiry_in_claim_fence_gap_consumes_claim(self):
        check=self.check(); original=self.a._db; owner=self
        class GapConnection:
            def __init__(self): self.db=original(); self.begins=0
            def __getattr__(self,name): return getattr(self.db,name)
            def execute(self,sql,*args):
                if sql=='BEGIN IMMEDIATE':
                    self.begins+=1
                    if self.begins==2: owner.now=200
                return self.db.execute(sql,*args)
        with patch.object(self.a,'_db',GapConnection):
            with self.assertRaisesRegex(ValueError,'IAM_CLAIM_HOLD'):
                with self.claim(check): self.fail('expired after claim')
        self.assertEqual(self.count('claims'),1)
        self.assertEqual(self.count('iam_claim_pins'),1)

    def test_restore_old_db_rejected_with_retained_new_pin(self):
        backup=self.path.with_suffix('.old')
        with closing(self.a._db()) as src, closing(sqlite3.connect(backup)) as dst: src.backup(dst)
        self.assertTrue(self.r.revoke_local('demo-session',expected_revision=1))
        latest=self.r.durable_pin
        with closing(sqlite3.connect(backup)) as src, closing(self.a._db()) as dst: src.backup(dst)
        with self.assertRaisesRegex(ValueError,'IAM_PIN_HOLD'):
            self.reopen(latest)
        # Deliberate residual: restoring both DB and retained pin is NOT protected.
        self.assertIsNotNone(self.reopen(self.pin).resolve(self.secret,expected_scope=D0_SCOPE))

    def test_history_tamper_and_replace_rejected(self):
        self.assertTrue(self.r.revoke_local('demo-session',expected_revision=1))
        with closing(self.a._db()) as db:
            for sql in ("DELETE FROM iam_revocations", "UPDATE iam_sessions SET principal='demo-other'", "INSERT OR REPLACE INTO iam_revocations VALUES (3,'demo-session')"):
                with self.assertRaises(sqlite3.IntegrityError): db.execute(sql)

    def test_interrupted_bootstrap_cannot_be_used_as_legacy(self):
        partial=self.path.with_name('partial.authority.sqlite')
        def broken_clock(): raise RuntimeError('injected bootstrap interruption')
        with self.assertRaisesRegex(RuntimeError,'bootstrap interruption'):
            D0SessionResolver.bootstrap_durable(partial,self.root,self.records,domain='demo-clock',clock=broken_clock)
        a=D0IntentAuthority(partial)
        with self.assertRaisesRegex(ValueError,'D0_IAM_CHECK_REQUIRED_HOLD'):
            with a.claim_and_fence(self.root,'1'*64,'2'*64,'demo-partial','3'*64): self.fail('partial bypass')
        with self.assertRaisesRegex(ValueError,'D0_JOINT_PUBLICATION_HOLD'):
            a.publish(self.root,RootPin('c'*64,'b'*64,1))
        with self.assertRaises(FileExistsError):
            D0SessionResolver.bootstrap_durable(partial,self.root,self.records,domain='demo-clock',clock=self.clock)

    def test_legacy_store_original_claim_unchanged(self):
        legacy=D0IntentAuthority.create(self.path.with_name('legacy.authority.sqlite'),self.root)
        with legacy.claim_and_fence(self.root,'1'*64,'2'*64,'demo-legacy','3'*64): pass
        with self.assertRaisesRegex(ValueError,'ALREADY_CLAIMED'):
            with legacy.claim_and_fence(self.root,'1'*64,'2'*64,'demo-legacy','3'*64): self.fail('repeat')

if __name__=='__main__': unittest.main()
