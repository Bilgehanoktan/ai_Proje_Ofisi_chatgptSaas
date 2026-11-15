"""Real disposable SQLite tests for 0196-M; no customer data or provider."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from app.engines.memory_engine.snapshot_store import (
    Snapshot, SnapshotPin, create_store, publish_snapshot, inspect_stored_memory,
)
import test_memory_access_0194 as fixture


class SnapshotStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'memory.d0.sqlite'
        f = fixture.MemoryAccessTests(); f.setUp()
        self.f = f
        self.snapshot = Snapshot(f.run, f.nodes, 'cache', f.view, f.acl, f.source, f.span, f.raw)
        create_store(self.path)

    def inspect(self, pin, **changes):
        f = self.f
        kwargs = dict(path=self.path, expected=pin, run=f.run, lease=f.lease,
                      lease_reference=f.lease, clock=f.clock)
        kwargs.update(changes)
        r = inspect_stored_memory(**kwargs)
        self.assertFalse(r.retrieval_allowed)
        self.assertFalse(r.release_allowed)
        self.assertFalse(hasattr(r, 'raw'))
        return r

    def next(self, **changes):
        return replace(self.snapshot, acl=replace(self.snapshot.acl, acl_revision=8), **changes)

    def revoke(self):
        v = replace(self.snapshot.tombstone, sequence=10, keys=('source',))
        return replace(self.snapshot, tombstone=v,
                       acl=replace(self.snapshot.acl, acl_revision=8, tombstone_sequence=10))

    def test_reopen_and_read_only(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        before = sha256(self.path.read_bytes()).hexdigest()
        r = self.inspect(pin)
        self.assertEqual(r.reason, 'D0_MEMORY_ACCESS_MATCH_ONLY')
        self.assertTrue(r.structural_match)
        self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), before)

    def test_create_refuses_existing(self):
        before = self.path.read_bytes()
        with self.assertRaises(FileExistsError): create_store(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_file_no_creation(self):
        path = self.path.with_name('absent.d0.sqlite')
        r = self.inspect(SnapshotPin(1, 'a'*64, 'b'*64), path=path)
        self.assertEqual(r.reason, 'MEMORY_SNAPSHOT_READ_HOLD')
        self.assertFalse(path.exists())

    def test_canonical_graph_and_metadata_order(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        other = self.path.with_name('other.d0.sqlite'); create_store(other)
        reordered = replace(self.snapshot, nodes=tuple(reversed(self.snapshot.nodes)),
                            acl=replace(self.snapshot.acl, entries=tuple(reversed(self.snapshot.acl.entries))))
        self.assertEqual(publish_snapshot(other, reordered, None), pin)

    def test_graph_edge_changes_digest(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        nodes = (self.snapshot.nodes[0], replace(self.snapshot.nodes[1], parents=()), self.snapshot.nodes[2])
        newer = publish_snapshot(self.path, self.next(nodes=nodes), pin)
        self.assertNotEqual(pin.graph_digest, newer.graph_digest)
        self.assertEqual(self.inspect(newer).reason, 'MEMORY_ACL_COVERAGE_HOLD')

    def test_revocation_and_stale_pin(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        newer = publish_snapshot(self.path, self.revoke(), pin)
        self.assertEqual(self.inspect(pin).reason, 'MEMORY_SNAPSHOT_CAS_HOLD')
        self.assertEqual(self.inspect(newer).reason, 'STALE_HOLD')

    def test_tombstone_cannot_resurrect(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        newer = publish_snapshot(self.path, self.revoke(), pin)
        restore = replace(self.snapshot, acl=replace(self.snapshot.acl, acl_revision=9))
        with self.assertRaisesRegex(ValueError, 'MONOTONIC'): publish_snapshot(self.path, restore, newer)
        self.assertEqual(self.inspect(newer).reason, 'STALE_HOLD')

    def test_stale_cas_cannot_append(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        newer = publish_snapshot(self.path, self.next(), pin)
        with self.assertRaisesRegex(ValueError, 'CAS'): publish_snapshot(self.path, self.next(), pin)
        self.assertTrue(self.inspect(newer).structural_match)

    def test_parallel_cas_single_winner(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        barrier = threading.Barrier(2)
        def worker():
            barrier.wait(timeout=5)
            try: return publish_snapshot(self.path, self.next(), pin)
            except ValueError as exc: return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(worker) for _ in range(2)]
            outcomes = [x.result(timeout=10) for x in futures]
        winner = [x for x in outcomes if isinstance(x, SnapshotPin)]
        self.assertEqual(len(winner), 1)
        self.assertIn('MEMORY_SNAPSHOT_CAS_HOLD', outcomes)
        self.assertTrue(self.inspect(winner[0]).structural_match)

    def test_insert_failure_preserves_head(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER refuse BEFORE INSERT ON snapshots BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError): publish_snapshot(self.path, self.next(), pin)
        self.assertTrue(self.inspect(pin).structural_match)

    def test_metadata_and_raw_tamper(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE snapshots SET raw=?', (b'bad',))
        self.assertEqual(self.inspect(pin).reason, 'MEMORY_SNAPSHOT_READ_HOLD')
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE snapshots SET metadata=?', ('{}',))
        self.assertEqual(self.inspect(pin).reason, 'MEMORY_SNAPSHOT_READ_HOLD')

    def test_forged_graph_pin(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        bad = replace(pin, graph_digest='d'*64)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE snapshots SET graph=?', (bad.graph_digest,))
        self.assertEqual(self.inspect(pin).reason, 'MEMORY_SNAPSHOT_CAS_HOLD')
        self.assertEqual(self.inspect(bad).reason, 'MEMORY_SNAPSHOT_READ_HOLD')

    def test_wrong_run_and_expired_lease(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        f = self.f
        self.assertEqual(self.inspect(pin, run=replace(f.run, version=4)).reason, 'RUN_REFERENCE_HOLD')
        self.assertEqual(self.inspect(pin, clock=replace(f.clock, now_tick=100)).reason, 'MEMORY_LEASE_HOLD')

    def test_deny_persisted(self):
        acl = self.snapshot.acl
        s = replace(self.snapshot, acl=replace(acl, entries=(replace(acl.entries[0], decision='DENY_READ'), acl.entries[1])))
        pin = publish_snapshot(self.path, s, None)
        self.assertEqual(self.inspect(pin).decision, 'DENY')

    def test_bad_path_and_pin(self):
        pin = publish_snapshot(self.path, self.snapshot, None)
        self.assertEqual(self.inspect(replace(pin, generation=True)).reason, 'MEMORY_SNAPSHOT_PIN_HOLD')
        with self.assertRaisesRegex(ValueError, 'PATH'): create_store(self.path.with_name('other.sqlite'))
        link = self.path.with_name('link.d0.sqlite')
        try: link.symlink_to(self.path)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314: self.skipTest('Windows symlink privilege')
            raise
        self.assertEqual(self.inspect(pin, path=link).reason, 'MEMORY_SNAPSHOT_READ_HOLD')


if __name__ == '__main__':
    unittest.main()
