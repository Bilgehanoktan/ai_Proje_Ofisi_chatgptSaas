"""MEM-05D: actual disposable stores, original fixtures, no independent authority."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import json
import sqlite3
from unittest import TestCase, main
from unittest.mock import patch

from app.core.agent_runtime import memory_checkpoint as c, memory_witness as w
from app.core.agent_runtime import memory_recovery_review as recovery
from app.core.agent_runtime import memory_gateway_review as bridge
from app.core.agent_runtime.joint_context import JointContext, joint_context_digest
from app.core.agent_runtime.lifecycle import RunState
from app.engines.memory_engine import snapshot_store as s
from app.engines.model_gateway.durable_receipt_adapter import owner_snapshot_digest
import test_memory_history_w5_mem03 as fixture
import test_memory_gateway_05c_r1 as gateway_fixture


class MemoryRecoveryTests(TestCase):
    def setUp(self):
        self.h = fixture.HistoryCommitmentTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.f, self.b = self.h.f, self.h.b
        self.path = self.b.store.path
        self.checkpoint()

    def checkpoint(self):
        self.body = c.prepare_checkpoint(self.path, self.f.reader, self.h.latest, self.f.pub)
        self.signature = self.f.key.sign(self.body)
        self.pin = sha256(self.body).hexdigest()

    def signed(self, body):
        return dict(checkpoint_body=body, checkpoint_signature=self.f.key.sign(body),
                    checkpoint_sha=sha256(body).hexdigest())

    def review(self, **changes):
        args = dict(path=self.path, reader=self.f.reader, expected_witness=self.h.latest,
                    public_key=self.f.pub, checkpoint_body=self.body, checkpoint_signature=self.signature,
                    checkpoint_sha=self.pin, current_run=self.b.f.run, current_lease=self.b.f.lease,
                    lease_reference=self.b.f.lease, clock=self.b.f.clock)
        args.update(changes)
        r = recovery.inspect_memory_recovery(**args)
        self.assertEqual(r.decision, 'HOLD')
        self.assertIs(r.quarantine_required, True)
        for flag in ('retrieval_allowed', 'release_allowed', 'provider_call_allowed', 'dispatch_allowed',
                     'spend_allowed', 'settlement_allowed', 'transition_allowed', 'retry_allowed',
                     'replay_allowed', 'publish_allowed', 'clear_pending_allowed', 'prune_allowed',
                     'independent_verified', 'atomicity_verified'):
            self.assertIs(getattr(r, flag), False)
        for name in ('raw', 'snapshot', 'checkpoint_body', 'pending_pin', 'receipt', 'signature'):
            self.assertFalse(hasattr(r, name))
        return r

    def assert_match(self, review, state, reason):
        self.assertEqual((review.pending_observation, review.reason), (state, reason))
        self.assertTrue(review.history_match and review.checkpoint_match)

    def assert_hold(self, review):
        self.assertFalse(review.history_match or review.checkpoint_match)
        self.assertEqual(review.pending_observation, 'UNVERIFIED')

    def stage(self, snapshot):
        pending, latest = self.h.stage(snapshot)
        self.h.latest = latest
        return pending

    def test_clean_head_old_checkpoint_full_audit_read_only(self):
        self.h.advance(8)
        self.h.advance(10)
        before = self.path.read_bytes(), self.f.path.read_bytes()
        with patch.object(s, '_review_history', wraps=s._review_history) as audit, \
             patch.object(c, 'inspect_checkpoint_suffix', side_effect=AssertionError('suffix substituted')):
            self.assert_match(self.review(), 'NONE_OBSERVED', 'D0_MEMORY_RECOVERY_HEAD_MATCH_ONLY')
        self.assertEqual(audit.call_count, 2)
        self.assertEqual(before, (self.path.read_bytes(), self.f.path.read_bytes()))

    def test_pending_base_absence_is_not_rollback(self):
        pending = self.stage(self.h.snapshot(8))
        before = self.path.read_bytes(), self.f.path.read_bytes()
        with patch.object(s, 'publish_snapshot', side_effect=AssertionError('writer called')), \
             patch.object(w.D0MemoryWitnessStore, 'append', side_effect=AssertionError('publisher called')):
            self.assert_match(self.review(), 'BASE_ONLY', 'D0_MEMORY_RECOVERY_PENDING_BASE_ABSENCE_NOT_PROOF')
        self.assertEqual(self.f.reader.read_latest(self.h.latest, self.f.pub), pending)
        self.assertEqual(before, (self.path.read_bytes(), self.f.path.read_bytes()))

    def test_pending_target_exact_match_does_not_finalize(self):
        snapshot = self.b.store.revoke()
        pending = self.stage(snapshot)
        self.assertEqual(s.publish_snapshot(self.path, snapshot, self.h.head.snapshot), pending.pending)
        before = self.path.read_bytes(), self.f.path.read_bytes()
        with patch.object(s, 'publish_snapshot', side_effect=AssertionError('writer called')), \
             patch.object(w.D0MemoryWitnessStore, 'append', side_effect=AssertionError('publisher called')):
            self.assert_match(self.review(), 'TARGET_OBSERVED', 'D0_MEMORY_RECOVERY_PENDING_TARGET_MATCH_ONLY')
        self.assertEqual(self.f.reader.read_latest(self.h.latest, self.f.pub), pending)
        self.assertEqual(before, (self.path.read_bytes(), self.f.path.read_bytes()))

    def test_owner_fixture_finalization_observed_without_grant(self):
        snapshot = self.h.snapshot(8)
        pending = self.stage(snapshot)
        s.publish_snapshot(self.path, snapshot, self.h.head.snapshot)
        old_pin = self.h.latest
        ready = replace(pending, sequence=pending.sequence+1, previous_sha=old_pin.record_sha,
                        snapshot=pending.pending, pending=None)
        self.h.latest = self.f.append(ready, old_pin.record_sha)
        self.assert_match(self.review(), 'NONE_OBSERVED', 'D0_MEMORY_RECOVERY_HEAD_MATCH_ONLY')
        self.assert_hold(self.review(expected_witness=old_pin))

    def test_wrong_pending_target_rejected(self):
        self.stage(self.h.snapshot(8))
        s.publish_snapshot(self.path, self.h.snapshot(9), self.h.head.snapshot)
        r = self.review()
        self.assert_hold(r)
        self.assertEqual(r.reason, 'MEMORY_RECOVERY_HEAD_MISMATCH_HOLD')

    def test_pending_target_with_invalid_history_rejected(self):
        self.h.advance(8)
        snapshot = self.h.snapshot(7)  # signed target with decreasing ACL revision
        pending = self.stage(snapshot)
        metadata, graph = s._encode(snapshot)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)',
                       (pending.pending.generation, pending.pending.digest, graph, metadata, snapshot.raw))
        self.assert_hold(self.review())

    def test_unsigned_successor_without_pending_rejected(self):
        s.publish_snapshot(self.path, self.h.snapshot(8), self.h.head.snapshot)
        self.assert_hold(self.review())

    def test_pending_target_payload_tamper_rejected(self):
        snapshot = self.h.snapshot(8)
        self.stage(snapshot)
        s.publish_snapshot(self.path, snapshot, self.h.head.snapshot)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE snapshots SET raw=? WHERE generation=2', (b'wrong',))
        self.assert_hold(self.review())

    def test_stale_restore_current_external_references(self):
        old_memory = self.path.with_name('old.d0.sqlite')
        old_witness = self.f.path.with_name('old.witness.sqlite')
        old_memory.write_bytes(self.path.read_bytes())
        old_witness.write_bytes(self.f.path.read_bytes())
        self.h.advance(8)
        reader = w.MemoryWitnessReader(old_witness)
        for changes in (dict(path=old_memory), dict(reader=reader), dict(path=old_memory, reader=reader)):
            self.assert_hold(self.review(**changes))

    def test_rollback_of_both_stores_and_all_refs_is_residual_hold(self):
        old_memory = self.path.with_name('old.d0.sqlite')
        old_witness = self.f.path.with_name('old.witness.sqlite')
        old_memory.write_bytes(self.path.read_bytes())
        old_witness.write_bytes(self.f.path.read_bytes())
        old_pin = self.h.latest
        self.h.advance(8)
        self.assert_match(self.review(path=old_memory, reader=w.MemoryWitnessReader(old_witness),
                                      expected_witness=old_pin), 'NONE_OBSERVED',
                          'D0_MEMORY_RECOVERY_HEAD_MATCH_ONLY')

    def test_bad_checkpoint_signature_digest_and_external_witness(self):
        for changes in (dict(checkpoint_signature=b'x'*64), dict(checkpoint_sha='0'*64),
                        dict(public_key=b'x'*32), dict(expected_witness=None),
                        dict(expected_witness=replace(self.h.latest, recovery_epoch=2))):
            self.assert_hold(self.review(**changes))

    def test_signed_wrong_checkpoint_summary_rejected(self):
        obj = json.loads(self.body)
        obj[3] += 1  # canonical and signed, but false retained byte count
        r = self.review(**self.signed(s._json(obj).encode('ascii')))
        self.assert_hold(r)
        self.assertEqual(r.reason, 'MEMORY_RECOVERY_CHECKPOINT_HOLD')

    def test_signed_anchor_from_other_chain_rejected(self):
        obj = json.loads(self.body)
        other = replace(self.h.head, issued_tick=self.h.head.issued_tick+1)
        obj[1] = w.witness_bytes(other).decode('ascii')
        self.assertEqual(self.review(**self.signed(s._json(obj).encode('ascii'))).reason,
                         'MEMORY_RECOVERY_CHECKPOINT_HOLD')

    def test_snapshot_prefix_tamper_despite_suffix_match(self):
        self.h.advance(8)
        self.checkpoint()
        self.h.rewrite(1, 6)
        suffix = c.inspect_checkpoint_suffix(self.path, self.f.reader, self.body, self.signature,
                    self.pin, self.h.latest, self.f.pub, self.b.f.scope, self.b.f.clock)
        self.assertTrue(suffix.suffix_match)
        self.assert_hold(self.review())

    def test_witness_prefix_tamper_despite_suffix_match(self):
        self.h.advance(8)
        self.checkpoint()
        with closing(sqlite3.connect(self.f.path)) as db, db:
            db.execute('DROP TRIGGER no_update')
            db.execute('UPDATE memory_witness SET signature=? WHERE sequence=1', (b'x'*64,))
        suffix = c.inspect_checkpoint_suffix(self.path, self.f.reader, self.body, self.signature,
                    self.pin, self.h.latest, self.f.pub, self.b.f.scope, self.b.f.clock)
        self.assertTrue(suffix.suffix_match)
        self.assert_hold(self.review())

    def test_missing_history_row_rejected(self):
        self.h.advance(8)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DELETE FROM snapshots WHERE generation=1')
        self.assert_hold(self.review())

    def test_runtime_lease_clock_and_scope_drift(self):
        run, lease, clock = self.b.f.run, self.b.f.lease, self.b.f.clock
        for changes in (dict(current_run=replace(run, version=4)), dict(current_run=replace(run, attempt=2)),
                        dict(current_run=replace(run, state=RunState.FAILED)),
                        dict(current_run=replace(run, attempt=True)),
                        dict(current_run=replace(run, scope=replace(run.scope, principal_id='demo-other'))),
                        dict(current_lease=replace(lease, fence=2)), dict(lease_reference=None),
                        dict(clock=replace(clock, now_tick=95)), dict(clock=replace(clock, policy_epoch=3)),
                        dict(clock=replace(clock, witness_epoch=5))):
            self.assert_hold(self.review(**changes))

    def test_recovery_epoch_advance_with_same_snapshot(self):
        old_pin = self.h.latest
        record = replace(self.h.head, sequence=self.h.head.sequence+1, previous_sha=old_pin.record_sha,
                         recovery_epoch=self.h.head.recovery_epoch+1)
        self.h.latest = self.f.append(record, old_pin.record_sha)
        self.assert_match(self.review(), 'NONE_OBSERVED', 'D0_MEMORY_RECOVERY_HEAD_MATCH_ONLY')
        self.assert_hold(self.review(expected_witness=old_pin))

    def test_missing_store_and_hardlink_alias(self):
        absent = self.path.with_name('absent.d0.sqlite')
        self.assert_hold(self.review(path=absent))
        self.assertFalse(absent.exists())
        alias = self.f.path.with_name('alias.witness.sqlite')
        alias.hardlink_to(self.path)
        self.assert_hold(self.review(reader=w.MemoryWitnessReader(alias)))

    def test_pending_target_appears_between_memory_reads(self):
        snapshot = self.h.snapshot(8)
        self.stage(snapshot)
        real = recovery._observe_memory
        count = 0
        def interleave(*args):
            nonlocal count
            result = real(*args)
            count += 1
            if count == 1:
                s.publish_snapshot(self.path, snapshot, self.h.head.snapshot)
            return result
        with patch.object(recovery, '_observe_memory', side_effect=interleave):
            self.assertEqual(self.review().reason, 'MEMORY_RECOVERY_CHANGED_HOLD')
        self.assertEqual(count, 2)

    def test_witness_changes_between_memory_reads(self):
        real = recovery._observe_memory
        def interleave(*args):
            result = real(*args)
            record = replace(self.h.head, sequence=2, previous_sha=self.h.latest.record_sha,
                             recovery_epoch=2)
            self.f.append(record, self.h.latest.record_sha)
            return result
        with patch.object(recovery, '_observe_memory', side_effect=interleave):
            r = self.review()
            self.assert_hold(r)
            self.assertEqual(r.reason, 'MEMORY_RECOVERY_CHANGED_HOLD')

    def test_mem05c_r2_stays_hold_after_pending_target_observed(self):
        g = gateway_fixture.MemoryGatewayTests()
        g.setUp()
        self.addCleanup(g.doCleanups)
        j = JointContext(g.b.pin, g.ctx.envelope)
        pin = joint_context_digest(j, g.ctx.registry)
        body = c.prepare_checkpoint(g.b.store.path, g.w.reader, g.w.latest, g.w.pub)
        args = (j, pin, g.ctx, g.b.store.path, g.w.reader)
        owner = (g.w.pub, g.owner, g.owner, g.owner.budget, owner_snapshot_digest(g.owner))
        self.assertTrue(bridge.inspect_memory_gateway(*args, g.w.latest, *owner).structural_match)
        snapshot = g.b.store.revoke()
        metadata, graph = s._encode(snapshot)
        target = s.SnapshotPin(2, sha256(metadata.encode('ascii')).hexdigest(), graph)
        pending = replace(g.w.record, sequence=2, previous_sha=g.w.latest.record_sha, pending=target)
        latest = g.w.append(pending, g.w.latest.record_sha)
        self.assertEqual(s.publish_snapshot(g.b.store.path, snapshot, g.b.pin), target)
        r = recovery.inspect_memory_recovery(g.b.store.path, g.w.reader, latest, g.w.pub,
                    body, g.w.key.sign(body), sha256(body).hexdigest(), g.f.run, g.f.lease, g.f.lease, g.f.clock)
        self.assert_match(r, 'TARGET_OBSERVED', 'D0_MEMORY_RECOVERY_PENDING_TARGET_MATCH_ONLY')
        self.assertFalse(r.publish_allowed or r.retry_allowed or r.dispatch_allowed)
        self.assertFalse(bridge.inspect_memory_gateway(*args, latest, *owner).structural_match)


if __name__ == '__main__':
    main(verbosity=2)
