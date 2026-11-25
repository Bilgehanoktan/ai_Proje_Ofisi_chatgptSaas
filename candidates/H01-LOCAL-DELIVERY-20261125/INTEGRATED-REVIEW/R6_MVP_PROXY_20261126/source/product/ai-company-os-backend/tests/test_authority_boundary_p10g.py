"""D0 trust-boundary diagnostics; negative cases are not security acceptance."""
from contextlib import closing
from dataclasses import asdict
from hashlib import sha256
import json
import os
import sqlite3
from unittest import TestCase, skipUnless
import test_transition_mapping_0194 as original
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction
from app.core.transaction.postgres_transition_mapping import transaction_ref


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode('ascii')).hexdigest()


class AuthorityBoundaryP10G(TestCase):
    def setUp(self):
        self.f = original.MappingTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.root = RootPin('a'*64, 'b'*64, 1)
        self.new = RootPin('c'*64, 'b'*64, 2)
        self.authority = D0IntentAuthority.create(self.f.path.with_name('root.authority.sqlite'), self.root)
        self.i = original.INTENT

    def execute(self, connect=None):
        with self.authority.claim_and_fence(self.root, digest(asdict(self.i.scope)), digest(asdict(self.i)),
                                            transaction_ref(self.i), self.i.request_digest):
            if connect is None:
                return self.f.commit()
            mapping = original.D0PostgresTransitionMapping(original.LEASE, lambda: original.CLOCK)
            c = LogicalT1Coordinator(lambda: postgres_transaction(connect, mapping))
            return original.commit_transition(c, original.BEFORE, original.TARGET, self.i)

    def test_missing_authority_does_not_initialize_or_commit(self):
        self.authority.path.unlink()
        with self.assertRaises(sqlite3.OperationalError):
            self.execute()
        self.f.assert_empty()
        self.assertFalse(self.authority.path.exists())

    def test_revoked_root_blocks_before_t1(self):
        self.authority.publish(self.root, self.new)
        with self.assertRaisesRegex(ValueError, 'ROOT_HOLD'):
            self.execute()
        self.f.assert_empty()

    @skipUnless(os.name == 'posix', 'POSIX replacement diagnostic only')
    def test_residual_root_path_replacement_while_fenced(self):
        # Negative D-03 trust-boundary case. Two separate disposable inodes.
        replacement = D0IntentAuthority.create(self.authority.path.with_name('replacement.authority.sqlite'), self.new)
        outer = self
        class ReplaceDuringCommit(original.SQLiteConnectionShim):
            def commit(self):
                os.replace(replacement.path, outer.authority.path)
                super().commit()
        receipt = self.execute(lambda: ReplaceDuringCommit(self.f.path))
        self.assertEqual(receipt.transaction_ref, transaction_ref(self.i))
        self.assertTrue(self.f.reconcile().exact_sample_match)
        with closing(sqlite3.connect(self.authority.path)) as db:
            self.assertEqual(db.execute('SELECT record_sha,epoch FROM roots').fetchall(), [(self.new.record_sha, 2)])
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone(), (0,))
        # Local SQLite lock does not establish independent root/path custody.
