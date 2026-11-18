"""W5-MEM-02: actual disposable SQLite regression of the existing store."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import sqlite3
from threading import Barrier
import unittest
from unittest.mock import patch
from app.engines.memory_engine import snapshot_store as store
import test_lineage_continuity as fixture


class RevisionContinuityTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.LineageContinuityDiagnostics()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.s = self.f.snapshot
        self.pin = self.f.pin
        self.path = self.f.path

    def append(self, s, expected=None):
        return store.publish_snapshot(self.path, s, self.pin if expected is None else expected)

    def review(self, pin, **changes):
        f = self.f
        args = dict(path=self.path, expected=pin, run=f.run, lease=f.lease,
                    lease_reference=f.lease, clock=f.clock)
        args.update(changes)
        r = store.inspect_stored_memory(**args)
        self.assertIs(r.retrieval_allowed, False)
        self.assertIs(r.release_allowed, False)
        self.assertFalse(hasattr(r, 'raw'))
        return r

    def reject(self, candidate, pin, reason='REVISION_IMMUTABLE'):
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, reason):
            self.append(candidate, pin)
        self.assertEqual(before, self.path.read_bytes())

    def revised_source(self, source_revision='v1', cache_revision='v2', acl_revision=8):
        raw = b'rewritten source'
        h = sha256(raw).hexdigest()
        source = replace(self.s.source, revision=source_revision, raw_digest=h)
        nodes = (replace(self.s.nodes[0], revision=source_revision, digest=h),
                 replace(self.s.nodes[1], revision=cache_revision), self.s.nodes[2])
        return replace(self.s, source=source, raw=raw, nodes=nodes,
                       span=store.ClaimSpan(source, 0, len(raw), h),
                       acl=replace(self.s.acl, acl_revision=acl_revision,
                                   entries=self.f.grants(nodes[:2])))

    def test_same_source_revision_new_digest_rejected(self):
        self.reject(self.revised_source(), self.pin)
        self.assertTrue(self.review(self.pin).structural_match)

    def test_same_target_revision_detaching_revoked_ancestor_rejected(self):
        revoked = self.f.revoke()
        latest = self.append(revoked)
        self.reject(self.f.rebind(revoked), latest)
        self.assertEqual(self.review(latest).reason, 'STALE_HOLD')

    def test_parent_revision_change_requires_child_revision_even_with_same_parent_digest(self):
        nodes = (replace(self.s.nodes[0], revision='v2'), *self.s.nodes[1:])
        source = replace(self.s.source, revision='v2')
        candidate = replace(self.s, nodes=nodes, source=source,
                            span=replace(self.s.span, source=source),
                            acl=replace(self.s.acl, acl_revision=8, entries=self.f.grants(nodes[:2])))
        self.reject(candidate, self.pin)

    def test_fresh_source_and_child_revision_allowed_no_grant(self):
        latest = self.append(self.revised_source('v2', 'v3'))
        r = self.review(latest)
        self.assertTrue(r.structural_match)
        self.assertEqual(r.decision, 'HOLD')
        self.assertEqual(self.review(self.pin).reason, 'MEMORY_SNAPSHOT_CAS_HOLD')

    def test_new_revision_with_new_ancestor_no_grant(self):
        revoked = self.f.revoke()
        pin = self.append(revoked)
        latest = self.append(self.f.rebind(revoked, 'v3'), pin)
        self.assertTrue(self.review(latest).structural_match)
        self.assertEqual(self.review(latest).decision, 'HOLD')

    def test_reintroduced_old_revision_different_digest_rejected(self):
        pin = self.append(self.revised_source('v2', 'v3'))
        self.reject(self.revised_source('v1', 'v4', 9), pin)

    def test_removed_node_revision_cannot_be_redefined(self):
        s = replace(self.s, nodes=self.s.nodes[:2], acl=replace(self.s.acl, acl_revision=8))
        pin = self.append(s)
        nodes = (*s.nodes, replace(self.s.nodes[2], digest='e'*64))
        self.reject(replace(s, nodes=nodes, acl=replace(s.acl, acl_revision=9)), pin)

    def test_reintroduced_identical_revision_permitted(self):
        s = replace(self.s, nodes=self.s.nodes[:2], acl=replace(self.s.acl, acl_revision=8))
        pin = self.append(s)
        latest = self.append(replace(self.s, acl=replace(self.s.acl, acl_revision=9)), pin)
        self.assertTrue(self.review(latest).structural_match)

    def test_acl_only_revocation_retains_revision(self):
        latest = self.append(self.f.revoke())
        self.assertEqual(latest.graph_digest, self.pin.graph_digest)
        self.assertEqual(self.review(latest).reason, 'STALE_HOLD')

    def test_order_insensitive_parent_and_node_order(self):
        cache = replace(self.s.nodes[1], revision='v3', parents=('source', 'other'))
        nodes = (self.s.nodes[0], cache, self.s.nodes[2])
        s = replace(self.s, nodes=nodes, acl=replace(self.s.acl, acl_revision=8,
                                                    entries=self.f.grants(nodes)))
        pin = self.append(s)
        s = replace(s, nodes=(nodes[2], replace(cache, parents=('other', 'source')), nodes[0]),
                    acl=replace(s.acl, acl_revision=9))
        latest = self.append(s, pin)
        self.assertEqual(latest.graph_digest, pin.graph_digest)
        self.assertTrue(self.review(latest).structural_match)

    def test_missing_history_row_holds_both_read_paths_and_append(self):
        s = replace(self.s, acl=replace(self.s.acl, acl_revision=8))
        p2 = self.append(s)
        p3 = self.append(replace(s, acl=replace(s.acl, acl_revision=9)), p2)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DELETE FROM snapshots WHERE generation=2')
        self.assertEqual(self.review(p3).reason, 'MEMORY_SNAPSHOT_READ_HOLD')
        self.assertEqual(store.inspect_stored_memory_input(self.path, p3, self.f.run,
                         self.f.lease, self.f.lease, self.f.clock, s.raw), 'MEMORY_SNAPSHOT_READ_HOLD')
        self.reject(replace(s, acl=replace(s.acl, acl_revision=10)), p3, 'HISTORY_HOLD')

    def test_legacy_coherent_conflicting_row_holds(self):
        s = self.revised_source()
        metadata, graph = store._encode(s)
        pin = store.SnapshotPin(2, store._hash(metadata), graph)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)', (2, pin.digest, graph, metadata, s.raw))
        self.assertEqual(self.review(pin).reason, 'MEMORY_SNAPSHOT_READ_HOLD')
        self.assertEqual(store.inspect_stored_memory_input(self.path, pin, self.f.run,
                         self.f.lease, self.f.lease, self.f.clock, s.raw), 'MEMORY_SNAPSHOT_READ_HOLD')
        self.reject(replace(s, acl=replace(s.acl, acl_revision=9)), pin)

    def test_historical_raw_tamper_holds_even_with_valid_current_pin(self):
        latest = self.append(replace(self.s, acl=replace(self.s.acl, acl_revision=8)))
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE snapshots SET raw=? WHERE generation=1', (b'bad',))
        self.assertEqual(self.review(latest).reason, 'MEMORY_SNAPSHOT_READ_HOLD')

    def test_generation_bound_does_not_create_unreadable_head(self):
        with patch.object(store, 'HISTORY_LIMIT', 1):
            self.reject(replace(self.s, acl=replace(self.s.acl, acl_revision=8)), self.pin, 'HISTORY_LIMIT')
            self.assertTrue(self.review(self.pin).structural_match)

    def test_total_byte_bound_does_not_create_unreadable_head(self):
        metadata, _ = store._encode(self.s)
        with patch.object(store, 'HISTORY_BYTES', len(metadata)+len(self.s.raw)):
            self.reject(replace(self.s, acl=replace(self.s.acl, acl_revision=8)), self.pin, 'HISTORY_LIMIT')
            self.assertTrue(self.review(self.pin).structural_match)

    def test_two_writers_cas_single_winner(self):
        barrier = Barrier(2)
        candidate = replace(self.s, acl=replace(self.s.acl, acl_revision=8))
        def writer():
            barrier.wait(5)
            try: return self.append(candidate)
            except ValueError as e: return str(e)
        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = (pool.submit(writer) for _ in range(2))
            outcomes = [a.result(10), b.result(10)]
        self.assertIn('MEMORY_SNAPSHOT_CAS_HOLD', outcomes)
        winner = next(x for x in outcomes if isinstance(x, store.SnapshotPin))
        self.assertTrue(self.review(winner).structural_match)

    def test_runtime_lease_and_input_remain_read_only(self):
        before = self.path.read_bytes()
        self.assertEqual(self.review(self.pin, clock=replace(self.f.clock, now_tick=100)).reason, 'MEMORY_LEASE_HOLD')
        self.assertEqual(self.review(self.pin, run=replace(self.f.run, version=4)).reason, 'RUN_REFERENCE_HOLD')
        self.assertEqual(store.inspect_stored_memory_input(self.path, self.pin, self.f.run,
                         self.f.lease, self.f.lease, self.f.clock, self.s.raw), 'D0_MEMORY_INPUT_MATCH_ONLY')
        self.assertEqual(self.path.read_bytes(), before)

if __name__ == '__main__':
    unittest.main(verbosity=2)
