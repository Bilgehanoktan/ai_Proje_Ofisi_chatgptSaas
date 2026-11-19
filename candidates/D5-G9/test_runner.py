"""Synthetic launcher mechanics only; not product tests."""
from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
import json
import tempfile
import unittest
import run_exact_checkout as r


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()/'root'
        self.stage = self.root.parent/'stage'
        self.stage.mkdir()
        self.files = {}
        self.pins = {}
        for i in range(403):
            key = ('ai-company-os-backend/' if i < 248 else 'ai-company-os-frontend/')+f'f{i}.txt'
            data = f'file {i}'.encode()
            self.files[key] = dict(bytes=len(data),sha256=sha256(data).hexdigest())
            if i < 248:
                self.put('product/'+key,data)
            if i < 29:
                self.pins['product/'+key] = r.blob(data)
        for i in range(26):
            rel=f'candidates/fixture/f{i}.txt'
            self.put(rel,b'fixture')
            self.pins[rel]=r.blob(b'fixture')
        self.put(r.FIXTURE,b'original test')
        self.pins[r.FIXTURE]=r.blob(b'original test')
        m=json.dumps(dict(files=self.files)).encode()
        p=json.dumps(self.pins).encode()
        self.put('product/SOURCE_MANIFEST.json',m)
        self.put(r.PINS,p)
        mocks=patch.multiple(r,MANIFEST=r.blob(m),PIN_BLOB=r.blob(p),FIXTURE_BLOB=r.blob(b'original test'))
        mocks.start(); self.addCleanup(mocks.stop)

    def put(self, rel, data):
        p=self.root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)

    def test_exact_staging(self):
        report=r.stage_exact(self.root,self.stage)
        self.assertEqual((report['backend_verified'],report['selected_pins_verified'],report['external_pins_verified']),(248,56,27))
        self.assertEqual(len(list(p for p in self.stage.rglob('*') if p.is_file())),277)
        self.assertEqual((self.stage/r.FIXTURE).read_bytes(),b'original test')
        self.assertEqual((self.root/r.FIXTURE).read_bytes(),b'original test')

    def test_manifest_tamper(self):
        self.put('product/SOURCE_MANIFEST.json',b'{}')
        with self.assertRaisesRegex(ValueError,'MANIFEST_HOLD'): r.stage_exact(self.root,self.stage)

    def test_unpinned_backend_tamper(self):
        self.put('product/ai-company-os-backend/f100.txt',b'file 999')
        with self.assertRaisesRegex(ValueError,'SOURCE_SHA_HOLD'): r.stage_exact(self.root,self.stage)

    def test_external_tamper(self):
        self.put(r.FIXTURE,b'fake test')
        with self.assertRaisesRegex(ValueError,'SOURCE_PIN_HOLD'): r.stage_exact(self.root,self.stage)

    def test_missing_external(self):
        (self.root/r.FIXTURE).unlink()
        with self.assertRaisesRegex(ValueError,'SOURCE_MISSING'): r.stage_exact(self.root,self.stage)

    def test_pin_manifest_tamper(self):
        self.put(r.PINS,b'{}')
        with self.assertRaisesRegex(ValueError,'PIN_MANIFEST_HOLD'): r.stage_exact(self.root,self.stage)

    def test_path_escape(self):
        for rel in ('../escape','/absolute','C:/x','a\\b'):
            with self.assertRaisesRegex(ValueError,'PATH_HOLD'): r.read(self.root,rel)

    def test_result_exact(self):
        summary=dict(tests=7,failures=0,errors=0,skips=0,expected_failures=0,unexpected_successes=0)
        line=lambda s: ('RESULT_JSON='+json.dumps(s)+'\n').encode()
        self.assertTrue(r.result_ok(0,line(summary)))
        self.assertFalse(r.result_ok(1,line(summary)))
        self.assertFalse(r.result_ok(0,line(summary)+line(summary)))
        self.assertFalse(r.result_ok(0,b'OK\n'))
        for field in ('failures','errors','skips','expected_failures','unexpected_successes'):
            self.assertFalse(r.result_ok(0,line(summary|{field:1})))
        self.assertFalse(r.result_ok(0,line(summary|{'tests':6})))


if __name__ == '__main__': unittest.main(verbosity=2)
