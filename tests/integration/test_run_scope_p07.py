"""P07: exact existing D0 run-head SQL on disposable persisted SQLite.

Only schema qualifier and parameter markers are translated. This exercises
PostgresRunRepository.read/advance, not PostgreSQL locking, T1 or authority.
Clock and lease references are synthetic test values, never trusted sources.
Run: python -B tests/integration/test_run_scope_p07.py -v
"""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import hashlib
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'product/ai-company-os-backend'))
from app.core.agent_runtime.lifecycle import (
    Scope, RunObservation, RunState, LeaseObservation, ClockSample,
    inspect_transition, inspect_lease,
)
from app.core.agent_runtime.postgres_run import PostgresRunRepository

SCOPE = Scope('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY',
              'sha256:' + 'a' * 64, 'task-p07', 'demo-run-p07',
              'demo-agent-p07', 'demo-principal-p07')
BEFORE = RunObservation(SCOPE, RunState.PLANNING, 4, 1)
LEASE = LeaseObservation(SCOPE, 'lease-p07', 'grant-p07', 1, 1, 7, 2, 3, 20, 9)
CLOCK = ClockSample(10, 2, 3, 5)


class SQLiteReadWriteCursor:
    def __init__(self, db):
        self.cursor = db.cursor()

    def execute(self, sql, params=()):
        if 'FOR UPDATE' in sql:
            raise AssertionError('PostgreSQL locking is outside this test')
        return self.cursor.execute(sql.replace('t1_candidate.', '').replace('%s', '?'), params)

    def fetchone(self):
        return self.cursor.fetchone()


class PersistedScopeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='aicos-p07-')
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'scope.d0.sqlite'
        self.repo = PostgresRunRepository()
        ddl = (ROOT / 'database/0193/candidate_run_head.sql').read_text()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executescript(ddl.replace('t1_candidate.', ''))
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                       (SCOPE.tenant_id, SCOPE.company_id, SCOPE.environment_id,
                        SCOPE.plan_revision, SCOPE.task_id, SCOPE.run_id,
                        SCOPE.agent_instance_id, SCOPE.principal_id,
                        BEFORE.state.value, BEFORE.version, BEFORE.attempt))

    def read(self, scope=SCOPE):
        with closing(sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True)) as db:
            return self.repo.read(SQLiteReadWriteCursor(db), scope)

    def digest(self):
        return hashlib.sha256(self.path.read_bytes()).hexdigest()

    def preview(self, **kwargs):
        fields = dict(run=self.read(), target=RunState.RUNNING, expected_version=4,
                      lease=LEASE, reference=LEASE, clock=CLOCK)
        fields.update(kwargs)
        result = inspect_transition(**fields)
        self.assertFalse(result.commit_allowed)
        self.assertFalse(result.dispatch_allowed)
        return result

    def test_exact_scope_reopens_persisted_head(self):
        digest = self.digest()
        self.assertEqual(self.read(), BEFORE)
        self.assertEqual(self.read(), BEFORE)
        self.assertEqual(self.digest(), digest)

    def test_plan_task_run_agent_principal_mismatch(self):
        digest = self.digest()
        for field, value in (('plan_revision', 'sha256:' + 'b' * 64),
                             ('task_id', 'other-task'), ('run_id', 'demo-other-run'),
                             ('agent_instance_id', 'demo-other-agent'),
                             ('principal_id', 'demo-other-principal')):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'RUN_HEAD_NOT_FOUND'):
                self.read(replace(SCOPE, **{field: value}))
        self.assertEqual(self.digest(), digest)

    def test_tenant_company_environment_mismatch(self):
        for field, value in (('tenant_id', 'other-tenant'), ('company_id', 'other-company'),
                             ('environment_id', 'PROD')):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'RUN_SCOPE_INVALID'):
                self.read(replace(SCOPE, **{field: value}))

    def test_cas_persists_and_reopens(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            result = self.repo.advance(SQLiteReadWriteCursor(db), BEFORE, RunState.RUNNING)
        self.assertEqual(result, replace(BEFORE, state=RunState.RUNNING, version=5))
        self.assertEqual(self.read(), result)

    def test_cas_rejects_stale_version_and_attempt(self):
        digest = self.digest()
        for bad in (replace(BEFORE, version=3), replace(BEFORE, attempt=0)):
            with self.subTest(bad=bad), closing(sqlite3.connect(self.path)) as db, db:
                with self.assertRaisesRegex(ValueError, 'RUN_HEAD_CAS_MISMATCH'):
                    self.repo.advance(SQLiteReadWriteCursor(db), bad, RunState.RUNNING)
        self.assertEqual(self.read(), BEFORE)
        self.assertEqual(self.digest(), digest)

    def test_fresh_sample_is_not_authority(self):
        result = inspect_lease(LEASE, LEASE, CLOCK)
        self.assertEqual((result.freshness, result.decision), ('FRESH', 'HOLD'))
        self.assertFalse(result.dispatch_allowed)
        self.assertEqual(self.preview().reason, 'T1_ATOMICITY_NOT_PROVEN')

    def test_missing_clock_or_reference(self):
        self.assertEqual(self.preview(clock=None).reason, 'CLOCK_SAMPLE_INVALID')
        self.assertEqual(self.preview(reference=None).reason, 'LEASE_REFERENCE_INVALID_OR_MISSING')

    def test_expiry_and_stale_heartbeat(self):
        self.assertEqual(self.preview(clock=replace(CLOCK, now_tick=20)).reason, 'LEASE_EXPIRED')
        self.assertEqual(self.preview(clock=replace(CLOCK, now_tick=15)).reason, 'HEARTBEAT_STALE')
        self.assertEqual(self.preview(clock=replace(CLOCK, now_tick=8)).reason, 'HEARTBEAT_IN_FUTURE')

    def test_policy_and_witness_epoch_deny(self):
        for clock, reason in ((replace(CLOCK, policy_epoch=3), 'ERR_POLICY_EPOCH_STALE'),
                              (replace(CLOCK, witness_epoch=4), 'ERR_WA_EPOCH_STALE')):
            with self.subTest(reason=reason):
                result = self.preview(clock=clock)
                self.assertEqual((result.decision, result.reason), ('DENY', reason))

    def test_lease_bound_to_persisted_scope(self):
        wrong = replace(LEASE, scope=replace(SCOPE, principal_id='demo-other-principal'))
        self.assertEqual(self.preview(lease=wrong, reference=wrong).reason, 'RUN_LEASE_BINDING_MISSING')
        result = self.preview(reference=wrong)
        self.assertEqual((result.decision, result.reason), ('DENY', 'LEASE_SCOPE_MISMATCH'))

    def test_renewal_fence_and_reference_mismatch(self):
        for change in ({'fence': 8}, {'lease_version': 2}, {'heartbeat_revision': 2}, {'grant_id': 'other-grant'}):
            with self.subTest(change=change):
                self.assertEqual(self.preview(reference=replace(LEASE, **change)).reason, 'LEASE_REFERENCE_MISMATCH')

    def test_unknown_result_and_stale_head_hold(self):
        self.assertEqual(self.preview(outcome_unknown=True).reason, 'ERR_PROVIDER_RESULT_UNKNOWN')
        self.assertEqual(self.preview(expected_version=3).reason, 'CAS_VERSION_MISMATCH_OR_EXHAUSTED')
        self.assertEqual(self.read(), BEFORE)


if __name__ == '__main__':
    unittest.main()
