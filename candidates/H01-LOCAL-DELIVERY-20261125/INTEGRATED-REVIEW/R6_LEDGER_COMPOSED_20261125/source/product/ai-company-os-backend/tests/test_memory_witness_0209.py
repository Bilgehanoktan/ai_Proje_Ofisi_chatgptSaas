"""Actual disposable separate SQLite files and Ed25519 test key; no independent custody."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.core.agent_runtime import memory_witness as w
from app.engines.memory_engine.snapshot_store import publish_snapshot, _encode, SnapshotPin
import test_joint_context_0208 as fixture


class MemoryWitnessTests(TestCase):
    def setUp(self):
        self.j = fixture.JointContextTests()
        self.j.setUp()
        self.addCleanup(self.j.doCleanups)
        self.b = self.j.base
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)/'external.witness.sqlite'
        self.store = w.D0MemoryWitnessStore.create(self.path)
        self.key = Ed25519PrivateKey.generate()
        self.pub = self.key.public_key().public_bytes_raw()
        self.record = w.MemoryWitness(self.b.f.scope, 1, 1, 2, 4, self.b.pin, 80, 95)
        self.latest = self.append(self.record, None)
        self.reader = w.MemoryWitnessReader(self.path)

    def append(self, rec, previous):
        return self.store.append(rec, self.key.sign(w.witness_bytes(rec)), self.pub, previous)

    def next(self, **changes):
        return replace(self.record, sequence=2, previous_sha=w.witness_sha(self.record), **changes)

    def review(self, **changes):
        j, b = self.j, self.b
        args = dict(context=j.context, registry=b.registry, expected_digest=j.pin,
                    memory_path=b.store.path, current_run=b.f.run, current_lease=b.f.lease,
                    clock=b.f.clock, raw=j.raw, reader=self.reader,
                    expected_witness=self.latest, public_key=self.pub)
        args.update(changes)
        r = w.inspect_witnessed_context(**args)
        self.assertEqual(r.decision, 'DENY')
        for flag in ('retrieval_allowed', 'release_allowed', 'provider_call_allowed',
                     'dispatch_allowed', 'spend_allowed', 'independent_verified', 'retry_allowed'):
            self.assertIs(getattr(r, flag), False)
        return r

    def test_exact_read_only(self):
        before = self.path.read_bytes()
        self.assertTrue(self.review().structural_match)
        self.assertEqual(self.path.read_bytes(), before)

    def test_key_pin_mismatch(self):
        key = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
        self.assertFalse(self.review(public_key=key).structural_match)

    def test_wrong_external_pin(self):
        self.assertFalse(self.review(expected_witness=replace(self.latest, record_sha='0'*64)).structural_match)

    def test_expired(self):
        self.assertEqual(self.review(clock=replace(self.b.f.clock, now_tick=95)).reason, 'MEMORY_WITNESS_CONTEXT_HOLD')

    def test_future(self):
        self.assertEqual(self.review(clock=replace(self.b.f.clock, now_tick=79)).reason, 'MEMORY_WITNESS_CONTEXT_HOLD')

    def test_policy_epoch(self):
        self.assertEqual(self.review(clock=replace(self.b.f.clock, policy_epoch=3)).reason, 'MEMORY_WITNESS_CONTEXT_HOLD')

    def test_witness_epoch(self):
        self.assertEqual(self.review(clock=replace(self.b.f.clock, witness_epoch=5)).reason, 'MEMORY_WITNESS_CONTEXT_HOLD')

    def test_wrong_scope(self):
        run = replace(self.b.f.run, scope=replace(self.b.f.scope, principal_id='demo-other'))
        self.assertEqual(self.review(current_run=run).reason, 'MEMORY_WITNESS_CONTEXT_HOLD')

    def test_pending_blocks_even_old_matching_snapshot(self):
        future = replace(self.b.pin, generation=2, digest='d'*64)
        rec = self.next(pending=future)
        latest = self.append(rec, self.latest.record_sha)
        self.assertEqual(self.review(expected_witness=latest).reason, 'MEMORY_WITNESS_PENDING_HOLD')
        self.assertFalse(self.review().structural_match)

    def test_pending_cannot_clear_on_absence(self):
        rec = self.next(pending=replace(self.b.pin, generation=2, digest='d'*64))
        latest = self.append(rec, self.latest.record_sha)
        with self.assertRaisesRegex(ValueError, 'PENDING'):
            self.append(replace(rec, sequence=3, previous_sha=latest.record_sha, pending=None), latest.record_sha)
        self.assertEqual(self.review(expected_witness=latest).reason, 'MEMORY_WITNESS_PENDING_HOLD')

    def test_restore_memory_with_current_external_head(self):
        old = self.b.store.path.with_name('old.d0.sqlite')
        old.write_bytes(self.b.store.path.read_bytes())
        new = publish_snapshot(self.b.store.path, self.b.store.revoke(), self.b.pin)
        pending = self.next(pending=new)
        p = self.append(pending, self.latest.record_sha)
        ready = replace(pending, sequence=3, previous_sha=p.record_sha, snapshot=new, pending=None)
        latest = self.append(ready, p.record_sha)
        self.assertEqual(self.review(memory_path=old, expected_witness=latest).reason, 'MEMORY_WITNESS_CONTEXT_HOLD')
        self.assertFalse(self.review(memory_path=old).structural_match)
        c = replace(self.j.context, memory_pin=new)
        self.assertEqual(self.review(expected_witness=latest, **self.j.repin(c)).reason, 'STALE_HOLD')

    def test_restore_both_with_current_external_pin(self):
        old = self.path.with_name('old.witness.sqlite')
        old.write_bytes(self.path.read_bytes())
        latest = self.append(self.next(recovery_epoch=2), self.latest.record_sha)
        self.assertFalse(self.review(reader=w.MemoryWitnessReader(old), expected_witness=latest).structural_match)
        # If all three trust inputs roll back, no local anti-restore proof exists.
        self.assertTrue(self.review(reader=w.MemoryWitnessReader(old)).structural_match)

    def test_append_during_joint_review(self):
        real = w.inspect_joint_context
        def interleave(*args):
            result = real(*args)
            self.append(self.next(recovery_epoch=2), self.latest.record_sha)
            return result
        with patch.object(w, 'inspect_joint_context', side_effect=interleave):
            self.assertFalse(self.review().structural_match)

    def test_cas(self):
        rec = self.next(recovery_epoch=2)
        latest = self.append(rec, self.latest.record_sha)
        with self.assertRaisesRegex(ValueError, 'CAS'):
            self.append(rec, self.latest.record_sha)
        self.assertTrue(self.review(expected_witness=latest).structural_match)

    def test_signature_tamper(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DROP TRIGGER no_update')
            db.execute('UPDATE memory_witness SET signature=?', (b'x'*64,))
        self.assertFalse(self.review().structural_match)

    def test_missing_file(self):
        p = self.path.with_name('absent.witness.sqlite')
        self.assertFalse(self.review(reader=w.MemoryWitnessReader(p)).structural_match)
        self.assertFalse(p.exists())

    def test_alias(self):
        p = self.path.with_name('alias.witness.sqlite')
        p.hardlink_to(self.b.store.path)
        self.assertEqual(self.review(reader=w.MemoryWitnessReader(p)).reason, 'MEMORY_WITNESS_SEPARATION_HOLD')

    def test_chain_forgery(self):
        with self.assertRaisesRegex(ValueError, 'CHAIN'):
            self.append(replace(self.next(recovery_epoch=2), previous_sha='f'*64), self.latest.record_sha)

    def test_illegal_direct_generation_advance(self):
        with self.assertRaisesRegex(ValueError, 'MONOTONIC'):
            self.append(self.next(snapshot=replace(self.b.pin, generation=2, digest='d'*64), recovery_epoch=2), self.latest.record_sha)

    def test_append_only(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('DELETE FROM memory_witness')
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('INSERT OR REPLACE INTO memory_witness SELECT * FROM memory_witness')

    def test_stage_before_memory_write_then_finalize(self):
        b = self.b
        snap = b.store.revoke()
        metadata, graph = _encode(snap)
        target = SnapshotPin(2, sha256(metadata.encode('ascii')).hexdigest(), graph)
        pending = self.next(pending=target)
        p = self.append(pending, self.latest.record_sha)
        self.assertEqual(self.review(expected_witness=p).reason, 'MEMORY_WITNESS_PENDING_HOLD')
        self.assertEqual(publish_snapshot(b.store.path, snap, b.pin), target)
        ready = replace(pending, sequence=3, previous_sha=p.record_sha, snapshot=target, pending=None)
        latest = self.append(ready, p.record_sha)
        c = replace(self.j.context, memory_pin=target)
        self.assertEqual(self.review(expected_witness=latest, **self.j.repin(c)).reason, 'STALE_HOLD')

    def test_concurrent_append_single_winner(self):
        barrier = Barrier(2, timeout=3)
        rec = self.next(recovery_epoch=2)
        def attempt():
            barrier.wait()
            try:
                return self.append(rec, self.latest.record_sha)
            except ValueError as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(attempt) for _ in range(2)]
            results = [f.result(timeout=5) for f in futures]
        winners = [x for x in results if type(x) is w.LatestWitnessPin]
        self.assertEqual(len(winners), 1)
        self.assertIn('MEMORY_WITNESS_CAS_HOLD', results)
        self.assertTrue(self.review(expected_witness=winners[0]).structural_match)

    def test_untrusted_reader_subclass_rejected(self):
        class ForgedReader(w.MemoryWitnessReader):
            def read_latest(self, expected, public_key):
                return self.record
        self.assertEqual(self.review(reader=ForgedReader(self.path)).reason, 'MEMORY_WITNESS_SEPARATION_HOLD')
