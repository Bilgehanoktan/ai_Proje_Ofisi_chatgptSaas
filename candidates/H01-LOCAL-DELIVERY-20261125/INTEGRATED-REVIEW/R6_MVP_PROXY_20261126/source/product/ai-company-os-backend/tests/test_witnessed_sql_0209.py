"""Original six-role candidate SQL mapping + witness guard on SQLite, not PG locks."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace, astuple
from pathlib import Path
import sqlite3
from threading import Barrier
from unittest import TestCase

from app.core.agent_runtime.lifecycle import RunState
from app.core.transaction.postgres_transition_mapping import (
    D0PostgresTransitionMapping, _lease, transaction_ref, verify_transition_rows,
)
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction, CommitOutcomeUnknown
from app.core.transaction.witnessed_mapping import WitnessedTransitionMapping
from app.engines.memory_engine.snapshot_store import publish_snapshot
import test_witnessed_t1_0209 as fixture

ROOT = Path(__file__).resolve().parents[3]
TABLES = ('run_heads', 'run_leases', 'run_mutations', 'run_audit', 'events', 'outbox', 'fences')


class Cursor:
    def __init__(self, db):
        self.c = db.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.c.close()

    def execute(self, sql, params=()):
        return self.c.execute(sql.replace('t1_candidate.', '').replace(' FOR UPDATE', '').replace('%s', '?'), params)

    def fetchone(self):
        return self.c.fetchone()


class Connection(fixture.FixtureConnection):
    def __init__(self, path, unknown=False, before_commit=None):
        self.db = sqlite3.connect(path, timeout=3)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('BEGIN IMMEDIATE')
        self.unknown = unknown
        self.before_commit = before_commit

    def cursor(self):
        return Cursor(self.db)

    def commit(self):
        if self.before_commit:
            self.before_commit()
        super().commit()


class FaultMapping(D0PostgresTransitionMapping):
    def __init__(self, lease, clock, fault=None):
        super().__init__(lease, clock)
        self.fault = fault

    def write_transition_role(self, c, role, i, before, target):
        super().write_transition_role(c, role, i, before, target)
        if self.fault:
            self.fault(role)


class WitnessedSqlTests(TestCase):
    def setUp(self):
        self.f = fixture.WitnessedT1Tests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.w = self.f.w
        self.i, self.before, self.target = self.f.intent, self.f.before, self.f.target
        self.path = self.w.path.with_name('actual-mapping.db')
        s, lease = self.before.scope, self.w.b.f.lease
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('PRAGMA foreign_keys=ON')
            for name in ('0192/candidate_event_outbox_fence.sql', '0193/candidate_run_head.sql', '0194/candidate_transition_roles.sql'):
                db.executescript((ROOT/'database'/name).read_text().replace('CREATE SCHEMA t1_candidate;', '').replace('t1_candidate.', ''))
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                       (*astuple(s), self.before.state.value, self.before.version, self.before.attempt))
            db.execute('INSERT INTO run_leases VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (s.tenant_id, s.company_id, s.environment_id, s.run_id, s.plan_revision,
                        s.task_id, s.agent_instance_id, s.principal_id, *astuple(lease)[1:]))
        self.initial = self.dump()

    def dump(self):
        with closing(sqlite3.connect(self.path)) as db:
            return tuple(tuple(db.execute('SELECT * FROM '+t)) for t in TABLES)

    def execute(self, fault=None, unknown=False, before_commit=None):
        w, f = self.w, self.w.b.f
        original = FaultMapping(f.lease, lambda: f.clock, fault)
        adapter = WitnessedTransitionMapping(original, w.j.context, w.b.registry, w.latest, self.f.binding,
            w.b.store.path, w.reader, w.pub, w.j.raw, lambda c: (_lease(c, self.i, lock=True), f.clock, w.latest))
        co = LogicalT1Coordinator(lambda: postgres_transaction(lambda: Connection(self.path, unknown, before_commit), adapter))
        return co.commit_transition(self.i, self.before, self.target)

    def exact_readback(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON')
            with Cursor(db) as c:
                verify_transition_rows(c, self.i, self.before, self.target, self.w.b.f.lease)

    def test_original_six_role_sql_commit(self):
        r = self.execute()
        self.assertEqual(r.transaction_ref, transaction_ref(self.i))
        self.exact_readback()
        self.assertEqual(tuple(len(x) for x in self.dump()), (1,1,1,1,1,1,1))

    def test_memory_revocation_rolls_back_all_original_roles(self):
        b = self.w.b
        def fault(role):
            if role == 'AUDIT':
                publish_snapshot(b.store.path, b.store.revoke(), b.pin)
        with self.assertRaisesRegex(ValueError, 'CAS_HOLD'):
            self.execute(fault=fault)
        self.assertEqual(self.dump(), self.initial)

    def test_witness_epoch_change_rolls_back_all_original_roles(self):
        w = self.w
        def fault(role):
            if role == 'AUDIT':
                w.append(w.next(recovery_epoch=2), w.latest.record_sha)
        with self.assertRaisesRegex(ValueError, 'WITNESS'):
            self.execute(fault=fault)
        self.assertEqual(self.dump(), self.initial)

    def test_unknown_original_commit_readback_no_retry(self):
        with self.assertRaises(CommitOutcomeUnknown):
            self.execute(unknown=True)
        self.exact_readback()
        before = self.dump()
        with self.assertRaises(ValueError):
            self.execute()
        self.assertEqual(self.dump(), before)

    def test_concurrent_original_writers_single_winner(self):
        barrier = Barrier(2, timeout=3)
        def compete():
            barrier.wait()
            try:
                return self.execute().transaction_ref
            except ValueError as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(compete) for _ in range(2)]
            results = [j.result(timeout=5) for j in jobs]
        self.assertCountEqual(results, [transaction_ref(self.i), 'D0_HEAD_CAS_HOLD'])
        self.exact_readback()

    def test_persisted_lease_drift_denies(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE run_leases SET fence=fence+1')
        before = self.dump()
        with self.assertRaisesRegex(ValueError, 'REFERENCE_MISMATCH'):
            self.execute()
        self.assertEqual(self.dump(), before)

    def test_final_check_to_commit_gap_remains(self):
        # Deliberately interleave after the last check, before actual COMMIT.
        # D0 state persists; this does not authorize a provider effect.
        w = self.w
        def interleave():
            w.append(w.next(recovery_epoch=2), w.latest.record_sha)
        self.execute(before_commit=interleave)
        self.exact_readback()
        self.assertFalse(w.review().structural_match)
