from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app.core.development_review.atomic_sample import AtomicSample


class AtomicTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'test.atomic.d0.sqlite'
        self.store = AtomicSample(self.path)
        self.store.create()

    def test_heartbeat(self):
        self.assertEqual(self.store.renew('demo-a',None,1,5),1)
        self.assertEqual(self.store.renew('demo-a',1,3,10),1)
        self.assertEqual(self.store.observe('demo-x','demo-a',1,12,0),'SAMPLE_OBSERVED')

    def test_expiry_and_fence(self):
        self.store.renew('demo-a',None,1,3)
        with self.assertRaises(ValueError): self.store.renew('demo-a',1,4,3)
        self.assertEqual(self.store.renew('demo-b',None,4,3),2)
        with self.assertRaises(ValueError): self.store.observe('demo-x','demo-a',1,4,0)

    def test_clock_and_busy(self):
        self.store.renew('demo-a',None,4,5)
        for args in [('demo-a',1,3,5),('demo-a',1,4,5),('demo-b',1,5,5),('demo-a',None,5,5)]:
            with self.assertRaises(ValueError): self.store.renew(*args)

    def test_atomic_reopen_and_duplicate(self):
        self.store.renew('demo-a',None,1,5)
        args=('demo-x','demo-a',1,2,0)
        self.assertEqual(self.store.observe(*args),'SAMPLE_OBSERVED')
        again=AtomicSample(self.path)
        self.assertEqual(again.observe(*args),'DUPLICATE_IGNORED')
        with self.assertRaises(ValueError): again.observe('demo-x','demo-a',1,3,0)
        self.assertEqual(again.snapshot()['counts'],{'event':1,'audit':1,'outbox':1})
        self.assertFalse(again.snapshot()['dispatch_allowed'])

    def test_rollback(self):
        self.store.renew('demo-a',None,1,5)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER fail BEFORE INSERT ON outbox BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.store.observe('demo-x','demo-a',1,2,0)
        self.assertEqual(self.store.snapshot()['head'],(0,'PENDING'))
        self.assertEqual(self.store.snapshot()['counts'],{'event':0,'audit':0,'outbox':0})

    def test_concurrent_acquire(self):
        def claim(holder):
            try: return self.store.renew(holder,None,1,5)
            except ValueError: return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(claim,['demo-a','demo-b'])),[1,None])

    def test_no_overwrite(self):
        with self.assertRaises(FileExistsError): self.store.create()
        self.assertEqual(self.store.snapshot()['head'],(0,'PENDING'))

    def test_scope_and_meta(self):
        with self.assertRaises(ValueError): AtomicSample(self.path,tenant='other')
        with self.assertRaises(ValueError): AtomicSample(self.path,company='other')
        self.assertEqual(self.store.snapshot()['tenant'],'synthetic-tenant')
        with closing(sqlite3.connect(self.path)) as db, db: db.execute('DELETE FROM meta')
        with self.assertRaises(ValueError): self.store.snapshot()

    def test_cas_and_terminal(self):
        self.store.renew('demo-a',None,1,5)
        with self.assertRaises(ValueError): self.store.observe('demo-x','demo-a',1,2,1)
        self.store.observe('demo-x','demo-a',1,2,0)
        with self.assertRaises(ValueError): self.store.renew('demo-a',1,3,5)


if __name__ == '__main__': unittest.main()
