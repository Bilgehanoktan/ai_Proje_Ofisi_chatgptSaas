import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from app.core.development_review.lifecycle_read_snapshot import TABLES, lifecycle_snapshot, require_single_head

class Cursor:
    def __init__(self,db): self.c=db.cursor()
    def execute(self,sql,params=()): return self.c.execute(sql.replace('t1_candidate.','').replace('%s','?'),params)
    def fetchone(self): return self.c.fetchone()

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.path=Path(temp.name).resolve()/'lifecycle.d0.sqlite'
        self.key=('tenant','company','environment','run')
        with closing(sqlite3.connect(self.path)) as db,db:
            for table in sorted(TABLES):
                if table=='run_heads':db.execute('CREATE TABLE run_heads(tenant_id TEXT,company_id TEXT,environment_id TEXT,run_id TEXT)')
                else:db.execute('CREATE TABLE '+table+'(id INTEGER)')
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?)',self.key)
            db.execute('CREATE TABLE unrelated(secret TEXT)')
            db.execute("INSERT INTO unrelated VALUES ('hidden')")
    def modify(self,sql,params=()):
        with closing(sqlite3.connect(self.path)) as db,db: db.execute(sql,params)
    def snapshot(self): return lifecycle_snapshot(self.path,self.path.name)
    def test_read_only_snapshot_preserves_bytes(self):
        old=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.snapshot() as db:
            require_single_head(Cursor(db),self.key)
            self.assertEqual(db.execute('SELECT count(*) FROM run_heads').fetchone(),(1,))
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),old)
    def test_duplicate_head(self):
        self.modify('INSERT INTO run_heads VALUES (?,?,?,?)',self.key)
        with self.snapshot() as db,self.assertRaisesRegex(ValueError,'HEAD_COUNT'):require_single_head(Cursor(db),self.key)
    def test_absent_head(self):
        with self.snapshot() as db,self.assertRaisesRegex(ValueError,'HEAD_COUNT'):require_single_head(Cursor(db),('other',*self.key[1:]))
    def test_no_unrelated_read(self):
        with self.snapshot() as db,self.assertRaises(sqlite3.DatabaseError):db.execute('SELECT secret FROM unrelated').fetchall()
    def test_no_write(self):
        with self.snapshot() as db,self.assertRaises(sqlite3.DatabaseError):db.execute('DELETE FROM run_heads')
    def test_no_attach(self):
        with self.snapshot() as db,self.assertRaises(sqlite3.DatabaseError):db.execute("ATTACH DATABASE ':memory:' AS other")
    def test_no_unapproved_function(self):
        with self.snapshot() as db,self.assertRaises(sqlite3.DatabaseError):db.execute('SELECT random()')
    def test_no_pragma(self):
        with self.snapshot() as db,self.assertRaises(sqlite3.DatabaseError):db.execute('PRAGMA query_only=OFF')
    def test_missing_table(self):
        self.modify('DROP TABLE events')
        with self.assertRaisesRegex(ValueError,'SCHEMA'),self.snapshot():pass
    def test_view_instead_of_table(self):
        self.modify('DROP TABLE events');self.modify('CREATE VIEW events AS SELECT id FROM outbox')
        with self.assertRaisesRegex(ValueError,'SCHEMA'),self.snapshot():pass
    def test_unrelated_trigger(self):
        self.modify('CREATE TRIGGER hidden AFTER INSERT ON unrelated BEGIN SELECT 1; END')
        with self.assertRaisesRegex(ValueError,'SCHEMA'),self.snapshot():pass
    def test_sidecar_hold(self):
        Path(str(self.path)+'-wal').touch()
        with self.assertRaisesRegex(ValueError,'PATH'),self.snapshot():pass
    def test_wrong_name(self):
        with self.assertRaisesRegex(ValueError,'PATH'),lifecycle_snapshot(self.path,'lifecycle-prefix.d0.sqlite'):pass
    def test_snapshot_blocks_writer_commit(self):
        # A single read transaction protects the observation; not a PostgreSQL race proof.
        with self.snapshot() as db,closing(sqlite3.connect(self.path,timeout=.01)) as writer:
            writer.execute('INSERT INTO run_heads VALUES (?,?,?,?)',('other',*self.key[1:]))
            with self.assertRaises(sqlite3.OperationalError):writer.commit()
            writer.rollback()
            require_single_head(Cursor(db),self.key)
