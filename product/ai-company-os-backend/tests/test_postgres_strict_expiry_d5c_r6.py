"""D0 strict-route denial and unchanged transport regression; not PostgreSQL."""
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager, closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState
from app.core.agent_runtime.transition_command import transition_digest
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.postgres_session import (
    CommitOutcomeUnknown, postgres_transaction, protected_postgres_transaction,
)

HOLD = 'T1_STRICT_COMMIT_EXPIRY_UNPROVEN_HOLD'
SCOPE = Scope('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY',
              'sha256:'+'a'*64, 'task', 'demo-run', 'demo-agent', 'demo-principal')
INTENT = LogicalIntent(SCOPE, Operation.STATE_MUTATION, 1, 'b'*64, 'effect',
                       'idem', 'grant', 'lease', None, 1, 1)


class StrictRoute(unittest.TestCase):
    def setUp(self):
        self.connect = Mock(side_effect=AssertionError('must not connect'))
        self.mapping = Mock()
        self.coordinator = LogicalT1Coordinator.for_protected_postgres(self.connect, self.mapping)
        self.addCleanup(self.connect.assert_not_called)
        self.addCleanup(lambda: self.assertEqual(self.mapping.mock_calls, []))

    def test_direct_denies_before_connection(self):
        with self.assertRaisesRegex(PermissionError, HOLD):
            protected_postgres_transaction(self.connect, self.mapping)

    def test_all_valid_operations_denied(self):
        for op in Operation:
            with self.subTest(op=op), self.assertRaisesRegex(PermissionError, HOLD):
                self.coordinator.commit(replace(INTENT, operation=op, budget_ref='budget'))

    def test_bound_transition_denied(self):
        before = RunObservation(SCOPE, RunState.RUNNING, 1, 1)
        target = RunState.VERIFYING
        intent = replace(INTENT, request_digest=transition_digest(before, target))
        with self.assertRaisesRegex(PermissionError, HOLD):
            self.coordinator.commit_transition(intent, before, target)

    def test_no_legacy_fallback(self):
        with patch('app.core.transaction.postgres_session.postgres_transaction') as legacy:
            with self.assertRaisesRegex(PermissionError, HOLD):
                self.coordinator.commit(INTENT)
            legacy.assert_not_called()

    def test_invalid_intent_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'T1_INTENT_INVALID'):
            self.coordinator.commit(replace(INTENT, request_digest='invalid'))

    def test_missing_budget_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'T1_BUDGET_REFERENCE_MISSING'):
            self.coordinator.commit(replace(INTENT, operation=Operation.ADMISSION))


class SQLiteShim:
    """Real disposable SQLite transaction; transport API shim, no PG claims."""
    autocommit = False

    def __init__(self, path, fault=None):
        self.db = sqlite3.connect(path)
        self.fault = fault
        self.commits = self.rollbacks = self.closes = 0

    @contextmanager
    def cursor(self):
        with closing(self.db.cursor()) as cur:
            yield cur
        if self.fault == 'cursor_exit':
            raise RuntimeError('cursor exit failed')

    def commit(self):
        self.commits += 1
        if self.fault == 'before_commit':
            raise RuntimeError('commit failed before write')
        self.db.commit()
        if self.fault == 'after_commit':
            raise RuntimeError('commit ACK lost')

    def rollback(self):
        self.rollbacks += 1
        self.db.rollback()

    def close(self):
        self.closes += 1
        self.db.close()
        if self.fault == 'close':
            raise RuntimeError('close failed')


class LegacyTransport(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)/'probe.sqlite'
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('CREATE TABLE probe (id int PRIMARY KEY)')
            db.commit()

    def rows(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute('SELECT id FROM probe').fetchall()

    def run_write(self, fault=None):
        c = SQLiteShim(self.path, fault)
        self.connection = c
        self.connect = Mock(return_value=c)
        with postgres_transaction(self.connect, None) as session:
            session.cursor.execute('INSERT INTO probe VALUES (1)')
            if fault == 'body':
                raise ValueError('body failure')

    def counts(self, commit, rollback, close=1):
        self.connect.assert_called_once_with()
        self.assertEqual((self.connection.commits, self.connection.rollbacks,
                          self.connection.closes), (commit, rollback, close))

    def test_commit_readback(self):
        self.run_write()
        self.assertEqual(self.rows(), [(1,)])
        self.counts(1, 0)

    def test_body_rollback(self):
        with self.assertRaisesRegex(ValueError, 'body failure'):
            self.run_write('body')
        self.assertEqual(self.rows(), [])
        self.counts(0, 1)

    def test_cursor_exit_rollback(self):
        with self.assertRaisesRegex(RuntimeError, 'cursor exit failed'):
            self.run_write('cursor_exit')
        self.assertEqual(self.rows(), [])
        self.counts(0, 1)

    def test_unknown_before_commit_no_retry(self):
        with self.assertRaisesRegex(CommitOutcomeUnknown, 'T1_COMMIT_OUTCOME_UNKNOWN'):
            self.run_write('before_commit')
        self.assertEqual(self.rows(), [])
        self.counts(1, 0)

    def test_unknown_after_commit_no_retry(self):
        with self.assertRaisesRegex(CommitOutcomeUnknown, 'T1_COMMIT_OUTCOME_UNKNOWN'):
            self.run_write('after_commit')
        self.assertEqual(self.rows(), [(1,)])
        self.counts(1, 0)

    def test_close_unknown_no_retry(self):
        with self.assertRaisesRegex(CommitOutcomeUnknown, 'T1_CLOSE_AFTER_COMMIT_RECONCILE'):
            self.run_write('close')
        self.assertEqual(self.rows(), [(1,)])
        self.counts(1, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
