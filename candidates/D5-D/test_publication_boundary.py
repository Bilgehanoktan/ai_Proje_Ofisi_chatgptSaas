"""D5-D diagnostics, not a product authority or a T1 regression.
Exact original authority + transport; separate temporary synthetic publisher DB.
PASS on a counterexample means the limitation is reproduced, not fixed.
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


def load_pinned(filename, pin, name):
    path = HERE / filename
    raw = path.read_bytes()
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() != pin:
        raise ValueError('SOURCE_PIN_HOLD')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {name: module}):
        spec.loader.exec_module(module)
    return module


A = load_pinned('intent_authority.original.py', 'fa47acd32adb309896f762ec50e47bf26641adbb', 'd5d_original_authority')
# Annotation-only stub, no T1 coordinator or role write validation is exercised.
port = types.ModuleType('app.core.transaction.port')
port.CommitReceipt = type('CommitReceipt', (), {})
with patch.dict(sys.modules, {'app.core.transaction.port': port}):
    T = load_pinned('postgres_session.original.py', '8e65e4575a77b11c38c2d2e62ec91fc89d75e23c', 'd5d_original_transport')


def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()


class Adapter:
    autocommit = False

    def __init__(self, path, before_commit):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute('BEGIN IMMEDIATE')
        self.before_commit = before_commit

    @contextlib.contextmanager
    def cursor(self):
        with contextlib.closing(self.db.cursor()) as c:
            yield c

    def commit(self):
        self.before_commit()
        self.db.execute('COMMIT')

    def rollback(self):
        self.db.execute('ROLLBACK')

    def close(self):
        self.db.close()


class PublicationBoundaryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='d5d-')
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)
        self.root = A.RootPin(digest('witness-1'), digest('key'), 1)
        self.authority = A.D0IntentAuthority.create(self.path/'root.authority.sqlite', self.root)
        self.owner = self.path/'publisher.sqlite'
        self.target = self.path/'target.sqlite'
        with contextlib.closing(sqlite3.connect(self.owner)) as db:
            db.execute('CREATE TABLE observations(kind TEXT PRIMARY KEY, revision INTEGER, active INTEGER)')
            db.executemany('INSERT INTO observations VALUES (?,1,1)', [(k,) for k in ('IAM','ORG','ROLE')])
            db.commit()
        with contextlib.closing(sqlite3.connect(self.target)) as db:
            db.execute('CREATE TABLE diagnostic(value INTEGER)')
            db.commit()

    def read_owner(self):
        with contextlib.closing(sqlite3.connect(self.owner)) as db:
            return tuple(db.execute('SELECT * FROM observations ORDER BY kind'))

    def revoke(self, kind):
        with contextlib.closing(sqlite3.connect(self.owner)) as db:
            db.execute('UPDATE observations SET revision=revision+1, active=0 WHERE kind=?', (kind,))
            db.commit()

    def claim(self, suffix='first'):
        return self.authority.claim_and_fence(self.root, digest('same-run-scope'), digest('binding-'+suffix), 'tx-'+suffix, digest('request-'+suffix))

    def rows(self):
        with contextlib.closing(sqlite3.connect(self.target)) as db:
            return db.execute('SELECT count(*) FROM diagnostic').fetchone()[0]

    def counterexample(self, publisher):
        pinned = self.read_owner()
        with self.claim():
            self.assertEqual(self.read_owner(), pinned)
            with T.postgres_transaction(lambda: Adapter(self.target, lambda: self.revoke(publisher)), None) as session:
                session.cursor.execute('INSERT INTO diagnostic VALUES (1)')
                self.assertEqual(self.read_owner(), pinned)
            self.assertNotEqual(self.read_owner(), pinned)
            with contextlib.closing(self.authority._db()) as db:
                self.assertEqual(self.authority._head(db), (1, self.root))
        self.assertEqual(self.rows(), 1)
        self.assertIn((publisher, 2, 0), self.read_owner())

    def test_iam_independent_publication_during_commit(self):
        self.counterexample('IAM')

    def test_org_independent_publication_during_commit(self):
        self.counterexample('ORG')

    def test_role_independent_publication_during_commit(self):
        self.counterexample('ROLE')

    def test_prebody_drift_control_rolls_back(self):
        pinned = self.read_owner()
        self.revoke('ORG')
        with self.claim():
            with self.assertRaisesRegex(ValueError, 'DIAGNOSTIC_DRIFT'):
                with T.postgres_transaction(lambda: Adapter(self.target, lambda: None), None) as session:
                    if self.read_owner() != pinned:
                        raise ValueError('DIAGNOSTIC_DRIFT')
                    session.cursor.execute('INSERT INTO diagnostic VALUES (1)')
        self.assertEqual(self.rows(), 0)

    def test_parent_claim_cannot_be_reused_as_child(self):
        with self.claim():
            pass
        with self.assertRaisesRegex(ValueError, 'D0_AUTHORITY_ALREADY_CLAIMED_HOLD'):
            with self.claim('distinct-economic-tx'):
                self.fail('original parent claim was reused')
        with contextlib.closing(self.authority._db()) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0], 1)
        self.assertEqual(self.rows(), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
