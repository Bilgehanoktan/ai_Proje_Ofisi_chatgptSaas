"""Local SQLite archive tests; not PostgreSQL or independent custody evidence."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from app.core.event_store.retained_history import ReferenceReader, ReferenceStore, digest, reference_bytes, history_reference, RetainedReview


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / 'references.db'; self.store = ReferenceStore(self.path)
        self.body = history_reference({'id':'p'}, 'rev', (), None)

    def test_reopen(self):
        key = self.store.put(self.body)
        self.assertEqual(ReferenceReader(self.path).read(key), self.body)

    def test_read_only_missing_archive(self):
        path = self.path.with_name('absent.db')
        with self.assertRaises(sqlite3.OperationalError): ReferenceReader(path).read('0'*64)
        self.assertFalse(path.exists())

    def test_idempotent(self):
        self.assertEqual(self.store.put(self.body), self.store.put(self.body))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM reference_objects').fetchone(), (1,))

    def test_changed_reference(self):
        a = self.store.put(self.body)
        b = self.store.put(history_reference({'id':'q'}, 'rev', (), None))
        self.assertNotEqual(a, b); self.assertEqual(self.store.read(a), self.body)

    def test_missing(self):
        with self.assertRaises(ValueError): self.store.read('0'*64)

    def test_bad_digest(self):
        with self.assertRaises(ValueError): self.store.read('../x')

    def test_update_delete_blocked(self):
        key = self.store.put(self.body)
        with closing(sqlite3.connect(self.path)) as db:
            for sql in ('UPDATE reference_objects SET body=? WHERE digest=?', 'DELETE FROM reference_objects WHERE body=? AND digest=?'):
                with self.assertRaises(sqlite3.IntegrityError): db.execute(sql, (self.body, key))

    def test_replace_blocked(self):
        key = self.store.put(self.body)
        with closing(sqlite3.connect(self.path)) as db:
            with self.assertRaises(sqlite3.IntegrityError): db.execute('INSERT OR REPLACE INTO reference_objects VALUES (?,?)', (key,b'changed'))
        self.assertEqual(self.store.read(key), self.body)

    def test_tamper_detected(self):
        key = self.store.put(self.body)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DROP TRIGGER reference_no_update')
            db.execute('UPDATE reference_objects SET body=? WHERE digest=?', (b'changed', key))
        with self.assertRaises(ValueError): self.store.read(key)

    def test_type_separation(self):
        for a, b in ((True,1), ([],()), ({'a':1}, [('a',1)])):
            self.assertNotEqual(reference_bytes('plan-history-v1', a), reference_bytes('plan-history-v1', b))

    def test_domain_separation(self):
        self.assertNotEqual(digest(reference_bytes('plan-history-v1', ())), digest(reference_bytes('terminal-command-v1', ())))

    def test_dict_order(self):
        self.assertEqual(reference_bytes('plan-history-v1', {'a':1,'b':2}), reference_bytes('plan-history-v1', {'b':2,'a':1}))

    def test_unsupported_and_size(self):
        for value in (object(), 1.5, 'x'*4097):
            with self.assertRaises(ValueError): reference_bytes('plan-history-v1', value)
        with self.assertRaises(ValueError): digest(b'x'*(8*1024*1024+1))

    def test_no_authority(self):
        r = RetainedReview('test', reference_match=True)
        self.assertEqual(r.decision,'HOLD'); self.assertFalse(r.independent_verified or r.dispatch_allowed or r.release_ready)


if __name__ == '__main__': unittest.main()
