"""D0 actual 0211 wrapper + original 0210 fixture. Local custody is not independent."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from threading import Barrier, Event
from unittest import TestCase, skipUnless
from unittest.mock import patch
import os
import sqlite3

from app.core.transaction.intent_authority import D0IntentAuthority, RootPin, execute_authority_fenced_transition
from app.core.transaction.fenced_transition import D0IntentJournal
from app.core.transaction.postgres_session import CommitOutcomeUnknown
from app.engines.memory_engine.snapshot_store import publish_snapshot
import test_fenced_transition_0210 as original
import test_witnessed_sql_0209 as sql


class AuthorityWrapperP10H(TestCase):
    def setUp(self):
        self.f = original.FencedTransitionTests(); self.f.setUp(); self.addCleanup(self.f.doCleanups)
        w = self.f.w
        self.root = RootPin(w.latest.record_sha, w.latest.key_sha, w.latest.recovery_epoch)
        self.next = replace(self.root, record_sha='f'*64, recovery_epoch=self.root.recovery_epoch+1)
        self.authority = D0IntentAuthority.create(w.path.with_name('root.authority.sqlite'), self.root)

    def execute(self, **changes):
        w, f = self.f.w, self.f.w.b.f
        args = dict(authority=self.authority, intent=self.f.i, context=w.j.context, registry=w.b.registry,
                    witness=w.latest, expected_binding=self.f.binding, memory_path=w.b.store.path,
                    reader=w.reader, public_key=w.pub, raw=w.j.raw, journal=self.f.journal,
                    connect=lambda: sql.Connection(self.f.f.path), clock=lambda: f.clock)
        args.update(changes)
        return execute_authority_fenced_transition(**args)

    def claims(self):
        with closing(sqlite3.connect(self.authority.path)) as db:
            return db.execute('SELECT scope_sha,binding,tx,request_digest FROM claims').fetchall()

    def assert_historical(self, result):
        self.assertEqual(result.status, 'HISTORICAL'); self.assertTrue(result.historical_match)
        self.f.f.exact_readback(); self.f.review('HISTORICAL')
        self.assertFalse(result.independent_verified or result.provider_call_allowed or result.retry_allowed)

    def test_exact_wrapper_commit_and_readback(self):
        self.assert_historical(self.execute())
        pin = self.f.pin
        self.assertEqual(self.claims(), [(pin.scope_sha, pin.binding, pin.transaction_ref, pin.request_digest)])

    def test_authority_claim_precedes_journal_and_t1(self):
        outer = self
        real = D0IntentJournal.stage
        def stage(journal, intent, binding):
            outer.assertEqual(len(outer.claims()), 1)
            outer.f.review('HOLD')
            return real(journal, intent, binding)
        def connect():
            self.f.review('PENDING'); self.assertEqual(len(self.claims()), 1)
            return sql.Connection(self.f.f.path)
        with patch.object(D0IntentJournal, 'stage', stage):
            self.assert_historical(self.execute(connect=connect))

    def test_old_root_before_wrapper_no_stage(self):
        self.authority.publish(self.root, self.next)
        with self.assertRaisesRegex(ValueError, 'ROOT_HOLD'): self.execute()
        self.assertEqual(self.claims(), []); self.f.review('HOLD')
        self.assertEqual(self.f.f.dump(), self.f.f.initial)

    def test_bad_binding_never_claims(self):
        with self.assertRaisesRegex(ValueError, 'BINDING_HOLD'): self.execute(expected_binding='0'*64)
        self.assertEqual(self.claims(), []); self.f.review('HOLD')

    def test_memory_revoked_claim_quarantines(self):
        b = self.f.w.b
        publish_snapshot(b.store.path, b.store.revoke(), b.pin)
        with self.assertRaisesRegex(ValueError, 'CAS_HOLD'): self.execute()
        self.assertEqual(len(self.claims()), 1); self.f.review('UNKNOWN')
        self.assertEqual(self.f.f.dump(), self.f.f.initial)
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'): self.execute()

    def test_unknown_commit_cannot_retry(self):
        with self.assertRaises(CommitOutcomeUnknown): self.execute(connect=lambda: sql.Connection(self.f.f.path, unknown=True))
        self.f.f.exact_readback(); self.f.review('UNKNOWN')
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'): self.execute()

    def test_journal_outcome_failure_keeps_claim_and_pending(self):
        with patch.object(D0IntentJournal, '_record', side_effect=OSError('synthetic journal outage')):
            with self.assertRaises(OSError): self.execute()
        self.f.f.exact_readback(); self.f.review('PENDING')
        self.assertEqual(len(self.claims()), 1)
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'): self.execute()

    def test_concurrent_wrappers_one_commit(self):
        barrier = Barrier(2, timeout=3)
        def attempt():
            barrier.wait()
            try: return self.execute().status
            except ValueError as e: return str(e)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(attempt) for _ in range(2)]
            self.assertCountEqual([j.result(timeout=5) for j in jobs], ['HISTORICAL','D0_AUTHORITY_ALREADY_CLAIMED_HOLD'])
        self.f.f.exact_readback(); self.assertEqual(len(self.claims()), 1)

    def test_cooperating_root_publisher_waits_through_commit(self):
        started, finished = Event(), Event()
        def publish():
            started.set(); self.authority.publish(self.root, self.next); finished.set()
        with ThreadPoolExecutor(max_workers=1) as pool:
            jobs = []
            def during_commit():
                jobs.append(pool.submit(publish)); self.assertTrue(started.wait(1)); self.assertFalse(finished.wait(.15))
            self.assert_historical(self.execute(connect=lambda: sql.Connection(self.f.f.path, before_commit=during_commit)))
            jobs[0].result(timeout=5)
        self.assertTrue(finished.is_set())

    def test_product_and_journal_restore_blocked_by_retained_authority(self):
        paths = (self.f.f.path, self.f.journal.path)
        before = [p.read_bytes() for p in paths]
        self.assert_historical(self.execute())
        for p, data in zip(paths, before): p.write_bytes(data)
        self.f.review('HOLD'); self.assertEqual(self.f.f.dump(), self.f.f.initial)
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'): self.execute()
        self.assertEqual(self.f.f.dump(), self.f.f.initial)

    def test_residual_all_three_stores_restored(self):
        # Negative D-04: authority custody itself remains an external prerequisite.
        paths = (self.f.f.path, self.f.journal.path, self.authority.path)
        before = [p.read_bytes() for p in paths]
        first = self.execute(); self.assert_historical(first)
        for p, data in zip(paths, before): p.write_bytes(data)
        self.assertEqual(self.claims(), []); self.f.review('HOLD')
        second = self.execute(); self.assert_historical(second); self.assertEqual(first, second)

    @skipUnless(os.name == 'posix', 'POSIX disposable path boundary only')
    def test_residual_authority_path_replaced_during_wrapper_commit(self):
        # Negative D-03: local file lock cannot establish separate administrative custody.
        replacement = D0IntentAuthority.create(self.authority.path.with_name('replacement.authority.sqlite'), self.next)
        def during_commit(): os.replace(replacement.path, self.authority.path)
        self.assert_historical(self.execute(connect=lambda: sql.Connection(self.f.f.path, before_commit=during_commit)))
        self.assertEqual(self.claims(), [])
        with closing(sqlite3.connect(self.authority.path)) as db:
            self.assertEqual(db.execute('SELECT record_sha,epoch FROM roots').fetchall(), [(self.next.record_sha,self.next.recovery_epoch)])
