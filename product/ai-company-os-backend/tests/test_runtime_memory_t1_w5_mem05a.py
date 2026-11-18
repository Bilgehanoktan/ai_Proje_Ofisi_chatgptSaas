"""MEM-05A: compose original T1 SQL mapping with exact MEM-04; D0 SQLite only."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import sqlite3
import unittest
from unittest.mock import patch

from app.core.agent_runtime import memory_checkpoint as checkpoint
from app.core.agent_runtime.joint_context import joint_context_digest
from app.core.transaction.witnessed_mapping import binding_digest
from app.engines.memory_engine import snapshot_store as store
import test_memory_history_w5_mem03 as history
import test_witnessed_sql_0209 as sql


class RuntimeMemoryT1Tests(unittest.TestCase):
    def setUp(self):
        self.sql = sql.WitnessedSqlTests()
        self.sql.setUp()
        self.addCleanup(self.sql.doCleanups)
        self.w = self.sql.w
        # Reuse original multi-generation fixture methods on the original SQL fixture.
        self.h = history.HistoryCommitmentTests()
        self.h.f, self.h.b = self.w, self.w.b
        self.h.head, self.h.latest = self.w.record, self.w.latest
        self.h.pins = [self.w.b.pin]
        self.memory = self.w.b.store.path

    def advance(self, revision):
        self.h.advance(revision)
        self.bind_current()

    def bind_current(self):
        self.w.latest = self.h.latest
        self.w.j.context = self.h.context()
        self.w.j.pin = joint_context_digest(self.w.j.context, self.w.b.registry)
        self.sql.f.binding = binding_digest(self.sql.i, self.w.j.context,
                                           self.w.b.registry, self.w.latest)

    def prepare(self):
        body = checkpoint.prepare_checkpoint(self.memory, self.w.reader,
                                             self.h.latest, self.w.pub)
        self.checkpoint_args = dict(path=self.memory, reader=self.w.reader, body=body,
            signature=self.w.key.sign(body), checkpoint_sha=sha256(body).hexdigest(),
            public_key=self.w.pub, scope=self.h.head.scope, clock=self.w.b.f.clock)

    def suffix_matches(self):
        r = checkpoint.inspect_checkpoint_suffix(expected=self.h.latest, **self.checkpoint_args)
        self.assertTrue(r.suffix_match)
        self.assertFalse(r.prefix_reaudited)
        self.assertEqual(r.decision, 'HOLD')
        self.assertFalse(r.dispatch_allowed)

    def rollback(self, reason, **kwargs):
        with self.assertRaisesRegex(ValueError, reason):
            self.sql.execute(**kwargs)
        self.assertEqual(self.sql.dump(), self.sql.initial)

    def test_multigeneration_original_sql_commit_without_checkpoint(self):
        self.advance(8)
        self.advance(10)
        before = self.memory.read_bytes(), self.w.path.read_bytes()
        with patch.object(checkpoint, 'inspect_checkpoint_suffix', side_effect=AssertionError('checkpoint substituted')):
            self.sql.execute()
        self.sql.exact_readback()
        self.assertEqual(tuple(len(x) for x in self.sql.dump()), (1,1,1,1,1,1,1))
        self.assertEqual(before, (self.memory.read_bytes(), self.w.path.read_bytes()))

    def test_valid_checkpoint_does_not_replace_full_audit(self):
        self.advance(8)
        self.prepare()
        self.advance(10)
        self.suffix_matches()
        with patch.object(store, '_review_history', wraps=store._review_history) as audit:
            self.sql.execute()
        self.sql.exact_readback()
        self.assertEqual(audit.call_count, 4)  # two full reads at each T1 check

    def test_prefix_snapshot_rewrite_fast_match_but_original_t1_denies(self):
        self.advance(8)
        self.prepare()
        self.advance(10)
        self.h.rewrite(1, 6)
        self.suffix_matches()
        self.rollback('MEMORY_SNAPSHOT_READ_HOLD')

    def test_middle_snapshot_rewrite_before_original_t1_denies(self):
        self.advance(8)
        self.advance(10)
        self.h.rewrite(2, 9)
        self.rollback('MEMORY_SNAPSHOT_READ_HOLD')

    def test_prefix_signature_rewrite_fast_match_but_original_t1_denies(self):
        self.advance(8)
        self.prepare()
        with closing(sqlite3.connect(self.w.path)) as db, db:
            db.execute('DROP TRIGGER no_update')
            db.execute('UPDATE memory_witness SET signature=? WHERE sequence=1', (b'x'*64,))
        self.suffix_matches()
        self.rollback('MEMORY_WITNESS_READ_HOLD')

    def test_prefix_rewrite_during_original_sql_roles_rolls_back_all(self):
        self.advance(8)
        self.prepare()
        self.advance(10)
        def fault(role):
            if role == 'AUDIT':
                self.h.rewrite(1, 6)
        self.rollback('MEMORY_SNAPSHOT_READ_HOLD', fault=fault)
        self.suffix_matches()

    def test_signed_pending_current_head_denies(self):
        self.advance(8)
        _, self.h.latest = self.h.stage(self.h.snapshot(10))
        self.bind_current()
        self.rollback('MEMORY_WITNESS_PENDING_HOLD')

    def test_stale_external_witness_after_advance_denies(self):
        self.advance(8)
        self.h.advance(10)  # do not update pinned SQL context
        self.rollback('MEMORY_WITNESS_READ_HOLD')

    def test_checkpoint_missing_prefix_denies_original_t1(self):
        self.advance(8)
        self.prepare()
        with closing(sqlite3.connect(self.memory)) as db, db:
            db.execute('DELETE FROM snapshots WHERE generation=1')
        self.assertFalse(checkpoint.inspect_checkpoint_suffix(expected=self.h.latest, **self.checkpoint_args).suffix_match)
        self.rollback('MEMORY_SNAPSHOT_READ_HOLD')


if __name__ == '__main__':
    unittest.main(verbosity=2)
