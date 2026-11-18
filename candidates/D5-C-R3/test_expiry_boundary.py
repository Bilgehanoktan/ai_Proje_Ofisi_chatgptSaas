"""Isolated timing diagnostic of the exact D0 transaction transport.
Real temporary SQLite, synthetic clock and adapter, no actual IAM or PostgreSQL.
A PASS reproduces the missing expiry-through-commit guarantee, not its fix.
"""
import contextlib
import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PIN = '8e65e4575a77b11c38c2d2e62ec91fc89d75e23c'


def load_original():
    path = HERE / 'postgres_session.original.py'
    raw = path.read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() != PIN:
        raise ValueError('SOURCE_PIN_HOLD')
    # The original imports CommitReceipt for a return annotation only.
    # This substitute is never instantiated or used for T1 role validation.
    port = types.ModuleType('app.core.transaction.port')
    port.CommitReceipt = type('CommitReceipt', (), {})
    spec = importlib.util.spec_from_file_location('d5c_original_transport', path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'app.core.transaction.port': port}):
        spec.loader.exec_module(module)
    return module


class Adapter:
    autocommit = False

    def __init__(self, path, clock, expire_at):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute('BEGIN IMMEDIATE')
        self.clock = clock
        self.expire_at = expire_at
        self.commit_ticks = []

    @contextlib.contextmanager
    def cursor(self):
        with contextlib.closing(self.db.cursor()) as cursor:
            yield cursor
        if self.expire_at == 'cursor_exit':
            self.clock[0] = 10

    def commit(self):
        self.commit_ticks.append(self.clock[0])
        if self.expire_at == 'inside_commit':
            self.clock[0] = 10
        self.db.execute('COMMIT')
        self.commit_ticks.append(self.clock[0])

    def rollback(self):
        self.db.execute('ROLLBACK')

    def close(self):
        self.db.close()


class ExpiryBoundaryTests(unittest.TestCase):
    def run_case(self, initial, expire_at, expected, expected_ticks):
        transport = load_original()
        with tempfile.TemporaryDirectory(prefix='d5c-r3-expiry-') as tmp:
            path = Path(tmp) / 'diagnostic.sqlite'
            with contextlib.closing(sqlite3.connect(path)) as init:
                init.execute('CREATE TABLE observation(value INTEGER NOT NULL)')
                init.commit()
            clock = [initial]
            adapter = Adapter(path, clock, expire_at)
            def write():
                with transport.postgres_transaction(lambda: adapter, None) as session:
                    # Deliberately synthetic validation just before leaving T1 body.
                    if clock[0] >= 10:
                        raise ValueError('DIAGNOSTIC_EXPIRED')
                    session.cursor.execute('INSERT INTO observation VALUES (1)')
            if not expected:
                with self.assertRaisesRegex(ValueError, 'DIAGNOSTIC_EXPIRED'):
                    write()
            else:
                write()
            with contextlib.closing(sqlite3.connect(path)) as independent_read:
                self.assertEqual(independent_read.execute('SELECT count(*) FROM observation').fetchone()[0], expected)
            self.assertEqual(adapter.commit_ticks, expected_ticks)

    def test_control_expired_before_body_rolls_back(self):
        self.run_case(10, None, 0, [])

    def test_control_valid_through_commit(self):
        self.run_case(9, None, 1, [9, 9])

    def test_expiry_at_cursor_exit_still_commits(self):
        self.run_case(9, 'cursor_exit', 1, [10, 10])

    def test_expiry_inside_commit_still_commits(self):
        self.run_case(9, 'inside_commit', 1, [9, 10])


if __name__ == '__main__':
    unittest.main(verbosity=2)
