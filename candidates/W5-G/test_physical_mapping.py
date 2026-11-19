"""Actual SQLite SQL tests, not PostgreSQL/RLS or owner receipt acceptance."""
import hashlib
from pathlib import Path
import re
import sqlite3
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PINS = {
    'database/0193/candidate_run_head.sql': '180924e97ee1f31fa27332941a41e37fdf73017e',
    'database/0194/candidate_transition_roles.sql': '7b5d374bb7973b283e4fcfa0d796ed6128ef9d27',
    'database/0195/candidate_admission_budget.sql': 'd5dc6abc045da14ef42e88b4e85e50e9062a1b27',
    'database/0196L/candidate_lease_settlement.sql': 'e4c9a84ff705c39486579c393b1f3aaef9e34da9',
}
SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
PLAN = 'sha256:' + 'a' * 64
RUN = 'demo-run'
KEY = (*SCOPE, RUN)
SQL = re.sub(r'%\((\w+)\)s', r':\1', (HERE / 'run_level_receipt_diagnostic.sql').read_text())


def ddl_bytes(path):
    raw = (ROOT / path).read_bytes()
    actual = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
    if actual != PINS[path]:
        raise AssertionError(f'Pinned DDL mismatch: {path}')
    return raw


class PhysicalMappingTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.execute('PRAGMA foreign_keys=ON')
        for path in PINS:
            self.db.executescript(ddl_bytes(path).decode().replace('t1_candidate.', ''))
        self.insert('run_heads', (*SCOPE, PLAN, 'task', RUN, 'demo-agent', 'demo-principal', 'RUNNING', 2, 0))
        self.insert('sample_budgets', (*SCOPE, 'budget', 1, 'USD', 100, 20, 0, False, 1, 2, 'a'*64))
        self.insert('run_admissions', (*KEY, 'admission', 'tx', 'digest', 'lease', 'grant', 'budget'))
        self.insert('sample_reservations', (*KEY, 'budget', 1, 20, 'USD', 'digest', 'tx'))
        self.db.commit()
        self.params = dict(zip(('tenant_id','company_id','environment_id'), SCOPE))
        self.params.update(run_id=RUN, plan_revision=PLAN, task_id='task', agent_instance_id='demo-agent',
                           principal_id='demo-principal', attempt=0, budget_id='budget',
                           currency='USD', policy_epoch=1, witness_epoch=2)

    def insert(self, table, row):
        self.db.execute(f'INSERT INTO {table} VALUES ({",".join("?" for _ in row)})', row)

    def read(self, **changes):
        before = self.db.total_changes
        self.db.execute('PRAGMA query_only=ON')
        try:
            rows = self.db.execute(SQL.replace('t1_candidate.', ''), self.params | changes).fetchall()
        finally:
            self.db.execute('PRAGMA query_only=OFF')
        self.assertEqual(before, self.db.total_changes)
        for row in rows:
            self.assertEqual(row[:4], ('HOLD', 0, 0, 0))
        self.assertLessEqual(len(rows), 1)
        return rows[0][4] if rows else None

    def test_matching_run_never_proves_invocation(self):
        self.assertEqual(self.read(), 'RUN_LEVEL_ONLY_INVOCATION_MEMBERSHIP_MISSING_HOLD')

    def test_scope_and_attempt_mismatch(self):
        for key in ('tenant_id','company_id','environment_id','run_id','plan_revision','task_id',
                    'agent_instance_id','principal_id','attempt'):
            with self.subTest(key=key):
                self.assertIsNone(self.read(**{key: 1 if key == 'attempt' else 'wrong'}))

    def test_sql_injection_is_data(self):
        self.assertIsNone(self.read(run_id="' OR 1=1 --"))

    def test_missing_reservation(self):
        self.db.execute('DELETE FROM sample_reservations')
        self.assertEqual(self.read(), 'RESERVATION_MISSING_HOLD')

    def test_missing_admission(self):
        self.db.execute('DELETE FROM sample_reservations')
        self.db.execute('DELETE FROM run_admissions')
        self.assertEqual(self.read(), 'ADMISSION_MISSING_HOLD')

    def test_bad_budget_id(self):
        self.assertEqual(self.read(budget_id='other'), 'RUN_RESERVATION_LINK_HOLD')

    def test_admission_transaction_and_digest(self):
        for column in ('transaction_ref','request_digest'):
            with self.subTest(column=column):
                self.db.execute('SAVEPOINT changed')
                self.db.execute(f'UPDATE sample_reservations SET {column}=?', ('other',))
                self.assertEqual(self.read(), 'RUN_RESERVATION_LINK_HOLD')
                self.db.execute('ROLLBACK TO changed')
                self.db.execute('RELEASE changed')

    def test_unknown_cost(self):
        self.db.execute('UPDATE sample_budgets SET unknown_cost=TRUE')
        self.assertEqual(self.read(), 'UNKNOWN_COST_HOLD')

    def test_epoch_mismatch(self):
        for key in ('policy_epoch','witness_epoch'):
            self.assertEqual(self.read(**{key:99}), 'BUDGET_EPOCH_HOLD')

    def test_currency_mismatch(self):
        self.assertEqual(self.read(currency='EUR'), 'BUDGET_REFERENCE_HOLD')

    def test_future_reservation_revision(self):
        self.db.execute('UPDATE sample_reservations SET budget_revision=2')
        self.assertEqual(self.read(), 'BUDGET_REFERENCE_HOLD')

    def test_invalid_reservation_revision(self):
        self.db.execute('UPDATE sample_reservations SET budget_revision=0')
        self.assertEqual(self.read(), 'BUDGET_REFERENCE_HOLD')

    def test_budget_balance(self):
        self.db.execute('UPDATE sample_budgets SET outstanding_minor=19')
        self.assertEqual(self.read(), 'BUDGET_BALANCE_HOLD')

    def test_failure_settlement_is_not_usage(self):
        self.insert('run_mutations', (*KEY, 3, 'terminal-tx', 'terminal-digest', 'RUNNING', 'FAILED', 0))
        self.insert('sample_settlements', (*KEY, 3, 'terminal-tx', 'terminal-digest', 'admission', 'budget',
                                          20, 0, 2, 'lease-digest', 'D0_LOCAL_FAILURE_NO_EFFECT'))
        self.db.execute('UPDATE sample_budgets SET revision=2,outstanding_minor=0')
        self.assertEqual(self.read(), 'RUN_SETTLEMENT_NOT_USAGE_HOLD')

    def test_newer_aggregate_is_not_invocation_proof(self):
        self.db.execute('UPDATE sample_budgets SET revision=2,outstanding_minor=40')
        self.assertEqual(self.read(), 'RUN_LEVEL_ONLY_INVOCATION_MEMBERSHIP_MISSING_HOLD')

    def test_no_invocation_identity_or_usage_columns(self):
        for table in ('sample_reservations','sample_settlements'):
            cols = {row[1] for row in self.db.execute(f'PRAGMA table_info({table})')}
            self.assertTrue(cols.isdisjoint({'invocation_id','invocation_pin','reservation_id',
                                             'input_tokens','output_tokens','usage_receipt_id'}))


if __name__ == '__main__':
    unittest.main(verbosity=2)
