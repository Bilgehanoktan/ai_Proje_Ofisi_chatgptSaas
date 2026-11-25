"""Offline recovery runner tests; actual candidate DDL tested separately from 17 cases."""
import hashlib
import json
from pathlib import Path
import sqlite3
import stat
import tempfile
import unittest
import warnings
import zipfile
from contextlib import closing
import run_lifecycle_p05 as runner

class RunnerTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve(); self.source=self.root/'source'; self.source.mkdir()
        self.stage=self.root/'stage'; self.stage.mkdir()
        self.name='product/ai-company-os-backend/tests/sample.py'
        self.data=b'hello\n'
        self.info={'path':self.name,'bytes':len(self.data),'git_blob':runner.blob(self.data),'sha256':hashlib.sha256(self.data).hexdigest()}
        self.lock={'files':[self.info]}
        path=self.source/self.name; path.parent.mkdir(parents=True);path.write_bytes(self.data)
    def test_exact_directory(self):
        runner.materialize(self.source,self.stage,self.lock)
        self.assertEqual((self.stage/self.name).read_bytes(),self.data)
    def test_tamper_same_size(self):
        (self.source/self.name).write_bytes(b'wrong\n')
        with self.assertRaisesRegex(ValueError,'BLOB_MISMATCH'):runner.materialize(self.source,self.stage,self.lock)
    def test_sha256_mismatch(self):
        self.info['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'SHA256_MISMATCH'):runner.materialize(self.source,self.stage,self.lock)
    def test_path_traversal(self):
        self.info['path']='../outside'
        with self.assertRaisesRegex(ValueError,'UNSAFE'):runner.materialize(self.source,self.stage,self.lock)
    def test_duplicate_pin(self):
        self.lock['files'].append(self.info)
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):runner.materialize(self.source,self.stage,self.lock)
    def test_nonempty_stage(self):
        (self.stage/'old').touch()
        with self.assertRaisesRegex(ValueError,'NOT_EMPTY'):runner.materialize(self.source,self.stage,self.lock)
    def zip(self, entries):
        p=self.root/'source.zip'
        with warnings.catch_warnings(),zipfile.ZipFile(p,'w') as z:
            warnings.simplefilter('ignore',UserWarning)
            for name,data in entries:z.writestr(name,data)
        return p
    def test_zip_exact_root(self):
        runner.materialize(self.zip([('archive/'+self.name,self.data),('ignored',b'x')]),self.stage,self.lock)
        self.assertEqual((self.stage/self.name).read_bytes(),self.data)
    def test_zip_duplicate_member(self):
        p=self.zip([(self.name,self.data),('archive/'+self.name,self.data)])
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):runner.materialize(p,self.stage,self.lock)
    def test_zip_symlink(self):
        entry=zipfile.ZipInfo(self.name);entry.create_system=3;entry.external_attr=(stat.S_IFLNK|0o777)<<16
        with self.assertRaisesRegex(ValueError,'NONREGULAR'):runner.materialize(self.zip([(entry,self.data)]),self.stage,self.lock)
    def test_zip_missing(self):
        with self.assertRaisesRegex(ValueError,'MISSING'):runner.materialize(self.zip([('other',self.data)]),self.stage,self.lock)
    def test_wrong_lock(self):
        path=self.root/'lock.json';path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'LOCK_BLOB'):runner.load_lock(path)
    def child(self,body,expected):
        tests=self.stage/runner.BACKEND/'tests';tests.mkdir(parents=True)
        (tests/'test_sample.py').write_text('import unittest\nclass Sample(unittest.TestCase):\n'+body)
        return runner.run_cases(self.stage,{'test_sample':expected})
    def test_actual_child_pass(self):
        r=self.child(' def test_ok(self): self.assertEqual(1,1)\n',1)
        self.assertEqual((r['status'],r['passed']),('PASS',1))
    def test_child_failure(self):
        r=self.child(' def test_bad(self): self.fail("bad")\n',1)
        self.assertEqual((r['status'],r['passed']),('FAIL',0))
    def test_child_skip(self):
        r=self.child(' @unittest.skip("not run")\n def test_skip(self): pass\n',1)
        self.assertEqual((r['status'],r['passed']),('FAIL',0))
    def test_child_count_mismatch(self):
        r=self.child(' def test_ok(self): pass\n',2)
        self.assertEqual(r['status'],'FAIL')
    def test_child_subtest_failure(self):
        r=self.child(' def test_bad(self):\n  with self.subTest(x=1): self.fail("bad")\n',1)
        self.assertEqual((r['status'],r['passed']),('FAIL',0))

if __name__=='__main__':unittest.main()
