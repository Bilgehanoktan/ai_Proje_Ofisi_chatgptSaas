"""Full 0209/0210/0211 witness + journal + authority + ORIGINAL SQL T1.
Requires full pinned repository; NOT executable in 0212 55-file source slice.
No independent custody or real effect grant. Run in isolated disposable DEV only.
"""
import secrets
from app.core.iam_session import (
    D0_SCOPE, D0SessionResolver, SessionRecord, SessionClaimCheck, credential_digest,
)
from contextlib import closing
from dataclasses import replace
import sqlite3
from threading import Event
from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin, execute_authority_fenced_transition
from app.core.transaction.fenced_transition import D0IntentJournal
from app.core.transaction.postgres_session import CommitOutcomeUnknown
from app.engines.memory_engine.snapshot_store import publish_snapshot
import test_fenced_transition_0210 as old
import test_witnessed_sql_0209 as sql


class AuthorityWrappedSqlTests(TestCase):
    def setUp(self):
        old.FencedTransitionTests.setUp(self)
        root=RootPin(self.w.latest.record_sha,self.w.latest.key_sha,self.w.latest.recovery_epoch)
        self.root=root
        self.authority=D0IntentAuthority.create(self.w.path.with_name('run.authority.sqlite'),root)

    def invoke(self, **changes):
        w=self.w
        args=dict(authority=self.authority,intent=self.i,context=w.j.context,
            registry=w.b.registry,witness=w.latest,expected_binding=self.binding,
            memory_path=w.b.store.path,reader=w.reader,public_key=w.pub,raw=w.j.raw,
            journal=self.journal,connect=lambda:sql.Connection(self.f.path),clock=lambda:w.b.f.clock)
        args.update(changes)
        return execute_authority_fenced_transition(**args)

    def _claims(self):
        with closing(sqlite3.connect(self.authority.path)) as db:
            return db.execute('SELECT count(*) FROM claims').fetchone()[0]

    def _enable_d0_iam(self):
        """Existing D0 session/authority source, never a live grant or real issuer."""
        scope = self.i.scope
        self.iam_now = 100
        self.iam_secret = secrets.token_urlsafe(32)
        self.iam_session_id = 'demo-bridge-session'
        record = SessionRecord(
            self.iam_session_id, credential_digest(self.iam_secret),
            scope.principal_id, 'AGENT', D0_SCOPE, scope.agent_instance_id,
            80, 200,
        )
        self.iam_resolver = D0SessionResolver.bootstrap_durable(
            self.w.path.with_name('run-iam.authority.sqlite'), self.root, (record,),
            domain='demo-bridge-clock', clock=lambda: self.iam_now,
        )
        self.authority = self.iam_resolver._authority
        observed = self.iam_resolver.resolve(self.iam_secret, expected_scope=D0_SCOPE)
        self.assertIsNotNone(observed)
        return SessionClaimCheck(
            self.iam_resolver, self.iam_secret, observed, D0_SCOPE,
            scope.principal_id, scope.agent_instance_id,
        )

    def test_iam_wrapper_missing_check_fails_before_t1(self):
        self._enable_d0_iam()
        with self.assertRaisesRegex(ValueError, 'D0_IAM_CHECK_REQUIRED_HOLD'):
            self.invoke()
        self.assertEqual(self._claims(), 0)
        self.assertEqual(self.f.dump(), self.f.initial)

    def test_iam_wrapper_explicit_scoped_check_historical_only(self):
        check = self._enable_d0_iam()
        result = self.invoke(session_check=check)
        self.assertTrue(result.historical_match)
        self.assertFalse(result.independent_verified or result.dispatch_allowed or result.retry_allowed)
        self.f.exact_readback()
        self.assertEqual(self._claims(), 1)
        with closing(sqlite3.connect(self.authority.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM iam_claim_pins').fetchone(), (1,))

    def test_iam_wrapper_wrong_principal_and_agent_denied(self):
        check = self._enable_d0_iam()
        for changed in (dict(principal='demo-forged'), dict(agent='demo-forged')):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError, 'D0_AUTHORITY_SESSION_SCOPE_HOLD'):
                    self.invoke(session_check=replace(check, **changed))
                self.assertEqual(self._claims(), 0)
                self.assertEqual(self.f.dump(), self.f.initial)

    def test_iam_wrapper_revoked_session_no_claim(self):
        check = self._enable_d0_iam()
        self.assertTrue(self.iam_resolver.revoke_local(self.iam_session_id, expected_revision=1))
        with self.assertRaisesRegex(ValueError, 'IAM_CLAIM_HOLD'):
            self.invoke(session_check=check)
        self.assertEqual(self._claims(), 0)
        self.assertEqual(self.f.dump(), self.f.initial)

    def test_iam_wrapper_expired_session_no_claim(self):
        check = self._enable_d0_iam()
        self.iam_now = 200
        with self.assertRaisesRegex(ValueError, 'IAM_CLAIM_HOLD'):
            self.invoke(session_check=check)
        self.assertEqual(self._claims(), 0)
        self.assertEqual(self.f.dump(), self.f.initial)

    def test_legacy_authority_rejects_iam_check(self):
        check = self._enable_d0_iam()
        self.authority = D0IntentAuthority(self.w.path.with_name('run.authority.sqlite'))
        with self.assertRaisesRegex(ValueError, 'D0_IAM_MODE_HOLD'):
            self.invoke(session_check=check)
        self.assertEqual(self._claims(), 0)
        self.assertEqual(self.f.dump(), self.f.initial)

    def test_original_t1_and_all_three_guards(self):
        result=self.invoke()
        self.assertTrue(result.historical_match)
        self.f.exact_readback()
        self.assertEqual(self._claims(),1)
        self.assertEqual(D0IntentJournal(self.journal.path).inspect(self.i,self.pin).status,'HISTORICAL')
        self.assertFalse(result.independent_verified or result.dispatch_allowed or result.retry_allowed)

    def test_restore_t1_and_journal_without_authority_blocks_replay(self):
        before_t1=self.f.path.read_bytes();before_j=self.journal.path.read_bytes()
        self.invoke();self.f.exact_readback()
        self.f.path.write_bytes(before_t1);self.journal.path.write_bytes(before_j)
        self.assertEqual(self.f.dump(),self.f.initial)
        self.authority=D0IntentAuthority(self.authority.path)
        with self.assertRaisesRegex(ValueError,'ALREADY_CLAIMED'):
            self.invoke()
        self.assertEqual(self.f.dump(),self.f.initial)

    def test_unknown_commit_stays_quarantined(self):
        with self.assertRaises(CommitOutcomeUnknown):
            self.invoke(connect=lambda:sql.Connection(self.f.path,unknown=True))
        self.f.exact_readback()
        self.assertEqual(self._claims(),1)
        self.assertEqual(D0IntentJournal(self.journal.path).inspect(self.i,self.pin).status,'UNKNOWN')
        with self.assertRaisesRegex(ValueError,'ALREADY_CLAIMED'):
            self.invoke()

    def test_revocation_before_attempt_denies_without_claim(self):
        self.authority.publish(self.root,replace(self.root,record_sha='f'*64,recovery_epoch=self.root.recovery_epoch+1))
        with self.assertRaisesRegex(ValueError,'ROOT_HOLD'):
            self.invoke()
        self.assertEqual(self._claims(),0)
        self.assertEqual(self.f.dump(),self.f.initial)

    def test_root_publisher_waits_through_original_commit(self):
        started=Event();done=Event();futures=[];self_outer=self
        def publish():
            started.set()
            self_outer.authority.publish(self_outer.root,replace(self_outer.root,record_sha='f'*64,recovery_epoch=self_outer.root.recovery_epoch+1))
            done.set()
        with ThreadPoolExecutor(max_workers=1) as pool:
            def precommit():
                futures.append(pool.submit(publish))
                self.assertTrue(started.wait(1))
                self.assertFalse(done.wait(.15))
            self.invoke(connect=lambda:sql.Connection(self.f.path,before_commit=precommit))
            futures[0].result(timeout=5)
        self.f.exact_readback();self.assertTrue(done.is_set())

    def test_full_authority_store_restore_is_still_unsafe_residual(self):
        # Reproduction, not a passing security property; independent monotonic root required.
        authority_before=self.authority.path.read_bytes()
        t1_before=self.f.path.read_bytes();journal_before=self.journal.path.read_bytes()
        self.invoke();self.f.exact_readback()
        self.authority.path.write_bytes(authority_before)
        self.f.path.write_bytes(t1_before);self.journal.path.write_bytes(journal_before)
        # This is deliberately expected to succeed: known D-04 unresolved failure.
        self.assertTrue(self.invoke().historical_match)
        self.assertEqual(self._claims(),1)
