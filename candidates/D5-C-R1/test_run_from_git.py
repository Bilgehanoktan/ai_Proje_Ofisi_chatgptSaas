"""Synthetic local Git fixture tests; NOT original Authority/T1 tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from run_from_git import blob, recover, safe_path, outcome, MANIFEST, RUNNER


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.repo = self.root/'repo'; self.repo.mkdir()
        self.stage = self.root/'stage'; self.stage.mkdir()
        self.git('init', '-q'); self.git('config', 'user.name', 'fixture'); self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        self.key = 'backend/tests/test_fixture.py'; self.path = 'product/'+self.key
        self.raw = b'fixture\n'; self.runner = b'# fixture; never executed\n'; self.ddl = b'-- fixture\n'
        self.write(self.path, self.raw); self.write(RUNNER, self.runner); self.write('database/f.sql', self.ddl)
        self.manifest = json.dumps({'files': {self.key: {'bytes': len(self.raw), 'sha256': hashlib.sha256(self.raw).hexdigest()}}}).encode()
        self.write(MANIFEST, self.manifest); self.commit = self.snapshot()

    def git(self, *args):
        return subprocess.check_output(['git','-C',str(self.repo),*args], stderr=subprocess.PIPE).decode().strip()

    def write(self, name, raw):
        p = self.repo/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(raw)

    def snapshot(self):
        self.git('add','-A'); self.git('commit','-qm','fixture'); return self.git('rev-parse','HEAD')

    def recover(self, **kw):
        args = dict(commit=self.commit, manifest_pin=blob(self.manifest), runner_pin=blob(self.runner),
                    prefix='backend/', expected=1, ddl={'database/f.sql': blob(self.ddl)}, tests={self.path: blob(self.raw)})
        args.update(kw); return recover(self.repo, self.stage, **args)

    def test_exact_staging(self):
        self.assertEqual(self.recover(), {'backend':1,'ddl':1,'explicit_test_pins':1,'files':4})
        self.assertEqual((self.stage/self.path).read_bytes(),self.raw)
        self.assertEqual((self.stage/RUNNER).read_bytes(),self.runner)

    def test_dirty_checkout_ignored(self):
        self.write(self.path,b'changed'); self.recover(); self.assertEqual((self.stage/self.path).read_bytes(),self.raw)
        self.assertEqual((self.repo/self.path).read_bytes(),b'changed')

    def test_missing_commit(self):
        with self.assertRaises(subprocess.CalledProcessError): self.recover(commit='0'*40)

    def test_manifest_pin_mismatch(self):
        with self.assertRaisesRegex(ValueError,'PIN_HOLD'): self.recover(manifest_pin='0'*40)

    def test_backend_extra_file(self):
        self.write('product/backend/extra.py',b''); commit=self.snapshot()
        with self.assertRaisesRegex(ValueError,'BACKEND_INVENTORY_HOLD'): self.recover(commit=commit)

    def test_manifest_hash_mismatch(self):
        self.write(self.path,b'changed\n'); commit=self.snapshot()
        with self.assertRaisesRegex(ValueError,'MANIFEST_DRIFT_HOLD'): self.recover(commit=commit, tests={self.path:blob(b'changed\n')})

    def test_test_pin_mismatch(self):
        with self.assertRaisesRegex(ValueError,'PIN_HOLD'): self.recover(tests={self.path:'0'*40})

    def test_ddl_pin_mismatch(self):
        with self.assertRaisesRegex(ValueError,'PIN_HOLD'): self.recover(ddl={'database/f.sql':'0'*40})

    def test_runner_pin_mismatch(self):
        with self.assertRaisesRegex(ValueError,'PIN_HOLD'): self.recover(runner_pin='0'*40)

    def test_nonempty_stage(self):
        (self.stage/'existing').touch()
        with self.assertRaisesRegex(ValueError,'STAGE_NOT_EMPTY_HOLD'): self.recover()

    def test_unsafe_paths(self):
        for p in ('../x','/x','a//b','a/./b','a/../b','a\\b','C:x',''):
            with self.subTest(p=p), self.assertRaises(ValueError): safe_path(p)

    def test_symlink_tree_entry_rejected(self):
        p=self.repo/self.path; p.unlink(); p.symlink_to('other'); commit=self.snapshot()
        with self.assertRaisesRegex(ValueError,'TREE_ENTRY_HOLD'): self.recover(commit=commit)

    def test_outcome_requires_all_markers(self):
        raw=b'PIN_MATCH: 237 backend manifest entries + 3 original DDL; 3 explicit test pins\nRan 17 tests in 0.1s\n\nOK\n'
        self.assertEqual(outcome(0,raw),'PASS_LOCAL_SQLITE_ONLY')
        for code, data in ((1,raw),(0,raw.replace(b'17 tests',b'16 tests')),(0,b'Ran 17 tests in 0.1s\nOK\n'),(0,raw.replace(b'OK',b'OK (skipped=1)'))):
            self.assertEqual(outcome(code,data),'FAIL_OR_INCOMPLETE')
        self.assertEqual(outcome(2,b'T1_REGRESSION_BLOCKED: missing'),'BLOCKED')


if __name__ == '__main__': unittest.main(verbosity=2)
