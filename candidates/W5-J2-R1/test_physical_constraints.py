"""Disposable SQLite fixture ONLY: constraint and transaction experiments.
No product migration, owner adapter, live DB, provider or financial effect.
The fixture starts with an already-reserved balance; no second debit is assumed.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

DDL = '''
CREATE TABLE fixture_budget (
 scope TEXT NOT NULL, budget TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=0),
 outstanding INTEGER NOT NULL CHECK(outstanding>=0), recognized INTEGER NOT NULL CHECK(recognized>=0),
 unknown INTEGER NOT NULL CHECK(unknown IN (0,1)), PRIMARY KEY(scope,budget));
CREATE TABLE fixture_member (
 scope TEXT NOT NULL, budget TEXT NOT NULL, reservation TEXT NOT NULL, invocation_key TEXT NOT NULL,
 invocation_pin TEXT NOT NULL, membership_pin TEXT NOT NULL, attempt INTEGER NOT NULL,
 amount INTEGER NOT NULL CHECK(amount>0), state TEXT NOT NULL CHECK(state IN ('RESERVED','CONSUMED','UNKNOWN','USAGE_KNOWN','RECONCILED')),
 PRIMARY KEY(scope,membership_pin), UNIQUE(scope,budget,reservation), UNIQUE(scope,invocation_key), UNIQUE(scope,invocation_pin),
 FOREIGN KEY(scope,budget) REFERENCES fixture_budget(scope,budget));
CREATE TABLE fixture_receipt (
 scope TEXT NOT NULL, member TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('RESERVATION','CONSUME','USAGE','RECONCILIATION')),
 pin TEXT NOT NULL, PRIMARY KEY(scope,member,role), UNIQUE(scope,pin),
 FOREIGN KEY(scope,member) REFERENCES fixture_member(scope,membership_pin));
'''

class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'fixture.sqlite';self.db=self.connect();self.addCleanup(self.db.close)
        self.db.executescript(DDL);self.db.execute("INSERT INTO fixture_budget VALUES ('scope','b',2,20,0,0)")
    def connect(self):
        db=sqlite3.connect(self.path, isolation_level=None,timeout=0);db.execute('PRAGMA foreign_keys=ON');return db
    def insert(self,db=None,*,reservation='r',key='k',invocation='i',member='m',attempt=1,state='RESERVED'):
        db=self.db if db is None else db
        db.execute('INSERT INTO fixture_member VALUES (?,?,?,?,?,?,?,?,?)',('scope','b',reservation,key,invocation,member,attempt,20,state))
    def receipt(self,role,pin,member='m'):
        self.db.execute('INSERT INTO fixture_receipt VALUES (?,?,?,?)',('scope',member,role,pin))
    def balances(self): return self.db.execute("SELECT revision,outstanding,recognized,unknown FROM fixture_budget").fetchone()
    def count(self,table): return self.db.execute('SELECT count(*) FROM '+table).fetchone()[0]
    def test_reservation_unique(self):
        self.insert()
        with self.assertRaises(sqlite3.IntegrityError): self.insert(key='k2',invocation='i2',member='m2',attempt=2)
    def test_invocation_key_unique(self):
        self.insert()
        with self.assertRaises(sqlite3.IntegrityError): self.insert(reservation='r2',invocation='i2',member='m2',attempt=2)
    def test_invocation_pin_unique(self):
        self.insert()
        with self.assertRaises(sqlite3.IntegrityError): self.insert(reservation='r2',key='k2',member='m2')
    def test_membership_unique(self):
        self.insert()
        with self.assertRaises(sqlite3.IntegrityError): self.insert(reservation='r2',key='k2',invocation='i2')
    def test_receipt_role_once(self):
        self.insert();self.receipt('CONSUME','p')
        with self.assertRaises(sqlite3.IntegrityError):self.receipt('CONSUME','other')
    def test_receipt_alias_cross_member_role(self):
        self.insert();self.insert(reservation='r2',key='k2',invocation='i2',member='m2');self.receipt('RESERVATION','p')
        with self.assertRaises(sqlite3.IntegrityError):self.receipt('USAGE','p','m2')
    def test_orphan_receipt(self):
        with self.assertRaises(sqlite3.IntegrityError):self.receipt('CONSUME','p')
    def test_atomic_rollback(self):
        self.db.execute('BEGIN IMMEDIATE');self.insert();self.receipt('RESERVATION','p')
        self.db.execute("UPDATE fixture_budget SET revision=3 WHERE revision=2")
        with self.assertRaises(sqlite3.IntegrityError):self.receipt('CONSUME','p')
        self.db.rollback()
        self.assertEqual((self.count('fixture_member'),self.count('fixture_receipt'),self.balances()),(0,0,(2,20,0,0)))
    def test_concurrent_writer(self):
        other=self.connect();self.addCleanup(other.close)
        self.db.execute('BEGIN IMMEDIATE');self.insert()
        with self.assertRaises(sqlite3.OperationalError) as err: other.execute('BEGIN IMMEDIATE')
        self.assertIn('locked',str(err.exception));self.db.commit()
        with self.assertRaises(sqlite3.IntegrityError): self.insert(other,attempt=2)
        self.assertEqual(self.count('fixture_member'),1)
    def test_unknown_preserves_balance(self):
        self.insert(state='UNKNOWN');self.db.execute('UPDATE fixture_budget SET unknown=1,revision=3')
        # The fixture's guarded settlement attempt cannot convert unknown to zero.
        changed=self.db.execute("UPDATE fixture_budget SET outstanding=0,revision=4 WHERE revision=3 AND unknown=0 AND EXISTS (SELECT 1 FROM fixture_member WHERE state='USAGE_KNOWN')").rowcount
        self.assertEqual(changed,0);self.assertEqual(self.balances(),(3,20,0,1))
    def test_known_settlement_cas_and_rollback(self):
        self.insert(state='USAGE_KNOWN');self.receipt('USAGE','u');self.db.execute('BEGIN IMMEDIATE')
        # Illustrative atomic CAS only, not an owner-approved settlement command.
        q="UPDATE fixture_budget SET revision=revision+1,outstanding=outstanding-20,recognized=recognized+12 WHERE revision=2 AND outstanding>=20 AND unknown=0"
        self.assertEqual(self.db.execute(q).rowcount,1)
        self.receipt('RECONCILIATION','q');self.db.execute("UPDATE fixture_member SET state='RECONCILED' WHERE membership_pin='m' AND state='USAGE_KNOWN'")
        self.assertEqual(self.db.execute(q).rowcount,0)
        self.db.rollback();self.assertEqual(self.balances(),(2,20,0,0));self.assertEqual(self.count('fixture_receipt'),1)
        self.assertEqual(self.db.execute('SELECT state FROM fixture_member').fetchone()[0],'USAGE_KNOWN')
    def test_known_settlement_commit_once(self):
        self.insert(state='USAGE_KNOWN');self.receipt('USAGE','u');self.db.execute('BEGIN IMMEDIATE')
        self.assertEqual(self.db.execute("UPDATE fixture_budget SET revision=3,outstanding=0,recognized=12 WHERE revision=2 AND unknown=0").rowcount,1)
        self.receipt('RECONCILIATION','q');self.db.execute("UPDATE fixture_member SET state='RECONCILED' WHERE membership_pin='m' AND state='USAGE_KNOWN'");self.db.commit()
        other=self.connect();self.addCleanup(other.close)
        self.assertEqual(other.execute('SELECT revision,outstanding,recognized FROM fixture_budget').fetchone(),(3,0,12))
        with self.assertRaises(sqlite3.IntegrityError):self.receipt('RECONCILIATION','q2')
        self.assertEqual(other.execute("UPDATE fixture_budget SET revision=4,recognized=24 WHERE revision=2").rowcount,0)

if __name__=='__main__': unittest.main(verbosity=2)
