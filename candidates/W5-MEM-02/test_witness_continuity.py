"""W5-MEM-02: signed fixture checks for the new retained-history rule."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import sqlite3
import unittest

from app.core.agent_runtime import memory_witness as w
from app.engines.memory_engine import snapshot_store as store
import test_memory_witness_0209 as fixture


class WitnessContinuityTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.MemoryWitnessTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.b = self.f.b
        s = self.b.store.snapshot
        # Even an unrelated historical node may not be redefined at the same revision.
        self.invalid = replace(s, nodes=(*s.nodes[:2], replace(s.nodes[2], digest='e'*64)),
                               acl=replace(s.acl, acl_revision=8))
        self.metadata, graph = store._encode(self.invalid)
        self.target = store.SnapshotPin(2, sha256(self.metadata.encode('ascii')).hexdigest(), graph)

    def stage(self):
        pending = self.f.next(pending=self.target)
        return pending, self.f.append(pending, self.f.latest.record_sha)

    def test_rejected_write_leaves_signed_pending_hold(self):
        pending, pin = self.stage()
        before = self.b.store.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'REVISION_IMMUTABLE'):
            store.publish_snapshot(self.b.store.path, self.invalid, self.b.pin)
        self.assertEqual(self.b.store.path.read_bytes(), before)
        self.assertEqual(self.f.review(expected_witness=pin).reason, 'MEMORY_WITNESS_PENDING_HOLD')
        self.assertFalse(self.f.review().structural_match)
        with self.assertRaisesRegex(ValueError, 'PENDING'):
            self.f.append(replace(pending, sequence=3, previous_sha=pin.record_sha, pending=None), pin.record_sha)

    def test_even_signed_legacy_conflict_cannot_match_joint_context(self):
        pending, pin = self.stage()
        with closing(sqlite3.connect(self.b.store.path)) as db, db:
            db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)',
                       (2, self.target.digest, self.target.graph_digest, self.metadata, self.invalid.raw))
        ready = replace(pending, sequence=3, previous_sha=pin.record_sha, snapshot=self.target, pending=None)
        latest = self.f.append(ready, pin.record_sha)
        context = replace(self.f.j.context, memory_pin=self.target)
        result = self.f.review(expected_witness=latest, **self.f.j.repin(context))
        self.assertEqual(result.reason, 'MEMORY_SNAPSHOT_READ_HOLD')
        self.assertFalse(result.structural_match)


if __name__ == '__main__':
    unittest.main(verbosity=2)
