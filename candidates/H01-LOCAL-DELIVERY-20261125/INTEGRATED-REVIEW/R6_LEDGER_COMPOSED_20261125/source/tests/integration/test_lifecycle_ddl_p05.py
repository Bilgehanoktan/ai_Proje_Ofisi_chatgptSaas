"""Actual pinned candidate DDL + P04 snapshot reader; not full lifecycle/API tests."""
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from app.core.development_review.lifecycle_read_snapshot import TABLES, lifecycle_snapshot, require_single_head

ROOT=Path(__file__).resolve().parents[2]
DDL=(('0192/candidate_event_outbox_fence.sql','6e4780bf9f267c0926b40d582d5afdbd6faa543c'),
     ('0193/candidate_run_head.sql','180924e97ee1f31fa27332941a41e37fdf73017e'),
     ('0194/candidate_transition_roles.sql','7b5d374bb7973b283e4fcfa0d796ed6128ef9d27'),
     ('0195/candidate_admission_budget.sql','d5dc6abc045da14ef42e88b4e85e50e9062a1b27'),
     ('0196L/candidate_lease_settlement.sql','e4c9a84ff705c39486579c393b1f3aaef9e34da9'))
KEY=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','demo-a')
REV='sha256:'+'a'*64

class Cursor:
    def __init__(self,db):self.c=db.cursor()
    def execute(self,sql,params=()):return self.c.execute(sql.replace('t1_candidate.','').replace('%s','?'),params)
    def fetchone(self):return self.c.fetchone()

class CandidateDDLTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.path=Path(temp.name).resolve()/'lifecycle.d0.sqlite'
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('PRAGMA foreign_keys=ON')
            for path,expected in DDL:
                raw=(ROOT/'database'/path).read_bytes()
                self.assertEqual(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),expected)
                db.executescript(raw.decode().replace('CREATE SCHEMA t1_candidate;','').replace('t1_candidate.',''))
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',(*KEY[:3],REV,'a',KEY[3],'demo-agent','demo-principal','QUEUED',0,0))
    def test_all_twelve_tables_selectable(self):
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with lifecycle_snapshot(self.path,self.path.name) as db:
            for t in sorted(TABLES):
                self.assertEqual(db.execute('SELECT count(*) FROM '+t).fetchone(),(1 if t=='run_heads' else 0,))
            require_single_head(Cursor(db),KEY)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)
    def test_same_plan_task_unique(self):
        with closing(sqlite3.connect(self.path)) as db,self.assertRaises(sqlite3.IntegrityError):
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?,?,?,?,?,?,?,?)',(*KEY[:3],REV,'a','demo-b','demo-agent','demo-principal','QUEUED',0,0))
    def test_orphan_reservation_rejected(self):
        with closing(sqlite3.connect(self.path)) as db,self.assertRaises(sqlite3.IntegrityError):
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('INSERT INTO sample_reservations VALUES (?,?,?,?,?,?,?,?,?,?)',(*KEY,'sample-budget',1,20,'USD','digest','tx'))
    def test_orphan_outbox_rejected(self):
        with closing(sqlite3.connect(self.path)) as db,self.assertRaises(sqlite3.IntegrityError):
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('INSERT INTO outbox VALUES (?,?,?,?,?,?)',(*KEY,'event','digest'))
    def test_invalid_budget_rejected(self):
        with closing(sqlite3.connect(self.path)) as db,self.assertRaises(sqlite3.IntegrityError):
            db.execute('INSERT INTO sample_budgets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(*KEY[:3],'sample-budget',0,'USD',100,90,20,0,2,3,'a'*64))
    def test_scope_mismatch_hold(self):
        with lifecycle_snapshot(self.path,self.path.name) as db,self.assertRaisesRegex(ValueError,'HEAD_COUNT'):
            require_single_head(Cursor(db),(*KEY[:3],'demo-absent'))
    def test_write_denied(self):
        with lifecycle_snapshot(self.path,self.path.name) as db,self.assertRaises(sqlite3.DatabaseError):
            db.execute('UPDATE run_heads SET version=1')

if __name__=='__main__':unittest.main()
