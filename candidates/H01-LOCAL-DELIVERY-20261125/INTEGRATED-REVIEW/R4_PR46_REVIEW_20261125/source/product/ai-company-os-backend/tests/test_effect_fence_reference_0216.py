import concurrent.futures
from dataclasses import replace
from pathlib import Path
import shutil
import sqlite3
import tempfile
import threading
import unittest

from app.core.transaction.effect_fence_reference import D0EffectFenceReference, Head, Intent, external_effect_decision


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'d0.effect-reference.sqlite'
        self.h = Head(1,'a'*64,1)
        self.i = Intent('b'*64,'c'*64,'tx1','d'*64)
        self.f = D0EffectFenceReference.create(self.path,self.h)

    def test_receipt_denies_real_effect(self):
        r = self.f.consume_synthetic(self.h,self.i)
        self.assertEqual((r.status,r.intent,r.head),('D0_SYNTHETIC_CONSUMED',self.i,self.h))
        self.assertFalse(r.external_effect_allowed or r.independent_verified or r.retry_allowed)
        self.assertEqual(external_effect_decision(),'EXTERNAL_EFFECT_HOLD')

    def test_reopen_replay(self):
        self.f.consume_synthetic(self.h,self.i)
        with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED'):
            D0EffectFenceReference(self.path).consume_synthetic(self.h,self.i)

    def test_scope_conflict(self):
        self.f.consume_synthetic(self.h,self.i)
        with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED'):
            self.f.consume_synthetic(self.h,replace(self.i,binding_sha='e'*64,transaction_ref='tx2'))

    def test_binding_conflict(self):
        self.f.consume_synthetic(self.h,self.i)
        with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED'):
            self.f.consume_synthetic(self.h,replace(self.i,scope_sha='e'*64,transaction_ref='tx2'))

    def test_tx_conflict(self):
        self.f.consume_synthetic(self.h,self.i)
        with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED'):
            self.f.consume_synthetic(self.h,replace(self.i,scope_sha='e'*64,binding_sha='f'*64))

    def test_stale_head(self):
        new=Head(2,'e'*64,2)
        self.f.advance(self.h,new)
        with self.assertRaisesRegex(ValueError,'STALE_HEAD'):
            self.f.consume_synthetic(self.h,self.i)
        self.assertEqual(self.f.consume_synthetic(new,self.i).head,new)

    def test_nonmonotonic(self):
        for new in (Head(3,'e'*64,2),Head(2,'a'*64,2),Head(2,'e'*64,0)):
            with self.assertRaises(ValueError): self.f.advance(self.h,new)
        self.f.advance(self.h,Head(2,'e'*64,2))
        with self.assertRaisesRegex(ValueError,'HEAD_CAS'):
            self.f.advance(Head(2,'e'*64,2),Head(3,'f'*64,1))

    def test_bad_input(self):
        for bad in (replace(self.i,scope_sha='x'),replace(self.i,transaction_ref=''),replace(self.i,request_sha='A'*64)):
            with self.assertRaisesRegex(ValueError,'INTENT_SHAPE'):
                self.f.consume_synthetic(self.h,bad)
        self.f.consume_synthetic(self.h,self.i)

    def test_concurrent_claim(self):
        barrier=threading.Barrier(2)
        def attempt():
            barrier.wait(timeout=5)
            try: self.f.consume_synthetic(self.h,self.i); return 'PASS'
            except ValueError as e: return str(e)
        with concurrent.futures.ThreadPoolExecutor(2) as ex:
            results=list(ex.map(lambda _:attempt(),range(2)))
        self.assertCountEqual(results,['PASS','ALREADY_CONSUMED_HOLD'])

    def test_append_only(self):
        self.f.consume_synthetic(self.h,self.i)
        with sqlite3.connect(self.path) as db:
            for sql in ('DELETE FROM consumed','UPDATE heads SET epoch=2','INSERT OR REPLACE INTO consumed SELECT * FROM consumed'):
                with self.assertRaises(sqlite3.IntegrityError): db.execute(sql)

    def test_reference_restore_residual(self):
        backup=self.path.with_suffix('.backup')
        shutil.copyfile(self.path,backup)
        self.f.consume_synthetic(self.h,self.i)
        shutil.copyfile(backup,self.path)
        # Expected residual: restoring the reference store itself defeats local replay protection.
        self.assertEqual(self.f.consume_synthetic(self.h,self.i).status,'D0_SYNTHETIC_CONSUMED')

    def test_product_restore_does_not_reset_reference(self):
        product=Path(self.tmp.name)/'product.sqlite'
        with sqlite3.connect(product) as db: db.execute('CREATE TABLE sample(x)')
        backup=product.with_suffix('.backup'); shutil.copyfile(product,backup)
        self.f.consume_synthetic(self.h,self.i)
        with sqlite3.connect(product) as db: db.execute('INSERT INTO sample VALUES (1)')
        shutil.copyfile(backup,product)
        with self.assertRaisesRegex(ValueError,'ALREADY_CONSUMED'):
            self.f.consume_synthetic(self.h,self.i)

    def test_missing_store_fails(self):
        self.path.unlink()
        with self.assertRaises(sqlite3.OperationalError): self.f.consume_synthetic(self.h,self.i)
        self.assertFalse(self.path.exists())


if __name__ == '__main__': unittest.main()
