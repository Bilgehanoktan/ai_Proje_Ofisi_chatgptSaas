"""Adapter-only tests. Smoke doubles exercise control flow, not actual Next/Phaser."""
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import w8_ux_a0b as a
from native_ux_a0b import local_origin


class ExactChain(unittest.TestCase):
    def test_actual_parent_chain_rebound(self):
        w = a.load_candidate()
        self.assertEqual(w.MANIFEST_BLOB, a.MANIFEST)
        self.assertEqual(w.verify.__defaults__[0], a.MANIFEST)
        for name, expected in a.PARENT_PINS.items():
            self.assertEqual(a.blob((Path(a.__file__).parent/name).read_bytes()), expected)

    def test_wrong_manifest_pin_rejected(self):
        w = a.load_candidate()
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError,'P10F_MANIFEST_PIN_HOLD'):
            w.verify(Path(tmp),pin='0'*40,clean=True)

    def test_missing_checkout_rejected_by_original(self):
        w = a.load_candidate()
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError,'missing or wrong SOURCE_MANIFEST'):
            w.verify(Path(tmp),clean=True)

    def test_missing_review_blocks_test_and_smoke(self):
        w = a.load_candidate()
        with tempfile.TemporaryDirectory() as tmp:
            stage=Path(tmp)
            for call in (lambda:w.test(stage,'0'*64),lambda:w.smoke(stage,'0'*64,Path('chromium'))):
                with self.assertRaisesRegex(ValueError,'missing or wrong SOURCE_MANIFEST'):
                    call()
            self.assertFalse((stage/'BUILD_TEST_OK').exists())
            self.assertFalse((stage/'SMOKE_OK').exists())
            self.assertFalse((stage/'NATIVE_SMOKE_OK').exists())

    def test_pin_exact_and_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'x';p.write_bytes(b'a')
            self.assertEqual(a.checked_pin(root,'x',a.blob(b'a')),p)
            p.write_bytes(b'b')
            with self.assertRaisesRegex(ValueError,'PIN_HOLD'):
                a.checked_pin(root,'x',a.blob(b'a'))

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'x';p.write_bytes(b'a');q=root/'y'
            try:q.symlink_to(p)
            except OSError:self.skipTest('symlink unavailable')
            with self.assertRaisesRegex(ValueError,'PIN_HOLD'):
                a.checked_pin(root,'y',a.blob(b'a'))

    def test_loopback_origin_only(self):
        self.assertEqual(local_origin('http://127.0.0.1:17300/'),'http://127.0.0.1:17300')
        for url in ('https://127.0.0.1:17300','http://localhost:17300','http://127.0.0.1:17300/x','http://127.0.0.1:17300/?q=1','http://user@127.0.0.1:17300','http://example.org:17300'):
            with self.subTest(url=url), self.assertRaises(ValueError):local_origin(url)


class SmokeControlFlow(unittest.TestCase):
    # Deliberate test doubles. These never run or approve the product.
    def exercise(self, mode):
        with tempfile.TemporaryDirectory() as tmp:
            stage=Path(tmp);script=stage/a.NATIVE_PATH;script.parent.mkdir(parents=True)
            shutil.copy2(Path(a.__file__).parent/'native_ux_a0b.py',script)
            calls=[];approval='a'*64
            def run(args,cwd,env):
                calls.append(str(args[1]))
                if mode=='native_failure' and str(args[1])==str(script):raise ValueError('synthetic native failure')
            def smoke(stage,approval,chromium,front,back):
                if mode!='missing_hook':
                    w.run(['python',stage/a.LAST_SMOKE],stage,{})
                if mode=='duplicate_hook':
                    w.run(['python',stage/a.LAST_SMOKE],stage,{})
                if mode=='original_failure':raise ValueError('synthetic original failure')
                (stage/'SMOKE_OK').write_text(approval)
            w=SimpleNamespace(verify_aux=lambda root:{},test=lambda stage,approval:None,smoke=smoke,installed=lambda stage,approval:None,reviewed=lambda stage,approval:None,run=run,python=lambda stage:'python',env_local=lambda:{})
            a.extend_candidate(w)
            if mode=='success':
                w.smoke(stage,approval,Path('chromium'))
                self.assertEqual((stage/'NATIVE_SMOKE_OK').read_text(),approval)
                self.assertEqual(calls,[str(stage/a.LAST_SMOKE),str(script)])
            else:
                with self.assertRaises(ValueError):w.smoke(stage,approval,Path('chromium'))
                self.assertFalse((stage/'SMOKE_OK').exists())
                self.assertFalse((stage/'NATIVE_SMOKE_OK').exists())
            self.assertIs(w.run,run)

    def test_success_flow(self):self.exercise('success')
    def test_native_failure(self):self.exercise('native_failure')
    def test_original_failure(self):self.exercise('original_failure')
    def test_missing_hook(self):self.exercise('missing_hook')
    def test_duplicate_hook(self):self.exercise('duplicate_hook')


if __name__=='__main__':unittest.main(verbosity=2)
