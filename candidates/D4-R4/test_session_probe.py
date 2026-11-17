import unittest
from dataclasses import astuple, replace
from types import SimpleNamespace
from test_identity_binding import R,B,F
from session_probe import inspect_connection,TABLES

class Cursor:
    def __init__(self,db):self.db=db;self.rows=[]
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def execute(self,sql,args=()):
        self.db.calls.append(sql)
        if sql.startswith('SET TRANSACTION'):self.db.info.transaction_status=2
        elif sql.startswith('SELECT session_user'):self.rows=list(self.db.rows)
        elif sql.startswith('SELECT relname'):self.rows=[(x,) for x in sorted(self.db.tables)]
        else:raise AssertionError('unexpected SQL')
    def fetchone(self):return self.rows.pop(0) if self.rows else None
    def fetchall(self):return self.rows

class Connection:
    def __init__(self):
        self.autocommit=False;self.info=SimpleNamespace(transaction_status=0,backend_pid=123)
        self.calls=[];self.rows=[astuple(F)];self.tables=TABLES;self.closed=False;self.rollback_fail=False;self.close_fail=False
    def cursor(self):return Cursor(self)
    def rollback(self):
        if self.rollback_fail:raise RuntimeError('rollback')
        self.info.transaction_status=0
    def close(self):
        self.closed=True
        if self.close_fail:raise RuntimeError('close')

class ProbeTests(unittest.TestCase):
    def test_read_only_and_close(self):
        d=Connection();r=inspect_connection(R,B,lambda:B,lambda:9,lambda:d)
        self.assertTrue(r.structural_match);self.assertFalse(r.commit_allowed);self.assertTrue(d.closed)
        self.assertEqual(len(d.calls),3);self.assertIn('READ ONLY',d.calls[0]);self.assertEqual(d.info.transaction_status,0)
    def test_revoke_before_connect(self):
        def no_connect():raise AssertionError('must not connect')
        r=inspect_connection(R,B,lambda:replace(B,active=False),lambda:9,no_connect)
        self.assertFalse(r.structural_match);self.assertEqual(r.reason,'D4_SCOPE_OR_REVISION_HOLD')
    def test_revoke_during_probe(self):
        d=Connection();pins=iter((B,replace(B,active=False)))
        r=inspect_connection(R,B,lambda:next(pins),lambda:9,lambda:d)
        self.assertFalse(r.structural_match);self.assertTrue(d.closed)
    def test_dirty(self):
        d=Connection();d.info.transaction_status=2
        self.assertFalse(inspect_connection(R,B,lambda:B,lambda:9,lambda:d).structural_match);self.assertTrue(d.closed);self.assertEqual(d.calls,[])
    def test_autocommit(self):
        d=Connection();d.autocommit=True
        self.assertFalse(inspect_connection(R,B,lambda:B,lambda:9,lambda:d).structural_match);self.assertTrue(d.closed)
    def test_wrong_role(self):
        d=Connection();d.rows=[astuple(replace(F,session_user='other'))]
        self.assertFalse(inspect_connection(R,B,lambda:B,lambda:9,lambda:d).structural_match);self.assertTrue(d.closed)
    def test_missing_table(self):
        d=Connection();d.tables=TABLES[:-1]
        self.assertFalse(inspect_connection(R,B,lambda:B,lambda:9,lambda:d).structural_match);self.assertTrue(d.closed)
    def test_duplicate_facts(self):
        d=Connection();d.rows*=2
        self.assertFalse(inspect_connection(R,B,lambda:B,lambda:9,lambda:d).structural_match);self.assertTrue(d.closed)
    def test_rollback_failure(self):
        d=Connection();d.rollback_fail=True
        self.assertFalse(inspect_connection(R,B,lambda:B,lambda:9,lambda:d).structural_match);self.assertTrue(d.closed)
    def test_close_failure(self):
        d=Connection();d.close_fail=True
        self.assertEqual(inspect_connection(R,B,lambda:B,lambda:9,lambda:d).reason,'D4_CLOSE_HOLD')
    def test_resolver_failure(self):
        def fail():raise RuntimeError('offline')
        self.assertFalse(inspect_connection(R,B,fail,lambda:9,lambda:Connection()).structural_match)

if __name__=='__main__':unittest.main()
