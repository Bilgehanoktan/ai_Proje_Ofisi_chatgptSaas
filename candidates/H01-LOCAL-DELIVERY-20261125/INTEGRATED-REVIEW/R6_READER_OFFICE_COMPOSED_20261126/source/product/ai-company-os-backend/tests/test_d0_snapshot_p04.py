import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from app.core.development_review.d0_snapshot import open_d0_snapshot, MAX_BYTES

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve(); self.p = self.root/'lifecycle.d0.sqlite'
        with sqlite3.connect(self.p) as db:
            db.execute('CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('INSERT INTO sample VALUES (1,?)', ('historical',))
        db.close()

    def test_actual_read_preserves_hash(self):
        before = hashlib.sha256(self.p.read_bytes()).hexdigest()
        with open_d0_snapshot(self.p, self.p.name) as c:
            c.execute('SELECT value FROM t1_candidate.sample WHERE id=%s', (1,))
            self.assertEqual(c.fetchone(), ('historical',)); self.assertIsNone(c.fetchone())
        self.assertEqual(before, hashlib.sha256(self.p.read_bytes()).hexdigest())

    def test_reject_write_attach_and_multiple_statements(self):
        with open_d0_snapshot(self.p, self.p.name) as c:
            for sql in ('UPDATE sample SET value=0','ATTACH DATABASE \'x\' AS other','PRAGMA query_only=OFF','SELECT 1; SELECT 2','SELECT 1 FOR UPDATE'):
                with self.subTest(sql=sql),self.assertRaises(ValueError): c.execute(sql)
            # Guard plus actual SQLite read-only connection, even if bypassing wrapper.
            with self.assertRaises(sqlite3.OperationalError): c.cursor.execute('DELETE FROM sample')

    def test_cursor_closed(self):
        with open_d0_snapshot(self.p, self.p.name) as c: c.execute('SELECT 1')
        with self.assertRaises(sqlite3.ProgrammingError): c.fetchone()

    def test_missing_does_not_create(self):
        p=self.root/'missing'/'lifecycle.d0.sqlite'
        with self.assertRaises(ValueError):
            with open_d0_snapshot(p,p.name): pass
        self.assertFalse(p.exists())

    def test_wrong_name(self):
        with self.assertRaises(ValueError):
            with open_d0_snapshot(self.p,'lifecycle-prefix.d0.sqlite'): pass

    def test_relative_path(self):
        with self.assertRaises(ValueError):
            with open_d0_snapshot(Path('lifecycle.d0.sqlite'),'lifecycle.d0.sqlite'): pass

    def test_empty_file(self):
        self.p.write_bytes(b'')
        with self.assertRaises(ValueError):
            with open_d0_snapshot(self.p,self.p.name): pass

    def test_oversize(self):
        with self.p.open('r+b') as f: f.truncate(MAX_BYTES+1)
        with self.assertRaises(ValueError):
            with open_d0_snapshot(self.p,self.p.name): pass

    def test_sidecars(self):
        for suffix in ('-wal','-shm','-journal'):
            sidecar=Path(str(self.p)+suffix);sidecar.touch()
            try:
                with self.subTest(suffix=suffix),self.assertRaises(ValueError):
                    with open_d0_snapshot(self.p,self.p.name): pass
            finally:sidecar.unlink()

    def test_sidecar_appears_during_read(self):
        sidecar=Path(str(self.p)+'-wal')
        try:
            with self.assertRaisesRegex(ValueError,'SIDECAR'):
                with open_d0_snapshot(self.p,self.p.name): sidecar.touch()
        finally:sidecar.unlink(missing_ok=True)

    def test_symlink(self):
        alias=self.root/'link';alias.mkdir();p=alias/self.p.name
        try:p.symlink_to(self.p)
        except OSError:self.skipTest('symlink not available')
        with self.assertRaises(ValueError):
            with open_d0_snapshot(p,p.name): pass

    def test_deadline_holds(self):
        with patch('app.core.development_review.d0_snapshot.time.monotonic',side_effect=[10.0,13.0]):
            with self.assertRaisesRegex(ValueError,'DEADLINE'):
                with open_d0_snapshot(self.p,self.p.name): pass

    def test_exception_cleanup_preserves_hash(self):
        before=hashlib.sha256(self.p.read_bytes()).hexdigest()
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with open_d0_snapshot(self.p,self.p.name) as c: raise RuntimeError('injected')
        with self.assertRaises(sqlite3.ProgrammingError):c.fetchone()
        self.assertEqual(before,hashlib.sha256(self.p.read_bytes()).hexdigest())
