"""D0 direct claim/fence + original ordinary T1 SQL integration on SQLite.
Not the 0211 witness/journal wrapper, independent custody or a PG test.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import asdict, replace
from hashlib import sha256
import json
import sqlite3
from threading import Event, Barrier
from unittest import TestCase
import test_transition_mapping_0194 as original
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin
from app.core.transaction.postgres_transition_mapping import transaction_ref
from app.core.transaction.postgres_session import CommitOutcomeUnknown, postgres_transaction
from app.core.transaction.port import LogicalT1Coordinator


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('ascii')).hexdigest()


class IntentAuthorityT1Tests(TestCase):
    def setUp(self):
        self.f = original.MappingTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.root = RootPin('a'*64, 'b'*64, 1)
        self.next = RootPin('c'*64, 'b'*64, 2)
        self.authority = D0IntentAuthority.create(self.f.path.with_name('root.authority.sqlite'), self.root)
        self.i = original.INTENT
        self.scope_sha = _hash(asdict(self.i.scope))
        self.binding = _hash(asdict(self.i))
        self.tx = transaction_ref(self.i)

    def run_t1(self, *, root=None, unknown=False, clock=lambda: original.CLOCK, connect=None):
        with self.authority.claim_and_fence(root or self.root, self.scope_sha, self.binding, self.tx, self.i.request_digest):
            if connect is None:
                return self.f.commit(unknown=unknown, clock=clock)
            mapping = original.D0PostgresTransitionMapping(original.LEASE, clock)
            c = LogicalT1Coordinator(lambda: postgres_transaction(connect, mapping))
            return original.commit_transition(c, original.BEFORE, original.TARGET, self.i)

    def claims(self):
        with closing(sqlite3.connect(self.authority.path)) as db:
            return db.execute('SELECT scope_sha,binding,tx,request_digest FROM claims').fetchall()

    def test_actual_commit_and_readback(self):
        receipt = self.run_t1()
        self.assertEqual(receipt.transaction_ref, self.tx)
        self.assertEqual(self.f.rows(), (('RUNNING',5,1),(1,1,1,1,1)))
        self.assertEqual(self.claims(), [(self.scope_sha,self.binding,self.tx,self.i.request_digest)])
        self.assertTrue(self.f.reconcile().exact_sample_match)
        self.assertFalse(self.f.reconcile().retry_allowed)

    def test_product_database_restore_no_replay(self):
        before = self.f.path.read_bytes()
        self.run_t1()
        self.f.path.write_bytes(before)
        self.f.assert_empty()
        self.authority = D0IntentAuthority(self.authority.path)
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'):
            self.run_t1()
        self.f.assert_empty()

    def test_unknown_commit_quarantined(self):
        with self.assertRaises(CommitOutcomeUnknown):
            self.run_t1(unknown=True)
        self.assertTrue(self.f.reconcile().exact_sample_match)
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'):
            self.run_t1()
        self.assertEqual(len(self.claims()), 1)

    def test_rollback_does_not_enable_retry(self):
        with self.assertRaisesRegex(ValueError, 'LEASE_EXPIRED'):
            self.run_t1(clock=lambda:replace(original.CLOCK,now_tick=20))
        self.f.assert_empty()
        self.assertFalse(self.f.reconcile().exact_sample_match)
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'):
            self.run_t1()

    def test_root_publisher_waits_through_actual_commit(self):
        started, finished = Event(), Event()
        def publish():
            started.set()
            self.authority.publish(self.root, self.next)
            finished.set()
        outer = self
        with ThreadPoolExecutor(max_workers=1) as pool:
            jobs = []
            class Connection(original.SQLiteConnectionShim):
                def commit(self):
                    jobs.append(pool.submit(publish))
                    outer.assertTrue(started.wait(1))
                    outer.assertFalse(finished.wait(.15))
                    super().commit()
                    outer.assertFalse(finished.is_set())
            self.run_t1(connect=lambda:Connection(self.f.path))
            jobs[0].result(timeout=4)
        self.assertTrue(finished.is_set())
        self.assertTrue(self.f.reconcile().exact_sample_match)

    def test_revocation_first_no_t1(self):
        self.authority.publish(self.root, self.next)
        with self.assertRaisesRegex(ValueError, 'ROOT_HOLD'):
            self.run_t1()
        self.assertEqual(self.claims(), [])
        self.f.assert_empty()

    def test_two_claimants_only_one_commit(self):
        barrier = Barrier(2, timeout=3)
        def attempt():
            barrier.wait()
            try:
                self.run_t1()
                return 'COMMIT'
            except ValueError as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(attempt) for _ in range(2)]
            self.assertCountEqual([j.result(timeout=5) for j in jobs], ['COMMIT','D0_AUTHORITY_ALREADY_CLAIMED_HOLD'])
        self.assertEqual(self.f.rows(), (('RUNNING',5,1),(1,1,1,1,1)))
