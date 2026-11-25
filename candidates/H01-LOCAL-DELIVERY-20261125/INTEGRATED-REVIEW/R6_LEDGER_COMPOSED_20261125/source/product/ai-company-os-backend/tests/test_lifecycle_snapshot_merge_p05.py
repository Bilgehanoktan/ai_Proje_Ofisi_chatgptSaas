import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from app.core.development_review.lifecycle_read_snapshot import TABLES, lifecycle_snapshot, require_single_head

class Cursor:
    def __init__(self,db): self.c=db.cursor()
    def execute(self,sql,params=()): return self.c.execute(sql.replace('t1_candidate.','').replace('%s','?'),params)
    def fetchone(self): return self.c.fetchone()

class MergeTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.p=Path(t.name).resolve()/'lifecycle.d0.sqlite'
        self.key=('tenant','company','env','run')
        with closing(sqlite3.connect(self.p)) as db,db:
            for table in sorted(TABLES):
                db.execute('CREATE TABLE '+table+(' (tenant_id TEXT,company_id TEXT,environment_id TEXT,run_id TEXT)' if table=='run_heads' else ' (id INTEGER)'))
            db.execute('INSERT INTO run_heads VALUES (?,?,?,?)',self.key)
            db.execute('CREATE TABLE unrelated(secret TEXT)')
    def snap(self):return lifecycle_snapshot(self.p,self.p.name)
    def change(self,sql):
        with closing(sqlite3.connect(self.p)) as db,db:db.execute(sql)
    def test_exact_read_and_hash(self):
        before=hashlib.sha256(self.p.read_bytes()).hexdigest()
        with self.snap() as db:require_single_head(Cursor(db),self.key)
        self.assertEqual(before,hashlib.sha256(self.p.read_bytes()).hexdigest())
    def test_authorizer(self):
        with self.snap() as db:
            for sql in ('SELECT secret FROM unrelated','DELETE FROM run_heads','SELECT random()','PRAGMA query_only=OFF',"ATTACH DATABASE ':memory:' AS other"):
                with self.subTest(sql=sql),self.assertRaises(sqlite3.DatabaseError):db.execute(sql).fetchall()
    def test_duplicate_head(self):
        self.change("INSERT INTO run_heads VALUES ('tenant','company','env','run')")
        with self.snap() as db,self.assertRaisesRegex(ValueError,'HEAD_COUNT'):require_single_head(Cursor(db),self.key)
    def test_missing_table(self):
        self.change('DROP TABLE events')
        with self.assertRaisesRegex(ValueError,'SCHEMA'),self.snap():pass
    def test_view(self):
        self.change('DROP TABLE events');self.change('CREATE VIEW events AS SELECT id FROM outbox')
        with self.assertRaisesRegex(ValueError,'SCHEMA'),self.snap():pass
    def test_trigger(self):
        self.change('CREATE TRIGGER hidden AFTER INSERT ON unrelated BEGIN SELECT 1; END')
        with self.assertRaisesRegex(ValueError,'SCHEMA'),self.snap():pass
    def test_sidecars_before_and_after(self):
        for suffix in ('-wal','-shm','-journal'):
            s=Path(str(self.p)+suffix);s.touch()
            try:
                with self.subTest(suffix=suffix),self.assertRaisesRegex(ValueError,'PATH'),self.snap():pass
            finally:s.unlink()
        s=Path(str(self.p)+'-wal')
        try:
            with self.assertRaisesRegex(ValueError,'PATH'):
                with self.snap():s.touch()
        finally:s.unlink(missing_ok=True)
    def test_empty_file(self):
        self.p.write_bytes(b'')
        with self.assertRaisesRegex(ValueError,'PATH'),self.snap():pass
    def test_deadline(self):
        with patch('app.core.development_review.lifecycle_read_snapshot.time.monotonic',side_effect=[10.0,13.0]):
            with self.assertRaisesRegex(ValueError,'DEADLINE'),self.snap():pass
    def test_writer_blocked(self):
        with self.snap() as db,closing(sqlite3.connect(self.p,timeout=.01)) as writer:
            writer.execute("INSERT INTO run_heads VALUES ('other','company','env','run')")
            with self.assertRaises(sqlite3.OperationalError):writer.commit()
            writer.rollback();require_single_head(Cursor(db),self.key)
    def test_exception_cleanup(self):
        before=hashlib.sha256(self.p.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with self.snap() as db:raise RuntimeError('injected')
        with self.assertRaises(sqlite3.ProgrammingError):db.execute('SELECT 1')
        self.assertEqual(before,hashlib.sha256(self.p.read_bytes()).hexdigest())
