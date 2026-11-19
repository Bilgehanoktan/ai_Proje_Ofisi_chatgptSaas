"""MEM-04: real SQLite and ephemeral signing, never independent custody."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import json
import sqlite3
import unittest
from unittest.mock import patch

from app.core.agent_runtime import memory_checkpoint as c, memory_witness as w
from app.engines.memory_engine import snapshot_store as s
import test_memory_history_w5_mem03 as fixture


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.h = fixture.HistoryCommitmentTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.f, self.path = self.h.f, self.h.b.store.path

    def checkpoint(self):
        body = c.prepare_checkpoint(self.path, self.f.reader, self.h.latest, self.f.pub)
        self.body, self.signature, self.pin = body, self.f.key.sign(body), sha256(body).hexdigest()

    def inspect(self, **changes):
        args = dict(path=self.path, reader=self.f.reader, body=self.body, signature=self.signature,
                    checkpoint_sha=self.pin, expected=self.h.latest, public_key=self.f.pub,
                    scope=self.h.head.scope, clock=self.h.b.f.clock)
        args.update(changes)
        review = c.inspect_checkpoint_suffix(**args)
        self.assertEqual(review.decision, 'HOLD')
        for flag in ('prefix_reaudited', 'retrieval_allowed', 'release_allowed', 'provider_call_allowed',
                     'dispatch_allowed', 'spend_allowed', 'prune_allowed', 'retry_allowed', 'independent_verified'):
            self.assertIs(getattr(review, flag), False)
        return review

    def append(self, snapshot, bypass=False):
        pending, p = self.h.stage(snapshot)
        pin = pending.pending
        if bypass:
            metadata, graph = s._encode(snapshot)
            with closing(sqlite3.connect(self.path)) as db, db:
                db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)',
                           (pin.generation, pin.digest, graph, metadata, snapshot.raw))
        else:
            self.assertEqual(s.publish_snapshot(self.path, snapshot, self.h.head.snapshot), pin)
        ready = replace(pending, sequence=pending.sequence + 1, previous_sha=p.record_sha,
                        snapshot=pin, pending=None)
        self.h.latest = self.f.append(ready, p.record_sha)
        self.h.head = ready

    def test_signed_checkpoint_zero_suffix_read_only(self):
        self.h.advance(8)
        before = self.path.read_bytes(), self.f.path.read_bytes()
        self.checkpoint()
        review = self.inspect()
        self.assertTrue(review.suffix_match)
        self.assertEqual((review.snapshot_suffix, review.witness_suffix, review.retention), (0, 0, 'RETAIN_ONLY'))
        self.assertEqual(before, (self.path.read_bytes(), self.f.path.read_bytes()))
        self.assertNotIn(self.h.b.store.snapshot.raw, self.body)
        self.assertEqual(self.body, c.prepare_checkpoint(self.path, self.f.reader, self.h.latest, self.f.pub))

    def test_suffix_only_no_prefix_payload_replay(self):
        self.h.advance(8)
        self.h.advance(9)
        self.checkpoint()
        self.h.advance(10)
        before = self.path.read_bytes(), self.f.path.read_bytes()
        with patch.object(s, '_review_history', side_effect=AssertionError('full snapshot replay')), \
             patch.object(w, '_latest', side_effect=AssertionError('full witness replay')), \
             patch.object(s, '_load', wraps=s._load) as load, \
             patch.object(w, '_decode', wraps=w._decode) as decode:
            review = self.inspect()
        self.assertTrue(review.suffix_match)
        self.assertEqual((review.snapshot_suffix, review.witness_suffix), (1, 2))
        self.assertEqual([a.args[1].generation for a in load.call_args_list], [3, 4])
        self.assertEqual(len(decode.call_args_list), 7)  # checkpoint anchor + two suffix observations
        self.assertEqual(before, (self.path.read_bytes(), self.f.path.read_bytes()))

    def test_bad_signature_digest_and_key(self):
        self.checkpoint()
        for changes in (dict(signature=b'x'*64), dict(checkpoint_sha='0'*64),
                        dict(public_key=b'x'*32), dict(body=self.body+b' '),
                        dict(expected=replace(self.h.latest, key_sha='0'*64))):
            self.assertFalse(self.inspect(**changes).suffix_match)

    def test_noncanonical_signed_summary_rejected(self):
        self.checkpoint()
        body = self.body+b' '
        self.assertFalse(self.inspect(body=body, signature=self.f.key.sign(body),
                                     checkpoint_sha=sha256(body).hexdigest()).suffix_match)

    def test_duplicate_revision_in_signed_summary_rejected(self):
        self.checkpoint()
        doc = json.loads(self.body)
        doc[-1].append(doc[-1][0])
        body = s._json(doc).encode('ascii')
        self.assertFalse(self.inspect(body=body, signature=self.f.key.sign(body),
                                     checkpoint_sha=sha256(body).hexdigest()).suffix_match)

    def test_stale_restore_with_current_external_pin_rejected(self):
        self.checkpoint()
        old_memory = self.path.with_name('old.d0.sqlite')
        old_witness = self.f.path.with_name('old.witness.sqlite')
        old_memory.write_bytes(self.path.read_bytes())
        old_witness.write_bytes(self.f.path.read_bytes())
        self.h.advance(8)
        self.assertFalse(self.inspect(path=old_memory).suffix_match)
        self.assertFalse(self.inspect(reader=w.MemoryWitnessReader(old_witness)).suffix_match)
        self.assertFalse(self.inspect(path=old_memory, reader=w.MemoryWitnessReader(old_witness)).suffix_match)

    def test_full_restore_with_stale_external_pins_residual(self):
        self.checkpoint()
        old_pin = self.h.latest
        old_memory = self.path.with_name('old.d0.sqlite')
        old_witness = self.f.path.with_name('old.witness.sqlite')
        old_memory.write_bytes(self.path.read_bytes())
        old_witness.write_bytes(self.f.path.read_bytes())
        self.h.advance(8)
        self.assertTrue(self.inspect(path=old_memory, reader=w.MemoryWitnessReader(old_witness),
                                     expected=old_pin).suffix_match)  # limitation, HOLD only

    def test_scope_clock_and_pending(self):
        self.checkpoint()
        for changes in (dict(scope=replace(self.h.head.scope, principal_id='demo-other')),
                        dict(clock=replace(self.h.b.f.clock, now_tick=95)),
                        dict(clock=replace(self.h.b.f.clock, witness_epoch=5))):
            self.assertFalse(self.inspect(**changes).suffix_match)
        _, self.h.latest = self.h.stage(self.h.snapshot(8))
        self.assertFalse(self.inspect().suffix_match)
        with self.assertRaises(ValueError):
            c.prepare_checkpoint(self.path, self.f.reader, self.h.latest, self.f.pub)

    def test_recovery_epoch_suffix_without_new_generation(self):
        self.checkpoint()
        rec = replace(self.h.head, sequence=self.h.head.sequence+1,
                      previous_sha=self.h.latest.record_sha, recovery_epoch=2)
        self.h.latest = self.f.append(rec, self.h.latest.record_sha)
        review = self.inspect()
        self.assertTrue(review.suffix_match)
        self.assertEqual((review.snapshot_suffix, review.witness_suffix), (0, 1))

    def test_removed_revision_cannot_rebind_after_checkpoint(self):
        original = self.h.b.store.snapshot
        removed = replace(original, nodes=original.nodes[:2], acl=replace(original.acl, acl_revision=8))
        self.append(removed)
        self.checkpoint()
        self.append(replace(removed, nodes=(*removed.nodes, replace(original.nodes[2], digest='e'*64)),
                            acl=replace(removed.acl, acl_revision=9)), bypass=True)
        self.assertFalse(self.inspect().suffix_match)

    def test_tombstone_resurrection_rejected_after_checkpoint(self):
        self.append(self.h.b.store.revoke())
        self.checkpoint()
        self.append(self.h.snapshot(9), bypass=True)
        self.assertFalse(self.inspect().suffix_match)

    def test_suffix_snapshot_tamper_rejected(self):
        self.checkpoint()
        self.h.advance(8)
        self.h.rewrite(2, 9)
        self.assertFalse(self.inspect().suffix_match)

    def test_anchor_snapshot_tamper_rejected(self):
        self.h.advance(8)
        self.checkpoint()
        self.h.rewrite(2, 9)
        self.assertFalse(self.inspect().suffix_match)

    def test_prefix_payload_tamper_requires_original_full_audit(self):
        self.h.advance(8)
        self.checkpoint()
        self.h.rewrite(1, 6)
        self.assertTrue(self.inspect().suffix_match)  # explicitly not a prefix audit
        self.assertFalse(self.h.review().structural_match)
        with self.assertRaises(ValueError):
            c.prepare_checkpoint(self.path, self.f.reader, self.h.latest, self.f.pub)

    def test_missing_prefix_row_rejected(self):
        self.h.advance(8)
        self.checkpoint()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DELETE FROM snapshots WHERE generation=1')
        self.assertFalse(self.inspect().suffix_match)

    def test_witness_suffix_signature_tamper_rejected(self):
        self.checkpoint()
        self.h.advance(8)
        with closing(sqlite3.connect(self.f.path)) as db, db:
            db.execute('DROP TRIGGER no_update')
            db.execute('UPDATE memory_witness SET signature=? WHERE sequence=2', (b'x'*64,))
        self.assertFalse(self.inspect().suffix_match)

    def test_witness_changes_between_observations_rejected(self):
        self.checkpoint()
        original = c._snapshot_suffix
        def interleave(*args):
            result = original(*args)
            self.h.advance(8)
            return result
        with patch.object(c, '_snapshot_suffix', side_effect=interleave):
            self.assertFalse(self.inspect().suffix_match)

    def test_valid_revocation_is_retained_and_never_grants(self):
        self.checkpoint()
        self.append(self.h.b.store.revoke())
        self.assertTrue(self.inspect().suffix_match)
        self.assertEqual(self.h.review().reason, 'STALE_HOLD')
        self.checkpoint()
        self.assertEqual(self.inspect().snapshot_suffix, 0)

    def test_prefix_witness_signature_requires_full_audit(self):
        self.h.advance(8)
        self.checkpoint()
        with closing(sqlite3.connect(self.f.path)) as db, db:
            db.execute('DROP TRIGGER no_update')
            db.execute('UPDATE memory_witness SET signature=? WHERE sequence=1', (b'x'*64,))
        self.assertTrue(self.inspect().suffix_match)
        self.assertFalse(self.h.review().structural_match)

    def test_missing_witness_prefix_row_rejected(self):
        self.h.advance(8)
        self.checkpoint()
        with closing(sqlite3.connect(self.f.path)) as db, db:
            db.execute('DROP TRIGGER no_delete')
            db.execute('DELETE FROM memory_witness WHERE sequence=1')
        self.assertFalse(self.inspect().suffix_match)

    def test_accounted_byte_bound_for_suffix(self):
        self.checkpoint()
        accounted = self.inspect().accounted_bytes
        self.h.advance(8)
        with patch.object(s, 'HISTORY_BYTES', accounted):
            self.assertFalse(self.inspect().suffix_match)

    def test_storage_limit_holds_no_pruning(self):
        self.checkpoint()
        before = self.path.read_bytes(), self.f.path.read_bytes()
        with patch.object(s, 'HISTORY_LIMIT', 1):
            self.assertEqual(self.inspect().retention, 'LIMIT_HOLD')
        with patch.object(c, 'MAX_CHECKPOINT_BYTES', 1):
            self.assertFalse(self.inspect().suffix_match)
            with self.assertRaises(ValueError):
                c.prepare_checkpoint(self.path, self.f.reader, self.h.latest, self.f.pub)
        self.assertEqual(before, (self.path.read_bytes(), self.f.path.read_bytes()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
