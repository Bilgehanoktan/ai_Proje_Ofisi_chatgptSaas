"""Characterize 0196-M snapshot continuity on exact existing D0 modules.
PASS on a residual test means the limitation was reproduced, not fixed.
All data are synthetic; no authority or product writes are enabled.
"""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, LeaseObservation, ClockSample
from app.engines.memory_engine.retrieval import Node, TombstoneView
from app.engines.memory_engine.runtime_binding import MemoryAclEntry, MemoryAclView
from app.engines.knowledge_engine.provenance import SourceVersion, ClaimSpan
from app.engines.memory_engine.snapshot_store import (
    Snapshot, create_store, publish_snapshot, inspect_stored_memory, inspect_stored_memory_input,
)


def digest(raw):
    return sha256(raw).hexdigest()


class LineageContinuityDiagnostics(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / 'lineage.d0.sqlite'
        scope = Scope('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY',
                      'sha256:' + 'a'*64, 'research', 'demo-run', 'demo-agent', 'demo-principal')
        self.run = RunObservation(scope, RunState.RUNNING, 3, 1)
        self.lease = LeaseObservation(scope, 'lease', 'grant', 1, 1, 1, 2, 4, 100, 80)
        self.clock = ClockSample(85, 2, 4, 10)
        raw, self.other_raw = b'original source', b'alternate source'
        source = SourceVersion(scope, 'source', 'v1', digest(raw))
        span = ClaimSpan(source, 0, len(raw), digest(raw))
        nodes = (Node(scope, 'source', 'v1', digest(raw), ()),
                 Node(scope, 'cache', 'v2', 'b'*64, ('source',)),
                 Node(scope, 'other', 'v1', digest(self.other_raw), ()))
        view = TombstoneView(scope, 5, 9, (), True)
        acl = MemoryAclView(scope, 3, 1, 2, 4, 5, 9, 7, True, self.grants(nodes[:2]))
        self.snapshot = Snapshot(self.run, nodes, 'cache', view, acl, source, span, raw)
        create_store(self.path)
        self.pin = publish_snapshot(self.path, self.snapshot, None)

    @staticmethod
    def grants(nodes):
        return tuple(MemoryAclEntry(n.node_id, n.revision, n.digest, 'ALLOW_READ') for n in nodes)

    def review(self, pin):
        result = inspect_stored_memory(self.path, pin, self.run, self.lease, self.lease, self.clock)
        self.assertIs(result.retrieval_allowed, False)
        self.assertIs(result.release_allowed, False)
        self.assertFalse(hasattr(result, 'raw'))
        return result

    def revoke(self):
        s = self.snapshot
        return replace(s, tombstone=replace(s.tombstone, sequence=10, keys=('source',)),
                       acl=replace(s.acl, acl_revision=8, tombstone_sequence=10))

    def rebind(self, revoked, revision='v2'):
        first, cache, other = revoked.nodes
        cache = replace(cache, revision=revision, parents=('other',))
        source = SourceVersion(other.scope, other.node_id, other.revision, other.digest)
        raw = self.other_raw
        return replace(revoked, nodes=(first, cache, other), source=source, raw=raw,
                       span=ClaimSpan(source, 0, len(raw), digest(raw)),
                       acl=replace(revoked.acl, acl_revision=9, entries=self.grants((cache, other))))

    def test_baseline_no_authority(self):
        r = self.review(self.pin)
        self.assertEqual((r.reason, r.decision), ('D0_MEMORY_ACCESS_MATCH_ONLY', 'HOLD'))
        self.assertTrue(r.structural_match)

    def test_revocation_propagates_and_old_pin_rejected(self):
        newer = publish_snapshot(self.path, self.revoke(), self.pin)
        self.assertEqual(self.review(newer).reason, 'STALE_HOLD')
        self.assertEqual(self.review(self.pin).reason, 'MEMORY_SNAPSHOT_CAS_HOLD')

    def test_tombstone_removal_rejected(self):
        newer = publish_snapshot(self.path, self.revoke(), self.pin)
        restore = replace(self.snapshot, acl=replace(self.snapshot.acl, acl_revision=9))
        with self.assertRaisesRegex(ValueError, 'MONOTONIC'):
            publish_snapshot(self.path, restore, newer)
        self.assertEqual(self.review(newer).reason, 'STALE_HOLD')

    def test_residual_same_revision_source_digest_rebind(self):
        s = self.snapshot
        raw = b'rewritten source'
        source = replace(s.source, raw_digest=digest(raw))
        nodes = (replace(s.nodes[0], digest=digest(raw)), *s.nodes[1:])
        rewritten = replace(s, nodes=nodes, source=source, raw=raw,
                            span=ClaimSpan(source, 0, len(raw), digest(raw)),
                            acl=replace(s.acl, acl_revision=8, entries=self.grants(nodes[:2])))
        self.assertEqual(source.revision, s.source.revision)
        newer = publish_snapshot(self.path, rewritten, self.pin)
        self.assertNotEqual(newer.graph_digest, self.pin.graph_digest)
        self.assertTrue(self.review(newer).structural_match)
        self.assertEqual(self.review(newer).decision, 'HOLD')

    def test_residual_same_revision_detaches_tombstoned_ancestor(self):
        revoked = self.revoke()
        newer = publish_snapshot(self.path, revoked, self.pin)
        self.assertEqual(self.review(newer).reason, 'STALE_HOLD')
        rebound = self.rebind(revoked)
        self.assertEqual((rebound.nodes[1].revision, rebound.nodes[1].digest),
                         (revoked.nodes[1].revision, revoked.nodes[1].digest))
        self.assertEqual(rebound.tombstone, revoked.tombstone)
        latest = publish_snapshot(self.path, rebound, newer)
        self.assertNotEqual(latest.graph_digest, newer.graph_digest)
        self.assertEqual(self.review(latest).reason, 'D0_MEMORY_ACCESS_MATCH_ONLY')
        self.assertEqual(self.review(latest).decision, 'HOLD')
        self.assertEqual(self.review(newer).reason, 'MEMORY_SNAPSHOT_CAS_HOLD')

    def test_legitimate_new_revision_is_not_automatically_a_grant(self):
        revoked = self.revoke()
        newer = publish_snapshot(self.path, revoked, self.pin)
        latest = publish_snapshot(self.path, self.rebind(revoked, 'v3'), newer)
        self.assertEqual(self.review(latest).decision, 'HOLD')

    def test_exact_input_and_readback_are_read_only(self):
        before = self.path.read_bytes()
        args = (self.path, self.pin, self.run, self.lease, self.lease, self.clock)
        self.assertEqual(inspect_stored_memory_input(*args, self.snapshot.raw), 'D0_MEMORY_INPUT_MATCH_ONLY')
        self.assertEqual(inspect_stored_memory_input(*args, b'wrong'), 'JOINT_INPUT_SPAN_HOLD')
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
