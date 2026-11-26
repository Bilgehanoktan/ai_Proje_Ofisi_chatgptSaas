"""Selected synthetic tests; fake cursor and mapping, no PostgreSQL server."""
import unittest
from dataclasses import replace
from unittest.mock import Mock, MagicMock
from app.core.agent_runtime.lifecycle import Scope, RunState, RunObservation
from app.core.agent_runtime.transition_command import commit_transition, transition_digest
from app.core.agent_runtime.postgres_run import PostgresRunRepository
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.port import LogicalT1Coordinator, CommitReceipt
from app.core.transaction.postgres_session import postgres_transaction, CommitOutcomeUnknown

SCOPE = Scope('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY',
              'sha256:'+'a'*64, 'task', 'demo-run', 'demo-agent', 'demo-principal')
BEFORE = RunObservation(SCOPE, RunState.PLANNING, 4, 1)
TARGET = RunState.RUNNING
AFTER = replace(BEFORE, state=TARGET, version=5)
INTENT = LogicalIntent(SCOPE, Operation.STATE_MUTATION, 4,
                       transition_digest(BEFORE, TARGET), 'effect', 'idem', 'grant',
                       'lease', None, 1, 1)
ROLES = ['HEAD', 'MUTATION', 'FENCE', 'EVENT', 'OUTBOX', 'AUDIT']


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock(autocommit=False)
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.mapping = Mock()
        self.mapping.lock_transition.return_value = BEFORE
        self.mapping.read_transition.return_value = AFTER
        self.mapping.verify_write_set.return_value = CommitReceipt('tx', 5, INTENT.request_digest)
        self.coordinator = LogicalT1Coordinator(lambda: postgres_transaction(lambda: self.connection, self.mapping))

    def run_transition(self):
        return commit_transition(self.coordinator, BEFORE, TARGET, INTENT)

    def test_success(self):
        self.assertEqual(self.run_transition(), CommitReceipt('tx', 5, INTENT.request_digest))
        self.assertEqual([c.args[1] for c in self.mapping.write_transition_role.call_args_list], ROLES)
        self.mapping.lock_and_validate.assert_called_once_with(self.cursor, INTENT)
        self.mapping.lock_transition.assert_called_once_with(self.cursor, INTENT)
        self.mapping.read_transition.assert_called_once_with(self.cursor, INTENT)
        self.mapping.write_role.assert_not_called()
        self.connection.commit.assert_called_once()
        self.connection.rollback.assert_not_called()
        self.connection.close.assert_called_once()

    def test_stale_version(self):
        self.mapping.lock_transition.return_value = replace(BEFORE, version=3)
        with self.assertRaisesRegex(ValueError, 'PREIMAGE'):
            self.run_transition()
        self.mapping.write_transition_role.assert_not_called()
        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()

    def test_stale_state(self):
        self.mapping.lock_transition.return_value = replace(BEFORE, state=RunState.ADMITTED)
        with self.assertRaisesRegex(ValueError, 'PREIMAGE'):
            self.run_transition()
        self.mapping.write_transition_role.assert_not_called()

    def test_wrong_scope(self):
        self.mapping.lock_transition.return_value = replace(BEFORE, scope=replace(SCOPE, principal_id='demo-other'))
        with self.assertRaisesRegex(ValueError, 'PREIMAGE'):
            self.run_transition()

    def test_wrong_attempt(self):
        self.mapping.lock_transition.return_value = replace(BEFORE, attempt=0)
        with self.assertRaisesRegex(ValueError, 'PREIMAGE'):
            self.run_transition()

    def test_wrong_postimage(self):
        self.mapping.read_transition.return_value = BEFORE
        with self.assertRaisesRegex(ValueError, 'POSTIMAGE'):
            self.run_transition()
        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()

    def test_role_failure(self):
        self.mapping.write_transition_role.side_effect = RuntimeError('write failure')
        with self.assertRaisesRegex(RuntimeError, 'write failure'):
            self.run_transition()
        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()

    def test_bad_receipt(self):
        self.mapping.verify_write_set.return_value = CommitReceipt('tx', 6, INTENT.request_digest)
        with self.assertRaisesRegex(ValueError, 'RECEIPT'):
            self.run_transition()
        self.connection.rollback.assert_called_once()

    def test_unknown_commit(self):
        self.connection.commit.side_effect = OSError('connection lost')
        with self.assertRaisesRegex(CommitOutcomeUnknown, 'OUTCOME_UNKNOWN'):
            self.run_transition()
        self.connection.rollback.assert_not_called()
        self.connection.close.assert_called_once()

    def test_close_after_commit(self):
        self.connection.close.side_effect = OSError('close lost')
        with self.assertRaisesRegex(CommitOutcomeUnknown, 'CLOSE_AFTER_COMMIT'):
            self.run_transition()
        self.connection.commit.assert_called_once()

    def test_cleanup_does_not_mask_preimage_error(self):
        self.mapping.lock_transition.return_value = None
        self.connection.rollback.side_effect = OSError('rollback failed')
        self.connection.close.side_effect = OSError('close failed')
        with self.assertRaisesRegex(ValueError, 'PREIMAGE'):
            self.run_transition()

    def test_autocommit_rejected(self):
        self.connection.autocommit = True
        with self.assertRaisesRegex(ValueError, 'AUTOCOMMIT'):
            self.run_transition()
        self.mapping.lock_and_validate.assert_not_called()
        self.connection.commit.assert_not_called()

    def test_no_generic_fallback(self):
        old = Mock(spec=['commit'])
        with self.assertRaises(AttributeError):
            commit_transition(old, BEFORE, TARGET, INTENT)
        old.commit.assert_not_called()

    def test_approval_not_bypassed(self):
        waiting = replace(BEFORE, state=RunState.WAITING_APPROVAL)
        intent = replace(INTENT, request_digest=transition_digest(waiting, TARGET))
        with self.assertRaisesRegex(PermissionError, 'APPROVAL_HOLD'):
            commit_transition(self.coordinator, waiting, TARGET, intent)
        self.connection.cursor.assert_not_called()

    def test_terminal_not_bypassed(self):
        verifying = replace(BEFORE, state=RunState.VERIFYING)
        intent = replace(INTENT, request_digest=transition_digest(verifying, RunState.SUCCEEDED))
        with self.assertRaisesRegex(PermissionError, 'SPECIAL_TRANSITION'):
            commit_transition(self.coordinator, verifying, RunState.SUCCEEDED, intent)
        self.connection.cursor.assert_not_called()

    def test_digest_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'BINDING'):
            commit_transition(self.coordinator, BEFORE, TARGET, replace(INTENT, request_digest='b'*64))
        self.connection.cursor.assert_not_called()

    def test_legacy_generic_path(self):
        self.assertEqual(self.coordinator.commit(INTENT).committed_version, 5)
        self.assertEqual([c.args[1] for c in self.mapping.write_role.call_args_list], ROLES)
        self.mapping.lock_transition.assert_not_called()


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.repo = PostgresRunRepository()
        self.cursor = Mock()

    def test_lock_all_scope(self):
        self.cursor.fetchone.return_value = ('PLANNING', 4, 1)
        self.assertEqual(self.repo.lock(self.cursor, SCOPE), BEFORE)
        sql, args = self.cursor.execute.call_args.args
        self.assertTrue(sql.endswith('FOR UPDATE'))
        self.assertEqual(args, tuple(vars(SCOPE).values()))
        self.assertEqual(sql.count('%s'), 8)

    def test_read_missing(self):
        self.cursor.fetchone.return_value = None
        with self.assertRaisesRegex(ValueError, 'NOT_FOUND'):
            self.repo.read(self.cursor, SCOPE)

    def test_cas(self):
        self.cursor.fetchone.return_value = ('RUNNING', 5, 1)
        self.assertEqual(self.repo.advance(self.cursor, BEFORE, TARGET), AFTER)
        sql, args = self.cursor.execute.call_args.args
        self.assertIn('AND state=%s AND version=%s AND attempt=%s', sql)
        self.assertEqual(args, ('RUNNING', *vars(SCOPE).values(), 'PLANNING', 4, 1))
        self.assertEqual(sql.count('%s'), len(args))

    def test_cas_conflict(self):
        self.cursor.fetchone.return_value = None
        with self.assertRaisesRegex(ValueError, 'CAS_MISMATCH'):
            self.repo.advance(self.cursor, BEFORE, TARGET)

    def test_cas_wrong_postimage(self):
        self.cursor.fetchone.return_value = ('RUNNING', 6, 1)
        with self.assertRaisesRegex(ValueError, 'POSTIMAGE'):
            self.repo.advance(self.cursor, BEFORE, TARGET)

    def test_invalid_scope_never_queries(self):
        with self.assertRaisesRegex(ValueError, 'SCOPE'):
            self.repo.lock(self.cursor, replace(SCOPE, tenant_id='other'))
        self.cursor.execute.assert_not_called()

    def test_invalid_terminal_edge(self):
        with self.assertRaisesRegex(ValueError, 'EDGE'):
            self.repo.advance(self.cursor, BEFORE, RunState.SUCCEEDED)
        self.cursor.execute.assert_not_called()

    def test_invalid_approval_edge(self):
        with self.assertRaisesRegex(ValueError, 'EDGE'):
            self.repo.advance(self.cursor, replace(BEFORE, state=RunState.WAITING_APPROVAL), TARGET)
        self.cursor.execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()
