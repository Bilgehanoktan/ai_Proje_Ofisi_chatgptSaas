"""W5-MEM-03: real disposable SQLite / signed Witness fixture tests."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import sqlite3
import unittest
from unittest.mock import patch

from app.core.agent_runtime import joint_context as joint
from app.core.agent_runtime import memory_witness as w
from app.engines.memory_engine import snapshot_store as store
import test_memory_witness_0209 as fixture


class HistoryCommitmentTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.MemoryWitnessTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.b = self.f.b
        self.head, self.latest = self.f.record, self.f.latest
        self.pins = [self.b.pin]

    def snapshot(self, revision):
        original = self.b.store.snapshot
        return replace(original, acl=replace(original.acl, acl_revision=revision))

    def stage(self, snapshot):
        metadata, graph = store._encode(snapshot)
        target = store.SnapshotPin(self.head.snapshot.generation + 1,
                                   sha256(metadata.encode('ascii')).hexdigest(), graph)
        pending = replace(self.head, sequence=self.head.sequence + 1,
                          previous_sha=self.latest.record_sha, pending=target)
        return pending, self.f.append(pending, self.latest.record_sha)

    def advance(self, revision):
        snapshot = self.snapshot(revision)
        pending, p = self.stage(snapshot)
        self.assertEqual(store.publish_snapshot(self.b.store.path, snapshot,
                                               self.head.snapshot), pending.pending)
        ready = replace(pending, sequence=pending.sequence + 1, previous_sha=p.record_sha,
                        snapshot=pending.pending, pending=None)
        self.latest = self.f.append(ready, p.record_sha)
        self.head = ready
        self.pins.append(ready.snapshot)

    def context(self):
        return replace(self.f.j.context, memory_pin=self.head.snapshot)

    def review(self):
        return self.f.review(expected_witness=self.latest, **self.f.j.repin(self.context()))

    def rewrite(self, generation, revision):
        snapshot = self.snapshot(revision)
        metadata, graph = store._encode(snapshot)
        with closing(sqlite3.connect(self.b.store.path)) as db, db:
            db.execute('UPDATE snapshots SET digest=?,graph=?,metadata=?,raw=? WHERE generation=?',
                       (sha256(metadata.encode('ascii')).hexdigest(), graph,
                        metadata, snapshot.raw, generation))

    def assert_plain_matches(self):
        # The old diagnostic knows only the latest pin; this demonstrates the
        # coherent rewrite still satisfies MEM-02 local continuity.
        self.assertTrue(self.f.j.review(**self.f.j.repin(self.context())).structural_match)

    def test_three_committed_generations_match_read_only(self):
        self.advance(8)
        self.advance(10)
        before = (self.b.store.path.read_bytes(), self.f.path.read_bytes())
        self.assertEqual(self.f.reader.read_history(self.latest, self.f.pub),
                         (self.head, tuple(self.pins)))
        self.assertTrue(self.review().structural_match)
        self.assertEqual(before, (self.b.store.path.read_bytes(), self.f.path.read_bytes()))

    def test_coherent_genesis_rewrite_same_head_rejected(self):
        self.advance(8)
        self.rewrite(1, 6)
        self.assert_plain_matches()
        self.assertEqual(self.review().reason, 'MEMORY_SNAPSHOT_READ_HOLD')
        self.assertFalse(self.review().structural_match)

    def test_coherent_middle_rewrite_same_head_rejected(self):
        self.advance(8)
        self.advance(10)
        self.rewrite(2, 9)
        self.assert_plain_matches()
        self.assertFalse(self.review().structural_match)

    def test_rewrite_between_joint_reads_rejected(self):
        self.advance(8)
        real = joint.inspect_invocation
        def interleave(*args):
            result = real(*args)
            self.rewrite(1, 6)
            return result
        with patch.object(joint, 'inspect_invocation', side_effect=interleave):
            self.assertEqual(self.review().reason, 'MEMORY_SNAPSHOT_READ_HOLD')
        self.assert_plain_matches()

    def test_recovery_epoch_does_not_duplicate_committed_pin(self):
        self.advance(8)
        rec = replace(self.head, sequence=self.head.sequence + 1,
                      previous_sha=self.latest.record_sha,
                      recovery_epoch=self.head.recovery_epoch + 1)
        self.latest = self.f.append(rec, self.latest.record_sha)
        self.head = rec
        self.assertEqual(self.f.reader.read_history(self.latest, self.f.pub),
                         (rec, tuple(self.pins)))
        self.assertTrue(self.review().structural_match)

    def test_pending_excluded_and_review_stays_hold(self):
        self.advance(8)
        pending, p = self.stage(self.snapshot(10))
        self.assertEqual(self.f.reader.read_history(p, self.f.pub),
                         (pending, tuple(self.pins)))
        self.assertEqual(self.f.review(expected_witness=p, **self.f.j.repin(self.context())).reason,
                         'MEMORY_WITNESS_PENDING_HOLD')

    def test_incomplete_and_wrong_order_pins_rejected(self):
        self.advance(8)
        args = self.f.j.repin(self.context())
        for history in ((), (self.pins[-1],), tuple(reversed(self.pins)), list(self.pins)):
            with self.subTest(history=history):
                self.assertFalse(self.f.j.review(expected_history=history, **args).structural_match)

    def test_missing_history_row_rejected(self):
        self.advance(8)
        with closing(sqlite3.connect(self.b.store.path)) as db, db:
            db.execute('DELETE FROM snapshots WHERE generation=1')
        self.assertFalse(self.review().structural_match)

    def test_historical_signature_tamper_rejected(self):
        self.advance(8)
        with closing(sqlite3.connect(self.f.path)) as db, db:
            db.execute('DROP TRIGGER no_update')
            db.execute('UPDATE memory_witness SET signature=? WHERE sequence=1', (b'x' * 64,))
        self.assertFalse(self.review().structural_match)


if __name__ == '__main__':
    unittest.main(verbosity=2)
