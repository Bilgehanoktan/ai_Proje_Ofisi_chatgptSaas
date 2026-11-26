"""Uses existing 0199 SQLite fixture and real plan reader; PG adapter is patched."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import test_plan_history_review_0199 as base
from app.core.event_store.retained_history import ReferenceReader, ReferenceStore, history_reference, reference_bytes, review_retained_snapshot


class RetainedSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.f = base.PlanHistoryTests(); self.f.setUp(); self.addCleanup(self.f.doCleanups)
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.store = ReferenceStore(Path(tmp.name)/'refs.db')
        self.reader = ReferenceReader(self.store.path)
        self.readback = patch('app.core.event_store.postgres_snapshot.read_plan_snapshot', side_effect=self.snapshot).start()
        self.addCleanup(patch.stopall)

    def snapshot(self, connect, plan, revision, pins, *, exclusive_budget_anchors=None):
        return self.f.review(pins=pins, plan=plan, revision=revision, anchors=exclusive_budget_anchors)

    def seal(self):
        pins = self.f.pins(); key = self.store.put(history_reference(self.f.plan,self.f.revision,pins))
        return pins,key

    def review(self, pins, key, refs=(), plan=None):
        return review_retained_snapshot(self.reader, None, self.f.plan if plan is None else plan,
                                        self.f.revision,pins,key,terminal_refs=refs)

    def hold(self, result):
        self.assertFalse(result.reference_match or result.independent_verified or result.release_ready or result.dispatch_allowed)
        self.assertIsNone(result.history); self.assertEqual(result.failure_commands,())

    def test_real_admission_readback(self):
        pins,key = self.seal(); r = self.review(pins,key)
        self.assertTrue(r.reference_match); self.assertEqual(r.history.event_count,1)
        self.assertFalse(r.independent_verified or r.dispatch_allowed or r.release_ready)

    def test_changed_plan_before_db(self):
        pins,key = self.seal(); plan=copy.deepcopy(self.f.plan); plan['tasks'][0]['label']='changed'
        self.hold(self.review(pins,key,plan=plan)); self.readback.assert_not_called()

    def test_missing_reference_before_db(self):
        pins,key = self.seal(); self.hold(self.review(pins,'0'*64)); self.readback.assert_not_called()

    def test_failure_needs_separate_terminal_pin(self):
        self.f.f.chain(); pins,key = self.seal(); cmd=pins[0].commands[-1]
        tkey=self.store.put(reference_bytes('terminal-command-v1',cmd)); run=pins[0].initial.scope.run_id
        self.hold(self.review(pins,key)); self.readback.assert_not_called()
        self.hold(self.review(pins,key,((run,'0'*64),))); self.readback.assert_not_called()
        r=self.review(pins,key,((run,tkey),)); self.assertTrue(r.reference_match)
        self.assertEqual(r.failure_commands[0][:2],(run,tkey)); self.assertFalse(r.independent_verified)

    def test_tampered_ledger(self):
        pins,key=self.seal(); self.f.change('DELETE FROM run_audit'); self.hold(self.review(pins,key))


if __name__ == '__main__': unittest.main()
