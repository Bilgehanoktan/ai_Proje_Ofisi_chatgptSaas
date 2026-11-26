"""Original candidate T1 on SQLite with actual persistent fence and quarantine."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from threading import Event, Barrier
import sqlite3
from unittest import TestCase
from unittest.mock import patch

from app.core.transaction.fenced_transition import (
    D0IntentJournal, execute_fenced_transition, intent_pin, local_revocation_fence,
)
from app.core.transaction.postgres_session import CommitOutcomeUnknown
from app.engines.memory_engine.snapshot_store import publish_snapshot
import test_witnessed_sql_0209 as fixture


class FencedTransitionTests(TestCase):
    def setUp(self):
        self.f = fixture.WitnessedSqlTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.w = self.f.w
        self.i = self.f.i
        self.binding = self.f.f.binding
        self.journal = D0IntentJournal.create(self.w.path.with_name('run.intent.sqlite'))
        self.pin = intent_pin(self.i, self.binding)

    def execute(self, **changes):
        w, f = self.w, self.w.b.f
        args = dict(intent=self.i, context=w.j.context, registry=w.b.registry,
            witness=w.latest, expected_binding=self.binding, memory_path=w.b.store.path,
            reader=w.reader, public_key=w.pub, raw=w.j.raw, journal=self.journal,
            connect=lambda: fixture.Connection(self.f.path), clock=lambda: f.clock,
            latest=lambda: w.latest)
        args.update(changes)
        return execute_fenced_transition(**args)

    def review(self, status):
        r = D0IntentJournal(self.journal.path).inspect(self.i, self.pin)
        self.assertEqual(r.status, status)
        self.assertEqual(r.decision, 'HOLD')
        for flag in ('dispatch_allowed','release_allowed','retry_allowed','provider_call_allowed',
                     'spend_allowed','independent_verified'):
            self.assertIs(getattr(r, flag), False)
        return r

    def test_original_commit_historical_only(self):
        self.assertTrue(self.execute().historical_match)
        self.f.exact_readback()
        self.review('HISTORICAL')

    def test_pending_is_durable_before_t1_connect(self):
        def connect():
            self.review('PENDING')
            return fixture.Connection(self.f.path)
        self.execute(connect=connect)
        self.review('HISTORICAL')

    def test_crash_after_stage_no_retry(self):
        self.journal.stage(self.i, self.binding)
        self.review('PENDING')
        with self.assertRaisesRegex(ValueError, 'ALREADY_STAGED'):
            self.execute()
        self.assertEqual(self.f.dump(), self.f.initial)

    def test_unknown_commit_persists_no_retry(self):
        with self.assertRaises(CommitOutcomeUnknown):
            self.execute(connect=lambda: fixture.Connection(self.f.path, unknown=True))
        self.f.exact_readback()
        self.review('UNKNOWN')
        before = self.f.dump()
        with self.assertRaisesRegex(ValueError, 'ALREADY_STAGED'):
            self.execute()
        self.assertEqual(self.f.dump(), before)

    def test_precommit_error_quarantines_even_absence(self):
        with self.assertRaisesRegex(ValueError, 'LATEST_HOLD'):
            self.execute(latest=lambda: replace(self.w.latest, record_sha='0'*64))
        self.review('UNKNOWN')
        self.assertEqual(self.f.dump(), self.f.initial)
        with self.assertRaisesRegex(ValueError, 'ALREADY_STAGED'):
            self.execute()

    def test_commit_then_journal_failure_leaves_pending(self):
        with patch.object(D0IntentJournal, '_record', side_effect=OSError('journal unavailable')):
            with self.assertRaises(OSError):
                self.execute()
        self.f.exact_readback()
        self.review('PENDING')
        with self.assertRaisesRegex(ValueError, 'ALREADY_STAGED'):
            self.execute()

    def test_witness_and_memory_writers_wait_until_commit(self):
        w = self.w
        started = [Event(), Event()]
        finished = [Event(), Event()]
        def witness_write():
            started[0].set()
            try:
                return w.append(w.next(recovery_epoch=2), w.latest.record_sha)
            finally:
                finished[0].set()
        def memory_write():
            started[1].set()
            try:
                return publish_snapshot(w.b.store.path, w.b.store.revoke(), w.b.pin)
            finally:
                finished[1].set()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = []
            def interleave():
                futures.extend([pool.submit(witness_write), pool.submit(memory_write)])
                for e in started:
                    self.assertTrue(e.wait(1))
                for e in finished:
                    self.assertFalse(e.wait(.1))
                self.review('PENDING')
            self.execute(connect=lambda: fixture.Connection(self.f.path, before_commit=interleave))
            for job in futures:
                job.result(timeout=5)
        self.f.exact_readback()
        self.review('HISTORICAL')
        self.assertFalse(w.review().structural_match)

    def test_witness_before_fence_rejected(self):
        w = self.w
        w.append(w.next(recovery_epoch=2), w.latest.record_sha)
        with self.assertRaisesRegex(ValueError, 'WITNESS'):
            self.execute()
        self.review('UNKNOWN')
        self.assertEqual(self.f.dump(), self.f.initial)

    def test_memory_before_fence_rejected(self):
        w = self.w
        publish_snapshot(w.b.store.path, w.b.store.revoke(), w.b.pin)
        with self.assertRaisesRegex(ValueError, 'CAS_HOLD'):
            self.execute()
        self.review('UNKNOWN')
        self.assertEqual(self.f.dump(), self.f.initial)

    def test_concurrent_same_intent_one_commit(self):
        barrier = Barrier(2, timeout=3)
        def compete():
            barrier.wait()
            try:
                return self.execute().status
            except ValueError as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(compete) for _ in range(2)]
            self.assertCountEqual([j.result(timeout=5) for j in jobs], ['HISTORICAL','D0_INTENT_ALREADY_STAGED_HOLD'])
        self.f.exact_readback()

    def test_different_intent_same_scope_quarantined(self):
        self.journal.stage(self.i, self.binding)
        with self.assertRaisesRegex(ValueError, 'ALREADY_STAGED'):
            self.journal.stage(replace(self.i, effect_key='different'), 'd'*64)
        self.review('PENDING')

    def test_append_only_and_no_replace(self):
        self.execute()
        with closing(sqlite3.connect(self.journal.path)) as db, db:
            for sql in ('DELETE FROM intents','DELETE FROM outcomes', 'UPDATE intents SET version=99',
                        "UPDATE outcomes SET status='UNKNOWN'", 'INSERT OR REPLACE INTO intents SELECT * FROM intents',
                        'INSERT OR REPLACE INTO outcomes SELECT * FROM outcomes'):
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute(sql)
        self.review('HISTORICAL')

    def test_alias_rejected(self):
        w = self.w
        alias = w.path.with_name('alias.intent.sqlite')
        alias.hardlink_to(w.path)
        with self.assertRaisesRegex(ValueError, 'SEPARATION'):
            with local_revocation_fence(w.b.store.path, w.reader, D0IntentJournal(alias)):
                self.fail('alias accepted')

    def test_invalid_binding_no_stage(self):
        with self.assertRaisesRegex(ValueError, 'BINDING'):
            self.execute(expected_binding='0'*64)
        self.review('HOLD')
        self.assertEqual(self.f.dump(), self.f.initial)

    def test_external_latest_change_after_last_check_still_unlocked(self):
        # The local fence serializes the two DB writers, not an independent trust root.
        w = self.w
        latest = [w.latest]
        def interleave():
            latest[0] = replace(w.latest, record_sha='f'*64)
        r = self.execute(latest=lambda: latest[0], connect=lambda: fixture.Connection(self.f.path, before_commit=interleave))
        self.assertTrue(r.historical_match)
        self.f.exact_readback()
        self.assertFalse(w.review(expected_witness=latest[0]).structural_match)
        self.review('HISTORICAL')

    def test_joint_journal_and_t1_restore_still_requires_external_intent_head(self):
        # The witness has not changed during an ordinary transition. Restoring both
        # journal and T1 to their pre-attempt images removes local replay evidence.
        journal_before = self.journal.path.read_bytes()
        t1_before = self.f.path.read_bytes()
        self.assertTrue(self.execute().historical_match)
        self.f.exact_readback()
        self.journal.path.write_bytes(journal_before)
        self.f.path.write_bytes(t1_before)
        self.assertEqual(self.f.dump(), self.f.initial)
        self.review('HOLD')
        self.assertTrue(self.execute().historical_match)
        self.review('HISTORICAL')
        self.f.exact_readback()
