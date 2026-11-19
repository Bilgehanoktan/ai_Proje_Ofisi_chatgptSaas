"""Pending exact 0214 fixture integration; requires full original dependency closure."""
from contextlib import closing
from hashlib import sha256
import sqlite3
from unittest import TestCase
from unittest.mock import Mock

from app.core.transaction.intent_authority import execute_protected_authority_fenced_transition
import test_authority_fullchain_0214 as original


class ProtectedFullChainTests(TestCase):
    def setUp(self):
        self.f = original.FullChainTests()
        self.addCleanup(self.f.doCleanups)
        self.f.setUp()

    def snapshot(self):
        f = self.f
        with closing(sqlite3.connect(f.journal.path.as_uri()+'?mode=ro', uri=True)) as db:
            journal = (db.execute('SELECT * FROM intents ORDER BY binding').fetchall(),
                       db.execute('SELECT * FROM outcomes ORDER BY binding').fetchall())
        with closing(sqlite3.connect(f.authority.path.as_uri()+'?mode=ro', uri=True)) as db:
            authority = (db.execute('SELECT * FROM roots ORDER BY seq').fetchall(),
                         db.execute('SELECT * FROM claims ORDER BY scope_sha').fetchall())
        digests = tuple(sha256(p.read_bytes()).hexdigest() for p in
                        (f.f.path, f.journal.path, f.authority.path, f.memory, f.store.path))
        return f.f.rows(), journal, authority, digests

    def assert_protected_hold(self):
        f = self.f
        connect = Mock(side_effect=AssertionError('must not connect'))
        clock = Mock(side_effect=AssertionError('must not read clock'))
        before = self.snapshot()
        with self.assertRaisesRegex(PermissionError, 'T1_STRICT_COMMIT_EXPIRY_UNPROVEN_HOLD'):
            execute_protected_authority_fenced_transition(authority=f.authority, intent=f.i,
                context=f.context, registry=f.registry, witness=f.witness,
                expected_binding=f.binding, memory_path=f.memory, reader=f.reader,
                public_key=f.pub, raw=f.raw, journal=f.journal, connect=connect, clock=clock)
        connect.assert_not_called()
        clock.assert_not_called()
        self.assertEqual(self.snapshot(), before)
        f.empty()

    def test_original_fullchain_no_new_claim_or_stage(self):
        self.assert_protected_hold()
        self.assertEqual(self.f.claims(), 0)
        self.f.review('HOLD')

    def test_original_fullchain_pending_quarantine_preserved(self):
        f = self.f
        with f.authority.claim_and_fence(f.root, f.pin.scope_sha, f.pin.binding,
                                        f.pin.transaction_ref, f.pin.request_digest):
            f.journal.stage(f.i, f.binding)
        f.review('PENDING')
        self.assert_protected_hold()
        self.assertEqual(f.claims(), 1)
        f.review('PENDING')
