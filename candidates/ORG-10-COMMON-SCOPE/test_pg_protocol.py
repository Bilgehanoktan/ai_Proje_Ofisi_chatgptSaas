"""Local protocol tests with a fake DB; never counts as PostgreSQL evidence."""
import unittest
from dataclasses import replace
from types import SimpleNamespace
from pg_transaction import run, Hold, CommitUnknown, CleanupHold, WRITERS, DATABASE, CLUSTER, SCHEMA, TABLES, R3Read, lock_head
from pg_operations import TaskReference, reference_check

ROLE='aicos_org10_writer_a'; SCOPE=WRITERS[ROLE]

class Cursor:
    def __init__(self,row=None): self.row=row
    def fetchone(self): return self.row
    def fetchall(self): return self.row

class Fake:
    def __init__(self,write=True):
        self.autocommit=False; self.info=SimpleNamespace(transaction_status=0)
        self.row=(DATABASE,ROLE,ROLE,False,False,False,False,False,False,'127.0.0.1','127.0.0.1',*(('read committed','off') if write else ('repeatable read','on')),CLUSTER,'170012','55436')
        self.calls=[]; self.commit_error=False; self.close_error=False; self.rollback_error=False
        self.inventory=[(t,True,True,'aicos_org10_owner') for t in sorted(TABLES)]; self.membership=(0,)
    def execute(self,sql,args=()):
        self.calls.append((sql,args))
        return Cursor(self.row if sql.startswith('SELECT current_database()') else self.inventory if sql.startswith('SELECT c.relname') else self.membership if sql.startswith('SELECT count(*) FROM pg_catalog.pg_auth_members') else None)
    def commit(self):
        self.calls.append('commit')
        if self.commit_error: raise OSError('lost reply')
    def rollback(self):
        self.calls.append('rollback')
        if self.rollback_error: raise OSError('lost rollback')
    def close(self):
        self.calls.append('close')
        if self.close_error: raise OSError('close')

class Protocol(unittest.TestCase):
    def test_commit(self):
        d=Fake(); self.assertEqual(run(lambda:d,SCOPE,True,lambda db:'ok'),'ok'); self.assertEqual(d.calls[-2:],['commit','close'])
    def test_read(self):
        d=Fake(False); self.assertEqual(run(lambda:d,SCOPE,False,lambda db:1),1); self.assertNotIn('commit',d.calls); self.assertEqual(d.calls[-2:],['rollback','close'])
    def test_failure(self):
        d=Fake()
        def broken(db): raise ValueError('no')
        with self.assertRaisesRegex(ValueError,'no'): run(lambda:d,SCOPE,True,broken)
        self.assertEqual(d.calls[-2:],['rollback','close']); self.assertNotIn('commit',d.calls)
    def test_commit_unknown(self):
        d=Fake(); d.commit_error=True
        with self.assertRaises(CommitUnknown): run(lambda:d,SCOPE,True,lambda db:1)
        self.assertEqual(d.calls.count('commit'),1); self.assertNotIn('rollback',d.calls); self.assertEqual(d.calls[-1],'close')
    def test_close_failure(self):
        d=Fake(); d.close_error=True
        with self.assertRaises(CleanupHold): run(lambda:d,SCOPE,True,lambda db:1)
        self.assertEqual(d.calls.count('commit'),1)
    def test_rollback_failure(self):
        d=Fake(); d.rollback_error=True
        with self.assertRaises(CleanupHold): run(lambda:d,SCOPE,True,lambda db:1/0)
        self.assertNotIn('commit',d.calls)
    def test_context_change(self):
        d=Fake()
        def change(db): db.row=(*db.row[:9],'::1',*db.row[10:]); return 1
        with self.assertRaisesRegex(Hold,'CONTEXT_CHANGED'): run(lambda:d,SCOPE,True,change)
        self.assertNotIn('commit',d.calls)
    def test_wrong_db(self):
        d=Fake(); d.row=('production',*d.row[1:])
        with self.assertRaisesRegex(Hold,'SCOPE_ROLE'): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_cross_scope(self):
        d=Fake()
        with self.assertRaises(Hold): run(lambda:d,WRITERS['aicos_org10_writer_b'],True,lambda db:self.fail())
    def test_superuser(self):
        d=Fake(); d.row=(*d.row[:3],True,*d.row[4:])
        with self.assertRaisesRegex(Hold,'ROLE_FLAGS'): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_switched_role(self):
        d=Fake(); d.row=(*d.row[:2],'other',*d.row[3:])
        with self.assertRaises(Hold): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_remote(self):
        d=Fake(); d.row=(*d.row[:9],'10.0.0.2',*d.row[10:])
        with self.assertRaisesRegex(Hold,'LOCAL_ONLY'): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_active_tx(self):
        d=Fake(); d.info.transaction_status=2
        with self.assertRaisesRegex(Hold,'FRESH_CONNECTION'): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_reader_cannot_write(self):
        d=Fake(); d.row=(d.row[0],'aicos_org10_reader_a','aicos_org10_reader_a',*d.row[3:])
        with self.assertRaises(Hold): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_reader_read(self):
        d=Fake(False); d.row=(d.row[0],'aicos_org10_reader_a','aicos_org10_reader_a',*d.row[3:]); self.assertEqual(run(lambda:d,SCOPE,False,lambda db:1),1)
    def test_wrong_cluster(self):
        d=Fake(); d.row=(*d.row[:13],'core','170012','55436')
        with self.assertRaisesRegex(Hold,'PG_CLUSTER_VERSION'): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_wrong_version(self):
        d=Fake(); d.row=(*d.row[:14],'180004',d.row[15])
        with self.assertRaisesRegex(Hold,'PG_CLUSTER_VERSION'): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_rls_disabled(self):
        d=Fake(); d.inventory[0]=(d.inventory[0][0],True,False,'aicos_org10_owner')
        with self.assertRaisesRegex(Hold,'PG_RLS_INVENTORY'): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_role_membership(self):
        d=Fake(); d.membership=(1,)
        with self.assertRaisesRegex(Hold,'PG_ROLE_MEMBERSHIP'): run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_read_adapter(self):
        d=Fake(); R3Read(d).execute('SELECT rev FROM org_head WHERE t=?',('a',)); self.assertEqual(d.calls[-1],(f'SELECT rev FROM {SCHEMA}.org_head WHERE t=%s',('a',)))
    def test_read_adapter_sort(self):
        d=Fake(); R3Read(d).execute('SELECT id,kind,parent FROM org_unit WHERE t=? ORDER BY 1',('a',))
        self.assertTrue(d.calls[-1][0].endswith('ORDER BY id COLLATE \"C\"'))
    def test_read_adapter_rejects(self):
        for sql in ('DELETE FROM org_head','SELECT x FROM other','SELECT x FROM org_head; DELETE FROM org_head','SELECT x FROM org_head WHERE t=?'):
            with self.subTest(sql=sql),self.assertRaises(Hold): R3Read(Fake()).execute(sql)
    def test_lock(self):
        d=Fake(); self.assertIsNone(lock_head(d,SCOPE)); self.assertTrue(d.calls[-1][0].endswith('FOR UPDATE'))

class References(unittest.TestCase):
    def setUp(self): self.p=TaskReference(SCOPE,'project','sha256:'+'a'*64,'task','research','demo-x','demo-principal')
    def test_match(self): self.assertEqual(reference_check(self.p,self.p,SCOPE,'demo-x'),self.p)
    def test_different_task(self):
        with self.assertRaises(Hold): reference_check(replace(self.p,task='other'),self.p,SCOPE,'demo-x')
    def test_different_instance(self):
        with self.assertRaises(Hold): reference_check(self.p,self.p,SCOPE,'demo-y')
    def test_different_scope(self):
        with self.assertRaises(Hold): reference_check(self.p,self.p,WRITERS['aicos_org10_writer_b'],'demo-x')
    def test_invalid_plan(self):
        p=replace(self.p,plan='invalid')
        with self.assertRaises(Hold): reference_check(p,p,SCOPE,'demo-x')
    def test_non_demo_principal(self):
        p=replace(self.p,principal='real')
        with self.assertRaises(Hold): reference_check(p,p,SCOPE,'demo-x')

if __name__=='__main__': unittest.main(verbosity=2)
