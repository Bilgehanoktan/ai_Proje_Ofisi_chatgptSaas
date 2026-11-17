"""Isolated historical-source materializer and W8 hook tests; no product acceptance."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import w8_p10j24 as p


def info(name, raw):
    return {'path':name,'bytes':len(raw),'git_blob':p.blob(raw),'sha256':hashlib.sha256(raw).hexdigest()}


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.a = tempfile.TemporaryDirectory()
        self.b = tempfile.TemporaryDirectory()
        self.stage, self.dest = Path(self.a.name).resolve(), Path(self.b.name).resolve()
        self.old, self.new = b'old-source', b'new-source'
        (self.stage/'product.py').write_bytes(self.new)
        (self.stage/'historical.py').write_bytes(self.old)
        (self.stage/'unchanged.py').write_bytes(b'common')
        self.entries = [info('product.py', self.old), info('unchanged.py', b'common')]

    def tearDown(self):
        self.a.cleanup(); self.b.cleanup()

    def test_overlay_preserves_current_product(self):
        p.materialize_locked(self.stage,self.dest,self.entries,{'product.py':'historical.py'})
        self.assertEqual((self.dest/'product.py').read_bytes(),self.old)
        self.assertEqual((self.stage/'product.py').read_bytes(),self.new)
        self.assertEqual((self.dest/'unchanged.py').read_bytes(),b'common')

    def test_old_source_tamper_rejected(self):
        (self.stage/'historical.py').write_bytes(b'bad-source')
        with self.assertRaisesRegex(ValueError,'SOURCE_PIN_HOLD'):
            p.materialize_locked(self.stage,self.dest,self.entries,{'product.py':'historical.py'})

    def test_current_shared_tamper_rejected(self):
        (self.stage/'unchanged.py').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'SOURCE_PIN_HOLD'):
            p.materialize_locked(self.stage,self.dest,self.entries,{'product.py':'historical.py'})

    def test_duplicate_lock_path_rejected(self):
        with self.assertRaisesRegex(ValueError,'LOCK_SCOPE_HOLD'):
            p.materialize_locked(self.stage,self.dest,self.entries+self.entries,{'product.py':'historical.py'})

    def test_unlisted_replacement_rejected(self):
        with self.assertRaisesRegex(ValueError,'LOCK_SCOPE_HOLD'):
            p.materialize_locked(self.stage,self.dest,self.entries,{'other.py':'historical.py'})

    def test_nonempty_dest_rejected(self):
        (self.dest/'other').touch()
        with self.assertRaisesRegex(ValueError,'DESTINATION_HOLD'):
            p.materialize_locked(self.stage,self.dest,self.entries,{'product.py':'historical.py'})

    def test_unsafe_path_rejected(self):
        for name in ['../outside','/absolute','a\\b','a/../b','a//b']:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):
                p.safe_path(self.stage,name)

    def test_invalid_history_lock_rejected(self):
        lock=self.stage/p.LOCK;lock.parent.mkdir(parents=True);lock.write_text('{}')
        with self.assertRaisesRegex(ValueError,'LOCK_PIN_HOLD'):
            p.materialize_history(self.stage,self.dest)

    def mock_w(self, mode):
        calls=[]
        def run(args,cwd,env=None):
            args=list(map(str,args));calls.append(args)
            if args[1]==str(self.stage/p.RUNNER):
                self.assertNotEqual(args[3],str(self.stage));self.assertTrue(Path(args[3]).is_dir())
                if mode=='fail': raise RuntimeError('test failure')
            return 0
        w=SimpleNamespace(MANIFEST_BLOB=p.CANDIDATE_MANIFEST,verify_aux=lambda root:{},installed=lambda *x:None,reviewed=lambda *x:None,python=lambda s:s/'python',run=run)
        def inherited(stage,approval):
            args=[w.python(stage),stage/p.RUNNER,'--source',stage,'--report',stage/'core29-p10f.json']
            if mode=='wrong': args[4]='--other'
            if mode!='skip':w.run(args,stage,{})
            if mode=='duplicate':w.run(args,stage,{})
            w.run(['node','current-product-test'],stage,{})
            (stage/'BUILD_TEST_OK').write_text(approval)
        w.test=inherited
        p.extend_candidate(w)
        w.verify_aux=lambda root:{}  # synthetic hook isolation; actual aux pins are separate
        return w,run,calls

    def test_hook_success_rewrites_only_historical_call(self):
        w,original,calls=self.mock_w('ok')
        with patch.object(p,'materialize_history') as materialize:
            w.test(self.stage,'approval');materialize.assert_called_once()
        self.assertEqual(calls[1],['node','current-product-test']);self.assertIs(w.run,original)
        self.assertFalse(Path(calls[0][3]).exists());self.assertEqual((self.stage/'BUILD_TEST_OK').read_text(),'approval')

    def test_hook_failure_clears_markers_and_restores_runner(self):
        for mode in ['skip','wrong','duplicate','fail']:
            with self.subTest(mode=mode):
                for marker in p.MARKERS:(self.stage/marker).touch()
                w,original,calls=self.mock_w(mode)
                with patch.object(p,'materialize_history'), self.assertRaises((RuntimeError,ValueError)):
                    w.test(self.stage,'approval')
                self.assertIs(w.run,original)
                self.assertTrue(all(not (self.stage/m).exists() for m in p.MARKERS))


if __name__=='__main__':unittest.main()
