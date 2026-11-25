"""Supplemental SQLite tests of exact ORG-05R3 and MI03 assignment-owner SQL.

All data is disposable synthetic D0. Does NOT execute Python OperationsStore,
Core three-store readback, accepted owner signature or production PostgreSQL.
"""
import hashlib
import json
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import closing

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    'schema.sql': ('32b7609b18e8a53420f17d23f4b53544e7f6f6ad', '76e71112695ade87fd55a63cbd156ca8eb14f96f0971a3883735aa0ecc21d3ed'),
    'operations.sql': ('3443f6581eb3a8d3894aea0b620f2b8d6dba9b2a', '97c595a2e11b1822bf5ca1bda70417915503fdb14f29866927979cf044fd6a77'),
    'assignment_review.sql': ('3e887b10263f44b601f6a811a89687b2ee4d864e', '8983995430cbd87a1bca68c5dac0206e1051c9039659c4f0be9be0b79209ab21'),
}


def read_pin(name):
    b = (ROOT / name).read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
    digest = hashlib.sha256(b).hexdigest()
    if (blob, digest) != PINS[name]:
        raise RuntimeError('SOURCE_PIN_HOLD: ' + name)
    return b.decode('utf-8')


class ExactOrgSqlTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / 'org_d0.sqlite'
        self.db = sqlite3.connect(self.path)
        self.addCleanup(self.db.close)
        self.db.execute('PRAGMA foreign_keys=ON')
        for name in PINS:
            self.db.executescript(read_pin(name))

    def insert_assignment(self, run='demo-run', revision=1, state='ACCEPTED_D0', digest='a'*64, previous='0'*64):
        self.db.execute('INSERT INTO op_assignment_review VALUES (?,?,?,?,?,?,?,?,?)',
                        ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY', run,
                         revision, state, previous, digest, '{}'))

    def test_exact_owner_source_pins(self):
        self.assertEqual([name for name in PINS if read_pin(name)], list(PINS))

    def test_initializes_all_owner_tables_and_immutable_triggers(self):
        tables = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({'org_revision', 'org_head', 'org_binding', 'op_team',
                         'op_entry', 'op_notice', 'op_assignment_review'} <= tables)
        triggers = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        self.assertTrue({'op_assignment_review_no_update','op_assignment_review_no_delete'} <= triggers)
        self.assertEqual(self.db.execute('PRAGMA foreign_keys').fetchone(), (1,))

    def test_direct_accepted_d0_record_remains_non_authoritative(self):
        self.insert_assignment()
        self.assertEqual(self.db.execute('SELECT state,revision FROM op_assignment_review').fetchone(),
                         ('ACCEPTED_D0', 1))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM op_notice').fetchone(), (0,))

    def test_revocation_revision_two_requires_correct_state(self):
        self.insert_assignment()
        self.insert_assignment(revision=2, state='REVOKED_D0', digest='b'*64, previous='a'*64)
        self.assertEqual(self.db.execute('SELECT state FROM op_assignment_review ORDER BY revision').fetchall(),
                         [('ACCEPTED_D0',), ('REVOKED_D0',)])
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert_assignment(revision=2,state='ACCEPTED_D0',digest='c'*64)

    def test_duplicate_acceptance_revision_blocked(self):
        self.insert_assignment()
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert_assignment(digest='c'*64)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM op_assignment_review').fetchone(), (1,))

    def test_invalid_state_revision_and_digest_are_rejected(self):
        for bad in [dict(state='REVOKED_D0'),dict(state='LIVE'),dict(revision=3),
                    dict(digest='a'),dict(previous='0')]:
            with self.subTest(bad=bad):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.insert_assignment(**bad)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM op_assignment_review').fetchone(), (0,))

    def test_append_only_trigger_denies_update_and_delete(self):
        self.insert_assignment()
        with self.assertRaisesRegex(sqlite3.IntegrityError,'IMMUTABLE'):
            self.db.execute("UPDATE op_assignment_review SET body='altered' WHERE run='demo-run'")
        with self.assertRaisesRegex(sqlite3.IntegrityError,'IMMUTABLE'):
            self.db.execute("DELETE FROM op_assignment_review WHERE run='demo-run'")
        self.assertEqual(self.db.execute('SELECT body FROM op_assignment_review').fetchone(), ('{}',))

    def test_scope_digest_uniqueness_cannot_be_reused_other_run(self):
        self.insert_assignment()
        with self.assertRaises(sqlite3.IntegrityError):
            self.insert_assignment(run='different-run')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM op_assignment_review').fetchone(), (1,))

    def test_org_revision_requires_valid_sequence(self):
        scope=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO org_revision VALUES (?,?,?,?,?,?,?,?)',
                            (*scope,'r0',0,None,'a'*64,None))
        self.db.execute('INSERT INTO org_revision VALUES (?,?,?,?,?,?,?,?)',
                        (*scope,'r1',1,None,'a'*64,None))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO org_revision VALUES (?,?,?,?,?,?,?,?)',
                            (*scope,'r2',2,None,'b'*64,None))

    def test_org_notice_enforces_hold_only(self):
        scope=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
        self.db.execute('INSERT INTO org_revision VALUES (?,?,?,?,?,?,?,?)',
                        (*scope,'r1',1,None,'a'*64,None))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO org_notice VALUES (?,?,?,?,?,?,?)',
                            (*scope,'r1','b'*64,'ORG_REVISION_RECORDED_D0','GRANT'))
        self.db.execute('INSERT INTO org_notice VALUES (?,?,?,?,?,?,?)',
                        (*scope,'r1','b'*64,'ORG_REVISION_RECORDED_D0','HOLD'))
        self.assertEqual(self.db.execute('SELECT state FROM org_notice').fetchone(), ('HOLD',))

    def test_operations_requires_real_fk_member_not_direct_stub(self):
        scope=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO op_team VALUES (?,?,?,?,?,?,?)',
                            (*scope,'not-registered','project','demo-seat','a'*64))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM op_team').fetchone(),(0,))


if __name__=='__main__':
    unittest.main(verbosity=2)
