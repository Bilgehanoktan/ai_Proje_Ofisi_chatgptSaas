"""0194 memory access reference tests; no retrieval IO or real authority."""
import unittest
from dataclasses import replace
from hashlib import sha256
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, LeaseObservation, ClockSample
from app.engines.memory_engine.retrieval import Node, TombstoneView, inspect_retrieval
from app.engines.memory_engine.runtime_binding import MemoryAclEntry, MemoryAclView, inspect_run_memory_access
from app.engines.knowledge_engine.provenance import SourceVersion, ClaimSpan


class MemoryAccessTests(unittest.TestCase):
    def setUp(self):
        self.scope = Scope("synthetic-tenant", "synthetic-company", "A0_SAMPLE_ONLY",
                           "sha256:" + "a"*64, "research", "demo-run", "demo-agent", "demo-principal")
        self.run = RunObservation(self.scope, RunState.RUNNING, 3, 1)
        self.lease = LeaseObservation(self.scope, "lease", "grant", 1, 1, 1, 2, 4, 100, 80)
        self.clock = ClockSample(85, 2, 4, 10)
        self.raw = "açık kaynak".encode("utf-8")
        self.source = SourceVersion(self.scope, "source", "v1", sha256(self.raw).hexdigest())
        self.span = ClaimSpan(self.source, 1, 3, sha256(self.raw[1:3]).hexdigest())
        self.nodes = (
            Node(self.scope, "source", "v1", self.source.raw_digest, ()),
            Node(self.scope, "cache", "v2", "b"*64, ("source",)),
            Node(self.scope, "other", "v1", "c"*64, ()),
        )
        self.view = TombstoneView(self.scope, 5, 9, (), True)
        self.entries = tuple(MemoryAclEntry(n.node_id, n.revision, n.digest, "ALLOW_READ") for n in self.nodes[:2])
        self.acl = MemoryAclView(self.scope, 3, 1, 2, 4, 5, 9, 7, True, self.entries)

    def review(self, **changes):
        args = dict(run=self.run, expected_run=self.run, nodes=self.nodes, target="cache",
                    view=self.view, current=self.view, acl=self.acl, current_acl=self.acl,
                    lease=self.lease, lease_reference=self.lease, clock=self.clock,
                    source=self.source, span=self.span, raw=self.raw)
        args.update(changes)
        result = inspect_run_memory_access(**args)
        self.assertFalse(result.retrieval_allowed)
        self.assertFalse(result.release_allowed)
        self.assertFalse(hasattr(result, "raw"))
        return result

    def both(self, acl):
        return dict(acl=acl, current_acl=acl)

    def test_match_never_grants(self):
        r = self.review()
        self.assertTrue(r.structural_match)
        self.assertEqual((r.reason, r.decision), ("D0_MEMORY_ACCESS_MATCH_ONLY", "HOLD"))

    def test_run_version_and_attempt_drift(self):
        for change in (dict(version=4), dict(attempt=2), dict(attempt=True)):
            self.assertEqual(self.review(expected_run=replace(self.run, **change)).reason, "RUN_REFERENCE_HOLD")

    def test_terminal_or_non_running(self):
        for state in (RunState.PLANNING, RunState.WAITING_APPROVAL, RunState.SUCCEEDED):
            run = replace(self.run, state=state)
            self.assertEqual(self.review(run=run, expected_run=run).reason, "RUN_REFERENCE_HOLD")

    def test_cross_principal_run(self):
        run = replace(self.run, scope=replace(self.scope, principal_id="demo-other"))
        self.assertEqual(self.review(expected_run=run).reason, "RUN_REFERENCE_HOLD")

    def test_expired_and_wrong_scope_lease(self):
        self.assertEqual(self.review(clock=replace(self.clock, now_tick=100)).reason, "MEMORY_LEASE_HOLD")
        lease = replace(self.lease, scope=replace(self.scope, principal_id="demo-other"))
        self.assertEqual(self.review(lease=lease, lease_reference=lease).reason, "MEMORY_LEASE_HOLD")

    def test_tombstone_propagation(self):
        view = replace(self.view, keys=("source",))
        self.assertEqual(self.review(view=view, current=view).reason, "STALE_HOLD")

    def test_current_tombstone_boolean_alias(self):
        view = replace(self.view, epoch=1, sequence=1)
        for changes in (dict(epoch=True), dict(sequence=True), dict(complete=1)):
            current = replace(view, **changes)
            self.assertEqual(inspect_retrieval(self.scope, self.nodes, "cache", view, current).reason,
                             "TOMBSTONE_VIEW_UNKNOWN_HOLD")

    def test_acl_reference_revision_and_type(self):
        for current in (replace(self.acl, acl_revision=8), replace(self.acl, complete=1),
                        replace(self.acl, run_attempt=True)):
            self.assertEqual(self.review(current_acl=current).reason, "MEMORY_ACL_REFERENCE_HOLD")

    def test_acl_epochs_and_tombstone_sequence(self):
        for changes in (dict(policy_epoch=3), dict(witness_epoch=3), dict(tombstone_epoch=6),
                        dict(tombstone_sequence=10)):
            acl = replace(self.acl, **changes)
            self.assertEqual(self.review(**self.both(acl)).reason, "MEMORY_ACL_REFERENCE_HOLD")

    def test_acl_exact_ancestor_coverage(self):
        for entries in ((self.entries[1],), self.entries + (MemoryAclEntry("other","v1","c"*64,"ALLOW_READ"),)):
            self.assertEqual(self.review(**self.both(replace(self.acl, entries=entries))).reason,
                             "MEMORY_ACL_COVERAGE_HOLD")

    def test_duplicate_acl_entry(self):
        acl = replace(self.acl, entries=self.entries + (self.entries[0],))
        self.assertEqual(self.review(**self.both(acl)).reason, "MEMORY_ACL_REFERENCE_HOLD")

    def test_ancestor_deny(self):
        acl = replace(self.acl, entries=(replace(self.entries[0], decision="DENY_READ"), self.entries[1]))
        r = self.review(**self.both(acl))
        self.assertEqual((r.reason, r.decision), ("MEMORY_ACL_DENY", "DENY"))

    def test_acl_pin_mismatch(self):
        acl = replace(self.acl, entries=(replace(self.entries[0], digest="d"*64), self.entries[1]))
        self.assertEqual(self.review(**self.both(acl)).reason, "MEMORY_ACL_PIN_HOLD")

    def test_unrelated_source_and_wrong_principal(self):
        for source in (replace(self.source, source_id="other"),
                       replace(self.source, scope=replace(self.scope, principal_id="demo-other"))):
            self.assertEqual(self.review(source=source).reason, "MEMORY_SOURCE_SCOPE_HOLD")

    def test_source_revision_mismatch(self):
        self.assertEqual(self.review(source=replace(self.source, revision="v2")).reason, "MEMORY_SOURCE_PIN_HOLD")

    def test_raw_and_span_tamper(self):
        self.assertEqual(self.review(raw=b"changed").reason, "SOURCE_DIGEST_HOLD")
        self.assertEqual(self.review(span=replace(self.span, end=4)).reason, "SPAN_DIGEST_HOLD")
        self.assertEqual(self.review(span=replace(self.span, start=True)).reason, "SPAN_BOUNDS_HOLD")

    def test_graph_cycle_orphan(self):
        nodes = (replace(self.nodes[0], parents=("cache",)), *self.nodes[1:])
        self.assertEqual(self.review(nodes=nodes).reason, "LINEAGE_CYCLE_HOLD")
        self.assertEqual(self.review(nodes=self.nodes[1:]).reason, "LINEAGE_ORPHAN_OR_DUPLICATE_HOLD")


if __name__ == "__main__":
    unittest.main()
