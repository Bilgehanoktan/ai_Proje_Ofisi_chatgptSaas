"""Scoped standard-library fixture tests, NOT original seven product tests."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).with_name('verify_current_org_g7.py')
spec = importlib.util.spec_from_file_location('current_g7_runner', MODULE)
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


class IsolatedRunnerGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, rel, data=b'abc'):
        p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        return p

    def test_git_blob_has_correct_git_hash(self):
        self.assertEqual(runner.git_blob(b'hello\n'), 'ce013625030ba8dba906f756967f9e9ca394464a')

    def test_exact_source_pin_accepts_regular_file(self):
        self.put('x.py',b'abc')
        self.assertEqual(runner.pinned_bytes(self.root,'x.py',runner.git_blob(b'abc')),b'abc')

    def test_modified_source_fails_closed(self):
        self.put('x.py',b'abc')
        with self.assertRaisesRegex(runner.GateError,'BLOB_MISMATCH'):
            runner.pinned_bytes(self.root,'x.py',runner.git_blob(b'abd'))

    def test_traversal_rejected(self):
        self.put('x.py')
        for bad in ('../x.py','/tmp/x.py','x/../x.py','x\\path',''):
            with self.subTest(bad=bad),self.assertRaises(runner.GateError):
                runner.safe_file(self.root,bad)

    def test_symlink_regular_file_rejected(self):
        self.put('x.py')
        (self.root/'link.py').symlink_to(self.root/'x.py')
        with self.assertRaisesRegex(runner.GateError,'SYMLINK'):
            runner.safe_file(self.root,'link.py')

    def test_symlink_parent_rejected(self):
        a=self.root/'a';a.mkdir(); (a/'file.py').write_bytes(b'ok')
        (self.root/'link').symlink_to(a, target_is_directory=True)
        with self.assertRaisesRegex(runner.GateError,'SYMLINK'):
            runner.safe_file(self.root,'link/file.py')

    def test_missing_source_rejected(self):
        with self.assertRaisesRegex(runner.GateError,'MISSING'):
            runner.safe_file(self.root,'absent.py')

    def test_manifest_invalid_pin_rejected(self):
        blob=b'{"files":{"a.txt":{"bytes":3,"sha256":"x"}}}'
        self.put('product/SOURCE_MANIFEST.json',blob)
        with patch.object(runner,'PRODUCT_MANIFEST_BLOB',runner.git_blob(blob)):
            with self.assertRaisesRegex(runner.GateError,'MANIFEST_ENTRY_COUNT'):
                runner.verify_manifest(self.root)

    def test_g7_invalid_pin_count_rejected(self):
        blob=b'{}';self.put(runner.G7_PINS_PATH,blob)
        with patch.object(runner,'ORIGINAL_G7_PINS_BLOB',runner.git_blob(blob)):
            with self.assertRaisesRegex(runner.GateError,'G7_PINSET_COUNT'):
                runner.verify_original_pins(self.root)

    def test_preloaded_injected_old_module_rejected(self):
        with patch.dict(sys.modules,{'durable_ops':object()}):
            with self.assertRaisesRegex(runner.GateError,'PRELOADED_ORG_UNTRUSTED'):
                with runner.product_import_first(self.root): pass

    def test_commit_invalid_or_no_git_rejected(self):
        with self.assertRaises(runner.GateError):
            runner.check_commit(self.root)

    def test_non_clean_git_checkout_rejected(self):
        subprocess.run(['git','-C',str(self.root),'init','-q'],check=True)
        subprocess.run(['git','-C',str(self.root),'config','user.email','test@example.invalid'],check=True)
        subprocess.run(['git','-C',str(self.root),'config','user.name','Isolated Test'],check=True)
        self.put('tracked.txt')
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.root),'commit','-qm','test'],check=True)
        sha=subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
        self.put('untracked.txt')
        with self.assertRaisesRegex(runner.GateError,'NONCLEAN_CHECKOUT'):
            runner.check_commit(self.root,sha)

    def test_unchanged_git_checkout_can_pass_commit_gate(self):
        subprocess.run(['git','-C',str(self.root),'init','-q'],check=True)
        subprocess.run(['git','-C',str(self.root),'config','user.email','test@example.invalid'],check=True)
        subprocess.run(['git','-C',str(self.root),'config','user.name','Isolated Test'],check=True)
        self.put('tracked.txt')
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.root),'commit','-qm','test'],check=True)
        sha=subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
        self.assertIsNone(runner.check_commit(self.root,sha))

    def test_import_origin_check_rejects_other_fixture(self):
        class F:
            __file__=str(self.root/'not-original.py')
            OperationsStore=object
        with patch.dict(sys.modules,{'test_org_core_checkout':F()}):
            with self.assertRaisesRegex(runner.GateError,'WRONG_ORG06_FIXTURE'):
                runner.assert_fixture_uses_product(type('M',(),{})(),self.root)

    def test_import_identity_check_rejects_other_operations_store(self):
        class F:
            __file__=str(self.root/'candidates/ORG-06/test_org_core_checkout.py')
            OperationsStore=object
        class M: OperationsStore=str
        with patch.dict(sys.modules,{'test_org_core_checkout':F()}):
            with self.assertRaisesRegex(runner.GateError,'FIXTURE_HAS_HISTORICAL'):
                runner.assert_fixture_uses_product(M,self.root)

    def test_missing_checkout_from_cli_returns_hold(self):
        self.assertEqual(runner.main(['--root',str(self.root)]),2)


if __name__=='__main__':unittest.main(verbosity=2)
