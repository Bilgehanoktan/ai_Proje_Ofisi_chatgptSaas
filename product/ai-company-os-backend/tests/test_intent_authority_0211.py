from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Event, Barrier
from unittest import TestCase
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin


class IntentAuthorityTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'root.authority.sqlite'
        self.root = RootPin('a'*64, 'b'*64, 1)
        self.new = RootPin('c'*64, 'b'*64, 2)
        self.a = D0IntentAuthority.create(self.path, self.root)

    def claim(self, root=None, scope='d', binding='e', tx='tx'):
        return self.a.claim_and_fence(root or self.root, scope*64, binding*64, tx, 'f'*64)

    def test_joint_product_restore_no_second_attempt(self):
        # Product stores are disposable files, not an actual original T1 mapping.
        j, t = self.path.with_name('journal'), self.path.with_name('t1')
        j.write_bytes(b'old'); t.write_bytes(b'old')
        with self.claim():
            j.write_bytes(b'new'); t.write_bytes(b'new')
        j.write_bytes(b'old'); t.write_bytes(b'old')
        self.a = D0IntentAuthority(self.path)
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'):
            with self.claim(): self.fail('replay')

    def test_exception_consumes_claim(self):
        with self.assertRaises(RuntimeError):
            with self.claim(): raise RuntimeError('lost outcome')
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'):
            with self.claim(): self.fail('retry')

    def test_publisher_waits_through_fence(self):
        started, done = Event(), Event()
        def publish():
            started.set(); self.a.publish(self.root, self.new); done.set()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with self.claim():
                job = pool.submit(publish)
                self.assertTrue(started.wait(1)); self.assertFalse(done.wait(.15))
            job.result(timeout=4)
        self.assertTrue(done.is_set())
        with self.assertRaisesRegex(ValueError, 'ROOT_HOLD'):
            with self.claim(scope='1', binding='2', tx='new'): self.fail('stale root')

    def test_revocation_first(self):
        self.a.publish(self.root, self.new)
        with self.assertRaisesRegex(ValueError, 'ROOT_HOLD'):
            with self.claim(): self.fail('stale root')
        with self.claim(self.new): pass

    def test_two_claims_one_winner(self):
        barrier = Barrier(2, timeout=3)
        def try_claim():
            barrier.wait()
            try:
                with self.claim(): return 'winner'
            except ValueError as e: return str(e)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(try_claim) for _ in range(2)]
            self.assertCountEqual([j.result(timeout=5) for j in jobs], ['winner','D0_AUTHORITY_ALREADY_CLAIMED_HOLD'])

    def test_cas_monotonic_and_key(self):
        for bad in (RootPin('c'*64,'0'*64,2), RootPin('a'*64,'b'*64,2), RootPin('c'*64,'b'*64,0)):
            with self.assertRaises(ValueError): self.a.publish(self.root, bad)
        self.a.publish(self.root, self.new)
        with self.assertRaisesRegex(ValueError, 'CAS'):
            self.a.publish(self.root, RootPin('9'*64,'b'*64,3))
        with self.assertRaisesRegex(ValueError, 'CAS'):
            self.a.publish(self.new, RootPin('9'*64,'b'*64,1))

    def test_scope_survives_root_advance(self):
        with self.claim(): pass
        self.a.publish(self.root,self.new)
        with self.assertRaisesRegex(ValueError, 'ALREADY_CLAIMED'):
            with self.claim(self.new,binding='1',tx='different'): self.fail('replay')

    def test_append_only(self):
        with self.claim(): pass
        with closing(sqlite3.connect(self.path)) as db:
            for sql in ('DELETE FROM claims','UPDATE claims SET tx=\'other\'','INSERT OR REPLACE INTO claims SELECT * FROM claims','DELETE FROM roots','UPDATE roots SET epoch=9','INSERT OR REPLACE INTO roots SELECT * FROM roots'):
                with self.assertRaises(sqlite3.IntegrityError): db.execute(sql)

    def test_missing_and_existing(self):
        with self.assertRaises(FileExistsError): D0IntentAuthority.create(self.path,self.root)
        self.path.unlink()
        with self.assertRaises(sqlite3.OperationalError):
            with self.claim(): self.fail('missing store initialized')
        self.assertFalse(self.path.exists())

    def test_root_restore_limitation(self):
        # If the authority itself is restored, the fixture cannot prove freshness.
        before = self.path.read_bytes()
        with self.claim(): pass
        self.path.write_bytes(before)
        with self.claim(): pass  # Reproduced residual, NOT a security pass.
